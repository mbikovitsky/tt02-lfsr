`default_nettype none
`timescale 1ns/1ps

module cpu_tb (
    input   clk,
    input   cpu_reset,
    input   mem_reset
);

    initial begin
        $dumpfile ("cpu_tb.vcd");
        $dumpvars (0, cpu_tb);
        #1;
    end

    CPU cpu (
        .clk(clk),
        .reset(cpu_reset),
        .instruction(instruction),
        .next_instruction_addr_o(next_instruction_addr),
        .memory_addr_o(memory_addr),
        .memory_we_o(memory_we),
        .memory_i(cpu_memory_in),
        .memory_o(cpu_memory_out)
    );

    wire [15:0] instruction;
    wire [14:0] next_instruction_addr;

    wire [14:0] memory_addr;
    wire        memory_we;
    wire [15:0] cpu_memory_in;
    wire [15:0] cpu_memory_out;

    RAM #(
        .WORDS(16 * 1024),
        .WORD_WIDTH(16)
    ) ram (
        .clk(clk),
        .reset(mem_reset),
        .address_i(memory_addr[13:0]),
        .wr_en_i(memory_we),
        .data_i(cpu_memory_out),
        .data_o(cpu_memory_in)
    );

    RAM #(
        .WORDS(32 * 1024),
        .WORD_WIDTH(16)
    ) rom (
        .clk(clk),
        .reset(mem_reset),
        .address_i(next_instruction_addr),
        .wr_en_i(1'b0),
        .data_i(16'b0),
        .data_o(instruction)
    );

endmodule
