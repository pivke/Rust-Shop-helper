import sys
import time
import threading
import os
import json
import pyautogui
from pynput import keyboard # Only need keyboard now
# from pynput import mouse, keyboard # Remove mouse
# import tkinter as tk
# from tkinter import messagebox, simpledialog
# from tkinter import ttk 

# --- PySide6 Imports ---
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QGroupBox, QMessageBox, QInputDialog,
    QScrollArea, QFrame, QSizePolicy, QSpacerItem, QLayout # Added QLayout
)
from PySide6.QtGui import (
    QMouseEvent, QPainter, QPen, QBrush, QColor, QScreen, QFont,
    QGuiApplication, QIcon # Import QIcon
)
from PySide6.QtCore import (
    Qt, QThread, Signal, Slot, QObject, QRect, QPoint, QTimer, QSize, QMargins, # Added QSize, QMargins
    QSettings, QByteArray # Import QSettings & QByteArray
)

# --- Helper Function for Bundled Resources ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        print(f"Running bundled, MEIPASS: {base_path}") # Debug line
    except Exception:
        # Not running in PyInstaller bundle, use script directory
        base_path = os.path.abspath(os.path.dirname(__file__))
        print(f"Running from script, base_path: {base_path}") # Debug line

    return os.path.join(base_path, relative_path)
# ---------------------------------------------

# --- Constants --- (Keep existing constants for now)
PRESET_FILE = "presets_area.json"
INPUT_ANCHOR_IMG = resource_path("input_field_anchor.png")
BUY_GREEN_IMG = resource_path("buy_button_green.png")
BUY_RED_IMG = resource_path("buy_button_red.png")
BUY_GRAY_IMG = resource_path("buy_button_gray.png")
# VENDING_IMG = "vending.png" # Removed as code using it is deleted
CONFIDENCE_LEVEL = 0.8
BUTTON_CONFIDENCE = 0.80
VENDING_CONFIDENCE = 0.9
INPUT_CLICK_OFFSET_X = 30
INPUT_CLICK_OFFSET_Y = 5
RED_BUTTON_TIMEOUT = 5.0
LOOP_DELAY = 0.15
POST_BUY_DELAY = 0.5

# Settings constants
ORG_NAME = "PivkeSoftware" # Or your preferred name
APP_NAME = "RustBuyer"

# --- Globals --- (Will be managed within classes where possible)
stop_automation_flag = False
automation_running = False
paused_flag = False
selected_search_region = None # Tuple (x, y, w, h)
presets = {}
active_preset_name = None
# Global reference to main window might be needed for callbacks/threads
main_window_ref = None

# Hotkey constants remain
start_stop_hotkey = {keyboard.Key.f10}
pause_resume_hotkey = {keyboard.Key.f9}

# --- Prettier Stylesheet (QSS) ---
DARK_STYLE_SHEET = """
QWidget {
    font-family: "Inter", "Segoe UI", sans-serif; /* Prioritize Inter */
    font-size: 14px;
    background-color: #1e1f23; /* Base dark background */
    color: #dddddd; /* Light text */
}

QMainWindow {
    background-color: #1e1f23;
}

QGroupBox {
    background-color: #2a2b2f; /* Slightly lighter dark for groupbox */
    border: 1px solid #3b3c41; /* Subtle border */
    border-radius: 10px;
    margin-top: 16px;
    padding: 12px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top;
    padding: 0 6px; /* Reduced horizontal padding */
    padding-top: 5px; /* Add top padding to lower the text */
    font-weight: 600; /* Semi-bold title */
    font-size: 14px;
    color: #aaaaaa; /* Gray title */
}

QPushButton {
    background-color: #3a3b3f; /* Dark gray button */
    border: 1px solid #4a4b50;
    border-radius: 8px;
    color: #eeeeee; /* Lighter text */
    padding: 8px 14px;
    font-weight: 500; /* Medium weight */
}

QPushButton:hover {
    background-color: #44454a; /* Slightly lighter hover */
    border-color: #5a5b60;
}

QPushButton:pressed {
    background-color: #353639; /* Slightly darker pressed */
    border-color: #5c5d62;
}

QPushButton:disabled {
    background-color: #2a2b2f; /* Dimmer background for disabled */
    border: 1px solid #3b3c41;
    color: #777777; /* Dimmer text color */
}

QLineEdit {
    background-color: #2b2c30; /* Input background */
    color: #e0e0e0;
    border: 1px solid #3d3e42; /* Input border */
    border-radius: 6px;
    padding: 6px 8px;
}

QLineEdit:focus {
    border: 1px solid #666666; /* Slightly lighter border on focus */
    background-color: #2e2f33; /* Slightly lighter bg on focus */
}

QLabel {
    color: #bbbbbb; /* Default label color */
    padding: 2px 0;
    background-color: transparent;
}

/* Style for Status Label - Adapt to new theme */
QLabel#StatusLabel {
    background-color: #2b2c30; /* Match input background */
    color: #bbbbbb; /* Match label color */
    border: 1px solid #3d3e42; /* Match input border */
    border-radius: 6px; /* Match input radius */
    padding: 6px 8px; /* Match input padding */
    font-weight: normal;
    alignment: AlignCenter;
}
QLabel#StatusLabel[paused="true"] {
    color: #ffcc66; /* Yellow for Paused */
    font-weight: bold;
}

/* Style for Preset Buttons - Adapt to new theme */
QPushButton#PresetButton {
    background-color: #2f3034; /* Slightly different gray than regular buttons */
    border: 1px solid #404145;
    border-radius: 6px; /* Match input radius */
    color: #cccccc;
    padding: 5px 10px; /* Smaller preset button padding */
    text-align: left;
    font-weight: normal;
}
QPushButton#PresetButton:hover {
    background-color: #3a3b3f;
    border-color: #505155;
    color: #dddddd;
}
QPushButton#PresetButton:pressed {
    background-color: #2a2b2f;
    color: #eeeeee;
}
QPushButton#PresetButton[active="true"] {
    background-color: #4a4b50; /* More prominent gray for active */
    border: 1px solid #666666;
    color: #ffffff; /* White text for active */
    font-weight: bold;
}

/* Scrollbar Styling - Use theme's definition */
QScrollArea {
    border: none;
    background-color: #2a2b2f; /* Match GroupBox background */
}
QWidget#PresetScrollWidget {
    background-color: #2a2b2f; /* Match GroupBox background */
}
QScrollBar:vertical {
    background: transparent; /* Use theme's transparent track */
    width: 10px;
    margin: 0px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #4a4b50; /* Scrollbar handle from theme */
    border-radius: 5px;
    min-height: 25px;
}
QScrollBar::handle:vertical:hover {
    background: #5b5c61; /* Handle hover from theme */
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
    height: 0px;
    width: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

/* Card style - Adapt to new theme */
QWidget#CardWidget {
    background-color: #2a2b2f; /* Match GroupBox */
    border: 1px solid #3b3c41; /* Match GroupBox */
    border-radius: 10px; /* Match GroupBox */
}

/* Add Checkbox/Radio/ComboBox from new theme if needed */
QCheckBox, QRadioButton {
    spacing: 6px;
    color: #dddddd;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 14px;
    height: 14px;
    border-radius: 7px;
    border: 1px solid #666666;
    background-color: #2a2b2f;
}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #666666;
    border: 1px solid #888888;
}
QComboBox {
    background-color: #2b2c30;
    border: 1px solid #3d3e42;
    border-radius: 6px;
    padding: 6px;
    color: #dddddd;
    selection-background-color: #3f4044; /* For dropdown selection */
}
QComboBox::drop-down {
    border: none;
    background: transparent;
}
QComboBox::down-arrow {
    image: url(none); /* Consider adding a custom arrow later if needed */
}
QComboBox QAbstractItemView {
    background-color: #2a2b2f;
    border: 1px solid #3d3e42;
    selection-background-color: #3f4044;
    color: #dddddd;
    outline: 0px; /* Remove focus outline in dropdown */
}
"""

