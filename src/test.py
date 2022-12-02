import ctypes
import os.path
import random
from enum import IntEnum, IntFlag
from typing import Iterable, List, Union

import cocotb
from cocotb.handle import HierarchyObject, ModifiableObject
from cocotb.triggers import ClockCycles, Edge, Timer, with_timeout
from galois import GF2, GLFSR

import util

GATE_LEVEL: bool = "GATE_LEVEL" in cocotb.plusargs


LFSR_BITS = 5


# https://en.wikipedia.org/wiki/Seven-segment_display#Hexadecimal
SEVEN_SEGMENT_DECODER = {
    0b0111111: 0,
    0b0000110: 1,
    0b1011011: 2,
    0b1001111: 3,
    0b1100110: 4,
    0b1101101: 5,
    0b1111101: 6,
    0b0000111: 7,
    0b1111111: 8,
    0b1101111: 9,
    0b1110111: 10,
    0b1111100: 11,
    0b0111001: 12,
    0b1011110: 13,
    0b1111001: 14,
    0b1110001: 15,
}


class Bus:
    def __init__(self, wires: Iterable[ModifiableObject]):
        self._wires = list(wires)
        self._total_bits = sum(wire.value.n_bits for wire in self._wires)

    @property
    def value(self) -> int:
        for wire in self._wires:
            if not wire.value.is_resolvable:
                raise ValueError(f"Wire {wire._path} is not resolvable ({wire.value})")

        return int("".join(wire.value.binstr for wire in reversed(self._wires)), 2)

    @value.setter
    def value(self, value: int):
        if value < 0:
            raise NotImplementedError("Negative values are not supported")
        if value >= (1 << self._total_bits):
            raise ValueError(f"{value} is out of range for this bus")

        bit_offset = 0
        for wire in self._wires:
            wire.value = (value >> bit_offset) & ((1 << wire.value.n_bits) - 1)
            bit_offset += wire.value.n_bits


class AInstruction(ctypes.Union):
    class _Bits(ctypes.LittleEndianStructure):
        _fields_ = (
            ("address", ctypes.c_uint16, 15),
            ("reserved0_0", ctypes.c_uint16, 1),
        )

    _anonymous_ = ("u",)
    _fields_ = (("u", _Bits), ("full", ctypes.c_uint16))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reserved0_0 = 0b0

    def __int__(self) -> int:
        return self.full


class CInstruction(ctypes.Union):
    class _Bits(ctypes.LittleEndianStructure):
        _fields_ = (
            ("jump", ctypes.c_uint16, 3),
            ("dest", ctypes.c_uint16, 3),
            ("comp", ctypes.c_uint16, 6),
            ("a", ctypes.c_uint16, 1),
            ("extended", ctypes.c_uint16, 2),
            ("reserved0_1", ctypes.c_uint16, 1),
        )

    _anonymous_ = ("u",)
    _fields_ = (("u", _Bits), ("full", ctypes.c_uint16))

    def __init__(self, *args, extended=0b11, **kwargs):
        super().__init__(*args, **kwargs)
        self.extended = extended
        self.reserved0_1 = 0b1

    def __int__(self) -> int:
        return self.full


class JumpSpec(IntEnum):
    NONE = 0b000
    JGT = 0b001
    JEQ = 0b010
    JGE = 0b011
    JLT = 0b100
    JNE = 0b101
    JLE = 0b110
    JMP = 0b111


class DestSpec(IntFlag):
    NONE = 0b000
    A = 0b100
    D = 0b010
    M = 0b001


@cocotb.test()
async def test_maximal_length(dut: HierarchyObject):
    # https://users.ece.cmu.edu/~koopman/lfsr/5.txt
    taps = random.choice([0x12, 0x14, 0x17, 0x1B, 0x1D, 0x1E])

    encountered = await _test_lfsr(dut, _random_initial_state(), taps)
    assert len(encountered) == 2**LFSR_BITS - 1


@cocotb.test()
async def test_random_taps(dut: HierarchyObject):
    await _test_lfsr(dut, _random_initial_state(), _random_taps())


