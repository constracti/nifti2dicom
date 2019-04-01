#!/usr/bin/python3

import argparse
import os
import re

import pydicom

def _path2dataset(path):
	assert os.path.isfile(path)
	assert re.search("\.(?:dcm|ima)$", path, flags=re.I)
	return pydicom.dcmread(path)

def diff(dcm1, dcm2):
	if type(dcm1) is str:
		dcm1 = _path2dataset(dcm1)
	if type(dcm2) is str:
		dcm2 = _path2dataset(dcm2)
	tags1 = iter(sorted(dcm1.keys()))
	tags2 = iter(sorted(dcm2.keys()))
	tag1 = next(tags1, None)
	tag2 = next(tags2, None)
	while tag1 and tag2:
		val1 = dcm1[tag1]
		val2 = dcm2[tag2]
		if tag1 < tag2:
			print("< {}".format(val1))
			tag1 = next(tags1, None)
		elif tag2 < tag1:
			print("> {}".format(val2))
			tag2 = next(tags2, None)
		else:
			if val1 != val2:
				print("< {}".format(val1))
				print("> {}".format(val2))
			tag1 = next(tags1, None)
			tag2 = next(tags2, None)
	while tag1:
		val1 = dcm1[tag1]
		print("< {}".format(val1))
		tag1 = next(tags1, None)
	while tag2:
		val2 = dcm2[tag2]
		print("< {}".format(val2))
		tag2 = next(tags2, None)


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("dcm1", help="first DICOM file")
	parser.add_argument("dcm2", help="second DICOM file")
	args = parser.parse_args()
	diff(args.dcm1, args.dcm2)
