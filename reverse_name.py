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
import locale

reverse_list = [r"\.\d{2}e\d{2}s\.", r"\.p0612\.", r"\.[pi]0801\.", r"\.p027\.", r"\.[pi]675\.", r"\.[pi]084\.", r"\.p063\.", r"\b[45]62[xh]\.", r"\.yarulb\.", r"\.vtd[hp]\.",
                r'\.(?:ld[.-]?)?bew\.', r"\.pir.?(shv|dov|bew|dvd|db|rb)\.", r"\brdvd\.", r"\.vts\.", r"\.reneercs\.", r"\.dcv\.", r"\b(pir|mac)dh\b", r"\.reporp\.", r"\.kcaper\.",
                r"\.lanretni\.", r"\b3ca\b", r"\bcaa\b", r"\b3pm\b", r"\.cstn\.", r"\.5r\.", r"\brcs\b"]
reverse_pattern = re.compile('|'.join(reverse_list), flags=re.IGNORECASE)
season_pattern = re.compile(r"(.*\.\d{2}e\d{2}s\.)(.*)", flags=re.IGNORECASE)
word_pattern = re.compile(r"([^A-Z0-9]*[A-Z0-9]+)")
char_replace = [[r"(\w)1\.(\w)",r"\1i\2"]
]
garbage_name = re.compile(r"^[a-zA-Z0-9]{2,}$")
media_list = [r"\.s\d{2}e\d{2}\.", r"\.2160p\.", r"\.1080[pi]\.", r"\.720p\.", r"\.576[pi]\.", r"\.480[pi]\.", r"\.360p\.", r"\.[xh]26[45]\b", r"\.bluray\.", r"\.[hp]dtv\.",
              r'\.web(?:[.-]?dl)?\.', r"\.(vhs|vod|dvd|web|bd|br).?rip\.", r"\.dvdr\b", r"\.stv\.", r"\.screener\.", r"\.vcd\.", r"\bhd(cam|rip)\b", r"\.proper\.", r"\.repack\.",
              r"\.internal\.", r"\bac3\b", r"\baac\b", r"\bmp3\b", r"\.ntsc\.", r"\.pal\.", r"\.secam\.", r"\bdivx\b", r"\bxvid\b", r"\.r5\.", r"\.scr\."]
media_pattern = re.compile('|'.join(media_list), flags=re.IGNORECASE)
media_extentions = [".mkv", ".mp4", ".avi", ".wmv", ".divx", ".xvid"]

PY2 = 2 == sys.version_info[0]

if not PY2:
    string_types = str,
    text_type = str

    def iteritems(d, **kw):
        return iter(d.items(**kw))
else:
    # noinspection PyUnresolvedReferences
    string_types = basestring,
    # noinspection PyUnresolvedReferences
    text_type = unicode

    def iteritems(d, **kw):
        # noinspection PyCompatibility
        return d.iteritems(**kw)


class EnvVar(object):
    def __init__(self):
        pass

    def __getitem__(self, key):
        return os.environ[key]

    @staticmethod
    def get(key, default=None):
        return os.environ.get(key, default)


if not PY2:
    env_var = EnvVar()

elif 'nt' == os.name:
    from ctypes import windll, create_unicode_buffer

    # noinspection PyCompatibility
    class WinEnvVar(EnvVar):

        @staticmethod
        def get_environment_variable(name):
            name = text_type(name)  # ensures string argument is unicode
            n = windll.kernel32.GetEnvironmentVariableW(name, None, 0)
            env_value = None
            if n:
                buf = create_unicode_buffer(u'\0' * n)
                windll.kernel32.GetEnvironmentVariableW(name, buf, n)
                env_value = buf.value
            return env_value

        def __getitem__(self, key):
            return self.get_environment_variable(key)

        def get(self, key, default=None):
            r = self.get_environment_variable(key)
            return r if None is not r else default

    env_var = WinEnvVar()
else:
    class LinuxEnvVar(EnvVar):
        # noinspection PyMissingConstructor
        def __init__(self, environ):
            self.environ = environ

        def __getitem__(self, key):
            v = self.environ.get(key)
            try:
                return v if not isinstance(v, str) else v.decode(SYS_ENCODING)
            except (UnicodeDecodeError, UnicodeEncodeError):
                return v

        def get(self, key, default=None):
            v = self[key]
            return v if None is not v else default

    env_var = LinuxEnvVar(os.environ)