# --- Preset Loading/Saving --- (Keep for now, connect later)
def load_presets():
    global presets
    if os.path.exists(PRESET_FILE):
        try:
            with open(PRESET_FILE, 'r') as f:
                loaded_data = json.load(f)
                if isinstance(loaded_data, dict):
                    presets = loaded_data
                    print(f"Loaded {len(presets)} area presets from {PRESET_FILE}")
                else:
                     print(f"Error: {PRESET_FILE} does not contain a valid preset dictionary.")
                     presets = {}
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {PRESET_FILE}. File corrupt/empty?")
            presets = {}
        except Exception as e:
            print(f"An error occurred loading presets: {e}")
            presets = {}
    else:
        print("Preset file not found. Starting empty.")
        presets = {}

def save_presets():
    global presets
    try:
        with open(PRESET_FILE, 'w') as f:
            json.dump(presets, f, indent=4)
        print(f"Saved {len(presets)} area presets to {PRESET_FILE}")
    except Exception as e:
        print(f"Error saving presets: {e}")
        # Show message box via main window later if needed
        if main_window_ref:
             QMessageBox.critical(main_window_ref, "Save Error", f"Could not save presets: {e}")

# --- Automation Worker --- (Adapted for Qt Signals)
class AutomationWorker(QObject):
    # Signals to emit back to the GUI thread
    status_updated = Signal(str, bool) # status_text, is_paused
    finished = Signal(str) # final_status
    error_occurred = Signal(str)
    request_stop = Signal() # Worker asking main thread to stop fully

    def __init__(self, search_region, amount):
        super().__init__()
        self.search_region = search_region
        self.amount_to_type = amount
        self._is_running = True
        self._is_paused = False # Internal pause state for worker

    @Slot()
    def run(self):
        global stop_automation_flag, paused_flag # Still using global flags for control from main

        print(f"Automation started in worker thread. Search region: {self.search_region}")
        red_button_visible_since = None
        last_state_scan_time = time.time()
        paused_emitted_flag = False # Track if paused status was emitted

        while self._is_running:
            if stop_automation_flag:
                print("Stop flag detected in worker loop.")
                self._is_running = False
                break

            current_time = time.time()
            time_since_last_scan = current_time - last_state_scan_time
            if time_since_last_scan < LOOP_DELAY:
                # Use QThread.msleep for better Qt integration if needed,
                # but time.sleep is often fine for background tasks unless precision is critical.
                time.sleep(LOOP_DELAY - time_since_last_scan)
            last_state_scan_time = time.time()

            # --- Handle Pausing ---
            # Check both internal _is_paused (from toggle_pause) and global paused_flag (from F9)
            while self._is_paused or paused_flag:
                if not self._is_running or stop_automation_flag: break # Allow stopping while paused
                # Emit paused status only once per pause period
                if not paused_emitted_flag:
                    self.status_updated.emit("Paused", True)
                    paused_emitted_flag = True
                time.sleep(0.1) # Reduce CPU usage while paused
                last_state_scan_time = time.time() # Prevent large delay buildup
            if not self._is_running or stop_automation_flag: break
            # Reset paused emitted flag if we were paused
            if paused_emitted_flag:
                self.status_updated.emit("Scanning...", False) # Status after resume
                paused_emitted_flag = False

            if not self._is_running: break # Check again after pause loop

            try:
                # --- Green Button Check ---
                self.status_updated.emit("Scanning...", False)
                buy_pos = self._locate_image_safe(BUY_GREEN_IMG, region=self.search_region, confidence=BUTTON_CONFIDENCE)
                if buy_pos:
                    print("Action: Green Found.")
                    red_button_visible_since = None
                    self.status_updated.emit("Action: Buying", False)
                    
                    anchor_pos = self._locate_image_safe(INPUT_ANCHOR_IMG, region=self.search_region, confidence=CONFIDENCE_LEVEL, grayscale=True)
                    if not anchor_pos: raise Exception(f"Anchor '{INPUT_ANCHOR_IMG}' lost in region {self.search_region}")
                    if not self._is_running: break

                    input_click_x = anchor_pos.x + INPUT_CLICK_OFFSET_X; input_click_y = anchor_pos.y + INPUT_CLICK_OFFSET_Y
                    print(f"Clicking input -> ({input_click_x:.0f}, {input_click_y:.0f})...")
                    pyautogui.click(input_click_x, input_click_y); time.sleep(0.05)
                    if stop_automation_flag: raise Exception("Stopped input click")
                    if not self._is_running: break

                    print(f"Typing '{self.amount_to_type}'...")
                    pyautogui.write(self.amount_to_type, interval=0.02); time.sleep(0.1)
                    if stop_automation_flag: raise Exception("Stopped typing")
                    if not self._is_running: break

                    print(f"Clicking Buy -> ({buy_pos.x:.0f}, {buy_pos.y:.0f})...")
                    pyautogui.click(buy_pos.x, buy_pos.y);
                    time.sleep(POST_BUY_DELAY)
                    last_state_scan_time = time.time()
                    if stop_automation_flag: raise Exception("Stopped post buy")
                    if not self._is_running: break
                    continue # Go to next loop iteration immediately after buying

                if not self._is_running: break
                # --- Red Button Check ---
                is_red = self._locate_image_safe(BUY_RED_IMG, region=self.search_region, confidence=BUTTON_CONFIDENCE)
                if is_red:
                    print("State: Red Found.")
                    if red_button_visible_since is None:
                        print("Red timer started."); red_button_visible_since = current_time
                    elapsed_red_time = current_time - red_button_visible_since
                    if elapsed_red_time >= RED_BUTTON_TIMEOUT:
                        timeout_msg = f"Red button visible for {elapsed_red_time:.1f}s. Stopping."; print(timeout_msg)
                        # Request stop via signal
                        self.request_stop.emit() # Ask main thread to initiate stop
                        self._is_running = False # Stop worker loop too
                        break
                    else:
                        status_red = f"State: Red ({elapsed_red_time:.1f}s)";
                        self.status_updated.emit(status_red, False)
                    continue # Skip gray check if red is found
                else: # Red not found, reset timer
                    red_button_visible_since = None

                if not self._is_running: break
                # --- Gray Button Check ---
                is_gray = self._locate_image_safe(BUY_GRAY_IMG, region=self.search_region, confidence=BUTTON_CONFIDENCE)
                if is_gray:
                    print("State: Gray Found (Busy). Waiting...")
                    self.status_updated.emit("State: Busy (Gray Btn)", False)
                    continue

                if not self._is_running: break
                # --- Button State Unknown ---
                print("Warning: Button state unknown (Not Green/Red/Gray). Retrying...")
                self.status_updated.emit("State: Unknown Button", False)

            except Exception as e:
                if not self._is_running: break # Don't report errors if we were already stopping
                current_error_str = str(e); print(f"Automation error: {current_error_str}")
                self.error_occurred.emit(current_error_str[:100]) # Emit truncated error
                if "lost" in current_error_str.lower(): # Example: stop on critical errors
                    print("Essential element lost. Stopping.")
                    self.request_stop.emit() # Ask main thread to initiate stop
                    self._is_running = False # Stop worker loop
                time.sleep(1)
                # No break here unless self._is_running becomes false

        # --- Loop End ---
        # Determine final status based on whether the loop exited naturally or via stop flag
        final_status = "Stopped" if stop_automation_flag else "Finished"
        print(f"Automation {final_status} in worker.");
        self.finished.emit(final_status)

    def _locate_image_safe(self, image_path, **kwargs):
        """Wrapper for pyautogui locate functions to handle exceptions during shutdown."""
        # image_path should now be the absolute path from resource_path
        if not self._is_running: return None
        try:
            # Using locateCenterOnScreen as it's simpler
            return pyautogui.locateCenterOnScreen(image_path, **kwargs)
        except pyautogui.ImageNotFoundException:
            return None
        except Exception as e:
            # Avoid spamming logs if error is due to script stopping
            if self._is_running:
                # Don't print the full absolute path here, might be long/revealing
                print(f"Error locating image [...] in worker: {e}") 
            return None

    @Slot()
    def stop(self):
        """Slot called by the main thread to signal the worker loop to stop."""
        print("Worker stop() slot called.")
        self._is_running = False

    @Slot()
    def toggle_pause(self):
        """Slot called by the main thread to pause/resume the worker's actions."""
        self._is_paused = not self._is_paused
        print(f"Worker internal pause toggled to: {self._is_paused}")
        # Status update will come from run() loop via signals

