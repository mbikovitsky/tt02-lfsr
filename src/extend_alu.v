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

    // Choose which of the results we should output.
    // If both bits are set - return whatever the plain ALU returned.
    // Otherwise, the lower bit takes precedence, 0 meaning the multiplication
    // result should be returned. If it is not 0, we return the shift
    // result.
    // UPDATE: Multiplication disabled
    reg signed [15:0] result;
    always @(*) begin
        if (instruction[8]) begin
            result = simple_alu_result;
        end else begin
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
        end
    end

    assign out = result;
    assign zr = (result == 0);
    assign ng = (result < 0);

endmodule
