# http://nipy.org/nibabel/dicom/siemens_arr.html

import math

def decode(arr):
	assert arr[0:4] == b"SV10"
	# arr[4:8] # unused
	ntags = int.from_bytes(arr[8:12], "little")
	# int.from_bytes(arr[8:12], "little") # unused 77
	i = 16
	hdr = {}
	for ctags in range(0, ntags):
		key = arr[i:i+64].split(bytes(1),1)[0].decode()
		hdr[key] = {}
		hdr[key]["VM"] = int.from_bytes(arr[i+64:i+68], "little")
		hdr[key]["VR"] = arr[i+68:i+72].split(bytes(1),1)[0].decode()
		hdr[key]["SyngoDT"] = int.from_bytes(arr[i+72:i+76], "little")
		nitems = int.from_bytes(arr[i+76:i+80], "little")
		# int.from_bytes(arr[80:84], "little") # unused 77 or 205
		i += 84
		hdr[key]["Data"] = []
		for citems in range(0, nitems):
			item_len = int.from_bytes(arr[i:i+4], "little")
			int.from_bytes(arr[i+4:i+8], "little") # unused
			int.from_bytes(arr[i+8:i+12], "little") # unused
			int.from_bytes(arr[i+12:i+16], "little") # unused
			hdr[key]["Data"].append(arr[i+16:i+16+item_len].decode())
			i += 16 + math.ceil(item_len / 4) * 4
	return hdr

def encode(hdr):
	arr = b""
	arr += b"SV10"
	arr += bytes(4) # unused
	arr += len(hdr).to_bytes(4, "little")
	arr += bytes(4) # unused 77
	for key, val in hdr.items():
		arr += key.encode().ljust(64, bytes(1))
		arr += val["VM"].to_bytes(4, "little")
		arr += val["VR"].encode().ljust(4, bytes(1))
		arr += val["SyngoDT"].to_bytes(4, "little")
		arr += len(val["Data"]).to_bytes(4, "little")
		arr += bytes(4) # unused 77 or 205
		for dat in val["Data"]:
			item_len = len(dat)
			arr += item_len.to_bytes(4, "little")
			arr += bytes(4) # unused
			arr += bytes(4) # unused
			arr += bytes(4) # unused
			arr += dat.encode().ljust(math.ceil(item_len / 4) * 4, bytes(1))
	arr += bytes(4) # append one more zero
	return arr
