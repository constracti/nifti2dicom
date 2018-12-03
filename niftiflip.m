function nifti = niftiflip(nifti, F)
%NIFTIFLIP Flip a NIfTI image along specific dimensions
%% load file
if ~isstruct(nifti)
    nifti = niftiinfo(nifti);
end
if ~isfield(nifti, 'img')
    nifti.img = niftiread(nifti.Filename);
end
%% parse header
L = nifti.ImageSize';
S = nifti.PixelDimensions';
R = nifti.Transform.T(1:3, 1:3)' * diag(1 ./ S(1:3));
T = nifti.Transform.T(4, 1:3)';
%% transform header
R(:, F) = -R(:, F);
T = T - R * diag(S(1:3)) * diag(F) * (L(1:3) - 1);
%% transform image
for d = 1:3
    if F(d)
        nifti.img = flip(nifti.img, d);
    end
end
%% update header
nifti.Transform = affine3d([
    (R * diag(S(1:3)))', zeros(3, 1);
    T', 1;
]);
nifti.Qfactor = sign(det(R));
end
