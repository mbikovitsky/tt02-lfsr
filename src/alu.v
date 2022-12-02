/*
 * ALU based on the Nand2Tetris course at the Hebrew University of Jerusalem.
 *
 * Signals:
 *  x:           First input.
 *  y:           Second input.
 *  zx:          If high, the (x) input is treated as 0, instead.
 *  nx:          If high, the (x) input is inverted, after applying (zx).
 *  zy:          If high, the (y) input is treated as 0, instead.
 *  ny:          If high, the (y) input is inverted, after applying (zy).
 *  f:           If high, computes (x + y). Otherwise, (x & y).
 *  no:          If high, the computation result is inverted.
 *  out:         Operation result.
 *  zr:          Indicates whether the result is 0.
 *  ng:          Indicates whether the result is negative.
 */
module ALU (
    input  signed   [15:0]  x,
    input  signed   [15:0]  y,
    input                   zx,
    input                   nx,
    input                   zy,
    input                   ny,
    input                   f,
    input                   no,

    output signed   [15:0]  out,
    output                  zr,
    output                  ng
);

    // Preprocess x
    reg signed [15:0] input_x;
    always @(*) begin
        input_x = (zx ? 0 : x);
        input_x = (nx ? ~input_x : input_x);
    end

    // Preprocess y
    reg signed [15:0] input_y;
    always @(*) begin
        input_y = (zy ? 0 : y);
        input_y = (ny ? ~input_y : input_y);
    end

    // Carry out the calculations and select the appropriate result
    reg signed [15:0] result;
    always @(*) begin
        if (f)
            result = input_x + input_y;
        else
            result = input_x & input_y;

        if (no)
            result = ~result;
    end

    assign out = result;
    assign zr = (result == 0);
    assign ng = (result < 0);

endmodule