SYS_ENCODING = None

try:
    locale.setlocale(locale.LC_ALL, '')
except (locale.Error, IOError):
    pass
try:
    SYS_ENCODING = locale.getpreferredencoding()
except (locale.Error, IOError):
    pass

if not SYS_ENCODING or SYS_ENCODING in ('ANSI_X3.4-1968', 'US-ASCII', 'ASCII'):
    SYS_ENCODING = 'UTF-8'


# noinspection PyCompatibility
class Ek(object):
    def __init__(self):
        pass

    @staticmethod
    def fix_string_encoding(x):
        if not PY2:
            return x

        if str == type(x):
            try:
                return x.decode(SYS_ENCODING)
            except UnicodeDecodeError:
                pass
        elif text_type == type(x):
            return x

    @staticmethod
    def fix_out_encoding(x):
        if PY2 and isinstance(x, string_types):
            return Ek.fix_string_encoding(x)
        return x

    @staticmethod
    def fix_list_encoding(x):
        if not PY2:
            return x

        if type(x) not in (list, tuple):
            return x
        return filter(lambda i: None is not i, map(Ek.fix_out_encoding, x))

    @staticmethod
    def encode_item(x):
        if not PY2:
            return x

        try:
            return x.encode(SYS_ENCODING)
        except UnicodeEncodeError:
            return x.encode(SYS_ENCODING, 'ignore')

    @staticmethod
    def win_encode_unicode(x):
        if PY2 and isinstance(x, str):
            try:
                return x.decode('UTF-8')
            except UnicodeDecodeError:
                pass
        return x

    @staticmethod
    def ek(func, *args, **kwargs):
        if not PY2:
            return func(*args, **kwargs)

        if 'nt' == os.name:
            # convert all str parameter values to unicode
            args = tuple([x if not isinstance(x, str) else Ek.win_encode_unicode(x) for x in args])
            kwargs = {k: x if not isinstance(x, str) else Ek.win_encode_unicode(x) for k, x in iteritems(kwargs)}
            func_result = func(*args, **kwargs)
        else:
            func_result = func(*[Ek.encode_item(x) if type(x) == str else x for x in args], **kwargs)

        if type(func_result) in (list, tuple):
            return Ek.fix_list_encoding(func_result)
        elif str == type(func_result):
            return Ek.fix_string_encoding(func_result)
        return func_result


def ex(exc):
    """Returns a unicode string from the exception text if it exists"""

    if not PY2:
        return str(exc)

    e_message = u''

    if not exc or not exc.args:
        return e_message

    for arg in exc.args:

        if None is not arg:
            if isinstance(arg, (str, text_type)):
                fixed_arg = Ek.fix_string_encoding(arg)

            else:
                try:
                    fixed_arg = u'error ' + Ek.fix_string_encoding(str(arg))

                except (BaseException, Exception):
                    fixed_arg = None

            if fixed_arg:
                if not e_message:
                    e_message = fixed_arg

                else:
                    e_message = e_message + ' : ' + fixed_arg

    return e_message


class Logger(object):
    INFO, DETAIL, ERROR, WARNING = 'INFO', 'DETAIL', 'ERROR', 'WARNING'
    # '[NZB]' send a command message to NZBGet (no log)
    NZB = 'NZB'

    def __init__(self):
        pass

    @staticmethod
    def safe_print(msg_type, message):
        if not PY2:
            print('[%s] %s' % (msg_type, message))
        else:
            try:
                print('[%s] %s' % (msg_type, message.encode(SYS_ENCODING)))
            except (BaseException, Exception):
                try:
                    print('[%s] %s' % (msg_type, message))
                except (BaseException, Exception):
                    try:
                        print('[%s] %s' % (msg_type, repr(message)))
                    except (BaseException, Exception):
                        pass

    @staticmethod
    def log(message, msg_type=INFO):
        size = 900
        if size > len(message):
            Logger.safe_print(msg_type, message)
        else:
            for group in [message[pos:pos + size] for pos in range(0, len(message), size)]:
                Logger.safe_print(msg_type, group)


def tryInt(s, s_default=0):
    try:
        return int(s)
    except:
        return s_default

