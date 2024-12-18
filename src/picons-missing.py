#!/usr/bin/python
import sys, unicodedata, re, os, glob, zipfile
from time import strftime
import json

def missingPicons():
	sortOrder = []
	for x in sys.argv[2:]:
		try:
			argVal = int(int(x) - 1)
			sortOrder.append(argVal)
		except:
			print("Command line arguments must be numbers, not '%s'." % (x))
	tmpPicon = "/tmp/picon/"
	tmpLamedb = "/tmp/lamedb"
	if os.path.exists(tmpLamedb):
		lamedb = tmpLamedb
	else:
		lamedb = "/etc/enigma2/lamedb"
	if not (len(sys.argv) > 1 and (piconLocations := json.loads(sys.argv[1])) and isinstance(piconLocations, list) and piconLocations):
		piconLocations = ["/usr/share/enigma2/picon/", "/picon/", "/media/usb/picon/","/media/usb2/picon/", "/media/hdd/picon/", "/media/hdd2/picon/", "/media/cf/picon/", "/media/sdb/picon/", "/media/sdb2/picon/","/media/sda/picon/",]
	omit_types = (0,12)
	outfile = "/tmp/missing-picons" + strftime("_%Y-%m-%d_%H-%M-%S") + ".zip"
	outlog1 = "found-picons"
	outlog2 = "missing-picons"
	outlog3 = "impossible-picons"
	outlog4 = "utf8-picon-names"
	outlog5 = "utf8-picon-list"  # not CSV
	logExt = ".csv"
	piconOutFolder = "/picon/"
	messages1 = []
	messages2 = {}
	messages3 = []
	#messages = {}
	messages = []
	messages4 = []
	messages5 = []
	paths = []
	pattern = "*.png"
	serviceTypes = []
	print("Searching for picons...")
	if os.path.isdir(tmpPicon):
		paths = glob.glob(tmpPicon + pattern)
	else:
		for l in piconLocations:
			paths = paths + glob.glob(l + pattern)
	pathsSplit = []
	for p in paths:
		pathsSplit.append(p.rsplit('/',1))
	del(paths)
	paths = {}
	print("Processing paths...")
	for p in pathsSplit:
		#parts = p[1].split('_', 3)
		f = p[0] + '/' + p[1]
		#n = "1_0_*_%s" % (parts[3])
		n = p[1]
		if os.path.islink(f):
			f = p[0] + '/' + os.readlink(f)
			if os.path.exists(f):
				paths[n] = f
		else:
			paths[n] = f
	del(pathsSplit)
	print("Reading lamedb...")
	f = open(lamedb, mode="r", encoding="UTF8", errors="ignore").readlines()
	f = f[f.index("services\n")+1:-3]
	i = 0
	done = []
	zf = zipfile.ZipFile(outfile, mode='w', compression=zipfile.ZIP_DEFLATED)
	while len(f) > 2:
		ref = [x for x in f[0][:-1].split(':')]
		name = f[1][:-1]
		f = f[3:] # for next iteration
		slot = slot1(ref[1])
		sat = slot1(ref[1])
		#if sat not in (130,192,282):
		#	continue
		refstr = "1:0:1:%X:%X:%X:%X:0:0:0" % (int(ref[0], 0x10), int(ref[2], 0x10), int(ref[3], 0x10), int(ref[1], 0x10))
		serviceType = str(hex(int(ref[4]))).replace('0x', '') # just for the log
		refstr2 = "1:0:%s:%X:%X:%X:%X:0:0:0" % (serviceType, int(ref[0], 0x10), int(ref[2], 0x10), int(ref[3], 0x10), int(ref[1], 0x10)) # just for the log
		ocram_str = "%X_%X_%X_%X0000" % (int(ref[0], 0x10), int(ref[2], 0x10), int(ref[3], 0x10), int(ref[1], 0x10) >> 16)
		#ref = f[0][:-1] # service ref string from lamedb
		oldPiconName = refstr.replace(':','_') + ".png"
		oldPiconName2 = refstr2.replace(':','_') + ".png"
		# newName1 = unicodedata.normalize('NFKD', str(name)).encode('ASCII', 'ignore').decode('ASCII', 'ignore')
		newName1 = sanitizeFilename(name)
		utf8_name_short = name and newName1 and newName1.lower()
		utf8_name = utf8_name_short + ".png"
		newName2 = re.sub("[^a-z0-9]", "", newName1.replace("&", "and").replace("+", "plus").replace("*", "star").lower())
		newPiconName = newName2  + ".png"
		if int(ref[4]) < 26 and int(ref[4]) not in omit_types: # service type in decimal
			if name and utf8_name != "__.png" and "SID 0x" not in name and not name.replace(".", "").isdecimal():
				messages4.append((name, sat, utf8_name, refstr2))
				messages5.append((utf8_name_short, ocram_str))
			else:
				utf8_name = ""  # utf8 name is not valid so truncate it
			if (name and newName2 and newPiconName in paths) or oldPiconName in paths or oldPiconName2 in paths or utf8_name and utf8_name in paths:
				#found = True
				if newName2 and newPiconName in paths:
					foundPiconName = newPiconName
				elif oldPiconName in paths:
					foundPiconName = oldPiconName
				elif oldPiconName2 in paths:
					foundPiconName = oldPiconName2
				elif utf8_name and utf8_name in paths:
					foundPiconName = utf8_name
				# messages1 = [(channel_name, sat, service_ref, picon_name_short, picon_name_full)]
				messages1.append((name, sat, refstr2, foundPiconName, paths[foundPiconName]))
			else:
				#if not slot in messages2:
				#	messages2[slot] = []
				#messages2[slot].append(('"'+newName1+'"', newPiconName, sat, refstr2))
				#if sat not in messages:
				#	messages[sat] = []
				#messages[sat].append((newName1, newPiconName, refstr2, sat, int(ref[4])))
				symlink = newName2 and "ln -s ./%s ./%s" % (newPiconName, oldPiconName2)
				utf8_symlink = utf8_name and "ln -s ./%s ./%s" % (utf8_name, oldPiconName2)
				messages.append((name and newName1, newPiconName, oldPiconName2, sat, int(ref[4]), ocram_str, symlink, utf8_name, utf8_symlink))
			i += 1
			if i % 100 == 0:
				print("Read %i channels... " % (i))
			#if i == 500:
			#	break
				
			serviceTypes.append(int(ref[4]))
		
	#print sorted(list(set(serviceTypes)))
	
	print("Sorting logs...")
	messages1 = sortByValue(messages1, 0)
	#messages2 = sortByValue(messages2, 0)
	#messages3 = sortByValue(messages3, 2)
	messages4.sort()
	
	messages = sortByValueRecursive(messages, sortOrder)
	#all = []
	#for sat in messages.keys():
	#	tv = []
	#	other = []
	#	for item in messages[sat]:
	#		if item[4] in (1,4,5,17,22,25):
	#			tv.append(item)
	#			all.append(item)
	#		else:
	#			other.append(item)
	#			all.append(item)
	#	tv = sortByValue(tv, 0)
	#	other = sortByValue(other, 0)
	#	log = ''
	#	for ch in tv:
	#		log += '"%s","%s","%s"\n' % (ch[0],ch[1],ch[2])
	#	zf.writestr(outlog2 + '-' + satname(sat) + '-tv' + logExt, log)
	#	log = ''
	#	for ch in other:
	#		log += '"%s","%s","%s"\n' % (ch[0],ch[1],ch[2])
	#	zf.writestr(outlog2 + '-' + satname(sat) + '-other' + logExt, log)
	#all = sortByValue(all, 0)
	#for ch in all:
	#	log += '"%s","%s","%s","%s"\n' % (ch[0],ch[1],ch[2], satname(ch[3]))
	#zf.writestr(outlog2 + '-all_services' + logExt, log)

