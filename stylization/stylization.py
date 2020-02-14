"""This module contains various stylization functions of text appearance."""
import sys

_style_dict = {
    "reset": "\033[0m",
    "bold": "\033[01m",
    "disable": '\033[02m',
    "underline": '\033[04m',
    "reverse": '\033[07m',
    "strikethrough": '\033[09m',
    "invisible": '\033[08m'
}

_fg_dict = {
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "orange": "\033[33m",
    "blue": "\033[34m",
    "purple": "\033[35m",
    "cyan": "\033[36m",
    "lightgrey": "\033[37m",
    "darkgrey": "\033[90m",
    "lightred": "\033[91m",
    "lightgreen": "\033[92m",
    "yellow": "\033[93m",
    "lightblue": "\033[94m",
    "pink": "\033[95m",
    "lightcyan": "\033[96m"
}
_bg_dict = {
    "black": "\033[40m",
    "red": "\033[41m",
    "green": "\033[42m",
    "orange": "\033[43m",
    "blue": "\033[44m",
    "purple": "\033[45m",
    "cyan": "\033[46m",
    "lightgrey": "\033[47m"
}


def _names2ascii(fg=None, stylename=None, bg=None) -> str:
    """Convert names of foreground, styles and background to ASCII symbols string"""
    fg_string = _fg_dict[fg] if fg is not None else ""
    bg_string = _bg_dict[bg] if bg is not None else ""
    st_string = ""
    if stylename is not None:
        style_list = stylename.split(" ")
        for style_item in style_list:
            st_string = "".join((st_string, _style_dict[style_item]))
    st_bg_fg_str = "".join((
        st_string,
        fg_string,
        bg_string))
    return st_bg_fg_str


def style_string(string: str, fg=None, stylename=None, bg=None) -> str:
    """Apply styles to text.
    It is able to change style (like bold, underline etc), foreground and background colors of text string."""
    ascii_str = _names2ascii(fg, stylename, bg)
    return "".join((
        ascii_str,
        string,
        _style_dict["reset"]))


def style_func_stream(stream=sys.stdout, fg=None, stylename=None, bg=None):
    """Apply styles to stream and call the .
    It is able to change style (like bold, underline etc), foreground and background colors of text string.
    Example usage:
    style_stream(_stream, fg=fg, stylename=stylename,bg=bg)\
                        (sys.print_exception)\
                        (e, _stream)
    Also you may use it as decorator function."""
    def decorator(func):
        def wrapper(*args, **kwds):
            ascii_str = _names2ascii(fg, stylename, bg)
            stream.write(ascii_str)
            func(*args, **kwds)
            stream.write(_style_dict["reset"])
        return wrapper
    return decorator


def _chunks(l: bytearray, n: int):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def hexdump(bytebuffer: bytearray, offset: int = 0):
    """Print hexdump of bytearray from offset"""
    for i, chunk in enumerate(_chunks(bytebuffer, 16)):
        print("%08X: " % (i * 16 + offset), end="")
        for byte in chunk[:8]:
            print('%02X ' % byte, end="")
        print(' ', end="")
        for byte in chunk[8:]:
            print('%02X ' % byte, end="")
        for k in range(16 - len(chunk)):
            print('%2s ' % " ", end="")
        print(' | ', end="")
        for byte in chunk:
            if 0x20 <= byte <= 0x7F:
                print("%c" % chr(byte), end="")
            else:
                print(".", end="")
        print()

