#!/usr/bin/python3

import argparse
import os
import re
import math
import datetime
from collections import OrderedDict

import numpy
import pydicom
try:
	import unidecode
except ImportError:
	pass

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
		csa_image_header_info = csa2_decode(dataset1[0x0029, 0x1010].value)
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

def autobrightness(dataset, data = None):
	assert (0x0028, 0x1050) in dataset and (0x0028, 0x1051) in dataset
	if data is None:
		data = dataset.pixel_array
	# (0x0028, 0x0106) Smallest Image Pixel Value
	if (0x0028, 0x0106) in dataset:
		data_min = dataset[0x0028, 0x0106].value
	else:
		data_min = data.min()
	# (0x0028, 0x0107) Largest Image Pixel Value
	if (0x0028, 0x0107) in dataset:
		data_max = dataset[0x0028, 0x0107].value
	else:
		data_max = data.max()
	"""
	data_sorted = numpy.sort(data.flatten())
	data_len = len(data_sorted)
	assert data_len > 1
	data_min = data_sorted[0]
	data_inf = data_sorted[-1]
	step = (data_inf - data_min) / 100
	i = data_len - 1
	while i > 0 and data_sorted[i] - data_sorted[i-1] < step:
		i -= 1
	if i > 0:
		data_max = (data_sorted[i-1] - data_min) * 1.1 + data_min
		if data_max > data_inf:
			data_max = data_inf
	else:
		data_max = data_inf
	"""
	window_width = data_max - data_min + 1
	window_center = data_min + window_width / 2
	# (0x0028, 0x1050) Window Center
	dataset[0x0028, 0x1050].value = window_center
	# (0x0028, 0x1051) Window Width
	dataset[0x0028, 0x1051].value = window_width


########
# csa2 #
########

# http://nipy.org/nibabel/dicom/siemens_csa.html

def csa2_decode(arr):
	assert arr[0:4] == b"SV10"
	# arr[4:8] # unused
	ntags = int.from_bytes(arr[8:12], "little")
	# int.from_bytes(arr[12:16], "little") # unused 77
	i = 16
	hdr = OrderedDict()
	for ctags in range(0, ntags):
		key = arr[i:i+64].split(bytes(1), 1)[0].decode()
		hdr[key] = {}
		hdr[key]["VM"] = int.from_bytes(arr[i+64:i+68], "little")
		hdr[key]["VR"] = arr[i+68:i+72].split(bytes(1), 1)[0].decode()
		hdr[key]["SyngoDT"] = int.from_bytes(arr[i+72:i+76], "little")
		nitems = int.from_bytes(arr[i+76:i+80], "little")
		# int.from_bytes(arr[80:84], "little") # unused 77 or 205
		i += 84
		hdr[key]["Data"] = []
		for citems in range(nitems):
			item_len = int.from_bytes(arr[i:i+4], "little")
			# int.from_bytes(arr[i+4:i+8], "little") # unused
			# int.from_bytes(arr[i+8:i+12], "little") # unused
			# int.from_bytes(arr[i+12:i+16], "little") # unused
			if item_len:
				hdr[key]["Data"].append(arr[i+16:i+16+item_len].split(bytes(1), 1)[0].decode())
			else:
				hdr[key]["Data"].append(None)
			i += 16 + math.ceil(item_len / 4) * 4
	return hdr

def csa2_encode(hdr):
	arr = b""
	arr += b"SV10"
	arr += bytes(4) # unused
	arr += len(hdr).to_bytes(4, "little")
	arr += bytes(4) # unused 77
	for key, val in hdr.items():
		arr += key.encode().ljust(64, bytes(1))
		arr += val["VM"].to_bytes(4, "little")
		arr += val["VR"].encode().ljust(4, bytes(1))
		arr += val["SyngoDT"].to_bytes(4, "little")
		arr += len(val["Data"]).to_bytes(4, "little")
		arr += bytes(4) # unused 77 or 205
		for dat in val["Data"]:
			item_len = len(dat) + 1 if dat is not None else 0
			arr += item_len.to_bytes(4, "little")
			arr += bytes(4) # unused
			arr += bytes(4) # unused
			arr += bytes(4) # unused
			if item_len:
				arr += dat.encode().ljust(math.ceil(item_len / 4) * 4, bytes(1))
	arr += bytes(4) # append one more zero
	return arr

