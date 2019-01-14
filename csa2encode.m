function str = csa2encode(tags)
%CSA2ENCODE Encode the Siemens CSA2 private header
%   http://nipy.org/nibabel/dicom/siemens_csa.html
% TODO Do we want identical or simply equivalent encoding?
str = zeros(16, 1, 'uint8');
str(1:4) = uint8('SV10');
% str(5:8) % unused
tagnames = fieldnames(tags);
ntags = length(tagnames);
str(9:12) = typecast(uint32(ntags), 'uint8');
% str(13:16) = typecast(uint32(77), 'uint8'); % unused 77
for ctags = 1:ntags
    tagstr = zeros(84, 1, 'uint8');
    tagname = tagnames{ctags};
    tagstr(1:length(tagname)) = uint8(tagname);
    tag = tags.(tagname);
    vm = tag.VM;
    tagstr(65:68) = typecast(uint32(vm), 'uint8');
    vr = tag.VR;
    tagstr(69:68+length(vr)) = uint8(vr);
    syngodt = tag.SyngoDT;
    tagstr(73:76) = typecast(uint32(syngodt), 'uint8');
    items = tag.Data;
    nitems = length(items);
    tagstr(77:80) = typecast(uint32(nitems), 'uint8');
    % tag(81:84) = typecast(uint32(77), 'uint8'); % unused 77 or 205
    for citems = 1:nitems
        item = items{citems};
        itemlen = length(item);
        itemlenceil = ceil(itemlen / 4) * 4;
        itemstr = zeros(16 + itemlenceil, 1, 'uint8');
        itemstr(1:4) = typecast(uint32(itemlen), 'uint8');
        % itemstr(5:8) % unused
        % itemstr(9:12) % unused
        % itemstr(13:16) % unused
        itemstr(17:16+itemlen) = uint8(item);
        tagstr = [tagstr; itemstr];
    end
    str = [str; tagstr];
end
str = [str; typecast(uint32(0), 'uint8')']; % append one more uint32 zero
end
