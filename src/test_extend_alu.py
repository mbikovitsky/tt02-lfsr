import ctypes
import random
from typing import Optional, Union

import cocotb
from cocotb.handle import HierarchyObject
from cocotb.triggers import Timer

VAL_MIN = -32768
VAL_MAX = 32767


class ALUInstruction(ctypes.Union):
    class _Bits(ctypes.LittleEndianStructure):
        _fields_ = (
            ("no", ctypes.c_uint16, 1),
            ("f", ctypes.c_uint16, 1),
            ("ny", ctypes.c_uint16, 1),
            ("zy", ctypes.c_uint16, 1),
            ("nx", ctypes.c_uint16, 1),
            ("zx", ctypes.c_uint16, 1),
            ("reserved0_0", ctypes.c_uint16, 1),
            ("reserved1_1", ctypes.c_uint16, 2),
        )

    _anonymous_ = ("u",)
    _fields_ = (("u", _Bits), ("full", ctypes.c_uint16))

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.reserved0_0 = 0b0
        self.reserved1_1 = 0b11


class ExtendALUInstruction(ctypes.Union):
    class _Bits(ctypes.LittleEndianStructure):
        _fields_ = (
            ("reserved0_0", ctypes.c_uint16, 4),
            ("shift_x", ctypes.c_uint16, 1),
            ("shift_left", ctypes.c_uint16, 1),
            ("reserved1_0", ctypes.c_uint16, 1),
            ("shift", ctypes.c_uint16, 1),
            ("reserved2_0", ctypes.c_uint16, 1),
        )

    _anonymous_ = ("u",)
    _fields_ = (("u", _Bits), ("full", ctypes.c_uint16))

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        self.reserved0_0 = 0b0000
        self.reserved1_0 = 0b0
        self.reserved2_0 = 0b0


@cocotb.test()
async def test_zero(dut: HierarchyObject):
    await _test_computation(dut, ALUInstruction(zx=1, nx=0, zy=1, ny=0, f=1, no=0), 0)


@cocotb.test()
async def test_one(dut: HierarchyObject):
    await _test_computation(dut, ALUInstruction(zx=1, nx=1, zy=1, ny=1, f=1, no=1), 1)


@cocotb.test()
async def test_neg_one(dut: HierarchyObject):
    await _test_computation(dut, ALUInstruction(zx=1, nx=1, zy=1, ny=0, f=1, no=0), -1)


@cocotb.test()
async def test_x_identity(dut: HierarchyObject):
    value = _random_value()
    await _test_computation(
        dut, ALUInstruction(zx=0, nx=0, zy=1, ny=1, f=0, no=0), value, x=value
    )


@cocotb.test()
async def test_y_identity(dut: HierarchyObject):
    value = _random_value()
    await _test_computation(
        dut, ALUInstruction(zx=1, nx=1, zy=0, ny=0, f=0, no=0), value, y=value
    )


@cocotb.test()
async def test_not_x(dut: HierarchyObject):
    value = _random_value()

    await _test_computation(
        dut, ALUInstruction(zx=0, nx=0, zy=1, ny=1, f=0, no=1), ~value, x=value
    )

    await _test_computation(
        dut, ALUInstruction(zx=0, nx=0, zy=1, ny=1, f=0, no=1), ~VAL_MIN, x=VAL_MIN
    )

    await _test_computation(
        dut, ALUInstruction(zx=0, nx=0, zy=1, ny=1, f=0, no=1), ~VAL_MAX, x=VAL_MAX
    )


@cocotb.test()
async def test_not_y(dut: HierarchyObject):
    value = _random_value()

    await _test_computation(
        dut, ALUInstruction(zx=1, nx=1, zy=0, ny=0, f=0, no=1), ~value, y=value
    )

    await _test_computation(
        dut, ALUInstruction(zx=1, nx=1, zy=0, ny=0, f=0, no=1), ~VAL_MIN, y=VAL_MIN
    )

    await _test_computation(
        dut, ALUInstruction(zx=1, nx=1, zy=0, ny=0, f=0, no=1), ~VAL_MAX, y=VAL_MAX
    )


