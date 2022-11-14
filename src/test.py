import random
from typing import List

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer
from galois import GF2, GLFSR

LFSR_BITS = 5


@cocotb.test()
async def test_maximal_length(dut):
    # https://users.ece.cmu.edu/~koopman/lfsr/5.txt
    taps = random.choice([0x12, 0x14, 0x17, 0x1B, 0x1D, 0x1E])

    encountered = await _test_lfsr(dut, _random_initial_state(), taps)
    assert len(encountered) == 2**LFSR_BITS - 1


@cocotb.test()
async def test_random_taps(dut):
    await _test_lfsr(dut, _random_initial_state(), _random_taps())


@cocotb.test()
async def test_zero_initial_state(dut):
    encountered = await _test_lfsr(dut, 0, _random_taps())
    assert encountered == {0}


async def _test_lfsr(dut, initial_state: int, taps: int):
    clock = Clock(dut.clk, 1, units="ms")  # 1000 Hz
    cocotb.start_soon(clock.start())

    lfsr_reference = GLFSR.Taps(
        taps=GF2(_bits_lits(taps, LFSR_BITS)),
        state=_bits_lits(initial_state, LFSR_BITS),
    )

    dut.data_in.value = taps
    dut.reset_taps.value = 1
    await ClockCycles(dut.clk, 10)
    dut.reset_taps.value = 0

    dut.data_in.value = initial_state
    dut.reset_lfsr.value = 1
    await ClockCycles(dut.clk, 10)
    dut.reset_lfsr.value = 0

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
    return random.randint(1, 2**LFSR_BITS - 1)


def _random_taps() -> int:
    return random.randint(2 ** (LFSR_BITS - 1), 2**LFSR_BITS - 1)


def _bits_lits(number: int, bits: int) -> List[int]:
    return list(reversed([_get_bit(number, i) for i in range(bits)]))


def _get_bit(number: int, bit: int) -> int:
    return (number >> bit) & 1


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
    0b1100111: 9,
    0b1110111: 10,
    0b1111100: 11,
    0b0111001: 12,
    0b1011110: 13,
    0b1111001: 14,
    0b1110001: 15,
}

def _seven_segment_to_number(bits: int):
    result = 0

    if bits & (1 << 7):
        result += 0x10
        bits &= 0x7F

    result += SEVEN_SEGMENT_DECODER[bits]

    return result
