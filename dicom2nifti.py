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

# read first and last DICOM files
dicom1 = pydicom.dcmread(dicoms[0], stop_before_pixels=True)
dicom2 = pydicom.dcmread(dicoms[-1], stop_before_pixels=True)

# TODO datatype
DT = numpy.int16

# build DICOM affine
csa_image_header_info = csa2.decode(dicom1[0x0029, 0x1010].value)
if csa_image_header_info["NumberOfImagesInMosaic"]["Data"]:
	nslices = int(csa_image_header_info["NumberOfImagesInMosaic"]["Data"][0]);
else:
	nslices = 1;
X = numpy.array(dicom1.ImageOrientationPatient[0:3])
Y = numpy.array(dicom1.ImageOrientationPatient[3:6])
T = numpy.array(dicom1.ImagePositionPatient)
if nslices > 1:
	# http://nipy.org/nibabel/dicom/dicom_mosaic.html
	nblocks = math.ceil(math.sqrt(nslices))
	L = numpy.array([dicom1.Columns//nblocks, dicom1.Rows//nblocks, nslices, len(dicoms)])
	S = numpy.flip(numpy.array(dicom1.PixelSpacing))
	S = numpy.append(S, [
		dicom1.SpacingBetweenSlices if "SpacingBetweenSlices" in dicom1 else dicom1.SliceThickness,
		dicom1.RepetitionTime / 1000,
	])
	Z = numpy.array(csa_image_header_info["SliceNormalVector"]["Data"][0:3]).astype(float)
	T += numpy.column_stack((X, Y)) * S[0:2] @ (numpy.array([dicom1.Columns, dicom1.Rows]) - L[0:2]) / 2
else:
	L = numpy.array([dicom1.Columns, dicom1.Rows, len(dicoms)])
	S = numpy.flip(numpy.array(dicom1.PixelSpacing))
	Z = (numpy.array(dicom2.ImagePositionPatient) - numpy.array(dicom1.ImagePositionPatient)) \
		/ (dicom2.InstanceNumber - dicom1.InstanceNumber);
	S = numpy.append(S, numpy.linalg.norm(Z))
	Z /= S[2]

# calculate NIfTI affine
R = numpy.column_stack((X, Y, Z))
# convert DICOM LPS to NIfTI RAS coordinate system
R[0:2, :] *= -1
T[0:2] *= -1
affine = numpy.concatenate((R * S[0:3], T[numpy.newaxis].T), axis=1)
affine = numpy.concatenate((affine, numpy.array([0, 0, 0, 1])[numpy.newaxis]), axis=0)

# build NIfTI image
tags = [
	"InstanceNumber",
	"BitsAllocated", "Rows", "Columns", "PixelRepresentation", "SamplesPerPixel", "PixelData"
]
slice_times = [];
data = numpy.zeros(L, DT)
for f in range(L[-1]):
	print("reading [{}/{}] DICOM file {}".format(str(f + 1).rjust(math.floor(math.log10(L[-1]) + 1)), L[-1], dicoms[f]))
	dicom = pydicom.dcmread(dicoms[f], specific_tags=tags)
	data_slice = dicom.pixel_array
	if nslices > 1:
		jinc = L[1]
		jbeg, jend = 0, jinc
		iinc = L[0]
		ibeg, iend = 0, iinc
		for k in range(L[2]):
			data[:, :, k, dicom.InstanceNumber - 1] = data_slice[jbeg:jend, ibeg:iend].T
			ibeg, iend = ibeg + iinc, iend + iinc
			if iend > dicom1.Columns:
				ibeg, iend = 0, iinc
				jbeg, jend = jbeg + jinc, jend + jinc
	else:
		data[:, :, dicom.InstanceNumber - 1] = data_slice.T

nifti = nibabel.Nifti1Image(data, affine)

# build NIfTI header
# https://brainder.org/2012/09/23/the-nifti-file-format/
nifti.header["regular"] = b"r" # unused
# NOTE dim_info
if dicom1.InPlanePhaseEncodingDirection == "COL":
	nifti.header.set_dim_info(freq=0, phase=1, slice=2)
elif dicom1.InPlanePhaseEncodingDirection == "ROW":
	nifti.header.set_dim_info(freq=1, phase=0, slice=2)
else:
	nifti.header.set_dim_info(slice=2)
# NOTE pixdim[4], pixdim[7]
nifti.header.set_zooms(S)
# TODO slice_start, slice_end, slice_code, slice_duration
nifti.header.set_xyzt_units("mm", "sec")
nifti.header["glmax"] = 255    # unused, normally data.max()
nifti.header["glmin"] = 0      # unused, normally data.min()
# NOTE descrip
# NOTE qform_code, sform_code

# apply default NIfTI transformation
ornt = numpy.array([[0, 1], [1, -1], [2, 1]])
if numpy.linalg.det(R) < 0:
	ornt[2, 1] = -1
nifti = nifti.as_reoriented(ornt)

# save NIfTI object
dst_path = os.path.join(args.dir, datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ".nii.gz")
assert not os.path.exists(dst_path)
print("writing NIfTI file {}".format(dst_path))
nibabel.save(nifti, dst_path)

print("complete")
