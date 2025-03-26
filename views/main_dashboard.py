import tkinter as tk
from datetime import datetime
from views.widgets.stats_card import StatsCard
from views.widgets.action_button import ActionButton
from config.settings import UI_COLORS
from views.purchase_views import PurchaseListView, PurchaseFormView
from views.vendor_views import VendorListView
from views.budget_views import BudgetListView
from views.report_views import BudgetReportView, VendorReportView
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from tkinter import messagebox

class MainDashboard:
    def __init__(self, parent, controllers, show_view_callback):
        self.parent = parent
        self.controllers = controllers
        self.show_view = show_view_callback

        self.frame = tk.Frame(parent)
        self.setup_ui()

    def setup_ui(self):
        # Header section
        header_frame = tk.Frame(self.frame, bg=UI_COLORS["header_bg"])
        header_frame.pack(fill=tk.X, padx=20, pady=10)

        title_label = tk.Label(header_frame, text="Purchase Management System",
                               font=("Arial", 20, "bold"), bg=UI_COLORS["header_bg"])
        title_label.pack(side=tk.LEFT, pady=10)

        # Current date display
        current_date = datetime.now().strftime("%B %d, %Y")
        date_label = tk.Label(header_frame, text=f"Today: {current_date}",
                              font=("Arial", 12), bg=UI_COLORS["header_bg"])
        date_label.pack(side=tk.RIGHT, pady=10)

        # Dashboard content (3-column layout)
        dashboard_frame = tk.Frame(self.frame)
        dashboard_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        left_frame = tk.Frame(dashboard_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        center_frame = tk.Frame(dashboard_frame)
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        right_frame = tk.Frame(dashboard_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        # Stats cards
        self.create_stats_cards(left_frame)
        self.create_action_buttons(center_frame)
        self.create_charts_and_activity(right_frame)
        # Add a menu bar


    def create_stats_cards(self, parent):
        # Create a frame for cards with shadow effect
        cards_frame = tk.Frame(parent, bg="#f0f0f0", padx=10, pady=10)
        cards_frame.pack(fill=tk.BOTH, expand=True)
        
        # Updated colors for better contrast and visibility
        card_colors = {
            "pending": "#ff7e7a",
            "orders": "#7aa7de",
            "spending": "#7ade94"
        }
        
        # Add card titles and icons
        card_data = [
            {
                "title": "Pending Orders",
                "value": self.controllers["purchase"].count_pending_orders(),
                "color": card_colors["pending"],
                "icon": "📋"  # Use Unicode icons if custom icons unavailable
            },
            {
                "title": "Total Orders (YTD)",
                "value": len(self.controllers["purchase"].get_current_year_purchases()),
                "color": card_colors["orders"],
                "icon": "📦"
            },
            {
                "title": "Total Spending (YTD)",
                "value": f"${self.controllers['purchase'].calculate_ytd_spending():,.2f}",
                "color": card_colors["spending"],
                "icon": "💰"
            }
        ]
    
        # Create the cards with the updated StatsCard class
        self.stat_cards = []
        for data in card_data:
            card = StatsCard(cards_frame, 
                            data["title"], 
                            data["value"], 
                            data["color"],
                            data["icon"])
            self.stat_cards.append(card)

    def create_action_buttons(self, parent):
        actions_card = tk.LabelFrame(parent, text="Actions", font=("Arial", 12, "bold"))
        actions_card.pack(fill=tk.BOTH, expand=True, pady=10)

        actions = [
            ("View Purchases", self.view_purchases, "icons/purchases.png"),
            ("Add Purchase", self.add_purchase, "icons/add.png"),
            ("Manage Vendors", self.manage_vendors, "icons/vendors.png"),
            ("Manage Budgets", self.manage_budgets, "icons/budgets.png"),
            ("Receiving Dashboard", self.receiving_dashboard, "icons/receiving.png"),
            ("Budget Reports", self.budget_reports, "icons/reports.png"),
            ("Vendor Reports", self.vendor_reports, "icons/vendors.png"),
            ("Exit System", self.exit_system, "icons/exit.png")
        ]

        # Create button grid
        row, col = 0, 0
        for text, command, icon_path in actions:
            ActionButton(actions_card, text, command, icon_path, row, col)
            col += 1
            if col > 2:  # 3 buttons per row
                col = 0
                row += 1

    def create_charts_and_activity(self, parent):
        # Budget overview chart
        chart_frame = tk.LabelFrame(parent, text="Budget Overview", font=("Arial", 12, "bold"))
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Calculate budget usage data
        self.controllers["budget"].set_purchase_controller(self.controllers["purchase"])
        budget_data = self.controllers["budget"].calculate_budget_usage()

        # Create a simple bar chart for budget usage
        if budget_data:
            # Only show top 5 budgets for readability
            sorted_data = sorted(budget_data, key=lambda x: x["percent"], reverse=True)[:5]

            fig, ax = plt.subplots(figsize=(4, 3), dpi=100)

            y_pos = range(len(sorted_data))
            percentages = [item["percent"] for item in sorted_data]
            names = [item["name"] for item in sorted_data]

            ax.barh(y_pos, percentages)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(names)
            ax.set_xlim(0, 100)
            ax.set_xlabel('% Used')
            ax.set_title('Budget Usage')

            canvas = FigureCanvasTkAgg(fig, chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            tk.Label(chart_frame, text="No budget data available").pack(pady=20)

        # Recent activity
        activity_frame = tk.LabelFrame(parent, text="Recent Activity", font=("Arial", 12, "bold"))
        activity_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Get recent purchases (last 5)
        recent_purchases = sorted(
            self.controllers["purchase"].get_all_purchases(),
            key=lambda p: datetime.strptime(p.date, "%Y-%m-%d"),
            reverse=True
        )[:5]

        if recent_purchases:
            for purchase in recent_purchases:
                activity_text = f"{purchase.date}: {purchase.order_number} - {purchase.vendor_name}"
                tk.Label(activity_frame, text=activity_text, anchor="w").pack(fill=tk.X, padx=5, pady=3)
        else:
            tk.Label(activity_frame, text="No recent activity").pack(pady=20)

    def refresh_dashboard(self):
        """Refresh dashboard data"""
        # Get current values
        card_values = [
            self.controllers["purchase"].count_pending_orders(),
            len(self.controllers["purchase"].get_current_year_purchases()),
            f"${self.controllers['purchase'].calculate_ytd_spending():,.2f}"
        ]
        
        # Update each card with its new value if stat_cards exist
        if hasattr(self, 'stat_cards') and self.stat_cards:
            for i, value in enumerate(card_values):
                if i < len(self.stat_cards):
                    self.stat_cards[i].update_value(value)
        else:
            # Find the left frame where the cards are located
            # Look first in the frame attribute
            container_frame = None
            if hasattr(self, 'frame'):
                # Try to find the dashboard_frame or equivalent
                for widget in self.frame.winfo_children():
                    if isinstance(widget, tk.Frame):
                        # This is likely the dashboard_frame
                        container_frame = widget
                        break
                        
            if container_frame:
                # Look for the left panel
                for widget in container_frame.winfo_children():
                    if isinstance(widget, tk.Frame):
                        # First frame is likely the left panel
                        self.create_stats_cards(widget)
                        break

        # Recreate charts and activity
        # (In a more advanced implementation, we would update these without rebuilding)

    # Navigation methods
    def view_purchases(self):
        """Open purchases list view"""
        purchase_list = PurchaseListView(self.parent, self.controllers, self.show_view)
        self.show_view(purchase_list)

    def receiving_dashboard(self):
        """Open receiving dashboard view"""
        from views.receiving_view import ReceivingDashboardView  # Import the new view
        receiving_view = ReceivingDashboardView(self.parent, self.controllers, self.show_view)
        self.show_view(receiving_view)

    def add_purchase(self):
        """Open add purchase form"""
        purchase_form = PurchaseFormView(self.parent, self.controllers, self.show_view)
        self.show_view(purchase_form)

    def manage_vendors(self):
        """Open vendor management view"""
        vendor_list = VendorListView(self.parent, self.controllers, self.show_view)
        self.show_view(vendor_list)

    def manage_budgets(self):
        """Open budget management view"""
        budget_list = BudgetListView(self.parent, self.controllers, self.show_view)
        self.show_view(budget_list)

    def budget_reports(self):
        """Open budget reports view"""
        budget_report = BudgetReportView(self.parent, self.controllers, self.show_view)
        self.show_view(budget_report)

    def vendor_reports(self):
        """Open vendor reports view"""
        vendor_report = VendorReportView(self.parent, self.controllers, self.show_view)
        self.show_view(vendor_report)

    def exit_system(self):
        """Exit the application"""
        exit()

    def show(self):
        """Show this view"""
        self.refresh_dashboard()
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """Hide this view"""
        self.frame.pack_forget()

    def create_action_buttons(self, parent):
        actions_card = tk.LabelFrame(parent, text="Actions", font=("Arial", 12, "bold"))
        actions_card.pack(fill=tk.BOTH, expand=True, pady=10)

        actions = [
            ("View Purchases", self.view_purchases, "icons/purchases.png"),
            ("Add Purchase", self.add_purchase, "icons/add.png"),
            ("Manage Vendors", self.manage_vendors, "icons/vendors.png"),
            ("Manage Budgets", self.manage_budgets, "icons/budgets.png"),
            ("Receiving Dashboard", self.receiving_dashboard, "icons/receiving.png"),
            ("Approval Dashboard", self.approval_dashboard, "icons/approval.png"),  # New button
            ("Budget Reports", self.budget_reports, "icons/reports.png"),
            ("Vendor Reports", self.vendor_reports, "icons/vendors.png"),
            ("Import Data", self.import_data, "icons/import.png"),  # New button
            ("Exit System", self.exit_system, "icons/exit.png")
        ]

        # Create button grid
        row, col = 0, 0
        for text, command, icon_path in actions:
            ActionButton(actions_card, text, command, icon_path, row, col)
            col += 1
            if col > 2:  # 3 buttons per row
                col = 0
                row += 1

    def approval_dashboard(self):
        """Open approval dashboard view"""
        from views.approval_view import ApprovalDashboardView
        approval_view = ApprovalDashboardView(self.parent, self.controllers, self.show_view)
        self.show_view(approval_view)

    def import_data(self):
        """Open import data dialog"""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Import Data from CSV"
        )

        if file_path:
            success, message = self.controllers["purchase"].data_manager.import_purchases_from_csv(file_path)

            if success:
                messagebox.showinfo("Import Successful", message)
                self.refresh_dashboard()
            else:
                messagebox.showerror("Import Failed", message)

