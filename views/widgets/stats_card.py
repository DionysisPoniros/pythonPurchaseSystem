# views/widgets/stats_card.py
import tkinter as tk
from config.settings import UI_FONTS, UI_COLORS

class StatsCard:
    def __init__(self, parent, title, value, bg_color=None, icon=None):
        """
        Create a card to display statistics with improved visual design
        
        Args:
            parent: Parent widget
            title: Card title
            value: Value to display
            bg_color: Background color (or use from settings if None)
            icon: Unicode icon or None
        """
        # Use settings for default values
        if bg_color is None:
            bg_color = UI_COLORS.get("orders_card", "#e6f2ff")
        
        # Create card with rounded appearance
        self.card = tk.Frame(parent, bg=bg_color, bd=1, relief=tk.RAISED)
        self.card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add some padding
        self.inner_frame = tk.Frame(self.card, bg=bg_color, padx=15, pady=15)
        self.inner_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add header with icon if provided
        self.header_frame = tk.Frame(self.inner_frame, bg=bg_color)
        self.header_frame.pack(fill=tk.X)
        
        if icon:
            self.icon_label = tk.Label(
                self.header_frame, 
                text=icon, 
                font=UI_FONTS.get("large", ("Arial", 16)), 
                bg=bg_color
            )
            self.icon_label.pack(side=tk.LEFT, pady=(5, 0))
        
        self.title_label = tk.Label(
            self.header_frame, 
            text=title, 
            font=UI_FONTS.get("header", ("Arial", 12)), 
            bg=bg_color, 
            anchor="w"
        )
        self.title_label.pack(side=tk.LEFT, pady=(5, 0), padx=(5, 0))
        
        # Value with larger font
        self.value_label = tk.Label(
            self.inner_frame, 
            text=str(value), 
            font=UI_FONTS.get("large", ("Arial", 22, "bold")), 
            bg=bg_color
        )
        self.value_label.pack(pady=(10, 5))
        
        # Store the original background color for updates
        self.bg_color = bg_color

    def update_value(self, new_value):
        """Update the displayed value"""
        # Update the label text
        self.value_label.config(text=str(new_value))
        
    def update_color(self, new_color):
        """Update the card color"""
        # Update all components with the new color
        self.card.config(bg=new_color)
        self.inner_frame.config(bg=new_color)
        self.header_frame.config(bg=new_color)
        self.title_label.config(bg=new_color)
        self.value_label.config(bg=new_color)
        
        # Update icon label if it exists
        if hasattr(self, 'icon_label'):
            self.icon_label.config(bg=new_color)
            
        # Update stored color
        self.bg_color = new_color
        
    def destroy(self):
        """Destroy the card"""
        self.card.destroy()