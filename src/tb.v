`default_nettype none
`timescale 1ns/1ps

module tb (
    input clk,
    input data_in_0,
    input data_in_1,
    input data_in_2,
    input data_in_3,
    input data_in_4,
    input data_in_5,
    input data_in_6,
    output [7:0] data_out
);

    initial begin
        $dumpfile ("tb.vcd");
        $dumpvars (0, tb);
        #1;
    end

    mbikovitsky_top
`ifdef CLOCK_HZ
    #(.CLOCK_HZ(`CLOCK_HZ))
`endif
    mbikovitsky_top (
        .io_in ({data_in_6, data_in_5, data_in_4, data_in_3, data_in_2, data_in_1, data_in_0, clk}),
        .io_out (data_out)
    );

endmodule
