import argparse
import os
import re

import numpy
import nibabel

def _path2obj(path):
	assert os.path.isfile(path)
	assert re.search("\.nii(?:\.gz)$", path, flags=re.I)
	return nibabel.load(path)

def diff(nifti1, nifti2):
	if type(nifti1) is str:
		nifti1 = _path2obj(nifti1)
	if type(nifti2) is str:
		nifti2 = _path2obj(nifti2)
	for key, value1, value2 in zip(nifti1.header.keys(), nifti1.header.values(), nifti2.header.values()):
		try:
			if not numpy.allclose(value1, value2, equal_nan=True):
				print("< {}: {}".format(key, value1))
				print("> {}: {}".format(key, value2))
		except:
			if not value1 == value2:
				print("< {}: {}".format(key, value1))
				print("> {}: {}".format(key, value2))

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("path1", help="first file path")
	parser.add_argument("path2", help="second file path")
	args = parser.parse_args()
	diff(args.path1, args.path2)
