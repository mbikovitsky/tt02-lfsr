/*
 * UART transceiver. Only RXD/TXD lines and 8N1 mode is supported.
 *
 * Based on:
 * https://lab.whitequark.org/notes/2016-10-18/implementing-an-uart-in-verilog-and-migen/
 * https://nandland.com/uart-serial-port-module/
 *
 * Parameters:
 *  CLOCK_HZ:   Frequency of (clk)
 *  BAUD:       Baud rate
 *
 * Common signals:
 *  reset:      Active-high reset. Synchronous to (clk).
 *  clk:        Input clock, from which receiver and transmitter clocks are derived.
 *              All transitions happen on (posedge clk).
 *
 * Receiver signals:
 *  rx_i:       Serial line input.
 *  rx_data_o:  Received octet, only valid while (rx_ack_i).
 *  rx_ready_o: Indicates whether (rx_data_o) contains a complete octet.
 *  rx_ack_i:   Indicates that a new octet may be received.
 *  rx_error_o: Asserted if a start bit arrives while the previous octet has not
 *              been acknowledged, or if a start bit is not followed with the stop bit
 *              at the appropriate time.
 *
 * Transmitter signals:
 *  tx_o:       Serial line output.
 *  tx_data_i:  Octet to be sent. Needs to be valid while (tx_ready_i && tx_ack_o).
 *  tx_ready_i: Indicates that a new octet should be sent.
 *  tx_ack_o:   Indicates that a new octet may be sent.
 */
