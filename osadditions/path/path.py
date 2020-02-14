"""This module contains functions for filesystem actions.
All functions work almost the same way as normal python3 os.path module functions do."""
import os

DIR_TYPE = const(0x4000)
FILE_TYPE = const(0x8000)


def normcase(s: str) -> str:
    """Normalize path case. Just for compatibility with normal python3."""
    return s


def normpath(s: str) -> str:
    """Normalize path. Just for compatibility with normal python3."""
    return s


def abspath(s: str) -> str:
    """Get absolute filepath."""
    return "/".join((os.getcwd(), s)) if s[0] != "/" else s


def join(*args):
    """Concatenation of paths. Just for compatibility with normal python3."""
    return "/".join(args)


def split(path: str):
    """Split path into (head, tail) tuple. Tail is the last path component. Head is all the rest."""
    if path == "":
        return "", ""
    r = path.rsplit("/", 1)
    if len(r) == 1:
        return "", path
    head = "/" if not r[0] else r[0]
    return head, r[1]


def basename(path: str) -> str:
    """Return the base name of pathname path."""
    return split(path)[1]


def dirname(path: str) -> str:
    """Get directory name from filepath."""
    slash_i = path.rfind("/")
    if slash_i == -1:
        return ""
    return path[:slash_i] if slash_i != 0 else "/"


def getsize(path: str):
    """Get size of file in bytes. Dirs are not supported."""
    filename = path[path.rfind("/") + 1:]
    for f in os.ilistdir(dirname(path)):
        if f[0] == filename and f[1] == FILE_TYPE:
            return f[3]
    raise FileNotFoundError("No such file or directory: '%s'." % filename)


def isdir(path: str):
    """Check if a directory exists, or if the path given is a directory.
    Original isdir does follow symlinks, this implementation does not."""
    cwd = os.getcwd()
    slash_i = path.find("/")
    if slash_i == -1:
        fir_part, sec_part = path, ""
    else:
        if slash_i == 0:
            slash_i = path.find("/", slash_i+1)
            fir_part, sec_part = (path, "") if slash_i == -1 else (path[:slash_i], path[slash_i+1:])
        else:
            fir_part, sec_part = path[:slash_i], path[slash_i+1:]
    # The code above is written to handle state when user tries to create dir in /.
    # It is impossible to do this. But there will be no exception if you try to os.chdir("/") and then os.chdir("anyD")
    # But if if you run os.chdir("/anyD") the exception will occur.
    try:
        os.chdir(fir_part)
    except OSError:
        os.chdir(cwd)
        return False
    res = isdir(sec_part) if sec_part != "" else True
    os.chdir(cwd)
    return res


def isabs(path: str):
    """Check if path is an absolute pathname."""
    return path.find("/") == 0


def isfile(path: str):
    """Check if both a file exists and if it is a file.
    Original isfile does follow symlinks, this implementation does not."""
    if isdir(dirname(path)):
        filename = path[path.rfind("/")+1:]
        for f in os.ilistdir(dirname(path)):
            if f[0] == filename and f[1] == FILE_TYPE:
                return True
    return False
