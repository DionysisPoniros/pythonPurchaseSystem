import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from database.models import Purchase, Vendor, LineItem, PurchaseBudget
import uuid
from utils.exporters import CSVExporter
from utils.table_utils import configure_treeview
# ***** Added import line below *****
from views.view_factory import ViewFactory


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

        # Populate the list initially
        self.refresh_purchase_list()


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
            # Handle potential None values or type mismatches during sort
            try:
                if self.sort_column == "Order #":
                    purchases.sort(key=lambda x: x.order_number or '', reverse=self.sort_reverse)
                elif self.sort_column == "Vendor":
                    purchases.sort(key=lambda x: x.vendor_name or '', reverse=self.sort_reverse)
                elif self.sort_column == "Date":
                    purchases.sort(key=lambda x: x.date or '', reverse=self.sort_reverse)
                elif self.sort_column == "Total":
                    purchases.sort(key=lambda x: x.get_total() or 0.0, reverse=self.sort_reverse)
                elif self.sort_column == "Status":
                    purchases.sort(key=lambda x: x.get_status() or '', reverse=self.sort_reverse)
            except Exception as e:
                print(f"Error sorting purchases: {e}") # Log error, continue without sorting


        # Insert purchase data into treeview
        for i, purchase in enumerate(purchases):
            try:
                total = purchase.get_total()
                status = purchase.get_status()
            except Exception as e:
                print(f"Error processing purchase {purchase.id} for display: {e}")
                total = 0.0 # Default values on error
                status = "Error"


            row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            # Add status tag
            if status == "Pending":
                status_tag = 'pending'
            elif status == "Partial":
                status_tag = 'partial'
            else: # Received or Error
                status_tag = 'approved'

            self.purchase_tree.insert("", "end", values=(
                purchase.id or "N/A",
                purchase.order_number or "N/A",
                purchase.vendor_name or "N/A",
                purchase.date or "N/A",
                f"${total:.2f}",
                status
            ), tags=(row_tag, status_tag))

    def filter_by_status(self, status_filter):
        """Filter purchases by status"""
        self.purchase_tree.delete(*self.purchase_tree.get_children())

        # Get all purchases
        purchases = self.controllers["purchase"].get_all_purchases()
        filtered = []

        if status_filter == "All":
            filtered = purchases
        else:
            for purchase in purchases:
                try:
                    purchase_status = purchase.get_status()
                    if status_filter == purchase_status:
                        filtered.append(purchase)
                except Exception as e:
                     print(f"Error getting status for purchase {purchase.id} during filter: {e}")

        # Display filtered purchases
        for i, purchase in enumerate(filtered):
            try:
                total = purchase.get_total()
                status_text = purchase.get_status()
            except Exception as e:
                print(f"Error processing purchase {purchase.id} for display: {e}")
                total = 0.0 # Default values on error
                status_text = "Error"

            row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            # Add status tag
            if status_text == "Pending":
                status_tag = 'pending'
            elif status_text == "Partial":
                status_tag = 'partial'
            else: # Received or Error
                status_tag = 'approved'

            self.purchase_tree.insert("", "end", values=(
                purchase.id or "N/A",
                purchase.order_number or "N/A",
                purchase.vendor_name or "N/A",
                purchase.date or "N/A",
                f"${total:.2f}",
                status_text
            ), tags=(row_tag, status_tag))

    def perform_search(self):
        """Search purchases based on criteria"""
        search_text = self.search_var.get().lower().strip()
        search_field = self.search_option_var.get()

        if not search_text:
            self.refresh_purchase_list()
            return

        # Get all purchases
        all_purchases = self.controllers["purchase"].get_all_purchases()
        filtered_purchases = []

        for purchase in all_purchases:
            try:
                match = False
                order_num = (purchase.order_number or "").lower()
                vendor_name = (purchase.vendor_name or "").lower()
                date_str = (purchase.date or "").lower()
                status_str = (purchase.get_status() or "").lower()

                if search_field == "All Fields":
                    # Search all relevant fields
                    if (search_text in order_num or
                        search_text in vendor_name or
                        search_text in date_str or
                        search_text in status_str):
                         match = True
                elif search_field == "Order #" and search_text in order_num:
                    match = True
                elif search_field == "Vendor" and search_text in vendor_name:
                    match = True
                elif search_field == "Date" and search_text in date_str:
                     match = True
                elif search_field == "Status" and search_text in status_str:
                    match = True

                if match:
                    filtered_purchases.append(purchase)
            except Exception as e:
                print(f"Error during search processing for purchase {purchase.id}: {e}")


        # Sort filtered purchases (reuse sorting logic from refresh_purchase_list)
        if self.sort_column:
             # Handle potential None values or type mismatches during sort
            try:
                if self.sort_column == "Order #":
                    filtered_purchases.sort(key=lambda x: x.order_number or '', reverse=self.sort_reverse)
                elif self.sort_column == "Vendor":
                    filtered_purchases.sort(key=lambda x: x.vendor_name or '', reverse=self.sort_reverse)
                elif self.sort_column == "Date":
                    filtered_purchases.sort(key=lambda x: x.date or '', reverse=self.sort_reverse)
                elif self.sort_column == "Total":
                    filtered_purchases.sort(key=lambda x: x.get_total() or 0.0, reverse=self.sort_reverse)
                elif self.sort_column == "Status":
                    filtered_purchases.sort(key=lambda x: x.get_status() or '', reverse=self.sort_reverse)
            except Exception as e:
                print(f"Error sorting search results: {e}") # Log error, continue without sorting


        # Display filtered results
        self.purchase_tree.delete(*self.purchase_tree.get_children())

        for i, purchase in enumerate(filtered_purchases):
            try:
                total = purchase.get_total()
                status = purchase.get_status()
            except Exception as e:
                print(f"Error processing purchase {purchase.id} for display: {e}")
                total = 0.0 # Default values on error
                status = "Error"

            row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            # Add status tag
            if status == "Pending":
                status_tag = 'pending'
            elif status == "Partial":
                status_tag = 'partial'
            else: # Received or Error
                status_tag = 'approved'

            self.purchase_tree.insert("", "end", values=(
                purchase.id or "N/A",
                purchase.order_number or "N/A",
                purchase.vendor_name or "N/A",
                purchase.date or "N/A",
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
        # Use the controller which now eager loads relationships
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
            ("Date:", purchase.date or "N/A"),
            ("Vendor:", purchase.vendor_name or "N/A"), # Use vendor_name from purchase
            ("Invoice #:", purchase.invoice_number or "Not Available"),
            ("Status:", purchase.get_status() or "N/A"),
            ("Approval:", f"{purchase.status or 'N/A'} by {purchase.approver or 'N/A'} on {purchase.approval_date or 'N/A'}") # Added Approval Info
        ]

        for i, (label, value) in enumerate(info_fields):
            tk.Label(info_frame, text=label, font=("Arial", 11, "bold")).grid(row=i, column=0, sticky="w", pady=3)
            tk.Label(info_frame, text=value).grid(row=i, column=1, sticky="w", pady=3)

        # Budget allocations - Access via loaded relationships
        budget_frame = tk.Frame(main_frame)
        budget_frame.pack(fill=tk.X, pady=10)

        tk.Label(budget_frame, text="Budget Allocations:", font=("Arial", 11, "bold")).pack(anchor="w")

        if purchase.budgets:
             for budget_alloc in purchase.budgets:
                 # Use budget_alloc.budget.name and budget_alloc.amount
                 budget_name = budget_alloc.budget.name if budget_alloc.budget else "Unknown Budget"
                 tk.Label(budget_frame, text=f"• {budget_name}: ${budget_alloc.amount:.2f}").pack(
                     anchor="w", padx=20)
        else:
             tk.Label(budget_frame, text="No budget allocations.").pack(anchor="w", padx=20)


        # Line items - Access via loaded relationship
        lines_frame = tk.Frame(main_frame)
        lines_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        tk.Label(lines_frame, text="Line Items:", font=("Arial", 11, "bold")).pack(anchor="w")

        # Create treeview for line items
        columns = ("Item", "Description", "Quantity", "Unit Price", "Total", "Received")
        lines_tree = ttk.Treeview(lines_frame, columns=columns, show="headings") # Corrected parent to lines_frame


        # Set column headings
        for col in columns:
            lines_tree.heading(col, text=col)

        lines_tree.column("Item", width=50, anchor="center")
        lines_tree.column("Description", width=300)
        lines_tree.column("Quantity", width=70, anchor="e")
        lines_tree.column("Unit Price", width=100, anchor="e")
        lines_tree.column("Total", width=100, anchor="e")
        lines_tree.column("Received", width=80, anchor="center")

        # Apply styling
        lines_tree = configure_treeview(lines_tree)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(lines_frame, orient="vertical", command=lines_tree.yview)
        lines_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        lines_tree.pack(fill="both", expand=True)

        # Insert line items - Access via loaded relationship
        if purchase.line_items:
             for i, item in enumerate(purchase.line_items):
                 # item is now a LineItem object
                 total = item.quantity * item.unit_price
                 received = "Yes" if item.received else "No"
                 row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'

                 lines_tree.insert("", "end", values=(
                     i + 1,
                     item.description or "",
                     item.quantity or 0,
                     f"${item.unit_price:.2f}",
                     f"${total:.2f}",
                     received
                 ), tags=(row_tag,))
        else:
             # Optionally display a message if no line items
             lines_tree.insert("", "end", values=("", "No line items found.", "", "", "", ""))


        # Total
        total_frame = tk.Frame(main_frame)
        total_frame.pack(fill=tk.X, pady=10)

        tk.Label(total_frame, text="Total Amount:", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        tk.Label(total_frame, text=f"${purchase.get_total():.2f}",
                 font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=10)

        # Close button
        tk.Button(main_frame, text="Close", command=details_window.destroy).pack(pady=10)

    def add_purchase(self):
        """Open form to add a new purchase using ViewFactory"""
        # Corrected to use ViewFactory
        purchase_form = ViewFactory.create_view('PurchaseFormView', self.parent, self.controllers, self.show_view)
        self.show_view(purchase_form)

    def edit_purchase(self):
        """Edit selected purchase using ViewFactory"""
        selected_item = self.purchase_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No purchase selected")
            return

        item_id = self.purchase_tree.item(selected_item, "values")[0]
        purchase = self.controllers["purchase"].get_purchase_by_id(item_id)

        if not purchase:
            messagebox.showerror("Error", "Purchase not found")
            return

        # Corrected to use ViewFactory
        purchase_form = ViewFactory.create_view('PurchaseFormView', self.parent, self.controllers, self.show_view, purchase=purchase)
        self.show_view(purchase_form)


    def delete_purchase(self):
        """Delete selected purchase"""
        selected_item = self.purchase_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No purchase selected")
            return

        item_id = self.purchase_tree.item(selected_item, "values")[0]

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this purchase? This cannot be undone."):
             # Ensure delete_purchase returns success status
             success, message = self.controllers["purchase"].delete_purchase(item_id)
             if success:
                  messagebox.showinfo("Success", message)
                  self.refresh_purchase_list() # Refresh list after successful deletion
             else:
                  messagebox.showerror("Error", message)


    def receive_items(self):
        """Open receive items dialog for selected purchase"""
        selected_item = self.purchase_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No purchase selected")
            return

        item_id = self.purchase_tree.item(selected_item, "values")[0]
        # Fetch purchase with loaded line items
        purchase = self.controllers["purchase"].get_purchase_by_id(item_id)


        if not purchase:
            messagebox.showerror("Error", "Purchase not found")
            return

        # Create a new window for receiving
        receive_window = tk.Toplevel(self.parent)
        receive_window.title(f"Receive Items - Order #{purchase.order_number}")
        receive_window.geometry("700x500")
        receive_window.minsize(700, 500)
        receive_window.transient(self.parent) # Make it modal
        receive_window.grab_set()


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
        columns = ("Index", "Description", "Quantity", "Received") # Added Index
        items_tree = ttk.Treeview(items_frame, columns=columns, show="headings")


        # Set column headings
        for col in columns:
            items_tree.heading(col, text=col)

        items_tree.column("Index", width=50, stretch=tk.NO, anchor="center") # Hide index later if needed
        items_tree.column("Description", width=300)
        items_tree.column("Quantity", width=70, anchor="e")
        items_tree.column("Received", width=80, anchor="center")


        # Apply styling
        items_tree = configure_treeview(items_tree)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(items_frame, orient="vertical", command=items_tree.yview)
        items_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        items_tree.pack(fill="both", expand=True)

        # Store line item objects with their original index
        line_items_with_index = list(enumerate(purchase.line_items))


        # Insert line items using line_items_with_index
        for i, item in line_items_with_index:
            # item is now a LineItem object
            received = "Yes" if item.received else "No"
            row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            status_tag = 'approved' if item.received else 'pending'


            items_tree.insert("", "end", iid=str(i), values=( # Use original index as iid
                i, # Display original index
                item.description or "",
                item.quantity or 0,
                received
            ), tags=(row_tag, status_tag))


        # Buttons frame
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        def update_receive_status(receive_flag):
             selected_iids = items_tree.selection() # Get selected iids (original indices)
             if not selected_iids:
                  messagebox.showerror("Error", "No item selected", parent=receive_window)
                  return

             indices_to_update = [int(iid) for iid in selected_iids]

             success = self.controllers["purchase"].receive_items(purchase.id, indices_to_update, receive_flag)

             if success:
                  # Update display in the popup window
                  for iid in selected_iids:
                       idx = int(iid)
                       item_obj = line_items_with_index[idx][1] # Get the LineItem object
                       new_status = "Yes" if receive_flag else "No"
                       new_tag = 'approved' if receive_flag else 'pending'
                       row_tag = items_tree.item(iid, "tags")[0] # Keep original row tag

                       items_tree.item(iid, values=(
                            idx,
                            item_obj.description or "",
                            item_obj.quantity or 0,
                            new_status
                       ), tags=(row_tag, new_tag)) # Update tags

                  messagebox.showinfo("Success", f"Items marked as {'received' if receive_flag else 'not received'}", parent=receive_window)
                  # Refresh main list view AFTER the popup might be closed
                  self.refresh_purchase_list()
             else:
                  messagebox.showerror("Error", "Failed to update item status", parent=receive_window)


        def receive_all():
             all_indices = list(range(len(purchase.line_items)))
             success = self.controllers["purchase"].receive_items(purchase.id, all_indices, True)

             if success:
                 # Update display in the popup window
                 for iid in items_tree.get_children(): # Iterate through all items in tree
                      idx = int(iid)
                      item_obj = line_items_with_index[idx][1]
                      row_tag = items_tree.item(iid, "tags")[0] # Keep original row tag

                      items_tree.item(iid, values=(
                           idx,
                           item_obj.description or "",
                           item_obj.quantity or 0,
                           "Yes"
                      ), tags=(row_tag, 'approved')) # Update tags


                 messagebox.showinfo("Success", "All items marked as received", parent=receive_window)
                 # Refresh main list view AFTER the popup might be closed
                 self.refresh_purchase_list()
             else:
                 messagebox.showerror("Error", "Failed to receive all items", parent=receive_window)


        tk.Button(button_frame, text="Mark Selected as Received", command=lambda: update_receive_status(True)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Mark Selected as Not Received", command=lambda: update_receive_status(False)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Receive All Items", command=receive_all).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Close", command=receive_window.destroy).pack(side=tk.RIGHT, padx=5)


    def export_purchases(self):
        """Export purchases to CSV file"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="purchase_export.csv", # Suggest a filename
            title="Export Purchases to CSV"
        )

        if not file_path:
            return

        # Get purchases currently displayed (could be filtered/sorted)
        # For simplicity, exporting all purchases for now.
        # To export only displayed items:
        # displayed_ids = [self.purchase_tree.item(item, "values")[0] for item in self.purchase_tree.get_children()]
        # purchases_to_export = [p for p in self.controllers["purchase"].get_all_purchases() if p.id in displayed_ids]
        purchases_to_export = self.controllers["purchase"].get_all_purchases()


        # Export to CSV
        success, message = CSVExporter.export_purchases(purchases_to_export, file_path)

        if success:
            messagebox.showinfo("Export Successful", message)
        else:
            messagebox.showerror("Export Failed", message)

    def return_to_dashboard(self):
        """Return to main dashboard using ViewFactory"""
        # Corrected to use ViewFactory
        dashboard = ViewFactory.create_view('MainDashboard', self.parent, self.controllers, self.show_view)
        self.show_view(dashboard)


    def show(self):
        """Show this view"""
        self.refresh_purchase_list() # Refresh list when shown
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """Hide this view"""
        self.frame.pack_forget()


class PurchaseFormView:
    def __init__(self, parent, controllers, show_view_callback, purchase=None):
        self.parent = parent
        self.controllers = controllers
        self.show_view = show_view_callback
        self.db_manager = controllers["purchase"].db_manager
        self.purchase = purchase  # Purchase to edit, or None for new purchase
        # Fetch full purchase details if editing, ensuring relationships are loaded
        if self.purchase and hasattr(self.purchase, 'id'):
             self.purchase = self.controllers["purchase"].get_purchase_by_id(self.purchase.id)

        self.is_edit = self.purchase is not None


        self.frame = tk.Frame(parent)
        self.setup_ui()

    def setup_ui(self):
        # --- Main Structure ---
        # Back button first
        back_button = tk.Button(self.frame, text="< Back to Purchase List",
                                command=self.return_to_purchase_list)
        back_button.pack(anchor="nw", padx=10, pady=10)

        # Create scrollable canvas structure
        canvas = tk.Canvas(self.frame, borderwidth=0, background="#ffffff")
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=canvas.yview)
        content_frame = tk.Frame(canvas, background="#ffffff", padx=10, pady=10) # Add padding to content

        # Binding for scroll region update
        content_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Form Content in content_frame ---
        form_padding = {'padx': 10, 'pady': 6} # Consistent padding
        label_style = {'font': ('Arial', 10), 'anchor': 'w'}
        entry_width = 25


        # Title
        title = "Edit Purchase" if self.is_edit else "Add New Purchase"
        tk.Label(content_frame, text=title, font=("Arial", 16, "bold"), background="#ffffff").grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 20), padx=form_padding['padx'])

        # --- Purchase info section ---
        tk.Label(content_frame, text="Order Number:", **label_style, background="#ffffff").grid(
            row=1, column=0, sticky="w", **form_padding)
        self.order_number_var = tk.StringVar(value=self.purchase.order_number if self.is_edit else "")
        order_entry = ttk.Entry(content_frame, textvariable=self.order_number_var, width=entry_width)
        order_entry.grid(row=1, column=1, sticky="ew", **form_padding)

        tk.Label(content_frame, text="Invoice Number:", **label_style, background="#ffffff").grid(
            row=1, column=2, sticky="w", **form_padding)
        self.invoice_number_var = tk.StringVar(value=self.purchase.invoice_number if self.is_edit else "")
        invoice_entry = ttk.Entry(content_frame, textvariable=self.invoice_number_var, width=entry_width)
        invoice_entry.grid(row=1, column=3, sticky="ew", **form_padding)

        tk.Label(content_frame, text="Date (YYYY-MM-DD):", **label_style, background="#ffffff").grid(
            row=2, column=0, sticky="w", **form_padding)
        self.date_var = tk.StringVar(
            value=self.purchase.date if self.is_edit else datetime.now().strftime("%Y-%m-%d"))
        date_entry = ttk.Entry(content_frame, textvariable=self.date_var, width=entry_width)
        date_entry.grid(row=2, column=1, sticky="ew", **form_padding)
        # Consider adding a DatePicker widget here for better UX

        tk.Label(content_frame, text="Vendor:", **label_style, background="#ffffff").grid(
            row=2, column=2, sticky="w", **form_padding)

        # Vendor Dropdown Frame (to hold dropdown and add button)
        vendor_widget_frame = tk.Frame(content_frame, background="#ffffff")
        vendor_widget_frame.grid(row=2, column=3, sticky="ew", **form_padding)

        vendor_names = self.controllers["vendor"].get_vendor_names()
        self.vendor_var = tk.StringVar()
        self.vendor_dropdown = ttk.Combobox(vendor_widget_frame, textvariable=self.vendor_var, values=vendor_names, width=entry_width-5, state="readonly") # Readonly state
        self.vendor_dropdown.pack(side=tk.LEFT, fill=tk.X, expand=True)


        if self.is_edit and self.purchase.vendor_name in vendor_names:
            self.vendor_var.set(self.purchase.vendor_name)
        elif vendor_names:
            self.vendor_var.set(vendor_names[0]) # Default to first if available

        if not vendor_names:
            self.vendor_dropdown["state"] = "disabled"
            tk.Label(content_frame, text=" (No vendors available)", fg="grey", background="#ffffff").grid(
                 row=3, column=3, sticky="w", padx=form_padding['padx'])

        # Add new vendor button (nicer placement)
        add_vendor_btn = ttk.Button(vendor_widget_frame, text="+", width=2, command=self.add_new_vendor)
        add_vendor_btn.pack(side=tk.LEFT, padx=(5,0))


        # --- Line items section ---
        items_frame = tk.LabelFrame(content_frame, text="Line Items", font=('Arial', 11, 'bold'), padx=10, pady=10, background="#ffffff")
        items_frame.grid(row=4, column=0, columnspan=4, sticky="ew", padx=form_padding['padx'], pady=(20, 10))

        # Header row for line items
        header_frame = tk.Frame(items_frame, background="#f0f0f0") # Light grey background for header
        header_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(header_frame, text="Description", width=35, anchor='w', background="#f0f0f0").grid(row=0, column=0, padx=5, pady=2)
        tk.Label(header_frame, text="Qty", width=8, anchor='e', background="#f0f0f0").grid(row=0, column=1, padx=5, pady=2)
        tk.Label(header_frame, text="Unit Price", width=12, anchor='e', background="#f0f0f0").grid(row=0, column=2, padx=5, pady=2)
        tk.Label(header_frame, text="Total", width=12, anchor='e', background="#f0f0f0").grid(row=0, column=3, padx=5, pady=2)
        if self.is_edit: # Only show 'Received' checkbox when editing
             tk.Label(header_frame, text="Rcvd?", width=5, background="#f0f0f0").grid(row=0, column=4, padx=5, pady=2)
        tk.Label(header_frame, text="", width=3, background="#f0f0f0").grid(row=0, column=5, padx=5, pady=2) # For remove button


        self.lines_container = tk.Frame(items_frame, background="#ffffff")
        self.lines_container.pack(fill=tk.X)
        self.line_items = [] # List to hold dicts representing each row's widgets/vars

        # ***** DEFINE total_amount_var EARLIER *****
        self.total_amount_var = tk.StringVar(value="$0.00")

        # Add existing line items or one empty row
        if self.is_edit and self.purchase.line_items:
             # Pass the actual LineItem object
             for item in self.purchase.line_items:
                 self.add_line_item_row(item)
        else:
             self.add_line_item_row() # Add one empty row

        # Add line item button (nicer style)
        add_item_btn = ttk.Button(items_frame, text="+ Add Line Item",
                                 command=lambda: self.add_line_item_row())
        add_item_btn.pack(anchor="w", pady=5)

        # --- Budget allocation section ---
        budget_frame = tk.LabelFrame(content_frame, text="Budget Allocation", font=('Arial', 11, 'bold'), padx=10, pady=10, background="#ffffff")
        budget_frame.grid(row=5, column=0, columnspan=4, sticky="ew", padx=form_padding['padx'], pady=10)

        # Header for budget allocations
        budget_header = tk.Frame(budget_frame, background="#f0f0f0")
        budget_header.pack(fill=tk.X, pady=(0, 5))
        tk.Label(budget_header, text="Budget Name", width=30, anchor='w', background="#f0f0f0").grid(row=0, column=0, padx=5, pady=2)
        tk.Label(budget_header, text="Amount ($)", width=15, anchor='e', background="#f0f0f0").grid(row=0, column=1, padx=5, pady=2)
        tk.Label(budget_header, text="", width=3, background="#f0f0f0").grid(row=0, column=2, padx=5, pady=2) # For remove button

        self.budget_container = tk.Frame(budget_frame, background="#ffffff")
        self.budget_container.pack(fill=tk.X)
        self.budget_allocations = [] # List to hold dicts for budget rows

        # Get budget options (ID, Name)
        self.budget_options = self.controllers["budget"].get_budget_options()

        if not self.budget_options:
            tk.Label(budget_frame, text="No budgets available. Please add budgets first.",
                     fg="red", background="#ffffff").pack(anchor="w")
        else:
            # Add existing budget allocations or one empty row
            if self.is_edit and self.purchase.budgets:
                 # Pass the actual PurchaseBudget object
                 for budget_alloc in self.purchase.budgets:
                     self.add_budget_row(budget_alloc)
            else:
                 self.add_budget_row() # Add one empty row

            # Add budget button (nicer style)
            add_budget_btn = ttk.Button(budget_frame, text="+ Add Budget Allocation",
                                       command=lambda: self.add_budget_row())
            add_budget_btn.pack(anchor="w", pady=5)


        # --- Notes Section ---
        notes_frame = tk.LabelFrame(content_frame, text="Notes", font=('Arial', 11, 'bold'), padx=10, pady=10, background="#ffffff")
        notes_frame.grid(row=6, column=0, columnspan=4, sticky="ew", padx=form_padding['padx'], pady=10)
        self.notes_text = tk.Text(notes_frame, height=4, width=60, borderwidth=1, relief="solid")
        self.notes_text.pack(fill="x", expand=True)
        if self.is_edit and self.purchase.notes:
             self.notes_text.insert("1.0", self.purchase.notes)


        # --- Buttons ---
        buttons_frame = tk.Frame(content_frame, background="#ffffff")
        buttons_frame.grid(row=7, column=0, columnspan=4, sticky="e", padx=form_padding['padx'], pady=(20, 0))

        ttk.Button(buttons_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=5)
        save_text = "Save Changes" if self.is_edit else "Save Purchase"
        ttk.Button(buttons_frame, text=save_text, command=self.save_purchase_data).pack(side=tk.LEFT, padx=5)


        # --- Total Display ---
        # self.total_amount_var is now defined earlier
        total_display_frame = tk.Frame(content_frame, background="#ffffff")
        total_display_frame.grid(row=8, column=0, columnspan=4, sticky="e", padx=form_padding['padx'], pady=(5,0))
        tk.Label(total_display_frame, text="Purchase Total:", font=('Arial', 11, 'bold'), background="#ffffff").pack(side=tk.LEFT)
        tk.Label(total_display_frame, textvariable=self.total_amount_var, font=('Arial', 11, 'bold'), background="#ffffff").pack(side=tk.LEFT, padx=5)

        self.update_purchase_total() # Calculate initial total


    def add_new_vendor(self):
        """Add a new vendor via dialog and refresh dropdown"""
        # Use a simple dialog for quick addition
        dialog = tk.Toplevel(self.frame)
        dialog.title("Add New Vendor")
        dialog.geometry("300x150")
        dialog.transient(self.frame)
        dialog.grab_set()

        tk.Label(dialog, text="New Vendor Name:").pack(pady=(10, 5))
        name_var = tk.StringVar()
        entry = ttk.Entry(dialog, textvariable=name_var, width=30)
        entry.pack(pady=5)
        entry.focus_set()

        def save_new():
             name = name_var.get().strip()
             if not name:
                  messagebox.showerror("Error", "Vendor name cannot be empty.", parent=dialog)
                  return

             vendor_data = {"name": name} # Minimal data for adding
             success, message = self.controllers["vendor"].add_vendor(vendor_data)

             if success:
                  dialog.destroy()
                  # Refresh vendor dropdown in the main form
                  new_vendor_names = self.controllers["vendor"].get_vendor_names()
                  self.vendor_dropdown["values"] = new_vendor_names
                  self.vendor_dropdown.set(name) # Set dropdown to newly added vendor
                  self.vendor_dropdown["state"] = "readonly"
                  messagebox.showinfo("Success", "Vendor added successfully.")
             else:
                  messagebox.showerror("Error", message, parent=dialog)

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save Vendor", command=save_new).pack(side=tk.LEFT, padx=5)


    def add_line_item_row(self, item_obj=None):
        """Adds a row for a line item to the form."""
        row_frame = tk.Frame(self.lines_container, background="#ffffff")
        row_frame.pack(fill=tk.X, pady=2)

        desc_var = tk.StringVar(value=item_obj.description if item_obj else "")
        qty_var = tk.StringVar(value=str(item_obj.quantity) if item_obj else "1")
        price_var = tk.StringVar(value=f"{item_obj.unit_price:.2f}" if item_obj else "0.00")
        total_var = tk.StringVar(value="$0.00") # Calculated
        rcvd_var = tk.BooleanVar(value=item_obj.received if item_obj else False)

        ttk.Entry(row_frame, textvariable=desc_var, width=35).grid(row=0, column=0, padx=5, pady=2, sticky="ew")
        qty_entry = ttk.Entry(row_frame, textvariable=qty_var, width=8, justify='right')
        qty_entry.grid(row=0, column=1, padx=5, pady=2)
        price_entry = ttk.Entry(row_frame, textvariable=price_var, width=12, justify='right')
        price_entry.grid(row=0, column=2, padx=5, pady=2)
        ttk.Label(row_frame, textvariable=total_var, width=12, anchor='e', background="#ffffff").grid(row=0, column=3, padx=5, pady=2)

        if self.is_edit: # Only show checkbox if editing
             ttk.Checkbutton(row_frame, variable=rcvd_var).grid(row=0, column=4, padx=5, pady=2)


        # --- Calculation and Update Logic ---
        def _calculate_and_update_total(*args):
             try:
                  qty = int(qty_var.get())
                  price = float(price_var.get())
                  total_var.set(f"${qty * price:.2f}")
             except ValueError:
                  total_var.set("$0.00")
             self.update_purchase_total() # Update the grand total


        qty_var.trace_add("write", _calculate_and_update_total)
        price_var.trace_add("write", _calculate_and_update_total)
        _calculate_and_update_total() # Initial calculation


        # --- Remove Button ---
        item_data_dict = {
            "row_frame": row_frame,
            "description_var": desc_var,
            "quantity_var": qty_var,
            "price_var": price_var,
            "total_var": total_var,
            "received_var": rcvd_var # Keep track even if not displayed
        }

        def remove_row():
             row_frame.destroy()
             self.line_items.remove(item_data_dict)
             self.update_purchase_total() # Recalculate total when item removed


        remove_btn = ttk.Button(row_frame, text="✖", command=remove_row, width=2, style="Toolbutton") # Use Toolbutton style if available
        remove_btn.grid(row=0, column=5, padx=(5,0), pady=2)


        self.line_items.append(item_data_dict)


    def add_budget_row(self, budget_alloc_obj=None):
        """Adds a row for budget allocation."""
        if not self.budget_options: return # Can't add if no budgets exist

        row_frame = tk.Frame(self.budget_container, background="#ffffff")
        row_frame.pack(fill=tk.X, pady=2)

        budget_id_var = tk.StringVar()
        amount_var = tk.StringVar(value="0.00")
        budget_name_var = tk.StringVar() # For display in combobox


        # --- Setup Initial Values ---
        current_budget_id = None
        if budget_alloc_obj:
             current_budget_id = budget_alloc_obj.budget_id
             amount_var.set(f"{budget_alloc_obj.amount:.2f}")
             # Find the name for the current ID
             budget_name = next((name for bid, name in self.budget_options if bid == current_budget_id), "")
             budget_name_var.set(budget_name)
             budget_id_var.set(current_budget_id) # Set the hidden ID var
        elif self.budget_options:
             # Default to the first budget option if adding new
             budget_id_var.set(self.budget_options[0][0])
             budget_name_var.set(self.budget_options[0][1])


        # --- Widgets ---
        budget_combo = ttk.Combobox(row_frame, textvariable=budget_name_var, width=28, state="readonly")
        budget_combo["values"] = [name for _, name in self.budget_options]
        budget_combo.grid(row=0, column=0, padx=5, pady=2, sticky="ew")

        amount_entry = ttk.Entry(row_frame, textvariable=amount_var, width=15, justify='right')
        amount_entry.grid(row=0, column=1, padx=5, pady=2)

        # --- Combobox Selection Logic ---
        def on_budget_select(event):
             selected_name = budget_name_var.get()
             # Find the ID corresponding to the selected name
             selected_id = next((bid for bid, name in self.budget_options if name == selected_name), None)
             if selected_id:
                  budget_id_var.set(selected_id) # Update the hidden ID variable


        budget_combo.bind("<<ComboboxSelected>>", on_budget_select)

        # --- Store References and Remove Button ---
        budget_data_dict = {
            "row_frame": row_frame,
            "budget_id_var": budget_id_var, # Stores the actual ID
            "amount_var": amount_var,
            "budget_name_var": budget_name_var # For the combobox display
        }

        def remove_row():
             row_frame.destroy()
             self.budget_allocations.remove(budget_data_dict)


        remove_btn = ttk.Button(row_frame, text="✖", command=remove_row, width=2, style="Toolbutton")
        remove_btn.grid(row=0, column=2, padx=(5,0), pady=2)


        self.budget_allocations.append(budget_data_dict)

    def update_purchase_total(self):
        """Calculates and updates the total purchase amount label."""
        total = 0.0
        for item_dict in self.line_items:
            try:
                qty = int(item_dict["quantity_var"].get())
                price = float(item_dict["price_var"].get())
                total += qty * price
            except ValueError:
                pass # Ignore items with invalid numbers for total calculation
        # Ensure self.total_amount_var exists before setting
        if hasattr(self, 'total_amount_var'):
            self.total_amount_var.set(f"${total:.2f}")


    def cancel(self):
        """Cancel form and return to purchase list"""
        # Check if form is dirty (optional, more complex)
        if messagebox.askyesno("Cancel", "Discard changes and return to the list?"):
            self.return_to_purchase_list()

    def save_purchase_data(self):
        """Validates and saves purchase data using the controller."""
        try:
            # --- Gather and Validate Basic Info ---
            order_number = self.order_number_var.get().strip()
            if not order_number: raise ValueError("Order Number is required.")

            date_str = self.date_var.get().strip()
            try:
                 # Validate date format (simple check)
                 datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                 raise ValueError("Date must be in YYYY-MM-DD format.")

            vendor_name = self.vendor_var.get()
            if not vendor_name: raise ValueError("Vendor is required.")

            # Correct way to get vendor_id
            selected_vendor = next((v for v in self.controllers["vendor"].get_all_vendors() if v.name == vendor_name), None)
            if not selected_vendor: raise ValueError(f"Selected vendor '{vendor_name}' not found.")
            vendor_id = selected_vendor.id


            # --- Gather and Validate Line Items ---
            if not self.line_items: raise ValueError("At least one Line Item is required.")
            parsed_items = []
            total_purchase_amount = 0.0
            for i, item_dict in enumerate(self.line_items):
                 desc = item_dict["description_var"].get().strip()
                 if not desc: raise ValueError(f"Line Item #{i+1}: Description is required.")
                 try:
                      qty = int(item_dict["quantity_var"].get())
                      if qty <= 0: raise ValueError("Quantity must be positive.")
                 except ValueError:
                      raise ValueError(f"Line Item #{i+1}: Quantity must be a valid positive integer.")
                 try:
                      price = float(item_dict["price_var"].get())
                      if price < 0: raise ValueError("Unit price cannot be negative.")
                 except ValueError:
                      raise ValueError(f"Line Item #{i+1}: Unit Price must be a valid number.")

                 parsed_items.append({
                      "description": desc,
                      "quantity": qty,
                      "unit_price": price,
                      "received": item_dict["received_var"].get() if self.is_edit else False # Only include received if editing
                 })
                 total_purchase_amount += qty * price


            # --- Gather and Validate Budget Allocations ---
            parsed_budgets = []
            total_allocated_amount = 0.0
            allocated_budget_ids = set()
            if not self.budget_allocations and self.budget_options: # Check if required
                 # Decide if budget allocation is mandatory if options exist
                 # raise ValueError("At least one Budget Allocation is required.")
                 pass # Allow saving without budget allocation

            for i, budget_dict in enumerate(self.budget_allocations):
                 budget_id = budget_dict["budget_id_var"].get()
                 if not budget_id: raise ValueError(f"Budget Allocation #{i+1}: Budget selection is required.")
                 if budget_id in allocated_budget_ids: raise ValueError(f"Budget Allocation #{i+1}: Budget '{budget_dict['budget_name_var'].get()}' allocated more than once.")

                 try:
                      amount = float(budget_dict["amount_var"].get())
                      if amount <= 0: raise ValueError("Allocation amount must be positive.")
                 except ValueError:
                      raise ValueError(f"Budget Allocation #{i+1}: Amount must be a valid positive number.")

                 parsed_budgets.append({
                      "budget_id": budget_id,
                      "amount": amount
                 })
                 total_allocated_amount += amount
                 allocated_budget_ids.add(budget_id)


            # --- Final Validation: Totals Match ---
            # Allow for small floating point differences only if budgets are allocated
            if parsed_budgets and abs(total_purchase_amount - total_allocated_amount) > 0.01:
                 raise ValueError(f"Total Allocated Amount (${total_allocated_amount:.2f}) must match Purchase Total (${total_purchase_amount:.2f}).")


            # --- Prepare Data and Call Controller ---
            purchase_data = {
                 "order_number": order_number,
                 "invoice_number": self.invoice_number_var.get().strip(),
                 "date": date_str,
                 "vendor_id": vendor_id,
                 "vendor_name": vendor_name, # Keep vendor name for display consistency
                 "line_items": parsed_items,
                 "budgets": parsed_budgets,
                 "notes": self.notes_text.get("1.0", tk.END).strip() # Get notes from Text widget
            }

            if self.is_edit:
                 # Preserve existing approval status when editing
                 purchase_data["id"] = self.purchase.id
                 purchase_data["status"] = self.purchase.status
                 purchase_data["approver"] = self.purchase.approver
                 purchase_data["approval_date"] = self.purchase.approval_date
                 success = self.controllers["purchase"].update_purchase(self.purchase.id, purchase_data)
                 message = "Purchase updated successfully."
            else:
                 # New purchases default to Pending
                 purchase_data["status"] = "Pending"
                 success = self.controllers["purchase"].add_purchase(purchase_data)
                 message = "Purchase added successfully."

            # --- Handle Success or Failure ---
            if success:
                 messagebox.showinfo("Success", message)
                 self.return_to_purchase_list() # Go back to list view
            else:
                 # The controller might return a more specific error message
                 messagebox.showerror("Error", "Failed to save purchase. Check console for details.")


        except ValueError as ve:
             messagebox.showerror("Validation Error", str(ve))
        except Exception as e:
             messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
             print(f"Save purchase error: {e}") # Log detailed error


    def return_to_purchase_list(self):
        """Return to purchase list view using ViewFactory"""
        # Corrected to use ViewFactory
        purchase_list = ViewFactory.create_view('PurchaseListView', self.parent, self.controllers, self.show_view)
        self.show_view(purchase_list)


    def show(self):
        """Show this view"""
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """Hide this view"""
        self.frame.pack_forget()