module UART #(
    parameter CLOCK_HZ  = 1_000_000,
    parameter BAUD      = 9600
) (
    input           reset,
    input           clk,
    // Receiver half
    input           rx_i,
    output [7:0]    rx_data_o,
    output          rx_ready_o,
    input           rx_ack_i,
    output          rx_error_o,
    // Transmitter half
    output          tx_o,
    input  [7:0]    tx_data_i,
    input           tx_ready_i,
    output          tx_ack_o
);

    // Length of a single bit in clock ticks.
    // We round down to get a slightly faster actual baud rate.
    localparam TICKS_PER_BIT = CLOCK_HZ / BAUD;
    localparam ACTUAL_BAUD = CLOCK_HZ / TICKS_PER_BIT;
    localparam PPM = 64'd1_000_000 * (ACTUAL_BAUD - BAUD) / BAUD;

    localparam TICKS_PER_HALF_BIT = TICKS_PER_BIT / 2;

    generate
        // To be on the safe side, we want to sample at least 8 times faster
        // than the baud rate
        if (TICKS_PER_BIT < 8)
            _ERROR_FREQ_TOO_HIGH_ error();

        // Seems like a safe bet...
        // https://lab.whitequark.org/notes/2016-10-18/implementing-an-uart-in-verilog-and-migen/
        if (PPM > 50_000)
            _ERROR_FREQ_DEVIATION_TOO_HIGH_ error();
    endgenerate

    // Delay input data to reduce chance of metastability
    reg rx;
    reg rx_intermediate;
    always @(posedge clk) begin
        rx_intermediate <= rx_i;
        rx <= rx_intermediate;
    end

    //
    // RX state machine
    //

    localparam RX_IDLE  = 3'd0,
               RX_START = 3'd1,
               RX_DATA  = 3'd2,
               RX_STOP  = 3'd3,
               RX_FULL  = 3'd4,
               RX_ERROR = 3'd5;

    reg [2:0] rx_state;

    reg [7:0] rx_data;

    reg [$clog2(TICKS_PER_BIT)-1:0] rx_tick_count;

    reg [$clog2(8)-1:0] rx_bit_count;

    always @(posedge clk) begin
        if (reset) begin
            rx_state <= RX_IDLE;
            rx_data <= 0;
            rx_tick_count <= 0;
            rx_bit_count <= 0;
        end else case (rx_state)
            RX_IDLE:
                if (rx == 0) begin
                    rx_state <= RX_START;
                    rx_tick_count <= 0;
                end
            RX_START:
                if (rx_tick_count == TICKS_PER_HALF_BIT - 1) begin
                    if (rx == 0) begin
                        // Input is still low after half bit length,
                        // so it's probably a start bit.
                        rx_state <= RX_DATA;
                        rx_tick_count <= 0;
                        rx_bit_count <= 0;
                    end else begin
                        // Input went high. Must be a spurious pulse.
                        rx_state <= RX_IDLE;
                    end
                end else begin
                    rx_tick_count <= rx_tick_count + 1;
                end
            RX_DATA:
                if (rx_tick_count == TICKS_PER_BIT - 1) begin
                    rx_data <= {rx, rx_data[7:1]};
                    rx_tick_count <= 0;

                    if (rx_bit_count == 7) begin
                        // All done
                        rx_state <= RX_STOP;
                    end else begin
                        rx_bit_count <= rx_bit_count + 1;
                    end
                end else begin
                    // Wait a whole bit time before sampling
                    rx_tick_count <= rx_tick_count + 1;
                end
            RX_STOP:
                if (rx_tick_count == TICKS_PER_BIT - 1) begin
                    if (rx == 0) begin
                        // Stop bit should be high
                        rx_state <= RX_ERROR;
                    end else begin
                        rx_state <= RX_FULL;
                    end
                end else begin
                    // Wait a whole bit time before sampling
                    rx_tick_count <= rx_tick_count + 1;
                end
            RX_FULL:
                if (rx_ack_i) begin
                    rx_state <= RX_IDLE;
                end else if (rx == 0) begin
                    rx_state <= RX_ERROR;
                end
        endcase
    end

    assign rx_data_o  = rx_data;
    assign rx_ready_o = (rx_state == RX_FULL);
    assign rx_error_o = (rx_state == RX_ERROR);

    //
    // TX state machine
    //

    localparam TX_IDLE  = 2'd0,
               TX_START = 2'd1,
               TX_DATA  = 2'd2,
               TX_STOP  = 2'd3;

    reg [1:0] tx_state;

    reg [7:0] tx_data;

    reg [$clog2(TICKS_PER_BIT)-1:0] tx_tick_count;

    reg [$clog2(8)-1:0] tx_bit_count;

    reg tx_buf;

    always @(posedge clk) begin
        if (reset) begin
            tx_state <= TX_IDLE;
            tx_data <= 0;
            tx_tick_count <= 0;
            tx_bit_count <= 0;
            tx_buf <= 1;
        end else case (tx_state)
            TX_IDLE:
                if (tx_ready_i) begin
                    tx_state <= TX_START;
                    tx_data <= tx_data_i;
                    tx_tick_count <= 0;
                    tx_bit_count <= 0;

                    tx_buf <= 0; // Start bit
                end
            TX_START: begin
                if (tx_tick_count == TICKS_PER_BIT - 1) begin
                    // Done transmitting the start bit
                    tx_state <= TX_DATA;
                    tx_tick_count <= 0;

                    // First bit of data
                    tx_buf <= tx_data[0];
                end else begin
                    tx_tick_count <= tx_tick_count + 1;
                end
            end
            TX_DATA: begin
                if (tx_tick_count == TICKS_PER_BIT - 1) begin
                    tx_data <= {1'b0, tx_data[7:1]};
                    tx_tick_count <= 0;

                    if (tx_bit_count == 7) begin
                        // All done
                        tx_state <= TX_STOP;
                        tx_buf <= 1; // Stop bit
                    end else begin
                        tx_buf <= tx_data[1]; // Next bit of data
                        tx_bit_count <= tx_bit_count + 1;
                    end
                end else begin
                    tx_tick_count <= tx_tick_count + 1;
                end
            end
            TX_STOP: begin
                if (tx_tick_count == TICKS_PER_BIT - 2) begin
                    tx_state <= TX_IDLE;
                    tx_tick_count <= 0;
                end else begin
                    tx_tick_count <= tx_tick_count + 1;
                end
            end
        endcase
    end

    assign tx_o     = tx_buf;
    assign tx_ack_o = (tx_state == TX_IDLE);

endmodule
