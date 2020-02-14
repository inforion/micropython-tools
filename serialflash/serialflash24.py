"""This module contains functions for serial IC ROM 24xxxx series actions."""
from micropython import const
from pyb import Pin, I2C, delay

import logging
from osadditions import makedirs
from osadditions.path import dirname, isfile, getsize

log = logging.get_logger(__name__)

MAX_READ_ITEM_SIZE = const(128)


class SerialFlash24:
    """Class to communicate Serial EEPROM Memory 24xxxx series with."""

    def __init__(self,
                 name: str,
                 size: int,
                 i2c: int,
                 wp: str,
                 a0: str,
                 a1: str,
                 a2: str,
                 i2c_addr: int = 80,
                 addr_bytes_num: int = 16
                 ) -> None:
        self.name = name
        self.size = size
        self.addr_bytes_num = addr_bytes_num
        self.a0 = Pin(a0, Pin.OUT_PP)
        self.a1 = Pin(a1, Pin.OUT_PP)
        self.a2 = Pin(a2, Pin.OUT_PP)
        self.wp = Pin(wp, Pin.OUT_PP)
        self.i2c = I2C(i2c, I2C.MASTER, baudrate=20000)
        # item_size to prevent memory allocation error in dump()
        self.item_size = size if size <= MAX_READ_ITEM_SIZE else MAX_READ_ITEM_SIZE
        self.items_cnt = self.size // self.item_size
        self.i2c_addr = i2c_addr

    def dump(self, path: str) -> None:
        """Dump all device contents to binary file."""
        makedirs(dirname(path))
        with open(path, 'wb') as f:
            for i in range(0, self.items_cnt):
                buf = self.read(i * self.item_size, self.item_size)
                f.write(buf)
                del buf
        log.info("Dump finished. %s image -> %s" % (self.name, path))

    def program(self, path: str):
        """Flash binary to device."""
        if not isfile(path):
            raise FileNotFoundError("File  not found: '%s'" % path)
        filesize = getsize(path)
        if filesize != self.size:
            raise ValueError("File size (0x%02X bytes) doesn't equal IC size (0x%02X bytes)" % (filesize, self.size))
        with open(path, 'rb') as f:
            for i in range(0, self.items_cnt):
                buf = bytearray(f.read(self.item_size))
                self.write(i*self.item_size, buf)
        log.info("Program finished. %s image -> %s" % (path, self.name))

    def chip_erase(self) -> None:
        """Erase chip."""
        for i in range(0, self.items_cnt):
            self.write(i*self.item_size, bytearray([0xFF] * self.item_size))
        log.info("Chip erase finished.")

    def read(self, offset: int, size: int) -> bytearray:
        """Read data from specified offset using specified size."""
        res = self.i2c.mem_read(size, self.i2c_addr, offset, timeout=5000, addr_size=self.addr_bytes_num)
        log.info("Data read 0x%02X-0x%02X finished." % (offset, offset+size))
        return res

    def write(self, offset: int, bytebuffer: bytearray) -> None:
        """Read data from specified offset using specified size."""
        self.i2c.mem_write(bytebuffer, self.i2c_addr, offset, timeout=5000, addr_size=self.addr_bytes_num)
        delay(300)
        log.info("Data write 0x%02X-0x%02X finished." % (offset, offset+len(bytebuffer)))