@cocotb.test()
async def test_zero_initial_state(dut: HierarchyObject):
    encountered = await _test_lfsr(dut, 0, _random_taps())
    assert encountered == {0}


@cocotb.test()
async def test_upload_program(dut: HierarchyObject):
    _start_clock(dut)

    await _enter_cpu_mode(dut)

    program = [random.randint(0x0000, 0xFFFF) for _ in range(_prom_size(dut))]

    await _upload_program(dut, program)


@cocotb.test()
async def test_io_out(dut: HierarchyObject):
    _start_clock(dut)

    await _enter_cpu_mode(dut)

    value = random.randint(0x0000, 0x7FFF)

    program = [
        # Write our value to io_out
        AInstruction(address=value),  # @value
        CInstruction(dest=DestSpec.M, a=0, comp=0b110000),  # M=A
        # Increment it in-place
        CInstruction(dest=DestSpec.M, a=1, comp=0b110111),  # M=M+1
    ]

    await _upload_program(dut, program)

    await _run_cpu(dut, len(program) + 1)

    # Only the lower 8 bits are actually output
    assert dut.data_out.value.integer == ((value + 1) & 0xFF)


@cocotb.test()
async def test_add(dut: HierarchyObject):
    _start_clock(dut)

    await _enter_cpu_mode(dut)

    x = random.randint(0x0000, 0x7FFF)
    y = random.randint(0x0000, 0x7FFF)

    program = [
        AInstruction(address=x),  # @x
        CInstruction(dest=DestSpec.D, a=0, comp=0b110000),  # D=A
        AInstruction(address=y),  # @y
        CInstruction(dest=DestSpec.M, a=0, comp=0b000010),  # M=D+A
    ]

    await _upload_program(dut, program)

    await _run_cpu(dut, len(program) * 3)

    # Only the lower 8 bits are actually output
    assert dut.data_out.value.integer == ((x + y) & 0xFF)


@cocotb.test()
async def test_sub(dut: HierarchyObject):
    _start_clock(dut)

    await _enter_cpu_mode(dut)

    x = random.randint(0x0000, 0x7FFF)
    y = random.randint(0x0000, 0x7FFF)

    program = [
        AInstruction(address=x),  # @x
        CInstruction(dest=DestSpec.D, a=0, comp=0b110000),  # D=A
        AInstruction(address=y),  # @y
        CInstruction(dest=DestSpec.M, a=0, comp=0b010011),  # M=D-A
    ]

    await _upload_program(dut, program)

    await _run_cpu(dut, len(program) * 3)

    # Only the lower 8 bits are actually output
    assert dut.data_out.value.integer == ((x - y) & 0xFF)


@cocotb.test()
async def test_and(dut: HierarchyObject):
    _start_clock(dut)

    await _enter_cpu_mode(dut)

    x = random.randint(0x0000, 0x7FFF)
    y = random.randint(0x0000, 0x7FFF)

    program = [
        AInstruction(address=x),  # @x
        CInstruction(dest=DestSpec.D, a=0, comp=0b110000),  # D=A
        AInstruction(address=y),  # @y
        CInstruction(dest=DestSpec.M, a=0, comp=0b000000),  # M=D&A
    ]

    await _upload_program(dut, program)

    await _run_cpu(dut, len(program) * 3)

    # Only the lower 8 bits are actually output
    assert dut.data_out.value.integer == ((x & y) & 0xFF)


@cocotb.test()
async def test_or(dut: HierarchyObject):
    _start_clock(dut)

    await _enter_cpu_mode(dut)

    x = random.randint(0x0000, 0x7FFF)
    y = random.randint(0x0000, 0x7FFF)

    program = [
        AInstruction(address=x),  # @x
        CInstruction(dest=DestSpec.D, a=0, comp=0b110000),  # D=A
        AInstruction(address=y),  # @y
        CInstruction(dest=DestSpec.M, a=0, comp=0b010101),  # M=D|A
    ]

    await _upload_program(dut, program)

    await _run_cpu(dut, len(program) * 3)

    # Only the lower 8 bits are actually output
    assert dut.data_out.value.integer == ((x | y) & 0xFF)


