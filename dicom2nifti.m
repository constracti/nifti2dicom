function [hdr, img] = dicom2nifti(dicoms)
%DICOM2NIFTI Convert DICOM files to NIfTI header and image
%% obtain dicom headers
if isstring(dicoms) && isscalar(dicoms) && isfolder(dicoms)
    dicoms = dir2ff(dicoms);
elseif ischar(dicoms) && isrow(dicoms) && isfolder(dicoms)
    dicoms = dir2ff(dicoms);
end
if isstruct(dicoms)
    dicom1 = dicoms(1);
    dicom2 = dicoms(end);
else
    dicom1 = dicominfo(dicoms(1));
    dicom2 = dicominfo(dicoms(end));
end
csa = csa2(dicom1.Private_0029_1010);
if isempty(csa.NumberOfImagesInMosaic.Data)
    n_slices = 1;
else
    n_slices = str2double(csa.NumberOfImagesInMosaic.Data{1});
end
%% TODO nifti datatype
switch dicom1.BitsAllocated
    otherwise
        DT = 'int16';
end
%% dicom affine
Xxyz = dicom1.ImageOrientationPatient(1:3);
Yxyz = dicom1.ImageOrientationPatient(4:6);
Txyz = dicom1.ImagePositionPatient;
if n_slices > 1
    % http://nipy.org/nibabel/dicom/dicom_mosaic.html
    n_blocks = ceil(sqrt(n_slices));
    L = zeros(4, 1);
    L(1:2) = [dicom1.Columns; dicom1.Rows] / n_blocks;
    L(3) = n_slices;
    L(4) = length(dicoms);
    S = zeros(4, 1);
    S(1:2) = flip(dicom1.PixelSpacing);
    if isfield(dicom1, 'SpacingBetweenSlices')
        S(3) = dicom1.SpacingBetweenSlices;
    else
        S(3) = dicom1.SliceThickness;
    end
    S(4) = dicom1.RepetitionTime / 1000;
    Zxyz = cellfun(@str2num,csa.SliceNormalVector.Data(1:3));
    Txyz = Txyz + [Xxyz, Yxyz] * diag(S(1:2)) * (double([dicom1.Columns; dicom1.Rows]) - L(1:2)) / 2;
else
    L = zeros(3, 1);
    L(1:2) = [dicom1.Columns; dicom1.Rows];
    L(3) = length(dicoms);
    S = zeros(3, 1);
    S(1:2) = flip(dicom1.PixelSpacing);
    Zxyz = (dicom2.ImagePositionPatient - dicom1.ImagePositionPatient) /...
        (dicom2.InstanceNumber - dicom1.InstanceNumber);
    S(3) = norm(Zxyz);
    Zxyz = Zxyz / S(3);
end
%% nifti affine
R = [Xxyz, Yxyz, Zxyz];
T = Txyz;
R(1:2, :) = -R(1:2, :);
T(1:2) = -T(1:2);
%% nifti image
img = zeros(L', DT);
if n_slices > 1
    for t = 1:L(4)
        dicomimg = dicomread(dicoms(t));
        jstp = L(2);
        jbeg = 1;
        jend = jstp;
        istp = L(1);
        ibeg = 1;
        iend = istp;
        for k = 1:L(3)
            img(:, :, k, t) = dicomimg(jbeg:jend, ibeg:iend)';
            ibeg = ibeg + istp;
            iend = iend + istp;
            if iend > dicom1.Columns
                ibeg = 1;
                iend = istp;
                jbeg = jbeg + jstp;
                jend = jend + jstp;
            end
        end
    end
else
    for k = 1:L(3)
        dicomimg = dicomread(dicoms(k));
        img(:, :, k) = dicomimg';
    end
end
%% nifti header
hdr = struct();
hdr.Description = ''; % multiple sources
hdr.ImageSize = L';
hdr.PixelDimensions = S';
hdr.Datatype = DT;
hdr.SpaceUnits = 'Millimeter';
hdr.TimeUnits = 'Second';
% nifti.AdditiveOffset = 0;
% nifti.MultiplicativeScaling = 1;
hdr.SliceCode = 'Sequential-Increasing';
hdr.SliceStart = 0;
hdr.SliceEnd = L(3) - 1;
hdr.SliceDuration = 0; % ignore this field
% nifti.TimeOffset = 0;
% nifti.DisplayIntensityRange = [0 0]; % ignore this field
hdr.TransformName = 'Sform';
hdr.Transform = affine3d([
    (R * diag(S(1:3)))', zeros(3, 1);
    T', 1;
]);
hdr.Qfactor = sign(det(R)); % ignore this field
switch dicom1.InPlanePhaseEncodingDirection
    case 'COL'
        hdr.FrequencyDimension = 1;
        hdr.PhaseDimension = 2;
        hdr.SpatialDimension = 3;
    case 'ROW'
        hdr.FrequencyDimension = 2;
        hdr.PhaseDimension = 1;
        hdr.SpatialDimension = 3;
    otherwise
        hdr.FrequencyDimension = 0;
        hdr.PhaseDimension = 0;
        hdr.SpatialDimension = 3;
end
end
