#!/usr/bin/python3

import argparse
import os
import re

import nibabel

def file_is_valid(filename):
	if not os.path.isfile(filename):
		return False
	if re.search("\.nii(?:\.gz)$", filename, flags=re.I) is None:
		return False
	return True

def orient(nifti, outpath=None, diagonal=False):
	if type(nifti) is str:
		nifti = nibabel.load(nifti)
	nifti = nibabel.as_closest_canonical(nifti, diagonal)
	if outpath is not None:
		nibabel.save(nifti, outpath)
	return nifti

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	subparsers = parser.add_subparsers(dest="action", help="one of the following actions", metavar="ACTION")
	subparsers.required = True
	parser_header = subparsers.add_parser("header", description="Output the header of a NIfTI file.", help="output the header of a NIfTI file")
	parser_header.add_argument("path", help="path to the NIfTI file", metavar="PATH")
	parser_affine = subparsers.add_parser("affine", description="Output the affine of a NIfTI file.", help="output the affine of a NIfTI file")
	parser_affine.add_argument("path", help="path to the NIfTI file", metavar="PATH")
	parser_orient = subparsers.add_parser("orient", description="Orient a NIfTI file.", help="orient a NIfTI file")
	parser_orient.add_argument("inpath", help="path to the input NIfTI file", metavar="INPATH")
	parser_orient.add_argument("-o", "--outpath", help="path to the output NIfTI file; default INPATH-oriented")
	parser_orient.add_argument("-d", "--diagonal", action="store_true", help="apply orientation only if resulting affine is close to diagonal")
	args = parser.parse_args()
	if args.action == "header":
		nifti = nibabel.load(args.path)
		print(nibabel.volumeutils.pretty_mapping(nifti.get_header()))
	elif args.action == "affine":
		nifti = nibabel.load(args.path)
		print(nifti.get_affine())
	elif args.action == "orient":
		if args.outpath is None:
			args.outpath = re.sub("(\.nii(?:\.gz))$", "-oriented\\1", args.inpath, flags=re.I)
		orient(args.inpath, outpath=args.outpath, diagonal=args.diagonal)
