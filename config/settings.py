"""
Application settings for the Purchase Management System
"""

# Application name and version
APP_NAME = "Purchase Management System"
APP_VERSION = "1.0.0"

# Data directory
DATA_DIR = "data"

# File names
PURCHASES_FILE = "purchases.json"
VENDORS_FILE = "vendors.json"
BUDGETS_FILE = "budgets.json"

# UI settings
UI_THEME = "default"
UI_COLORS = {
    "header_bg": "#f0f0f0",
    "pending_card": "#ffcccb",
    "orders_card": "#e6f2ff",
    "spending_card": "#e6ffe6"
}

# Chart colors
CHART_COLORS = [
    "#4e79a7", "#f28e2c", "#e15759", "#76b7b2", "#59a14f",
    "#edc949", "#af7aa1", "#ff9da7", "#9c755f", "#bab0ab"
]