# start: removed by edit 1
#	i = 0
#	log = ''
#	for message in messages:
#		if i % 35 == 0:
#			log += 'Channel name,SNP name,SRP name,Orbital,DVB type,Ocram database,Symlink\n'
#		log += '"%s","%s","%s","%s",%i,%s,%s\n' % (message[0],message[1],message[2], satname(message[3]), message[4], message[5], message[6])
#		i += 1
# end: removed by edit 1

# start: edit 1
	print("write missing")
	log = ['Channel name,SRP name,utf8_name,SNP name,Ocram database,Orbital,DVB type,symlink,utf8_symlink\n']
	for message in messages:
		log.append('"%s","%s",%s,"%s",%s,"%s",%i,%s,%s\n' % (message[0], message[2][:-4], message[7], message[1][:-4], message[5], satname(message[3]), message[4], message[6], message[8]))
# end: edit 1
	zf.writestr(outlog2 + '-all_services' + logExt, "".join(log))
	
	#found picons... (channel_name, sat, service_ref, picon_name_short, picon_name_full)
	control_chars = ''.join(map(chr, list(range(0,32)) + list(range(127,160))))
	control_char_re = re.compile('[%s]' % re.escape(control_chars))
	print("write found")
	log = ['Channel name,Orbital,Service ref,Picon name,Picon path\n']
	for message in messages1:
		log.append('"%s","%s","%s","%s",%s\n' % (control_char_re.sub('', message[0]),satname(message[1]),message[2], message[3], message[4]))
	zf.writestr(outlog1 + logExt, "".join(log))

	print("write UTF8")
	log = ['Channel name,Orbital,UTF8 picon name,Service ref\n']
	for message in messages4:
		log.append('"%s","%s","%s","%s"\n' % (message[0], satname(message[1]), message[2], message[3]))
	zf.writestr(outlog4 + logExt, "".join(log))

	log = []
	for message in messages5:
		log.append('%s=%s\n' % (message[0], message[1]))
	log.sort(key=lambda x: x.split("=", 1)[0])
	zf.writestr(outlog5, "".join(log))  # don't use logExt
	


	
	#print "Writing picons-missing log..."
	#log = ''
	#for m in messages:
	#	log += ', '.join(m) + "\n"
	#zf.writestr(outlog2 + logExt, log)
	
	#print "Writing picons-found log..."
	#log1 = ''
	#for m in messages1:
	#	log1 += ', '.join(m) + "\n"
	#zf.writestr(outlog1 + logExt, log1)
	
	#print "Writing picons-missing logs..."
	#log2 = ''
	#slots = sorted(messages2.keys())
	#for slot in slots:
	#	missing = sortByValue(messages2[slot], 0)
	#	for m in missing:
	#		log2 += ', '.join(m) + "\n"
	#zf.writestr(outlog2 + logExt, log2)
	
	#print "Writing picons-impossible log..."
	#log3 = ''
	#for m in messages3:
	#	log3 += ', '.join(m) + "\n"
	#zf.writestr(outlog3 + logExt, log3)
	
	zf.close()
	print("Task completed. Output saved in %s." %(outfile))


