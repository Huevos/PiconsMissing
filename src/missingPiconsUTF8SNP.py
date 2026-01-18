#!/usr/bin/python
# picons-missing.py - Version for UTF8 SNP picons only
# by lululla

import sys
import unicodedata
import re
import os
import glob
import zipfile
import json
from time import strftime


def missingPiconsUTF8SNP():
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
        piconLocations = [
            "/usr/share/enigma2/picon/", "/picon/", "/media/usb/picon/",
            "/media/usb2/picon/", "/media/hdd/picon/", "/media/hdd2/picon/",
            "/media/cf/picon/", "/media/sdb/picon/", "/media/sdb2/picon/",
            "/media/sda/picon/",
        ]

    omit_types = (0, 12)
    outfile = "/tmp/missing-picons-utf8snp" + strftime("_%Y-%m-%d_%H-%M-%S") + ".zip"
    outlog1 = "found-picons-utf8snp"
    outlog2 = "missing-picons-utf8snp"
    logExt = ".csv"

    messages1 = []  # Found picons
    messages = []   # Missing picons
    paths = {}
    pattern = "*.png"

    print("Searching for picons in UTF8 SNP format...")

    # Collect all picon files
    if os.path.isdir(tmpPicon):
        path_list = glob.glob(tmpPicon + pattern)
    else:
        path_list = []
        for location in piconLocations:
            path_list.extend(glob.glob(location + pattern))

    # Process paths and handle symlinks
    for full_path in path_list:
        dir_path, filename = full_path.rsplit('/', 1)
        if os.path.islink(full_path):
            link_target = os.readlink(full_path)
            resolved_path = dir_path + '/' + link_target
            if os.path.exists(resolved_path):
                paths[filename] = resolved_path
        else:
            paths[filename] = full_path

    print("Reading lamedb...")
    try:
        with open(lamedb, mode="r", encoding="UTF8", errors="ignore") as f:
            lines = f.readlines()
    except:
        print("Error reading lamedb file")
        return

    # Find services section
    try:
        start_index = lines.index("services\n") + 1
        lines = lines[start_index:-3]
    except:
        print("Invalid lamedb format")
        return

    i = 0
    serviceTypes = []

    while len(lines) > 2:
        ref = [x for x in lines[0][:-1].split(':')]
        name = lines[1][:-1]
        lines = lines[3:]  # Move to next service

        # Skip invalid services
        if len(ref) < 5:
            continue

        sat = slot1(ref[1])
        serviceType = str(hex(int(ref[4]))).replace('0x', '')

        # Create service reference string for log
        refstr2 = "1:0:%s:%X:%X:%X:%X:0:0:0" % (
            serviceType, int(ref[0], 0x10), int(ref[2], 0x10),
            int(ref[3], 0x10), int(ref[1], 0x10)
        )

        # Create Ocram database string
        ocram_str = "%X_%X_%X_%X0000" % (
            int(ref[0], 0x10), int(ref[2], 0x10),
            int(ref[3], 0x10), int(ref[1], 0x10) >> 16
        )

        # Old picon name (for symlink)
        oldPiconName2 = refstr2.replace(':', '_') + ".png"

        # Generate UTF8 SNP filename
        sanitized_name = sanitizeFilename(name)

        # Apply UTF8 SNP rules: lowercase, replace special chars, remove non-alphanumeric
        utf8snp_name = sanitized_name.lower()
        utf8snp_name = utf8snp_name.replace("&", "and")
        utf8snp_name = utf8snp_name.replace("+", "plus")
        utf8snp_name = utf8snp_name.replace("*", "star")
        utf8snp_name = re.sub("[^a-z0-9]", "", utf8snp_name)

        utf8snp_filename = utf8snp_name + ".png"

        # Check if service type should be processed
        if int(ref[4]) < 26 and int(ref[4]) not in omit_types:
            # Check if UTF8 SNP picon exists
            if utf8snp_name and utf8snp_filename in paths:
                # Picon found
                messages1.append((
                    name,
                    sat,
                    refstr2,
                    utf8snp_filename,
                    paths[utf8snp_filename]
                ))
            else:
                # Picon missing - generate symlink suggestion
                symlink = ""
                if utf8snp_name:
                    symlink = "ln -s ./%s ./%s" % (utf8snp_filename, oldPiconName2)

                messages.append((
                    sanitized_name if name else "",
                    utf8snp_filename,
                    oldPiconName2,
                    sat,
                    int(ref[4]),
                    ocram_str,
                    symlink
                ))

            i += 1
            if i % 100 == 0:
                print("Processed %i channels..." % (i))

            serviceTypes.append(int(ref[4]))

    print("Sorting logs...")

    # Sort found picons by channel name
    messages1 = sortByValue(messages1, 0)

    # Sort missing picons according to sortOrder
    if sortOrder:
        messages = sortByValueRecursive(messages, sortOrder)
    else:
        messages = sortByValue(messages, 0)

    # Create ZIP file with logs
    try:
        zf = zipfile.ZipFile(outfile, mode='w', compression=zipfile.ZIP_DEFLATED)

        # Write found picons log
        print("Writing found picons log...")
        log_header = 'Channel name,Orbital,Service ref,Picon name,Picon path\n'
        log_lines = [log_header]

        for message in messages1:
            # Remove control characters from channel name
            control_chars = ''.join(map(chr, list(range(0, 32)) + list(range(127, 160))))
            control_char_re = re.compile('[%s]' % re.escape(control_chars))
            clean_name = control_char_re.sub('', message[0])

            log_lines.append('"%s","%s","%s","%s","%s"\n' % (
                clean_name,
                satname(message[1]),
                message[2],
                message[3],
                message[4]
            ))

        zf.writestr(outlog1 + logExt, "".join(log_lines))

        # Write missing picons log
        print("Writing missing picons log...")
        log_header = 'Channel name,SRP name,SNP name,Ocram database,Orbital,DVB type,Symlink\n'
        log_lines = [log_header]

        for message in messages:
            srp_name = message[2][:-4]  # Remove .png extension
            snp_name = message[1][:-4]  # Remove .png extension
            orbital = satname(message[3])

            log_lines.append('"%s","%s","%s","%s","%s",%i,"%s"\n' % (
                message[0],
                srp_name,
                snp_name,
                message[5],
                orbital,
                message[4],
                message[6]
            ))

        zf.writestr(outlog2 + logExt, "".join(log_lines))

        zf.close()
        print("Task completed. Output saved in %s." % (outfile))

    except Exception as e:
        print("Error creating ZIP file: %s" % str(e))
        return


