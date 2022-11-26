`default_nettype none
`timescale 1ns/1ps

module uart_tb (
    input           reset,
    input           clk,
    // Receiver half
    input           rx_i,
    output [7:0]    rx_data_o,
    output          rx_ready_o,
    input           rx_ack_i,
    output          rx_error_o,
    // Transmitter half
    output          tx_o,
    input  [7:0]    tx_data_i,
    input           tx_ready_i,
    output          tx_ack_o,
    // Loopback mode
    input           loopback_i
);

    localparam CLOCK_HZ = 6250;
    localparam BAUD     = 781;

    initial begin
        $dumpfile ("uart_tb.vcd");
        $dumpvars (0, uart_tb);
        #1;
    end

    wire [7:0] rx_data;
    wire       rx_ready;
    wire       rx_ack;
    wire [7:0] tx_data;
    wire       tx_ready;
    wire       tx_ack;

    assign rx_data_o    = rx_data;
    assign rx_ready_o   = rx_ready;
    assign tx_ack_o     = tx_ack;

    assign rx_ack       = loopback_i ? rx_strobe    : rx_ack_i;
    assign tx_data      = loopback_i ? data         : tx_data_i;
    assign tx_ready     = loopback_i ? tx_strobe    : tx_ready_i;

    reg        empty;
    reg  [7:0] data;
    wire       rx_strobe = (rx_ready && empty);
    wire       tx_strobe = (tx_ack && !empty);

    always @(posedge clk) begin
        if (reset) begin
            empty <= 1'b1;
            data <= 8'h00;
        end else begin
            if (rx_strobe) begin
                data <= rx_data;
                empty <= 1'b0;
            end
            if (tx_strobe) begin
                empty <= 1'b1;
            end
        end
    end

    UART #(
        .CLOCK_HZ(CLOCK_HZ),
        .BAUD(BAUD)
    ) uart(
        .reset(reset),
        .clk(clk),

        .rx_i(rx_i),
        .rx_data_o(rx_data),
        .rx_ready_o(rx_ready),
        .rx_ack_i(rx_ack),
        .rx_error_o(rx_error_o),

        .tx_o(tx_o),
        .tx_data_i(tx_data),
        .tx_ready_i(tx_ready),
        .tx_ack_o(tx_ack)
    );

endmodule
