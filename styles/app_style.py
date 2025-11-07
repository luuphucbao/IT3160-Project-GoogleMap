import os
from PyQt6.QtGui import QPalette, QColor


def apply_dark_palette(app):
    """Apply a consistent dark QPalette to the QApplication.

    Kept here so run.py stays minimal and all styling/palette logic lives in styles/.
    """
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


def apply_stylesheet(app, qss_filename="dark_theme.qss"):
    """Load a QSS file from the styles folder and apply it to the QApplication.

    The QSS file is expected to live next to this module (styles/).
    """
    style_file = os.path.join(os.path.dirname(__file__), qss_filename)
    try:
        with open(style_file, "r", encoding="utf-8") as f:
            style = f.read()
            app.setStyleSheet(style)
    except Exception as e:
        # Keep this lightweight: don't crash the app if the stylesheet is missing.
        print(f"Error loading style sheet '{style_file}': {e}")


def apply_app_style(app):
    """Convenience helper to apply the app's palette and stylesheet."""
    apply_dark_palette(app)
    apply_stylesheet(app)
