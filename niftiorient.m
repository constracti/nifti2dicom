function [hdr, img] = niftiorient(hdr, img)
%NIFTIORIENT Orient a NIfTI header and image
S = hdr.PixelDimensions';
R = hdr.Transform.T(1:3, 1:3)' * diag(1 ./ S(1:3));
P = zeros(1, 3);
Rtmp = abs(R);
for d = 1:3
    [~, P(d)] = max(abs(Rtmp(:, d)));
    Rtmp(P(d), :) = 0;
end
F = R(P + (0:3:6)) < 0;
[hdr, img] = niftiflip(hdr, img, F);
[~, P] = sort(P);
[hdr, img] = niftipermute(hdr, img, P);
end
