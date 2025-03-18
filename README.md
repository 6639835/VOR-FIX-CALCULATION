# VOR-FIX-CALCULATION: Your Ultimate Aviation Coordinate Tool! ✈️ 🌍

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)  [![Tkinter](https://img.shields.io/badge/Tkinter-GUI-brightgreen.svg)](https://docs.python.org/3/library/tkinter.html)  [![geographiclib](https://img.shields.io/badge/geographiclib-Dependency-yellow.svg)](https://pypi.org/project/geographiclib/)  [![License: MIT](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)  [![GitHub Stars](https://img.shields.io/github/stars/6639835/VOR-FIX-CALCULATION?style=social)](https://github.com/6639835/VOR-FIX-CALCULATION)

Calculate aviation navigation coordinates with ease! This project provides a powerful and user-friendly coordinate calculation tool built with Python and Tkinter. Whether you're a flight simmer, aviation enthusiast, or developer, this tool will help you determine accurate waypoint and FIX locations.

**Unlock the Power of Precise Navigation!**

---

## 🌟 Key Features

*   **Dual Calculation Modes:**
    *   **WAYPOINT Mode:** Calculate waypoint coordinates using VOR/DME/NDB data, magnetic bearing, distance, and magnetic declination.
    *   **FIX Mode:** Determine FIX coordinates with detailed parameters like type, usage, runway encoding, and airport code.
*   **Intuitive GUI:** A clean and easy-to-use graphical interface built with Tkinter. No command-line wizardry needed!
*   **Error Validation:** Prevents incorrect calculations by validating your inputs.
*   **Clipboard Integration:** Copy calculated results directly to your clipboard for seamless integration with other applications.
*   **One-Click Reset:** Quickly clear input fields with the "Clear" button.
*   **Cross-Platform Compatibility:** Runs on any operating system that supports Python and Tkinter (Windows, macOS, Linux).
*   **Open Source:** Licensed under the MIT License, allowing for free use, modification, and distribution.

---

## 💡 How It Works

The Coordinate Calculator is a Python-based GUI application that assists with calculating navigation coordinates using two distinct modes:

*   **WAYPOINT Mode:** Uses VOR/DME/NDB coordinates, magnetic bearing, distance, and magnetic declination to compute a target coordinate. This is ideal for determining the location of a new waypoint based on existing navigation aids.
*   **FIX Mode:** Uses FIX coordinates along with type, usage, runway encoding, and airport code to generate a specific output string. This is useful for creating or modifying FIX definitions in navigation databases.

---

## ✅ Requirements

*   Python 3.x (Recommended Python 3.7 or above) - Download from [https://www.python.org/downloads/](https://www.python.org/downloads/)
*   Tkinter (usually comes pre-installed with Python)
*   [geographiclib](https://pypi.org/project/geographiclib/) - For accurate geographic calculations.

---

## 🛠️ Installation

1.  **Clone the Repository:**

    ```bash
    git clone https://github.com/6639835/VOR-FIX-CALCULATION.git
    cd VOR-FIX-CALCULATION
    ```

2.  **Install Dependencies:**

    If you have a `requirements.txt` file:

    ```bash
    pip install -r requirements.txt
    ```

    Otherwise, manually install geographiclib:

    ```bash
    pip install geographiclib
    ```

    If Tkinter is missing (rare), install it using your system's package manager. For example, on Ubuntu:

    ```bash
    sudo apt-get install python3-tk
    ```

---

## 🚀 Usage

1.  **Run the Application:**

    ```bash
    python "VOR FIX CALCULATION.py"
    ```

    (Make sure the filename matches your local copy.)

2.  **Using the Tool:**

    *   Select the desired mode (WAYPOINT or FIX) from the dropdown menu.
    *   Enter the required parameters into the input fields.  The GUI provides helpful labels.
    *   Click the "Calculate" button.
    *   The results will appear in the output area.  Use the "Copy to Clipboard" button to easily transfer the results to other applications.

---

## 📁 Project Structure

*   `VOR FIX CALCULATION.py`: The main Python file containing the GUI code and calculation logic.
*   `LICENSE`: The MIT License file.

---

## 🐛 Common Issues & Solutions

1.  **Tkinter Not Installed:**

    *   Error message related to `_tkinter` or `TkVersion`?  Install Tkinter using your system's package manager (e.g., `sudo apt-get install python3-tk` on Ubuntu).

2.  **geographiclib Not Found:**

    *   Error message indicating that `geographiclib` is missing? Run `pip install geographiclib`.

---

## 🤝 Contributing

Contributions are welcome! If you find a bug, have a feature request, or want to contribute code, please open an issue or submit a pull request.

[![RepoBeats](https://repobeats.axiom.co/api/embed/99ff823a402aefae830d6336bca425e24b8df416.svg)](https://repobeats.axiom.co/)

---

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

**Happy Calculating!  Let's make aviation navigation easier together!**
