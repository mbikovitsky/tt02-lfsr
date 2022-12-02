/*
 * Galois LFSR.
 *
 * Note: The LFSR won't run if any of the resets are asserted.
 *
 * Parameters:
 *  BITS:               Number of bits for the LFSR state.
 *  TICKS:              Number of clock ticks between LFSR state transitions.
 *
 * Signals:
 *  clk:                Input clock. Resets are synchronous to it.
 *
 *  reset_lfsr_i:       Active-high. Resets the LFSR state to the input
 *                      from (initial_state_i).
 *  initial_state_i:    --
 *
 *  reset_taps_i:       Active-high. Resets the LFSR's taps to the input from (taps_i).
 *  taps_i:             --
 *
 *  state_o:            Outputs the current LFSR state.
 */
module lfsr #(
    parameter BITS = 8,
    parameter TICKS = 1
) (
    input clk,

    input reset_lfsr_i,
    input [BITS-1:0] initial_state_i,

    input reset_taps_i,
    input [BITS-1:0] taps_i,

    output [BITS-1:0] state_o
);

    reg [BITS-1:0] lfsr;

    localparam TICK_BITS = ($clog2(TICKS) == 0) ? 1 : $clog2(TICKS);
    reg [TICK_BITS-1:0] tick_count;

    assign state_o = lfsr;

    always @(posedge clk) begin
        if (reset_lfsr_i) begin
            tick_count <= 0;
            lfsr <= initial_state_i;
        end else if (reset_taps_i) begin
        end else begin
            if (tick_count == TICKS - 1) begin
                tick_count <= 0;

                // Advance the LFSR
                if (lfsr[0]) begin
                    lfsr <= (lfsr >> 1) ^ taps_i;
                end else begin
                    lfsr <= (lfsr >> 1);
                end
            end else begin
                tick_count <= tick_count + 1;
            end
        end
    end

endmodule
