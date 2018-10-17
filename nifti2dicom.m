function nifti2dicom(nifti, dicom1, dicom2)
%NIFTI2DICOM reconstruct DICOM files given one NIfTI and two DICOM files
%   nifti2dicom(nifti, dicom1, dicom2)
%   nifti is the NIfTI header
%   dicom1 and dicom2 are the two DICOM headers
%   nifti, dicom1 and dicom2 can also hold the paths to the corresponding
%   files
    %% read nifti file
    if ~isstruct(nifti)
        nifti = niftiinfo(nifti);
    end
    data = niftiread(nifti.Filename);
    if ~isstruct(dicom1)
        dicom1 = dicominfo(dicom1);
    end
    if ~isstruct(dicom2)
        dicom2 = dicominfo(dicom2);
    end
    %% auxiliary constants
    M = diag([-1; -1; 1]);
    Txy = [0 1 0; 1 0 0; 0 0 1];
    %% calculate nifti parameters
    ISn = nifti.ImageSize';
    PDn = nifti.PixelDimensions';
    Rn = nifti.Transform.T(1:3, 1:3)';
    Rn = bsxfun(@rdivide, Rn, PDn');
    Sn = nifti.Transform.T(4, 1:3)';
    %% calculate dicom parameters
    Xd = dicom1.ImageOrientationPatient(1:3);
    Yd = dicom1.ImageOrientationPatient(4:6);
    Zd = (dicom2.ImagePositionPatient - dicom1.ImagePositionPatient) /...
        (dicom2.InstanceNumber - dicom1.InstanceNumber);
    Zd = Zd / norm(Zd);
    Rd = [Xd, Yd, Zd];
    %% calculate output parameters
    C = linsolve(Rd, M * Rn);
    C = round(C);
    % assert(nnz(C) == 3 && all(abs(sum(C, 1)) == 1) && all(abs(sum(C, 2)) == 1));
    Cabs = abs(C);
    Csum = sum(C, 1)';
    ISd = Cabs * ISn;
    PDd = Cabs * PDn;
    Sd = M * (Sn - Rn * diag(PDn) * diag((Csum - 1) / 2) * (ISn - 1));
    %% reorient data matrix
    for d = 1:3
        if Csum(d) < 0
            data = flip(data, d);
        end
    end
    data = permute(data, Txy * Cabs * (1:3)');
    data = uint16(data);
    %% write output files
    folder = fileparts(nifti.Filename);
    folder = folder + "\dcm";
    if exist(folder, 'dir')
        rmdir(folder, 's');
    end
    mkdir(folder);
    hdr = dicom1;
    fns = fieldnames(hdr);
    for fnc = 1:length(fns)
        fn = fns{fnc};
        % FileMeta* are calculated automatically
        % WindowCenterWidthExplanation is not included
        if startsWith(fn, 'Private_') || startsWith(fn, 'File') || startsWith(fn, 'Window')
            hdr = rmfield(hdr, fn);
        end
    end
    % *ClassUID can be magically recalculated
    hdr = rmfield(hdr, {
        'MediaStorageSOPInstanceUID';
        'SOPInstanceUID';
    });
    hdr.SeriesInstanceUID = dicomuid();
    hdr = rmfield(hdr, 'DataSetTrailingPadding');
    assert(isequal(hdr.Width, ISd(1)));
    assert(isequal(hdr.Height, ISd(2)));
    assert(hdr.SliceThickness <= PDd(3));
    assert(isequal(hdr.ImageOrientationPatient(1:3), Xd));
    assert(isequal(hdr.ImageOrientationPatient(4:6), Yd));
    assert(isequal(hdr.Rows, ISd(2)));
    assert(isequal(hdr.Columns, ISd(1)));
    assert(isequal(hdr.PixelSpacing, flip(PDd(1:2))));
    fprintf("saving %d slices\n", ISd(3));
    for k = 1:ISd(3)
        dicomfile = folder + "\" + pad(num2str(k - 1), floor(log10(ISd(3))) + 1, 'left', '0') + ".dcm";
        hdr.InstanceNumber = k;
        [hdr.InstanceCreationDate, hdr.InstanceCreationTime] = nifti2dicomdt(...
            dicom1.InstanceCreationDate, dicom1.InstanceCreationTime, dicom1.InstanceNumber, ...
            dicom2.InstanceCreationDate, dicom2.InstanceCreationTime, dicom2.InstanceNumber, ...
            k...
        );
        [hdr.ContentDate, hdr.ContentTime] = nifti2dicomdt(...
            dicom1.ContentDate, dicom1.ContentTime, dicom1.InstanceNumber, ...
            dicom2.ContentDate, dicom2.ContentTime, dicom2.InstanceNumber, ...
            k...
        );
        hdr.ImagePositionPatient = Sd + Zd * PDd(3) * (k - 1);
        hdr.SliceLocation = sum(abs(Zd) .* hdr.ImagePositionPatient);
        hdr.LargestImagePixelValue = max(squeeze(reshape(data(:, :, k), 1, 1, [])));
        hdr.SmallestImagePixelValue = min(squeeze(reshape(data(:, :, k), 1, 1, [])));
        dicomwrite(data(:, :, k), dicomfile, hdr);
        fprintf("slice %d out of %d saved\n", k, ISd(3));
    end
end

function [date0, time0] = nifti2dicomdt(date1, time1, number1, date2, time2, number2, numbers)
    dt1 = datetime([date1 time1], 'InputFormat','yyyyMMddHHmmss.SSSSSS');
    dt2 = datetime([date2 time2], 'InputFormat','yyyyMMddHHmmss.SSSSSS');
    dt = dt1 + (dt2 - dt1) / (number2 - number1) * numbers;
    dt.Format = 'yyyyMMdd';
    date0 = char(dt);
    dt.Format = 'HHmmss.SSSSSS';
    time0 = char(dt);
end