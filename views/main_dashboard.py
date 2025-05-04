# purchase_system/views/main_dashboard.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog # Added ttk
from datetime import datetime
# Removed direct StatsCard/ActionButton imports if not used in new design, or keep if adapted
# from views.widgets.stats_card import StatsCard
# from views.widgets.action_button import ActionButton
from config.settings import UI_COLORS, UI_FONTS # Added UI_FONTS
from views.view_factory import ViewFactory
from utils.chart_utils import ChartGenerator # Import ChartGenerator
from utils.table_utils import configure_treeview # Import Treeview config

class MainDashboard:
    def __init__(self, parent, controllers, show_view_callback):
        self.parent = parent
        self.controllers = controllers
        self.show_view = show_view_callback
        # Ensure purchase controller is set for budget controller if needed early
        self.controllers["budget"].set_purchase_controller(self.controllers["purchase"])
        # Ensure report controller has references if needed early
        self.controllers["report"].set_controllers(
            self.controllers["purchase"],
            self.controllers["budget"],
            self.controllers["vendor"]
        )

        # --- Main Frame ---
        self.frame = ttk.Frame(parent, padding="10 10 10 10") # Use ttk.Frame and add padding
        self.frame.pack(fill=tk.BOTH, expand=True) # Make frame fill window

        # Configure grid columns (1fr for main, auto for sidebar)
        self.frame.columnconfigure(0, weight=3) # Main content column (larger weight)
        self.frame.columnconfigure(1, weight=1) # Sidebar column
        self.frame.rowconfigure(1, weight=1) # Allow content row to expand

        self.setup_ui()

    def setup_ui(self):
        # --- Header ---
        header_frame = ttk.Frame(self.frame, style='Header.TFrame') # Style for header
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        style = ttk.Style()
        style.configure('Header.TFrame', background=UI_COLORS.get("header_bg", "#e0e0e0"))

        title_label = ttk.Label(header_frame, text="Purchase Management Dashboard",
                               font=UI_FONTS.get("title", ("Arial", 16, "bold")),
                               style='Header.TLabel', background=UI_COLORS.get("header_bg", "#e0e0e0"))
        title_label.pack(side=tk.LEFT, padx=10, pady=5)
        style.configure('Header.TLabel', background=UI_COLORS.get("header_bg", "#e0e0e0"))

        current_date = datetime.now().strftime("%B %d, %Y")
        date_label = ttk.Label(header_frame, text=f"Today: {current_date}",
                              font=UI_FONTS.get("default", ("Arial", 10)),
                              style='Header.TLabel')
        date_label.pack(side=tk.RIGHT, padx=10, pady=5)

        # --- Left Column (Main Content) ---
        left_column = ttk.Frame(self.frame, padding="5")
        left_column.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        left_column.rowconfigure(1, weight=1) # Allow pending actions to expand
        left_column.rowconfigure(2, weight=1)
        left_column.columnconfigure(0, weight=1)

        self.create_kpi_section(left_column)
        self.create_pending_approvals_section(left_column)
        self.create_pending_receipts_section(left_column)

        # --- Right Column (Sidebar) ---
        right_column = ttk.Frame(self.frame, padding="5")
        right_column.grid(row=1, column=1, sticky="nsew", padx=(5, 0))
        right_column.rowconfigure(1, weight=1) # Allow chart to expand
        right_column.columnconfigure(0, weight=1)

        self.create_navigation_panel(right_column)
        self.create_budget_overview_chart(right_column)

        # Initial data load
        self.refresh_dashboard_data()


    def create_kpi_section(self, parent):
        """Creates the Key Performance Indicator section."""
        kpi_frame = ttk.Frame(parent, style='Card.TFrame')
        kpi_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        kpi_frame.columnconfigure(0, weight=1)
        kpi_frame.columnconfigure(1, weight=1)
        kpi_frame.columnconfigure(2, weight=1)

        style = ttk.Style()
        style.configure('Card.TFrame', background='white', relief='raised', borderwidth=1)
        style.configure('KPI.TLabel', background='white', anchor='center', font=UI_FONTS.get("default"))
        style.configure('KPIValue.TLabel', background='white', anchor='center', font=UI_FONTS.get("large"))

        # Placeholder labels - values updated in refresh_dashboard_data
        self.pending_approval_kpi = ttk.Label(kpi_frame, text="0", style='KPIValue.TLabel')
        self.pending_receipt_kpi = ttk.Label(kpi_frame, text="0", style='KPIValue.TLabel')
        self.ytd_spending_kpi = ttk.Label(kpi_frame, text="$0.00", style='KPIValue.TLabel')

        ttk.Label(kpi_frame, text="Pending Approvals", style='KPI.TLabel').grid(row=0, column=0, pady=(5,0))
        self.pending_approval_kpi.grid(row=1, column=0, pady=(0,5))
        ttk.Button(kpi_frame, text="View >", style='Link.TButton',
                   command=self.approval_dashboard).grid(row=2, column=0, pady=(0,5))

        ttk.Label(kpi_frame, text="Awaiting Receipt", style='KPI.TLabel').grid(row=0, column=1, pady=(5,0))
        self.pending_receipt_kpi.grid(row=1, column=1, pady=(0,5))
        ttk.Button(kpi_frame, text="View >", style='Link.TButton',
                   command=self.receiving_dashboard).grid(row=2, column=1, pady=(0,5))

        ttk.Label(kpi_frame, text="YTD Spending", style='KPI.TLabel').grid(row=0, column=2, pady=(5,0))
        self.ytd_spending_kpi.grid(row=1, column=2, pady=(0,5))
        # No link needed for YTD spending, maybe link to reports?

        style.configure('Link.TButton', padding=0, relief='flat', foreground='blue', font=(UI_FONTS.get("default")[0], UI_FONTS.get("default")[1], 'underline'))


    def create_pending_approvals_section(self, parent):
        """Creates section to show top pending approvals."""
        frame = ttk.LabelFrame(parent, text="Action Required: Pending Approvals", padding="10")
        frame.grid(row=1, column=0, sticky="nsew", pady=5)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        cols = ("Order #", "Vendor", "Total")
        self.pending_approval_tree = ttk.Treeview(frame, columns=cols, show='headings', height=4) # Limit height
        self.pending_approval_tree = configure_treeview(self.pending_approval_tree)

        for col in cols:
            self.pending_approval_tree.heading(col, text=col)
        self.pending_approval_tree.column("Order #", width=80)
        self.pending_approval_tree.column("Vendor", width=150)
        self.pending_approval_tree.column("Total", width=80, anchor='e')

        # No scrollbar needed for short list, but can add if desired
        self.pending_approval_tree.grid(row=0, column=0, sticky="nsew")
        self.pending_approval_tree.bind("<Double-1>", lambda e: self.approval_dashboard()) # Double-click goes to full view


    def create_pending_receipts_section(self, parent):
        """Creates section to show top pending receipts."""
        frame = ttk.LabelFrame(parent, text="Action Required: Pending Receipts", padding="10")
        frame.grid(row=2, column=0, sticky="nsew", pady=5)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        cols = ("Order #", "Vendor", "Days Out")
        self.pending_receipt_tree = ttk.Treeview(frame, columns=cols, show='headings', height=4) # Limit height
        self.pending_receipt_tree = configure_treeview(self.pending_receipt_tree)

        for col in cols:
            self.pending_receipt_tree.heading(col, text=col)
        self.pending_receipt_tree.column("Order #", width=80)
        self.pending_receipt_tree.column("Vendor", width=150)
        self.pending_receipt_tree.column("Days Out", width=80, anchor='center')

        self.pending_receipt_tree.grid(row=0, column=0, sticky="nsew")
        self.pending_receipt_tree.bind("<Double-1>", lambda e: self.receiving_dashboard()) # Double-click goes to full view


    def create_navigation_panel(self, parent):
        """Creates the main navigation buttons in the sidebar."""
        nav_frame = ttk.LabelFrame(parent, text="Navigation", padding="10")
        nav_frame.grid(row=0, column=0, sticky="nsew", pady=(0,10))
        nav_frame.columnconfigure(0, weight=1) # Allow buttons to expand

        nav_actions = [
            ("➕ Add Purchase", self.add_purchase),
            ("🧾 View Purchases", self.view_purchases),
            ("🛒 Manage Vendors", self.manage_vendors),
            ("💰 Manage Budgets", self.manage_budgets),
            ("📊 Reports", self.show_reports_menu), # Changed to menu trigger
            ("📥 Import Purchases", self.import_data),
            
            ("🚪 Exit System", self.exit_system),
        ]

        for i, (text, command) in enumerate(nav_actions):
            button = ttk.Button(nav_frame, text=text, command=command, style='Nav.TButton')
            button.grid(row=i, column=0, sticky="ew", pady=4)

        style = ttk.Style()
        style.configure('Nav.TButton', font=UI_FONTS.get("default"), padding=6)


    def create_budget_overview_chart(self, parent):
        """Creates the budget overview donut chart placeholder."""
        self.budget_chart_frame = ttk.LabelFrame(parent, text="YTD Budget Overview", padding="10")
        self.budget_chart_frame.grid(row=1, column=0, sticky="nsew", pady=5)
        self.budget_chart_frame.columnconfigure(0, weight=1)
        self.budget_chart_frame.rowconfigure(0, weight=1)

        # Placeholder label, chart canvas added during refresh
        self.budget_chart_canvas_widget = None # Initialize placeholder


    def refresh_dashboard_data(self):
        """Fetches fresh data and updates all relevant dashboard widgets."""
        # --- Refresh KPIs ---
        try:
            pending_approvals = len(self.controllers["purchase"].get_purchases_by_approval_status("Pending"))
            # Assuming count_pending_orders counts orders needing items received
            pending_receipts = self.controllers["purchase"].count_pending_orders()
            ytd_spending = self.controllers["purchase"].calculate_ytd_spending()

            self.pending_approval_kpi.config(text=str(pending_approvals))
            self.pending_receipt_kpi.config(text=str(pending_receipts))
            self.ytd_spending_kpi.config(text=f"${ytd_spending:,.2f}")
        except Exception as e:
            print(f"Error refreshing KPIs: {e}")
            self.pending_approval_kpi.config(text="Error")
            self.pending_receipt_kpi.config(text="Error")
            self.ytd_spending_kpi.config(text="Error")

        # --- Refresh Pending Approvals List ---
        if hasattr(self, 'pending_approval_tree') and self.pending_approval_tree.winfo_exists():
            self.pending_approval_tree.delete(*self.pending_approval_tree.get_children())
            try:
                # Fetch top 5 pending approvals (modify controller if needed)
                pending_approvals_list = self.controllers["purchase"].get_purchases_by_approval_status("Pending")[:5]
                for i, p in enumerate(pending_approvals_list):
                    self.pending_approval_tree.insert("", "end", values=(
                        p.order_number or "N/A",
                        p.vendor_name or "N/A",
                        f"${p.get_total():,.2f}"
                    ), tags=('evenrow' if i % 2 == 0 else 'oddrow', 'pending'))
            except Exception as e:
                print(f"Error refreshing pending approvals list: {e}")
                self.pending_approval_tree.insert("", "end", values=("Error loading data", "", ""))

        # --- Refresh Pending Receipts List ---
        if hasattr(self, 'pending_receipt_tree') and self.pending_receipt_tree.winfo_exists():
            self.pending_receipt_tree.delete(*self.pending_receipt_tree.get_children())
            try:
                # Fetch top 5 pending receipts (needs controller logic or filter here)
                all_purchases = self.controllers["purchase"].get_all_purchases()
                pending_receipt_list = [
                    p for p in all_purchases if not p.is_received() and p.status != 'Rejected'
                ]
                # Sort by date/days outstanding if needed before slicing
                today = datetime.now().date()
                pending_receipt_list.sort(key=lambda p: p.date or '0000-00-00') # Sort oldest first
                for i, p in enumerate(pending_receipt_list[:5]): # Slice top 5
                     days_out = "N/A"
                     try:
                         p_date = datetime.strptime(p.date, "%Y-%m-%d").date()
                         days_out = (today - p_date).days
                     except: pass
                     self.pending_receipt_tree.insert("", "end", values=(
                         p.order_number or "N/A",
                         p.vendor_name or "N/A",
                         days_out
                     ), tags=('evenrow' if i % 2 == 0 else 'oddrow', 'partial' if days_out == "N/A" or days_out < 14 else 'pending'))
            except Exception as e:
                print(f"Error refreshing pending receipts list: {e}")
                self.pending_receipt_tree.insert("", "end", values=("Error loading data", "", ""))

        # --- Refresh Budget Overview Chart ---
        if hasattr(self, 'budget_chart_frame') and self.budget_chart_frame.winfo_exists():
            # Clear previous chart
            if self.budget_chart_canvas_widget:
                self.budget_chart_canvas_widget.destroy()
                self.budget_chart_canvas_widget = None

            try:
                # Get overall budget summary (needs controller method)
                # Example: Assuming controller returns {'total_budget': N, 'total_spent': M}
                # For now, calculate manually from budget_usage
                budget_usage = self.controllers["budget"].calculate_budget_usage() # Gets usage for current year by default
                total_budget = sum(b['amount'] for b in budget_usage)
                total_spent = sum(b['spent'] for b in budget_usage)

                if total_budget > 0:
                    remaining = total_budget - total_spent
                    chart_data = [
                        {'label': 'Spent', 'value': total_spent},
                        {'label': 'Remaining', 'value': remaining if remaining > 0 else 0} # Don't show negative remaining
                    ]
                    chart_colors = [UI_COLORS.get("pending", "#ffcccb"), UI_COLORS.get("approved", "#ccffcc")]

                    # Use ChartGenerator for pie/donut chart
                    canvas = ChartGenerator.create_pie_chart(
                        self.budget_chart_frame,
                        chart_data,
                        label_field='label',
                        value_field='value',
                        title=f"Total Budget: ${total_budget:,.0f}" # Add total to title
                    )
                    self.budget_chart_canvas_widget = canvas.get_tk_widget()
                    self.budget_chart_canvas_widget.grid(row=0, column=0, sticky="nsew")
                else:
                    ttk.Label(self.budget_chart_frame, text="No budget data for current year.", anchor='center').grid(row=0, column=0, sticky="nsew")

            except Exception as e:
                print(f"Error refreshing budget chart: {e}")
                ttk.Label(self.budget_chart_frame, text="Error loading chart.", anchor='center').grid(row=0, column=0, sticky="nsew")


    # --- Navigation Methods ---
    # (Keep existing navigation methods like view_purchases, add_purchase, etc.)
    # Make sure they use ViewFactory correctly

    def show_reports_menu(self):
         """Placeholder for showing a reports submenu or navigating directly."""
         # Option 1: Simple navigation to first report
         self.budget_reports()
         # Option 2: Create a small Toplevel window with report choices
         # report_menu = tk.Toplevel(self.frame)
         # report_menu.title("Reports")
         # ttk.Button(report_menu, text="Budget Reports", command=self.budget_reports).pack(pady=5)
         # ttk.Button(report_menu, text="Vendor Reports", command=self.vendor_reports).pack(pady=5)
         # report_menu.transient(self.frame)
         # report_menu.grab_set()

    def show_db_management(self):
         """Triggers the DB management dialog from the main app instance."""
         # The DB management dialog logic is currently in app.py
         # We need a way to call it from here.
         # Option 1: Pass the app instance or a callback during init (complex)
         # Option 2: Replicate the dialog logic here (code duplication)
         # Option 3 (Chosen): Assume app has a method, try calling it (might fail if not structured this way)
         try:
              # This assumes the root Tk instance has a reference to the PurchaseApp instance
              # And PurchaseApp has the show_db_management method. This might need adjustment
              # based on your actual app structure in app.py
              app_instance = self.frame.winfo_toplevel() # Get the root window
              if hasattr(app_instance, 'show_db_management'):
                   app_instance.show_db_management()
              else:
                   messagebox.showwarning("Not Implemented", "DB Management access from here is not set up.")
         except Exception as e:
              print(f"Error accessing DB Management: {e}")
              messagebox.showerror("Error", "Could not open DB Management.")

    # --- Existing Navigation methods using ViewFactory (ensure they are present) ---
    def view_purchases(self):
        purchase_list = ViewFactory.create_view('PurchaseListView', self.parent, self.controllers, self.show_view)
        self.show_view(purchase_list)

    def add_purchase(self):
        purchase_form = ViewFactory.create_view('PurchaseFormView', self.parent, self.controllers, self.show_view)
        self.show_view(purchase_form)

    def manage_vendors(self):
        vendor_list = ViewFactory.create_view('VendorListView', self.parent, self.controllers, self.show_view)
        self.show_view(vendor_list)

    def manage_budgets(self):
        budget_list = ViewFactory.create_view('BudgetListView', self.parent, self.controllers, self.show_view)
        self.show_view(budget_list)

    def budget_reports(self):
        budget_report = ViewFactory.create_view('BudgetReportView', self.parent, self.controllers, self.show_view)
        self.show_view(budget_report)

    def vendor_reports(self):
        vendor_report = ViewFactory.create_view('VendorReportView', self.parent, self.controllers, self.show_view)
        self.show_view(vendor_report)

    def receiving_dashboard(self):
        receiving_view = ViewFactory.create_view('ReceivingDashboardView', self.parent, self.controllers, self.show_view)
        self.show_view(receiving_view)

    def approval_dashboard(self):
        approval_view = ViewFactory.create_view('ApprovalDashboardView', self.parent, self.controllers, self.show_view)
        self.show_view(approval_view)

    def import_data(self):
        file_path = filedialog.askopenfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Import Purchases from CSV"
        )
        if file_path:
            if hasattr(self.controllers["purchase"], "import_purchases_from_csv"):
                success, message = self.controllers["purchase"].import_purchases_from_csv(file_path)
                if success:
                    messagebox.showinfo("Import Successful", message)
                    self.refresh_dashboard_data() # Refresh data after import
                else:
                    messagebox.showerror("Import Failed", message)
            else: # Fallback/error if method doesn't exist
                 messagebox.showerror("Import Error", "Import function not found in controller.")


    def exit_system(self):
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.parent.quit() # Use parent which should be the root Tk instance

    # --- Show/Hide ---
    def show(self):
        self.refresh_dashboard_data() # Refresh data when shown
        self.frame.pack(fill=tk.BOTH, expand=True) # Use pack for the main frame if preferred

    def hide(self):
        self.frame.pack_forget() # Use pack_forget if using pack
        # Or use grid_forget if using grid for self.frame
        # self.frame.grid_forget()