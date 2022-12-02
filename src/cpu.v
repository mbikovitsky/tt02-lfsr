/*
 * Extended CPU based on the Nand2Tetris course at the Hebrew University of Jerusalem.
 *
 * Signals:
 *  clk:                        Input clock. All transitions happen on (posedge clk).
 *  reset:                      Active-high reset. Synchronous to (clk).
 *  instruction:                Current instruction.
 *  next_instruction_addr_o:    Outputs the address of the next instruction.
 *  memory_addr_o:              Memory address to operate on.
 *  memory_we_o:                Whether to write the contents of (memory_o) to memory.
 *  memory_i:                   Current value at memory address (memory_addr_o).
 *  memory_o:                   Memory output value.
 */
module CPU (
    input           clk,
    input           reset,

    input   [15:0]  instruction,
    output  [14:0]  next_instruction_addr_o,

    output  [14:0]  memory_addr_o,
    output          memory_we_o,
    input   [15:0]  memory_i,
    output  [15:0]  memory_o
);

    wire c_instruction = instruction[15];
    wire a_instruction = !c_instruction;

    // A register. Loaded when the instruction is the A instruction,
    // or when the instruction is the C instruction and the destination
    // spec. is A.
    reg [15:0] a_reg;
    always @(posedge clk) begin
        if (reset) begin
            a_reg <= 0;
        end else begin
            if (a_instruction) begin
                a_reg <= {1'b0, instruction[14:0]};
            end else if (instruction[5]) begin
                a_reg <= alu_output;
            end
        end
    end

    // D register. Loaded when the instruction is the C instruction
    // and the destination spec. is D.
    reg [15:0] d_reg;
    always @(posedge clk) begin
        if (reset) begin
            d_reg <= 0;
        end else begin
            if (c_instruction && instruction[4]) begin
                d_reg <= alu_output;
            end
        end
    end

    // "M" register.
    // The input value is already provided inside inM, and we always pipe
    // the ALU output to outM and the A register's value to addressM.
    // The only thing remaining to be taken care of is the writeM output.
    // We write to M when the instruction is the C instruction and
    // the destination spec. is M.
    assign memory_addr_o = a_reg[14:0];
    assign memory_we_o = (c_instruction && instruction[3]);
    assign memory_o = alu_output;

    // PC register. Input is always the A register, but whether it is actually
    // used is controlled by the ALU output and the jump bits
    // of the instruction.
    reg [14:0] pc_reg;
    always @(posedge clk) begin
        if (reset) begin
            pc_reg <= 0;
        end else begin
            if (jump) begin
                pc_reg <= a_reg[14:0];
            end else begin
                pc_reg <= pc_reg + 1;
            end
        end
    end

    assign next_instruction_addr_o = pc_reg;

    // ALU operation. The first input is always the D register,
    // and the second input varies according to the 'a' bit in the instruction.
    // Bits 6..11 of the instruction (the 'comp' bits) map nicely
    // to the ALU inputs, so we simply forward them as-is.
    // The extended CPU also defines bits 13 and 14 of the instruction
    // to control the extended ALU functions. Again, these map nicely to
    // bits 7 and 8 of the ALU input, so we can forward them as well.
    // See the documentation for the extended ALU for more insight.
    ExtendALU alu (
        .x(d_reg),
        .y(instruction[12] ? memory_i : a_reg),
        .instruction({instruction[14:13], 1'b0, instruction[11:6]}),
        .out(alu_output),
        .zr(alu_zero),
        .ng(alu_negative)
    );

    wire [15:0] alu_output;
    wire        alu_zero;
    wire        alu_negative;
    wire        alu_positive = ((!alu_negative) && (!alu_zero));

    // Determine whether a jump should actually take place.
    wire jump = c_instruction && (
        (instruction[0] && alu_positive)    ||
        (instruction[1] && alu_zero)        ||
        (instruction[2] && alu_negative)
    );

endmodule