def sortByValue(inputList, sortKey): # Sort case insensitive
	return sorted(inputList, key=lambda listItem: listItem[sortKey].lower())


def sortByValueRecursive(inputList, sortKey=[], level = 0): # Sort case insensitive
	#for sorting nested arrays
	if isinstance(sortKey, int):
		sortKey = [sortKey]
	if len(sortKey) < 1 or len(sortKey) > len(inputList[0]):
		return inputList
	if len(sortKey) == 1:
		print("level(upper):", level)
		return sorted(inputList, key=lambda listItem: (listItem[sortKey[0]] if isinstance(listItem[sortKey[0]], int) else  listItem[sortKey[0]].lower()))
	firstSortKey = sortKey.pop(0)
	sortList = []
	sortDict = {}
	for listItem in inputList:
		listItemSortKey = listItem[firstSortKey] if isinstance(listItem[firstSortKey], int) else listItem[firstSortKey].lower()
		if listItemSortKey not in sortList:
			sortList.append(listItemSortKey)
			sortListIndex = sortList.index(listItemSortKey)
			sortDict[sortListIndex] = []
		sortListIndex = sortList.index(listItemSortKey)
		sortDict[sortListIndex].append(listItem)
		
	sortListPairs = []
	i = 0
	for sortItem in sortList:
		sortListPairs.append((i, sortItem))
		i += 1
	sortListPairs =  sorted(sortListPairs, key=lambda listItem: listItem[1])
	
	for pairs in sortListPairs:
		try:
			print("level(lower):", level)
			sortDict[pairs[0]] = sortByValueRecursive(sortDict[pairs[0]], sortKey, level + 1)
		except:
			print("sortDict.keys()", list(sortDict.keys()))
			flog = open('errors.log', 'w')
			flog.write("level: %i\n"%(level))
			for eachKey in list(sortDict.keys()):
				joined = "','".join(map(str,sortDict[eachKey]))
				out = "%s: %s\n"%(str(eachKey), joined)
				flog.write(out)
			flog.close()
			print("pairs[0]: ", pairs[0])
			sortDict[pairs[0]] = sortByValueRecursive(sortDict[pairs[0]], sortKey, level + 1)
			return
	
	#for sortItem in sortList:
		#sortDict[sortItem] = sortByValueRecursive(sortDict[sortItem], sortKey)
	output = []
	for pairs in sortListPairs:
		output = output + sortDict[pairs[0]]
	return output


