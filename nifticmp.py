import argparse
import os
import nibabel
import numpy

def _path2obj(path):
	assert os.path.isfile(path)
	return nibabel.load(path)

def cmp(nifti1, nifti2):
	if type(nifti1) is str:
		nifti1 = _path2obj(nifti1)
	if type(nifti1) is not numpy.ndarray:
		nifti1 = nifti1.get_fdata()
	if type(nifti2) is str:
		nifti2 = _path2obj(nifti2)
	if type(nifti2) is not numpy.ndarray:
		nifti2 = nifti2.get_fdata()
	ret = numpy.all(nifti1 == nifti2)
	if __name__ == "__main__":
		exit(not ret)
	return ret

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("path1", help="first file path")
	parser.add_argument("path2", help="second file path")
	args = parser.parse_args()
	cmp(args.path1, args.path2)
