BANK ?= banks/example.bank.json
ASSESSMENT ?= quiz-example-001
FORMAT ?= all
REFERENCE_DIR ?= build/reference

.DEFAULT_GOAL := help

.PHONY: help validate list build review reference md typst latex qti pdf doctor test clean

help:
	@echo "Quizbank uses its container for every normal command."
	@echo ""
	@echo "  make validate"
	@echo "  make list"
	@echo "  make build ASSESSMENT=quiz-example-001 FORMAT=all"
	@echo "  make review"
	@echo "  make reference"
	@echo "  make pdf ASSESSMENT=quiz-example-001"
	@echo "  make doctor"

validate:
	./quizbank validate --bank $(BANK)

list:
	./quizbank list --bank $(BANK)

build:
	./quizbank build $(ASSESSMENT) --bank $(BANK) --format $(FORMAT)

review:
	./quizbank review --bank $(BANK)

reference:
	./quizbank reference --bank $(BANK) --output-dir $(REFERENCE_DIR)

md:
	./quizbank build $(ASSESSMENT) --bank $(BANK) --format markdown

typst:
	./quizbank build $(ASSESSMENT) --bank $(BANK) --format typst

latex:
	./quizbank build $(ASSESSMENT) --bank $(BANK) --format latex

qti:
	./quizbank build $(ASSESSMENT) --bank $(BANK) --format qti

pdf:
	./quizbank build $(ASSESSMENT) --bank $(BANK) --format pdf

doctor:
	./quizbank doctor

test:
	docker compose run --rm --entrypoint python quizbank -m pytest -q

clean:
	rm -rf build/*
