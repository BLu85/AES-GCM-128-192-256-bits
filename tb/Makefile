TOPLEVEL_LANG ?= vhdl
PWD=$(shell pwd)
SRCDIR=$(PWD)/../src
BUILDIR=$(PWD)/gen_rtl

SIM ?= ghdl

ifeq ($(SIM),icarus)
COMPILE_ARGS+=-I$(SRCDIR)/hdl/
else
GHDL_ARGS+=-fexplicit --ieee=synopsys
endif

ifeq ($(WAVE_ON),true)
PLUSARGS+=--wave=$(DUMP_FILENAME)
endif

#DUT
VHDL_SOURCES += $(SRCDIR)/aes_pkg.vhd
VHDL_SOURCES += $(SRCDIR)/aes_func.vhd
VHDL_SOURCES += $(SRCDIR)/aes_last_round.vhd
VHDL_SOURCES += $(BUILDIR)/aes_round.vhd
VHDL_SOURCES += $(BUILDIR)/aes_kexp.vhd
VHDL_SOURCES += $(BUILDIR)/aes_ecb.vhd
VHDL_SOURCES += $(SRCDIR)/gcm_pkg.vhd
VHDL_SOURCES += $(SRCDIR)/aes_icb.vhd
VHDL_SOURCES += $(SRCDIR)/gcm_gctr.vhd
VHDL_SOURCES += $(SRCDIR)/ghash_gfmul.vhd
VHDL_SOURCES += $(SRCDIR)/gcm_ghash.vhd
VHDL_SOURCES += $(SRCDIR)/aes_enc_dec_ctrl.vhd
VHDL_SOURCES += $(SRCDIR)/aes_gcm.vhd
VHDL_SOURCES += $(BUILDIR)/top_aes_gcm.vhd

TOPLEVEL = top_aes_gcm

GPI_IMPL := vpi

export TOPLEVEL_LANG
MODULE=gcm_test

include $(shell cocotb-config --makefiles)/Makefile.sim
