#!/usr/bin/env python
#
##############################################################################
### NZBGET POST-PROCESSING SCRIPT                                          ###

# Reverse filenames.
#
# NOTE: This script requires Python to be installed on your system.

##############################################################################
### OPTIONS                                                                ###

# Also rename Directory (yes, no).
#
# Note: Only used if only one videofile is found in the Directory.
#rename_dir=no

# comma separeted list of video extentions that are used for the Option 
# Rename Dirname to determine if there is more then one videofile
#
#video_ext=.mkv,.avi,.mp4,.wmv

### NZBGET POST-PROCESSING SCRIPT                                          ###
##############################################################################

import os
import sys
import re

reverse_list = [r"\.\d{2}e\d{2}s\.", r"\.[pi]0801\.", r"\.p027\.", r"\b[45]62[xh]\.", r"\.yarulb\.", r"\.vtdh\.", r"\.ld[.-]?bew\.", r"\.pir[dvd|bew|db|rb]\."]
reverse_pattern = re.compile('|'.join(reverse_list), flags=re.IGNORECASE)
season_pattern = re.compile(r"(.*\.\d{2}e\d{2}s\.)(.*)", flags=re.IGNORECASE)
word_pattern = re.compile(r"([^A-Z0-9]*[A-Z0-9]+)")
char_replace = [[r"(\w)1\.(\w)",r"\1i\2"]
]

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

    try:
        rename_dir=os.environ['NZBPO_RENAME_DIR'] == 'yes'
    except:
        rename_dir=False

    rd = False
    videos = 0
    new_dirname = None
    try:
        videoExtensions = os.environ['NZBPO_VIDEO_EXT'].split(',')
    except:
        videoExtensions = ".mkv,.avi,.mp4,.wmv"

    for dirpath, dirnames, filenames in os.walk(os.environ['NZBPP_DIRECTORY']):
        for file in filenames:

            filePath = os.path.join(dirpath, file)
            fileName, fileExtension = os.path.splitext(file)

            if fileExtension in videoExtensions:
                videos += 1

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
                    new_filename = fileName[::-1].title()
                print "[INFO] reversing filename from: ", fileName, " to ", new_filename 
                try:
                    os.rename(filePath, os.path.join(dirpath, new_filename + fileExtension))
                    rd = True
                    if videos == 1:
                        new_dirname = os.path.join(os.path.dirname(os.environ['NZBPP_DIRECTORY']), new_filename)
                except Exception,e:
                    print "[INFO] " + str(e)
                    print "[INFO] Error: unable to rename file ", file
                    pass

    if rd:
        if rename_dir and (videos == 1) and new_dirname is not None:
            print "[INFO] changing Dirname from: ", os.environ['NZBPP_DIRECTORY'], " to ", new_dirname
            try:
                os.rename(os.environ['NZBPP_DIRECTORY'], new_dirname)
            except Exception,e:
                print "[INFO] " + str(e)
                print "[INFO] Error: unable to rename directory ", os.environ['NZBPP_DIRECTORY'], " to ", new_dirname
                pass
        sys.exit(POSTPROCESS_SUCCESS)
    else:
        sys.exit(POSTPROCESS_NONE)

else:
    print "[ERROR] This script can only be called from NZBGet (11.0 or later)."
    sys.exit(0)
