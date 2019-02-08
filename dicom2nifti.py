import argparse
import os
import re
import datetime
import math
import numpy

import pydicom
import nibabel

import csa2

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("dir", help="directory of source DICOM files")
args = parser.parse_args()

# find DICOM files
assert os.path.isdir(args.dir), "{} is not a directory".format(args.dir)

dicoms = []
for file in os.listdir(args.dir):
	if re.search("\.(?:dcm|ima)$", file, flags=re.I):
		dicoms.append(os.path.join(args.dir, file))
assert len(dicoms) >= 2, "{} does not contain at least two DICOM files".format(args.dir)

# select first and last DICOM files in the directory
dataset1 = pydicom.dcmread(dicoms[0], stop_before_pixels=True)
dataset2 = pydicom.dcmread(dicoms[-1], stop_before_pixels=True)

# TODO datatype
DT = numpy.int16

# build DICOM affine
csa_image_header_info = csa2.decode(dataset1[0x0029, 0x1010].value)
if csa_image_header_info["NumberOfImagesInMosaic"]["Data"]:
	nslices = int(csa_image_header_info["NumberOfImagesInMosaic"]["Data"][0]);
else:
	nslices = 1;
X = numpy.array(dataset1.ImageOrientationPatient[0:3])
Y = numpy.array(dataset1.ImageOrientationPatient[3:6])
T = numpy.array(dataset1.ImagePositionPatient)
if nslices > 1:
	# http://nipy.org/nibabel/dicom/dicom_mosaic.html
	nblocks = math.ceil(math.sqrt(nslices))
	L = numpy.array([dataset1.Columns//nblocks, dataset1.Rows//nblocks, nslices, len(dicoms)])
	S = numpy.flip(numpy.array(dataset1.PixelSpacing))
	S = numpy.append(S, [
		dataset1.SpacingBetweenSlices if "SpacingBetweenSlices" in dataset1 else dataset1.SliceThickness,
		dataset1.RepetitionTime / 1000,
	])
	Z = numpy.array(csa_image_header_info["SliceNormalVector"]["Data"][0:3]).astype(float)
	T += numpy.column_stack((X, Y)) * S[0:2] @ (numpy.array([dataset1.Columns, dataset1.Rows]) - L[0:2]) / 2
else:
	L = numpy.array([dataset1.Columns, dataset1.Rows, len(dicoms)])
	S = numpy.flip(numpy.array(dataset1.PixelSpacing))
	Z = (numpy.array(dataset2.ImagePositionPatient) - numpy.array(dataset1.ImagePositionPatient)) \
		/ (dataset2.InstanceNumber - dataset1.InstanceNumber);
	S = numpy.append(S, numpy.linalg.norm(Z))
	Z /= S[2]

# calculate NIfTI affine
R = numpy.column_stack((X, Y, Z))
# convert DICOM LPS to NIfTI RAS coordinate system
R[0:2, :] *= -1
T[0:2] *= -1
A = numpy.concatenate((R * S[0:3], T[numpy.newaxis].T), axis=1)
A = numpy.concatenate((A, numpy.array([0, 0, 0, 1])[numpy.newaxis]), axis=0)

# build NIfTI image
data = numpy.zeros(L, DT)
tags = ["BitsAllocated", "Rows", "Columns", "PixelRepresentation", "SamplesPerPixel", "PixelData"]
if nslices > 1:
	for t in range(L[3]):
		data_slice = pydicom.dcmread(dicoms[t], specific_tags=tags).pixel_array
		jinc = L[1]
		jbeg, jend = 0, jinc
		iinc = L[0]
		ibeg, iend = 0, iinc
		for k in range(L[2]):
			data[:, :, k, t] = data_slice[jbeg:jend, ibeg:iend].T
			ibeg, iend = ibeg + iinc, iend + iinc
			if iend > dataset1.Columns:
				ibeg, iend = 0, iinc
				jbeg, jend = jbeg + jinc, jend + jinc
else:
	for k in range(L[2]):
		data_slice = pydicom.dcmread(dicoms[k], specific_tags=tags).pixel_array
		data[:, :, k] = data_slice.T

nifti = nibabel.Nifti1Image(data, A)

# TODO header

# apply default NIfTI transformation
ornt = numpy.array([[0, 1], [1, -1], [2, 1]])
if numpy.linalg.det(R) < 0:
	ornt[2, 1] = -1
nifti = nifti.as_reoriented(ornt)

# save NIfTI object
dst_path = os.path.join(args.dir, datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ".nii.gz")
assert not os.path.exists(dst_path)
nibabel.save(nifti, dst_path)
