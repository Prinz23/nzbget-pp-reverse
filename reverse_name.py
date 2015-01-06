#!/usr/bin/env python
#
##############################################################################
### NZBGET POST-PROCESSING SCRIPT                                          ###

# Reverse filenames.
#
# NOTE: This script requires Python to be installed on your system.

##############################################################################
### OPTIONS                                                                ###

### NZBGET POST-PROCESSING SCRIPT                                          ###
##############################################################################

import os
import sys
import re

reverse_list = [r"\.\d{2}e\d{2}s\.", r"\.p0612\.", r"\.[pi]0801\.", r"\.p027\.", r"\.[pi]675\.", r"\.[pi]084\.", r"\.p063\.", r"\b[45]62[xh]\.", r"\.yarulb\.", r"\.vtd[hp]\.", 
                r"\.ld[.-]?bew\.", r"\.pir.?(shv|dov|dvd|bew|db|rb)\.", r"\brdvd\.", r"\.vts\.", r"\.reneercs\.", r"\.dcv\.", r"\b(pir|mac)dh\b", r"\.reporp\.", r"\.kcaper\.", 
                r"\.lanretni\.", r"\b3ca\b", r"\bcaa\b", r"\b3pm\b", r"\.cstn\.", r"\.5r\.", r"\brcs\b"]
reverse_pattern = re.compile('|'.join(reverse_list), flags=re.IGNORECASE)
season_pattern = re.compile(r"(.*\.\d{2}e\d{2}s\.)(.*)", flags=re.IGNORECASE)
word_pattern = re.compile(r"([^A-Z0-9]*[A-Z0-9]+)")
char_replace = [[r"(\w)1\.(\w)",r"\1i\2"]
]
garbage_name = re.compile(r"^[a-zA-Z0-9]{3,}$")
media_list = [r"\.s\d{2}e\d{2}\.", r"\.2160p\.", r"\.1080[pi]\.", r"\.720p\.", r"\.576[pi]\.", r"\.480[pi]\.", r"\.360p\.", r"\.[xh]26[45]\b", r"\.bluray\.", r"\.[hp]dtv\.", 
              r"\.web[.-]?dl\.", r"\.(vhs|vod|dvd|web|bd|br).?rip\.", r"\.dvdr\b", r"\.stv\.", r"\.screener\.", r"\.vcd\.", r"\bhd(cam|rip)\b", r"\.proper\.", r"\.repack\.", 
              r"\.internal\.", r"\bac3\b", r"\baac\b", r"\bmp3\b", r"\.ntsc\.", r"\.pal\.", r"\.secam\.", r"\bdivx\b", r"\bxvid\b", r"\.r5\.", r"\.scr\."]
media_pattern = re.compile('|'.join(media_list), flags=re.IGNORECASE)
media_extentions = [".mkv", ".mp4", ".avi", ".wmv", ".divx", ".xvid"]

