# nifti2dicom
reconstruct DICOM files given one NIfTI and two DICOM files

## Dependencies
1. [Python 3.x](https://www.python.org/)
   > Python is a programming language that lets you work quickly and integrate systems more effectively.
2. [NumPy](http://www.numpy.org/)
   > NumPy is the fundamental package for scientific computing with Python.
   ```
   pip install numpy
   ```
3. [NiBabel](http://nipy.org/nibabel/)
   > Read / write access to some common neuroimaging file formats.
   ```
   pip install nibabel
   ```

## Parse a directory
```matlab
[dicoms, nifti] = dir2ff(directory);
```
The `directory` contents are analyzed.
Subdirectories are excluded.
Files with .dcm or .ima extensions are recognized as DICOM and appended to the `dicoms` string array.
Files with .nii or .nii.gz extensions are recognized as NIfTI and returned as the `nifti` string.

## The NIfTI structure
Let's say that variable `nifti` is the path to a NIfTI file. Then, the corresponding NIfTI structure could be obtained with the following procedure:
```matlab
nifti = niftiinfo(nifti);
nifti.img = niftiread(nifti.Filename);
```
After the execution of this block of code, `nifti` holds a structure like the one returned by [niftiinfo](https://www.mathworks.com/help/images/ref/niftiinfo.html).
Additionally, it has a field `nifti.img` containing the image data that would be returned by [niftiread](https://www.mathworks.com/help/images/ref/niftiread.html).

## Convert DICOM files to NIfTI structure
```matlab
nifti = dicom2nifti(dicoms);
```

## Convert NIfTI structure to DICOM files
```matlab
filepath = nifti2dicom(nifti, dicom1, dicom2);
```

## DICOM helper functions
* `dicomcompare` compares the images of two set of DICOM files
* `dicomdiff` prints the difference between two DICOM headers
* `dicomimage` displays a DICOM file in grayscale

## NIfTI helper functions
* `niftiflip` flips a NIfTI structure along specific dimensions
* `niftipermute` permutes a NIfTI structure in a specific order
* `niftiorient` orients a NIfTI structure

## References
* [Defining the DICOM orientation](http://nipy.org/nibabel/dicom/dicom_orientation.html)
* [Siemens mosaic format](http://nipy.org/nibabel/dicom/dicom_mosaic.html)
* [Siemens format DICOM with CSA header](http://nipy.org/nibabel/dicom/siemens_csa.html)
* [NIfTI conversion, visualization and transformation tools](https://www.mathworks.com/matlabcentral/fileexchange/42997-xiangruili-dicm2nii)
