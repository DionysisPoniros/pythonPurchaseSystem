import tkinter as tk
import os


class ActionButton:
    def __init__(self, parent, text, command, icon_path=None, row=0, col=0):
        """
        Create an action button with icon and text

        Args:
            parent: Parent widget
            text: Button text
            command: Button command
            icon_path: Path to icon image
            row: Grid row
            col: Grid column
        """
        self.button_frame = tk.Frame(parent)
        self.button_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        # Try to load icon, use text-only button if icon not found
        try:
            if icon_path and os.path.exists(icon_path):
                self.icon = tk.PhotoImage(file=icon_path)
                self.icon = self.icon.subsample(4, 4)  # Resize icon
                self.btn = tk.Button(self.button_frame, text=text, image=self.icon,
                                     compound=tk.TOP, command=command, width=120, height=100)
                self.btn.image = self.icon  # Keep a reference to prevent garbage collection
            else:
                raise FileNotFoundError("Icon not found")
        except:
            self.btn = tk.Button(self.button_frame, text=text, command=command, width=15, height=5)

        self.btn.pack(fill=tk.BOTH, expand=True)