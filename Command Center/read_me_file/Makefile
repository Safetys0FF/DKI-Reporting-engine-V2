PYTHON ?= python
VENV_DIR := .venv

ifeq ($(OS),Windows_NT)
    VENV_PYTHON := $(VENV_DIR)/Scripts/python.exe
    VENV_PIP := $(VENV_DIR)/Scripts/pip.exe
else
    VENV_PYTHON := $(VENV_DIR)/bin/python
    VENV_PIP := $(VENV_DIR)/bin/pip
endif

REQ_FILE := The\ War\ Room/Processors/requirements.txt
BUS_MAIN := Command\ Center/Data\ Bus/Bus\ Core\ Design/main_application.py
WARDEN_MAIN := The\ Warden/warden_main.py
MARSHALL_MAIN := The\ Marshall/Gateway/gateway_controller.py
DEBRIEF_MAIN := Command\ Center/Mission\ Debrief/Debrief/README/mission_debrief_manager.py

.DEFAULT_GOAL := help

.PHONY: help venv install lint format test run-bus run-warden run-marshall run-debrief clean

help:
	@echo "Available targets:"
	@echo "  make install       Create venv and install dependencies"
	@echo "  make lint          Run formatting checks (black --check)"
	@echo "  make format        Apply code formatting"
	@echo "  make test          Execute pytest suites"
	@echo "  make run-bus       Launch Data Bus runtime"
	@echo "  make run-warden    Launch Warden controller"
	@echo "  make run-marshall  Launch Marshall gateway controller"
	@echo "  make run-debrief   Launch Mission Debrief manager"
	@echo "  make clean         Remove virtual environment and caches"

venv:
	@"$(PYTHON)" - <<'PY'
import os, sys, venv
venv_dir = r"$(VENV_DIR)"
if not os.path.exists(venv_dir):
    builder = venv.EnvBuilder(with_pip=True)
    builder.create(venv_dir)
PY
	@echo "Virtual environment ready at $(VENV_DIR)"

install: venv
	@"$(VENV_PYTHON)" -m pip install --upgrade pip setuptools wheel
	@"$(VENV_PYTHON)" -m pip install -r "$(REQ_FILE)"

lint:
	@"$(VENV_PYTHON)" -m black --check "Command Center" "The Warden" "The Marshall" "Command Center/Mission Debrief" || true

format:
	@"$(VENV_PYTHON)" -m black "Command Center" "The Warden" "The Marshall" "Command Center/Mission Debrief"

test:
	@"$(VENV_PYTHON)" -m pytest

run-bus:
	@"$(VENV_PYTHON)" "$(BUS_MAIN)"

run-warden:
	@"$(VENV_PYTHON)" "$(WARDEN_MAIN)"

run-marshall:
	@"$(VENV_PYTHON)" "$(MARSHALL_MAIN)"

run-debrief:
	@"$(VENV_PYTHON)" "$(DEBRIEF_MAIN)"

clean:
	@"$(PYTHON)" - <<'PY'
import os, shutil
venv_dir = r"$(VENV_DIR)"
if os.path.exists(venv_dir):
    shutil.rmtree(venv_dir)
for root, dirs, files in os.walk('.', topdown=False):
    for name in dirs:
        if name == '__pycache__':
            shutil.rmtree(os.path.join(root, name), ignore_errors=True)
PY
	@echo "Clean complete"
