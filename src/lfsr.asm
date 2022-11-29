// IO_OUT   - holds current LFSR state
// R0       - holds loop count
// R1       - temp storage

(lblStart)
    @1          // Initial state
    D=A
    @16385      // IO_OUT
    M=D

(lblLoop)
    // Each instruction takes a cycle, and there are 10 instructions in the
    // busy loop, so we need 625 loops to wait a second, with a clock speed
    // of 6250 Hz.
    @R0
    D=M
    @624
    D=D-A
    @lblNext
    D;JEQ

    @R0
    M=M+1
    @lblLoop
    0;JMP

(lblNext)
    @R0
    M=0

    @16385  // IO_OUT
    D=M
    M=M>>
    @1
    D=D&A
    @lblXor
    D;JGT

    @lblLoop
    0;JMP

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
    0;JMP
