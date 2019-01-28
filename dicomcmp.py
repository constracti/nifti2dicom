import argparse
import os
import re
import pydicom


def _path2set(path):
	set = []
	if os.path.isdir(path):
		for f in os.listdir(path):
			if re.search("\.(?:dcm|ima)$", f, flags=re.I):
				set.append(os.path.join(path, f))
		assert set, "directory {} does not contain any DICOM file".format(path)
	elif os.path.isfile(path):
		assert re.search("\.(?:dcm|ima)$", path, flags=re.I), "not a DICOM file {}".format(path)
		set.append(path)
	else:
		assert False, "not a valid directory or file {}".format(path)
	return set


def cmp(set1, set2, verbose=False):
	if type(set1) is str:
		set1 = _path2set(set1)
	if type(set2) is str:
		set2 = _path2set(set2)

	assert len(set1) == len(set2), "sets have different number of elements"
	if verbose:
		print("comparing {} pairs of DICOM pixel data".format(len(set1)))

	for i, (f1, f2) in enumerate(zip(set1, set2)):
		if verbose:
			print("pair #{}: ".format(i), end="")
		if type(f1) is not bytes:
			if type(f1) is not pydicom.dataset.FileDataset:
				f1 = pydicom.dcmread(f1, specific_tags=["PixelData"])
			f1 = f1.PixelData
		if type(f2) is not bytes:
			if type(f2) is not pydicom.dataset.FileDataset:
				f2 = pydicom.dcmread(f2, specific_tags=["PixelData"])
			f2 = f2.PixelData
		cmp = f1 == f2
		if verbose:
			print("pass" if cmp else "fail")
		if not cmp:
			if __name__ == "__main__":
				exit(1)
			return False
	if __name__ == "__main__":
		exit(0)
	return True


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("dir1", help="first directory")
	parser.add_argument("dir2", help="second directory")
	parser.add_argument("--verbose", "-v", action="store_true")
	args = parser.parse_args()
	cmp(args.dir1, args.dir2, verbose=args.verbose)