# --- Region Selection Overlay (Qt Version) ---
class SelectionOverlay(QWidget):
    # Signal emitting the selected QRect(x, y, width, height)
    region_selected = Signal(QRect)
    selection_cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # Get primary screen geometry more robustly
        primary_screen = QApplication.primaryScreen()
        if not primary_screen:
            print("Error: Could not get primary screen.")
            QTimer.singleShot(0, self.close) # Close immediately if screen info fails
            return
        screen_geometry = primary_screen.geometry()
        self.setGeometry(screen_geometry)

        # Make window frameless, transparent, and stay on top
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        # Set background to be fully transparent initially
        self.setAttribute(Qt.WA_TranslucentBackground)
        # Set strong focus to capture key events like Esc
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.CrossCursor)

        self.start_point = QPoint()
        self.end_point = QPoint()
        self.selecting = False
        self.mouse_pressed = False

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            # Use event.globalPosition() again
            self.start_point = event.globalPosition().toPoint() 
            self.end_point = self.start_point
            self.selecting = True
            self.mouse_pressed = True
            self.update() # Trigger paint event
            print(f"Selection started (Qt Global Logical): {self.start_point}")

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.selecting and self.mouse_pressed:
            # Use event.globalPosition() again
            self.end_point = event.globalPosition().toPoint() 
            self.update() # Trigger paint event

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self.selecting:
            self.selecting = False
            self.mouse_pressed = False
            # Use the stored global logical coords (as QPoints) for the final rect
            selection_rect = QRect(self.start_point, self.end_point).normalized()
            print(f"Selection ended (Qt Global Logical): {selection_rect}")
            if selection_rect.width() < 20 or selection_rect.height() < 20:
                print("Region too small (Qt).")
                if main_window_ref: # Show message via main window ref
                     QMessageBox.warning(main_window_ref, "Region Too Small", "Selected area is too small.")
                self.selection_cancelled.emit() # Signal cancellation
                self.close()
            else:
                # Emit the QRect based on global logical coords
                self.region_selected.emit(selection_rect) 
                self.close()
        # Don't automatically close on right-click release, wait for key press or left release

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(80, 80, 80, 100))

        if self.selecting:
            # Map the global logical start/end points back to local for drawing
            local_start = self.mapFromGlobal(self.start_point) 
            local_end = self.mapFromGlobal(self.end_point)
            selection_rect_local = QRect(local_start, local_end).normalized()
            pen = QPen(QColor("#00ff00"), 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(selection_rect_local)

    def keyPressEvent(self, event):
        # Allow cancelling selection with Escape key
        if event.key() == Qt.Key_Escape:
            print("Selection cancelled via Escape key.")
            self.selecting = False # Stop selection drawing
            self.selection_cancelled.emit()
            self.close()
        else:
            super().keyPressEvent(event) # Pass other keys along

# --- Feedback Widget (Qt Version) ---
class FeedbackWidget(QWidget):
    def __init__(self, rect, parent=None): # rect should be global screen coordinates QRect
        super().__init__(parent)
        self.setGeometry(rect)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # No setStyleSheet needed

        # Close after original delay
        QTimer.singleShot(600, self.close) # Back to 600ms

    def paintEvent(self, event):
        painter = QPainter(self)
        # Fill the widget area with transparent bright green
        # Alpha 51 is approx 20% opacity
        painter.fillRect(self.rect(), QColor(0, 255, 0, 51)) # Green with Alpha

# --- Scan Area Visualizer Widget ---
class ScanAreaVisualizer(QWidget):
    """A persistent widget to show the automation scan area."""
    def __init__(self, rect, parent=None): # rect should be global logical screen coordinates QRect
        super().__init__(parent)
        self.setGeometry(rect)
        # Frameless, always on top, doesn't steal focus (Tool), transparent background
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose) # Ensure deletion when closed

    def paintEvent(self, event):
        painter = QPainter(self)
        # Draw only the border - bright red, slightly thicker
        pen = QPen(QColor(255, 0, 0, 200), 3, Qt.SolidLine) # Red border, 3px thick
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush) # No fill
        # Draw rect slightly inset so border is fully visible within geometry
        painter.drawRect(self.rect().adjusted(1, 1, -1, -1)) 

    def update_geometry(self, rect):
        """Allows updating the position/size if needed."""
        self.setGeometry(rect)
        self.update() # Trigger repaint

