#!/bin/bash
# Helper script to clean python cache and run pytest suites

set -e

# Change directory to project root
cd "$(dirname "$0")/.."

echo "Cleaning python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.py[co]" -delete

# Detect virtual env pytest
PYTEST_BIN="pytest"
if [ -f ".venv/bin/pytest" ]; then
    PYTEST_BIN=".venv/bin/pytest"
elif [ -f "venv/bin/pytest" ]; then
    PYTEST_BIN="venv/bin/pytest"
fi

echo "Running pytest test suite using $PYTEST_BIN..."
$PYTEST_BIN -v

