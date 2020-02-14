"""This module contains common logging functions. It works almost the same way as normal python3 logging module does."""
import sys
from micropython import const

from stylization import style_func_stream

CRITICAL = const(50)
ERROR = const(40)
WARNING = const(30)
INFO = const(20)
DEBUG = const(10)
NOTSET = const(0)

_level_dict = {
    CRITICAL: "CRIT",
    ERROR: "ERROR",
    WARNING: "WARN",
    INFO: "INFO",
    DEBUG: "DEBUG",
}
_stream = sys.stderr


def _colorize(fg, stylename=None, bg=None):
    """Decorator to choose whether to colorize output stream or not."""
    def decorator(func):
        def wrapper(*args, **kwds):
            style_func_stream(_stream, fg=fg, stylename=stylename, bg=bg)\
                (func)\
                (*args, **kwds) if _colorize_enable else func(*args, **kwds)
        return wrapper
    return decorator


class Logger:
    level = NOTSET

    def __init__(self, name: str) -> None:
        self.name = name

    def _level_str(self, level: int) -> str:
        """Get level name by its int level number."""
        l = _level_dict.get(level)
        if l is not None:
            return l
        return "LVL%s" % level

    def set_level(self, level: int) -> None:
        """Set logging level."""
        self.level = level

    def is_enabled_for(self, level: int) -> bool:
        """Formatting of message arguments is deferred until it cannot be avoided.
        However, computing the arguments passed to the logging method can also be expensive,
        and you may want to avoid doing it if the logger will just throw away your event.
        Example usage:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('Message with %s, %s', expensive_func1(),
                                                expensive_func2())"""
        return level >= (self.level or _level)

    def log(self, level: int, msg: str, *args) -> None:
        """Write message to output stream."""
        if level >= (self.level or _level):
            msg_string = msg if not args else msg % args
            _stream.write("%s:%s:%s\n" % (self._level_str(level), self.name, msg_string))

    @_colorize(fg="green")
    def debug(self, msg: str, *args) -> None:
        """Display debug level message."""
        self.log(DEBUG, msg, *args)

    @_colorize(fg="blue")
    def info(self, msg: str, *args) -> None:
        """Display info level message."""
        self.log(INFO, msg, *args)

    @_colorize(fg="yellow")
    def warning(self, msg: str, *args) -> None:
        """Display warning level message."""
        self.log(WARNING, msg, *args)

    @_colorize(fg="red")
    def error(self, msg: str, *args) -> None:
        """Display error level message."""
        self.log(ERROR, msg, *args)

    @_colorize(fg="red", stylename="bold", bg="black")
    def critical(self, msg: str, *args):
        """Display critical level message."""
        self.log(CRITICAL, msg, *args)

    @_colorize(fg="red")
    def exception(self, e, msg: str, *args) -> None:
        """Display exception message and exception trace."""
        self.log(ERROR, msg, *args)
        sys.print_exception(e, _stream)


_level = INFO
_colorize_enable = True
_loggers = {}


def get_logger(name) -> Logger:
    """Get logger by name or create it by name if it does not exist."""
    if name in _loggers:
        return _loggers[name]
    l = Logger(name)
    _loggers[name] = l
    return l


def info(msg: str, *args) -> None:
    """Create info message with no logger name specified."""
    get_logger(None).info(msg, *args)


def debug(msg: str, *args) -> None:
    """Create debug message with no logger name specified."""
    get_logger(None).debug(msg, *args)


def basic_config(level: int = INFO, filename=None, stream=None, format=None, colorize: bool = True) -> None:
    """Function sets basic config setting of logging module."""
    global _level, _stream, _colorize_enable
    _level = level
    _colorize_enable = colorize
    if filename is not None:
        raise ValueError("filename argument is not supported on this platform.")
    else:
        if stream:
            _stream = stream
    if format is not None:
        raise ValueError("format argument is not supported on this platform.")
