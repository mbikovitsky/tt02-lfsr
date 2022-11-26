`default_nettype none
`timescale 1ns/1ps

module extend_alu_tb (
    input  signed   [15:0]  x,
    input  signed   [15:0]  y,
    input           [8:0]   instruction,
    output signed   [15:0]  out,
    output                  zr,
    output                  ng
);

    initial begin
        $dumpfile ("extend_alu_tb.vcd");
        $dumpvars (0, extend_alu_tb);
        #1;
    end

    ExtendALU alu (
        .x(x),
        .y(y),
        .instruction(instruction),
        .out(out),
        .zr(zr),
        .ng(ng)
    );

endmodule
