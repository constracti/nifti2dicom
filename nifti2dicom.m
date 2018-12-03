function filepath = nifti2dicom(nifti, dicom1, dicom2)
%NIFTITODICOM Convert a NIfTI image to DICOM
% TODO NIfTI SliceCode
% TODO NIfTI *Dimension
%% load NIfTI image
if ~isstruct(nifti)
    nifti = niftiinfo(nifti);
end
if ~isfield(nifti, 'img')
    nifti.img = niftiread(nifti.Filename);
end
%% parse NIfTI header
L0 = nifti.ImageSize';
S0 = nifti.PixelDimensions';
R0 = nifti.Transform.T(1:3, 1:3)' * diag(1 ./ S0(1:3));
%% parse DICOM headers
if ~isstruct(dicom1)
    dicom1 = dicominfo(dicom1);
end
if ~isstruct(dicom2)
    dicom2 = dicominfo(dicom2);
end
csa = csa2decode(dicom1.Private_0029_1010);
if isempty(csa.NumberOfImagesInMosaic.Data)
    n_slices = 1;
else
    n_slices = str2double(csa.NumberOfImagesInMosaic.Data{1});
end
%% parse DICOM affine
Xxyz = dicom1.ImageOrientationPatient(1:3);
Yxyz = dicom1.ImageOrientationPatient(4:6);
if n_slices > 1
    Zxyz = cellfun(@str2num,csa.SliceNormalVector.Data(1:3));
else
    Zxyz = (dicom2.ImagePositionPatient - dicom1.ImagePositionPatient) /...
        (dicom2.InstanceNumber - dicom1.InstanceNumber);
    Zxyz = Zxyz / norm(Zxyz);
end
%% calculate NIfTI target affine
R = [Xxyz, Yxyz, Zxyz];
R(1:2, :) = -R(1:2, :);
%% prepare NIfTI image
C = R \ R0;
P = zeros(1, 3);
Ctmp = abs(C);
for d = 1:3
    [~, P(d)] = max(Ctmp(:, d));
    Ctmp(P(d), :) = 0;
end
F = C(P + (0:3:6)) < 0;
Ctmp(P + (0:3:6)) = 1 - 2 * F;
assert(norm(C - Ctmp) < pow2(-6)); % use pow2(-6) instead of eps
nifti = niftiflip(nifti, F);
[~, P] = sort(P);
nifti = niftipermute(nifti, P);
L = L0;
L(1:3) = L(P);
%% prepare common DICOM header
hdr = dicom1;
% *ClassUID values are magically recalculated
hdr = rmfield(hdr, {'Filename', 'FileModDate', 'FileSize'}); % new values are assigned
hdr = rmfield(hdr, {'FileMetaInformationGroupLength', 'FileMetaInformationVersion'}); % values are recalculated;
hdr = rmfield(hdr, {'MediaStorageSOPInstanceUID', 'SOPInstanceUID'}); % new IDs are assigned
hdr = rmfield(hdr, {'SmallestImagePixelValue', 'LargestImagePixelValue'}); % values are recalculated
hdr = rmfield(hdr, {'WindowCenter', 'WindowWidth', 'WindowCenterWidthExplanation'}); % explanation is not included
hdr = rmfield(hdr, 'DataSetTrailingPadding'); % unknown purpose
hdr.ProtocolName = nifti2dicomProtocolName(nifti.Filename); % customization
hdr.SeriesInstanceUID = dicomuid(); % customization
%% save DICOM files
filepath  = fileparts(nifti.Filename);
filepath = fullfile(filepath, hdr.ProtocolName);
filepath = strcat(filepath, '-', datestr(now, 'yyyymmddHHMMSS'));
if exist(filepath, 'dir'), rmdir(filepath, 's'); end
mkdir(filepath);
fprintf('writing %d files in %s\n', L(end), filepath);
if n_slices > 1
    for t = 1:L(4)
        filename = fullfile(filepath, [pad(num2str(t - 1), floor(log10(L(4))) + 1, 'left', '0') '.dcm']);
        hdr.AcquisitionNumber = t;
        hdr.InstanceNumber = t;
        hdr = nifti2dicomDateTime({'InstanceCreation', 'Acquisition', 'Content'}, hdr, dicom1, dicom2);
        hdr = nifti2dicomValue('Private_0019_1016', hdr, dicom1, dicom2);
        csa.ICE_Dims.Data{1} = sprintf('X_1_1_1_%d_1_1_1_1_1_1_1_300\0', t);
        csa.TimeAfterStart.Data{1} = sprintf('%.8f\0', hdr.Private_0019_1016);
        hdr.Private_0029_1010 = csa2encode(csa);
        img = zeros(hdr.Rows, hdr.Columns, 'uint16');
        jinc = L(2);
        jbeg = 1;
        jend = jinc;
        iinc = L(1);
        ibeg = 1;
        iend = iinc;
        for k = 1:L(3)
            img(jbeg:jend, ibeg:iend) = nifti.img(:, :, k, t)';
            ibeg = ibeg + iinc;
            iend = iend + iinc;
            if iend > hdr.Columns
                ibeg = 1;
                iend = iinc;
                jbeg = jbeg + jinc;
                jend = jend + jinc;
            end
        end
        dicomwrite(img, filename, hdr, 'WritePrivate', true);
        fprintf('file %d out of %d written\n', t, L(4));
    end