# --- FlowLayout Class (from Qt example) ---
class FlowLayout(QLayout):
    def __init__(self, parent=None):
        super().__init__(parent)

        if parent is not None:
            self.setContentsMargins(QMargins(0, 0, 0, 0)) # No margins inside the layout itself

        self._item_list = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]

        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)

        return None

    def expandingDirections(self):
        return Qt.Orientation(0) # Not expanding

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._do_layout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())

        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect, test_only):
        m = self.contentsMargins()
        effective_rect = rect.adjusted(+m.left(), +m.top(), -m.right(), -m.bottom())
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0
        spacing = self.spacing() # Use layout's spacing property

        # Adjust spacing for PushButtons like the example does
        style_spacing_x = 0
        style_spacing_y = 0
        if len(self._item_list) > 0:
            # Get style spacing if possible
            try:
                style = self._item_list[0].widget().style()
                style_spacing_x = style.layoutSpacing(
                    QSizePolicy.ControlType.PushButton, QSizePolicy.ControlType.PushButton,
                    Qt.Orientation.Horizontal)
                style_spacing_y = style.layoutSpacing(
                    QSizePolicy.ControlType.PushButton, QSizePolicy.ControlType.PushButton,
                    Qt.Orientation.Vertical)
            except AttributeError: # Handle if first item isn't a widget or has no style
                pass

        # Combined spacing
        h_space = spacing + style_spacing_x
        v_space = spacing + style_spacing_y

        for item in self._item_list:
            wid = item.widget()
            next_x = x + item.sizeHint().width() + h_space
            if next_x - h_space > effective_rect.right() and line_height > 0: # Wrap condition
                x = effective_rect.x()
                y = y + line_height + v_space
                next_x = x + item.sizeHint().width() + h_space
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - effective_rect.y()

