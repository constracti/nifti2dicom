#!/usr/bin/python3

# TODO slice_code

import argparse
import os
import copy
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
	# prepare common DICOM dataset
	dataset = copy.deepcopy(dataset1)
	# Window Explanation Algorithm not specified
	# (0x0028, 0x1050) Window Center
	dataset.pop((0x0028, 0x1050), None)
	# (0x0028, 0x1051) Window Width
	dataset.pop((0x0028, 0x1051), None)
	# (0x0028, 0x1055) Window Center & Width Explanation
	dataset.pop((0x0028, 0x1055), None)
	for nifticnt, niftipath in enumerate(niftipaths):
		print("reading [{}/{}] NIfTI file {}".format(nifticnt + 1, len(niftipaths), niftipath))
		# reorient NIfTI image
		nifti = nibabel.load(niftipath)
		ornt = nibabel.io_orientation(numpy.linalg.solve(affine, nifti.get_affine()))
		nifti = nifti.as_reoriented(ornt)
		shape = nifti.get_shape()
		# prepare DICOM pixel data by transposing NIfTI data
		data = numpy.asarray(nifti.dataobj).swapaxes(0, 1)
		# customize common DICOM dataset
		dataset.ProtocolName = re.sub("\.nii(?:\.gz)$", "", os.path.split(niftipath)[-1], flags=re.I)
		dataset.SeriesInstanceUID = pydicom.uid.generate_uid()
		# save DICOM files
		subdirname = dicomtools.get_series(dataset) + datetime.datetime.now().strftime("-%Y%m%d%H%M%S")
		subdirpath = os.path.join(dirpath, subdirname)
		assert not os.path.exists(subdirpath)
		os.mkdir(subdirpath)
		for f in range(shape[-1]):
			dicomname = str(f).zfill(math.floor(math.log10(shape[-1])) + 1) + ".dcm"
			dicompath = os.path.join(subdirpath, dicomname)
			# (0x0020, 0x0013) Instance Number
			dataset.InstanceNumber = f + 1
			# Slice Number MR
			if (0x2001, 0x100a) in dataset:
				dataset[0x2001, 0x100a].value = f + 1
			dicomtools.linear_datetime(["InstanceCreation", "Acquisition", "Content"], dataset, dataset1, dataset2)
			# NOTE (0x0008, 0x0018) SOP Instance UID
			# NOTE (0x0029, 0x1010) CSA Image Header Info
			if len(shape) == 4:
				dataset.AcquisitionNumber = f + 1
				# (0x0019, 0x1016) [TimeAfterStart]
				dicomtools.linear_float((0x0019, 0x1016), dataset, dataset1, dataset2)
				data_slice = numpy.zeros((dataset.Rows, dataset.Columns), data.dtype)
				jinc = shape[1]
				jbeg, jend = 0, jinc
				iinc = shape[0]
				ibeg, iend = 0, iinc
				for k in range(shape[2]):
					data_slice[jbeg:jend, ibeg:iend] = data[:, :, k, f]
					ibeg, iend = ibeg + iinc, iend + iinc
					if iend > dataset1.Columns:
						ibeg, iend = 0, iinc
						jbeg, jend = jbeg + jinc, jend + jinc
				# NOTE (0x0008, 0x2112) Source Image Sequence
			else:
				# (0x0019, 0x1016) [SlicePosition_PCS]
				if (0x0019, 0x1016) in dataset:
					dicomtools.linear_float_array((0x0019, 0x1015), dataset, dataset1, dataset2)
				# (0x0019, 0x1016) [TimeAfterStart]
				if (0x0019, 0x1016) in dataset:
					dicomtools.linear_float((0x0019, 0x1016), dataset, dataset1, dataset2)
				# (0x0020, 0x0032) Image Position (Patient)
				dicomtools.linear_float_array((0x0020, 0x0032), dataset, dataset1, dataset2)
				# (0x0020, 0x1041) Slice Location
				dicomtools.linear_float((0x0020, 0x1041), dataset, dataset1, dataset2)
				data_slice = data[:, :, f]
				# NOTE (0x0051, 0x100d), e.g. SP A116.1 and SP P72.4
			# (0x0028, 0x0106) Smallest Image Pixel Value
			if "SmallestImagePixelValue" in dataset:
				dataset.SmallestImagePixelValue = data_slice.min()
			# (0x0028, 0x0107) Largest Image Pixel Value
			if "LargestImagePixelValue" in dataset:
				dataset.LargestImagePixelValue = data_slice.max()
			# assuming data.dtype.itemsize == 2; thus VR="OW" (Other Word) and not "OB" (Other Byte)
			# http://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.7.6.3.html
			# http://dicom.nema.org/medical/dicom/current/output/chtml/part05/sect_6.2.html
			# (0x7fe0, 0x0010) Pixel Data
			dataset.add_new((0x7fe0, 0x0010), "OW",  data_slice.tobytes())
			# NOTE (0xfffc, 0xfffc) Data Set Trailing Padding
			print("writing [{}/{}] DICOM file {}".format(f + 1, shape[-1], dicompath))
			pydicom.dcmwrite(dicompath, dataset)
	print("nifti2dicom complete")

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Convert a NIfTI file to a set of DICOM files.")
	parser.add_argument("path", help="source NIfTI file or directory")
	args = parser.parse_args()
	nifti2dicom(args.path)
