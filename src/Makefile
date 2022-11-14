SIM ?= icarus
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES +=				\
	$(PWD)/tb.v					\
	$(PWD)/mbikovitsky_top.v	\
	$(PWD)/seven_segment.v

TOPLEVEL = tb

MODULE = test

include $(shell cocotb-config --makefiles)/Makefile.sim
