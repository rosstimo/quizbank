# Makefile for Quizbank with sane verbosity

PYTHON := python3

# Tools
VALIDATOR := tools/validate_items.py
BUILD_MD  := tools/build_md.py
BUILD_TYP := tools/build_typst.py
BUILD_QTI := tools/build_qti.py

# Inputs
QUIZ ?= quizzes/quiz-example.yaml
QNAME := $(basename $(notdir $(QUIZ)))

# Outputs
OUT_MD    := build/markdown/$(QNAME).md
OUT_TYPST := build/typst/$(QNAME).typ
OUT_PDF   := build/typst/$(QNAME).pdf
OUT_QTI   := build/qti/$(QNAME)-qti12.zip

# ----- Verbosity handling -----------------------------------------------
# Accept VERBOSE=1 or V=1, or pseudo-goals: 'verbose' or 'v'
VERBOSE ?= $(V)

ifneq (,$(filter verbose v --verbose -v,$(MAKECMDGOALS)))
  VERBOSE := 1
  # Strip the pseudo-goals so make doesn’t try to build them
  MAKECMDGOALS := $(filter-out verbose v --verbose -v,$(MAKECMDGOALS))
endif

# Q prefixes each command; empty when VERBOSE=1
ifeq ($(VERBOSE),1)
  Q :=
else
  Q := @
endif

# Helper: print message only when verbose
define say
	@if [ "$(VERBOSE)" = "1" ]; then printf '%s\n' "$(1)"; fi
endef

# ------------------------------------------------------------------------

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Targets:"
	@echo "  validate         Validate all YAML items"
	@echo "  md               Build Markdown quiz -> $(OUT_MD)"
	@echo "  typst            Build Typst source  -> $(OUT_TYPST)"
	@echo "  typst-pdf        Compile Typst PDF   -> $(OUT_PDF)"
	@echo "  qti              Build QTI 1.2 zip   -> $(OUT_QTI)"
	@echo "  all              Validate + md + typst + qti"
	@echo "  clean            Remove build artifacts"
	@echo ""
	@echo "Flags: VERBOSE=1 or V=1, or add pseudo-goal 'verbose' or 'v'."
	@echo "Examples:"
	@echo "  make md QUIZ=quizzes/quiz-example.yaml"
	@echo "  make verbose qti QUIZ=quizzes/quiz-example.yaml"
	@echo "  make all V=1"

# ---------------- Core ----------------

.PHONY: validate
validate:
	$(call say,Validating items with $(VALIDATOR))
	$(Q)$(PYTHON) $(VALIDATOR) qbank/**/*.yaml

.PHONY: md
md: $(OUT_MD)
$(OUT_MD): $(BUILD_MD) $(QUIZ)
	$(call say,Building Markdown -> $@)
	$(Q)mkdir -p $(dir $@)
	$(Q)$(PYTHON) $(BUILD_MD) $(QUIZ) --out $@

.PHONY: typst
typst: $(OUT_TYPST)
$(OUT_TYPST): $(BUILD_TYP) $(QUIZ)
	$(call say,Building Typst -> $@)
	$(Q)mkdir -p $(dir $@)
	$(Q)$(PYTHON) $(BUILD_TYP) $(QUIZ) --out $@

.PHONY: typst-pdf
typst-pdf: $(OUT_PDF)
$(OUT_PDF): $(OUT_TYPST)
	$(call say,Compiling Typst PDF -> $@)
	$(Q)command -v typst >/dev/null || { echo "typst not found in PATH"; exit 2; }
	$(Q)typst compile $(OUT_TYPST) $(OUT_PDF)

.PHONY: qti
qti: $(OUT_QTI)
$(OUT_QTI): $(BUILD_QTI) $(QUIZ)
	$(call say,Building QTI -> $@)
	$(Q)mkdir -p $(dir $@)
	$(Q)$(PYTHON) $(BUILD_QTI) $(QUIZ) --out $@

.PHONY: all
all: validate md typst qti

.PHONY: clean
clean:
	$(call say,Cleaning build/)
	$(Q)rm -rf build/*

.PHONY: tree
tree:
	$(Q)tree -a -I '.git|.venv|__pycache__' || true
