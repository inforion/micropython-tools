"""This module contains functions that are missed in micropython os package.
All functions work almost the same way as normal python3 os module functions do."""
import os
import errno
from osadditions.path import dirname, isfile, isdir, split, abspath


def makedirs(name: str, mode=None, exist_ok: bool = True) -> None:
    """Create all dirs in path. If directory does not exist, this directory would be created."""
    if mode is not None:
        raise ValueError("Mode argument is not supported on this platform.")
    cwd = os.getcwd()
    slash_i = name.find("/")
    if slash_i == -1:
        fir_part, sec_part = name, ""
    else:
        if slash_i == 0:
            slash_i = name.find("/", slash_i+1)
            fir_part, sec_part = (name, "") if slash_i == -1 else (name[:slash_i], name[slash_i+1:])
        else:
            fir_part, sec_part = name[:slash_i], name[slash_i+1:]
    # The code above is written to handle state when user tries to create dir in /.
    # It is impossible to do this. But there will be no exception if you try to os.chdir("/") and then os.chdir("anyD")
    # But if if you run os.chdir("/anyD") the exception will occur.
    try:
        os.chdir(fir_part)
        if not exist_ok:
            os.chdir(cwd)
            raise FileExistsError("File exists: '%s'" % fir_part)
    except OSError:
        try:
            os.mkdir(fir_part)
        except OSError:
            os.chdir(cwd)
            raise ValueError("Directory %s could not be created. "
                             "Creating dirs in / is not permitted on this platform." % fir_part)
        os.chdir(fir_part)
    if sec_part != "":
        makedirs(sec_part)
    os.chdir(cwd)


def truncate(path: str, length: int) -> None:
    """Truncate the file corresponding to path, so that it is at most length bytes in size."""
    with open(path, 'rb') as f:
        buf = f.read(length)
    with open(path, 'wb') as f:
        f.write(buf)


def renames(old: str, new: str) -> None:
    """Recursive directory or file renaming function."""
    if isfile(old):
        makedirs(dirname(new))
    elif isdir(old):
        makedirs(dirname(dirname(new)))  # return parent directory name of dir which is passed as new argument
    os.rename(old, new)


def removedirs(path: str):
    """Remove directories recursively."""
    abs_path = abspath(path)
    path_head = split(abs_path)[0]
    try:
        os.rmdir(abs_path)
    except OSError as e:
        if e.args[0] == errno.EACCES:
            return
        else:
            raise
    if path_head != "/sd" and path_head != "/flash":  # PyBoard restriction: you can not remove this two folders in /
        removedirs(path_head)


def walk(top: str, topdown=True):
    """Generate the file names in a directory tree by walking the tree either top-down or bottom-up."""
    cwd = os.getcwd()
    files = []
    dirs = []
    for dirent in os.ilistdir(top):
        os.chdir(top)
        fname = dirent[0]
        if isdir(fname):
            dirs.append(fname)
        else:
            files.append(fname)
    os.chdir(cwd)
    if topdown:
        yield top, dirs, files
    for d in dirs:
        yield from walk(top + "/" + d, topdown)
    if not topdown:
        yield top, dirs, files


def replace(src: str, dst: str):
    """Replace the file or directory src to dst. """
    if isfile(src) and isfile(dst):
        with open(src, 'rb') as srcf:
            with open(dst, 'wb') as dstf:
                dstf.write(srcf.read())
    elif isfile(src) and isdir(dst):
        raise OSError("Is a directory: '%s' -> '%s'" % (src, dst))
    elif isdir(src) and isfile(dst):
        raise OSError("Not a directory: '%s' -> '%s'" % (src, dst))
    elif isdir(src) and isdir(src):
        os.rmdir(dst)
        os.rename(src, dst)
