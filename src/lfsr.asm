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
    // busy loop, so we need 78.125 loops to wait a second, with a clock speed
    // of 625 Hz.
    @R0
    D=M
    @78
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

    // (-IO_OUT[0]) & Taps
    // https://en.wikipedia.org/wiki/Linear-feedback_shift_register#Galois_LFSRs
    @1
    D=D&A
    D=-D
    @142    // Taps - 0x8E
    D=D&A

    @16385  // IO_OUT
    @32767  // Replace with M=D^M (1001000000001000)

    @lblLoop
    M=0;JMP
