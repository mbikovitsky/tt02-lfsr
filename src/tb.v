`default_nettype none
`timescale 1ns/1ps

module tb (
    input clk,
    input reset_lfsr,
    input reset_taps,
    input [4:0] data_in,
    output [7:0] data_out
);

    initial begin
        $dumpfile ("tb.vcd");
        $dumpvars (0, tb);
        #1;
    end

    mbikovitsky_top #(.CLOCK_HZ(1)) mbikovitsky_top (
        .io_in ({data_in, reset_taps, reset_lfsr, clk}),
        .io_out (data_out)
    );

endmodule