@cocotb.test()
async def test_xor(dut: HierarchyObject):
    _start_clock(dut)

    await _enter_cpu_mode(dut)

    x = random.randint(0x0000, 0x7FFF)
    y = random.randint(0x0000, 0x7FFF)

    program = [
        AInstruction(address=x),  # @x
        CInstruction(dest=DestSpec.D, a=0, comp=0b110000),  # D=A
        AInstruction(address=y),  # @y
        CInstruction(dest=DestSpec.M, extended=0b00, a=0, comp=0b000000),  # M=D^A
    ]

    await _upload_program(dut, program)

    await _run_cpu(dut, len(program) * 3)

    # Only the lower 8 bits are actually output
    assert dut.data_out.value.integer == ((x ^ y) & 0xFF)


@cocotb.test()
async def test_not(dut: HierarchyObject):
    _start_clock(dut)

    await _enter_cpu_mode(dut)

    x = random.randint(0x0000, 0x7FFF)

    program = [
        AInstruction(address=x),  # @x
        CInstruction(dest=DestSpec.M, a=0, comp=0b110001),  # M=!A
    ]

    await _upload_program(dut, program)

    await _run_cpu(dut, len(program) * 3)

    # Only the lower 8 bits are actually output
    assert dut.data_out.value.integer == ((~x) & 0xFF)


@cocotb.test()
async def test_neg(dut: HierarchyObject):
    _start_clock(dut)

    await _enter_cpu_mode(dut)

    x = random.randint(0x0000, 0x7FFF)

    program = [
        AInstruction(address=x),  # @x
        CInstruction(dest=DestSpec.M, a=0, comp=0b110011),  # M=-A
    ]

    await _upload_program(dut, program)

    await _run_cpu(dut, len(program) * 3)

    # Only the lower 8 bits are actually output
    assert dut.data_out.value.integer == ((-x) & 0xFF)


@cocotb.test()
async def test_zero(dut: HierarchyObject):
    _start_clock(dut)

    await _enter_cpu_mode(dut)

    program = [
        CInstruction(dest=DestSpec.M, a=0, comp=0b101010),  # M=0
    ]

    await _upload_program(dut, program)

    await _run_cpu(dut, len(program) * 3)

    # Only the lower 8 bits are actually output
    assert dut.data_out.value.integer == 0


@cocotb.test()
async def test_one(dut: HierarchyObject):
    _start_clock(dut)

    await _enter_cpu_mode(dut)

    program = [
        CInstruction(dest=DestSpec.M, a=0, comp=0b111111),  # M=1
    ]

    await _upload_program(dut, program)

    await _run_cpu(dut, len(program) * 3)

    # Only the lower 8 bits are actually output
    assert dut.data_out.value.integer == 1


@cocotb.test()
async def test_minus_one(dut: HierarchyObject):
    _start_clock(dut)

    await _enter_cpu_mode(dut)

    program = [
        CInstruction(dest=DestSpec.M, a=0, comp=0b111010),  # M=-1
    ]

    await _upload_program(dut, program)

    await _run_cpu(dut, len(program) * 3)

    # Only the lower 8 bits are actually output
    assert dut.data_out.value.integer == 0xFF


@cocotb.test()
async def test_multi_stage(dut: HierarchyObject):
    cpu_reset = dut.data_in_2
    mem_reset = dut.data_in_3

    _start_clock(dut)

    await _enter_cpu_mode(dut)

    x = random.randint(0x0000, 0x7FFF)

    first_stage = [
        AInstruction(address=x),  # @x
        CInstruction(dest=DestSpec.M, a=0, comp=0b110011),  # M=-A
    ]

    await _upload_program(dut, first_stage)

    # Run first stage
    cpu_reset.value = 0
    mem_reset.value = 0
    await ClockCycles(dut.clk, len(first_stage) * 3)

    assert dut.data_out.value.integer == (-x) & 0xFF

    second_stage = [
        CInstruction(dest=DestSpec.M, extended=0b01, a=1, comp=0b000000),  # M=M>>
        CInstruction(dest=DestSpec.M, extended=0b01, a=1, comp=0b000000),  # M=M>>
        AInstruction(address=3),
        CInstruction(jump=JumpSpec.JMP),
    ]

    for i in range(1, 3):
        cpu_reset.value = 1

        await _upload_program(dut, second_stage)

        # Run second stage
        cpu_reset.value = 0
        await ClockCycles(dut.clk, len(second_stage) * 3)

        assert dut.data_out.value.integer == ((-x) >> (i * 2)) & 0xFF


