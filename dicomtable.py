#!/usr/bin/python3

import argparse
import os
import re

import pydicom

import dicomtools

parser = argparse.ArgumentParser(description="Output a table with the variable fields of a DICOM set as a CSV.")
parser.add_argument("path", help="directory of DICOM files")
args = parser.parse_args()

assert os.path.isdir(args.path)

dicompaths = dicomtools.dir_list_files(args.path)

datasets = [pydicom.dcmread(dicompath, stop_before_pixels=True) for dicompath in dicompaths]

tags = set().union(*[dataset.keys() for dataset in datasets])

vartags = set()

for tag in tags:
	value = None
	for i, dataset in enumerate(datasets):
		if i == 0:
			if tag in dataset:
				value = str(dataset[tag].value)
		else:
			if tag in dataset and str(dataset[tag].value) == value or tag not in dataset and value is None:
				pass
			else:
				vartags.add(tag)

tags = list(vartags)

tags.sort()

properties = ["VR", "VM", "name", None, "keyword"]

print("id", end="\t")
print("\t".join([str(tag) for tag in tags]))

print("is_private", end="\t")
print("\t".join([str(tag.is_private) for tag in tags]))

dataset = datasets[0]
for i, property in enumerate(properties):
	if property is not None:
		print(property, end="")
		for tag in tags:
			if tag.is_private:
				# http://dicom.nema.org/dicom/2013/output/chtml/part05/sect_7.8.html
				private_creator = dataset[tag.group, tag.element >> 8].value
				if property != "keyword":
					print("\t{}".format(pydicom.datadict.get_private_entry(tag, private_creator)[i]), end="")
				else:
					print("\t", end="")
			else:
				print("\t{}".format(pydicom.datadict.get_entry(tag)[i]), end="")
		print()

for i, dataset in enumerate(datasets):
	print(i, end="")
	for tag in tags:
		if tag in dataset:
			value = re.sub("\s+", " ", str(dataset[tag].value))
			print("\t{}".format(value if len(value) < 256 else "?"), end="")
		else:
			print("\t", end="")
	print()
