// IO_OUT   - holds current LFSR state
// R0       - holds loop count
// R1       - temp storage

(lblStart)
    @1          // Initial state
    D=A
    @16385      // IO_OUT
    M=D

(lblLoop)
    // Each instruction takes a cycle, and there are 8 instructions in the
    // busy loop, so we need 781.25 loops to wait a second, with a clock speed
    // of 6250 Hz.
    @R0
    D=M
    @781
    D=D-A
    @lblNext
    D;JEQ

    @lblLoop    // Since lblLoop is at address 4, and we have only 2 RAM slots,
                // this wraps around to 0 :)
    M=M+1;JMP

(lblNext)
    @16385  // IO_OUT
    D=M
    M=M>>
    @1
    D=D&A
    @lblXor
    D;JGT

    @lblLoop
    M=0;JMP

(lblXor)
    // R1 = ~(IO_OUT & Taps)
    @16385  // IO_OUT
    D=M
    @142    // Taps - 0x8E
    D=D&A
    D=!D
    @R1
    M=D

    // IO_OUT = (IO_OUT | Taps) & R1
    @16385  // IO_OUT
    D=M
    @142    // Taps - 0x8E
    D=D|A
    @R1
    D=D&M
    @16385  // IO_OUT
    M=D

    @lblLoop
    M=0;JMP
