# views/approval_view.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from utils.table_utils import configure_treeview

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

        # Status counts
        status_frame = tk.Frame(self.frame)
        status_frame.pack(fill=tk.X, padx=20, pady=10)

        # Calculate status counts
        purchases = self.controllers["purchase"].get_all_purchases()
        pending_count = sum(1 for p in purchases if p.status == "Pending")
        approved_count = sum(1 for p in purchases if p.status == "Approved")
        rejected_count = sum(1 for p in purchases if p.status == "Rejected")

        # Status cards
        status_data = [
            ("Pending Approval", pending_count, "#ffcccb"),
            ("Approved", approved_count, "#ccffcc"),
            ("Rejected", rejected_count, "#f0f0f0")
        ]

        for title, count, color in status_data:
            card = tk.Frame(status_frame, bg=color, bd=1, relief=tk.RAISED)
            card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

            tk.Label(card, text=title, font=("Arial", 12, "bold"), bg=color).pack(pady=(10, 5))
            tk.Label(card, text=str(count), font=("Arial", 24), bg=color).pack(pady=(5, 10))

        # Pending approvals
        pending_frame = tk.LabelFrame(self.frame, text="Purchases Pending Approval")
        pending_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Create treeview for pending approvals
        columns = ("ID", "Order #", "Vendor", "Date", "Total", "Submitter")
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
        self.pending_tree.column("Total", width=100)
        self.pending_tree.column("Submitter", width=150)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(pending_frame, orient="vertical", command=self.pending_tree.yview)
        self.pending_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.pending_tree.pack(fill="both", expand=True)

        # Insert pending approvals
        self.refresh_pending_list()

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
                  command=self.refresh_pending_list).pack(side=tk.RIGHT, padx=5)

    def refresh_pending_list(self):
        """Refresh the pending approvals list"""
        self.pending_tree.delete(*self.pending_tree.get_children())

        # Get pending purchases
        pending_purchases = self.controllers["purchase"].get_purchases_by_approval_status("Pending")

        for i, purchase in enumerate(pending_purchases):
            # Add row tags for styling
            row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            
            self.pending_tree.insert("", "end", values=(
                purchase.id,
                purchase.order_number,
                purchase.vendor_name,
                purchase.date,
                f"${purchase.get_total():.2f}",
                "User"  # In a real system, this would be the submitter's name
            ), tags=(row_tag, 'pending'))
            
    def view_purchase_details(self):
        """View details of selected purchase"""
        selected_item = self.pending_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No purchase selected")
            return

        purchase_id = self.pending_tree.item(selected_item, "values")[0]
        purchase = self.controllers["purchase"].get_purchase_by_id(purchase_id)

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
            ("Status:", purchase.get_status()),
            ("Approval Status:", purchase.status)
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
        lines_tree = configure_treeview(lines_tree)

        # Set column headings
        for col in columns:
            lines_tree.heading(col, text=col)

        lines_tree.column("Item", width=50)
        lines_tree.column("Description", width=200)
        lines_tree.column("Quantity", width=70)
        lines_tree.column("Unit Price", width=100)
        lines_tree.column("Total", width=100)
        lines_tree.column("Received", width=80)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(lines_frame, orient="vertical", command=lines_tree.yview)
        lines_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        lines_tree.pack(fill="both", expand=True)

        # Insert line items
        for i, item in enumerate(purchase.line_items):
            total = item.get("quantity", 0) * item.get("unit_price", 0)
            received = "Yes" if item.get("received", False) else "No"

            lines_tree.insert("", "end", values=(
                i + 1,
                item.get("description", ""),
                item.get("quantity", 0),
                f"${item.get('unit_price', 0):.2f}",
                f"${total:.2f}",
                received
            ))

        # Total
        total_frame = tk.Frame(main_frame)
        total_frame.pack(fill=tk.X, pady=10)

        tk.Label(total_frame, text="Total Amount:", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        tk.Label(total_frame, text=f"${purchase.get_total():.2f}",
                 font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=10)

        # Approval buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # If pending approval, show approve/reject buttons
        if purchase.status == "Pending":
            def approve():
                success, message = self.controllers["purchase"].approve_purchase(
                    purchase.id, self.current_approver)
                if success:
                    messagebox.showinfo("Success", message)
                    details_window.destroy()
                    self.refresh_pending_list()
                else:
                    messagebox.showerror("Error", message)

            def reject():
                # Ask for rejection notes
                notes_window = tk.Toplevel(details_window)
                notes_window.title("Rejection Notes")
                notes_window.geometry("400x250")
                notes_window.transient(details_window)
                notes_window.grab_set()

                tk.Label(notes_window, text="Please provide rejection notes:").pack(pady=10)

                notes_text = tk.Text(notes_window, height=5, width=40)
                notes_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

                def confirm_reject():
                    notes = notes_text.get("1.0", tk.END).strip()
                    if not notes:
                        messagebox.showerror("Error", "Please provide rejection notes")
                        return

                    success, message = self.controllers["purchase"].reject_purchase(
                        purchase.id, self.current_approver, notes)
                    if success:
                        messagebox.showinfo("Success", message)
                        notes_window.destroy()
                        details_window.destroy()
                        self.refresh_pending_list()
                    else:
                        messagebox.showerror("Error", message)

                button_frame = tk.Frame(notes_window)
                button_frame.pack(pady=10)

                tk.Button(button_frame, text="Cancel", command=notes_window.destroy).pack(side=tk.LEFT, padx=10)
                tk.Button(button_frame, text="Confirm Rejection", command=confirm_reject).pack(side=tk.LEFT, padx=10)

            tk.Button(button_frame, text="Approve", command=approve).pack(side=tk.LEFT, padx=10)
            tk.Button(button_frame, text="Reject", command=reject).pack(side=tk.LEFT, padx=10)

        # Close button
        tk.Button(main_frame, text="Close", command=details_window.destroy).pack(pady=10)

    def approve_selected(self):
        """Approve selected purchase"""
        selected_item = self.pending_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No purchase selected")
            return

        purchase_id = self.pending_tree.item(selected_item, "values")[0]

        if messagebox.askyesno("Confirm Approval", "Are you sure you want to approve this purchase?"):
            success, message = self.controllers["purchase"].approve_purchase(
                purchase_id, self.current_approver)
            if success:
                messagebox.showinfo("Success", message)
                self.refresh_pending_list()
            else:
                messagebox.showerror("Error", message)

    def reject_selected(self):
        """Reject selected purchase"""
        selected_item = self.pending_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No purchase selected")
            return

        purchase_id = self.pending_tree.item(selected_item, "values")[0]

        # Ask for rejection notes
        notes_window = tk.Toplevel(self.parent)
        notes_window.title("Rejection Notes")
        notes_window.geometry("400x250")
        notes_window.transient(self.parent)
        notes_window.grab_set()

        tk.Label(notes_window, text="Please provide rejection notes:").pack(pady=10)

        notes_text = tk.Text(notes_window, height=5, width=40)
        notes_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        def confirm_reject():
            notes = notes_text.get("1.0", tk.END).strip()
            if not notes:
                messagebox.showerror("Error", "Please provide rejection notes")
                return

            success, message = self.controllers["purchase"].reject_purchase(
                purchase_id, self.current_approver, notes)
            if success:
                messagebox.showinfo("Success", message)
                notes_window.destroy()
                self.refresh_pending_list()
            else:
                messagebox.showerror("Error", message)

        button_frame = tk.Frame(notes_window)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Cancel", command=notes_window.destroy).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Confirm Rejection", command=confirm_reject).pack(side=tk.LEFT, padx=10)

    def return_to_dashboard(self):
        """Return to main dashboard"""
        from views.main_dashboard import MainDashboard
        dashboard = MainDashboard(self.parent, self.controllers, self.show_view)
        self.show_view(dashboard)

    def show(self):
        """Show this view"""
        self.refresh_pending_list()
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """Hide this view"""
        self.frame.pack_forget()