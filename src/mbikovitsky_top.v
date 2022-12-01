module mbikovitsky_top #(
    parameter CLOCK_HZ = 6250,
    parameter BAUD = 781,
    parameter ROM_WORDS = 27,
    parameter RAM_WORDS = 2  // Must be a power of 2
) (
    input [7:0] io_in,
    output [7:0] io_out
);

    localparam LFSR_BITS = 5;

    generate
        if (RAM_WORDS < 2)
            _ERROR_RAM_SIZE_MUST_BE_AT_LEAST_2_ error();
        if ((RAM_WORDS & (RAM_WORDS - 1)) != 0)
            _ERROR_RAM_SIZE_MUST_BE_A_POWER_OF_2_ error();
    endgenerate

    wire clk = io_in[0];

    wire mode_cpu = reset_lfsr & reset_taps;

    assign io_out = mode_cpu ? cpu_io_out : segments;

    //
    // LFSR
    //

    wire reset_lfsr = io_in[1];
    wire reset_taps = io_in[2];
    wire [LFSR_BITS-1:0] data_in = io_in[3+LFSR_BITS-1:3];

    wire [7:0] segments;

    seven_segment seven_segment (
        .value_i(lfsr_out),
        .segments_o(segments)
    );

    wire [LFSR_BITS-1:0] lfsr_out;

    lfsr #(.BITS(LFSR_BITS), .TICKS(CLOCK_HZ)) lfsr(
        .clk(clk),

        .reset_lfsr_i(reset_lfsr),
        .initial_state_i(data_in),

        .reset_taps_i(reset_taps),
        .taps_i(data_in),

        .state_o(lfsr_out)
    );

    //
    // CPU
    //

    wire cpu_reset  = (!mode_cpu) || (mode_cpu && io_in[3]);
    wire mem_reset  = (!mode_cpu) || (mode_cpu && io_in[4]);
    wire uart_reset = (!mode_cpu) || (mode_cpu && (!io_in[3] || io_in[4]));
    wire uart_rx    = io_in[5];

    CPU cpu (
        .clk(clk),
        .reset(cpu_reset),
        .instruction(instruction),
        .next_instruction_addr_o(next_instruction_addr),
        .memory_addr_o(memory_addr),
        .memory_we_o(memory_we),
        .memory_i(cpu_memory_in),
        .memory_o(cpu_memory_out)
    );

    wire [15:0] instruction;
    wire [14:0] next_instruction_addr;

    wire [14:0] memory_addr;
    wire        memory_we;
    reg  [15:0] cpu_memory_in;
    wire [15:0] cpu_memory_out;

    // Address map (in 16-bit words)
    // ---
    // 0            -   RAM_WORDS-1     - RAM
    // RAM_WORDS    -   0x3FFF          - A20 :)
    // 0x4000       -   0x4000          - io_in (high 8 bits are always 0 on read)
    // 0x4001       -   0x4001          - io_out (high 8 bits are ignored on write,
    //                                            0 on read)

    wire is_ram_address = !memory_addr[14];
    wire is_io_in_address = (!is_ram_address) && (memory_addr[0] == 0);
    wire is_io_out_address = (!is_ram_address) && (memory_addr[0] == 1);

    // Route memory reads
    always @(*) begin
        if (is_ram_address) begin
            cpu_memory_in = ram_data_out;
        end else if (is_io_in_address) begin
            cpu_memory_in = {'0, io_in};
        end else if (is_io_out_address) begin
            cpu_memory_in = {'0, cpu_io_out};
        end else begin
            // Reads from any other address return 0xFF
            cpu_memory_in = '1;
        end
    end

    // I/O output
    reg [7:0] cpu_io_out;
    always @(posedge clk) begin
        if (mem_reset) begin
            cpu_io_out <= 0;
        end else begin
            if (memory_we && is_io_out_address) begin
                cpu_io_out <= cpu_memory_out[7:0];
            end
        end
    end

    wire [15:0] ram_data_out;

    // RAM

    RAM #(
        .WORDS(RAM_WORDS),
        .WORD_WIDTH(16)
    ) ram (
        .clk(clk),
        .reset(mem_reset),
        .address_i(memory_addr[$clog2(RAM_WORDS)-1:0]),
        .wr_en_i(is_ram_address ? memory_we : 1'b0),
        .data_i(cpu_memory_out),
        .data_o(ram_data_out)
    );

    // PROM

    reg [16-1:0] prom [ROM_WORDS];

    assign instruction = prom[next_instruction_addr[$clog2(ROM_WORDS)-1:0]];

    // UART to fill the PROM

    UART #(
        .CLOCK_HZ(CLOCK_HZ),
        .BAUD(BAUD)
    ) uart(
        .reset(uart_reset),
        .clk(clk),
        .rx_i(uart_rx),
        .rx_data_o(rx_data),
        .rx_ready_o(rx_ready),
        .rx_ack_i(1'b1)
    );

    wire [7:0] rx_data;
    wire       rx_ready;

    reg [$clog2(ROM_WORDS)-1:0] uart_write_address;
    reg [0:0]                   uart_state;

    localparam  UART_RECEIVE_LOW    = 2'd0,
                UART_RECEIVE_HIGH   = 2'd1;

    always @(posedge clk) begin
        if (uart_reset) begin
            uart_write_address <= 0;
            uart_state <= UART_RECEIVE_LOW;
        end else begin
            case (uart_state)
                UART_RECEIVE_LOW: begin
                    if (rx_ready) begin
                        prom[uart_write_address][7:0] <= rx_data;
                        uart_state <= UART_RECEIVE_HIGH;
                    end
                end
                UART_RECEIVE_HIGH: begin
                    if (rx_ready) begin
                        prom[uart_write_address][15:8] <= rx_data;
                        uart_state <= UART_RECEIVE_LOW;

                        if (uart_write_address == ROM_WORDS - 1) begin
                            uart_write_address <= 0;
                        end else begin
                            uart_write_address <= uart_write_address + 1;
                        end
                    end
                end
            endcase
        end
    end

endmodule