# --- Main Window Class ---
class MainWindow(QMainWindow):
    # --- Signals for Cross-Thread Communication ---
    # Worker thread control
    request_worker_stop = Signal()
    request_worker_pause_toggle = Signal()
    # Hotkey events (emitted from listener thread)
    f10_hotkey_pressed = Signal()
    f9_hotkey_pressed = Signal()
    esc_hotkey_pressed = Signal()
    # --------------------------------------------

    def __init__(self):
        super().__init__()
        # --- Use Absolute Path for Icon (via resource_path) ---
        # script_dir = os.path.dirname(os.path.abspath(__file__))
        # icon_path = os.path.join(script_dir, "icon.ico") # Old path
        icon_path = resource_path("icon.ico") # Use helper function
        self.setWindowIcon(QIcon(icon_path)) 
        # ------------------------------------
        global main_window_ref
        main_window_ref = self # Store global reference

        self.setWindowTitle("Rust Shop Helper")
        # Don't set initial geometry here, let restoreGeometry handle it
        # self.setGeometry(100, 100, 550, 450) # x, y, width, height
        self.setMinimumSize(550, 480) # Set a minimum size
        # self.resize(600, 500) # Initial size
        self.setStyleSheet(DARK_STYLE_SHEET)
        
        # --- Add the Always On Top flag ---
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        # ----------------------------------

        # Automation thread management
        self.automation_thread = None
        self.automation_worker = None

        # Selection overlay reference
        self.selection_overlay = None
        self.feedback_widget = None
        # Add reference for persistent visualizer
        self.scan_visualizer = None 

        # Pynput listener instance
        self.pynput_listener_instance = None

        self._setup_ui()
        self._connect_signals()
        self.load_presets() # Load presets data
        self.update_preset_buttons() # Initial population
        self._update_ui_state() # Set initial UI state
        
        # --- Restore Geometry ---
        self._restore_window_geometry()
        # ------------------------
        
        # --- Connect Hotkey Signals ---
        self.f10_hotkey_pressed.connect(self.toggle_automation)
        self.f9_hotkey_pressed.connect(self.toggle_pause_resume)
        self.esc_hotkey_pressed.connect(self.stop_automation)
        # -----------------------------

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        # Main layout is now HORIZONTAL
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10) # Spacing between cards
        main_layout.setContentsMargins(10, 10, 10, 10) # Margins around cards

        # --- Card 1: Left Side (Area, Settings, Control) --- 
        left_card_widget = QWidget()
        left_card_widget.setObjectName("CardWidget") # Assign object name for styling
        left_layout = QVBoxLayout(left_card_widget) 
        left_layout.setContentsMargins(8, 8, 8, 8) # Padding inside card
        left_layout.setSpacing(10) # Spacing between groups in card
        main_layout.addWidget(left_card_widget, 1) # Allow left card to stretch width slightly more if needed

        # Group 1.1: Region Selection
        region_group = QGroupBox("Shop Search Area")
        region_layout = QVBoxLayout(region_group)
        region_layout.setContentsMargins(5, 15, 5, 5) 
        self.select_region_button = QPushButton("Select Shop Area (Live)")
        self.region_label = QLabel("Shop Area: Not Set")
        region_layout.addWidget(self.select_region_button)
        region_layout.addWidget(self.region_label)
        left_layout.addWidget(region_group)

        # Group 1.2: Settings
        settings_group = QGroupBox("Buy Settings")
        settings_layout = QGridLayout(settings_group)
        settings_layout.setContentsMargins(5, 15, 5, 5) 
        settings_layout.addWidget(QLabel("Amount:"), 0, 0) 
        self.amount_input = QLineEdit("999")
        settings_layout.addWidget(self.amount_input, 0, 1)
        settings_layout.setColumnStretch(1, 1) 
        settings_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding), 1, 0, 1, 2)
        # Remove fixed width policy for settings group
        # settings_group.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred) 
        left_layout.addWidget(settings_group)
        
        # Group 1.3: Control (Moved to Left Card)
        control_group = QGroupBox("Control (F10, F9, Esc)")
        control_layout = QVBoxLayout(control_group)
        control_layout.setContentsMargins(5, 15, 5, 5) 
        self.start_stop_button = QPushButton("Start")
        self.status_label = QLabel("Status: Idle")
        self.status_label.setObjectName("StatusLabel") 
        control_layout.addWidget(self.start_stop_button)
        control_layout.addWidget(self.status_label)
        left_layout.addWidget(control_group)

        # Add stretch to push left card content up if window is tall
        left_layout.addStretch(1) 

        # --- Card 2: Right Side (Presets) --- 
        right_card_widget = QWidget()
        right_card_widget.setObjectName("CardWidget") # Assign object name for styling
        right_layout = QVBoxLayout(right_card_widget)
        right_layout.setContentsMargins(8, 8, 8, 8) # Padding inside card
        right_layout.setSpacing(10) # Spacing between groups in card
        main_layout.addWidget(right_card_widget, 1) # Allow cards to share space

        # Group 2.1: Preset Management
        preset_manage_group = QGroupBox("Area Preset Management")
        preset_manage_layout = QGridLayout(preset_manage_group)
        preset_manage_layout.setContentsMargins(5, 15, 5, 5) 
        preset_manage_layout.addWidget(QLabel("Name:"), 0, 0)
        self.preset_name_input = QLineEdit()
        preset_manage_layout.addWidget(self.preset_name_input, 0, 1) 
        preset_button_layout = QHBoxLayout() 
        self.save_preset_button = QPushButton("Save Area")
        self.delete_preset_button = QPushButton("Delete")
        preset_button_layout.addWidget(self.save_preset_button)
        preset_button_layout.addWidget(self.delete_preset_button)
        preset_manage_layout.addLayout(preset_button_layout, 1, 0, 1, 2) 
        preset_manage_layout.setColumnStretch(1, 1) 
        right_layout.addWidget(preset_manage_group)

        # Group 2.2: Preset List
        preset_list_group = QGroupBox("Load Preset Area")
        preset_list_layout = QVBoxLayout(preset_list_group) 
        preset_list_layout.setContentsMargins(4, 15, 4, 4) 
        self.preset_scroll_area = QScrollArea()
        self.preset_scroll_area.setWidgetResizable(True)
        self.preset_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.preset_scroll_widget = QWidget() 
        self.preset_scroll_widget.setObjectName("PresetScrollWidget") 
        # Use FlowLayout instead of QVBoxLayout
        self.preset_buttons_layout = FlowLayout(self.preset_scroll_widget)
        self.preset_buttons_layout.setSpacing(6) # Spacing between buttons
        self.preset_buttons_layout.setContentsMargins(2,2,2,2) 
        self.preset_scroll_area.setWidget(self.preset_scroll_widget)
        preset_list_layout.addWidget(self.preset_scroll_area)
        # Allow preset list to stretch vertically within the right card
        right_layout.addWidget(preset_list_group, 1) 

        # --- Remove Old Layout Structure --- 
        # The old main_layout, middle_widget, left_frame, right_frame logic is replaced
        
    def _connect_signals(self):
        self.select_region_button.clicked.connect(self.start_region_selection)
        self.start_stop_button.clicked.connect(self.toggle_automation)
        self.save_preset_button.clicked.connect(self.save_preset_action)
        self.delete_preset_button.clicked.connect(self.delete_preset_action)
        # Preset load buttons are connected dynamically in update_preset_buttons

    @Slot()
    def start_region_selection(self):
        print("Starting region selection...")
        # Hide main window immediately
        self.hide()
        # Use QTimer to ensure hide event is processed before creating overlay
        QTimer.singleShot(50, self._create_and_show_overlay)

    def _create_and_show_overlay(self):
        # Check if overlay already exists (e.g., user clicked twice quickly)
        if self.selection_overlay is not None:
            self.selection_overlay.activateWindow() # Bring existing one to front
            return
            
        self.selection_overlay = SelectionOverlay()
        # Connect signals from the overlay to slots in the main window
        self.selection_overlay.region_selected.connect(self.handle_region_selected)
        self.selection_overlay.selection_cancelled.connect(self.handle_selection_cancelled)
        # Ensure overlay is deleted when closed to release resources
        self.selection_overlay.setAttribute(Qt.WA_DeleteOnClose)
        self.selection_overlay.show()
        self.selection_overlay.activateWindow() # Ensure it gets focus for key events
        self.selection_overlay.setFocus()


    @Slot(QRect) # QRect received contains GLOBAL LOGICAL coordinates
    def handle_region_selected(self, rect): 
        global selected_search_region, active_preset_name
        # print(f"Region selected signal received (Global Logical): {rect}") # REMOVE DEBUG
        
        # --- Convert Global Logical Coords to Primary Monitor Relative PHYSICAL Coords ---
        primary_screen = QGuiApplication.primaryScreen()
        if not primary_screen:
             print("CRITICAL ERROR: Cannot get primary screen geometry!")
             self.selection_overlay = None
             self.show(); self.raise_(); self.activateWindow()
             return
        primary_geometry = primary_screen.geometry()
        pixel_ratio = primary_screen.devicePixelRatio() or 1.0 # Ensure DPR is at least 1.0
        print(f"Primary Screen Geometry: {primary_geometry}, DPR: {pixel_ratio}")
        
        # Calculate coords relative to primary monitor's top-left AND scale by DPR
        physical_x = int((rect.x() - primary_geometry.x()) * pixel_ratio)
        physical_y = int((rect.y() - primary_geometry.y()) * pixel_ratio)
        physical_width = int(rect.width() * pixel_ratio)  
        physical_height = int(rect.height() * pixel_ratio)
        # -----------------------------------------------------------------------------
        
        # Store the PRIMARY-RELATIVE PHYSICAL coordinates
        selected_search_region = (physical_x, physical_y, physical_width, physical_height)
        print(f"Stored Primary-Relative PHYSICAL Region for PyAutoGUI: {selected_search_region}")
        
        self.update_region_label() # Update label (shows physical relative coords now)
        # Use the original GLOBAL LOGICAL rect for the feedback flash widget position 
        self.show_feedback_flash(rect) 
        active_preset_name = None 
        self.update_preset_buttons() 
        self.update_preset_buttons() # Update buttons to remove highlight
        self.selection_overlay = None # Clear reference, it was deleted on close
        # Show main window again
        self.show()
        self.raise_() # Bring to front
        self.activateWindow()
        # Explicitly update UI state after selection
        self._update_ui_state()

    @Slot()
    def handle_selection_cancelled(self):
        print("Selection cancelled signal received.")
        self.selection_overlay = None # Clear reference, it was deleted on close
        self.show()
        self.raise_()
        self.activateWindow()

    def show_feedback_flash(self, rect): # rect is global QRect
        # Check if a previous feedback widget exists and try to close it safely
        try:
            if self.feedback_widget is not None:
                 self.feedback_widget.close()
        except RuntimeError as e:
             print(f"Ignoring runtime error checking/closing previous feedback widget: {e}")
        self.feedback_widget = None 

        # Create and show the new one
        # print(f"Showing feedback flash at: {rect}") # REMOVE DEBUG 
        self.feedback_widget = FeedbackWidget(rect)
        # print("FeedbackWidget instance created.") # REMOVE DEBUG
        self.feedback_widget.setAttribute(Qt.WA_DeleteOnClose)
        self.feedback_widget.show()

    def update_region_label(self):
        if selected_search_region:
            self.region_label.setText(f"Shop Area: {selected_search_region}")
        else:
            self.region_label.setText("Shop Area: Not Set")

    @Slot()
    def toggle_automation(self):
        # print("--- toggle_automation slot reached (main thread) ---") # REMOVE DEBUG
        global automation_running, stop_automation_flag, paused_flag
        if automation_running or paused_flag:
            self.stop_automation()
        else:
            self.start_automation()
        # Don't call _update_ui_state here, rely on signals from worker/stop_automation

    def start_automation(self):
        global automation_running, stop_automation_flag, paused_flag, selected_search_region
        if automation_running: return # Prevent starting multiple times
        if not selected_search_region:
            QMessageBox.warning(self, "Error", "Please select the shop area first.")
            return

        amount = self.amount_input.text().strip()
        try:
             amount_int = int(amount)
             if amount_int <= 0: raise ValueError("Amount must be positive")
        except ValueError:
             QMessageBox.warning(self, "Error", "Please enter a valid positive integer amount.")
             return

        # File check (Check original relative names before resource_path is applied)
        missing_files = []
        # List the *original* relative filenames here
        essential_relative_files = ["input_field_anchor.png", "buy_button_green.png", 
                                    "buy_button_red.png", "buy_button_gray.png"]
        for rel_file in essential_relative_files:
            # Check existence using the path generated by resource_path
            abs_file_path = resource_path(rel_file)
            if not os.path.exists(abs_file_path):
                missing_files.append(rel_file) # Report the original name
        if missing_files:
            QMessageBox.critical(self, "File Error", f"Missing essential resource files: {', '.join(missing_files)}\nEnsure they are bundled correctly.")
            return

        # --- Visualize the intended scan area (Persistent) --- 
        if selected_search_region:
            try:
                # --- Close previous visualizer if any ---
                if self.scan_visualizer:
                    self.scan_visualizer.close() # Will trigger WA_DeleteOnClose
                    self.scan_visualizer = None
                # ---------------------------------------
                primary_screen = QGuiApplication.primaryScreen()
                offset_x, offset_y = 0, 0
                pixel_ratio = 1.0
                if primary_screen:
                    geo = primary_screen.geometry()
                    offset_x, offset_y = geo.x(), geo.y()
                    pixel_ratio = primary_screen.devicePixelRatio() or 1.0
                
                # Convert stored primary-relative PHYSICAL back to GLOBAL LOGICAL for visualizer
                vis_x = int(selected_search_region[0] / pixel_ratio) + offset_x
                vis_y = int(selected_search_region[1] / pixel_ratio) + offset_y
                vis_w = int(selected_search_region[2] / pixel_ratio)
                vis_h = int(selected_search_region[3] / pixel_ratio)
                rect_to_visualize = QRect(vis_x, vis_y, vis_w, vis_h) 
                print(f"Visualizing scan area (Global Logical): {rect_to_visualize}")
                # Create and show the persistent visualizer
                self.scan_visualizer = ScanAreaVisualizer(rect_to_visualize)
                self.scan_visualizer.show()
            except Exception as viz_err:
                 print(f"Error visualizing scan area: {viz_err}")
        # -------------------------------------------------

        print("Starting automation via Qt...")
        automation_running = True
        stop_automation_flag = False
        paused_flag = False
        self._update_ui_state("Starting...") # Initial status update

        # Create worker and thread
        self.automation_worker = AutomationWorker(selected_search_region, amount)
        self.automation_thread = QThread(self) # Parent thread to main window
        self.automation_worker.moveToThread(self.automation_thread)

        # Connect worker signals to main window slots
        self.automation_worker.status_updated.connect(self.handle_status_update)
        self.automation_worker.finished.connect(self.handle_automation_finished)
        self.automation_worker.error_occurred.connect(self.handle_automation_error)
        self.automation_worker.request_stop.connect(self.stop_automation) # Worker asks main thread to stop

        # Connect thread signals
        self.automation_thread.started.connect(self.automation_worker.run)
        # Ensure thread quits when worker is done or stopped
        self.automation_worker.finished.connect(self.automation_thread.quit)
        # Clean up worker/thread when thread finishes
        self.automation_worker.finished.connect(self.automation_worker.deleteLater)
        self.automation_thread.finished.connect(self.automation_thread.deleteLater)
        # Connect _clear_automation_refs only to thread finished signal
        self.automation_thread.finished.connect(self._clear_automation_refs)

        # Connect stop requests from main window to worker slot
        self.request_worker_stop.connect(self.automation_worker.stop)
        # Connect pause toggle from main window to worker slot
        self.request_worker_pause_toggle.connect(self.automation_worker.toggle_pause)

        self.automation_thread.start()
        print("Automation thread started.")
        self._update_ui_state() # Update buttons etc. to running state

    @Slot()
    def stop_automation(self):
        # print("--- stop_automation slot reached (main thread) ---") # REMOVE DEBUG
        global stop_automation_flag, automation_running, paused_flag
        print("Stop requested via Qt...")
        if self.automation_thread and self.automation_thread.isRunning():
            if not stop_automation_flag: # Prevent multiple stop signals
                stop_automation_flag = True # Set global flag first
                paused_flag = False # Ensure not paused externally
                print("Emitting request_worker_stop signal...")
                self.request_worker_stop.emit() # Signal the worker to stop its loop
                self._update_ui_state("Stopping...")
            else:
                print("Stop already in progress.")
        else:
            print("Automation not running or thread already stopped.")
            # Reset state if somehow called when not running
            automation_running = False
            stop_automation_flag = False
            paused_flag = False
            self._update_ui_state("Idle")

        # --- Hide Visualizer on Stop --- 
        if self.scan_visualizer:
            self.scan_visualizer.hide()
        # -------------------------------

    @Slot()
    def toggle_pause_resume(self):
        # print("--- toggle_pause_resume slot reached (main thread) ---") # REMOVE DEBUG
        global automation_running, paused_flag
        if automation_running:
            paused_flag = not paused_flag # Toggle global flag
            self.request_worker_pause_toggle.emit() # Signal worker to toggle its internal pause
            print(f"Pause flag toggled to: {paused_flag}")
            # Status update will come from worker signal based on its state
            # Force immediate UI update for pause button state might be needed if worker signal is delayed
            # self._update_ui_state("Paused" if paused_flag else "Resuming...") # Example immediate feedback
        else:
            print("Cannot pause/resume: Automation not running.")

    def _clear_automation_refs(self):
         print("Clearing automation thread/worker references.")
         # Check if worker exists before trying to disconnect (might be deleted already)
         if self.automation_worker:
             # Attempt to disconnect signals to prevent potential issues after deletion
             try: self.request_worker_stop.disconnect(self.automation_worker.stop)
             except RuntimeError: pass # Ignore if already disconnected
             try: self.request_worker_pause_toggle.disconnect(self.automation_worker.toggle_pause)
             except RuntimeError: pass
         self.automation_thread = None
         self.automation_worker = None
         # State flags (automation_running etc.) are reset in handle_automation_finished
         # --- Hide Visualizer on Clear --- 
         if self.scan_visualizer:
             self.scan_visualizer.hide()
         # -------------------------------
         self._update_ui_state() # Update button state etc.

    @Slot(str, bool) # status_text, is_paused
    def handle_status_update(self, status, is_paused_from_worker):
        # Update status label based on worker signal
        self.status_label.setText(f"Status: {status}")
        # Use dynamic property for styling paused state based on worker's report
        self.status_label.setProperty("paused", is_paused_from_worker)
        # Re-polish to apply potential style changes (like paused color)
        self.status_label.style().polish(self.status_label)

    @Slot(str) # final_status
    def handle_automation_finished(self, status):
        global automation_running, stop_automation_flag, paused_flag
        print(f"Automation finished signal received: {status}")
        automation_running = False
        stop_automation_flag = False # Reset flags
        paused_flag = False
        self._update_ui_state(status)
        # --- Hide Visualizer on Finish --- 
        if self.scan_visualizer:
            self.scan_visualizer.hide()
        # ---------------------------------
        # Optionally reset status to Idle after a delay
        QTimer.singleShot(2500, lambda: self._update_ui_state("Idle") if not automation_running else None)

    @Slot(str) # error_msg
    def handle_automation_error(self, error_msg):
        # Display error in status label
        error_display_text = f"Status: Error: {error_msg}"
        print(f"Handling automation error: {error_msg}")
        self.status_label.setText(error_display_text)
        self.status_label.setProperty("paused", False) # Ensure not styled as paused
        self.status_label.style().polish(self.status_label)
        # Optionally show a message box for errors
        # QMessageBox.warning(self, "Automation Error", error_msg)

    def _update_ui_state(self, status_text=None):
        """Updates the enable/disable state of UI elements and the status label."""
        global automation_running, paused_flag

        is_running_or_paused = automation_running or paused_flag
        self.start_stop_button.setText("Stop" if is_running_or_paused else "Start")

        # Enable/disable controls based on state
        # Prevent user interaction while running/paused
        can_interact = not is_running_or_paused
        self.select_region_button.setEnabled(can_interact)
        self.amount_input.setEnabled(can_interact)
        self.preset_name_input.setEnabled(can_interact)
        # Enable Save only when not running AND a region is selected
        self.save_preset_button.setEnabled(can_interact and selected_search_region is not None)
        # Enable Delete only when not running AND text is in the name field
        self.delete_preset_button.setEnabled(can_interact and bool(self.preset_name_input.text().strip()))
        # Enable/disable preset load buttons (handled by update_preset_buttons)
        self.update_preset_buttons() # update_preset_buttons also checks can_interact

        # --- Status Label Update ---
        # Determine the current actual state for the label
        current_status = "Idle"
        is_currently_paused = False # For styling

        if paused_flag: # Check global paused flag first (user-initiated pause)
             current_status = "Paused"
             is_currently_paused = True
        elif automation_running: # If running but not paused by user
             if status_text and status_text != "Idle":
                 current_status = status_text # Use status from worker/start/stop
             else:
                 current_status = "Running" # Default running state
             # Check if worker reported pause internally (e.g., via signal)
             # This requires the worker to reliably emit its pause state.
             # For simplicity, we primarily rely on the global paused_flag for styling.
             # If status_text includes 'Paused' explicitly, we can use that.
             if "Paused" in current_status:
                  is_currently_paused = True
        elif status_text: # If not running/paused, but a final status was provided
            current_status = status_text # e.g., "Finished", "Stopped", "Error..."

        # Only update label if the calculated status is different or forced
        final_text = f"Status: {current_status}"
        if self.status_label.text() != final_text or status_text is not None:
            self.status_label.setText(final_text)
            self.status_label.setProperty("paused", is_currently_paused)
            self.status_label.style().polish(self.status_label)


    # --- Preset Methods (Qt Adapated) ---
    def load_presets(self):
        """Loads presets from file and updates button list."""
        load_presets() # Call the global function
        self.update_preset_buttons()

    def save_presets(self):
        """Saves presets to file."""
        save_presets() # Call the global function

    @Slot()
    def save_preset_action(self):
        # print("--- save_preset_action called ---") # REMOVE DEBUG
        global presets, selected_search_region
        name = self.preset_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Error", "Please enter a preset name."); return
        if not selected_search_region:
            QMessageBox.warning(self, "Input Error", "Please select a shop area before saving."); return

        confirm_overwrite = True
        if name in presets:
            reply = QMessageBox.question(self, "Confirm Overwrite",
                                         f"Preset '{name}' exists. Overwrite?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            confirm_overwrite = (reply == QMessageBox.Yes)

        if confirm_overwrite:
            presets[name] = {"region": selected_search_region}
            self.save_presets() # Save to file
            self.update_preset_buttons() # Refresh GUI list
            print(f"Preset '{name}' saved.")

    @Slot()
    def delete_preset_action(self):
        # print("--- delete_preset_action called ---") # REMOVE DEBUG
        global presets, active_preset_name, selected_search_region
        name = self.preset_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Error", "Enter preset name to delete."); return
        if name not in presets:
            QMessageBox.warning(self, "Not Found", f"Preset '{name}' not found."); return

        reply = QMessageBox.question(self, "Confirm Delete", f"Delete preset '{name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            del presets[name]
            self.save_presets()
            self.update_preset_buttons()
            print(f"Preset '{name}' deleted.")
            # Clear input field if it was the deleted preset name
            if self.preset_name_input.text().strip() == name:
                self.preset_name_input.clear()
            # If the deleted preset was the active one, clear the selection
            if active_preset_name == name:
                 selected_search_region = None
                 active_preset_name = None
                 self.update_region_label()
                 self.update_preset_buttons() # Update styling


    @Slot()
    def load_preset_action(self):
        """Handles click on a preset button in the scroll list."""
        # Sender tells us which button was clicked
        sender_button = self.sender()
        if not sender_button or not isinstance(sender_button, QPushButton):
             print("Error: Could not identify preset button.")
             return
        preset_name = sender_button.text() # Button text is the preset name

        global presets, selected_search_region, active_preset_name
        
        print(f"Attempting to load preset: {preset_name}")
        if preset_name in presets:
            preset_data = presets[preset_name]
            region_tuple = preset_data.get("region") # Get the saved tuple
            # Validate region data format
            if isinstance(region_tuple, (list, tuple)) and len(region_tuple) == 4 and all(isinstance(v, int) for v in region_tuple):
                
                print(f"Preset '{preset_name}' contains primary-relative physical region: {region_tuple}")
                                
                # Store the primary-relative physical coordinates DIRECTLY for pyautogui
                selected_search_region = tuple(region_tuple) 
                active_preset_name = preset_name
                self.preset_name_input.setText(preset_name) 
                self.update_region_label() # Label now shows primary-relative physical
                print(f"Stored Direct Region for PyAutoGUI: {selected_search_region}")
                
                # --- Show feedback flash: Convert stored primary-relative PHYSICAL back to GLOBAL LOGICAL ---
                primary_screen = QGuiApplication.primaryScreen()
                offset_x, offset_y = 0, 0
                pixel_ratio = 1.0
                if primary_screen:
                    geo = primary_screen.geometry()
                    offset_x, offset_y = geo.x(), geo.y()
                    pixel_ratio = primary_screen.devicePixelRatio() or 1.0
                else:
                    print("Warning: Cannot get primary screen for feedback flash positioning.")
                    
                # Reverse the calculation: unscale first, then add global offset
                flash_x = int(selected_search_region[0] / pixel_ratio) + offset_x
                flash_y = int(selected_search_region[1] / pixel_ratio) + offset_y
                flash_w = int(selected_search_region[2] / pixel_ratio)
                flash_h = int(selected_search_region[3] / pixel_ratio)
                rect_to_flash = QRect(flash_x, flash_y, flash_w, flash_h) 
                print(f"Calculated GLOBAL LOGICAL rect for feedback flash: {rect_to_flash}")
                # -----------------------------------------------------------------------------------
                
                QTimer.singleShot(50, lambda r=rect_to_flash: self.show_feedback_flash(r))
                                
                self.update_preset_buttons() # Update button styling
            else:
                QMessageBox.warning(self, "Preset Error", f"Preset '{preset_name}' has invalid region data (must be tuple/list of 4 ints).")
                active_preset_name = None
                self.update_preset_buttons()
        else:
            QMessageBox.warning(self, "Load Error", f"Preset '{preset_name}' not found in memory.")
            active_preset_name = None
            self.update_preset_buttons()
        
        # Ensure button states are updated after loading
        self._update_ui_state()

    def update_preset_buttons(self):
        """Clears and repopulates the preset button list in the scroll area."""
        global presets, active_preset_name

        # Clear old buttons safely
        while self.preset_buttons_layout.count():
            item = self.preset_buttons_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater() # Schedule for deletion

        # Add label if no presets
        if not presets:
             no_preset_label = QLabel("No presets saved.")
             no_preset_label.setAlignment(Qt.AlignCenter)
             no_preset_label.setStyleSheet("color: #888888;") # Dim color
             self.preset_buttons_layout.addWidget(no_preset_label)
             return

        # Determine if automation is running to set button enable state
        is_running_or_paused = automation_running or paused_flag

        # Add buttons for each preset
        sorted_names = sorted(presets.keys())
        for name in sorted_names:
            button = QPushButton(name)
            button.setObjectName("PresetButton") # For QSS styling
            # Set dynamic property for active state styling
            is_active = (name == active_preset_name)
            button.setProperty("active", is_active)
            button.setToolTip(f"Load region for '{name}'")
            button.clicked.connect(self.load_preset_action) # Connect click to handler
            button.setEnabled(not is_running_or_paused) # Disable if automation running
            # Remove fixed size policy - FlowLayout uses sizeHint
            # button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            self.preset_buttons_layout.addWidget(button)

        # Force style re-evaluation for the container widget might be needed
        # if dynamic properties don't update automatically
        self.preset_scroll_widget.style().unpolish(self.preset_scroll_widget)
        self.preset_scroll_widget.style().polish(self.preset_scroll_widget)


    # --- Hotkey Handling (Using pynput listener) ---
    def start_hotkey_listener(self):
        """Starts the pynput keyboard listener in a separate thread."""
        # Check if listener is already running
        if hasattr(self, 'hotkey_listener_thread') and self.hotkey_listener_thread and self.hotkey_listener_thread.is_alive():
             print("Hotkey listener already running.")
             return
        # Pass self (MainWindow instance) to the target function
        self.hotkey_listener_thread = threading.Thread(target=self._run_pynput_listener, args=(self,), daemon=True)
        self.hotkey_listener_thread.start()


    def _run_pynput_listener(self, main_window):
        """Target function for the listener thread."""
        print(f"Starting pynput listener (F10, F9, Esc)")
        # Store main_window reference locally for callbacks
        self._main_window_for_listener = main_window 
        try:
            # Use Listener as a context manager
            with keyboard.Listener(on_press=self._on_hotkey_press, on_release=self._on_hotkey_release) as listener:
                self.pynput_listener_instance = listener # Store reference
                listener.join() # Block thread until listener stops
        except Exception as e:
            print(f"Pynput listener error: {e}")
        finally:
             print("Pynput listener thread finished.")
             self.pynput_listener_instance = None # Clear reference
             self._main_window_for_listener = None # Clear reference

    def _on_hotkey_press(self, key):
        """Callback executed by pynput thread on key press."""
        # Use the stored reference to the main window
        main_window = getattr(self, '_main_window_for_listener', None)
        if not main_window:
            print("Error: Listener callback cannot find main window reference.")
            return
            
        try:
             if key in start_stop_hotkey:
                 print("F10 detected (pynput thread)")
                 # Emit signal instead of using QTimer
                 main_window.f10_hotkey_pressed.emit()
             elif key in pause_resume_hotkey:
                 print("F9 detected (pynput thread)")
                 # Emit signal instead of using QTimer
                 main_window.f9_hotkey_pressed.emit()
        except Exception as e:
             print(f"Error processing hotkey press: {e}")


    def _on_hotkey_release(self, key):
        """Callback executed by pynput thread on key release."""
        main_window = getattr(self, '_main_window_for_listener', None)
        if not main_window:
             print("Error: Listener callback cannot find main window reference.")
             return
             
        try:
            if key == keyboard.Key.esc:
                print("ESC detected (pynput thread)")
                # Emit signal instead of using QTimer
                main_window.esc_hotkey_pressed.emit()
        except Exception as e:
            print(f"Error processing hotkey release: {e}")

    def stop_hotkey_listener(self):
         """Stops the running pynput listener instance."""
         if hasattr(self, 'pynput_listener_instance') and self.pynput_listener_instance:
             print("Stopping pynput listener...")
             try:
                 self.pynput_listener_instance.stop()
                 # Wait briefly for the thread to potentially finish after stop()
                 if hasattr(self, 'hotkey_listener_thread') and self.hotkey_listener_thread:
                     self.hotkey_listener_thread.join(timeout=0.5)
             except Exception as e:
                  print(f"Error stopping listener: {e}")
         else:
              print("Hotkey listener not running or instance not found.")


    # --- Window Closing / Geometry Saving ---
    def _save_window_geometry(self):
        print("Saving window geometry...")
        settings = QSettings(ORG_NAME, APP_NAME)
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        print(f"Saved geometry: {self.saveGeometry()}")

    def _restore_window_geometry(self):
        print("Restoring window geometry...")
        settings = QSettings(ORG_NAME, APP_NAME)
        geometry = settings.value("geometry")
        state = settings.value("windowState")
        if geometry:
            if isinstance(geometry, QByteArray):
                 print(f"Restoring geometry: {geometry}")
                 self.restoreGeometry(geometry)
            else:
                print(f"Warning: Saved geometry has unexpected type: {type(geometry)}")
        else:
            print("No saved geometry found, using default size.")
            self.resize(600, 500) # Apply default size if no settings
            
        if state:
             if isinstance(state, QByteArray):
                print(f"Restoring state: {state}")
                self.restoreState(state)
             else:
                 print(f"Warning: Saved state has unexpected type: {type(state)}")

    def closeEvent(self, event):
        """Handles the main window close event."""
        print("Close event detected.")
        # 1. Save geometry
        self._save_window_geometry()
        
        # 2. Stop automation if running
        if self.automation_thread and self.automation_thread.isRunning():
            print("Stopping automation before closing...")
            self.stop_automation()
            self.automation_thread.quit() 
            if not self.automation_thread.wait(1000): 
                 print("Warning: Automation thread did not stop gracefully.")

        # 3. Stop hotkey listener
        self.stop_hotkey_listener()

        # --- Ensure visualizer is closed --- 
        if self.scan_visualizer:
            self.scan_visualizer.close() # Ensure it's closed and deleted
        # -------------------------------------

        print("Exiting application.")
        event.accept() # Allow the window to close


# --- Main Execution ---
if __name__ == "__main__":
    # Set default pause for pyautogui (optional, but good practice)
    pyautogui.PAUSE = 0.05
    print(f"PyAutoGUI pause interval set to: {pyautogui.PAUSE}")

    # Create the Qt Application
    app = QApplication(sys.argv)

    # Load presets data initially
    load_presets()

    # Create and show the main window
    window = MainWindow()
    window.show()

    # Start the hotkey listener after the window is setup and shown
    window.start_hotkey_listener()

    # Start the Qt event loop
    sys.exit(app.exec())
