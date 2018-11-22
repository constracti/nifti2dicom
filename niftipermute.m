function [hdr, img] = niftipermute(hdr, img, P)
%NIFTIPERMUTE Permute a NIfTI header and in a specific order
%% load header
L = hdr.ImageSize';
S = hdr.PixelDimensions';
R = hdr.Transform.T(1:3, 1:3)' * diag(1 ./ S(1:3));
T = hdr.Transform.T(4, 1:3)';
%% transform header
L(1:3) = L(P);
S(1:3) = S(P);
R = R(:, P);
%% transform image
if ndims(img) > 3
    img = permute(img, [P 4]);
else
    img = permute(img, P);
end
%% save header
hdr.ImageSize = L';
hdr.PixelDimensions = S';
% hdr.SliceEnd = L(3) - 1;
hdr.Transform = affine3d([
    (R * diag(S(1:3)))', zeros(3, 1);
    T', 1;
]);
hdr.Qfactor = sign(det(R)); % ignore this field
% dims = {'FrequencyDimension', 'PhaseDimension', 'SpatialDimension'};
% for d = 1:length(dims)
%     dim = dims{d};
%     if hdr.(dim) == 0
%         continue
%     end
%     hdr.(dim) = find(P == hdr.(dim));
%     if isempty(hdr.(dim))
%         hdr.(dim) = 0;
%     end
% end
end