# NZBGet V11+
# Check if the script is called from nzbget 11.0 or later
nzbget_version = env_var.get('NZBOP_VERSION', '0.1')
nzbget_version = tryInt(nzbget_version[:nzbget_version.find(".")])
if nzbget_version >= 11:
    Logger.log("Script triggered from NZBGet (11.0 or later).")

    # NZBGet argv: all passed as environment variables.
    clientAgent = "nzbget"
    # Exit codes used by NZBGet
    POSTPROCESS_PARCHECK=92
    POSTPROCESS_SUCCESS=93
    POSTPROCESS_ERROR=94
    POSTPROCESS_NONE=95

    # Check nzbget.conf options
    status = 0

    if env_var['NZBOP_UNPACK'] != 'yes':
        Logger.log("Please enable option \"Unpack\" in nzbget configuration file, exiting")
        sys.exit(POSTPROCESS_NONE)

    parstatus = env_var['NZBPP_PARSTATUS']

    # Check par status
    if parstatus == '3':
        Logger.log("Par-check successful, but Par-repair disabled, exiting")
        sys.exit(POSTPROCESS_NONE)

    if parstatus == '1':
        Logger.log("Par-check failed, setting status \"failed\"")
        status = 1
        sys.exit(POSTPROCESS_NONE)

    unpackstatus = env_var['NZBPP_UNPACKSTATUS']

    # Check unpack status
    if unpackstatus == '1':
        Logger.log("Unpack failed, setting status \"failed\"")
        status = 1
        sys.exit(POSTPROCESS_NONE)

    directory = env_var['NZBPP_DIRECTORY']

    if unpackstatus == '0' and parstatus != '2':
        # Unpack is disabled or was skipped due to nzb-file properties or due to errors during par-check

        for dirpath, dirnames, filenames in Ek.ek(os.walk, directory):
            for file in filenames:
                fileExtension = Ek.ek(os.path.splitext, file)[1]

                if fileExtension in ['.par2']:
                    Logger.log("Post-Process: Unpack skipped and par-check skipped (although par2-files exist), setting status \"failed\"g")
                    status = 1
                    break

        if Ek.ek(os.path.isfile, Ek.ek(os.path.join, directory, "_brokenlog.txt")) and not status == 1:
            Logger.log("Post-Process: _brokenlog.txt exists, download is probably damaged, exiting")
            status = 1

        if not status == 1:
            Logger.log("Neither par2-files found, _brokenlog.txt doesn't exist, considering download successful")

    # Check if destination directory exists (important for reprocessing of history items)
    if not Ek.ek(os.path.isdir, directory):
        Logger.log("Post-Process: Nothing to post-process: destination directory %s doesn't exist" % directory)
        status = 1

    # All checks done, now launching the script.

    rd = False
    videos = 0
    old_name = None
    new_name = None
    base_name = Ek.ek(os.path.basename, directory)
    for dirpath, dirnames, filenames in Ek.ek(os.walk, directory):
        for file in filenames:

            filePath = Ek.ek(os.path.join, dirpath, file)
            fileName, fileExtension = Ek.ek(os.path.splitext, file)
            dirname = Ek.ek(os.path.dirname, filePath)

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
                Logger.log("reversing filename from: %s to %s" % (fileName, new_filename))
                try:
                    Ek.ek(os.rename, filePath, Ek.ek(os.path.join, dirpath, new_filename + fileExtension))
                    rd = True
                except Exception as e:
                    Logger.log(ex(e), Logger.ERROR)
                    Logger.log("Error: unable to rename file %s" % file, Logger.ERROR)
                    pass
            elif (fileExtension.lower() in media_extentions) and (garbage_name.search(fileName) is not None) and (media_pattern.search(base_name) is not None):
                videos += 1
                old_name = filePath
                new_name = Ek.ek(os.path.join, dirname, '%s%s' % (base_name, fileExtension))

    if not rd and videos == 1 and old_name is not None and new_name is not None:
        Logger.log("renaming the File %s  to the Dirname %s" % (Ek.ek(os.path.basename, old_name), base_name))
        try:
            Ek.ek(os.rename, old_name, new_name)
            rd = True
        except Exception as e:
            Logger.log(ex(e), Logger.ERROR)
            Logger.log("Error unable to rename file %s" % old_name, Logger.ERROR)
            pass

    if rd:
        sys.exit(POSTPROCESS_SUCCESS)
    else:
        sys.exit(POSTPROCESS_NONE)

else:
    Logger.log("This script can only be called from NZBGet (11.0 or later).", Logger.ERROR)
    sys.exit(0)
