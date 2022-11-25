import random
from typing import Iterable, List

import cocotb
from cocotb.clock import Clock
from cocotb.handle import HierarchyObject, ModifiableObject
from cocotb.triggers import ClockCycles, Timer
from galois import GF2, GLFSR

LFSR_BITS = 5
PRODUCTION_CLOCK_HZ = 1000  # Clock frequency in the production design


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


async def _test_lfsr(dut: HierarchyObject, initial_state: int, taps: int):
    """
    Exercises the DUT with the given initial state and taps.

    Verifies that the output is as expected, and returns a set of all
    encountered outputs.
    """

    clock_hz = int(cocotb.plusargs.get("SIM_CLOCK_HZ", PRODUCTION_CLOCK_HZ))
    clock_period_ns = round(1e9 / clock_hz)

    clock = Clock(dut.clk, clock_period_ns, units="ns")
    cocotb.start_soon(clock.start())

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
