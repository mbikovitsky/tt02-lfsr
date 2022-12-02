/*
 * Single port RAM.
 *
 * Parameters:
 *  WORDS:          Number of RAM cells.
 *  WORD_WIDTH:     Width of each cell, in bits.
 *
 * Signals:
 *  clk:        Input clock. All transitions happen on (posedge clk).
 *  reset:      Active-high reset. Synchronous to (clk).
 *  address_i:  Address.
 *  wr_en_i:    Write-enable.
 *  data_i:     Data to be written if (wr_en_i) is high.
 *  data_o:     Data currently at address (address_i).
 */
module RAM #(
    parameter WORDS      = 1024,
    parameter WORD_WIDTH = 8
) (
    input                       clk,
    input                       reset,
    input  [$clog2(WORDS)-1:0]  address_i,
    input                       wr_en_i,
    input  [WORD_WIDTH-1:0]     data_i,
    output [WORD_WIDTH-1:0]     data_o
);

    reg [WORD_WIDTH-1:0] memory [WORDS];

    assign data_o = memory[address_i];

    integer i;
    always @(posedge clk) begin
        if (reset) begin
            for (i = 0; i < WORDS; i = i + 1) begin
                memory[i] <= 0;
            end
        end else begin
            if (wr_en_i) begin
                memory[address_i] <= data_i;
            end
        end
    end

endmodule
