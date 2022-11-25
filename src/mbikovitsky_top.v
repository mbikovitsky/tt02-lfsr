module mbikovitsky_top #(
    parameter CLOCK_HZ = 6250
) (
    input [7:0] io_in,
    output [7:0] io_out
);

    localparam LFSR_BITS = 5;

    wire clk = io_in[0];

    wire mode_cpu = reset_lfsr & reset_taps;

    // TODO: Assign CPU output
    assign io_out = mode_cpu ? 0 : segments;

    // LFSR

    wire reset_lfsr = io_in[1];
    wire reset_taps = io_in[2];
    wire [LFSR_BITS-1:0] data_in = io_in[3+LFSR_BITS-1:3];

    wire [7:0] segments;

    seven_segment seven_segment (
        .value_i(lfsr_out),
        .segments_o(segments)
    );

    wire [LFSR_BITS-1:0] lfsr_out;

    lfsr #(.BITS(LFSR_BITS), .TICKS(CLOCK_HZ)) lfsr(
        .clk(clk),

        .reset_lfsr_i(reset_lfsr),
        .initial_state_i(data_in),

        .reset_taps_i(reset_taps),
        .taps_i(data_in),

        .state_o(lfsr_out)
    );

    // CPU

    // TODO

endmodule
