"""This module contains functions for serial IC ROM 25xxxx series actions."""
from micropython import const
from pyb import Pin, SPI

import logging
from osadditions import makedirs
from osadditions.path import dirname, isfile, getsize

log = logging.get_logger(__name__)
# Commands
CMD_WREN = const(0x06)
CMD_WRDI = const(0x04)
CMD_WRSR = const(0x01)
CMD_RDID = const(0x9F)
CMD_RDSR = const(0x05)
CMD_READ = const(0x03)
CMD_FAST_READ = const(0x0B)
CMD_RDSFDP = const(0x5A)
CMD_RES = const(0xAB)
CMD_REMS = const(0x90)
CMD_DREAD = const(0x3B)
CMD_SE = const(0x20)
CMD_BE = const(0x52)
CMD_CE = const(0x60)
CMD_PP = const(0x02)
CMD_RDSCUR = const(0x2B)
CMD_WRSCUR = const(0x2F)
CMD_ENSO = const(0xB1)
CMD_EXSO = const(0xC1)
CMD_DP = const(0xB9)
CMD_RDP = const(0xAB)

DUMMY_BYTE = const(0xFF)
# Status register bit masks
SR_WIP = const(0x01)
SR_WEL = const(0x02)
SR_BP0 = const(0x04)
SR_BP1 = const(0x08)
SR_BP2 = const(0x10)
SR_BP3 = const(0x20)
SR_SRWD = const(0x80)


