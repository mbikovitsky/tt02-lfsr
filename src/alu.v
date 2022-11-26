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
