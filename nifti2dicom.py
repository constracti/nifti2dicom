# python -i nifti2dicom.py T1_MPRAGE_TRA_ISO_0012

import argparse
import os
import re
import pydicom

parser = argparse.ArgumentParser()
parser.add_argument("src", help="source NIfTI file")
args = parser.parse_args()

if os.path.isfile(args.src):
	assert args.src.endswith((".nii", ".nii.gz")), "file {} is not a NIfTI file".format(args.src)
	src = args.src
elif os.path.isdir(args.src):
	# select the first NIfTI file in the directory
	src = None
	for file in os.listdir(args.src):
		if file.endswith((".nii", ".nii.gz")):
			src = os.path.join(args.src, file)
			break
	assert src is not None, "no NIfTI file found in directory {}".format(args.src)
else:
	assert False, "provide a NIfTI file"

dcm1 = None
dcm2 = None
src_dir = os.path.dirname(src)
for file in os.listdir(src_dir):
	if re.search("\.(?:dcm|ima)$", file, re.I) is not None:
		if dcm1 is None:
			dcm1 = os.path.join(src_dir, file)
		else:
			dcm2 = os.path.join(src_dir, file)

dcm1dataset = pydicom.filereader.dcmread(dcm1, stop_before_pixels=True)