@cocotb.test()
async def test_neg_x(dut: HierarchyObject):
    value = _random_value()

    await _test_computation(
        dut,
        ALUInstruction(zx=0, nx=0, zy=1, ny=1, f=1, no=1),
        ctypes.c_int16(-value).value,
        x=value,
    )

    await _test_computation(
        dut,
        ALUInstruction(zx=0, nx=0, zy=1, ny=1, f=1, no=1),
        ctypes.c_int16(-VAL_MIN).value,
        x=VAL_MIN,
    )

    await _test_computation(
        dut,
        ALUInstruction(zx=0, nx=0, zy=1, ny=1, f=1, no=1),
        ctypes.c_int16(-VAL_MAX).value,
        x=VAL_MAX,
    )


@cocotb.test()
async def test_neg_y(dut: HierarchyObject):
    value = _random_value()

    await _test_computation(
        dut,
        ALUInstruction(zx=1, nx=1, zy=0, ny=0, f=1, no=1),
        ctypes.c_int16(-value).value,
        y=value,
    )

    await _test_computation(
        dut,
        ALUInstruction(zx=1, nx=1, zy=0, ny=0, f=1, no=1),
        ctypes.c_int16(-VAL_MIN).value,
        y=VAL_MIN,
    )

    await _test_computation(
        dut,
        ALUInstruction(zx=1, nx=1, zy=0, ny=0, f=1, no=1),
        ctypes.c_int16(-VAL_MAX).value,
        y=VAL_MAX,
    )


@cocotb.test()
async def test_inc_x(dut: HierarchyObject):
    value = _random_value()

    await _test_computation(
        dut,
        ALUInstruction(zx=0, nx=1, zy=1, ny=1, f=1, no=1),
        ctypes.c_int16(value + 1).value,
        x=value,
    )

    await _test_computation(
        dut,
        ALUInstruction(zx=0, nx=1, zy=1, ny=1, f=1, no=1),
        ctypes.c_int16(VAL_MIN + 1).value,
        x=VAL_MIN,
    )

    await _test_computation(
        dut,
        ALUInstruction(zx=0, nx=1, zy=1, ny=1, f=1, no=1),
        ctypes.c_int16(VAL_MAX + 1).value,
        x=VAL_MAX,
    )


@cocotb.test()
async def test_inc_y(dut: HierarchyObject):
    value = _random_value()

    await _test_computation(
        dut,
        ALUInstruction(zx=1, nx=1, zy=0, ny=1, f=1, no=1),
        ctypes.c_int16(value + 1).value,
        y=value,
    )

    await _test_computation(
        dut,
        ALUInstruction(zx=1, nx=1, zy=0, ny=1, f=1, no=1),
        ctypes.c_int16(VAL_MIN + 1).value,
        y=VAL_MIN,
    )

    await _test_computation(
        dut,
        ALUInstruction(zx=1, nx=1, zy=0, ny=1, f=1, no=1),
        ctypes.c_int16(VAL_MAX + 1).value,
        y=VAL_MAX,
    )


@cocotb.test()
async def test_dec_x(dut: HierarchyObject):
    value = _random_value()

    await _test_computation(
        dut,
        ALUInstruction(zx=0, nx=0, zy=1, ny=1, f=1, no=0),
        ctypes.c_int16(value - 1).value,
        x=value,
    )

    await _test_computation(
        dut,
        ALUInstruction(zx=0, nx=0, zy=1, ny=1, f=1, no=0),
        ctypes.c_int16(VAL_MIN - 1).value,
        x=VAL_MIN,
    )

    await _test_computation(
        dut,
        ALUInstruction(zx=0, nx=0, zy=1, ny=1, f=1, no=0),
        ctypes.c_int16(VAL_MAX - 1).value,
        x=VAL_MAX,
    )


@cocotb.test()
async def test_dec_y(dut: HierarchyObject):
    value = _random_value()

    await _test_computation(
        dut,
        ALUInstruction(zx=1, nx=1, zy=0, ny=0, f=1, no=0),
        ctypes.c_int16(value - 1).value,
        y=value,
    )

    await _test_computation(
        dut,
        ALUInstruction(zx=1, nx=1, zy=0, ny=0, f=1, no=0),
        ctypes.c_int16(VAL_MIN - 1).value,
        y=VAL_MIN,
    )

    await _test_computation(
        dut,
        ALUInstruction(zx=1, nx=1, zy=0, ny=0, f=1, no=0),
        ctypes.c_int16(VAL_MAX - 1).value,
        y=VAL_MAX,
    )


