import random

import cocotb
from cocotb.handle import HierarchyObject
from cocotb.triggers import ClockCycles, Timer

import util

CLOCK_HZ = 6250
WORDS = int(cocotb.plusargs.get("WORDS", 1024))
WORD_WIDTH = int(cocotb.plusargs.get("WORD_WIDTH", 8))


@cocotb.test()
async def test_ram_reset(dut: HierarchyObject):
    util.start_clock(dut, CLOCK_HZ)
    await _reset(dut, 1)

    for i in range(WORDS):
        # NOTE: We should technically be testing that the read operation is indeed
        # combinatorial, but I didn't find a good way to do it.
        dut.address_i.value = i
        await Timer(1, units="step")
        assert dut.data_o.value.integer == 0


@cocotb.test()
async def test_ram_read_write(dut: HierarchyObject):
    util.start_clock(dut, CLOCK_HZ)
    await _reset(dut, 1)

    for i in range(WORDS):
        value = random.randint(0, (1 << WORD_WIDTH) - 1)

        dut.wr_en_i.value = 1
        dut.address_i.value = i
        dut.data_i.value = value

        await ClockCycles(dut.clk, 1)

        dut.wr_en_i.value = 0

        await ClockCycles(dut.clk, 1)

        assert dut.data_o.value.integer == value


async def _reset(dut: HierarchyObject, cycles: int):
    dut.wr_en_i.value = 0

    dut.reset.value = 1
    await ClockCycles(dut.clk, cycles)
    dut.reset.value = 0
    await ClockCycles(dut.clk, 1)
