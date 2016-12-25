from wupclient import wupclient

# constants
DEV_USB = "/dev/usb01"
LOCATION_USB = "/vol/storage_usb"
PATH_TITLES = LOCATION_USB + "/usr/title"
INTERESTING_TITLE_PREFIXES = ["00050000", "0005000c", "0005000e", "00050002,"]
PATH_META = "/meta/meta.xml"
REGION_KEYWORD = bytearray("</region>")

def mount_usb(w):
	if w.cd(LOCATION_USB):
		print("mounting usb")
		f = w.get_fsa_handle()
		w.FSA_Mount(f, DEV_USB, LOCATION_USB, 2)
	else:
		print("usb is already mounted")

def unmount_usb(w):
	print "unmounting usb"
	f = w.get_fsa_handle()
	w.FSA_Unmount(f, LOCATION_USB, 2)

def clean(w):
	if w.fsa_handle:
		w.close(w.fsa_handle)
		w.fsa_handle = None
	if w.s:
		w.s.close()
		w.s = None

def region_modify(w, target):
	l0 = w.ls(PATH_TITLES, True)
	f = w.get_fsa_handle()
	for d1 in l0:
		d1n = d1["name"]
		# print "\"" + d1 + "\""
		if d1["is_file"] or d1n not in INTERESTING_TITLE_PREFIXES:
			continue
		l1 = w.ls(PATH_TITLES + "/" + d1n, True)
		for d2 in l1:
			d2n = d2["name"]
			if d2["is_file"]:
				continue
			# full path
			fp = PATH_TITLES + "/" + d1n + "/" + d2n + PATH_META
			# read the file
			print("checking " + fp)
			r, h = w.FSA_OpenFile(f, fp, "r")
			assert r == 0, "\tcould not open meta for read"
			buf = bytearray()
			block_size = 0x400
			while True:
				r, d = w.FSA_ReadFile(f, h, 0x1, block_size)
				buf += d[:r]
				if r < block_size:
					break
			w.FSA_CloseFile(f, h)
			# check the meta
			i = buf.find(REGION_KEYWORD)
			if i == -1:
				print("\tcould not find region in meta")
				continue
			current = str(buf[i - 8:i])
			if buf[i - 9] != ord(">") or any(map(lambda c: c not in "0123456789", current)):
				print("\tsomething strange in meta, won't touch")
				continue
			if current == target:
				# nothing to do
				continue
			# modify and write the meta
			print("\t" + current + " => " + target)
			buf[i - 8:i] = bytearray(target)
			r, h = w.FSA_OpenFile(f, fp, "w")
			assert r == 0, "\tcould not open meta for write"
			while len(buf) > 0:
				w.FSA_WriteFile(f, h, buf[:block_size])
				buf = buf[block_size:]
			w.FSA_CloseFile(f, h)

if __name__ == '__main__':
	# edit IP accordingly
	w = wupclient("192.168.0.230")
	mount_usb(w)
	# edit target region accordingly, 00000001: JPN, 00000002: USA, 00000004: EUR
	region_modify(w, "00000002")
	unmount_usb(w)
	clean(w)
