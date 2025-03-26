import tkinter as tk
from tkinter import ttk, messagebox
from models.vendor import Vendor
from utils.table_utils import configure_treeview

class VendorListView:
    def __init__(self, parent, controllers, show_view_callback):
        self.parent = parent
        self.controllers = controllers
        self.show_view = show_view_callback

        self.frame = tk.Frame(parent)
        self.setup_ui()

    def setup_ui(self):
        # Create back button
        back_button = tk.Button(self.frame, text="Back to Dashboard",
                                command=self.return_to_dashboard)
        back_button.pack(anchor="nw", padx=10, pady=10)

        # Title
        tk.Label(self.frame, text="Vendor Management",
                 font=("Arial", 14, "bold")).pack(anchor="w", padx=20, pady=10)

        # Table frame
        table_frame = tk.Frame(self.frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Create treeview for vendors
        columns = ("ID", "Name", "Contact", "Phone", "Email")
        self.vendor_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.vendor_tree = configure_treeview(self.vendor_tree)
        # Set column headings
        for col in columns:
            self.vendor_tree.heading(col, text=col)

        # Hide ID column
        self.vendor_tree.column("ID", width=0, stretch=tk.NO)
        self.vendor_tree.column("Name", width=200)
        self.vendor_tree.column("Contact", width=150)
        self.vendor_tree.column("Phone", width=120)
        self.vendor_tree.column("Email", width=200)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.vendor_tree.yview)
        self.vendor_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.vendor_tree.pack(fill="both", expand=True)

        # Button frame
        button_frame = tk.Frame(self.frame)
        button_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Button(button_frame, text="Add Vendor",
                  command=self.add_vendor).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Edit Vendor",
                  command=self.edit_vendor).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Delete Vendor",
                  command=self.delete_vendor).pack(side=tk.LEFT, padx=5)

        # Populate vendor list
        self.refresh_vendor_list()

    def refresh_vendor_list(self):
        """Refresh the vendor list in the treeview"""
        self.vendor_tree.delete(*self.vendor_tree.get_children())

        vendors = self.controllers["vendor"].get_all_vendors()
        for i, vendor in enumerate(vendors):
            row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            
            self.vendor_tree.insert("", "end", values=(
                vendor.id,
                vendor.name,
                vendor.contact,
                vendor.phone,
                vendor.email
            ), tags=(row_tag,))

    def add_vendor(self):
        """Open dialog to add a new vendor"""
        self.open_vendor_dialog()

    def edit_vendor(self):
        """Open dialog to edit selected vendor"""
        selected_item = self.vendor_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No vendor selected")
            return

        vendor_id = self.vendor_tree.item(selected_item, "values")[0]
        vendor = self.controllers["vendor"].get_vendor_by_id(vendor_id)

        if not vendor:
            messagebox.showerror("Error", "Vendor not found")
            return

        self.open_vendor_dialog(vendor)

    def delete_vendor(self):
        """Delete selected vendor"""
        selected_item = self.vendor_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No vendor selected")
            return

        vendor_id = self.vendor_tree.item(selected_item, "values")[0]

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this vendor?"):
            success, message = self.controllers["vendor"].delete_vendor(vendor_id)

            if success:
                messagebox.showinfo("Success", message)
                self.refresh_vendor_list()
            else:
                messagebox.showerror("Error", message)

    def open_vendor_dialog(self, vendor=None):
        """Open dialog to add or edit a vendor"""
        is_edit = vendor is not None

        dialog = tk.Toplevel(self.parent)
        dialog.title("Edit Vendor" if is_edit else "Add Vendor")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.transient(self.parent)
        dialog.grab_set()

        # Vendor form
        form_frame = tk.Frame(dialog, padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(form_frame, text="Vendor Name:").grid(row=0, column=0, sticky="w", pady=5)
        name_var = tk.StringVar(value=vendor.name if is_edit else "")
        name_entry = tk.Entry(form_frame, textvariable=name_var, width=30)
        name_entry.grid(row=0, column=1, sticky="w", pady=5)

        tk.Label(form_frame, text="Contact Person:").grid(row=1, column=0, sticky="w", pady=5)
        contact_var = tk.StringVar(value=vendor.contact if is_edit else "")
        contact_entry = tk.Entry(form_frame, textvariable=contact_var, width=30)
        contact_entry.grid(row=1, column=1, sticky="w", pady=5)

        tk.Label(form_frame, text="Phone:").grid(row=2, column=0, sticky="w", pady=5)
        phone_var = tk.StringVar(value=vendor.phone if is_edit else "")
        phone_entry = tk.Entry(form_frame, textvariable=phone_var, width=30)
        phone_entry.grid(row=2, column=1, sticky="w", pady=5)

        tk.Label(form_frame, text="Email:").grid(row=3, column=0, sticky="w", pady=5)
        email_var = tk.StringVar(value=vendor.email if is_edit else "")
        email_entry = tk.Entry(form_frame, textvariable=email_var, width=30)
        email_entry.grid(row=3, column=1, sticky="w", pady=5)

        tk.Label(form_frame, text="Address:").grid(row=4, column=0, sticky="w", pady=5)
        address_var = tk.StringVar(value=vendor.address if is_edit else "")
        address_entry = tk.Entry(form_frame, textvariable=address_var, width=30)
        address_entry.grid(row=4, column=1, sticky="w", pady=5)

        # Buttons
        button_frame = tk.Frame(form_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)

        def save_vendor():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Vendor name is required")
                return

            if is_edit:
                # Update existing vendor
                vendor.name = name
                vendor.contact = contact_var.get().strip()
                vendor.phone = phone_var.get().strip()
                vendor.email = email_var.get().strip()
                vendor.address = address_var.get().strip()

                success, message = self.controllers["vendor"].update_vendor(vendor)
            else:
                # Create new vendor
                new_vendor = Vendor(
                    name=name,
                    contact=contact_var.get().strip(),
                    phone=phone_var.get().strip(),
                    email=email_var.get().strip(),
                    address=address_var.get().strip()
                )

                success, message = self.controllers["vendor"].add_vendor(new_vendor)

            if success:
                dialog.destroy()
                messagebox.showinfo("Success", message)
                self.refresh_vendor_list()
            else:
                messagebox.showerror("Error", message)

        tk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Save", command=save_vendor).pack(side=tk.RIGHT, padx=5)

        # Focus on name field
        name_entry.focus_set()

    def return_to_dashboard(self):
        """Return to main dashboard"""
        from views.main_dashboard import MainDashboard
        dashboard = MainDashboard(self.parent, self.controllers, self.show_view)
        self.show_view(dashboard)

    def show(self):
        """Show this view"""
        self.refresh_vendor_list()
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """Hide this view"""
        self.frame.pack_forget()