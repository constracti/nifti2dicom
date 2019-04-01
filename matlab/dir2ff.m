function [dicoms, nifti, niftio, niftico] = dir2ff(directory)
%% exclude directories
files = dir(directory);
isdir = extractfield(files, 'isdir');
isdir = cell2mat(isdir);
files = files(not(isdir));
%% keep filenames
files = extractfield(files, 'name');
files = string(files);
%% recognize dicom
isdcm = endsWith(files, [".dcm", ".ima"], 'IgnoreCase', true);
dicoms = files(isdcm);
dicoms = fullfile(directory, dicoms);
%% recognize nifti
isnii = endsWith(files, [".nii", ".nii.gz"], 'IgnoreCase', true);
niftis = files(isnii);
nifti = "";
niftio = "";
niftico = "";
for i = 1:length(niftis)
    if startsWith(niftis(i), "co")
        niftico = fullfile(directory, niftis(i));
    elseif startsWith(niftis(i), "o")
        niftio = fullfile(directory, niftis(i));
    else
        nifti = fullfile(directory, niftis(i));
    end
end
end
