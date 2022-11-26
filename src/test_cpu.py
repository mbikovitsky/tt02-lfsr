import ctypes
import random
from typing import Mapping, Optional, Sequence

import cocotb
from cocotb.handle import HierarchyObject
from cocotb.triggers import ClockCycles

import util

CLOCK_HZ = 6250

VAL_MIN = -32768
VAL_MAX = 32767


# Computes RAM[0] = 2 + 3
ADD = [
    0b0000000000000010,
    0b1110110000010000,
    0b0000000000000011,
    0b1110000010010000,
    0b0000000000000000,
    0b1110001100001000,
]

# Computes RAM[2] = max(RAM[0], RAM[1])
# Assumes both numbers are non-negative
MAX = [
    0b0000000000000000,
    0b1111110000010000,
    0b0000000000000001,
    0b1111010011010000,
    0b0000000000001010,
    0b1110001100000001,
    0b0000000000000001,
    0b1111110000010000,
    0b0000000000001100,
    0b1110101010000111,
    0b0000000000000000,
    0b1111110000010000,
    0b0000000000000010,
    0b1110001100001000,
    0b0000000000001110,
    0b1110101010000111,
]

# Computes RAM[13]/RAM[14] and stores the result in RAM[15].
# The remainder is discarded.
# It is assumed that both numbers are > 0.
DIVIDE = [
    0b0000000000111000,
    0b1110101010000111,
    0b0000000000010000,
    0b1111110000010000,
    0b0000000000010001,
    0b1110001100001000,
    0b0000000000010001,
    0b1111110000010000,
    0b0000000000010010,
    0b1111010011010000,
    0b0000000000010000,
    0b1110001100000001,
    0b0000000000010001,
    0b1011100000001000,
    0b0000000000000110,
    0b1110101010000111,
    0b0111111111111111,
    0b1110110000010000,
    0b0000000000010001,
    0b1011000000001000,
    0b1111000000001000,
    0b0000000000010011,
    0b1110101010001000,
    0b0000000000010001,
    0b1111110000010000,
    0b0000000000010000,
    0b1111010011010000,
    0b0000000000110001,
    0b1110001100000100,
    0b0000000000010011,
    0b1011100000001000,
    0b0000000000010010,
    0b1111110000010000,
    0b0000000000010001,
    0b1111010011010000,
    0b0000000000101101,
    0b1110001100000100,
    0b0000000000010011,
    0b1111110111001000,
    0b0000000000010010,
    0b1111110000010000,
    0b0000000000010001,
    0b1111010011010000,
    0b0000000000010010,
    0b1110001100001000,
    0b0000000000010001,
    0b1011000000001000,
    0b0000000000010111,
    0b1110101010000111,
    0b0000000000010011,
    0b1111110000010000,
    0b0000000000010100,
    0b1110001100001000,
    0b0000000000010101,
    0b1111110000100000,
    0b1110101010000111,
    0b0000000000001101,
    0b1111110000010000,
    0b0000000000010010,
    0b1110001100001000,
    0b0000000000001110,
    0b1111110000010000,
    0b0000000000010000,
    0b1110001100001000,
    0b0000000001000110,
    0b1110110000010000,
    0b0000000000010101,
    0b1110001100001000,
    0b0000000000000010,
    0b1110101010000111,
    0b0000000000010100,
    0b1111110000010000,
    0b0000000000001111,
    0b1110001100001000,
]

# Sorts the array at address RAM[14], with length specified in RAM[15].
# In descending order.
# Values are assumed to be >= 0
SORT = [
    0b0000000001000101,
    0b1110101010000111,
    0b0000000000010000,
    0b1110111111001000,
    0b0000000000010000,
    0b1111110000010000,
    0b0000000000010001,
    0b1111010011010000,
    0b0000000001000010,
    0b1110001100000011,
    0b0000000000010010,
    0b1111110000010000,
    0b0000000000010000,
    0b1111000010100000,
    0b1111110000010000,
    0b0000000000010011,
    0b1110001100001000,
    0b0000000000010000,
    0b1111110000010000,
    0b0000000000010100,
    0b1110001110001000,
    0b0000000000010100,
    0b1111110000010000,
    0b0000000000110011,
    0b1110001100000100,
    0b0000000000010010,
    0b1111110000010000,
    0b0000000000010100,
    0b1111000010100000,
    0b1111110000010000,
    0b0000000000010101,
    0b1110001100001000,
    0b0000000000010011,
    0b1111010011010000,
    0b0000000000110011,
    0b1110001100000001,
    0b0000000000010010,
    0b1111110111010000,
    0b0000000000010100,
    0b1111000010010000,
    0b0000000000010110,
    0b1110001100001000,
    0b0000000000010101,
    0b1111110000010000,
    0b0000000000010110,
    0b1111110000100000,
    0b1110001100001000,
    0b0000000000010100,
    0b1111110010001000,
    0b0000000000010101,
    0b1110101010000111,
    0b0000000000010010,
    0b1111110111010000,
    0b0000000000010100,
    0b1111000010010000,
    0b0000000000010110,
    0b1110001100001000,
    0b0000000000010011,
    0b1111110000010000,
    0b0000000000010110,
    0b1111110000100000,
    0b1110001100001000,
    0b0000000000010000,
    0b1111110111001000,
    0b0000000000000100,
    0b1110101010000111,
    0b0000000000010111,
    0b1111110000100000,
    0b1110101010000111,
    0b0000000000001110,
    0b1111110000010000,
    0b0000000000010010,
    0b1110001100001000,
    0b0000000000001111,
    0b1111110000010000,
    0b0000000000010001,
    0b1110001100001000,
    0b0000000001010011,
    0b1110110000010000,
    0b0000000000010111,
    0b1110001100001000,
    0b0000000000000010,
    0b1110101010000111,
]

