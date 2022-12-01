// IO_OUT - holds current LFSR state

@32767  // Replace with MD=D^M (1001000000011000)
M=M>>

// (-IO_OUT[0]) & Taps
// https://en.wikipedia.org/wiki/Linear-feedback_shift_register#Galois_LFSRs
@1
D=D&A
D=-D
@142    // Taps - 0x8E
D=D&A
