# nifti2dicom
reconstruct DICOM files given one NIfTI and two DICOM files

## Convert DICOM files to NIfTI header and image:
```matlab
[hdr, img] = dicom2nifti(directory);
[hdr, img] = niftiflip(hdr, img, [false, true, false]); % axial and coronal
[hdr, img] = niftiflip(hdr, img, [false, true, true]); % sagittal
```

## Orient a NIfTI header and image
```matlab
[hdr, img] = niftiorient(hdr, img);
```
