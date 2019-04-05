#!/usr/bin/python3

import argparse
import os
import shutil

import pydicom

parser = argparse.ArgumentParser(description="Place each DICOM file in a subdirectory according to Protocol Name.")
parser.add_argument("path", help="directory of mixed DICOM files")
parser.add_argument("-m", "--move", action="store_true", help="move files instead of copying")
parser.add_argument("-f", "--force", action="store_true", help="overwrite existing subdirectories")
parser.add_argument("-v", "--verbose", action="store_true", help="print actions")
args = parser.parse_args()

assert os.path.isdir(args.path), "path {} is not a directory".format(args.path)

def _get_protocol_name(file):
	try:
		dataset = pydicom.dcmread(file, specific_tags=["ProtocolName"])
		return dataset.ProtocolName
	except pydicom.errors.InvalidDicomError:
		return None

files = [(f, os.path.join(args.path, f)) for f in os.listdir(args.path)]
files = [(f[0], f[1], _get_protocol_name(f[1])) for f in files if os.path.isfile(f[1])]
files = [f for f in files if f[2] is not None]

protocolnames = set([f[2] for f in files])
if args.verbose:
	print("found {} DICOM files with {} different protocol names".format(len(files), len(protocolnames)))

if not args.force:
	for protocolname in protocolnames:
		path = os.path.join(args.path, protocolname)
		assert not os.path.isfile(path), "file {} exists".format(protocolname)
		assert not os.path.isdir(path), "directory {} exists".format(protocolname)

for protocolname in protocolnames:
	path = os.path.join(args.path, protocolname)
	if os.path.isfile(path):
		if args.verbose:
			print("removing file {}".format(protocolname))
		os.remove(path)
	elif os.path.isdir(path):
		if args.verbose:
			print("removing directory {}".format(protocolname))
		shutil.rmtree(path)
	if args.verbose:
		print("creating directory {}".format(protocolname))
	os.mkdir(path)

for filename, filepath, protocolname in files:
	path = os.path.join(args.path, protocolname, filename)
	if args.move:
		if args.verbose:
			print("moving file {} to directory {}".format(filename, protocolname))
		shutil.move(filepath, path)
	else:
		if args.verbose:
			print("copying file {} to directory {}".format(filename, protocolname))
		shutil.copy2(filepath, path)

if args.verbose:
	print("complete")