@cocotb.test()
async def test_xpy(dut: HierarchyObject):
    x = _random_value()
    y = _random_value()

    await _test_computation(
        dut,
        ALUInstruction(zx=0, nx=0, zy=0, ny=0, f=1, no=0),
        ctypes.c_int16(x + y).value,
        x=x,
        y=y,
    )


@cocotb.test()
async def test_xmy(dut: HierarchyObject):
    x = _random_value()
    y = _random_value()

    await _test_computation(
        dut,
        ALUInstruction(zx=0, nx=1, zy=0, ny=0, f=1, no=1),
        ctypes.c_int16(x - y).value,
        x=x,
        y=y,
    )


@cocotb.test()
async def test_ymx(dut: HierarchyObject):
    x = _random_value()
    y = _random_value()

    await _test_computation(
        dut,
        ALUInstruction(zx=0, nx=0, zy=0, ny=1, f=1, no=1),
        ctypes.c_int16(y - x).value,
        x=x,
        y=y,
    )


@cocotb.test()
async def test_xay(dut: HierarchyObject):
    x = _random_value()
    y = _random_value()

    await _test_computation(
        dut,
        ALUInstruction(zx=0, nx=0, zy=0, ny=0, f=0, no=0),
        ctypes.c_int16(x & y).value,
        x=x,
        y=y,
    )


@cocotb.test()
async def test_xoy(dut: HierarchyObject):
    x = _random_value()
    y = _random_value()

    await _test_computation(
        dut,
        ALUInstruction(zx=0, nx=1, zy=0, ny=1, f=0, no=1),
        ctypes.c_int16(x | y).value,
        x=x,
        y=y,
    )


@cocotb.test()
async def test_shl_x(dut: HierarchyObject):
    x = _random_value()

    await _test_computation(
        dut,
        ExtendALUInstruction(shift_x=1, shift_left=1, shift=1),
        expected=ctypes.c_int16(x << 1).value,
        x=x,
    )


@cocotb.test()
async def test_shl_y(dut: HierarchyObject):
    y = _random_value()

    await _test_computation(
        dut,
        ExtendALUInstruction(shift_x=0, shift_left=1, shift=1),
        expected=ctypes.c_int16(y << 1).value,
        y=y,
    )


@cocotb.test()
async def test_shr_x(dut: HierarchyObject):
    x = _random_value()

    await _test_computation(
        dut,
        ExtendALUInstruction(shift_x=1, shift_left=0, shift=1),
        expected=ctypes.c_int16(x >> 1).value,
        x=x,
    )


@cocotb.test()
async def test_shr_y(dut: HierarchyObject):
    y = _random_value()

    await _test_computation(
        dut,
        ExtendALUInstruction(shift_x=0, shift_left=0, shift=1),
        expected=ctypes.c_int16(y >> 1).value,
        y=y,
    )


@cocotb.test(skip=True)
async def test_mul(dut: HierarchyObject):
    x = _random_value()
    y = _random_value()

    await _test_computation(
        dut,
        ExtendALUInstruction(shift_x=0, shift_left=0, shift=0),
        expected=ctypes.c_int16(x * y).value,
        x=x,
        y=y,
    )


async def _test_computation(
    dut: HierarchyObject,
    instruction: Union[ALUInstruction, ExtendALUInstruction],
    expected: int,
    x: Optional[int] = None,
    y: Optional[int] = None,
):
    assert VAL_MIN <= expected <= VAL_MAX

    if x is not None:
        assert VAL_MIN <= x <= VAL_MAX
        dut.x.value = x

    if y is not None:
        assert VAL_MIN <= y <= VAL_MAX
        dut.y.value = y

    dut.instruction.value = instruction.full

    await Timer(1, units="step")

    assert dut.out.value.signed_integer == expected
    assert dut.zr.value.integer == int(expected == 0)
    assert dut.ng.value.integer == int(expected < 0)


def _random_value() -> int:
    return random.randint(VAL_MIN, VAL_MAX)
