.DEFAULT_GOAL := help

.PHONY: help clean clean-output clean-cache

help:
	@echo "make clean         Remove generated outputs, caches, and build artifacts"
	@echo "make clean-output  Remove generated outputs only"
	@echo "make clean-cache   Remove Python caches and build artifacts only"
	@echo "make -n clean      Preview cleanup commands without deleting files"

clean: clean-output clean-cache

clean-output:
	rm -rf output

clean-cache:
	rm -rf build dist .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage .coverage.*
	find . -type d \( -name .git -o -name .venv -o -name venv \) -prune -o \
		-type d -name __pycache__ -exec rm -rf {} +
