import tkinter as tk


class StatsCard:
    def __init__(self, parent, title, value, bg_color):
        """
        Create a card to display statistics

        Args:
            parent: Parent widget
            title: Card title
            value: Value to display
            bg_color: Background color
        """
        self.card = tk.Frame(parent, bg=bg_color, bd=1, relief=tk.RAISED)
        self.card.pack(fill=tk.X, pady=10)

        tk.Label(self.card, text=title, font=("Arial", 12), bg=bg_color).pack(pady=(10, 5))
        tk.Label(self.card, text=str(value), font=("Arial", 20, "bold"), bg=bg_color).pack(pady=(5, 10))

    def update_value(self, new_value):
        """Update the displayed value"""
        for widget in self.card.winfo_children():
            if isinstance(widget, tk.Label) and widget.cget("font") == "Arial 20 bold":
                widget.config(text=str(new_value))
                break