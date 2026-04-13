export PYTHONPATH := src

# Before virtual env
INITAL_PYTHON = python3

# Virtual env
VENV_DIR = venv
VENV_PYTHON = $(VENV_DIR)/bin/python
VENV_PIP = $(VENV_DIR)/bin/pip
VENV_PYLINT = $(VENV_DIR)/bin/pylint
VENV_MYPY = $(VENV_DIR)/bin/mypy
VENV_BLACK = $(VENV_DIR)/bin/black
VENV_PYTEST = $(VENV_DIR)/bin/pytest

# Folders
BUILD_DIR = build
SRC_DIR = src
TEST_DIR = test
UNIT_TEST_DIR = $(TEST_DIR)/unit
E2E_TEST_DIR = $(TEST_DIR)/e2e

clean:
	rm -rf $(VENV_DIR) $(BUILD_DIR) __pycache__ .pytest_cache .mypy_cache dist symbology_comparator.egg-info
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

venv:
	$(INITAL_PYTHON) -m venv $(VENV_DIR)

install: venv
	$(VENV_PIP) install -r requirements-dev.txt

lint: black-formatter pylint mypy

black-formatter:
	@echo "Running black formatter check"
	$(VENV_BLACK) -t py311 --check $(SRC_DIR)/ $(TEST_DIR)/

black-formatter-fix:
	@echo "Running black formatter"
	$(VENV_BLACK) -t py311 $(SRC_DIR)/ $(TEST_DIR)/

pylint:
	@echo "Running pylint on test code"
	$(VENV_PYLINT) $(UNIT_TEST_DIR) --output-format=colorized --disable=duplicate-code,too-many-public-methods,too-many-locals,broad-exception-caught,unused-argument,bare-except,protected-access,unbalanced-tuple-unpacking,redefined-outer-name,consider-using-with --fail-on E
	@echo "Running pylint on source"
	$(VENV_PYLINT) $(SRC_DIR) --output-format=colorized --fail-under 10 --fail-on E

mypy:
	@echo "Running mypy"
	$(VENV_MYPY) --explicit-package-bases --strict $(SRC_DIR)/ $(TEST_DIR)/

test: test-unit test-e2e

test-unit:
	rm -rf $(BUILD_DIR)/unit-test $(BUILD_DIR)/reports/unit-test
	mkdir -p $(BUILD_DIR)/reports/unit-test
	$(VENV_PYTEST) $(UNIT_TEST_DIR)/ --cov=$(SRC_DIR) --cov-config .coveragerc-unit-tests --cov-report term-missing --cov-report html --cov-report xml --cov-report json

test-e2e:
	rm -rf $(BUILD_DIR)/e2e-test $(BUILD_DIR)/reports/e2e-test
	mkdir -p $(BUILD_DIR)/reports/e2e-test
	$(VENV_PYTEST) $(E2E_TEST_DIR)/ --cov=$(SRC_DIR) --cov-config .coveragerc-e2e-tests --cov-report term-missing --cov-report html --cov-report xml --cov-report json

all: clean install lint test-unit

report-2024:
	$(VENV_PYTHON) -m contabilidade report 2024 --output relatorio-dirpf-2024.md

report-2025:
	$(VENV_PYTHON) -m contabilidade report 2025 --output relatorio-dirpf-2025.md

import-2024:
	$(VENV_PYTHON) -m contabilidade import 2024 \
		--file private-data/relatorio-consolidado-anual-2024.xlsx \
		--movimentacao private-data/movimentacao-2024.xlsx

import-2025:
	$(VENV_PYTHON) -m contabilidade import 2025 \
		--file private-data/relatorio-consolidado-anual-2025.xlsx \
		--movimentacao private-data/movimentacao-2025.xlsx