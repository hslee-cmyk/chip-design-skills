#============================================
# AMS Verification Makefile
# 아날로그 모델 교체 지원
#============================================

#--------------------------------------------
# Analog Model Selection
# BEHAV   : Behavioral (빠름, 기능 검증)
# WREAL   : Wreal (중간, 타이밍 검증)
# SPECTRE : Spectre (느림, 정밀 검증)
#--------------------------------------------
ANALOG_MODEL ?= BEHAV

#--------------------------------------------
# Tool Selection
#--------------------------------------------
TOOL ?= xcelium

#--------------------------------------------
# Directories
#--------------------------------------------
RTL_DIR     := ../rtl
ANALOG_DIR  := ../analog
TB_DIR      := ../tb
MODEL_DIR   := ../models

#--------------------------------------------
# Files
#--------------------------------------------
RTL_FILES   := $(wildcard $(RTL_DIR)/*.v) $(wildcard $(RTL_DIR)/*.sv)
TB_FILES    := $(wildcard $(TB_DIR)/*.sv)

# 아날로그 모델 파일
ANALOG_BEHAV  := $(ANALOG_DIR)/analog_top_behav.sv
ANALOG_WREAL  := $(ANALOG_DIR)/analog_top_wreal.sv
ANALOG_SPECTRE:= $(ANALOG_DIR)/analog_top_spectre.vams

#--------------------------------------------
# Model-specific settings
#--------------------------------------------
ifeq ($(ANALOG_MODEL), SPECTRE)
    MODEL_DEF   := +define+AMS_SPECTRE
    MODEL_FILES := $(ANALOG_SPECTRE)
    AMS_OPTS    := -ams -analogcontrol ams_control.scs
    SIM_TIMEOUT := 100ms
else ifeq ($(ANALOG_MODEL), WREAL)
    MODEL_DEF   := +define+AMS_WREAL
    MODEL_FILES := $(ANALOG_WREAL)
    AMS_OPTS    :=
    SIM_TIMEOUT := 10ms
else  # BEHAV
    MODEL_DEF   := +define+AMS_BEHAV
    MODEL_FILES := $(ANALOG_BEHAV)
    AMS_OPTS    :=
    SIM_TIMEOUT := 1ms
endif

#--------------------------------------------
# Compile Options
#--------------------------------------------
XMVLOG_OPTS := -sv \
               +incdir+$(TB_DIR) \
               -timescale 1ns/1ps \
               $(MODEL_DEF)

XMELAB_OPTS := -access +rwc \
               $(AMS_OPTS)

#--------------------------------------------
# Test Settings
#--------------------------------------------
TEST       ?= chip_sanity_test
SEED       ?= random
VERBOSITY  ?= UVM_MEDIUM

XMSIM_OPTS := +UVM_TESTNAME=$(TEST) \
              +UVM_VERBOSITY=$(VERBOSITY)

#--------------------------------------------
# Targets
#--------------------------------------------
.PHONY: all compile elab sim clean help
.PHONY: sim_behav sim_wreal sim_spectre
.PHONY: regress_daily regress_weekly regress_tapeout

all: compile elab sim

#--------------------------------------------
# Compile
#--------------------------------------------
compile:
	@echo "=== Compiling with $(ANALOG_MODEL) model ==="
	xmvlog $(XMVLOG_OPTS) \
		$(RTL_FILES) \
		$(TB_FILES) \
		$(MODEL_FILES)

#--------------------------------------------
# Elaborate
#--------------------------------------------
elab:
	@echo "=== Elaborating ==="
	xmelab $(XMELAB_OPTS) \
		-top hdl_top -top hvl_top \
		-snapshot chip_tb

#--------------------------------------------
# Simulate
#--------------------------------------------
sim:
	@echo "=== Running $(ANALOG_MODEL) simulation ==="
	xmsim chip_tb $(XMSIM_OPTS) \
		-input run_sim.tcl

#--------------------------------------------
# Convenience targets for each model
#--------------------------------------------
sim_behav:
	$(MAKE) clean compile elab sim ANALOG_MODEL=BEHAV

sim_wreal:
	$(MAKE) clean compile elab sim ANALOG_MODEL=WREAL

sim_spectre:
	$(MAKE) clean compile elab sim ANALOG_MODEL=SPECTRE

#--------------------------------------------
# Regression Strategies
#--------------------------------------------
TESTS_ALL := chip_sanity_test \
             chip_adc_test \
             chip_dac_test \
             chip_pll_test \
             chip_random_test

TESTS_CRITICAL := chip_adc_accuracy_test \
                  chip_pll_jitter_test

# 일일 회귀: Behavioral (빠름, 모든 테스트)
regress_daily:
	@echo "=== Daily Regression (Behavioral) ==="
	@for test in $(TESTS_ALL); do \
		$(MAKE) sim_behav TEST=$$test; \
	done

# 주간 회귀: Wreal (중간, 모든 테스트)
regress_weekly:
	@echo "=== Weekly Regression (Wreal) ==="
	@for test in $(TESTS_ALL); do \
		$(MAKE) sim_wreal TEST=$$test; \
	done

# 테잎아웃 회귀: Spectre (느림, Critical 테스트만)
regress_tapeout:
	@echo "=== Tapeout Regression (Spectre) ==="
	@for test in $(TESTS_CRITICAL); do \
		$(MAKE) sim_spectre TEST=$$test; \
	done

#--------------------------------------------
# Clean
#--------------------------------------------
clean:
	rm -rf xcelium.d INCA_libs *.shm *.log *.key
	rm -rf waves.vcd waves.shm

#--------------------------------------------
# Help
#--------------------------------------------
help:
	@echo "=== AMS Verification Makefile ==="
	@echo ""
	@echo "Usage:"
	@echo "  make sim               - Run with default model (BEHAV)"
	@echo "  make sim_behav         - Run with Behavioral model"
	@echo "  make sim_wreal         - Run with Wreal model"
	@echo "  make sim_spectre       - Run with Spectre model"
	@echo ""
	@echo "  make regress_daily     - Daily regression (BEHAV, all tests)"
	@echo "  make regress_weekly    - Weekly regression (WREAL, all tests)"
	@echo "  make regress_tapeout   - Tapeout regression (SPECTRE, critical)"
	@echo ""
	@echo "Variables:"
	@echo "  ANALOG_MODEL=BEHAV|WREAL|SPECTRE (default: BEHAV)"
	@echo "  TEST=<test_name>       (default: chip_sanity_test)"
	@echo "  SEED=<number>|random   (default: random)"
	@echo ""
	@echo "Model Comparison:"
	@echo "  BEHAV   : ~1min/test,   functional verification"
	@echo "  WREAL   : ~10min/test,  timing verification"
	@echo "  SPECTRE : ~1000min/test, analog accuracy"
