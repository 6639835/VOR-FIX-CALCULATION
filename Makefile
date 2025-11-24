.PHONY: help install install-dev test test-cov lint format clean build run

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install package dependencies
	pip install -r requirements.txt

install-dev:  ## Install development dependencies
	pip install -r requirements-dev.txt
	pip install -e .

test:  ## Run tests
	pytest tests/

test-cov:  ## Run tests with coverage report
	pytest --cov=src --cov-report=term-missing --cov-report=html tests/

lint:  ## Run code quality checks
	flake8 src tests
	mypy src
	pylint src

format:  ## Format code with black and isort
	black src tests
	isort src tests

format-check:  ## Check code formatting without making changes
	black --check src tests
	isort --check-only src tests

clean:  ## Clean build artifacts and cache files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type f -name '*.egg' -delete

build:  ## Build distribution packages
	python -m build

run:  ## Run the application
	python app.py

check: format-check lint test  ## Run all checks (format, lint, test)

all: clean install-dev format lint test  ## Clean, install, format, lint, and test
