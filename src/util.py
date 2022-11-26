import random

import cocotb
from cocotb.clock import Clock
from cocotb.handle import HierarchyObject, ModifiableObject
from cocotb.triggers import Timer


def randbytes(count: int) -> bytes:
    """
    Generates a random sequence of bytes.
    """
    return bytes(random.randint(0x00, 0xFF) for _ in range(count))


def start_clock(dut: HierarchyObject, clock_hz: int):
    """
    Starts a clock on an input called `clk` of the given DUT,
    with a frequency of `clock_hz`.
    """
    clock = Clock(dut.clk, round(1e9 / clock_hz), units="ns")
    cocotb.start_soon(clock.start())


async def uart_send(rx: ModifiableObject, baud: int, data: bytes):
    """
    Sends a sequence of bytes using 8N1 UART, with the given `baud` rate.
    """
    for byte in data:
        await uart_send_byte(rx, baud, byte)


async def uart_send_byte(
    rx: ModifiableObject, baud: int, byte: int, invalid_stop: bool = False
):
    """
    Sends a single byte using 8N1 UART, with the given `baud` rate.

    If `invalid_stop` is `True`, will generate an invalid stop bit (0).
    """

    assert 0 <= byte <= 0xFF

    # Start bit
    rx.value = 0
    await bit_time(baud)

    # Data bits
    for bit in range(8):
        rx.value = (byte >> bit) & 1
        await bit_time(baud)

    # Stop bit
    if invalid_stop:
        rx.value = 0
    else:
        rx.value = 1
    await bit_time(baud)


async def bit_time(baud: int):
    """
    Waits for a single bit time for with given baud rate.
    """
    await Timer(round(1e9 / baud), "ns")
