import tkinter as tk
from tkinter import ttk

def configure_treeview(treeview):
    """Apply consistent styling to treeviews"""
    # Configure the treeview styling
    style = ttk.Style()
    
    # Configure the treeview colors
    style.configure("Treeview",
                  background="#f8f8f8",
                  foreground="black",
                  rowheight=25,
                  fieldbackground="#f8f8f8")
    
    # Configure the treeview headings
    style.configure("Treeview.Heading",
                  background="#e0e0e0",
                  foreground="black",
                  relief="flat")
    
    style.map("Treeview.Heading",
            background=[('pressed', '#d0d0d0'), ('active', '#e0e0e0')])
    
    # Add zebra striping (alternating colors)
    treeview.tag_configure('oddrow', background='#f0f0f0')
    treeview.tag_configure('evenrow', background='#ffffff')
    
    # Status color coding
    treeview.tag_configure('pending', background='#ffcccb')
    treeview.tag_configure('approved', background='#ccffcc')
    treeview.tag_configure('partial', background='#ffffcc')
    
    return treeview