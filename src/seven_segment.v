module seven_segment (
    input wire [4:0] value,
    output reg [7:0] segments
);

    always @(*) begin
        case(value)
            // Hex digits
            // https://en.wikipedia.org/wiki/Seven-segment_display#Hexadecimal
            'h0:        segments = 8'b00111111;
            'h1:        segments = 8'b00000110;
            'h2:        segments = 8'b01011011;
            'h3:        segments = 8'b01001111;
            'h4:        segments = 8'b01100110;
            'h5:        segments = 8'b01101101;
            'h6:        segments = 8'b01111101;
            'h7:        segments = 8'b00000111;
            'h8:        segments = 8'b01111111;
            'h9:        segments = 8'b01101111;
            'hA:        segments = 8'b01110111;
            'hB:        segments = 8'b01111100;
            'hC:        segments = 8'b00111001;
            'hD:        segments = 8'b01011110;
            'hE:        segments = 8'b01111001;
            'hF:        segments = 8'b01110001;

            // Hex digits, but with the dot :)
            'h10:       segments = 8'b10111111;
            'h11:       segments = 8'b10000110;
            'h12:       segments = 8'b11011011;
            'h13:       segments = 8'b11001111;
            'h14:       segments = 8'b11100110;
            'h15:       segments = 8'b11101101;
            'h16:       segments = 8'b11111101;
            'h17:       segments = 8'b10000111;
            'h18:       segments = 8'b11111111;
            'h19:       segments = 8'b11101111;
            'h1A:       segments = 8'b11110111;
            'h1B:       segments = 8'b11111100;
            'h1C:       segments = 8'b10111001;
            'h1D:       segments = 8'b11011110;
            'h1E:       segments = 8'b11111001;
            'h1F:       segments = 8'b11110001;

            default:    segments = 8'b00000000;
        endcase
    end

endmodule
