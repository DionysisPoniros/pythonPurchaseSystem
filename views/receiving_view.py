import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from utils.chart_utils import ChartGenerator

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

        # Status counts
        status_frame = tk.Frame(self.frame)
        status_frame.pack(fill=tk.X, padx=20, pady=10)

        # Calculate status counts
        purchases = self.controllers["purchase"].get_all_purchases()
        pending_count = 0
        partial_count = 0
        received_count = 0

        for purchase in purchases:
            if purchase.is_received():
                received_count += 1
            elif purchase.is_partially_received():
                partial_count += 1
            else:
                pending_count += 1

        # Status cards
        status_data = [
            ("Pending", pending_count, "#ffcccb"),
            ("Partially Received", partial_count, "#ffffcc"),
            ("Fully Received", received_count, "#ccffcc")
        ]

        for title, count, color in status_data:
            card = tk.Frame(status_frame, bg=color, bd=1, relief=tk.RAISED)
            card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

            tk.Label(card, text=title, font=("Arial", 12, "bold"), bg=color).pack(pady=(10, 5))
            tk.Label(card, text=str(count), font=("Arial", 24), bg=color).pack(pady=(5, 10))

        # Pending items
        pending_frame = tk.LabelFrame(self.frame, text="Pending Receipts")
        pending_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Create treeview for pending items
        columns = ("ID", "Order #", "Vendor", "Date", "Items", "Days Outstanding")
        pending_tree = ttk.Treeview(pending_frame, columns=columns, show="headings")

        # Set column headings
        for col in columns:
            pending_tree.heading(col, text=col)

        # Hide ID column
        pending_tree.column("ID", width=0, stretch=tk.NO)
        pending_tree.column("Order #", width=100)
        pending_tree.column("Vendor", width=150)
        pending_tree.column("Date", width=100)
        pending_tree.column("Items", width=300)
        pending_tree.column("Days Outstanding", width=120)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(pending_frame, orient="vertical", command=pending_tree.yview)
        pending_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        pending_tree.pack(fill="both", expand=True)

        # Insert pending items
        today = datetime.now().date()

        for purchase in purchases:
            # Skip if all items received
            if purchase.is_received():
                continue

            # Calculate days outstanding
            try:
                purchase_date = datetime.strptime(purchase.date, "%Y-%m-%d").date()
                days_outstanding = (today - purchase_date).days
            except ValueError:
                days_outstanding = "N/A"

            # Get pending items
            pending_items = [
                item.get("description") for item in purchase.line_items
                if not item.get("received", False)
            ]
            pending_text = ", ".join(pending_items)
            if len(pending_text) > 50:
                pending_text = pending_text[:47] + "..."

            pending_tree.insert("", "end", values=(
                purchase.id,
                purchase.order_number,
                purchase.vendor_name,
                purchase.date,
                pending_text,
                days_outstanding
            ))

        # Button to receive items
        def receive_selected():
            selected = pending_tree.selection()
            if not selected:
                messagebox.showerror("Error", "No order selected")
                return

            purchase_id = pending_tree.item(selected, "values")[0]
            purchase = self.controllers["purchase"].get_purchase_by_id(purchase_id)

            if not purchase:
                messagebox.showerror("Error", "Purchase not found")
                return

            # Call the purchase view's receive_items method
            from views.purchase_views import PurchaseListView
            purchase_view = PurchaseListView(self.parent, self.controllers, self.show_view)
            purchase_view.receive_items()

            # Refresh display after receiving
            self.refresh_dashboard()

        button_frame = tk.Frame(self.frame)
        button_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Button(button_frame, text="Receive Selected Items",
                  command=receive_selected).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Refresh Dashboard",
                  command=self.refresh_dashboard).pack(side=tk.LEFT, padx=5)

    def refresh_dashboard(self):
        """Refresh the dashboard with current data"""
        self.hide()
        self.__init__(self.parent, self.controllers, self.show_view)
        self.show()

    def return_to_dashboard(self):
        """Return to main dashboard"""
        from views.main_dashboard import MainDashboard
        dashboard = MainDashboard(self.parent, self.controllers, self.show_view)
        self.show_view(dashboard)

    def show(self):
        """Show this view"""
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """Hide this view"""
        self.frame.pack_forget()