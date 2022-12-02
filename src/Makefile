SIM ?= icarus
TOPLEVEL_LANG ?= verilog

ifneq ($(GATES),yes)
# Normal simulation
VERILOG_SOURCES +=				\
	$(PWD)/tb.v					\
	$(PWD)/mbikovitsky_top.v	\
	$(PWD)/lfsr.v				\
	$(PWD)/seven_segment.v		\
	$(PWD)/uart.v				\
	$(PWD)/ram.v				\
	$(PWD)/alu.v				\
	$(PWD)/extend_alu.v			\
	$(PWD)/cpu.v
else
# Gate level simulation requires some extra setup
COMPILE_ARGS    += -DGL_TEST
COMPILE_ARGS    += -DFUNCTIONAL
COMPILE_ARGS    += -DUSE_POWER_PINS
COMPILE_ARGS    += -DSIM
COMPILE_ARGS    += -DUNIT_DELAY=\#1
VERILOG_SOURCES += $(PDK_ROOT)/sky130B/libs.ref/sky130_fd_sc_hd/verilog/primitives.v
VERILOG_SOURCES += $(PDK_ROOT)/sky130B/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v

VERILOG_SOURCES +=					\
	$(PWD)/tb.v						\
	$(PWD)/mbikovitsky_top.gl.v
endif

TOPLEVEL = tb

MODULE = test

ifdef CLOCK_HZ
COMPILE_ARGS += -DCLOCK_HZ=${CLOCK_HZ}
endif

ifdef SIM_CLOCK_HZ
PLUSARGS += +SIM_CLOCK_HZ=${SIM_CLOCK_HZ}
endif

ifdef SIM_BAUD
PLUSARGS += +SIM_BAUD=${SIM_BAUD}
endif

ifdef SIM_PROM_SIZE
PLUSARGS += +SIM_PROM_SIZE=${SIM_PROM_SIZE}
endif

ifeq ($(GATES),yes)
PLUSARGS += +GATE_LEVEL
endif

include $(shell cocotb-config --makefiles)/Makefile.sim
