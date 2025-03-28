# views/approval_view.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from utils.table_utils import configure_treeview
# Added imports
from views.view_factory import ViewFactory
from database.models import Purchase, LineItem, PurchaseBudget, Budget # Import models

class ApprovalDashboardView:
    def __init__(self, parent, controllers, show_view_callback):
        self.parent = parent
        self.controllers = controllers
        self.show_view = show_view_callback

        # For simplicity, we'll use a hardcoded approver name
        # In a real system, this would come from user authentication
        self.current_approver = "System Admin"

        self.frame = tk.Frame(parent)
        self.setup_ui()

    def setup_ui(self):
        # Create back button
        back_button = tk.Button(self.frame, text="Back to Dashboard",
                                command=self.return_to_dashboard)
        back_button.pack(anchor="nw", padx=10, pady=10)

        # Title
        tk.Label(self.frame, text="Purchase Approval Dashboard",
                 font=("Arial", 14, "bold")).pack(anchor="w", padx=20, pady=10)

        # Status counts frame - store reference for refreshing
        self.status_frame = tk.Frame(self.frame)
        self.status_frame.pack(fill=tk.X, padx=20, pady=10)
        self.display_status_cards() # Refactored card display

        # Pending approvals frame
        pending_frame = tk.LabelFrame(self.frame, text="Purchases Pending Approval")
        pending_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Create treeview for pending approvals
        columns = ("ID", "Order #", "Vendor", "Date", "Total", "Submitter")
        self.pending_tree = ttk.Treeview(pending_frame, columns=columns, show="headings", selectmode="browse") # browse selectmode
        self.pending_tree = configure_treeview(self.pending_tree)
        # Set column headings
        for col in columns:
            self.pending_tree.heading(col, text=col)

        # Hide ID column, configure others
        self.pending_tree.column("ID", width=0, stretch=tk.NO)
        self.pending_tree.column("Order #", width=100, anchor="w")
        self.pending_tree.column("Vendor", width=150, anchor="w")
        self.pending_tree.column("Date", width=100, anchor="center")
        self.pending_tree.column("Total", width=100, anchor="e")
        self.pending_tree.column("Submitter", width=150, anchor="w") # Placeholder

        # Add scrollbar
        scrollbar = ttk.Scrollbar(pending_frame, orient="vertical", command=self.pending_tree.yview)
        self.pending_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.pending_tree.pack(fill="both", expand=True)

        # Double-click binding
        self.pending_tree.bind("<Double-1>", lambda event: self.view_purchase_details())


        # Button frame
        button_frame = tk.Frame(self.frame)
        button_frame.pack(fill=tk.X, padx=20, pady=10)

        # Approval buttons
        tk.Button(button_frame, text="View Details",
                  command=self.view_purchase_details).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Approve Selected",
                  command=self.approve_selected).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Reject Selected",
                  command=self.reject_selected).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Refresh List",
                  command=self.refresh_all_data).pack(side=tk.RIGHT, padx=5) # Changed target

        # Populate list initially
        self.refresh_pending_list()


    def display_status_cards(self):
         """Calculates and displays status summary cards."""
         if not hasattr(self, 'status_frame') or not self.status_frame.winfo_exists():
             return # Don't try to update if frame doesn't exist

         try:
             purchases = self.controllers["purchase"].get_all_purchases()
             pending_count = sum(1 for p in purchases if p.status == "Pending")
             approved_count = sum(1 for p in purchases if p.status == "Approved")
             rejected_count = sum(1 for p in purchases if p.status == "Rejected")

             status_data = [
                 ("Pending Approval", pending_count, "#ffcccb"),
                 ("Approved", approved_count, "#ccffcc"),
                 ("Rejected", rejected_count, "#f0f0f0")
             ]

             # Clear previous cards if any
             for widget in self.status_frame.winfo_children():
                 widget.destroy()

             # Create new cards
             for title, count, color in status_data:
                 card = tk.Frame(self.status_frame, bg=color, bd=1, relief=tk.RAISED)
                 card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

                 tk.Label(card, text=title, font=("Arial", 12, "bold"), bg=color).pack(pady=(10, 5))
                 tk.Label(card, text=str(count), font=("Arial", 24), bg=color).pack(pady=(5, 10))
         except Exception as e:
             print(f"Error calculating status cards: {e}")
             # Clear previous cards if any
             for widget in self.status_frame.winfo_children():
                 widget.destroy()
             tk.Label(self.status_frame, text="Error loading stats.").pack()

    def refresh_pending_list(self):
        """Refresh the pending approvals list"""
        if not hasattr(self, 'pending_tree') or not self.pending_tree.winfo_exists():
             print("Error: pending_tree widget does not exist during refresh.")
             return # Don't try to refresh if widget gone

        self.pending_tree.delete(*self.pending_tree.get_children())

        try:
            # Get pending purchases (should have relationships loaded by controller)
            pending_purchases = self.controllers["purchase"].get_purchases_by_approval_status("Pending")

            for i, purchase in enumerate(pending_purchases):
                # Add row tags for styling
                row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                # Use pending tag for all pending items
                status_tag = 'pending'

                try:
                     total = purchase.get_total()
                except Exception as e:
                     print(f"Error getting total for purchase {purchase.id}: {e}")
                     total = 0.0

                self.pending_tree.insert("", "end", values=(
                    purchase.id,
                    purchase.order_number or "N/A",
                    purchase.vendor_name or "N/A",
                    purchase.date or "N/A",
                    f"${total:.2f}",
                    "User"  # Placeholder: In a real system, this would be the submitter's name
                ), tags=(row_tag, status_tag))
        except Exception as e:
             print(f"Error refreshing pending approval list: {e}")

    def refresh_all_data(self):
         """Refreshes both the list and the status cards."""
         self.refresh_pending_list()
         self.display_status_cards()


    def view_purchase_details(self):
        """View details of selected purchase"""
        selected_item = self.pending_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No purchase selected")
            return

        purchase_id = self.pending_tree.item(selected_item, "values")[0]
        # Fetch purchase with eagerly loaded relationships
        purchase = self.controllers["purchase"].get_purchase_by_id(purchase_id)

        if not purchase:
            messagebox.showerror("Error", "Purchase not found")
            return

        # --- Create the Toplevel Dialog Window ---
        details_window = tk.Toplevel(self.parent)
        details_window.title(f"Purchase Details - Order #{purchase.order_number}")
        details_window.geometry("800x600")
        details_window.minsize(800, 600)
        details_window.transient(self.parent)
        details_window.grab_set()

        # Main frame
        main_frame = tk.Frame(details_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Purchase header
        header_frame = tk.Frame(main_frame)
        header_frame.pack(fill=tk.X)
        tk.Label(header_frame, text=f"Order #{purchase.order_number}",
                 font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=5)

        # Purchase info frame
        info_frame = tk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=10)
        info_fields = [
            ("Date:", purchase.date or "N/A"),
            ("Vendor:", purchase.vendor_name or "N/A"),
            ("Invoice #:", purchase.invoice_number or "Not Available"),
            ("Receiving Status:", purchase.get_status() or "N/A"), # Use get_status for receiving
            ("Approval Status:", purchase.status or "N/A") # Direct status attribute for approval
        ]
        for i, (label, value) in enumerate(info_fields):
            tk.Label(info_frame, text=label, font=("Arial", 11, "bold")).grid(row=i, column=0, sticky="w", pady=3)
            tk.Label(info_frame, text=value).grid(row=i, column=1, sticky="w", pady=3)

        # --- Budget allocations Section ---
        budget_frame = tk.Frame(main_frame)
        budget_frame.pack(fill=tk.X, pady=10)
        tk.Label(budget_frame, text="Budget Allocations:", font=("Arial", 11, "bold")).pack(anchor="w")

        if purchase.budgets:
             # Access attributes directly from the PurchaseBudget and related Budget objects
             for budget_alloc in purchase.budgets:
                 budget_name = budget_alloc.budget.name if budget_alloc.budget else "Unknown Budget"
                 amount = budget_alloc.amount
                 tk.Label(budget_frame, text=f"• {budget_name}: ${amount:.2f}").pack(
                     anchor="w", padx=20)
        else:
             tk.Label(budget_frame, text="No budget allocations.", anchor='w', padx=20).pack()


        # --- Line items Section ---
        lines_frame = tk.Frame(main_frame)
        lines_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        tk.Label(lines_frame, text="Line Items:", font=("Arial", 11, "bold")).pack(anchor="w")

        columns = ("Item", "Description", "Quantity", "Unit Price", "Total", "Received")
        lines_tree = ttk.Treeview(lines_frame, columns=columns, show="headings")
        lines_tree = configure_treeview(lines_tree)

        for col in columns:
            lines_tree.heading(col, text=col)
        lines_tree.column("Item", width=50, anchor='center')
        lines_tree.column("Description", width=300)
        lines_tree.column("Quantity", width=70, anchor='e')
        lines_tree.column("Unit Price", width=100, anchor='e')
        lines_tree.column("Total", width=100, anchor='e')
        lines_tree.column("Received", width=80, anchor='center')

        scrollbar = ttk.Scrollbar(lines_frame, orient="vertical", command=lines_tree.yview)
        lines_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        lines_tree.pack(fill="both", expand=True)

        if purchase.line_items:
             # Access attributes directly from the LineItem object
             for i, item in enumerate(purchase.line_items):
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
            lines_tree.insert("", "end", values=("", "No line items found.", "", "", "", ""))


        # --- Total Amount ---
        total_frame = tk.Frame(main_frame)
        total_frame.pack(fill=tk.X, pady=10)
        tk.Label(total_frame, text="Total Amount:", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        tk.Label(total_frame, text=f"${purchase.get_total():.2f}",
                 font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=10)

        # --- Approval/Rejection Buttons ---
        action_button_frame = tk.Frame(main_frame)
        action_button_frame.pack(fill=tk.X, pady=10)

        # Show Approve/Reject only if status is Pending
        if purchase.status == "Pending":
            def approve_action():
                """Action specific to the details window approval."""
                if self._handle_approval_logic(purchase.id, details_window): # Use helper
                    details_window.destroy() # Close window on success
                    self.refresh_all_data() # Refresh list and cards

            def reject_action():
                 """Action specific to the details window rejection."""
                 self._handle_rejection_dialog_logic(purchase.id, details_window) # Use helper


            approve_btn = tk.Button(action_button_frame, text="Approve Purchase", command=approve_action)
            approve_btn.pack(side=tk.LEFT, padx=10)

            reject_btn = tk.Button(action_button_frame, text="Reject Purchase", command=reject_action)
            reject_btn.pack(side=tk.LEFT, padx=10)

        # --- Close Button ---
        tk.Button(main_frame, text="Close", command=details_window.destroy).pack(pady=10, anchor='se')


    def _handle_approval_logic(self, purchase_id, parent_messagebox_owner):
        """Internal helper to call controller and show messages for approval. Returns True on success."""
        if messagebox.askyesno("Confirm Approval", "Are you sure you want to approve this purchase?", parent=parent_messagebox_owner):
            success, message = self.controllers["purchase"].approve_purchase(
                purchase_id, self.current_approver)
            if success:
                messagebox.showinfo("Success", message, parent=parent_messagebox_owner)
                return True
            else:
                messagebox.showerror("Error", message, parent=parent_messagebox_owner)
                return False
        return False # Did not confirm


    def _handle_rejection_dialog_logic(self, purchase_id, parent_window):
         """Internal helper to show rejection notes dialog and call controller."""
         notes_window = tk.Toplevel(parent_window) # Child of calling window
         notes_window.title("Rejection Notes")
         notes_window.geometry("400x250")
         notes_window.transient(parent_window)
         notes_window.grab_set()

         tk.Label(notes_window, text="Please provide reason for rejection:").pack(pady=10)

         notes_text = tk.Text(notes_window, height=8, width=45, wrap=tk.WORD)
         notes_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
         notes_text.focus_set()

         def confirm_reject():
             notes = notes_text.get("1.0", tk.END).strip()
             if not notes:
                 messagebox.showerror("Error", "Rejection notes cannot be empty.", parent=notes_window)
                 return

             success, message = self.controllers["purchase"].reject_purchase(
                 purchase_id, self.current_approver, notes)
             if success:
                 messagebox.showinfo("Success", message, parent=notes_window)
                 notes_window.destroy() # Close notes window
                 # Don't close parent_window (details) here, let calling code do it
                 self.refresh_all_data() # Refresh main list and cards
             else:
                 messagebox.showerror("Error", message, parent=notes_window)

         button_frame = tk.Frame(notes_window)
         button_frame.pack(pady=10)
         tk.Button(button_frame, text="Cancel", command=notes_window.destroy).pack(side=tk.LEFT, padx=10)
         tk.Button(button_frame, text="Confirm Rejection", command=confirm_reject).pack(side=tk.LEFT, padx=10)


    def approve_selected(self):
        """Approve selected purchase from the main list"""
        selected_item = self.pending_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No purchase selected")
            return

        purchase_id = self.pending_tree.item(selected_item, "values")[0]
        # Call helper, refresh list/cards if successful
        if self._handle_approval_logic(purchase_id, self.frame): # Pass main frame as parent for messagebox
             self.refresh_all_data()


    def reject_selected(self):
        """Reject selected purchase from the main list"""
        selected_item = self.pending_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No purchase selected")
            return

        purchase_id = self.pending_tree.item(selected_item, "values")[0]
        # Call helper to show dialog, it will refresh list/cards on success
        self._handle_rejection_dialog_logic(purchase_id, self.frame) # Pass main frame as parent for dialog


    def return_to_dashboard(self):
        """Return to main dashboard"""
        dashboard = ViewFactory.create_view('MainDashboard', self.parent, self.controllers, self.show_view)
        self.show_view(dashboard)

    def show(self):
        """Show this view"""
        self.refresh_all_data() # Refresh when shown
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """Hide this view"""
        self.frame.pack_forget()