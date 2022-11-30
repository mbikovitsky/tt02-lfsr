/*
 * Seven segment display encoder.
 *
 * ┌───A───┐
 * │       │
 * F       B
 * │       │
 * ├───G───┤
 * │       │
 * E       C  ┌─┐
 * │       │  │P│
 * └───D───┘  └─┘
 *
 * Signals:
 *  value_i:        Value to encode.
 *  segments_o:     Encoded value.
 *                  Bit order is pgfedcba.
 *                  Values between 0x00-0x0F are output as hex digits.
 *                  Values between 0x10-0x1F are output as hex digits with a dot.
 */
module seven_segment (
    input [4:0] value_i,
    output [7:0] segments_o
);

    assign segments_o = {value_i[4], segments_low};

    reg [6:0] segments_low;
    always @(*) begin
        case(value_i[3:0])
            // Hex digits
            // https://en.wikipedia.org/wiki/Seven-segment_display#Hexadecimal

            //                      gfedcba
            4'h0: segments_low = 7'b0111111;
            4'h1: segments_low = 7'b0000110;
            4'h2: segments_low = 7'b1011011;
            4'h3: segments_low = 7'b1001111;
            4'h4: segments_low = 7'b1100110;
            4'h5: segments_low = 7'b1101101;
            4'h6: segments_low = 7'b1111101;
            4'h7: segments_low = 7'b0000111;
            4'h8: segments_low = 7'b1111111;
            4'h9: segments_low = 7'b1101111;
            4'hA: segments_low = 7'b1110111;
            4'hB: segments_low = 7'b1111100;
            4'hC: segments_low = 7'b0111001;
            4'hD: segments_low = 7'b1011110;
            4'hE: segments_low = 7'b1111001;
            4'hF: segments_low = 7'b1110001;
        endcase
    end

endmodule
