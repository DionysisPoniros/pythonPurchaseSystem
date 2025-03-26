# purchase_system/views/purchase_views.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from models.purchase import Purchase
from utils.exporters import CSVExporter
from utils.table_utils import configure_treeview


class PurchaseListView:
    def __init__(self, parent, controllers, show_view_callback):
        self.parent = parent
        self.controllers = controllers
        self.show_view = show_view_callback

        # Add sort state tracking
        self.sort_column = None
        self.sort_reverse = False

        self.frame = tk.Frame(parent)
        self.setup_ui()

    def setup_ui(self):
        # Create back button
        back_button = tk.Button(self.frame, text="Back to Dashboard",
                                command=self.return_to_dashboard)
        back_button.pack(anchor="nw", padx=10, pady=10)

        # Use the new search UI
        self.setup_search_ui()

        # Table frame
        table_frame = tk.Frame(self.frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Create treeview for purchases
        columns = ("ID", "Order #", "Vendor", "Date", "Total", "Status")
        self.purchase_tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        # Set column headings and widths
        for col in columns:
            if col != "ID":  # Skip binding the hidden ID column
                self.purchase_tree.heading(col, text=col,
                                           command=lambda c=col: self.treeview_sort_column(c))
            else:
                self.purchase_tree.heading(col, text=col)
            self.purchase_tree.column(col, width=100)

        # Hide ID column
        self.purchase_tree.column("ID", width=0, stretch=tk.NO)

        # Apply styling
        self.purchase_tree = configure_treeview(self.purchase_tree)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.purchase_tree.yview)
        self.purchase_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.purchase_tree.pack(fill="both", expand=True)

        # Button frame for actions
        action_frame = tk.Frame(self.frame)
        action_frame.pack(fill=tk.X, padx=20, pady=10)

        # Action buttons
        tk.Button(action_frame, text="View Details",
                  command=self.view_purchase_details).pack(side=tk.LEFT, padx=5)

        tk.Button(action_frame, text="Add Purchase",
                  command=self.add_purchase).pack(side=tk.LEFT, padx=5)

        tk.Button(action_frame, text="Edit Purchase",
                  command=self.edit_purchase).pack(side=tk.LEFT, padx=5)

        tk.Button(action_frame, text="Delete Purchase",
                  command=self.delete_purchase).pack(side=tk.LEFT, padx=5)

        tk.Button(action_frame, text="Receive Items",
                  command=self.receive_items).pack(side=tk.LEFT, padx=5)

        tk.Button(action_frame, text="Export to CSV",
                  command=self.export_purchases).pack(side=tk.RIGHT, padx=5)

    def setup_search_ui(self):
        search_frame = tk.Frame(self.frame, bg="#f5f5f5")
        search_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Title and search in same row
        header_frame = tk.Frame(search_frame, bg="#f5f5f5")
        header_frame.pack(fill=tk.X)
        
        tk.Label(header_frame, text="Purchase Orders", 
               font=("Arial", 14, "bold"), bg="#f5f5f5").pack(side=tk.LEFT)
        
        # More prominent search box
        search_box_frame = tk.Frame(header_frame, bg="#f5f5f5", bd=1, relief=tk.SOLID)
        search_box_frame.pack(side=tk.RIGHT)
        
        # Search icon (Unicode magnifying glass)
        tk.Label(search_box_frame, text="🔍", bg="#f5f5f5").pack(side=tk.LEFT, padx=5)
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_box_frame, textvariable=self.search_var, 
                              width=25, font=("Arial", 10), bd=0)
        search_entry.pack(side=tk.LEFT, padx=5, pady=5)
        search_entry.bind("<Return>", lambda e: self.perform_search())
        
        search_options = ["Order #", "Vendor", "Date", "Status", "All Fields"]
        self.search_option_var = tk.StringVar(value=search_options[0])
        option_menu = ttk.Combobox(search_box_frame, textvariable=self.search_option_var,
                                 values=search_options, width=12)
        option_menu.pack(side=tk.LEFT, padx=5)
        
        search_button = tk.Button(search_box_frame, text="Search", command=self.perform_search)
        search_button.pack(side=tk.LEFT, padx=5)
        
        # Add filter options below
        filter_frame = tk.Frame(search_frame, bg="#f5f5f5")
        filter_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(filter_frame, text="Filter by:", bg="#f5f5f5").pack(side=tk.LEFT)
        
        # Add filter buttons
        for status in ["All", "Pending", "Partial", "Received"]:
            btn = tk.Button(filter_frame, text=status, relief=tk.FLAT, 
                          padx=10, command=lambda s=status: self.filter_by_status(s))
            btn.pack(side=tk.LEFT, padx=3)

    def treeview_sort_column(self, col):
        """Sort treeview by column"""
        if self.sort_column == col:
            # If already sorting by this column, reverse the direction
            self.sort_reverse = not self.sort_reverse
        else:
            # New sort column, default to ascending
            self.sort_column = col
            self.sort_reverse = False

        # Update column headings to show sort direction
        for c in self.purchase_tree["columns"]:
            if c == col:
                self.purchase_tree.heading(c, text=f"{c} {'↓' if self.sort_reverse else '↑'}")
            elif c != "ID":  # Don't modify the hidden ID column
                self.purchase_tree.heading(c, text=c)  # Remove sort indicator

        # Refresh the list with the new sort
        self.refresh_purchase_list()

    def refresh_purchase_list(self):
        """Refresh the purchase list in the treeview"""
        self.purchase_tree.delete(*self.purchase_tree.get_children())

        # Get purchases from controller
        purchases = self.controllers["purchase"].get_all_purchases()

        # Sort purchases if a sort column is selected
        if self.sort_column:
            if self.sort_column == "Order #":
                purchases.sort(key=lambda x: x.order_number, reverse=self.sort_reverse)
            elif self.sort_column == "Vendor":
                purchases.sort(key=lambda x: x.vendor_name, reverse=self.sort_reverse)
            elif self.sort_column == "Date":
                purchases.sort(key=lambda x: x.date, reverse=self.sort_reverse)
            elif self.sort_column == "Total":
                purchases.sort(key=lambda x: x.get_total(), reverse=self.sort_reverse)
            elif self.sort_column == "Status":
                purchases.sort(key=lambda x: x.get_status(), reverse=self.sort_reverse)

        # Insert purchase data into treeview
        for i, purchase in enumerate(purchases):
            total = purchase.get_total()
            status = purchase.get_status()
            
            row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            # Add status tag
            if status == "Pending":
                status_tag = 'pending'
            elif status == "Partial":
                status_tag = 'partial'
            else:
                status_tag = 'approved'
                
            self.purchase_tree.insert("", "end", values=(
                purchase.id,
                purchase.order_number,
                purchase.vendor_name,
                purchase.date,
                f"${total:.2f}",
                status
            ), tags=(row_tag, status_tag))

    def filter_by_status(self, status):
        """Filter purchases by status"""
        self.purchase_tree.delete(*self.purchase_tree.get_children())
        
        # Get all purchases
        purchases = self.controllers["purchase"].get_all_purchases()
        filtered = []
        
        if status == "All":
            filtered = purchases
        else:
            for purchase in purchases:
                purchase_status = purchase.get_status()
                if status == purchase_status:
                    filtered.append(purchase)
        
        # Display filtered purchases
        for i, purchase in enumerate(filtered):
            total = purchase.get_total()
            status_text = purchase.get_status()
            
            row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            # Add status tag
            if status_text == "Pending":
                status_tag = 'pending'
            elif status_text == "Partial":
                status_tag = 'partial'
            else:
                status_tag = 'approved'
            
            self.purchase_tree.insert("", "end", values=(
                purchase.id,
                purchase.order_number,
                purchase.vendor_name,
                purchase.date,
                f"${total:.2f}",
                status_text
            ), tags=(row_tag, status_tag))

    def perform_search(self):
        """Search purchases based on criteria"""
        search_text = self.search_var.get().lower()
        search_field = self.search_option_var.get()

        if not search_text:
            self.refresh_purchase_list()
            return

        # Get all purchases
        all_purchases = self.controllers["purchase"].get_all_purchases()
        filtered_purchases = []

        for purchase in all_purchases:
            if search_field == "All Fields":
                # Search all fields
                searchable_text = (
                        purchase.order_number +
                        purchase.vendor_name +
                        purchase.date +
                        purchase.get_status()
                ).lower()

                if search_text in searchable_text:
                    filtered_purchases.append(purchase)
            else:
                # Search specific field
                if search_field == "Order #" and search_text in purchase.order_number.lower():
                    filtered_purchases.append(purchase)
                elif search_field == "Vendor" and search_text in purchase.vendor_name.lower():
                    filtered_purchases.append(purchase)
                elif search_field == "Date" and search_text in purchase.date.lower():
                    filtered_purchases.append(purchase)
                elif search_field == "Status" and search_text in purchase.get_status().lower():
                    filtered_purchases.append(purchase)

        # Sort filtered purchases
        if self.sort_column:
            if self.sort_column == "Order #":
                filtered_purchases.sort(key=lambda x: x.order_number, reverse=self.sort_reverse)
            elif self.sort_column == "Vendor":
                filtered_purchases.sort(key=lambda x: x.vendor_name, reverse=self.sort_reverse)
            elif self.sort_column == "Date":
                filtered_purchases.sort(key=lambda x: x.date, reverse=self.sort_reverse)
            elif self.sort_column == "Total":
                filtered_purchases.sort(key=lambda x: x.get_total(), reverse=self.sort_reverse)
            elif self.sort_column == "Status":
                filtered_purchases.sort(key=lambda x: x.get_status(), reverse=self.sort_reverse)

        # Display filtered results
        self.purchase_tree.delete(*self.purchase_tree.get_children())

        for i, purchase in enumerate(filtered_purchases):
            total = purchase.get_total()
            status = purchase.get_status()
            
            row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            # Add status tag
            if status == "Pending":
                status_tag = 'pending'
            elif status == "Partial":
                status_tag = 'partial'
            else:
                status_tag = 'approved'

            self.purchase_tree.insert("", "end", values=(
                purchase.id,
                purchase.order_number,
                purchase.vendor_name,
                purchase.date,
                f"${total:.2f}",
                status
            ), tags=(row_tag, status_tag))

    def view_purchase_details(self):
        """View details of selected purchase"""
        selected_item = self.purchase_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No purchase selected")
            return

        item_id = self.purchase_tree.item(selected_item, "values")[0]
        purchase = self.controllers["purchase"].get_purchase_by_id(item_id)

        if not purchase:
            messagebox.showerror("Error", "Purchase not found")
            return

        # Create a new window for details
        details_window = tk.Toplevel(self.parent)
        details_window.title(f"Purchase Details - Order #{purchase.order_number}")
        details_window.geometry("800x600")
        details_window.minsize(800, 600)

        # Main frame
        main_frame = tk.Frame(details_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Purchase header
        header_frame = tk.Frame(main_frame)
        header_frame.pack(fill=tk.X)

        tk.Label(header_frame, text=f"Order #{purchase.order_number}",
                 font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=5)

        info_frame = tk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=10)

        # Purchase info
        info_fields = [
            ("Date:", purchase.date),
            ("Vendor:", purchase.vendor_name),
            ("Invoice #:", purchase.invoice_number or "Not Available"),
            ("Status:", purchase.get_status())
        ]

        for i, (label, value) in enumerate(info_fields):
            tk.Label(info_frame, text=label, font=("Arial", 11, "bold")).grid(row=i, column=0, sticky="w", pady=3)
            tk.Label(info_frame, text=value).grid(row=i, column=1, sticky="w", pady=3)

        # Budget allocations
        budget_frame = tk.Frame(main_frame)
        budget_frame.pack(fill=tk.X, pady=10)

        tk.Label(budget_frame, text="Budget Allocations:", font=("Arial", 11, "bold")).pack(anchor="w")

        for budget_alloc in purchase.budgets:
            budget_id = budget_alloc.get("budget_id")
            budget = self.controllers["budget"].get_budget_by_id(budget_id)
            budget_name = budget.name if budget else "Unknown Budget"

            tk.Label(budget_frame, text=f"• {budget_name}: ${budget_alloc.get('amount', 0):.2f}").pack(
                anchor="w", padx=20)

        # Line items
        lines_frame = tk.Frame(main_frame)
        lines_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        tk.Label(lines_frame, text="Line Items:", font=("Arial", 11, "bold")).pack(anchor="w")

        # Create treeview for line items
        columns = ("Item", "Description", "Quantity", "Unit Price", "Total", "Received")
        lines_tree = ttk.Treeview(lines_frame, columns=columns, show="headings")

        # Set column headings
        for col in columns:
            lines_tree.heading(col, text=col)

        lines_tree.column("Item", width=50)
        lines_tree.column("Description", width=200)
        lines_tree.column("Quantity", width=70)
        lines_tree.column("Unit Price", width=100)
        lines_tree.column("Total", width=100)
        lines_tree.column("Received", width=80)

        # Apply styling
        lines_tree = configure_treeview(lines_tree)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(lines_frame, orient="vertical", command=lines_tree.yview)
        lines_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        lines_tree.pack(fill="both", expand=True)

        # Insert line items
        for i, item in enumerate(purchase.line_items):
            total = item.get("quantity", 0) * item.get("unit_price", 0)
            received = "Yes" if item.get("received", False) else "No"

            row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            
            lines_tree.insert("", "end", values=(
                i + 1,
                item.get("description", ""),
                item.get("quantity", 0),
                f"${item.get('unit_price', 0):.2f}",
                f"${total:.2f}",
                received
            ), tags=(row_tag,))

        # Total
        total_frame = tk.Frame(main_frame)
        total_frame.pack(fill=tk.X, pady=10)

        tk.Label(total_frame, text="Total Amount:", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        tk.Label(total_frame, text=f"${purchase.get_total():.2f}",
                 font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=10)

        # Close button
        tk.Button(main_frame, text="Close", command=details_window.destroy).pack(pady=10)

    def add_purchase(self):
        """Open form to add a new purchase"""
        purchase_form = PurchaseFormView(self.parent, self.controllers, self.show_view)
        self.show_view(purchase_form)

    def edit_purchase(self):
        """Edit selected purchase"""
        selected_item = self.purchase_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No purchase selected")
            return

        item_id = self.purchase_tree.item(selected_item, "values")[0]
        purchase = self.controllers["purchase"].get_purchase_by_id(item_id)

        if not purchase:
            messagebox.showerror("Error", "Purchase not found")
            return

        purchase_form = PurchaseFormView(self.parent, self.controllers, self.show_view, purchase)
        self.show_view(purchase_form)

    def delete_purchase(self):
        """Delete selected purchase"""
        selected_item = self.purchase_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No purchase selected")
            return

        item_id = self.purchase_tree.item(selected_item, "values")[0]

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this purchase?"):
            self.controllers["purchase"].delete_purchase(item_id)
            messagebox.showinfo("Success", "Purchase deleted successfully")
            self.refresh_purchase_list()

    def receive_items(self):
        """Open receive items dialog for selected purchase"""
        selected_item = self.purchase_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No purchase selected")
            return

        item_id = self.purchase_tree.item(selected_item, "values")[0]
        purchase = self.controllers["purchase"].get_purchase_by_id(item_id)

        if not purchase:
            messagebox.showerror("Error", "Purchase not found")
            return

        # Create a new window for receiving
        receive_window = tk.Toplevel(self.parent)
        receive_window.title(f"Receive Items - Order #{purchase.order_number}")
        receive_window.geometry("700x500")
        receive_window.minsize(700, 500)

        # Main frame
        main_frame = tk.Frame(receive_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Title
        tk.Label(main_frame, text=f"Receive Items for Order #{purchase.order_number}",
                 font=("Arial", 14, "bold")).pack(pady=10)

        # Line items frame
        items_frame = tk.Frame(main_frame)
        items_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Create treeview for line items
        columns = ("Item", "Description", "Quantity", "Received")
        items_tree = ttk.Treeview(items_frame, columns=columns, show="headings")

        # Set column headings
        for col in columns:
            items_tree.heading(col, text=col)

        items_tree.column("Item", width=50)
        items_tree.column("Description", width=300)
        items_tree.column("Quantity", width=70)
        items_tree.column("Received", width=80)

        # Apply styling
        items_tree = configure_treeview(items_tree)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(items_frame, orient="vertical", command=items_tree.yview)
        items_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        items_tree.pack(fill="both", expand=True)

        # Insert line items
        for i, item in enumerate(purchase.line_items):
            received = "Yes" if item.get("received", False) else "No"
            row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            status_tag = 'approved' if item.get("received", False) else 'pending'

            items_tree.insert("", "end", values=(
                i,  # Store index as item ID
                item.get("description", ""),
                item.get("quantity", 0),
                received
            ), tags=(row_tag, status_tag))

        # Buttons frame
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        def mark_received():
            selected = items_tree.selection()
            if not selected:
                messagebox.showerror("Error", "No item selected")
                return

            indices = [int(items_tree.item(item, "values")[0]) for item in selected]
            self.controllers["purchase"].receive_items(purchase.id, indices, True)

            # Update display
            for item in selected:
                idx = int(items_tree.item(item, "values")[0])
                items_tree.item(item, values=(
                    idx,
                    purchase.line_items[idx]["description"],
                    purchase.line_items[idx]["quantity"],
                    "Yes"
                ), tags=('evenrow' if idx % 2 == 0 else 'oddrow', 'approved'))

            messagebox.showinfo("Success", "Items marked as received")

            # Refresh main list view to show updated status
            self.refresh_purchase_list()

        def mark_not_received():
            selected = items_tree.selection()
            if not selected:
                messagebox.showerror("Error", "No item selected")
                return

            indices = [int(items_tree.item(item, "values")[0]) for item in selected]
            self.controllers["purchase"].receive_items(purchase.id, indices, False)

            # Update display
            for item in selected:
                idx = int(items_tree.item(item, "values")[0])
                items_tree.item(item, values=(
                    idx,
                    purchase.line_items[idx]["description"],
                    purchase.line_items[idx]["quantity"],
                    "No"
                ), tags=('evenrow' if idx % 2 == 0 else 'oddrow', 'pending'))

            messagebox.showinfo("Success", "Items marked as not received")

            # Refresh main list view to show updated status
            self.refresh_purchase_list()

        def receive_all():
            indices = list(range(len(purchase.line_items)))
            self.controllers["purchase"].receive_items(purchase.id, indices, True)

            # Update display
            for i, item in enumerate(items_tree.get_children()):
                idx = int(items_tree.item(item, "values")[0])
                items_tree.item(item, values=(
                    idx,
                    purchase.line_items[idx]["description"],
                    purchase.line_items[idx]["quantity"],
                    "Yes"
                ), tags=('evenrow' if idx % 2 == 0 else 'oddrow', 'approved'))

            messagebox.showinfo("Success", "All items marked as received")

            # Refresh main list view to show updated status
            self.refresh_purchase_list()

        tk.Button(button_frame, text="Mark as Received", command=mark_received).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Mark as Not Received", command=mark_not_received).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Receive All Items", command=receive_all).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Close", command=receive_window.destroy).pack(side=tk.RIGHT, padx=5)

    def export_purchases(self):
        """Export purchases to CSV file"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Purchases to CSV"
        )

        if not file_path:
            return

        # Get purchases
        purchases = self.controllers["purchase"].get_all_purchases()

        # Export to CSV
        success, message = CSVExporter.export_purchases(purchases, file_path)

        if success:
            messagebox.showinfo("Export Successful", message)
        else:
            messagebox.showerror("Export Failed", message)

    def return_to_dashboard(self):
        """Return to main dashboard"""
        from views.main_dashboard import MainDashboard
        dashboard = MainDashboard(self.parent, self.controllers, self.show_view)
        self.show_view(dashboard)

    def show(self):
        """Show this view"""
        self.refresh_purchase_list()
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """Hide this view"""
        self.frame.pack_forget()


class PurchaseFormView:
    def __init__(self, parent, controllers, show_view_callback, purchase=None):
        self.parent = parent
        self.controllers = controllers
        self.show_view = show_view_callback
        self.purchase = purchase  # Purchase to edit, or None for new purchase
        self.is_edit = purchase is not None

        self.frame = tk.Frame(parent)
        self.setup_ui()

    def setup_ui(self):
        # Create back button
        back_button = tk.Button(self.frame, text="Back to Purchase List",
                                command=self.return_to_purchase_list)
        back_button.pack(anchor="nw", padx=10, pady=10)

        # Define form styling variables
        form_padding = {'padx': 15, 'pady': 8}
        label_style = {'font': ('Arial', 10), 'anchor': 'w'}

        # Create scrollable canvas
        canvas = tk.Canvas(self.frame)
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=canvas.yview)

        form_frame = tk.Frame(canvas)

        # Configure scrolling
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas.create_window((0, 0), window=form_frame, anchor="nw")

        form_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Title
        title = "Edit Purchase" if self.is_edit else "Add New Purchase"
        tk.Label(form_frame, text=title, font=("Arial", 14, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=10)

        # Purchase info section with better visual hierarchy
        info_frame = tk.LabelFrame(form_frame, text="Purchase Information", 
                                 font=('Arial', 11, 'bold'), padx=15, pady=10)
        info_frame.grid(row=1, column=0, columnspan=3, sticky="ew", 
                      padx=10, pady=15)

        # Order number
        tk.Label(info_frame, text="Order Number:", **label_style).grid(
            row=0, column=0, sticky="w", **form_padding)
        self.order_number_var = tk.StringVar(value=self.purchase.order_number if self.is_edit else "")
        order_entry = tk.Entry(info_frame, textvariable=self.order_number_var, width=20)
        order_entry.grid(row=0, column=1, sticky="w", **form_padding)

        # Invoice number
        tk.Label(info_frame, text="Invoice Number:", **label_style).grid(row=0, column=2, sticky="w", **form_padding)
        self.invoice_number_var = tk.StringVar(value=self.purchase.invoice_number if self.is_edit else "")
        invoice_entry = tk.Entry(info_frame, textvariable=self.invoice_number_var, width=20)
        invoice_entry.grid(row=0, column=3, sticky="w", **form_padding)

        # Date
        tk.Label(info_frame, text="Date:", **label_style).grid(row=1, column=0, sticky="w", **form_padding)
        self.date_var = tk.StringVar(
            value=self.purchase.date if self.is_edit else datetime.now().strftime("%Y-%m-%d"))
        date_entry = tk.Entry(info_frame, textvariable=self.date_var, width=20)
        date_entry.grid(row=1, column=1, sticky="w", **form_padding)

        # Vendor
        tk.Label(info_frame, text="Vendor:", **label_style).grid(row=1, column=2, sticky="w", **form_padding)

        vendor_names = self.controllers["vendor"].get_vendor_names()
        self.vendor_var = tk.StringVar()

        if self.is_edit and self.purchase.vendor_name in vendor_names:
            self.vendor_var.set(self.purchase.vendor_name)
        elif vendor_names:
            self.vendor_var.set(vendor_names[0])

        vendor_dropdown = ttk.Combobox(info_frame, textvariable=self.vendor_var, values=vendor_names, width=20)
        vendor_dropdown.grid(row=1, column=3, sticky="w", **form_padding)

        if not vendor_names:
            vendor_dropdown["state"] = "disabled"
            tk.Label(info_frame, text="(No vendors available. Please add vendors first.)",
                     fg="red").grid(row=2, column=2, columnspan=2, sticky="w", padx=5)

        # Add new vendor button
        tk.Button(info_frame, text="Add New Vendor", command=self.add_new_vendor).grid(
            row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        # Line items section
        items_frame = tk.LabelFrame(form_frame, text="Line Items", font=('Arial', 11, 'bold'), padx=15, pady=10)
        items_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=10, pady=15)

        # Line items container (for dynamically adding items)
        self.lines_container = tk.Frame(items_frame)
        self.lines_container.pack(fill=tk.X, padx=5, pady=5)

        self.line_items = []

        # Add existing line items if editing
        if self.is_edit and self.purchase.line_items:
            for item in self.purchase.line_items:
                self.add_line_item_row(item)
        else:
            # Add one empty row for new purchase
            self.add_line_item_row()

        # Add line item button
        add_item_btn = tk.Button(items_frame, text="Add Another Line Item",
                                 command=lambda: self.add_line_item_row())
        add_item_btn.pack(anchor="w", padx=5, pady=5)

        # Budget allocation section
        budget_frame = tk.LabelFrame(form_frame, text="Budget Allocation", font=('Arial', 11, 'bold'), padx=15, pady=10)
        budget_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=10, pady=15)

        self.budget_container = tk.Frame(budget_frame)
        self.budget_container.pack(fill=tk.X, padx=5, pady=5)

        self.budget_allocations = []

        # Get budget options
        self.budget_options = self.controllers["budget"].get_budget_options()

        if not self.budget_options:
            tk.Label(budget_frame, text="No budgets available. Please add budgets first.",
                     fg="red").pack(anchor="w", padx=5)
        else:
            # Add existing budget allocations if editing
            if self.is_edit and self.purchase.budgets:
                for budget in self.purchase.budgets:
                    self.add_budget_row(budget)
            else:
                # Add one empty row for new purchase
                self.add_budget_row()

            # Add budget button
            add_budget_btn = tk.Button(budget_frame, text="Add Another Budget",
                                       command=lambda: self.add_budget_row())
            add_budget_btn.pack(anchor="w", padx=5, pady=5)

        # Buttons
        buttons_frame = tk.Frame(form_frame)
        buttons_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=10, pady=20)

        tk.Button(buttons_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=5)
        save_text = "Save Changes" if self.is_edit else "Save Purchase"
        tk.Button(buttons_frame, text=save_text, command=self.save_purchase_data).pack(side=tk.RIGHT, padx=5)

    def add_new_vendor(self):
        """Add a new vendor"""
        from tkinter import simpledialog
        vendor_name = simpledialog.askstring("New Vendor", "Enter vendor name:")
        if not vendor_name:
            return

        # Create and add new vendor
        from models.vendor import Vendor
        new_vendor = Vendor(name=vendor_name)

        success, message = self.controllers["vendor"].add_vendor(new_vendor)

        if success:
            # Refresh vendor dropdown
            vendor_names = self.controllers["vendor"].get_vendor_names()

            # Find the vendor dropdown
            for widget in self.frame.winfo_children():
                if isinstance(widget, tk.Canvas):
                    canvas = widget
                    form_frame = canvas.children[list(canvas.children.keys())[0]]
                    info_frame = None

                    for child in form_frame.winfo_children():
                        if isinstance(child, tk.LabelFrame) and child.cget("text") == "Purchase Information":
                            info_frame = child
                            break

                    if info_frame:
                        for child in info_frame.winfo_children():
                            if isinstance(child, ttk.Combobox):
                                child["values"] = vendor_names
                                child.current(vendor_names.index(vendor_name))
                                break

                    break

            self.vendor_var.set(vendor_name)
            messagebox.showinfo("Success", "Vendor added successfully")
        else:
            messagebox.showerror("Error", message)

    def add_line_item_row(self, item=None):
        """Add a new line item row"""
        row_frame = tk.Frame(self.lines_container, padx=5, pady=5, bd=1, relief=tk.GROOVE)
        row_frame.pack(fill=tk.X, pady=5)

        # Line item fields
        tk.Label(row_frame, text="Description:", font=('Arial', 10)).grid(row=0, column=0, sticky="w", padx=5)
        description_var = tk.StringVar(value=item.get("description", "") if item else "")
        description_entry = tk.Entry(row_frame, textvariable=description_var, width=30)
        description_entry.grid(row=0, column=1, sticky="w", padx=5)

        tk.Label(row_frame, text="Quantity:", font=('Arial', 10)).grid(row=0, column=2, sticky="w", padx=5)
        quantity_var = tk.StringVar(value=str(item.get("quantity", 1)) if item else "1")
        quantity_entry = tk.Entry(row_frame, textvariable=quantity_var, width=8)
        quantity_entry.grid(row=0, column=3, sticky="w", padx=5)

        tk.Label(row_frame, text="Unit Price:", font=('Arial', 10)).grid(row=0, column=4, sticky="w", padx=5)
        price_var = tk.StringVar(value=str(item.get("unit_price", 0.0)) if item else "0.00")
        price_entry = tk.Entry(row_frame, textvariable=price_var, width=10)
        price_entry.grid(row=0, column=5, sticky="w", padx=5)

        # Calculate total
        def calculate_total(*args):
            try:
                quantity = int(quantity_var.get())
                price = float(price_var.get())
                total = quantity * price
                total_var.set(f"${total:.2f}")
            except ValueError:
                total_var.set("$0.00")

        tk.Label(row_frame, text="Total:", font=('Arial', 10)).grid(row=0, column=6, sticky="w", padx=5)
        total_var = tk.StringVar(
            value=f"${item.get('quantity', 1) * item.get('unit_price', 0.0):.2f}" if item else "$0.00")
        total_label = tk.Label(row_frame, textvariable=total_var)
        total_label.grid(row=0, column=7, sticky="w", padx=5)

        # Bind events to calculate total
        quantity_var.trace_add("write", calculate_total)
        price_var.trace_add("write", calculate_total)

        # Received status (for edit mode)
        received_var = tk.BooleanVar(value=item.get("received", False) if item else False)
        received_cb = tk.Checkbutton(row_frame, text="Received", variable=received_var)
        received_cb.grid(row=0, column=8, sticky="w", padx=5)

        # Remove button
        def remove_row():
            row_frame.destroy()
            self.line_items.remove(item_dict)

        remove_btn = tk.Button(row_frame, text="✖", command=remove_row, bd=0, fg="red", font=("Arial", 10, "bold"))
        remove_btn.grid(row=0, column=9, sticky="w", padx=5)

        # Store references to variables
        item_dict = {
            "row_frame": row_frame,
            "description_var": description_var,
            "quantity_var": quantity_var,
            "price_var": price_var,
            "total_var": total_var,
            "received_var": received_var
        }

        self.line_items.append(item_dict)
        return item_dict

    def add_budget_row(self, budget_allocation=None):
        """Add a new budget allocation row"""
        if not self.budget_options:
            return None

        row_frame = tk.Frame(self.budget_container, padx=5, pady=5, bd=1, relief=tk.GROOVE)
        row_frame.pack(fill=tk.X, pady=5)

        # Budget selection
        budget_id_var = tk.StringVar()
        budget_name_var = tk.StringVar()

        # Set initial values if editing
        if budget_allocation:
            budget_id = budget_allocation.get("budget_id")
            budget_name = next((name for bid, name in self.budget_options if bid == budget_id), "")
            budget_id_var.set(budget_id)
            budget_name_var.set(budget_name)
            amount = budget_allocation.get("amount", 0.0)
        else:
            # Default to first budget
            budget_id_var.set(self.budget_options[0][0])
            budget_name_var.set(self.budget_options[0][1])
            amount = 0.0

        def update_budget_name(*args):
            selected_id = budget_id_var.get()
            selected_name = next((name for bid, name in self.budget_options if bid == selected_id), "")
            budget_name_var.set(selected_name)

        budget_id_var.trace_add("write", update_budget_name)

        # Budget dropdown
        tk.Label(row_frame, text="Budget:", font=('Arial', 10)).grid(row=0, column=0, sticky="w", padx=5)
        budget_menu = ttk.Combobox(row_frame, textvariable=budget_name_var, width=25)
        budget_menu["values"] = [name for _, name in self.budget_options]
        budget_menu.grid(row=0, column=1, sticky="w", padx=5)

        # When selection changes, update the hidden ID variable
        def on_budget_select(event):
            selected_name = budget_name_var.get()
            selected_id = next((bid for bid, name in self.budget_options if name == selected_name), None)
            if selected_id:
                budget_id_var.set(selected_id)

        budget_menu.bind("<<ComboboxSelected>>", on_budget_select)

        # Amount
        tk.Label(row_frame, text="Amount:", font=('Arial', 10)).grid(row=0, column=2, sticky="w", padx=5)
        amount_var = tk.StringVar(value=str(amount))
        amount_entry = tk.Entry(row_frame, textvariable=amount_var, width=15)
        amount_entry.grid(row=0, column=3, sticky="w", padx=5)

        # Remove button
        def remove_row():
            row_frame.destroy()
            self.budget_allocations.remove(budget_dict)

        remove_btn = tk.Button(row_frame, text="✖", command=remove_row, bd=0, fg="red", font=("Arial", 10, "bold"))
        remove_btn.grid(row=0, column=4, sticky="w", padx=5)

        # Store references
        budget_dict = {
            "row_frame": row_frame,
            "budget_id_var": budget_id_var,
            "amount_var": amount_var
        }

        self.budget_allocations.append(budget_dict)
        return budget_dict

    def cancel(self):
        """Cancel form and return to purchase list"""
        if messagebox.askyesno("Cancel", "Are you sure you want to cancel? Any unsaved changes will be lost."):
            self.return_to_purchase_list()

    def save_purchase_data(self):
        """Save purchase data"""
        try:
            # Validate input
            order_number = self.order_number_var.get().strip()
            if not order_number:
                raise ValueError("Order number is required")

            date = self.date_var.get().strip()
            if not date:
                raise ValueError("Date is required")

            vendor_name = self.vendor_var.get()
            if not vendor_name:
                raise ValueError("Vendor is required")

            # Get vendor ID
            vendor_id = None
            for vendor in self.controllers["vendor"].get_all_vendors():
                if vendor.name == vendor_name:
                    vendor_id = vendor.id
                    break

            if not vendor_id:
                raise ValueError("Selected vendor not found")

            # Validate line items
            if not self.line_items:
                raise ValueError("At least one line item is required")

            parsed_items = []
            for item in self.line_items:
                description = item["description_var"].get().strip()
                if not description:
                    raise ValueError("Line item description is required")

                try:
                    quantity = int(item["quantity_var"].get())
                    if quantity <= 0:
                        raise ValueError
                except ValueError:
                    raise ValueError("Quantity must be a positive integer")

                try:
                    unit_price = float(item["price_var"].get())
                    if unit_price < 0:
                        raise ValueError
                except ValueError:
                    raise ValueError("Unit price must be a valid number")

                parsed_items.append({
                    "description": description,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "received": item["received_var"].get()
                })

            # Validate budget allocations
            parsed_budgets = []
            for budget in self.budget_allocations:
                budget_id = budget["budget_id_var"].get()

                try:
                    amount = float(budget["amount_var"].get())
                    if amount <= 0:
                        raise ValueError
                except ValueError:
                    raise ValueError("Budget amount must be a positive number")

                parsed_budgets.append({
                    "budget_id": budget_id,
                    "amount": amount
                })

            # Check if total budget allocation matches total purchase amount
            total_purchase = sum(item["quantity"] * item["unit_price"] for item in parsed_items)
            total_budget = sum(budget["amount"] for budget in parsed_budgets)

            if abs(total_purchase - total_budget) > 0.01:  # Allow for small floating point differences
                raise ValueError(
                    f"Total budget allocation (${total_budget:.2f}) must match total purchase amount (${total_purchase:.2f})")

            # Create or update purchase object
            if self.is_edit:
                # Update existing purchase
                self.purchase.order_number = order_number
                self.purchase.invoice_number = self.invoice_number_var.get().strip()
                self.purchase.date = date
                self.purchase.vendor_id = vendor_id
                self.purchase.vendor_name = vendor_name
                self.purchase.line_items = parsed_items
                self.purchase.budgets = parsed_budgets

                self.controllers["purchase"].update_purchase(self.purchase)
                message = "Purchase updated successfully"
            else:
                # Create new purchase
                from models.purchase import Purchase
                new_purchase = Purchase(
                    order_number=order_number,
                    invoice_number=self.invoice_number_var.get().strip(),
                    date=date,
                    vendor_id=vendor_id,
                    vendor_name=vendor_name,
                    line_items=parsed_items,
                    budgets=parsed_budgets
                )

                self.controllers["purchase"].add_purchase(new_purchase)
                message = "Purchase added successfully"

            messagebox.showinfo("Success", message)
            self.return_to_purchase_list()

        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))

    def return_to_purchase_list(self):
        """Return to purchase list view"""
        purchase_list = PurchaseListView(self.parent, self.controllers, self.show_view)
        self.show_view(purchase_list)

    def show(self):
        """Show this view"""
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """Hide this view"""
        self.frame.pack_forget()