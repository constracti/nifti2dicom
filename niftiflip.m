function [hdr, img] = niftiflip(hdr, img, F)
%NIFTIFLIP Flip a NIfTI header and image along specific dimensions
%% load header
L = hdr.ImageSize';
S = hdr.PixelDimensions';
R = hdr.Transform.T(1:3, 1:3)' * diag(1 ./ S(1:3));
T = hdr.Transform.T(4, 1:3)';
%% transform header
R(:, F) = -R(:, F);
T = T - R * diag(S(1:3)) * diag(F) * (L(1:3) - 1);
%% transform image
for d = 1:3
    if F(d)
        img = flip(img, d);
    end
end
%% save header
hdr.Transform = affine3d([
    (R * diag(S(1:3)))', zeros(3, 1);
    T', 1;
]);
hdr.Qfactor = sign(det(R)); % ignore this field
end
