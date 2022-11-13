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

        state = int("".join(str(int(x)) for x in lfsr_reference.state), 2)
        assert dut.data_out.value.integer == state

        encountered.add(state)

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
