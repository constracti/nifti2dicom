# nifti2dicom

reconstruct DICOM files given one NIfTI and two DICOM files

## Dependencies

1. [Python 3.x](https://www.python.org/)
2. [NumPy](http://www.numpy.org/)
   > NumPy is the fundamental package for scientific computing with Python.
   ```
   pip3 install numpy
   ```
3. [NiBabel](http://nipy.org/nibabel/)
   > Read / write access to some common neuroimaging file formats.
   ```
   pip3 install nibabel
   ```
4. [Pydicom](https://pydicom.github.io/)
   > Pydicom is a pure Python package for working with DICOM files such as medical images, reports, and radiotherapy objects.
   ```
   pip3 install pydicom
   ```

## Usage

### dicom2nifti

Collect all DICOM files from directory `dir` and create a NIfTI file in the same directory.

```
./dicom2nifti.py dir
```

At least two DICOM files must be present in the directory.

### nifti2dicom

Collect all NIfTI files from directory `src` and create a subdirectory with DICOM files for each of them.
`src` can also be a NIfTI file, in which case only that NIfTI file will be taken into account.

```
./nifti2dicom.py src
```

At least two DICOM files must be present in the directory of the NIfTI files.

## Tools

### dicomsplit

Place each DICOM file in a subdirectory according to Protocol Name.

```
./dicomsplit.py [-m] [-f] [-v] path
```

#### positional arguments:

* `path`
   directory of mixed DICOM files

#### optional arguments:

* `-m`, `--help`
  move files instead of copying
* `-f`, `--force`
  overwrite existing subdirectories
* `-v`, `--verbose`
  print actions

### dicomdiff

Print the difference of the headers between two DICOM files.

```
./dicomdiff.py dcm1 dcm2
```

### dicomcmp

Compare data of all corresponding DICOM files in two directories.

```
./dicomcmp.py [-v] dir1 dir2
```

Returns 0 on success or 1 on failure.

Include `--verbose` (`-v`) to print the result of each comparison.

### niftidiff

Print the difference of the headers between two NIfTI files.

```
./niftidiff.py nii1 nii2
```

### nifticmp

Compare data of two NIfTI files.

```
./nifticmp.py nii1 nii2
```

Returns 0 on success or 1 on failure.

## References

* [Defining the DICOM orientation](http://nipy.org/nibabel/dicom/dicom_orientation.html)
* [Siemens mosaic format](http://nipy.org/nibabel/dicom/dicom_mosaic.html)
* [Siemens format DICOM with CSA header](http://nipy.org/nibabel/dicom/siemens_csa.html)
* [The NIFTI file format](https://brainder.org/2012/09/23/the-nifti-file-format/)
* [NIfTI conversion, visualization and transformation tools](https://www.mathworks.com/matlabcentral/fileexchange/42997-xiangruili-dicm2nii)
