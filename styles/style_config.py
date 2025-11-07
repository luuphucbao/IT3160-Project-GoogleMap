from PyQt6.QtGui import QColor

# Centralized UI color configuration for canvas and graphics
# Use these constants in map_viewer.py and other visualization modules.

# Countdown / text
COUNTDOWN_COLOR = QColor("white")
COUNTDOWN_BG_COLOR = QColor(0, 0, 0, 150)  # Semi-transparent black

# Traffic lines
TRAFFIC_LINE_COLOR = QColor("red")
TRAFFIC_LINE_TEMP_COLOR = QColor("orange")

# Rain area brushes/pens
RAIN_BRUSH_COLOR = QColor(0, 0, 255, 50)
RAIN_BRUSH_COLOR_FINAL = QColor(0, 0, 255, 80)
RAIN_PEN_COLOR = QColor("blue")

# Blocked way
BLOCK_WAY_COLOR = QColor("black")

# Temporary click / feedback point
TEMP_POINT_COLOR = QColor("gray")

# Permanent start / end point colors
START_POINT_COLOR = QColor("green")
END_POINT_COLOR = QColor("blue")

# Placeholder icon color
PLACEHOLDER_COLOR = QColor("purple")

# Traffic light effect line
TRAFFIC_LIGHT_LINE_COLOR = QColor("orange")

# Car block marker colors
CAR_BLOCK_COLOR = QColor("darkred")
CAR_BLOCK_PEN_COLOR = QColor("black")

# Other small UI constants
DEFAULT_POINT_RADIUS = 5
