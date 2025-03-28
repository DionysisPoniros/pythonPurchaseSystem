# purchase_system/views/receiving_view.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from utils.table_utils import configure_treeview
# Added imports needed for dialog and navigation
from views.view_factory import ViewFactory
from database.models import Purchase # Import Purchase if needed, though controller should handle it

class ReceivingDashboardView:
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
        tk.Label(self.frame, text="Receiving Dashboard",
                 font=("Arial", 14, "bold")).pack(anchor="w", padx=20, pady=10)

        # Status counts frame
        status_frame = tk.Frame(self.frame)
        status_frame.pack(fill=tk.X, padx=20, pady=10)
        # Calculate and display status cards (code omitted for brevity - assumed correct)
        self.display_status_cards(status_frame)


        # Pending items frame
        pending_frame = tk.LabelFrame(self.frame, text="Pending Receipts")
        pending_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Create treeview for pending items
        columns = ("ID", "Order #", "Vendor", "Date", "Items", "Days Outstanding")
        # Store treeview as instance variable
        self.pending_tree = ttk.Treeview(pending_frame, columns=columns, show="headings")
        self.pending_tree = configure_treeview(self.pending_tree)

        # Set column headings
        for col in columns:
            self.pending_tree.heading(col, text=col)

        # Hide ID column
        self.pending_tree.column("ID", width=0, stretch=tk.NO)
        self.pending_tree.column("Order #", width=100)
        self.pending_tree.column("Vendor", width=150)
        self.pending_tree.column("Date", width=100)
        self.pending_tree.column("Items", width=300)
        self.pending_tree.column("Days Outstanding", width=120)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(pending_frame, orient="vertical", command=self.pending_tree.yview)
        self.pending_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.pending_tree.pack(fill="both", expand=True)

        # Populate the list initially
        self.refresh_pending_list()


        # Button frame
        button_frame = tk.Frame(self.frame)
        button_frame.pack(fill=tk.X, padx=20, pady=10)

        # CORRECTED: Button now calls self.open_receive_dialog
        tk.Button(button_frame, text="Receive Selected Items",
                  command=self.open_receive_dialog).pack(side=tk.LEFT, padx=5)
        # Renamed refresh button for clarity
        tk.Button(button_frame, text="Refresh List",
                  command=self.refresh_pending_list).pack(side=tk.LEFT, padx=5)

    def display_status_cards(self, parent_frame):
        """Calculates and displays status summary cards."""
        try:
            purchases = self.controllers["purchase"].get_all_purchases()
            pending_count = 0
            partial_count = 0
            received_count = 0

            for purchase in purchases:
                # Use model methods safely
                is_rec = hasattr(purchase, 'is_received') and purchase.is_received()
                is_part = hasattr(purchase, 'is_partially_received') and purchase.is_partially_received()

                if is_rec:
                    received_count += 1
                elif is_part:
                    partial_count += 1
                # Only count as pending if not received and not partial
                elif purchase.status != 'Rejected': # Exclude rejected from pending receive
                    pending_count +=1


            status_data = [
                ("Pending", pending_count, "#ffcccb"),
                ("Partially Received", partial_count, "#ffffcc"),
                ("Fully Received", received_count, "#ccffcc")
            ]

            # Clear previous cards if any
            for widget in parent_frame.winfo_children():
                widget.destroy()

            # Create new cards
            for title, count, color in status_data:
                card = tk.Frame(parent_frame, bg=color, bd=1, relief=tk.RAISED)
                card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

                tk.Label(card, text=title, font=("Arial", 12, "bold"), bg=color).pack(pady=(10, 5))
                tk.Label(card, text=str(count), font=("Arial", 24), bg=color).pack(pady=(5, 10))
        except Exception as e:
            print(f"Error calculating status cards: {e}")
            tk.Label(parent_frame, text="Error loading stats.").pack()


    def refresh_pending_list(self):
        """Refreshes the list of purchases pending receipt."""
        # Clear existing items
        self.pending_tree.delete(*self.pending_tree.get_children())

        try:
            purchases = self.controllers["purchase"].get_all_purchases()
            today = datetime.now().date()

            for i, purchase in enumerate(purchases):
                # Skip if all items received or if purchase is rejected
                if (hasattr(purchase, 'is_received') and purchase.is_received()) or purchase.status == 'Rejected':
                    continue

                # Calculate days outstanding
                try:
                    purchase_date = datetime.strptime(purchase.date, "%Y-%m-%d").date()
                    days_outstanding = (today - purchase_date).days
                except (ValueError, TypeError):
                    days_outstanding = "N/A"

                # Get pending items description
                pending_text = "Error loading items"
                if hasattr(purchase, 'line_items'):
                     pending_items = [
                         item.description for item in purchase.line_items
                         if hasattr(item, 'received') and not item.received
                     ]
                     pending_text = ", ".join(pending_items)
                     if len(pending_text) > 50:
                         pending_text = pending_text[:47] + "..."
                elif not purchase.line_items:
                     pending_text = "No items found"


                # Add row tags for styling
                row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                status_tag = 'pending' if isinstance(days_outstanding, int) and days_outstanding > 14 else 'partial'

                self.pending_tree.insert("", "end", values=(
                    purchase.id,
                    purchase.order_number or "N/A",
                    purchase.vendor_name or "N/A",
                    purchase.date or "N/A",
                    pending_text,
                    days_outstanding
                ), tags=(row_tag, status_tag))
        except Exception as e:
             print(f"Error refreshing pending list: {e}")
             # Optionally display an error in the UI


    def open_receive_dialog(self):
        """Opens the dialog to receive items for the selected purchase."""
        selected = self.pending_tree.selection()
        if not selected:
            messagebox.showerror("Error", "No purchase order selected from the list.")
            return

        # Get the actual purchase ID from the selected treeview item
        purchase_id = self.pending_tree.item(selected[0], "values")[0]

        # Fetch the full purchase object using the controller
        # The controller's get_purchase_by_id should eager load line_items
        purchase = self.controllers["purchase"].get_purchase_by_id(purchase_id)

        if not purchase:
            messagebox.showerror("Error", "Selected purchase order could not be found.")
            return
        if not hasattr(purchase, 'line_items') or not purchase.line_items:
             messagebox.showinfo("Info", "Selected purchase order has no line items to receive.")
             return

        # --- Create the Toplevel Dialog Window ---
        receive_window = tk.Toplevel(self.parent)
        receive_window.title(f"Receive Items - Order #{purchase.order_number}")
        receive_window.geometry("700x500")
        receive_window.minsize(600, 400)
        receive_window.transient(self.parent) # Make it modal relative to parent
        receive_window.grab_set() # Grab focus

        # Main frame within the dialog
        main_frame = tk.Frame(receive_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(main_frame, text=f"Receive Items for Order #{purchase.order_number}",
                 font=("Arial", 14, "bold")).pack(pady=10)

        # Frame for the line items treeview
        items_frame = tk.Frame(main_frame)
        items_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Treeview for line items within the dialog
        columns = ("Index", "Description", "Quantity", "Received") # Use index to track items
        items_tree = ttk.Treeview(items_frame, columns=columns, show="headings", selectmode="extended")

        for col in columns:
            items_tree.heading(col, text=col)

        items_tree.column("Index", width=50, stretch=tk.NO, anchor="center")
        items_tree.column("Description", width=300)
        items_tree.column("Quantity", width=70, anchor="e")
        items_tree.column("Received", width=80, anchor="center")

        items_tree = configure_treeview(items_tree) # Apply common styling

        # Scrollbar for the items treeview
        scrollbar = ttk.Scrollbar(items_frame, orient="vertical", command=items_tree.yview)
        items_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        items_tree.pack(fill="both", expand=True)

        # Populate the items treeview - Store original index
        line_items_with_index = list(enumerate(purchase.line_items))
        for i, item in line_items_with_index:
            received_status = "Yes" if item.received else "No"
            row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            status_tag = 'approved' if item.received else 'pending'
            # Use original index 'i' as the item ID (iid) in the tree
            items_tree.insert("", "end", iid=str(i), values=(
                i, # Display original index
                item.description or "",
                item.quantity or 0,
                received_status
            ), tags=(row_tag, status_tag))

        # Frame for buttons at the bottom of the dialog
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # --- Action Functions for Dialog Buttons ---
        def update_receive_status(receive_flag):
            """Marks selected items in the dialog tree as received/not received."""
            selected_iids = items_tree.selection() # Get selected tree item IDs (original indices)
            if not selected_iids:
                messagebox.showerror("Error", "No items selected from the list.", parent=receive_window)
                return

            # Convert tree iids (strings) back to integer indices
            indices_to_update = [int(iid) for iid in selected_iids]

            # Call controller method
            success = self.controllers["purchase"].receive_items(purchase.id, indices_to_update, receive_flag)

            if success:
                # Update the display within the dialog's treeview
                for iid in selected_iids:
                    idx = int(iid)
                    item_obj = line_items_with_index[idx][1] # Get corresponding LineItem object
                    new_status_text = "Yes" if receive_flag else "No"
                    new_tag = 'approved' if receive_flag else 'pending'
                    original_row_tag = items_tree.item(iid, "tags")[0] # Preserve even/odd row tag

                    items_tree.item(iid, values=(
                        idx,
                        item_obj.description or "",
                        item_obj.quantity or 0,
                        new_status_text
                    ), tags=(original_row_tag, new_tag)) # Update tags in dialog

                messagebox.showinfo("Success", f"Selected items marked as {'received' if receive_flag else 'not received'}.", parent=receive_window)
                # Refresh the main dashboard list AFTER the dialog action is done
                self.refresh_pending_list()
            else:
                messagebox.showerror("Error", "Failed to update item status.", parent=receive_window)

        def receive_all_items():
            """Marks all items for this purchase as received."""
            all_indices = list(range(len(purchase.line_items)))
            success = self.controllers["purchase"].receive_items(purchase.id, all_indices, True)

            if success:
                 # Update the display of all items in the dialog's treeview
                for iid in items_tree.get_children():
                    idx = int(iid)
                    item_obj = line_items_with_index[idx][1]
                    original_row_tag = items_tree.item(iid, "tags")[0]

                    items_tree.item(iid, values=(
                        idx,
                        item_obj.description or "",
                        item_obj.quantity or 0,
                        "Yes"
                    ), tags=(original_row_tag, 'approved'))

                messagebox.showinfo("Success", "All items marked as received.", parent=receive_window)
                # Refresh the main dashboard list
                self.refresh_pending_list()
                # Optionally close dialog after receiving all
                # receive_window.destroy()
            else:
                messagebox.showerror("Error", "Failed to receive all items.", parent=receive_window)

        # --- Create Dialog Buttons ---
        tk.Button(button_frame, text="Mark Selected as Received", command=lambda: update_receive_status(True)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Mark Selected as Not Received", command=lambda: update_receive_status(False)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Receive All Items", command=receive_all_items).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Close", command=receive_window.destroy).pack(side=tk.RIGHT, padx=5)


    # Removed the old refresh_dashboard method, replaced by refresh_pending_list
    # def refresh_dashboard(self): ...

    def return_to_dashboard(self):
        """Return to main dashboard"""
        dashboard = ViewFactory.create_view('MainDashboard', self.parent, self.controllers, self.show_view)
        self.show_view(dashboard)

    def show(self):
        """Show this view"""
        self.refresh_pending_list() # Refresh list when the view is shown
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """Hide this view"""
        self.frame.pack_forget()