# NZBGet V11+
# Check if the script is called from nzbget 11.0 or later
if os.environ.has_key('NZBOP_SCRIPTDIR') and not os.environ['NZBOP_VERSION'][0:5] < '11.0':
    print "[INFO] Script triggered from NZBGet (11.0 or later)."

    # NZBGet argv: all passed as environment variables.
    clientAgent = "nzbget"
    # Exit codes used by NZBGet
    POSTPROCESS_PARCHECK=92
    POSTPROCESS_SUCCESS=93
    POSTPROCESS_ERROR=94
    POSTPROCESS_NONE=95

    # Check nzbget.conf options
    status = 0

    if os.environ['NZBOP_UNPACK'] != 'yes':
        print "[INFO] Please enable option \"Unpack\" in nzbget configuration file, exiting"
        sys.exit(POSTPROCESS_NONE)

    # Check par status
    if os.environ['NZBPP_PARSTATUS'] == '3':
        print "[INFO] Par-check successful, but Par-repair disabled, exiting"
        sys.exit(POSTPROCESS_NONE)

    if os.environ['NZBPP_PARSTATUS'] == '1':
        print "[INFO] Par-check failed, setting status \"failed\""
        status = 1
        sys.exit(POSTPROCESS_NONE)

    # Check unpack status
    if os.environ['NZBPP_UNPACKSTATUS'] == '1':
        print "[INFO] Unpack failed, setting status \"failed\""
        status = 1
        sys.exit(POSTPROCESS_NONE)

    if os.environ['NZBPP_UNPACKSTATUS'] == '0' and os.environ['NZBPP_PARSTATUS'] != '2':
        # Unpack is disabled or was skipped due to nzb-file properties or due to errors during par-check

        for dirpath, dirnames, filenames in os.walk(os.environ['NZBPP_DIRECTORY']):
            for file in filenames:
                fileExtension = os.path.splitext(file)[1]

                if fileExtension in ['.par2']:
                    print "[INFO] Post-Process: Unpack skipped and par-check skipped (although par2-files exist), setting status \"failed\"g"
                    status = 1
                    break

        if os.path.isfile(os.path.join(os.environ['NZBPP_DIRECTORY'], "_brokenlog.txt")) and not status == 1:
            print "[INFO] Post-Process: _brokenlog.txt exists, download is probably damaged, exiting"
            status = 1

        if not status == 1:
            print "[INFO] Neither par2-files found, _brokenlog.txt doesn't exist, considering download successful"

    # Check if destination directory exists (important for reprocessing of history items)
    if not os.path.isdir(os.environ['NZBPP_DIRECTORY']):
        print "[INFO] Post-Process: Nothing to post-process: destination directory ", os.environ['NZBPP_DIRECTORY'], "doesn't exist"
        status = 1

    # All checks done, now launching the script.

    rd = False
    videos = 0
    old_name = None
    new_name = None
    for dirpath, dirnames, filenames in os.walk(os.environ['NZBPP_DIRECTORY']):
        for file in filenames:

            filePath = os.path.join(dirpath, file)
            fileName, fileExtension = os.path.splitext(file)
            dirname = os.path.dirname(filePath)

            if reverse_pattern.search(fileName) is not None:
                na_parts = season_pattern.search(fileName)
                if na_parts is not None:
                    word_p = word_pattern.findall(na_parts.group(2))
                    new_words = ""
                    for wp in word_p:
                        if wp[0] == ".":
                            new_words += "."
                        new_words += re.sub(r"\W","",wp)
                    for cr in char_replace:
                        new_words = re.sub(cr[0],cr[1],new_words)
                    new_filename = new_words[::-1] + na_parts.group(1)[::-1]
                else:
                    new_filename = fileName[::-1]
                print "[INFO] reversing filename from: ", fileName, " to ", new_filename 
                try:
                    os.rename(filePath, os.path.join(dirpath, new_filename + fileExtension))
                    rd = True
                except Exception,e:
                    print "[INFO] " + str(e)
                    print "[INFO] Error: unable to rename file ", file
                    pass
            elif (fileExtension.lower() in media_extentions) and (garbage_name.search(fileName) is not None) and (media_pattern.search(os.path.basename(dirname)) is not None):
                videos += 1
                old_name = filePath
                new_name = os.path.join(dirname, os.path.basename(dirname) + fileExtension)

    if not rd and videos == 1 and old_name is not None and new_name is not None:
        print "[INFO] renaming the File " + os.path.basename(old_name) + " to the Dirname " + os.path.basename(os.path.dirname(new_name))
        try:
            os.rename(old_name, new_name)
            rd = True
        except Exception,e:
            print "[INFO] " + str(e)
            print "[INFO] Error unable to rename file ", old_name
            pass

    if rd:
        sys.exit(POSTPROCESS_SUCCESS)
    else:
        sys.exit(POSTPROCESS_NONE)

else:
    print "[ERROR] This script can only be called from NZBGet (11.0 or later)."
    sys.exit(0)
