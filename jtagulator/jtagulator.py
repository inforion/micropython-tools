import pyb

import logging

log = logging.get_logger(__name__)
TMS = TDI = TCK = TDO = None


def _product(items, repeat):
    n = len(items)
    total = n ** repeat
    for k in range(total):
        i_0 = k % n
        v = [None] * repeat
        v[repeat - 1] = items[i_0]
        for s in range(1, repeat):
            ns = n ** s
            i_s = (k // ns) % n
            v[repeat - s - 1] = items[i_s]
        yield tuple(v)


JTAG_PINS_BYPASS_COUNT = 4
JTAG_PINS_IDCODE_COUNT = 3
JTAG_BYPASS_PATTERN = "01101110011110001111110110111001111000111111"
MAX_IR_LEN = 32


def _io_values(pins, states):
    total = len(pins)
    TCK.value(False)
    pyb.delay(0)

    for k in range(total):
        pins[k].value(states[k])

    pyb.delay(0)
    TCK.value(True)
    pyb.delay(0)
    TCK.value(False)
    pyb.delay(0)
    return TDO.value()


def _io_tms_tdi(tms_values, tdi_values):
    result = [_io_values([TMS, TDI], [int(tms), int(tdi)]) for tms, tdi in zip(tms_values, tdi_values)]
    return "".join(map(str, result))


def _io_tms(values):
    result = [_io_values([TMS], [int(value)]) for value in values]
    return "".join(map(str, result))


def _restore_idle():
    _io_tms('111110')


def _enter_shift_ir():
    _io_tms('1100')


def _enter_shift_dr():
    _io_tms('100')


def _shift_array(data):
    num = len(data)
    if TDI is None:
        return _io_tms(data)
    else:
        return _io_tms_tdi('0' * (num-1) + '1', data)


def _send_data(data):
    _enter_shift_dr()
    result = _shift_array(data)
    _io_tms('10')  # Update-DR -> Run-Test Idle
    return result


def _bypass_test(pattern):
    _restore_idle()
    _enter_shift_ir()

    _io_tms_tdi('0' * MAX_IR_LEN, '1' * MAX_IR_LEN)

    _io_tms('110')  # Exit1-IR -> Update-IR -> Run-Test Idle

    return ''.join(_send_data(pattern))


def _idcode_test():
    _restore_idle()
    _enter_shift_dr()
    result = _shift_array('0' * 32)
    _io_tms('010')
    return ''.join(reversed(result))


class Jtagulator:

    def __init__(self,
                 name: str,
                 pins_scope: list,
                 ) -> None:
        self.name = name
        self.pins_scope = pins_scope

    def bypass_search(self):
        global TMS, TDI, TCK, TDO
        combs = _product(self.pins_scope, repeat=JTAG_PINS_BYPASS_COUNT)
        filtered = list(filter(lambda item: len(set(item)) == JTAG_PINS_BYPASS_COUNT, combs))
        for comb in filtered:
            TMS = pyb.Pin(comb[0], pyb.Pin.OUT_PP)
            TDI = pyb.Pin(comb[1], pyb.Pin.OUT_PP)
            TCK = pyb.Pin(comb[2], pyb.Pin.OUT_PP)
            TDO = pyb.Pin(comb[3], pyb.Pin.IN)
            response = _bypass_test(JTAG_BYPASS_PATTERN)

            if response == JTAG_BYPASS_PATTERN:
                log.info('Possible combination is: TMS = %s, TDI = %s, TCK = %s, TDO = %s' % (comb[0], comb[1], comb[2], comb[3]))

    def idcode_search(self):
        global TMS, TDI, TCK, TDO
        combs = _product(self.pins_scope, repeat=JTAG_PINS_IDCODE_COUNT)
        filtered = list(filter(lambda item: len(set(item)) == JTAG_PINS_IDCODE_COUNT, combs))
        for comb in filtered:
            TMS = pyb.Pin(comb[0], pyb.Pin.OUT_PP)
            TCK = pyb.Pin(comb[1], pyb.Pin.OUT_PP)
            TDO = pyb.Pin(comb[2], pyb.Pin.IN)
            response = _idcode_test()
            if (response != '11111111111111111111111111111111') and (response != '00000000000000000000000000000000'):
                log.info('Possible combination is: TMS =  %s, TCK = %s, TDO = %s -> IDCODE response = %s' % (comb[0], comb[1], comb[2], response))
