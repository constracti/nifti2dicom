import numpy
import datetime

def _prop(dataset, tag):
	if type(tag) is str:
		return dataset.data_element(tag)
	else:
		return dataset[tag]

def linear_float(tags, ds0, ds1, ds2):
	if not type(tags) is list:
		tags = [tags]
	for t in tags:
		v1 = _prop(ds1, t).value
		v2 = _prop(ds2, t).value
		v0 = v1 + (v2 - v1) / (ds2.InstanceNumber - ds1.InstanceNumber) * (ds0.InstanceNumber - ds1.InstanceNumber)
		_prop(ds0, t).value = v0

def linear_float_array(tags, ds0, ds1, ds2):
	if not type(tags) is list:
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
	if not type(tags) is list:
		tags = [tags]
	for t in tags:
		v1 = ds1.data_element(t + "Date").value + ds1.data_element(t + "Time").value
		v1 = datetime.datetime.strptime(v1, "%Y%m%d%H%M%S.%f")
		v2 = ds2.data_element(t + "Date").value + ds2.data_element(t + "Time").value
		v2 = datetime.datetime.strptime(v2, "%Y%m%d%H%M%S.%f")
		v0 = v1 + (v2 - v1) / (ds2.InstanceNumber - ds1.InstanceNumber) * (ds0.InstanceNumber - ds1.InstanceNumber)
		ds0.data_element(t + "Date").value = datetime.datetime.strftime(v0, "%Y%m%d")
		ds0.data_element(t + "Time").value = datetime.datetime.strftime(v0, "%H%M%S.%f")