else
    for k = 1:L(3)
        filename = fullfile(filepath, [pad(num2str(k - 1), floor(log10(L(3))) + 1, 'left', '0') '.dcm']);
        hdr.InstanceNumber = k;
        hdr = nifti2dicomDateTime({'InstanceCreation', 'Content'}, hdr, dicom1, dicom2);
        hdr = nifti2dicomValue({'ImagePositionPatient', 'SliceLocation', 'Private_0019_1015'}, hdr, dicom1, dicom2);
        % ImagePositionPatient = T + R(:, 3) * S(3) * (k - 1);
        % SliceLocation = R(:, 3)' * ImagePositionPatient
        % Private_0019_1015 = ImagePositionPatient
        img = zeros(hdr.Rows, hdr.Columns, 'uint16');
        img(:, :) = nifti.img(:, :, k)';
        dicomwrite(img, filename, hdr, 'WritePrivate', true);
        fprintf('file %d out of %d written\n', k, L(3));
    end
end
end

function name = nifti2dicomProtocolName(name)
% return NIfTI filename without path or extension
[~, name, ext] = fileparts(name);
name = [name ext];
name = regexprep(name, '\.nii(?:\.gz)?$', '', 'ignorecase');
end

function s0 = nifti2dicomValue(fns, s0, s1, s2)
if ischar(fns)
    fns = {fns};
end
for i = 1:length(fns)
    fn = fns{i};
    v1 = s1.(fn);
    v2 = s2.(fn);
    v0 = v1 + (v2 - v1) / (s2.InstanceNumber - s1.InstanceNumber) * (s0.InstanceNumber - s1.InstanceNumber);
    s0.(fn) = v0;
end
end

function s0 = nifti2dicomDateTime(fns, s0, s1, s2)
if ischar(fns)
    fns = {fns};
end
for i = 1:length(fns)
    fn = fns{i};
    date1 = s1.([fn 'Date']);
    time1 = s1.([fn 'Time']);
    date2 = s2.([fn 'Date']);
    time2 = s2.([fn 'Time']);
    dt1 = datetime([date1 time1], 'InputFormat','yyyyMMddHHmmss.SSSSSS');
    dt2 = datetime([date2 time2], 'InputFormat','yyyyMMddHHmmss.SSSSSS');
    dt0 = dt1 + (dt2 - dt1) / (s2.InstanceNumber - s1.InstanceNumber) * (s0.InstanceNumber - s1.InstanceNumber);
    dt0.Format = 'yyyyMMdd';
    s0.([fn 'Date']) = char(dt0);
    dt0.Format = 'HHmmss.SSSSSS';
    s0.([fn 'Time']) = char(dt0);
end
end