@cocotb.test(skip=True)
async def test_lfsr_program(dut: HierarchyObject):
    cpu_reset = dut.data_in_2
    mem_reset = dut.data_in_3

    _start_clock(dut)

    await _enter_cpu_mode(dut)

    init_program = [
        AInstruction(address=1),  # Initial state
        CInstruction(dest=DestSpec.D, a=0, comp=0b110000),  # D=A
        AInstruction(address=0x4001),  # io_out
        CInstruction(dest=DestSpec.M, a=0, comp=0b001100),  # M=D
    ]

    await _upload_program(dut, init_program)

    # Run the initialization
    cpu_reset.value = 0
    mem_reset.value = 0
    await ClockCycles(dut.clk, len(init_program) + 1)

    assert dut.data_out.value.integer == 1

    with open(
        os.path.join(os.path.dirname(__file__), "lfsr.hack"), mode="r", encoding="ASCII"
    ) as f:
        program = [int(line, 2) for line in f]

    cpu_reset.value = 1

    await _upload_program(dut, program)

    cpu_reset.value = 0

    async def collect_outputs():
        outputs = {}

        need_xor = False

        while True:
            value = dut.data_out.value.integer

            # Found a cycle
            if value in outputs:
                return list(outputs.keys())

            outputs[value] = None

            need_xor = bool(value & 1)

            # Wait for next value
            await Edge(dut.data_out)

            # If the next value requires XORing with the taps,
            # wait for that to happen
            if need_xor:
                await Edge(dut.data_out)

    # Wait for all outputs.
    outputs = await with_timeout(collect_outputs(), 300, "sec")

    lfsr_reference = GLFSR.Taps(
        taps=GF2(_bits_list(0x8E, 8)),
        state=_bits_list(1, 8),
    )

    expected_outputs = []
    for _ in range(len(outputs)):
        expected_outputs.append(
            int("".join(str(int(x)) for x in lfsr_reference.state), 2)
        )
        lfsr_reference.step()

    assert outputs == expected_outputs


async def _enter_cpu_mode(dut: HierarchyObject):
    """
    Puts the DUT into "CPU mode".

    CPU and memory are in reset when this function returns.
    """

    reset_lfsr = dut.data_in_0
    reset_taps = dut.data_in_1
    reset_lfsr.value = reset_taps.value = 1

    cpu_reset = dut.data_in_2
    cpu_reset.value = 1

    mem_reset = dut.data_in_3
    mem_reset.value = 1

    uart_reset = dut.data_in_5
    uart_reset.value = 1

    uart_rx = dut.data_in_4
    uart_rx.value = 1   # Make sure the UART doesn't do anything

    await ClockCycles(dut.clk, 2)


async def _upload_program(
    dut: HierarchyObject, program: Iterable[Union[int, AInstruction, CInstruction]]
):
    """
    Uploads a program to the CPU PROM via UART.

    The CPU should be in reset before running this function.
    """

    program = [int(instruction) for instruction in program]
    assert len(program) <= _prom_size(dut)

    program_bytes = b"".join(
        instruction.to_bytes(2, byteorder="little", signed=False)
        for instruction in program
    )

    uart_rx = dut.data_in_4
    uart_reset = dut.data_in_5

    assert uart_rx.value.integer == 1

    uart_reset.value = 0
    await ClockCycles(dut.clk, 2)

    # Clear PROM
    await util.uart_send(uart_rx, _baud_rate(dut), b"\x00\x00" * _prom_size(dut))
    await util.uart_send(uart_rx, _baud_rate(dut), program_bytes)

    # Wait for last write to propagate
    await ClockCycles(dut.clk, 2)

    if not GATE_LEVEL:
        for (index, value) in enumerate(dut.mbikovitsky_top.prom.value):
            dut._log.info(f"0x{index:X} - 0x{value.integer:X}")

        for value, expected in zip(dut.mbikovitsky_top.prom.value, program):
            assert value.integer == expected

    uart_reset.value = 1


