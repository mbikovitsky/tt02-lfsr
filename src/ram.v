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
