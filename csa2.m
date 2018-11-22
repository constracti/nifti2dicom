function hdr = csa2(csa)
%CSA2 Decode the Siemens CSA2 private header
%   http://nipy.org/nibabel/dicom/siemens_csa.html
assert(strcmp(char(csa(1:4))','SV10'));
hdr = struct();
% csa(5:8) % unused
n_tags = typecast(csa(9:12), 'uint32');
% typecast(csa(13:16), 'uint32'); % unused 77;
i = 16;
for c_tags = 1:n_tags
    name = char(csa(i+1:i+64))';
    name = strsplit(name, char(0));
    name = name{1};
    vm = typecast(csa(i+65:i+68), 'uint32');
    hdr.(name).VM = vm;
    vr = char(csa(i+69:i+71))';
    if vr(end) == char(0), vr = vr(1:end-1); end
    hdr.(name).VR = vr;
    syngodt = typecast(csa(i+73:i+76), 'uint32');
    hdr.(name).SyngoDT = syngodt;
    n_items = typecast(csa(i+77:i+80), 'uint32');
    data = cell(n_items, 1);
    % typecast(csa(i+81:i+84), 'uint32'); % unused 77 or 205
    i = i + 84;
    for c_items = 1:n_items
        item_len = typecast(csa(i+1:i+4), 'uint32');
        % typecast(csa(i+5:i+8), 'uint32') % unused
        % typecast(csa(i+9:i+12), 'uint32') % unused
        % typecast(csa(i+13:i+16), 'uint32') % unused
        data{c_items} = char(csa(i+17:i+16+item_len))';
        if item_len > 0 && data{c_items}(end) == char(0)
            data{c_items} = data{c_items}(1:end-1);
        end
        i = i + 16 + ceil(double(item_len) / 4) * 4;
    end
    hdr.(name).Data = data;
end
end
