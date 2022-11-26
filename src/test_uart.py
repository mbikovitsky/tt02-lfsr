import cocotb
from cocotb.handle import HierarchyObject
from cocotb.triggers import ClockCycles, FallingEdge

import util

DEFAULT_CLOCK_HZ = 6250
DEFAULT_UART_BAUD = 781


@cocotb.test()
async def test_rx(dut: HierarchyObject):
    util.start_clock(dut, DEFAULT_CLOCK_HZ)

    await _reset(dut, 10)

    await _test_rx_pattern(dut, DEFAULT_UART_BAUD, b"\x55")
    await _test_rx_pattern(dut, DEFAULT_UART_BAUD, b"\xC3")
    await _test_rx_pattern(dut, DEFAULT_UART_BAUD, b"\x81")
    await _test_rx_pattern(dut, DEFAULT_UART_BAUD, b"\xA5")
    await _test_rx_pattern(dut, DEFAULT_UART_BAUD, b"\xFF")
    await _test_rx_pattern(dut, DEFAULT_UART_BAUD, b"\x00")
    await _test_rx_pattern(dut, DEFAULT_UART_BAUD, b"Hello, world!")
    await _test_rx_pattern(dut, DEFAULT_UART_BAUD, util.randbytes(0x100))


@cocotb.test()
async def test_rx_frame_error(dut: HierarchyObject):
    util.start_clock(dut, DEFAULT_CLOCK_HZ)

    await _reset(dut, 10)

    await util.uart_send_byte(dut.rx_i, DEFAULT_UART_BAUD, 0xFF, True)
    assert dut.rx_error_o.value.integer
    assert not dut.rx_ready_o.value.integer


@cocotb.test()
async def test_rx_overflow(dut: HierarchyObject):
    util.start_clock(dut, DEFAULT_CLOCK_HZ)

    await _reset(dut, 10)

    await util.uart_send(dut.rx_i, DEFAULT_UART_BAUD, b"\xFF\x00")
    assert dut.rx_error_o.value.integer


@cocotb.test()
async def test_rx_sample_shift(dut: HierarchyObject):
    util.start_clock(dut, DEFAULT_CLOCK_HZ)

    # Start in the middle of the start bit
    for i in range(1, 6):
        await _test_rx_pattern(dut, DEFAULT_UART_BAUD, b"\x55", reset_cycles=i)


@cocotb.test()
async def test_tx(dut: HierarchyObject):
    util.start_clock(dut, DEFAULT_CLOCK_HZ)

    await _reset(dut, 10)

    await _test_tx_pattern(dut, DEFAULT_UART_BAUD, b"\x55")
    await _test_tx_pattern(dut, DEFAULT_UART_BAUD, b"\xC3")
    await _test_tx_pattern(dut, DEFAULT_UART_BAUD, b"\x81")
    await _test_tx_pattern(dut, DEFAULT_UART_BAUD, b"\xA5")
    await _test_tx_pattern(dut, DEFAULT_UART_BAUD, b"\xFF")
    await _test_tx_pattern(dut, DEFAULT_UART_BAUD, b"\x00")
    await _test_tx_pattern(dut, DEFAULT_UART_BAUD, b"Hello, world!")
    await _test_tx_pattern(dut, DEFAULT_UART_BAUD, util.randbytes(0x100))


@cocotb.test(skip=True)
async def test_loopback(dut: HierarchyObject):
    util.start_clock(dut, DEFAULT_CLOCK_HZ)

    await _reset(dut, 10, loopback=True)

    pattern = util.randbytes(64 * 1024)  # 64kb of data :)

    cocotb.start_soon(util.uart_send(dut.rx_i, DEFAULT_UART_BAUD, pattern))

    received = bytearray()

    while len(received) != len(pattern):
        assert not dut.rx_error_o.value.integer

        # Wait for start bit
        await FallingEdge(dut.tx_o)

        byte = 0
        for bit in range(8):
            # Wait bit time
            await util.bit_time(DEFAULT_UART_BAUD)

            # Sample bit
            byte |= dut.tx_o.value.integer << bit
        received.append(byte)

        # Wait for stop bit
        await util.bit_time(DEFAULT_UART_BAUD)
        assert dut.tx_o.value.integer  # It should be high

        if len(received) % 0x1000 == 0:
            dut._log.info(f"Received 0x{len(received):X} bytes")

    assert received == pattern


async def _test_rx_pattern(
    dut: HierarchyObject, baud: int, pattern: bytes, reset_cycles: int = 0
):
    send_task = cocotb.start_soon(util.uart_send(dut.rx_i, baud, pattern))

    if reset_cycles:
        await _reset(dut, reset_cycles)

    received = bytearray()

    while len(received) != len(pattern):
        while not dut.rx_ready_o.value.integer:
            assert not dut.rx_error_o.value.integer
            await ClockCycles(dut.clk, 1)

        received.append(dut.rx_data_o.value.integer)

        dut.rx_ack_i.value = 1

        while dut.rx_ready_o.value.integer:
            assert not dut.rx_error_o.value.integer
            await ClockCycles(dut.clk, 1)

        dut.rx_ack_i.value = 0

    assert received == pattern

    # Wait a little more to check that no more data is output
    await send_task.join()
    await ClockCycles(dut.clk, 100)
    assert not dut.rx_error_o.value.integer
    assert not dut.rx_ready_o.value.integer


async def _test_tx_pattern(dut: HierarchyObject, baud: int, pattern: bytes):
    for byte in pattern:
        # The output line should be high (stop bit)
        assert dut.tx_o.value.integer == 1

        # We should be able to send an octet
        assert dut.tx_ack_o.value.integer

        dut.tx_data_i.value = byte
        dut.tx_ready_i.value = 1

        # Wait for transmission to start
        await FallingEdge(dut.tx_o)
        assert not dut.tx_ack_o.value.integer
        dut.tx_ready_i.value = 0

        # Check transmitted bits
        for bit in range(8):
            assert not dut.tx_ack_o.value.integer

            await util.bit_time(baud)

            assert dut.tx_o.value.integer == ((byte >> bit) & 1)

        # Check stop bit
        assert not dut.tx_ack_o.value.integer
        await util.bit_time(baud)
        assert dut.tx_o.value.integer == 1
        assert not dut.tx_ack_o.value.integer
        await util.bit_time(baud)


async def _reset(dut: HierarchyObject, cycles: int, loopback: bool = False):
    dut.reset.value = 1
    dut.loopback_i.value = bool(loopback)
    await ClockCycles(dut.clk, cycles)
    dut.reset.value = 0
    await ClockCycles(dut.clk, 1)
