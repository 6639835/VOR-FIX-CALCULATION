# VOR-FIX-CALCULATION
This project is a coordinate calculation tool built with Python’s Tkinter library. It allows users to calculate navigation coordinates based on either WAYPOINT (using VOR/DME/NDB data) or FIX information.

The Coordinate Calculator is a Python-based GUI application that assists with calculating navigation coordinates based on two modes:
- **WAYPOINT Mode:** Uses VOR/DME/NDB coordinates, magnetic bearing, distance, and magnetic declination to compute a target coordinate.
- **FIX Mode:** Uses FIX coordinates along with type, usage, runway encoding, and airport code to generate a specific output.

## Features

- **Two Calculation Modes:**
  - **WAYPOINT:** For calculating waypoint coordinates using VOR data.
  - **FIX:** For calculating FIX coordinates with additional parameters.
- **User-Friendly GUI:** Built with Tkinter, the application provides clear input labels, error validations, and results displayed in an output area.
- **Clipboard Functionality:** Easily copy the computed results for further use.
- **Clear and Reset Options:** Clear input fields via a dedicated button.
  
## Requirements

- Python 3.x (Recommended Python 3.7 or above)
- [Tkinter](https://docs.python.org/3/library/tkinter.html) (usually comes with Python)
- [geographiclib](https://pypi.org/project/geographiclib/)

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/6639835/VOR-FIX-CALCULATION.git
   ```

2. **Install dependencies:**

   If you have a `requirements.txt` file, run:

   ```bash
   pip install -r requirements.txt
   ```

   Otherwise, manually install geographiclib:

   ```bash
   pip install geographiclib
   ```

   In case Tkinter is missing, install it based on your operating system. For example, for Ubuntu:

   ```bash
   sudo apt-get install python3-tk
   ```

## Usage

1. **Run the application:**

   ```bash
   python VOR FIX CALCULATION.py
   ```

   *(Replace `VOR FIX CALCULATION.py` with the actual filename if different.)*

2. **Using the tool:**
   - Select the desired mode (WAYPOINT or FIX) from the mode selection dropdown.
   - Fill in the required parameters in the input fields.
   - Click the "Calculate" button to compute the results.
   - The output will be displayed in the result area, and you can copy the results to your clipboard using the provided button.

## Project Structure

- `VOR FIX CALCULATION.py`
  - The main Python file that contains the GUI code and all logic for coordinate calculation.
- Additional supporting files (if any) can be added to further modularize the project.

## Common Issues

1. **Tkinter Not Installed:**
   - If you encounter an error related to Tkinter, please ensure it is installed using your system's package manager.
   
2. **geographiclib Not Found:**
   - Install geographiclib with `pip install geographiclib` if it is not already installed.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

Feel free to open issues or submit pull requests if you have any suggestions or improvements.
