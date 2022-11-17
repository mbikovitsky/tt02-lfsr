SIM ?= icarus
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES +=				\
	$(PWD)/tb.v					\
	$(PWD)/mbikovitsky_top.v	\
	$(PWD)/seven_segment.v

TOPLEVEL = tb

MODULE = test

ifdef CLOCK_HZ
COMPILE_ARGS = -DCLOCK_HZ=${CLOCK_HZ}
endif

ifdef SIM_CLOCK_HZ
PLUSARGS = +SIM_CLOCK_HZ=${SIM_CLOCK_HZ}
endif

include $(shell cocotb-config --makefiles)/Makefile.sim
