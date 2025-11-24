# VOR-FIX Coordinate Calculator

A Python tool for calculating aviation navigation waypoints and approach fixes using geodesic calculations based on VOR/DME/NDB data for X-Plane flight simulation.

## Features

- Calculate waypoint coordinates from VOR/DME/NDB stations
- Compute approach fixes for aviation navigation
- Geodesic calculations for accurate positioning
- User-friendly GUI interface built with Tkinter
- Support for magnetic declination corrections
- Import/export functionality for navigation data

## Requirements

- Python 3.8 or higher
- geographiclib >= 2.0

## Installation

### From Source

```bash
# Clone the repository
git clone <repository-url>
cd VOR-FIX-CALCULATION

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
pip install -e .
```

### Using pip

```bash
pip install -r requirements.txt
```

## Usage

### Running the Application

```bash
# If installed as a package
vor-fix-calculator

# Or run directly
python app.py
```

### As a Library

```python
from src.models import Coordinates, WaypointInput
from src.calculations import calculate_waypoint_coordinates

# Create a waypoint calculation
coords = Coordinates(latitude=37.6213, longitude=-122.3790)
waypoint = WaypointInput(
    coordinates=coords,
    identifier="WYPT1",
    magnetic_bearing=90.0,
    distance_nm=10.0,
    declination=15.0,
    airport_code="KSFO",
    vor_identifier="SFO"
)

# Calculate coordinates
result = calculate_waypoint_coordinates(waypoint)
print(f"Waypoint coordinates: {result.coordinates}")
```

## Project Structure

```
VOR-FIX-CALCULATION/
├── app.py                 # Main application entry point
├── requirements.txt       # Project dependencies
├── pyproject.toml        # Project metadata and build configuration
├── README.md             # This file
├── LICENSE               # Project license
├── src/                  # Source code package
│   ├── __init__.py       # Package initialization
│   ├── models.py         # Data models and classes
│   ├── calculations.py   # Core calculation functions
│   ├── constants.py      # Application constants
│   ├── file_operations.py # File I/O operations
│   ├── formatters.py     # Data formatting utilities
│   ├── ui.py             # GUI interface
│   └── validators.py     # Input validation
└── tests/                # Test suite
    └── __init__.py
```

## Development

### Running Tests

```bash
pytest
```

### Code Style

This project follows PEP 8 style guidelines. To check code style:

```bash
flake8 src tests
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Uses [GeographicLib](https://geographiclib.sourceforge.io/) for accurate geodesic calculations
- Designed for X-Plane flight simulation navigation data

## Support

For issues, questions, or contributions, please open an issue on the project repository.
