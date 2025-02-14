/*
 * Extended ALU based on the Nand2Tetris course at the Hebrew University of Jerusalem.
 *
 * Signals:
 *  x:           First input.
 *  y:           Second input.
 *  instruction: Encodes the operation to perform.
 *  out:         Operation result.
 *  zr:          Indicates whether the result is 0.
 *  ng:          Indicates whether the result is negative.
 */
module ExtendALU (
    input  signed   [15:0]  x,
    input  signed   [15:0]  y,
    input           [8:0]   instruction,
    output signed   [15:0]  out,
    output                  zr,
    output                  ng
);

    wire signed [15:0] simple_alu_result;

    // Delegate all the boring stuff to the simple ALU.
    ALU alu(
        .x(x), .y(y),
        .zx(instruction[5]), .nx(instruction[4]),
        .zy(instruction[3]), .ny(instruction[2]),
        .f(instruction[1]),
        .no(instruction[0]),
        .out(simple_alu_result)
    );

    reg signed [15:0] result;
    always @(*) begin
        case (instruction[8:7])
            2'b00:
                result = x ^ y;
            2'b01:
                case (instruction[5:4])
                    2'b00:
                        result = y >>> 1;
                    2'b01:
                        result = x >>> 1;
                    2'b10:
                        result = y <<< 1;
                    2'b11:
                        result = x <<< 1;
                endcase
            2'b10:
                result = x ^ y;
            2'b11:
                result = simple_alu_result;
        endcase
    end

    assign out = result;
    assign zr = (result == 0);
    assign ng = (result < 0);

endmodule
