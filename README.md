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
5. (recommended) [Unidecode](https://pypi.org/project/Unidecode/)
   > ASCII transliterations of Unicode text.
   ```
   pip3 install unidecode
   ```

## Usage

### dicom2nifti

Split directory by series in case DICOM files belong to different series (files are copied).

Then, convert each set of DICOM files to a NIfTI file.

```
./dicom2nifti.py PATH
```

#### positional arguments:

1. `PATH`
    directory of DICOM files

#### optional arguments:

* `-o`, `--orient`
  orient output NIFTI file

Each series must contain at least two DICOM files.

### nifti2dicom

Convert each NIfTI file in a directory to a set of DICOM files.

```
./nifti2dicom.py PATH
```

#### positional arguments:

1. `PATH`
   directory of NIfTI files or path of a NIfTI file

At least two DICOM files must be present in the directory of the NIfTI files.

In case `path` holds the path of a NIfTI file, only that NIfTI file will be taken into account.

## Tools

### dicomsplit

Place each DICOM file in a subdirectory according to Protocol Name and Series Number.

```
./dicomsplit.py [-m] [-f] [-v] PATH
```

#### positional arguments:

1. `PATH`
   directory of mixed DICOM files

#### optional arguments:

* `-m`, `--move`
  move files instead of copying
* `-f`, `--force`
  overwrite existing subdirectories
* `-s`, `--single`
  run even if all DICOM files belong to the same series
* `-v`, `--verbose`
  print actions

### dicomtable

Output a table with the variable fields of a DICOM set as a CSV.

```
./dicomtable.py PATH
```

#### positional arguments:

1. `PATH`
   directory of DICOM files

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

#### optional arguments:

* `-v`, `--verbose`
  print the result of each comparison

#### return values:

* `0` on success
* `1` on failure

### niftitools-header

Output the header of a NIfTI file.

```
./niftitools.py header PATH
```

#### positional arguments:

1. `PATH`
   path to the NIfTI file

### niftitools-affine

Output the affine of a NIfTI file.

```
./niftitools.py affine PATH
```

#### positional arguments:

1. `PATH`
   path to the NIfTI file

### niftitools-orient

Orient a NIfTI file.

```
./niftitools.py orient [-o OUTPATH] [-d] INPATH
```

#### positional arguments:

1. `INPATH`
   path to the input NIfTI file

#### optional arguments:

* `-o OUTPATH`, `--outpath OUTPATH`
  path to the output NIfTI file; default INPATH-oriented
* `-d`, `--diagonal`
  apply orientation only if resulting affine is close to diagonal

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

#### return values:

* `0` on success
* `1` on failure

## References

* [Defining the DICOM orientation](http://nipy.org/nibabel/dicom/dicom_orientation.html)
* [Siemens mosaic format](http://nipy.org/nibabel/dicom/dicom_mosaic.html)
* [Siemens format DICOM with CSA header](http://nipy.org/nibabel/dicom/siemens_csa.html)
* [The NIFTI file format](https://brainder.org/2012/09/23/the-nifti-file-format/)
* [NIfTI conversion, visualization and transformation tools](https://www.mathworks.com/matlabcentral/fileexchange/42997-xiangruili-dicm2nii)
