function dicomimage(dicom)
%DICOMIMAGE Display a DICOM file in grayscale
if isstruct(dicom)
    dicom = dicomread(dicom.Filename);
elseif ~isnumeric(dicom)
    dicom = dicomread(dicom);
end
image(dicom, 'CDataMapping', 'scaled');
colormap('gray');
end
