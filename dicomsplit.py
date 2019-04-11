#!/usr/bin/python3

import argparse
import os
import shutil

import pydicom

import dicomtools

def split(path, move=False, force=False, single=False, verbose=False):
	assert os.path.isdir(path), "path {} is not a directory".format(path)
	# find DICOM files
	files = []
	series = []
	for filename in os.listdir(path):
		filepath = os.path.join(path, filename)
		if not os.path.isfile(filepath):
			continue
		try:
			aseries = dicomtools.get_series(filepath)
		except pydicom.errors.InvalidDicomError:
			continue
		files.append((filename, filepath, aseries))
		if aseries not in series:
			series.append(aseries)
	if verbose:
		print("found {} DICOM files with {} different series".format(len(files), len(series)))
	if len(series) > 1 or len(series) == 1 and single:

		# check subdirectories
		if not force:
			for aseries in series:
				dirpath = os.path.join(path, aseries)
				assert not os.path.isfile(dirpath), "file {} exists".format(aseries)
				assert not os.path.isdir(dirpath), "directory {} exists".format(aseries)
		# create subdirectories
		for aseries in series:
			dirpath = os.path.join(path, aseries)
			if os.path.isfile(dirpath):
				if verbose:
					print("removing file {}".format(aseries))
				os.remove(dirpath)
			elif os.path.isdir(dirpath):
				if verbose:
					print("removing directory {}".format(aseries))
				shutil.rmtree(dirpath)
			if verbose:
				print("creating directory {}".format(aseries))
			os.mkdir(dirpath)
		# place DICOM files to subdirectories 
		for i, (filename, filepath, aseries) in enumerate(files):
			newpath = os.path.join(path, aseries, filename)
			if move:
				if verbose:
					print("[{}/{}] moving DICOM file {} to directory {}".format(i + 1, len(files), filename, aseries))
				shutil.move(filepath, newpath)
			else:
				if verbose:
					print("[{}/{}] copying DICOM file {} to directory {}".format(i + 1, len(files), filename, aseries))
				shutil.copy2(filepath, newpath)
	if verbose:
		print("dicomsplit complete")
	return series

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Place each DICOM file in a subdirectory according to Protocol Name and Series Number.")
	parser.add_argument("path", help="directory of mixed DICOM files")
	parser.add_argument("-m", "--move", action="store_true", help="move files instead of copying")
	parser.add_argument("-f", "--force", action="store_true", help="overwrite existing subdirectories")
	parser.add_argument("-s", "--single", action="store_true", help="run even if all DICOM files belong to the same series")
	parser.add_argument("-v", "--verbose", action="store_true", help="print actions")
	args = parser.parse_args()
	split(args.path, move=args.move, force=args.force, single=args.single, verbose=args.verbose)
