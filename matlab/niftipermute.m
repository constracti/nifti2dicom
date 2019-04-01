function nifti = niftipermute(nifti, P)
%NIFTIPERMUTE Permute a NIfTI image in a specific order
%% load file
if ~isstruct(nifti)
    nifti = niftiinfo(nifti);
end
if ~isfield(nifti, 'img')
    nifti.img = niftiread(nifti.Filename);
end
%% check identity
if isequal(P(:), (1:3)')
    return
end
%% parse header
L = nifti.ImageSize';
S = nifti.PixelDimensions';
R = nifti.Transform.T(1:3, 1:3)' * diag(1 ./ S(1:3));
T = nifti.Transform.T(4, 1:3)';
%% transform header
L(1:3) = L(P);
S(1:3) = S(P);
R = R(:, P);
%% transform image
if ndims(nifti.img) > 3
    nifti.img = permute(nifti.img, [P 4]);
else
    nifti.img = permute(nifti.img, P);
end
%% update header
nifti.ImageSize = L';
nifti.PixelDimensions = S';
% nifti.SliceEnd = L(3) - 1;
nifti.Transform = affine3d([
    (R * diag(S(1:3)))', zeros(3, 1);
    T', 1;
]);
nifti.Qfactor = sign(det(R));
dims = {'FrequencyDimension', 'PhaseDimension', 'SpatialDimension'};
for d = 1:length(dims)
    dim = dims{d};
    if nifti.(dim) == 0
        continue
    end
    nifti.(dim) = find(P == nifti.(dim));
    if isempty(nifti.(dim))
        nifti.(dim) = 0;
    end
end
end
