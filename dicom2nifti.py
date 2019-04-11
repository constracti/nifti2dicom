#!/usr/bin/python3

import argparse
import os
import datetime

import numpy
import pydicom
import nibabel

import dicomsplit
import dicomtools

def dicom2nifti(dirpath):
	# find DICOM files
	dicompaths = dicomtools.dir_list_files(dirpath)
	assert len(dicompaths) >= 2, "{} does not contain at least two DICOM files".format(dirpath)
	# read first and last DICOM files
	dataset1 = pydicom.dcmread(dicompaths[0], stop_before_pixels=True)
	dataset2 = pydicom.dcmread(dicompaths[-1], stop_before_pixels=True)
	assert dataset2.InstanceNumber - dataset1.InstanceNumber + 1 == len(dicompaths)
	# TODO datatype
	datatype = numpy.int16
	# calculate NIfTI affine
	shape, zooms, affine = dicomtools.get_affine(dataset1, dataset2)
	# build NIfTI image
	tags = [
		"InstanceNumber",
		"BitsAllocated", "Rows", "Columns", "PixelRepresentation", "SamplesPerPixel", "PixelData"
	]
	data = numpy.zeros(shape, datatype)
	for f, dicompath in enumerate(dicompaths):
		print("reading [{}/{}] DICOM file {}".format(f + 1, len(dicompaths), dicompath))
		dataset = pydicom.dcmread(dicompath, specific_tags=tags)
		data_slice = dataset.pixel_array
		if len(shape) == 4:
			jinc = shape[1]
			jbeg, jend = 0, jinc
			iinc = shape[0]
			ibeg, iend = 0, iinc
			for k in range(shape[2]):
				data[:, :, k, f] = data_slice[jbeg:jend, ibeg:iend].T
				ibeg, iend = ibeg + iinc, iend + iinc
				if iend > dataset1.Columns:
					ibeg, iend = 0, iinc
					jbeg, jend = jbeg + jinc, jend + jinc
		else:
			data[:, :, f] = data_slice.T
	# create NIfTI object
	nifti = nibabel.Nifti1Image(data, affine)
	# build NIfTI header
	# https://brainder.org/2012/09/23/the-nifti-file-format/
	nifti.header["regular"] = b"r" # unused
	# NOTE dim_info
	if dataset1.InPlanePhaseEncodingDirection == "COL":
		nifti.header.set_dim_info(freq=0, phase=1, slice=2)
	elif dataset1.InPlanePhaseEncodingDirection == "ROW":
		nifti.header.set_dim_info(freq=1, phase=0, slice=2)
	else:
		nifti.header.set_dim_info(slice=2)
	# NOTE pixdim[4:8]
	nifti.header.set_zooms(zooms)
	# TODO slice_start, slice_end, slice_code, slice_duration
	nifti.header.set_xyzt_units("mm", "sec")
	nifti.header["glmax"] = 255    # unused, normally data.max()
	nifti.header["glmin"] = 0      # unused, normally data.min()
	# NOTE descrip
	# NOTE qform_code, sform_code
	# apply default NIfTI transformation
	ornt = numpy.array([[0, 1], [1, -1], [2, 1]])
	if numpy.linalg.det(affine[:3, :3]) < 0:
		ornt[2, 1] = -1
	nifti = nifti.as_reoriented(ornt)
	# save NIfTI file
	niftiname = dicomtools.get_series(dataset1) + datetime.datetime.now().strftime("-%Y%m%d%H%M%S") + ".nii.gz"
	niftipath = os.path.join(dirpath, niftiname)
	assert not os.path.exists(niftipath)
	print("writing NIfTI file {}".format(niftipath))
	nibabel.save(nifti, niftipath)
	print("dicom2nifti complete")

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Convert a set of DICOM files to a NIfTI file.")
	parser.add_argument("path", help="source DICOM files directory")
	# TODO --oriented
	args = parser.parse_args()
	assert os.path.isdir(args.path), "{} is not a directory".format(args.path)
	# split DICOM files
	series = dicomsplit.split(args.path, single=False, verbose=True)
	if len(series) > 1:
		dirpaths = [os.path.join(args.path, aseries) for aseries in series]
	else:
		dirpaths = [args.path]
	# convert DICOM files
	for dirpath in dirpaths:
		dicom2nifti(dirpath)