def slotName(namespace):
	slot = slot1(namespace)
	return satname(slot)


def satname(slot):
	if slot == 65535:
		return 'cable'
	elif slot == 61166:
		return 'terrestrial'
	while slot < -1800:
		slot += 3600
	while slot > 1800:
		slot -= 3600
	westeast = 'E' if slot >= 0 else 'W'  
	return str(round(float(abs(slot))/10, 1)) + westeast


def slot1(namespace):
	return int(namespace[:len(namespace)-4], 16)


def sanitizeFilename(filename, maxlen=255):  # 255 is max length in ext4 (and most other file systems)
	"""Return a fairly safe version of the filename.

	We don't limit ourselves to ascii, because we want to keep municipality
	names, etc, but we do want to get rid of anything potentially harmful,
	and make sure we do not exceed filename length limits.
	Hence a less safe blacklist, rather than a whitelist.
	"""
	blacklist = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|", "\0"]
	reserved = [
		"CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5",
		"COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5",
		"LPT6", "LPT7", "LPT8", "LPT9",
	]  # Reserved words on Windows
	# Remove any blacklisted chars. Remove all charcters below code point 32. Normalize. Strip.
	filename = unicodedata.normalize("NFKD", "".join(c for c in filename if c not in blacklist and ord(c) > 31)).strip()
	if all([x == "." for x in filename]) or filename in reserved:  # if filename is a string of dots
		filename = "__" + filename
	# Most Unix file systems typically allow filenames of up to 255 bytes.
	# However, the actual number of characters allowed can vary due to the
	# representation of Unicode characters. Therefore length checks must
	# be done in bytes, not unicode.
	#
	# Also we cannot leave the byte truncate in the middle of a multi-byte
	# utf8 character! So, convert to bytes, truncate then get back to unicode,
	# ignoring errors along the way, the result will be valid unicode.
	# Prioritise maintaining the complete extension if possible.
	# Any truncation of root or ext will be done at the end of the string
	root, ext = os.path.splitext(filename.encode(encoding='utf-8', errors='ignore'))
	if len(ext) > maxlen - (1 if root else 0):  # leave at least one char for root if root
		ext = ext[:maxlen - (1 if root else 0)]
	# convert back to unicode, ignoring any incomplete utf8 multibyte chars
	filename = root[:maxlen - len(ext)].decode(encoding='utf-8', errors='ignore') + ext.decode(encoding='utf-8', errors='ignore')
	filename = filename.rstrip(". ")  # Windows does not allow these at end
	if len(filename) == 0:
		filename = "__"
	return filename
			
missingPicons()
