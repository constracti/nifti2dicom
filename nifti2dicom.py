import argparse
import os
import copy
import re
import datetime
import math
import numpy
import nibabel
import pydicom

import csa2
import dicomtools

parser = argparse.ArgumentParser()
parser.add_argument("src", help="source NIfTI file")
args = parser.parse_args()

# find NIfTI file
if os.path.isfile(args.src):
	assert re.search("\.nii(?:\.gz)$", args.src, flags=re.I), "file {} is not a NIfTI file".format(args.src)
	src = args.src
elif os.path.isdir(args.src):
	# select the first NIfTI file in the directory
	src = None
	for file in os.listdir(args.src):
		if re.search("\.nii(?:\.gz)$", file, flags=re.I):
			src = os.path.join(args.src, file)
			break
	assert src, "no NIfTI file found in directory {}".format(args.src)
else:
	assert False, "provide a NIfTI file"

# find DICOM files
# select first and last DICOM files in the directory of the NIfTI file
dcm1 = None
dcm2 = None
src_dir = os.path.dirname(src)
for file in os.listdir(src_dir):
	if re.search("\.(?:dcm|ima)$", file, flags=re.I):
		if dcm1 is None:
			dcm1 = os.path.join(src_dir, file)
		else:
			dcm2 = os.path.join(src_dir, file)

# read DICOM datasets
# stop before (7fe0, 0010) Pixel Data
# and         (fffc, fffc) Data Set Trailing Padding
ds1 = pydicom.dcmread(dcm1, stop_before_pixels=True)
ds2 = pydicom.dcmread(dcm2, stop_before_pixels=True)

# build DICOM affine
# http://nipy.org/nibabel/dicom/dicom_orientation.html
csa_image_header_info = csa2.decode(ds1[0x0029, 0x1010].value)
if csa_image_header_info["NumberOfImagesInMosaic"]["Data"]:
	nslices = int(csa_image_header_info["NumberOfImagesInMosaic"]["Data"][0]);
else:
	nslices = 1;
Xxyz = numpy.array(ds1.ImageOrientationPatient[0:3])
Yxyz = numpy.array(ds1.ImageOrientationPatient[3:6])
Sxyz = numpy.flip(numpy.array(ds1.PixelSpacing))
if nslices > 1:
	Zxyz = numpy.array(csa_image_header_info["SliceNormalVector"]["Data"][0:3]).astype(float)
	Sxyz = numpy.append(Sxyz, ds1.SliceThickness)
else:
	Zxyz = (numpy.array(ds2.ImagePositionPatient) \
		- numpy.array(ds1.ImagePositionPatient)) \
		/ (ds2.InstanceNumber - ds1.InstanceNumber)
	Sxyz = numpy.append(Sxyz, numpy.linalg.norm(Zxyz))
	Zxyz /= Sxyz[2]

# calculate corresponding NIfTI affine
Rxyz = numpy.column_stack((Xxyz, Yxyz, Zxyz)) * Sxyz
# convert DICOM LPS to NIfTI RAS coordinate system
Rxyz[0:2,:] *= -1
# ignore translation part of affine transformation
Rxyz = numpy.concatenate((Rxyz, numpy.zeros(3)[numpy.newaxis].T), axis=1)
Rxyz = numpy.concatenate((Rxyz, numpy.array([0, 0, 0, 1])[numpy.newaxis]), axis=0)

# reorient NIfTI image
nii = nibabel.load(src)
C = numpy.linalg.solve(Rxyz, nii.get_affine())
ornt = nibabel.io_orientation(C)
del C
nii = nii.as_reoriented(ornt)
L = nii.get_shape()
# prepare DICOM pixel data by transposing NIfTI data
data = numpy.asarray(nii.dataobj).swapaxes(0, 1)

# prepare common DICOM dataset
ds0 = copy.deepcopy(ds1)
del ds0.WindowCenter, ds0.WindowWidth, ds0.WindowCenterWidthExplanation
ds0.ProtocolName = re.sub("\.nii(?:\.gz)$", "", os.path.split(src)[-1], flags=re.I) # customization
ds0.SeriesInstanceUID = pydicom.uid.generate_uid() # customization

# save DICOM files
dst_dir = os.path.join(src_dir, ds0.ProtocolName + datetime.datetime.now().strftime("-%Y%m%d%H%M%S"))
assert not os.path.exists(dst_dir)
os.mkdir(dst_dir)
print("writing {} files in {}".format(L[-1], dst_dir))
if nslices > 1:
	assert False, "TODO Siemens mosaic"
else:
	for k in range(L[2]):
		dst = os.path.join(dst_dir, str(k).zfill(math.floor(math.log10(L[2])) + 1) + ".dcm")
		ds0.InstanceNumber = k + 1
		dicomtools.linear_datetime(["InstanceCreation", "Acquisition", "Content"], ds0, ds1, ds2)
		dicomtools.linear_float_array((0x0019, 0x1015), ds0, ds1, ds2)   # [SlicePosition_PCS]
		if (0x0019, 0x1016) in ds0:
			dicomtools.linear_float((0x0019, 0x1016), ds0, ds1, ds2) # [TimeAfterStart]
		dicomtools.linear_float_array((0x0020, 0x0032), ds0, ds1, ds2)   # Image Position (Patient)
		dicomtools.linear_float((0x0020, 0x1041), ds0, ds1, ds2)         # Slice Location
		data_slice = data[:,:,k]
		ds0.SmallestImagePixelValue = data_slice.min()                   # (0028, 0106)
		ds0.LargestImagePixelValue = data_slice.max()                    # (0028, 0107)
		# NOTE (0x0029, 0x1010) CSA Image Header Info
		# NOTE (0x0051, 0x100d), e.g. SP A116.1 and SP P72.4
		# add pixel data
		# assuming data.dtype.itemsize == 2; thus VR="OW" (Other Word) and not "OB" (Other Byte)
		# http://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.7.6.3.html
		# http://dicom.nema.org/medical/dicom/current/output/chtml/part05/sect_6.2.html
		ds0.add_new((0x7fe0, 0x0010), "OW",  data_slice.tobytes())       # Pixel Data
		# NOTE (0xfffc, 0xfffc) Data Set Trailing Padding
		pydicom.dcmwrite(dst, ds0)
		print("file {} out of {} written".format(k + 1, L[2]))
