function nifti = niftiorient(nifti)
%NIFTIORIENT Orient a NIfTI header and image
%% load file
if ~isstruct(nifti)
    nifti = niftiinfo(nifti);
end
if ~isfield(nifti, 'img')
    nifti.img = niftiread(nifti.Filename);
end
%% parse header
S = nifti.PixelDimensions';
R = nifti.Transform.T(1:3, 1:3)' * diag(1 ./ S(1:3));
%% apply conversion
P = zeros(1, 3);
Rtmp = abs(R);
for d = 1:3
    [~, P(d)] = max(Rtmp(:, d));
    Rtmp(P(d), :) = 0;
end
F = R(P + (0:3:6)) < 0;
nifti = niftiflip(nifti, F);
[~, P] = sort(P);
nifti = niftipermute(nifti, P);
end
