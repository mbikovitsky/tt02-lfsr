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
    input wire [4:0] value_i,
    output reg [7:0] segments_o
);

    always @(*) begin
        case(value_i)
            // Hex digits
            // https://en.wikipedia.org/wiki/Seven-segment_display#Hexadecimal

            //                          pgfedcba
            'h00:       segments_o = 8'b00111111;
            'h01:       segments_o = 8'b00000110;
            'h02:       segments_o = 8'b01011011;
            'h03:       segments_o = 8'b01001111;
            'h04:       segments_o = 8'b01100110;
            'h05:       segments_o = 8'b01101101;
            'h06:       segments_o = 8'b01111101;
            'h07:       segments_o = 8'b00000111;
            'h08:       segments_o = 8'b01111111;
            'h09:       segments_o = 8'b01101111;
            'h0A:       segments_o = 8'b01110111;
            'h0B:       segments_o = 8'b01111100;
            'h0C:       segments_o = 8'b00111001;
            'h0D:       segments_o = 8'b01011110;
            'h0E:       segments_o = 8'b01111001;
            'h0F:       segments_o = 8'b01110001;

            // Hex digits, but with the dot :)

            'h10:       segments_o = 8'b10111111;
            'h11:       segments_o = 8'b10000110;
            'h12:       segments_o = 8'b11011011;
            'h13:       segments_o = 8'b11001111;
            'h14:       segments_o = 8'b11100110;
            'h15:       segments_o = 8'b11101101;
            'h16:       segments_o = 8'b11111101;
            'h17:       segments_o = 8'b10000111;
            'h18:       segments_o = 8'b11111111;
            'h19:       segments_o = 8'b11101111;
            'h1A:       segments_o = 8'b11110111;
            'h1B:       segments_o = 8'b11111100;
            'h1C:       segments_o = 8'b10111001;
            'h1D:       segments_o = 8'b11011110;
            'h1E:       segments_o = 8'b11111001;
            'h1F:       segments_o = 8'b11110001;

            default:    segments_o = 8'b00000000;
        endcase
    end

endmodule
