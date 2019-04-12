import os
import re
import math
import datetime

import numpy
import pydicom
try:
	import unidecode
except ImportError:
	pass

import csa2

def file_is_valid(filename):
	try:
		pydicom.dcmread(filename, specific_tags=[])
		return True
	except:
		return False

def file_get_tag(filename, tag):
	try:
		dataset = pydicom.dcmread(filename, specific_tags=[tag])
		return dataset.data_element(tag).value
	except pydicom.errors.InvalidDicomError:
		return None

def dir_list_files(path="."):
	fs = [os.path.join(path, f) for f in os.listdir(path)]
	fs = [f for f in fs if os.path.isfile(f)]
	fs = [(f, file_get_tag(f, "InstanceNumber")) for f in fs]
	fs = [f for f in fs if f[1] is not None]
	fs.sort(key=lambda f: f[1])
	return [f[0] for f in fs]

def get_series(dataset):
	if type(dataset) is str:
		dataset = pydicom.dcmread(dataset, specific_tags=["SeriesNumber", "ProtocolName"])
	series = "{}-s{:03d}".format(dataset.ProtocolName, dataset.SeriesNumber)
	try:
		series = unidecode.unidecode(series)
	except NameError:
		pass
	return re.sub("[^a-zA-Z0-9]+", "-", series)

def get_affine(dataset1, dataset2):
	# number of slices
	nslices = 1
	if (0x0029, 0x0010) in dataset1 and dataset1[0x0029, 0x0010].value == "SIEMENS CSA HEADER":
		csa_image_header_info = csa2.decode(dataset1[0x0029, 0x1010].value)
		if csa_image_header_info["NumberOfImagesInMosaic"]["Data"]:
			nslices = int(csa_image_header_info["NumberOfImagesInMosaic"]["Data"][0])
	# shape, zooms & affine
	# http://nipy.org/nibabel/dicom/dicom_orientation.html
	X = numpy.array(dataset1.ImageOrientationPatient[0:3])
	Y = numpy.array(dataset1.ImageOrientationPatient[3:6])
	T = numpy.array(dataset1.ImagePositionPatient)
	zooms = numpy.flip(numpy.array(dataset1.PixelSpacing))
	if nslices > 1:
		# http://nipy.org/nibabel/dicom/dicom_mosaic.html
		nblocks = math.ceil(math.sqrt(nslices))
		shape = numpy.array([
			dataset1.Columns // nblocks,
			dataset1.Rows // nblocks,
			nslices,
			dataset2.InstanceNumber - dataset1.InstanceNumber + 1
		])
		zooms = numpy.append(zooms, [
			dataset1.SpacingBetweenSlices if "SpacingBetweenSlices" in dataset1 else dataset1.SliceThickness,
			dataset1.RepetitionTime / 1000,
		])
		Z = numpy.array(csa_image_header_info["SliceNormalVector"]["Data"][:3]).astype(float)
		T += numpy.column_stack((X, Y)) * zooms[:2] @ (numpy.array([dataset1.Columns, dataset1.Rows]) - shape[:2]) / 2
	else:
		shape = numpy.array([
			dataset1.Columns,
			dataset1.Rows,
			dataset2.InstanceNumber - dataset1.InstanceNumber + 1
		])
		Z = (numpy.array(dataset2.ImagePositionPatient) - numpy.array(dataset1.ImagePositionPatient)) / (dataset2.InstanceNumber - dataset1.InstanceNumber)
		zooms = numpy.append(zooms, numpy.linalg.norm(Z))
		Z /= zooms[2]
	R = numpy.column_stack((X, Y, Z))
	affine = numpy.concatenate((R * zooms[:3], T[numpy.newaxis].T), axis=1)
	affine = numpy.concatenate((affine, numpy.array([0, 0, 0, 1])[numpy.newaxis]), axis=0)
	# convert DICOM LPS to NIfTI RAS coordinate system
	affine[:2, :] *= -1
	# return
	return shape, zooms, affine

def _prop(dataset, tag):
	if type(tag) is str:
		return dataset.data_element(tag)
	else:
		return dataset[tag]

def linear_float(tags, ds0, ds1, ds2):
	if type(tags) is not list:
		tags = [tags]
	for t in tags:
		v1 = _prop(ds1, t).value
		v2 = _prop(ds2, t).value
		v0 = v1 + (v2 - v1) / (ds2.InstanceNumber - ds1.InstanceNumber) * (ds0.InstanceNumber - ds1.InstanceNumber)
		_prop(ds0, t).value = v0

def linear_float_array(tags, ds0, ds1, ds2):
	if type(tags) is not list:
		tags = [tags]
	for t in tags:
		v1 = _prop(ds1, t).value
		v2 = _prop(ds2, t).value
		v1 = numpy.array(v1)
		v2 = numpy.array(v2)
		v0 = v1 + (v2 - v1) / (ds2.InstanceNumber - ds1.InstanceNumber) * (ds0.InstanceNumber - ds1.InstanceNumber)
		v0 = v0.tolist()
		_prop(ds0, t).value = v0

def linear_datetime(tags, ds0, ds1, ds2):
	if type(tags) is not list:
		tags = [tags]
	for t in tags:
		v1 = ds1.data_element(t + "Date").value + ds1.data_element(t + "Time").value
		v1 = datetime.datetime.strptime(v1, "%Y%m%d%H%M%S.%f")
		v2 = ds2.data_element(t + "Date").value + ds2.data_element(t + "Time").value
		v2 = datetime.datetime.strptime(v2, "%Y%m%d%H%M%S.%f")
		v0 = v1 + (v2 - v1) / (ds2.InstanceNumber - ds1.InstanceNumber) * (ds0.InstanceNumber - ds1.InstanceNumber)
		ds0.data_element(t + "Date").value = datetime.datetime.strftime(v0, "%Y%m%d")
		ds0.data_element(t + "Time").value = datetime.datetime.strftime(v0, "%H%M%S.%f")
