# micropython-tools
Useful tools for baremetal MicroPython (Pyboard and etc.). 
* Some packages in this project are ported to baremetal MicroPython platforms from common Python implementations.
* Some of them were written from scratch using MicroPython specific peripherals.
## Installation
To use this packages clone this repository to the `lib` folder on sd of PyBoard. 
Default `sys.path` of MicroPython points exactly to this folder.
So you may import it as usual using for example:
```python
import logging
```
## How to use
* Some packages are described with its own Readme file. 
* Also comments written in source code will help you to understand the meaning of each class, option or function.
## Example usage
Copy the next code block to your `main.py` file to implement interactive communication with your Serail flash connected
```python
from serialflash import SerialFlash25

if __name__ == "__main__":
    spi_flash = SerialFlash25(name="serial_flash_example",
                              size=2*1024*1024,
                              sector_size=4*1024,
                              block_size=64*1024,
                              page_size=256,
                              addr_bytes_num=3,
                              spi=2,
                              cs="Y5",
                              wp="X11")
```