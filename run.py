import sys
import os
from PyQt6.QtWidgets import QApplication

# Create QApplication first, before any imports that might use QPixmap
app = QApplication(sys.argv)

# Apply app styling (palette + QSS) from styles package
from styles.app_style import apply_app_style

apply_app_style(app)

# Now import your main window
from app.main_window import MainWindow

# Create and show window
window = MainWindow()
window.setWindowTitle("PathFinding")
window.show()

sys.exit(app.exec())