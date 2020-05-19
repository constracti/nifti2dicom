#!/usr/bin/python3

import argparse
import os
import shutil

import pydicom

import dicomtools

def _get_tag(dicom, tags):
	if type(dicom) is str:
		dicom = pydicom.dcmread(dicom, specific_tags=tags)
	return "-".join(str(dicom[tag].value) for tag in tags)

def split(path, tags=[], move=False, force=False, single=False, verbose=False):
	assert os.path.isdir(path), "path {} is not a directory".format(path)
	# find DICOM files
	files = []
	dcmsets = []
	for filename in os.listdir(path):
		filepath = os.path.join(path, filename)
		if not os.path.isfile(filepath):
			continue
		try:
			if tags:
				dcmset = _get_tag(filepath, tags)
			else:
				dcmset = dicomtools.get_series(filepath)
		except pydicom.errors.InvalidDicomError:
			continue
		files.append((filename, filepath, dcmset))
		if dcmset not in dcmsets:
			dcmsets.append(dcmset)
	if verbose:
		print("found {} DICOM files with {} different series".format(len(files), len(dcmsets)))
	if len(dcmsets) > 1 or len(dcmsets) == 1 and single:
		# check subdirectories
		if not force:
			for dcmset in dcmsets:
				dirpath = os.path.join(path, dcmset)
				assert not os.path.isfile(dirpath), "file {} exists".format(dcmset)
				assert not os.path.isdir(dirpath), "directory {} exists".format(dcmset)
		# create subdirectories
		for dcmset in dcmsets:
			dirpath = os.path.join(path, dcmset)
			if os.path.isfile(dirpath):
				if verbose:
					print("removing file {}".format(dcmset))
				os.remove(dirpath)
			elif os.path.isdir(dirpath):
				if verbose:
					print("removing directory {}".format(dcmset))
				shutil.rmtree(dirpath)
			if verbose:
				print("creating directory {}".format(dcmset))
			os.mkdir(dirpath)
		# place DICOM files to subdirectories 
		for i, (filename, filepath, dcmset) in enumerate(files):
			newpath = os.path.join(path, dcmset, filename)
			if move:
				if verbose:
					print("[{}/{}] moving DICOM file {} to directory {}".format(i + 1, len(files), filename, dcmset))
				shutil.move(filepath, newpath)
			else:
				if verbose:
					print("[{}/{}] copying DICOM file {} to directory {}".format(i + 1, len(files), filename, dcmset))
				shutil.copy2(filepath, newpath)
	if verbose:
		print("dicomsplit complete")
	return dcmsets

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Place each DICOM file in a subdirectory according to Protocol Name and Series Number.")
	parser.add_argument("path", help="directory of mixed DICOM files", metavar="PATH")
	parser.add_argument("-m", "--move", action="store_true", help="move files instead of copying")
	parser.add_argument("-t", "--tag", action="append", help="split DICOM files according to a custom tag", dest="tags")
	parser.add_argument("-f", "--force", action="store_true", help="overwrite existing subdirectories")
	parser.add_argument("-s", "--single", action="store_true", help="run even if all DICOM files belong to the same series")
	parser.add_argument("-v", "--verbose", action="store_true", help="print actions")
	args = parser.parse_args()
	split(args.path, tags=args.tags, move=args.move, force=args.force, single=args.single, verbose=args.verbose)
