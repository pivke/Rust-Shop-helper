# Rust Shop Helper

Rust Shop Helper: A desktop application built with Python (PySide6, PyAutoGUI) to automate bulk buying from vending machines in the game Rust.

## Features

*   **Automated Buying:** Automatically clicks the buy button when available after entering a specified amount.
*   **Region Selection:** Select the specific area of the shop on your screen for the bot to monitor.
*   **Presets:** Save and load selected shop areas for quick setup.
*   **Status Display:** Shows the current state of the automation (Idle, Scanning, Buying, Paused, Error, etc.).
*   **Hotkey Control:**
    *   `F10`: Start/Stop Automation
    *   `F9`: Pause/Resume Automation
    *   `Esc`: Stop Automation
*   **Bundled Executable:** Can be built into a single `.exe` file for easy distribution (requires images/icon to be bundled).

## Requirements (for running from source)

*   Python 3.x
*   Dependencies listed in `requirements.txt` (PySide6, pyautogui, pynput)

## Installation (from source)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/pivke/Rust-Shop-helper.git
    cd Rust-Shop-helper
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the script:**
    ```bash
    python rust_buyer.py
    ```
2.  **Select Shop Area:** Click the "Select Shop Area (Live)" button. Your screen will dim; click and drag to draw a box around the vending machine interface, including the buy button and the item quantity input field. The selected area coordinates will be displayed.
3.  **Enter Amount:** Type the desired purchase quantity (e.g., 999) into the "Amount" field.
4.  **(Optional) Save Preset:** Enter a name in the "Name" field under "Area Preset Management" and click "Save Area" to save the current selection.
5.  **(Optional) Load Preset:** Click on a saved preset name under "Load Preset Area" to load a previously saved region.
6.  **Start Automation:** Press `F10` or click the "Start" button.
7.  **Control:**
    *   Use `F10` or the "Stop" button to stop.
    *   Use `F9` to pause and resume.
    *   Use `Esc` to stop.

## Building the Executable

If you want to create a standalone `.exe` file:

1.  **Install PyInstaller:**
    ```bash
    pip install pyinstaller
    ```
2.  **Run the build command (from the project directory):**
    ```bash
    python -m PyInstaller --windowed --onefile --icon=icon.ico --add-data "input_field_anchor.png;." --add-data "buy_button_green.png;." --add-data "buy_button_red.png;." --add-data "buy_button_gray.png;." --add-data "icon.ico;." rust_buyer.py
    ```
3.  The executable will be located in the `dist/` folder.

## Pre-built Release

Check the [Releases](https://github.com/pivke/Rust-Shop-helper/releases) page for pre-built `.exe` versions.

## Dependencies

*   [PySide6](https://pypi.org/project/PySide6/): For the graphical user interface.
*   [PyAutoGUI](https://pypi.org/project/PyAutoGUI/): For screen interaction (image finding, mouse clicks, typing).
*   [Pynput](https://pypi.org/project/pynput/): For global hotkey listening. 