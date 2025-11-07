import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor

# Create QApplication first, before any imports that might use QPixmap
app = QApplication(sys.argv)

# Set dark theme palette
dark_palette = QPalette()
dark_palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
dark_palette.setColor(QPalette.ColorRole.Base, QColor(45, 45, 45))
dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

app.setPalette(dark_palette)

# Load and apply dark theme stylesheet
style_file = os.path.join(os.path.dirname(__file__), "styles", "dark_theme.qss")
try:
    with open(style_file, "r") as f:
        style = f.read()
        app.setStyleSheet(style)
except Exception as e:
    print(f"Error loading style sheet: {e}")

# Now import your main window
from app.main_window import MainWindow

# Create and show window
window = MainWindow()
window.setWindowTitle("PathFinding - Dark Theme")
window.show()

sys.exit(app.exec())