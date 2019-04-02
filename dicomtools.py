import os
import re
import datetime

import numpy
import pydicom

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
