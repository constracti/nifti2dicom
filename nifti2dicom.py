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
	# TODO (0x0008, 0x0018) SOP Instance UID steady increment by one
	dataset.pop((0x0008, 0x0018), None)
	# (0x0008, 0x2112) Source Image Sequence
	dataset.pop((0x0008, 0x2112), None)
	if (0x0019, 0x0010) in dataset and dataset[0x0019, 0x0010].value == "SIEMENS MR HEADER":
		# (0x0019, 0x100b) SliceMeasurementDuration
		dataset.pop((0x0019, 0x100b), None)
		# (0x0019, 0x1029) MosaicRefAcqTimes
		dataset.pop((0x0019, 0x1029), None)
	# Window Explanation Algorithm not specified
	# (0x0028, 0x1050) Window Center
	dataset.pop((0x0028, 0x1050), None)
	# (0x0028, 0x1051) Window Width
	dataset.pop((0x0028, 0x1051), None)
	# (0x0028, 0x1055) Window Center & Width Explanation
	dataset.pop((0x0028, 0x1055), None)
	if (0x0029, 0x0010) in dataset and dataset[0x0029, 0x0010].value == "SIEMENS CSA HEADER":
		# (0x0029, 0x1010) CSA Image Header Info
		csa_image_header_info = dicomtools.csa2_decode(dataset[0x0029, 0x1010].value)
	if (0x0043, 0x0010) in dataset and dataset[0x0043, 0x0010].value == "GEMS_PARM_01":
		# (0x0043, 0x1028) Unique image iden
		dataset.pop((0x0043, 0x1028), None)
		# (0x0043, 0x1029) Histogram tables
		dataset.pop((0x0043, 0x1029), None)
		# (0x0043, 0x102a) User defined data
		dataset.pop((0x0043, 0x102a), None)
		# (0x0043, 0x1030) Vas collapse flag
		dataset.pop((0x0043, 0x1030), None)
		# (0x0043, 0x1039) Slop_int_6... slop_int_9
		dataset.pop((0x0043, 0x1039), None)
	if (0x0051, 0x0010) in dataset and dataset[0x0051, 0x0010].value == "SIEMENS MR HEADER":
		# (0x0051, 0x100d), e.g. SP A116.1 and SP P72.4
		dataset.pop((0x0051, 0x100d), None)
	if (0x2001, 0x0090) in dataset and dataset[0x2001, 0x0090].value == "Philips Imaging DD 129":
		# (0x2001, 0x9000) Unknown
		dataset.pop((0x2001, 0x9000), None)
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
			# (0x0008, 0x0012) & (0x0008, 0x0013) Instance Creation Date & Time
			if (0x0008, 0x0012) in dataset and (0x0008, 0x0013) in dataset:
				dicomtools.linear_datetime("InstanceCreation", dataset, dataset1, dataset2)
			# (0x0008, 0x0022) & (0x0008, 0x0032) Acquisition Date & Time
			dicomtools.linear_datetime("Acquisition", dataset, dataset1, dataset2)
			# (0x0008, 0x0023) & (0x0008, 0x0033) Content Date & Time
			dicomtools.linear_datetime("Content", dataset, dataset1, dataset2)
			if len(shape) == 4: # TODO nifti2dicom DTI
				# (0x0020, 0x0012) Acquisition Number
				dataset.AcquisitionNumber = f + 1
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
			else:
				data_slice = data[:, :, f]
			if (0x0019, 0x0010) in dataset and dataset[0x0019, 0x0010].value == "SIEMENS MR HEADER":
				# (0x0019, 0x1015) SlicePosition_PCS
				if (0x0019, 0x1015) in dataset:
					dicomtools.linear_float_array((0x0019, 0x1015), dataset, dataset1, dataset2)
				# (0x0019, 0x1016) TimeAfterStart
				if (0x0019, 0x1016) in dataset:
					dicomtools.linear_float((0x0019, 0x1016), dataset, dataset1, dataset2)
			elif (0x0019, 0x0010) in dataset and dataset[0x0019, 0x0010].value in ["GEMS_ACQU_01", "GEMS_IDEN_01"]:
				# (0x0019, 0x10a2) Raw data run number
				if (0x0019, 0x10a2) in dataset:
					pass # TODO b"\x1a\x16\x00\x00" linear byte
				# TODO (0x0019, 0x10??) User data ??
			# (0x0020, 0x0032) Image Position (Patient)
			if (0x0020, 0x0032) in dataset:
				dicomtools.linear_float_array((0x0020, 0x0032), dataset, dataset1, dataset2)
			# (0x0020, 0x1041) Slice Location
			if (0x0020, 0x1041) in dataset:
				dicomtools.linear_float((0x0020, 0x1041), dataset, dataset1, dataset2)
			# TODO (0x0020, 0x9057) In-Stack Position Number ge-t1 and ge-dti
			if (0x0027, 0x0010) in dataset and dataset[0x0027, 0x0010] == "GEMS_IMAG_01":
				# TODO (0x0027, 0x1040) RAS letter of image location b"S " if SliceLocation >= 0 else b"I "
				# TODO (0x0027, 0x1041) Image location e.g. b"Qj\xbd\xc2"
				pass
			# (0x0028, 0x0106) Smallest Image Pixel Value
			if (0x0028, 0x0106) in dataset:
				dataset[0x0028, 0x0106].value = data_slice.min()
			# (0x0028, 0x0107) Largest Image Pixel Value
			if (0x0028, 0x0107) in dataset:
				dataset[0x0028, 0x0107].value = data_slice.max()
			if (0x0029, 0x0010) in dataset and dataset[0x0029, 0x0010].value == "SIEMENS CSA HEADER":
				# (0x0029, 0x1010) CSA Image Header Info
				if csa_image_header_info["Actual3DImaPartNumber"]["Data"]:
					csa_image_header_info["Actual3DImaPartNumber"]["Data"][0] = str(f).ljust(8)
				elif not csa_image_header_info["MosaicRefAcqTimes"]["Data"]: # TODO linear int on csa_image_header_info
					csa_image_header_info["ProtocolSliceNumber"]["Data"][0] = str(f).ljust(8)
				# csa_image_header_info["GSWDDataType"] CORONAL
				# csa_image_header_info["RFSWDDataType"] CORONAL
				# csa_image_header_info["ICE_Dims"]["Data"][0] *
				# csa_image_header_info["MosaicRefAcqTimes"]["Data"] FMRI
				# csa_image_header_info["SliceMeasurementDuration"]["Data"][0] CORONAL
				csa_image_header_info["SlicePosition_PCS"]["Data"][0:3] = ["{:.8f}".format(x) for x in dataset.ImagePositionPatient]
				if csa_image_header_info["TimeAfterStart"]["Data"]:
					csa_image_header_info["TimeAfterStart"]["Data"][0] = "{:.8f}".format(dataset[0x0019, 0x1016].value)
				dataset[0x0029, 0x1010].value = dicomtools.csa2_encode(csa_image_header_info)
			if (0x2001, 0x0010) in dataset and dataset[0x2001, 0x0010].value == "Philips Imaging DD 001":
				# (0x2001, 0x100a) Slice Number MR
				if (0x2001, 0x100a) in dataset:
					dataset[0x2001, 0x100a].value = f + 1
			if (0x2005, 0x0010) in dataset and dataset[0x2005, 0x0010].value == "Philips MR Imaging DD 001":
				# (0x2005, 0x1008) Unknown
				if (0x2005, 0x1008) in dataset:
					dicomtools.linear_float((0x2005, 0x1008), dataset, dataset1, dataset2)
				# (0x2005, 0x1009) Unknown
				if (0x2005, 0x1009) in dataset:
					dicomtools.linear_float((0x2005, 0x1009), dataset, dataset1, dataset2)
				# (0x2005, 0x100a) Unknown
				if (0x2005, 0x100a) in dataset:
					dicomtools.linear_float((0x2005, 0x100a), dataset, dataset1, dataset2)
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
	parser.add_argument("path", help="directory of NIfTI files or path of a NIfTI file", metavar="PATH")
	args = parser.parse_args()
	nifti2dicom(args.path)
