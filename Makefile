# Makefile for Quizbank
# Run `make validate` before committing changes.

PYTHON := python3
VALIDATOR := tools/validate_items.py
SCHEMA := schemas/quiz-item.schema.json

# Default target
.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  validate     Validate all YAML items against $(SCHEMA)"
	@echo "  clean        Remove build artifacts"
	@echo "  tree         Show repo tree"
	@echo "  build-qti    (stub) Build Canvas QTI packages"
	@echo "  build-paper  (stub) Build paper quizzes (Typst/LaTeX/Markdown)"

.PHONY: validate
validate:
	@$(PYTHON) $(VALIDATOR) qbank/**/*.yaml

.PHONY: clean
clean:
	rm -rf build/*

.PHONY: tree
tree:
	@tree -a -I '.git|.venv|__pycache__'

# Future stubs
.PHONY: build-qti
build-qti:
	@echo "[stub] Would export to Canvas QTI here."

.PHONY: build-paper
build-paper:
	@echo "[stub] Would export to Typst/LaTeX/Markdown here."
