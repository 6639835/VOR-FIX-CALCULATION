# VOR FIX Coordinate Calculator

A professional aviation coordinate calculation application for determining waypoint and FIX coordinates using VOR, DME, and NDB navigation aids.

## Features

### Core Functionality
- **Waypoint Calculations**: Calculate coordinates from VOR/DME/NDB stations using bearing and distance
- **FIX Calculations**: Calculate FIX coordinates with DME intersection calculations
- **High-Precision Geodesic**: Ultra-precise calculations using WGS84 ellipsoid model
- **Magnetic Declination**: Automatic or manual magnetic declination handling
- **File Search**: Search navigation data files for station coordinates
- **History Management**: Track and reuse previous calculations

### Navigation Support
- **VOR (VHF Omnidirectional Range)**: Standard VOR navigation
- **DME (Distance Measuring Equipment)**: Precision distance measurements
- **NDB (Non-Directional Beacon)**: Traditional beacon navigation
- **Mixed Operations**: VOR/DME and NDB/DME combinations

### Calculation Modes
- **Magnetic/True Bearings**: Support for both magnetic and true bearings
- **Auto Declination**: Automatic magnetic declination calculation using pygeomag
- **Intersection Calculations**: Radial-distance intersection finding
- **Multiple Distance References**: DME or FIX-based distance calculations

## Installation

### Prerequisites
- Python 3.7+
- tkinter (usually included with Python)
- Required Python packages:

```bash
pip install geographiclib pygeomag
```

### Optional Dependencies
- **pygeomag**: For automatic magnetic declination calculation (recommended)

## Usage

### Starting the Application
```bash
python vor_fix_calculation.py
```

### File Setup
1. Select NAV and FIX data files using the "Browse" buttons
2. Files should be in standard X-Plane format with space-separated values

### Waypoint Mode
1. Select "WAYPOINT" mode
2. Either:
   - Enter a VOR/DME/NDB identifier and click "Search Coordinates"
   - Manually enter coordinates in "Lat Lon" format
3. Choose bearing mode (Magnetic/True)
4. Enter bearing in degrees (0-359)
5. Enter distance in nautical miles
6. Fill in airport code and VOR identifier
7. Click "Calculate Waypoint"

### FIX Mode
1. Select "FIX" mode
2. Enter FIX identifier or coordinates
3. For DME calculations:
   - Enter DME identifier or coordinates
   - Set bearing and distance
   - Choose distance reference (DME/FIX)
   - Click "Calculate Intersection"
4. Fill in FIX details (type, usage, runway, airport)
5. Click "Calculate FIX"

## Architecture

### Improved Code Structure
The application has been completely refactored from a monolithic ~1400-line class into a modular, maintainable architecture:

#### Core Services
- **`MagneticDeclinationService`**: Handles magnetic declination calculations
- **`CoordinateCalculator`**: High-precision geodesic calculations
- **`NavigationDataService`**: File reading and identifier searching
- **`InputValidator`**: Robust input validation with clear error messages

#### UI Components
- **`FileSelectionFrame`**: File browsing and selection
- **`BaseCalculationFrame`**: Common functionality for calculation frames
- **`WaypointCalculationFrame`**: Waypoint-specific UI and logic
- **`FixCalculationFrame`**: FIX-specific UI and logic

#### Data Models
- **`Coordinates`**: Type-safe coordinate representation with validation
- **`CalculationResult`**: Structured calculation results
- **Enums**: Type-safe constants for modes, file types, etc.

### Key Improvements

#### 1. **Separation of Concerns**
- Business logic separated from UI code
- Service classes handle specific responsibilities
- Clean interfaces between components

#### 2. **Type Safety**
- Comprehensive type hints throughout the codebase
- Dataclasses for structured data
- Enums for constants and modes

#### 3. **Error Handling**
- Robust input validation with specific error messages
- Graceful handling of file operations
- Clear user feedback for all error conditions

#### 4. **Code Reusability**
- Base classes for common functionality
- Shared services across UI components
- Consistent patterns throughout the application

#### 5. **Maintainability**
- Smaller, focused classes and methods
- Clear naming conventions
- Comprehensive documentation
- Reduced code duplication

## Technical Details

### Precision
- **Distance Tolerance**: 1 meter precision for intersection calculations
- **Angular Tolerance**: 0.0001 degrees (about 0.36 arcseconds)
- **Coordinate Precision**: 9 decimal places (sub-meter accuracy)
- **Iterative Refinement**: Up to 200 iterations for complex calculations

### Geodesic Calculations
- Uses GeographicLib for maximum precision
- WGS84 ellipsoid model
- Multi-step calculations for very long distances
- Verification and error checking for all calculations

### File Format Support
- **NAV Files**: X-Plane navigation data format
- **FIX Files**: X-Plane fix data format
- Automatic parsing and coordinate extraction
- Duplicate handling with user selection

## Output Formats

### Waypoint Output
- Short distance (≤26.5 NM): `D{bearing}{radius_letter} {airport_code}`
- Long distance (>26.5 NM): `{vor_id}{distance} {airport_code}`
- Includes operation codes for departure/arrival/approach

### FIX Output
- Format: `{usage_code}{fix_code}{runway:02d} {airport_code} {operation_code}`
- Supports all standard FIX types and usage codes

## History and Workflow

### Calculation History
- Automatic tracking of all calculations
- Sortable history view with timestamps
- Copy/reuse previous calculations
- Clear history functionality

### Workflow Features
- Auto-search coordinates from identifiers
- Auto-update magnetic declination
- Copy results to clipboard
- Clear form functionality

## Dependencies

### Required
- **geographiclib**: High-precision geodesic calculations
- **tkinter**: GUI framework (standard library)

### Optional
- **pygeomag**: Automatic magnetic declination calculation
  - Falls back to manual entry if not available
  - Supports both high and standard resolution models

## License

This software is provided as-is for aviation planning and educational purposes. Verify all calculations independently before use in actual navigation.

## Contributing

When contributing to this project:
1. Follow the established architecture patterns
2. Add type hints to all new code
3. Include comprehensive error handling
4. Write clear docstrings
5. Maintain the separation of concerns

## Changelog

### Version 2.0 (Refactored)
- **Complete Architecture Overhaul**: Modular design with service classes
- **Type Safety**: Full type hints and dataclass models
- **Improved Error Handling**: Comprehensive validation and user feedback
- **Enhanced UI**: Better organization and user experience
- **Code Quality**: Reduced complexity and improved maintainability
- **New Features**: Enhanced history management and workflow improvements
