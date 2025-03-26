import tkinter as tk

class StatsCard:
    def __init__(self, parent, title, value, bg_color, icon=None):
        """
        Create a card to display statistics with improved visual design
        
        Args:
            parent: Parent widget
            title: Card title
            value: Value to display
            bg_color: Background color
            icon: Unicode icon or None
        """
        # Create card with rounded appearance
        self.card = tk.Frame(parent, bg=bg_color, bd=1, relief=tk.RAISED)
        self.card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add some padding
        inner_frame = tk.Frame(self.card, bg=bg_color, padx=15, pady=15)
        inner_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add header with icon if provided
        header_frame = tk.Frame(inner_frame, bg=bg_color)
        header_frame.pack(fill=tk.X)
        
        if icon:
            icon_label = tk.Label(header_frame, text=icon, font=("Arial", 16), bg=bg_color)
            icon_label.pack(side=tk.LEFT, pady=(5, 0))
        
        title_label = tk.Label(header_frame, text=title, font=("Arial", 12), 
                              bg=bg_color, anchor="w")
        title_label.pack(side=tk.LEFT, pady=(5, 0), padx=(5, 0))
        
        # Value with larger font
        self.value_label = tk.Label(inner_frame, text=str(value), 
                                  font=("Arial", 22, "bold"), bg=bg_color)
        self.value_label.pack(pady=(10, 5))

    def update_value(self, new_value):
        """Update the displayed value"""
        self.value_label.config(text=str(new_value))