def csa2_diff(hdr1, hdr2):
	keys1 = iter(sorted(hdr1.keys()))
	keys2 = iter(sorted(hdr2.keys()))
	key1 = next(keys1, None)
	key2 = next(keys2, None)
	while key1 and key2:
		val1 = hdr1[key1]
		val2 = hdr2[key2]
		if key1 < key2:
			print("< {}: {}".format(key1, val1))
			key1 = next(keys1, None)
		elif key2 < key1:
			print("> {}: {}".format(key2, val2))
			key2 = next(keys2, None)
		else:
			if val1 != val2:
				print("< {}: {}".format(key1, val1))
				print("> {}: {}".format(key2, val2))
			key1 = next(keys1, None)
			key2 = next(keys2, None)
	while key1:
		val1 = hdr1[key1]
		print("< {}: {}".format(key1, val1))
		key1 = next(keys1, None)
	while key2:
		val2 = hdr2[key2]
		print("> {}: {}".format(key2, val2))
		key2 = next(keys2, None)


##########
# linear #
##########

def linear_float(tag, ds0, ds1, ds2):
	v1 = ds1[tag].value
	v2 = ds2[tag].value
	v0 = v1 + (v2 - v1) / (ds2.InstanceNumber - ds1.InstanceNumber) * (ds0.InstanceNumber - ds1.InstanceNumber)
	ds0[tag].value = v0

def linear_float_array(tag, ds0, ds1, ds2):
	v1 = ds1[tag].value
	v2 = ds2[tag].value
	v1 = numpy.array(v1)
	v2 = numpy.array(v2)
	v0 = v1 + (v2 - v1) / (ds2.InstanceNumber - ds1.InstanceNumber) * (ds0.InstanceNumber - ds1.InstanceNumber)
	v0 = v0.tolist()
	ds0[tag].value = v0

def linear_datetime(tag, ds0, ds1, ds2):
	fd = "%Y%m%d"
	ft = "%H%M%S.%f" if "." in ds0.data_element(tag + "Time").value else "%H%M%S"
	v1 = ds1.data_element(tag + "Date").value + ds1.data_element(tag + "Time").value
	v1 = datetime.datetime.strptime(v1, fd + ft)
	v2 = ds2.data_element(tag + "Date").value + ds2.data_element(tag + "Time").value
	v2 = datetime.datetime.strptime(v2, fd + ft)
	v0 = v1 + (v2 - v1) / (ds2.InstanceNumber - ds1.InstanceNumber) * (ds0.InstanceNumber - ds1.InstanceNumber)
	ds0.data_element(tag + "Date").value = datetime.datetime.strftime(v0, fd)
	ds0.data_element(tag + "Time").value = datetime.datetime.strftime(v0, ft)


########
# main #
########

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	subparsers = parser.add_subparsers(dest="action", help="one of the following actions", metavar="ACTION")
	subparsers.required = True
	parser_dataset = subparsers.add_parser("dataset", description="Output the dataset of a DICOM file.", epilog="""
	Pixel Data (0x7fe0, 0x0010) and Data Set Trailing Padding (0xfffc, 0xfffc) tags are ignored.
	""", help="output the dataset of a DICOM file")
	parser_dataset.add_argument("path", help="path to the DICOM file", metavar="PATH")
	parser_autobrightness = subparsers.add_parser("autobrightness", description="Auto-adjust brightness and contrast of a DICOM file.", epilog="""
	Only (0x0028, 0x1050) Window Center and (0x0028, 0x1051) Window Width tags are affected.
	""", help="auto-adjust brightness and contrast of a DICOM file")
	parser_autobrightness.add_argument("path", help="path of a DICOM file or directory of a set of DICOM files", metavar="PATH")
	args = parser.parse_args()
	if args.action == "dataset":
		dataset = pydicom.dcmread(args.path, stop_before_pixels=True)
		print(dataset)
	elif args.action == "autobrightness":
		if os.path.isfile(args.path):
			dicompaths = [args.path]
		elif os.path.isdir(args.path):
			dicompaths = dir_list_files(args.path)
		else:
			assert False
		for dicompath in dicompaths:
			dataset = pydicom.dcmread(dicompath)
			autobrightness(dataset)
			pydicom.dcmwrite(dicompath, dataset)