def sortByValue(inputList, sortKey):
    # Sort case insensitive
    return sorted(inputList, key=lambda listItem:
                  listItem[sortKey].lower() if isinstance(listItem[sortKey], str)
                  else listItem[sortKey])


def sortByValueRecursive(inputList, sortKey=[], level=0):
    # For sorting nested arrays
    if isinstance(sortKey, int):
        sortKey = [sortKey]

    if len(sortKey) < 1 or len(sortKey) > len(inputList[0]):
        return inputList

    if len(sortKey) == 1:
        return sorted(inputList, key=lambda listItem:
                      (listItem[sortKey[0]] if isinstance(listItem[sortKey[0]], int)
                       else listItem[sortKey[0]].lower()))

    firstSortKey = sortKey.pop(0)
    sortDict = {}

    for listItem in inputList:
        listItemSortKey = (listItem[firstSortKey] if isinstance(listItem[firstSortKey], int)
                           else listItem[firstSortKey].lower())

        if listItemSortKey not in sortDict:
            sortDict[listItemSortKey] = []

        sortDict[listItemSortKey].append(listItem)

    # Sort the keys
    sortedKeys = sorted(sortDict.keys())

    # Recursively sort each group
    for key in sortedKeys:
        sortDict[key] = sortByValueRecursive(sortDict[key], sortKey[:], level + 1)

    # Flatten the result
    result = []
    for key in sortedKeys:
        result.extend(sortDict[key])

    return result


def satname(slot):
    if slot == 65535:
        return 'cable'
    elif slot == 61166:
        return 'terrestrial'

    # Normalize satellite position
    while slot < -1800:
        slot += 3600
    while slot > 1800:
        slot -= 3600

    westeast = 'E' if slot >= 0 else 'W'
    position = abs(slot) / 10.0

    # Round to 1 decimal place
    position = round(position, 1)

    return str(position) + westeast


def slot1(namespace):
    # Extract satellite position from namespace
    if len(namespace) < 4:
        return 0
    return int(namespace[:len(namespace) - 4], 16)


def sanitizeFilename(filename, maxlen=255):
    # Return a safe version of the filename
    blacklist = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|", "\0"]
    reserved = [
        "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5",
        "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5",
        "LPT6", "LPT7", "LPT8", "LPT9",
    ]

    # Remove blacklisted chars and control characters
    filename = "".join(c for c in filename if c not in blacklist and ord(c) > 31)

    # Normalize Unicode
    filename = unicodedata.normalize("NFKD", filename).strip()

    # Handle reserved names or all-dots filenames
    if all([x == "." for x in filename]) or filename.upper() in reserved:
        filename = "__" + filename

    # Split into root and extension
    root, ext = os.path.splitext(filename.encode('utf-8', errors='ignore'))

    # Ensure total length doesn't exceed maxlen
    if len(ext) > maxlen - 1:
        ext = ext[:maxlen - 1]

    root_max_len = maxlen - len(ext)
    if root_max_len < 1:
        root_max_len = 1

    root = root[:root_max_len]

    # Convert back to Unicode
    filename = root.decode('utf-8', errors='ignore') + ext.decode('utf-8', errors='ignore')

    # Remove trailing dots and spaces
    filename = filename.rstrip(". ")

    if len(filename) == 0:
        filename = "__"

    return filename


if __name__ == "__main__":
    missingPiconsUTF8SNP()  # Call the main function