async def _run_cpu(dut: HierarchyObject, cycles: int):
    cpu_reset = dut.data_in_2
    mem_reset = dut.data_in_3

    # Reset the CPU
    cpu_reset.value = 1
    mem_reset.value = 1
    await ClockCycles(dut.clk, 2)
    cpu_reset.value = 0
    mem_reset.value = 0

    # Run the CPU for some clocks
    await ClockCycles(dut.clk, cycles)


async def _test_lfsr(dut: HierarchyObject, initial_state: int, taps: int):
    """
    Exercises the DUT with the given initial state and taps.

    Verifies that the output is as expected, and returns a set of all
    encountered outputs.
    """

    _start_clock(dut)

    lfsr_reference = GLFSR.Taps(
        taps=GF2(_bits_list(taps, LFSR_BITS)),
        state=_bits_list(initial_state, LFSR_BITS),
    )

    reset_lfsr = dut.data_in_0
    reset_taps = dut.data_in_1
    data_in = Bus(
        [dut.data_in_2, dut.data_in_3, dut.data_in_4, dut.data_in_5, dut.data_in_6]
    )

    reset_taps.value = 1
    data_in.value = taps
    await ClockCycles(dut.clk, 10)
    assert data_in.value == taps
    reset_taps.value = 0

    reset_lfsr.value = 1
    data_in.value = initial_state
    await ClockCycles(dut.clk, 10)
    assert data_in.value == initial_state
    reset_lfsr.value = 0

    encountered = set()

    for _ in range(2**LFSR_BITS):
        await Timer(1, units="sec")

        expected_state = int("".join(str(int(x)) for x in lfsr_reference.state), 2)

        state = _seven_segment_to_number(dut.data_out.value.integer)

        assert state == expected_state

        encountered.add(expected_state)

        lfsr_reference.step()

    return encountered


def _start_clock(dut: HierarchyObject):
    clock_hz = (
        int(cocotb.plusargs["SIM_CLOCK_HZ"])
        if GATE_LEVEL or "SIM_CLOCK_HZ" in cocotb.plusargs
        else dut.mbikovitsky_top.CLOCK_HZ.value
    )
    util.start_clock(dut, clock_hz)


def _baud_rate(dut: HierarchyObject) -> int:
    return (
        int(cocotb.plusargs["SIM_BAUD"])
        if GATE_LEVEL or "SIM_BAUD" in cocotb.plusargs
        else dut.mbikovitsky_top.BAUD.value
    )


def _prom_size(dut: HierarchyObject) -> int:
    return (
        int(cocotb.plusargs["SIM_PROM_SIZE"])
        if GATE_LEVEL or "SIM_PROM_SIZE" in cocotb.plusargs
        else len(dut.mbikovitsky_top.prom)
    )


def _random_initial_state() -> int:
    """
    Generates a random initial state for the LFSR DUT.
    """
    return random.randint(1, 2**LFSR_BITS - 1)


def _random_taps() -> int:
    """
    Generates a random arrangement of taps for the LFSR DUT.
    """
    return random.randint(2 ** (LFSR_BITS - 1), 2**LFSR_BITS - 1)


def _bits_list(number: int, bits: int) -> List[int]:
    """
    Returns a list of the `bits` least significant bits in the given number.

    The list is returned MSB-first.
    """
    return list(reversed([_get_bit(number, i) for i in range(bits)]))


def _get_bit(number: int, bit: int) -> int:
    """
    Returns bit `bit`, counting from the LSB, of the number.
    """
    return (number >> bit) & 1


def _seven_segment_to_number(bits: int):
    """
    Decodes the seven-segment display output of the DUT.
    """

    result = 0

    if bits & (1 << 7):
        result += 0x10
        bits &= 0x7F

    result += SEVEN_SEGMENT_DECODER[bits]

    return result
