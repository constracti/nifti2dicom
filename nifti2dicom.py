# python -i nifti2dicom.py T1_MPRAGE_TRA_ISO_0012
# python -i nifti2dicom.py T2_SPACE_DARK-FLUID_SAG_ISO_0011
# python -i nifti2dicom.py T1_BLADE_DARK-FLUID_COR_0018
# python -i nifti2dicom.py FMRI_RS_S4_2MM_0007

import argparse
import os
import re
import numpy
import nibabel
import pydicom

import csa2

parser = argparse.ArgumentParser()
parser.add_argument("src", help="source NIfTI file")
args = parser.parse_args()

# find NIfTI file
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

# parse NIfTI header
nii = nibabel.load(src)
L0 = nii.get_shape()
A0 = nii.get_affine()

# find DICOM files
dcm1 = None
dcm2 = None
src_dir = os.path.dirname(src)
for file in os.listdir(src_dir):
	if re.search("\.(?:dcm|ima)$", file, re.I) is not None:
		if dcm1 is None:
			dcm1 = os.path.join(src_dir, file)
		else:
			dcm2 = os.path.join(src_dir, file)

# parse DICOM headers
dcm1dataset = pydicom.filereader.dcmread(dcm1, stop_before_pixels=True)
dcm2dataset = pydicom.filereader.dcmread(dcm2, stop_before_pixels=True)

# parse DICOM affine
csa_image_header_info = csa2.decode(dcm1dataset[0x0029, 0x1010].value)
if csa_image_header_info["NumberOfImagesInMosaic"]["Data"]:
	nslices = int(csa_image_header_info["NumberOfImagesInMosaic"]["Data"][0]);
else:
	nslices = 1;
Xxyz = numpy.array(list(map(float, dcm1dataset.ImageOrientationPatient[0:3])))
Yxyz = numpy.array(list(map(float, dcm1dataset.ImageOrientationPatient[3:6])))
Sxyz = numpy.flip(numpy.array(list(map(float, dcm1dataset.PixelSpacing))))
if nslices > 1:
	Zxyz = numpy.array(list(map(float, csa_image_header_info["SliceNormalVector"]["Data"][0:3])))
	Sxyz = numpy.append(float(dcm1dataset.SliceThickness))
else:
	Zxyz = (numpy.array(list(map(float, dcm2dataset.ImagePositionPatient))) \
		- numpy.array(list(map(float, dcm1dataset.ImagePositionPatient)))) \
		/ (float(dcm2dataset.InstanceNumber) - float(dcm1dataset.InstanceNumber))
	Sxyz = numpy.append(Sxyz, numpy.linalg.norm(Zxyz))
	Zxyz /= Sxyz[2]

# calculate NIfTI target affine
Rxyz = numpy.column_stack((Xxyz, Yxyz, Zxyz)) * Sxyz
Rxyz[0:2,:] *= -1
Axyz = numpy.concatenate((Rxyz, numpy.zeros(3)[numpy.newaxis].T), axis=1)
Axyz = numpy.concatenate((Axyz, numpy.array([0, 0, 0, 1])[numpy.newaxis]), axis=0)

# prepare NIfTI image
C = numpy.linalg.solve(Axyz, A0)
ornt = nibabel.io_orientation(C)
nii = nii.as_reoriented(ornt)