# Multiplies RAM[0] and RAM[1] and stores the result in RAM[2].
MULT = [
    0b0000000000011101,
    0b1110101010000111,
    0b0000000000010000,
    0b1110101010001000,
    0b0000000000010001,
    0b1111110000010000,
    0b0000000000001110,
    0b1110001100000011,
    0b0000000000010010,
    0b1111110001010000,
    0b1110011111001000,
    0b0000000000010001,
    0b1111110001010000,
    0b1110011111001000,
    0b0000000000010001,
    0b1111110000010000,
    0b0000000000011010,
    0b1110001100000010,
    0b0000000000010001,
    0b1110001110001000,
    0b0000000000010010,
    0b1111110000010000,
    0b0000000000010000,
    0b1111000010001000,
    0b0000000000001110,
    0b1110101010000111,
    0b0000000000010011,
    0b1111110000100000,
    0b1110101010000111,
    0b0000000000000010,
    0b1110101010001000,
    0b0000000000000000,
    0b1111110000010000,
    0b0000000000010010,
    0b1110001100001000,
    0b0000000000000001,
    0b1111110000010000,
    0b0000000000010001,
    0b1110001100001000,
    0b0000000000101101,
    0b1110110000010000,
    0b0000000000010011,
    0b1110001100001000,
    0b0000000000000010,
    0b1110101010000111,
    0b0000000000010000,
    0b1111110000010000,
    0b0000000000000010,
    0b1110001100001000,
]


@cocotb.test()
async def test_add(dut: HierarchyObject):
    util.start_clock(dut, CLOCK_HZ)
    memory = await _execute_program(dut, ADD)
    assert memory[0] == 5


@cocotb.test()
async def test_max(dut: HierarchyObject):
    first = random.randint(0, VAL_MAX)
    second = random.randint(0, VAL_MAX)

    util.start_clock(dut, CLOCK_HZ)

    memory = await _execute_program(dut, MAX, memory={0: first, 1: second})

    assert memory[2] == max(first, second)


@cocotb.test()
async def test_div(dut: HierarchyObject):
    first = random.randint(1, VAL_MAX)
    second = random.randint(1, VAL_MAX)

    util.start_clock(dut, CLOCK_HZ)

    memory = await _execute_program(dut, DIVIDE, memory={13: first, 14: second})

    assert memory[15] == first // second


@cocotb.test(skip=True)
async def test_mul(dut: HierarchyObject):
    first = random.randint(0, VAL_MAX)
    second = random.randint(0, VAL_MAX)

    util.start_clock(dut, CLOCK_HZ)

    memory = await _execute_program(
        dut, MULT, memory={0: first, 1: second}, cycles=1000000
    )

    assert memory[2] == ctypes.c_int16(first * second).value


@cocotb.test(skip=True)
async def test_sort(dut: HierarchyObject):
    to_sort = [random.randint(0, VAL_MAX) for _ in range(100)]

    memory = {100 + i: value for i, value in enumerate(to_sort)}
    memory[14] = 100
    memory[15] = len(to_sort)

    util.start_clock(dut, CLOCK_HZ)

    out_memory = await _execute_program(dut, SORT, memory=memory, cycles=100000)

    output_array = out_memory[100 : 100 + len(to_sort)]

    assert output_array == sorted(to_sort, reverse=True)


@cocotb.test()
async def test_builtin_mul(dut: HierarchyObject):
    program = [
        0b0000000000111001,  # @57
        0b1110110011010000,  # D=-A
        0b0000000000000101,  # @5
        0b1010110000010000,  # D = D<<
        0b1100000000110000,  # DA = D*A
        0b0000000000000000,  # @0
        0b1110001100001000,  # M=D
    ]

    util.start_clock(dut, CLOCK_HZ)

    memory = await _execute_program(dut, program, cycles=len(program) + 1)

    assert memory[0] == -570


async def _execute_program(
    dut: HierarchyObject,
    program: Sequence[int],
    cycles: int = 1000,
    memory: Optional[Mapping[int, int]] = None,
):
    if not memory:
        memory = {}

    # Wait until next clock
    await ClockCycles(dut.clk, 1)

    # Hold CPU and memory resets for one clock
    dut.cpu_reset.value = 1
    dut.mem_reset.value = 1
    await ClockCycles(dut.clk, 1)

    # Release memory reset and initialize
    dut.mem_reset.value = 0
    for i, instruction in enumerate(program):
        dut.rom.memory[i].value = instruction
    for addr, value in memory.items():
        dut.ram.memory[addr].value = value
    await ClockCycles(dut.clk, 1)

    # Release CPU reset
    dut.cpu_reset.value = 0

    # Execute program for the given number of cycles
    await ClockCycles(dut.clk, cycles)

    return [ctypes.c_int16(obj.value.integer).value for obj in dut.ram.memory]
