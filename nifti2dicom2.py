#!/usr/bin/python3

import argparse
import os
import re
import datetime
import math

import numpy
import nibabel
import pydicom

import dicomtools

def nifti2dicom(path):
	# find NIfTI files
	if os.path.isfile(path):
		assert re.search("\.nii(?:\.gz)$", path, flags=re.I), "{} is not a NIfTI file".format(path)
		niftipaths = [path]
		dirpath = os.path.dirname(path)
	elif os.path.isdir(path):
		niftipaths = [os.path.join(path, filename) for filename in os.listdir(path) if re.search("\.nii(?:\.gz)$", filename, flags=re.I)]
		dirpath = path
	else:
		assert False, "{} is neither a file nor a directory".format(path)
	# find DICOM files
	dicompaths = dicomtools.dir_list_files(dirpath)
	assert len(dicompaths) >= 2, "directory {} must contain at least two DICOM files".format(dirpath)
	# read first and last DICOM files
	dataset1 = pydicom.dcmread(dicompaths[0], stop_before_pixels=True)
	dataset2 = pydicom.dcmread(dicompaths[-1], stop_before_pixels=True)
	# calculate NIfTI affine
	shape, zooms, affine = dicomtools.get_affine(dataset1, dataset2)
	for nifticnt, niftipath in enumerate(niftipaths):
		print("reading [{}/{}] NIfTI file {}".format(nifticnt + 1, len(niftipaths), niftipath))
		# reorient NIfTI image
		nifti = nibabel.load(niftipath)
		ornt = nibabel.io_orientation(numpy.linalg.solve(affine, nifti.get_affine()))
		nifti = nifti.as_reoriented(ornt)
		if not numpy.all(shape == nifti.get_shape()):
			print("skipping NIfTI file: incompatible shape")
			continue
		# customize common DICOM tags
		protocol_name = re.sub("\.nii(?:\.gz)$", "", os.path.split(niftipath)[-1], flags=re.I)
		series_instance_uid = pydicom.uid.generate_uid()
		# prepare DICOM pixel data by transposing NIfTI data
		data = numpy.asarray(nifti.dataobj).swapaxes(0, 1)
		# save DICOM files
		subdirname = dicomtools.get_series(dataset1) + datetime.datetime.now().strftime("-%Y%m%d%H%M%S")
		subdirpath = os.path.join(dirpath, subdirname)
		assert not os.path.exists(subdirpath)
		os.mkdir(subdirpath)
		dicomlen = len(dicompaths)
		dicomlog = math.floor(math.log10(dicomlen)) + 1
		for dicomcnt, dicompath in enumerate(dicompaths):
			newdicomname = str(dicomcnt).zfill(dicomlog) + ".dcm"
			newdicompath = os.path.join(subdirpath, newdicomname)
			dataset = pydicom.dcmread(dicompath, stop_before_pixels=True)
			if len(shape) == 4: # TODO nifti2dicom DTI
				data_slice = numpy.zeros((dataset.Rows, dataset.Columns), data.dtype)
				jinc = shape[1]
				jbeg, jend = 0, jinc
				iinc = shape[0]
				ibeg, iend = 0, iinc
				for k in range(shape[2]):
					data_slice[jbeg:jend, ibeg:iend] = data[:, :, k, dicomcnt]
					ibeg, iend = ibeg + iinc, iend + iinc
					if iend > dataset.Columns:
						ibeg, iend = 0, iinc
						jbeg, jend = jbeg + jinc, jend + jinc
			else:
				data_slice = data[:, :, dicomcnt]
			# (0x0018, 0x1030) Protocol Name
			if (0x0018, 0x1030) in dataset:
				dataset[0x0018, 0x1030].value = protocol_name
			# (0x0020, 0x000e) Series Instance UID
			if (0x0020, 0x000e) in dataset:
				dataset[0x0020, 0x000e].value = series_instance_uid
			# (0x0028, 0x0106) Smallest Image Pixel Value
			if (0x0028, 0x0106) in dataset:
				dataset[0x0028, 0x0106].value = data_slice.min()
			# (0x0028, 0x0107) Largest Image Pixel Value
			if (0x0028, 0x0107) in dataset:
				dataset[0x0028, 0x0107].value = data_slice.max()
			# (0x0028, 0x1050) Window Center
			# (0x0028, 0x1051) Window Width
			if (0x0028, 0x1050) in dataset and (0x0028, 0x1051) in dataset:
				dicomtools.autobrightness(dataset, data_slice)
			# (0x0028, 0x1052) Rescale Intercept
			if (0x0028, 0x1052) in dataset:
				dataset[0x0028, 0x1052].value = 0
			# (0x0028, 0x1053) Rescale Slope
			if (0x0028, 0x1053) in dataset:
				dataset[0x0028, 0x1053].value = 1
			# assuming data.dtype.itemsize == 2; thus VR="OW" (Other Word) and not "OB" (Other Byte)
			# http://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.7.6.3.html
			# http://dicom.nema.org/medical/dicom/current/output/chtml/part05/sect_6.2.html
			# (0x7fe0, 0x0010) Pixel Data
			dataset.add_new((0x7fe0, 0x0010), "OW",  data_slice.tobytes())
			# NOTE (0xfffc, 0xfffc) Data Set Trailing Padding
			print("writing [{}/{}] DICOM file {}".format(dicomcnt + 1, dicomlen, newdicompath))
			pydicom.dcmwrite(newdicompath, dataset)
	print("nifti2dicom complete")

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Convert NIfTI files to DICOM.", epilog="""
	A set of DICOM files is located in PATH.
	Then, for each NIfTI file in PATH, a subdirectory is created with a copy of the DICOM.
	Pixel Data (0x7fe0, 0x0010) in every copy of the original DICOM set is replaced by image data of the corresponding NIfTI file.
	The Data Set Trailing Padding (0xfffc, 0xfffc) tag is ignored.
	In case PATH holds the path of a NIfTI file, only that NIfTI file is taken under consideration, while the DICOM files set is located in the directory of the NIFTI file.
	""")
	parser.add_argument("path", help="directory of NIfTI files or path of a NIfTI file", metavar="PATH")
	args = parser.parse_args()
	nifti2dicom(args.path)
