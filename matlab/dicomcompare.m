function result = dicomcompare(dicom1, dicom2)
if (isstring(dicom1) && isscalar(dicom1) || ischar(dicom1) && isrow(dicom1)) && isfolder(dicom1)
    dicom1 = dir2ff(dicom1);
end
if (isstring(dicom2) && isscalar(dicom2) || ischar(dicom2) && isrow(dicom2)) && isfolder(dicom2)
    dicom2 = dir2ff(dicom2);
end
assert(length(dicom1) == length(dicom2));
result = true;
for i = 1:length(dicom1)
    if ~isequal(dicomread(dicom1(i)), dicomread(dicom2(i)))
        result = false;
        break
    end
end
end
