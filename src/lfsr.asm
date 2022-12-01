// IO_OUT   - holds current LFSR state

(lblStart)
    @1          // Initial state
    D=A
    @16385      // IO_OUT
    M=D

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

    @lblNext
    0;JMP
