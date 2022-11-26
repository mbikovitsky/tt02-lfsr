`default_nettype none
`timescale 1ns/1ps

module ram_tb #(
`ifdef WORDS
    parameter WORDS      = `WORDS,
`else
    parameter WORDS      = 1024,
`endif
`ifdef WORD_WIDTH
    parameter WORD_WIDTH = `WORD_WIDTH
`else
    parameter WORD_WIDTH = 8
`endif
) (
    input                       clk,
    input                       reset,
    input  [$clog2(WORDS)-1:0]  address_i,
    input                       wr_en_i,
    input  [WORD_WIDTH-1:0]     data_i,
    output [WORD_WIDTH-1:0]     data_o
);

    initial begin
        $dumpfile ("ram_tb.vcd");
        $dumpvars (0, ram_tb);
        #1;
    end

    RAM #(
        .WORDS(WORDS),
        .WORD_WIDTH(WORD_WIDTH)
    ) ram (
        .clk(clk),
        .reset(reset),
        .address_i(address_i),
        .wr_en_i(wr_en_i),
        .data_i(data_i),
        .data_o(data_o)
    );

endmodule
