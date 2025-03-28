"""
Application settings for the Purchase Management System
"""

# Application name and version
APP_NAME = "Purchase Management System"
APP_VERSION = "1.0.0"

# Database settings
DATABASE_FILE = "purchase_system.db"
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"
BACKUP_DIR = "backups"

# Data directory (for legacy JSON support, can be removed later)
DATA_DIR = "data"

# File names (legacy, can be removed later)
PURCHASES_FILE = "purchases.json"
VENDORS_FILE = "vendors.json"
BUDGETS_FILE = "budgets.json"

# UI settings
UI_THEME = "clam"  # Possible values: "clam", "alt", "default"
UI_FONTS = {
    "default": ("Arial", 10),
    "title": ("Arial", 14, "bold"),
    "header": ("Arial", 12, "bold"),
    "large": ("Arial", 22, "bold")
}
UI_COLORS = {
    "header_bg": "#f0f0f0",
    "pending_card": "#ffcccb",
    "orders_card": "#e6f2ff",
    "spending_card": "#e6ffe6",
    "even_row": "#f8f8f8",
    "odd_row": "#ffffff",
    "pending": "#ffcccb",
    "approved": "#ccffcc",
    "partial": "#ffffcc"
}

# Button style
BUTTON_STYLE = {
    "padx": 6,
    "pady": 6,
    "relief": "flat",
    "bg": "#4e79a7"
}

# Chart settings
CHART_COLORS = [
    "#4e79a7", "#f28e2c", "#e15759", "#76b7b2", "#59a14f",
    "#edc949", "#af7aa1", "#ff9da7", "#9c755f", "#bab0ab"
]

# Column widths
COLUMN_WIDTHS = {
    "id": 0,
    "order_number": 100,
    "vendor": 150,
    "date": 100,
    "total": 100,
    "status": 100,
    "description": 200,
    "quantity": 70,
    "unit_price": 100,
    "received": 80,
    "budget": 200,
    "amount": 100
}