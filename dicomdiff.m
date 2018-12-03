function dicomdiff(dicom1, dicom2)
%DICOMDIFF Print the differences between two DICOM headers
%   dicomdiff(dicom1, dicom2)
%   dicom1 and dicom2 are the two DICOM headers
%   dicom1 and dicom2 can also hold the paths to the DICOM files
if ~isstruct(dicom1)
    dicom1 = dicominfo(dicom1);
end
if ~isstruct(dicom2)
    dicom2 = dicominfo(dicom2);
end
fns = fieldnames(dicom1);
for i = 1:length(fns)
    fn = fns{i};
    if dicomdiffignore(fn)
    elseif ~isfield(dicom2, fn)
        fprintf('- %s: %s\n', fn, dicomdiffstr(dicom1.(fn)));
    elseif ~isequal(dicom1.(fn), dicom2.(fn))
        fprintf('- %s: %s\n', fn, dicomdiffstr(dicom1.(fn)));
        fprintf('+ %s: %s\n', fn, dicomdiffstr(dicom2.(fn)));
    end
end
fns = fieldnames(dicom2);
for i = 1:length(fns)
    fn = fns{i};
    if dicomdiffignore(fn)
    elseif ~isfield(dicom1, fn)
        fprintf('+ %s: %s\n', fn, dicomdiffstr(dicom2.(fn)));
    end
end
end

function str = dicomdiffstr(val)
if isstruct(val)
    val = struct2cell(val);
    val = cellfun(@dicomdiffstr, val, 'UniformOutput', false);
    str = strjoin(val, ', ');
else
    str = mat2str(val);
end
end

function ignore = dicomdiffignore(fn)
ignore = isequal(fn, 'DataSetTrailingPadding');
end
