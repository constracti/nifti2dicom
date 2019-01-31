function hdr = csa2decode(str)
%CSA2DECODE Decode the Siemens CSA2 private header
%   http://nipy.org/nibabel/dicom/siemens_csa.html
assert(strcmp(char(str(1:4))','SV10'));
hdr = struct();
% str(5:8) % unused
ntags = typecast(str(9:12), 'uint32');
% typecast(str(13:16), 'uint32'); % unused 77;
i = 16;
for ctags = 1:ntags
    name = char(str(i+1:i+64))';
    name = strsplit(name, char(0));
    name = name{1};
    vm = typecast(str(i+65:i+68), 'uint32');
    hdr.(name).VM = vm;
    vr = char(str(i+69:i+71))';
    if vr(end) == char(0), vr = vr(1:end-1); end
    hdr.(name).VR = vr;
    syngodt = typecast(str(i+73:i+76), 'uint32');
    hdr.(name).SyngoDT = syngodt;
    nitems = typecast(str(i+77:i+80), 'uint32');
    data = cell(nitems, 1);
    % typecast(str(i+81:i+84), 'uint32'); % unused 77 or 205
    i = i + 84;
    for citems = 1:nitems
        item_len = typecast(str(i+1:i+4), 'uint32');
        % typecast(str(i+5:i+8), 'uint32') % unused
        % typecast(str(i+9:i+12), 'uint32') % unused
        % typecast(str(i+13:i+16), 'uint32') % unused
        data{citems} = char(str(i+17:i+16+item_len))';
        i = i + 16 + ceil(double(item_len) / 4) * 4;
    end
    hdr.(name).Data = data;
end
end