def _is_available(parameter=None):
    """Decorator to check whether this action is available for IC specified or not."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if parameter is not None:
                if getattr(args[0], parameter) is None:
                    raise RuntimeError("Function %s is unavailable for this IC. Specify %s." % (func.__name__, parameter))
                else:
                    return func(*args, **kwargs)
            else:
                log.warning("Check if %s is implemented on your IC. It is not guaranteed." % func.__name__)
                return func(*args, **kwargs)
        return wrapper
    return decorator


class SerialFlash25:
    """Class to communicate Serial Flash Memory 25xxxx series with."""

    def __init__(self,
                 name: str,
                 size: int,
                 page_size: int,
                 addr_bytes_num: int,
                 spi: int,
                 cs: str,
                 wp: str,
                 block_size=None,
                 sector_size=None,
                 is_chip_erase=False,
                 conn_chk: bool = False) -> None:
        self.name = name
        self.size = size
        self.sector_size = sector_size
        self.block_size = block_size
        self.page_size = page_size
        self.addr_bytes_num = addr_bytes_num
        self.cs = Pin(cs, Pin.OUT_PP)
        self.wp = Pin(wp, Pin.OUT_PP)
        self.spi = SPI(spi, SPI.MASTER, prescaler=128, polarity=0, phase=0)
        self.conn_chk = conn_chk
        self.is_chip_erase = is_chip_erase
        self._pages_count = size // page_size
        self._sectors_count = size // sector_size if sector_size is not None else None
        self._blocks_count = size // block_size if block_size is not None else None

    @_is_available()
    def read_id(self) -> str:
        """Read device JEDEC Id."""
        self.cs.value(False)
        result = bytearray(4)
        self.spi.send_recv(bytearray([CMD_RDID]+[DUMMY_BYTE]*3), result)  # Id always contains 3 bytes
        self.cs.value(True)
        res_id = " ".join(["0x%02X" % x for x in result[1:]])
        if res_id == "0x00 0x00 0x00":
            raise RuntimeError("Either IC is connected incorrectly "
                               "or it doesn't support Read ID (0x%02X) command." % CMD_RDID)
        return res_id

    def dump(self, path: str) -> None:
        """Dump all device contents to binary file."""
        if self.conn_chk:
            self.read_id()
        if self.sector_size is not None:
            read_cnt, read_item_size = self._sectors_count, self.sector_size
        else:
            read_cnt, read_item_size = self._pages_count, self.page_size
        makedirs(dirname(path))
        with open(path, 'wb') as f:
            for i in range(0, read_cnt):
                # dumping is implemented by sectors/pages
                # because it may be impossible to allocate buffer size of full flash
                buf = self.read(i * read_item_size, read_item_size)
                f.write(buf)
                del buf
        log.info("Dump finished. %s image -> %s" % (self.name, path))

    def program(self, path: str):
        """Flash binary to device."""
        if self.conn_chk:
            self.read_id()
        if not isfile(path):
            raise FileNotFoundError("File  not found: '%s'" % path)
        filesize = getsize(path)
        if filesize != self.size:
            raise ValueError("File size (0x%02X bytes) doesn't equal IC size (0x%02X bytes)" % (filesize, self.size))
        self.chip_erase()
        with open(path, 'rb') as f:
            for i in range(0, self._pages_count):
                buf = bytearray(f.read(self.page_size))
                self.page_program(i, buf)
        log.info("Program finished. %s image -> %s" % (path, self.name))

    def chip_erase(self) -> None:
        """Erase chip."""
        if self.is_chip_erase:
            self._wait_wip_reset()
            self._write_enable()
            self.cs.value(False)
            self.spi.send(bytearray([CMD_CE]))
            self.cs.value(True)
            self._write_disable()
            self._wait_wip_reset()
        else:
            for i in range(0, self._pages_count):
                self.page_program(i, bytearray([0xFF]*self.page_size))
        log.info("Chip erase finished.")

    @_is_available("sector_size")
    def sector_program(self, sector_num: int, bytebuffer: bytearray) -> None:
        """Program sector with bytes in bytebuffer."""
        bytebuffer_len = len(bytebuffer)
        if sector_num > self._sectors_count:
            raise ValueError("Sector number (%d) is more than total sectors number (%d)." %
                             (sector_num, self._sectors_count))
        if bytebuffer_len > self.page_size:
            raise ValueError("Bytebuffer length (%d) is more than sector size (%d)." %
                             (len(bytebuffer), self.page_size))
        self.sector_erase(sector_num)
        pages_count = bytebuffer_len // self.page_size
        remain_bytes = bytebuffer_len % self.page_size
        if remain_bytes != 0:
            log.warning("sector_program: Bytebuffer is not sector aligned.")
        start_page = sector_num*self.sector_size//self.page_size
        for i in range(0, pages_count):
            self.page_program(start_page + i, bytebuffer[self.page_size*i:self.page_size*(i+1)+1])
        if remain_bytes != 0:
            self.page_program(start_page + pages_count, bytebuffer[self.page_size * pages_count:])
        log.info('Sector %d program finished.' % sector_num)

    @_is_available("sector_size")
    def sector_erase(self, sector_num: int) -> None:
        """Erase specified sector."""
        if sector_num > self._sectors_count:
            raise ValueError("Sector number (%d) is more than total sectors number (%d)." %
                             (sector_num, self._sectors_count))
        addr = sector_num*self.sector_size
        self._wait_wip_reset()
        self._write_enable()
        self.cs.value(False)
        self.spi.send(bytearray([CMD_SE]) + addr.to_bytes(self.addr_bytes_num, "big"))
        self.cs.value(True)
        self._write_disable()
        self._wait_wip_reset()
        log.info("Sector %d erase finished." % sector_num)

    @_is_available("block_size")
    def block_erase(self, block_num: int) -> None:
        """Erase specified block."""
        if block_num > self._blocks_count:
            raise ValueError("Block number (%d) is more than total block number (%d)." %
                             (block_num, self._blocks_count))
        addr = block_num * self.sector_size
        self._wait_wip_reset()
        self._write_enable()
        self.cs.value(False)
        self.spi.send(bytearray([CMD_BE]) + addr.to_bytes(self.addr_bytes_num, "big"))
        self.cs.value(True)
        self._write_disable()
        self._wait_wip_reset()
        log.info("Block %d erase finished." % block_num)

    def read(self, offset: int, size: int) -> bytearray:
        """Read data from specified offset using specified size."""
        if (offset > self.size) or (offset+size > self.size):
            raise ValueError("Read data from 0x%02X-0x%02X is out of range. Max address is 0x%02X." %
                             (offset, offset+size, self.size))
        self.cs.value(False)
        self.spi.send(bytearray([CMD_READ]) + offset.to_bytes(self.addr_bytes_num, "big"))
        result = bytearray(size)
        self.spi.send_recv(bytearray([DUMMY_BYTE]*size), result)
        self.cs.value(True)
        log.info("Data read 0x%02X-0x%02X finished." % (offset, offset+size))
        return result

    def page_program(self, page_num: int, bytebuffer: bytearray) -> None:
        """Program page with bytes in bytebuffer"""
        if page_num > self._pages_count:
            raise ValueError("Page number (%d) is more than total pages number (%d)." % (page_num, self._pages_count))
        if len(bytebuffer) > self.page_size:
            raise ValueError("Bytebuffer length (%d) is more than page size (%d)." % (len(bytebuffer), self.page_size))
        addr = page_num*self.page_size
        self._wait_wip_reset()
        self._write_enable()
        self.cs.value(False)
        self.spi.send(bytearray([CMD_PP]) + addr.to_bytes(self.addr_bytes_num, "big"))
        self.spi.send(bytebuffer)
        self.cs.value(True)
        self._write_disable()
        self._wait_wip_reset()
        log.info('Page %d program finished.' % page_num)

    def _wait_wip_reset(self) -> None:
        """Wait for WIP=0. WIP is bit0 in Status Register."""
        sr = self.read_sr()
        while sr & SR_WIP:
            sr = self.read_sr()

    def _write_enable(self) -> None:
        """Enable Write operation via command."""
        self.cs.value(False)
        self.spi.send(bytearray([CMD_WREN]))
        self.cs.value(True)

    def _write_disable(self) -> None:
        """Disable Write operation via command."""
        self.cs.value(False)
        self.spi.send(bytearray([CMD_WRDI]))
        self.cs.value(True)

    def read_sr(self):
        """Read status register."""
        result = bytearray(2)
        self.cs.value(False)
        self.spi.send_recv(bytearray([CMD_RDSR, DUMMY_BYTE]), result)
        self.cs.value(True)
        return result[1]

    def write_sr(self, sr_val: int) -> None:
        """Write status register."""
        self._write_enable()
        self.cs.value(False)
        self.spi.send(bytearray([CMD_WRSR, sr_val & 0xFF]))
        self.cs.value(True)
        self._write_disable()
