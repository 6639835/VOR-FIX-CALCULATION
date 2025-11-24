# Contributing to VOR-FIX Coordinate Calculator

Thank you for your interest in contributing to the VOR-FIX Coordinate Calculator! This document provides guidelines for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow:

- Be respectful and inclusive
- Welcome newcomers and encourage diverse perspectives
- Focus on constructive feedback
- Show empathy towards other community members

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment
4. Create a new branch for your changes

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip and virtualenv

### Installation

```bash
# Clone your fork
git clone https://github.com/yourusername/VOR-FIX-CALCULATION.git
cd VOR-FIX-CALCULATION

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install package in editable mode
pip install -e .
```

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/description` for new features
- `fix/description` for bug fixes
- `docs/description` for documentation updates
- `refactor/description` for code refactoring

### Commit Messages

Write clear, concise commit messages:
- Use the imperative mood ("Add feature" not "Added feature")
- Keep the first line under 50 characters
- Add a detailed description if needed after a blank line
- Reference issue numbers when applicable

Example:
```
Add magnetic declination validation

- Implement range checking for declination values
- Add error messages for invalid inputs
- Update tests to cover edge cases

Fixes #123
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_models.py

# Run specific test
pytest tests/test_models.py::TestCoordinates::test_coordinates_creation
```

### Writing Tests

- Write tests for all new functionality
- Maintain or improve code coverage
- Use descriptive test names
- Follow the Arrange-Act-Assert pattern
- Place tests in the `tests/` directory

Example:
```python
def test_calculate_waypoint_coordinates():
    """Test waypoint coordinate calculation with valid inputs."""
    # Arrange
    coords = Coordinates(latitude=37.6213, longitude=-122.3790)
    waypoint = WaypointInput(...)

    # Act
    result = calculate_waypoint_coordinates(waypoint)

    # Assert
    assert result.coordinates.latitude == pytest.approx(expected_lat)
```

## Code Style

### Python Style Guide

This project follows [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:

- Maximum line length: 100 characters
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes

### Code Formatting

We use automated tools to maintain code quality:

```bash
# Format code with black
black src tests

# Sort imports with isort
isort src tests

# Check style with flake8
flake8 src tests

# Type checking with mypy
mypy src
```

### Docstring Format

Use Google-style docstrings:

```python
def calculate_bearing(start: Coordinates, end: Coordinates) -> float:
    """
    Calculate the bearing between two coordinates.

    Args:
        start: Starting coordinates
        end: Ending coordinates

    Returns:
        Bearing in degrees (0-360)

    Raises:
        ValueError: If coordinates are invalid
    """
    pass
```

## Submitting Changes

### Pull Request Process

1. Update documentation for any changed functionality
2. Add tests for new features or bug fixes
3. Ensure all tests pass
4. Update the README.md if needed
5. Push your changes to your fork
6. Submit a pull request to the main repository

### Pull Request Checklist

- [ ] Code follows the project style guidelines
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] Commit messages are clear and descriptive
- [ ] No merge conflicts with main branch

### Pull Request Description

Include in your PR description:
- Summary of changes
- Motivation and context
- Related issue numbers
- Screenshots (if applicable)
- Testing performed

## Review Process

- Maintainers will review your PR as soon as possible
- Address any requested changes
- Once approved, a maintainer will merge your PR

## Questions?

If you have questions or need help:
- Open an issue on GitHub
- Tag it with the "question" label
- Provide as much context as possible

Thank you for contributing to VOR-FIX Coordinate Calculator!
