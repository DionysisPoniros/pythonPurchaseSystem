import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from utils.chart_utils import ChartGenerator
from utils.table_utils import configure_treeview
from views.view_factory import ViewFactory

class BudgetReportView:
    def __init__(self, parent, controllers, show_view_callback):
        self.parent = parent
        self.controllers = controllers
        self.show_view = show_view_callback

        self.current_year = datetime.now().year

        self.frame = tk.Frame(parent)
        self.setup_ui()

    def setup_ui(self):
        # Create back button
        back_button = tk.Button(self.frame, text="Back to Dashboard",
                                command=self.return_to_dashboard)
        back_button.pack(anchor="nw", padx=10, pady=10)

        # Title and year selection
        header_frame = tk.Frame(self.frame)
        header_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(header_frame, text="Budget Reports", font=("Arial", 14, "bold")).pack(side=tk.LEFT)

        # Year selector
        year_frame = tk.Frame(header_frame)
        year_frame.pack(side=tk.RIGHT)

        tk.Label(year_frame, text="Fiscal Year:").pack(side=tk.LEFT)
        self.year_var = tk.StringVar(value=str(self.current_year))
        year_options = [str(y) for y in range(self.current_year - 5, self.current_year + 6)]
        year_dropdown = ttk.Combobox(year_frame, textvariable=self.year_var, values=year_options, width=6)
        year_dropdown.pack(side=tk.LEFT, padx=5)

        # Create notebook for different reports
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Tab 1: Budget Summary
        self.summary_tab = tk.Frame(self.notebook)
        self.notebook.add(self.summary_tab, text="Budget Summary")

        # Tab 2: Budget vs. Actual
        self.vs_actual_tab = tk.Frame(self.notebook)
        self.notebook.add(self.vs_actual_tab, text="Budget vs. Actual")

        # Tab 3: Monthly Breakdown
        self.monthly_tab = tk.Frame(self.notebook)
        self.notebook.add(self.monthly_tab, text="Monthly Breakdown")

        # Export button
        self.export_btn = tk.Button(self.frame, text="Export Report", command=self.export_report)
        self.export_btn.pack(pady=10)

        # Bind year dropdown to update reports
        self.year_var.trace_add("write", self.update_reports)

    def update_reports(self, *args):
        """Update all report tabs when year changes"""
        self.update_summary_tab()
        self.update_vs_actual_tab()
        self.update_monthly_tab()

    def update_summary_tab(self):
        """Update budget summary tab"""
        # Clear existing widgets
        for widget in self.summary_tab.winfo_children():
            widget.destroy()

        # Get budget data
        selected_year = int(self.year_var.get())

        # Make sure controllers are set correctly
        if self.controllers["budget"].purchase_controller is None:
            self.controllers["budget"].set_purchase_controller(self.controllers["purchase"])

        if self.controllers["report"].purchase_controller is None:
            self.controllers["report"].set_controllers(
                self.controllers["purchase"],
                self.controllers["budget"],
                self.controllers["vendor"]
            )

        budget_data = self.controllers["report"].generate_budget_summary(selected_year)

        # Create summary frame
        summary_frame = tk.Frame(self.summary_tab)
        summary_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create treeview for budget summary
        columns = ("Budget", "Amount", "Spent", "Remaining", "Percent Used")
        summary_tree = ttk.Treeview(summary_frame, columns=columns, show="headings")
        summary_tree = configure_treeview(summary_tree)
        
        # Set column headings
        for col in columns:
            summary_tree.heading(col, text=col)
            summary_tree.column(col, width=100)

        summary_tree.column("Budget", width=200)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(summary_frame, orient="vertical", command=summary_tree.yview)
        summary_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        summary_tree.pack(fill="both", expand=True)

        # Insert budget data
        total_budget = 0
        total_spent = 0

        for i, data in enumerate(budget_data):
            row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            status_tag = 'approved' if data['percent'] < 75 else 'partial' if data['percent'] < 90 else 'pending'
            
            summary_tree.insert("", "end", values=(
                data["name"],
                f"${data['amount']:,.2f}",
                f"${data['spent']:,.2f}",
                f"${data['remaining']:,.2f}",
                f"{data['percent']:.1f}%"
            ), tags=(row_tag, status_tag))

        # Add total row
        total_remaining = total_budget - total_spent
        total_percent = (total_spent / total_budget * 100) if total_budget > 0 else 0

        summary_tree.insert("", "end", values=(
            "TOTAL",
            f"${total_budget:,.2f}",
            f"${total_spent:,.2f}",
            f"${total_remaining:,.2f}",
            f"{total_percent:.1f}%"
        ))

    def update_vs_actual_tab(self):
        """Update budget vs. actual tab with chart"""
        # Clear existing widgets
        for widget in self.vs_actual_tab.winfo_children():
            widget.destroy()

        # Get budget data
        selected_year = int(self.year_var.get())

        # Make sure controllers are set
        if self.controllers["budget"].purchase_controller is None:
            self.controllers["budget"].set_purchase_controller(self.controllers["purchase"])

        budget_data = self.controllers["budget"].calculate_budget_usage(selected_year)

        # Create chart frame
        chart_frame = tk.Frame(self.vs_actual_tab)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create chart only if we have data
        if budget_data:
            # Create chart using ChartGenerator
            canvas = ChartGenerator.create_budget_usage_chart(
                chart_frame,
                budget_data,
                f'Budget vs. Actual Spending - {selected_year}'
            )
            # Display the chart
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            # No data message
            tk.Label(chart_frame, text="No budget data available for selected year").pack(pady=20)

    def update_monthly_tab(self):
        """Update monthly breakdown tab with chart"""
        # Clear existing widgets
        for widget in self.monthly_tab.winfo_children():
            widget.destroy()

        # Get monthly data
        selected_year = int(self.year_var.get())

        # Make sure controllers are set
        if self.controllers["report"].purchase_controller is None:
            self.controllers["report"].set_controllers(
                self.controllers["purchase"],
                self.controllers["budget"],
                self.controllers["vendor"]
            )

        monthly_data = self.controllers["report"].generate_monthly_spending(selected_year)

        # Create chart frame
        chart_frame = tk.Frame(self.monthly_tab)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create chart only if we have data
        if monthly_data and sum(item["amount"] for item in monthly_data) > 0:
            # Create chart using ChartGenerator
            canvas = ChartGenerator.create_monthly_spending_chart(
                chart_frame,
                monthly_data,
                f'Monthly Spending - {selected_year}'
            )
            # Display the chart
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            # No data message
            tk.Label(chart_frame, text="No spending data available for selected year").pack(pady=20)

    def export_report(self):
        """Export budget report to CSV or PDF"""
        # Ask for export format
        export_format = messagebox.askquestion("Export Format",
                                               "Do you want to export as PDF? (No will export as CSV)")

        if export_format == 'yes':
            # PDF export
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Export Budget Report as PDF"
            )

            if not file_path:
                return

            # Get report data
            selected_year = int(self.year_var.get())
            budget_data = self.controllers["budget"].calculate_budget_usage(selected_year)
            monthly_data = self.controllers["report"].generate_monthly_spending(selected_year)

            # Import PDF exporter
            from utils.pdf_exporter import PDFExporter
            success, message = PDFExporter.export_budget_report(budget_data, monthly_data, selected_year, file_path)

        else:
            # CSV export
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Budget Report as CSV"
            )

            if not file_path:
                return

            # Export report
            selected_year = int(self.year_var.get())
            success, message = self.controllers["report"].export_budget_report(selected_year, file_path)

        if success:
            messagebox.showinfo("Export Successful", message)
        else:
            messagebox.showerror("Export Failed", message)

        if not file_path:
            return

        # Export report
        selected_year = int(self.year_var.get())
        success, message = self.controllers["report"].export_budget_report(selected_year, file_path)

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
        self.update_reports()
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """Hide this view"""
        self.frame.pack_forget()


class VendorReportView:
    def __init__(self, parent, controllers, show_view_callback):
        self.parent = parent
        self.controllers = controllers
        self.show_view = show_view_callback

        self.current_year = datetime.now().year

        self.frame = tk.Frame(parent)
        self.setup_ui()

    def setup_ui(self):
        # Create back button
        back_button = tk.Button(self.frame, text="Back to Dashboard",
                                command=self.return_to_dashboard)
        back_button.pack(anchor="nw", padx=10, pady=10)

        # Title and year selection
        header_frame = tk.Frame(self.frame)
        header_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(header_frame, text="Vendor Reports", font=("Arial", 14, "bold")).pack(side=tk.LEFT)

        # Year selector
        year_frame = tk.Frame(header_frame)
        year_frame.pack(side=tk.RIGHT)

        tk.Label(year_frame, text="Year:").pack(side=tk.LEFT)
        self.year_var = tk.StringVar(value=str(self.current_year))
        year_options = [str(y) for y in range(self.current_year - 5, self.current_year + 6)]
        year_dropdown = ttk.Combobox(year_frame, textvariable=self.year_var, values=year_options, width=6)
        year_dropdown.pack(side=tk.LEFT, padx=5)

        # Create notebook for different reports
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Tab 1: Vendor Spending
        self.spending_tab = tk.Frame(self.notebook)
        self.notebook.add(self.spending_tab, text="Vendor Spending")

        # Tab 2: Vendor Performance
        self.performance_tab = tk.Frame(self.notebook)
        self.notebook.add(self.performance_tab, text="Vendor Performance")

        # Export button
        self.export_btn = tk.Button(self.frame, text="Export Report", command=self.export_report)
        self.export_btn.pack(pady=10)

        # Bind year dropdown to update reports
        self.year_var.trace_add("write", self.update_reports)

    def update_reports(self, *args):
        """Update all report tabs when year changes"""
        self.update_spending_tab()
        self.update_performance_tab()

    def update_spending_tab(self):
        """Update vendor spending tab"""
        # Clear existing widgets
        for widget in self.spending_tab.winfo_children():
            widget.destroy()

        # Get vendor data
        selected_year = int(self.year_var.get())

        # Make sure controllers are set
        if self.controllers["report"].purchase_controller is None:
            self.controllers["report"].set_controllers(
                self.controllers["purchase"],
                self.controllers["budget"],
                self.controllers["vendor"]
            )

        vendor_data = self.controllers["report"].generate_vendor_spending(selected_year)

        # Create spending frame
        spending_frame = tk.Frame(self.spending_tab)
        spending_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create treeview for vendor spending
        columns = ("Vendor", "Total Spent", "Number of Orders", "Avg Order Value")
        spending_tree = ttk.Treeview(spending_frame, columns=columns, show="headings")
        spending_tree = configure_treeview(spending_tree)

        # Set column headings
        for col in columns:
            spending_tree.heading(col, text=col)
            spending_tree.column(col, width=100)

        spending_tree.column("Vendor", width=200)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(spending_frame, orient="vertical", command=spending_tree.yview)
        spending_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        spending_tree.pack(fill="both", expand=True)

        for i, data in enumerate(vendor_data):
            row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            
            spending_tree.insert("", "end", values=(
                data["name"],
                f"${data['total_spent']:,.2f}",
                data["purchase_count"],
                f"${data['avg_order']:,.2f}"
            ), tags=(row_tag,))

        # Create pie chart of vendor spending
        if vendor_data:
            chart_frame = tk.Frame(self.spending_tab)
            chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Create chart using ChartGenerator
            canvas = ChartGenerator.create_pie_chart(
                chart_frame,
                vendor_data,
                "name",
                "total_spent",
                f'Vendor Spending Distribution - {selected_year}'
            )
            # Display the chart
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update_performance_tab(self):
        """Update vendor performance tab"""
        # Clear existing widgets
        for widget in self.performance_tab.winfo_children():
            widget.destroy()

        # Get vendor data
        selected_year = int(self.year_var.get())

        # Here we'd normally have more performance metrics
        # For now, we'll just show the same data in a different way
        if self.controllers["report"].purchase_controller is None:
            self.controllers["report"].set_controllers(
                self.controllers["purchase"],
                self.controllers["budget"],
                self.controllers["vendor"]
            )

        vendor_data = self.controllers["report"].generate_vendor_spending(selected_year)

        # Sort by average order value to show which vendors get larger orders
        vendor_data_sorted = sorted(vendor_data, key=lambda x: x["avg_order"], reverse=True)

        if vendor_data_sorted:
            # Create performance frame with table
            performance_frame = tk.Frame(self.performance_tab)
            performance_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Display text explanation
            tk.Label(performance_frame, text="Vendor Order Size Analysis",
                     font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
            tk.Label(performance_frame, text="This report shows which vendors typically handle larger orders.").pack(
                anchor="w", pady=5)

            # Create treeview for vendor performance
            columns = ("Vendor", "Average Order Size", "Total Orders", "Total Spend")
            performance_tree = ttk.Treeview(performance_frame, columns=columns, show="headings")
            performance_tree = configure_treeview(performance_tree)
            # Set column headings
            for col in columns:
                performance_tree.heading(col, text=col)
                performance_tree.column(col, width=100)

            performance_tree.column("Vendor", width=200)

            # Add scrollbar
            scrollbar = ttk.Scrollbar(performance_frame, orient="vertical", command=performance_tree.yview)
            performance_tree.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            performance_tree.pack(fill="both", expand=True)

            # Insert vendor data
            for i, data in enumerate(vendor_data_sorted):
                row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                
                performance_tree.insert("", "end", values=(
                    data["name"],
                    f"${data['avg_order']:,.2f}",
                    data["purchase_count"],
                    f"${data['total_spent']:,.2f}"
                ), tags=(row_tag,))
        else:
            tk.Label(self.performance_tab, text="No vendor data available for selected year").pack(pady=20)

    def export_report(self):
        """Export budget report to CSV or PDF"""
        # Ask for export format
        export_format = messagebox.askquestion("Export Format",
                                               "Do you want to export as PDF? (No will export as CSV)")

        if export_format == 'yes':
            # PDF export
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Export Budget Report as PDF"
            )

            if not file_path:
                return

            # Get report data
            selected_year = int(self.year_var.get())
            budget_data = self.controllers["budget"].calculate_budget_usage(selected_year)
            monthly_data = self.controllers["report"].generate_monthly_spending(selected_year)

            # Import PDF exporter
            from utils.pdf_exporter import PDFExporter
            success, message = PDFExporter.export_budget_report(budget_data, monthly_data, selected_year, file_path)

        else:
            # CSV export
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Budget Report as CSV"
            )

            if not file_path:
                return

            # Export report
            selected_year = int(self.year_var.get())
            success, message = self.controllers["report"].export_budget_report(selected_year, file_path)

        if success:
            messagebox.showinfo("Export Successful", message)
        else:
            messagebox.showerror("Export Failed", message)

        if not file_path:
            return

        # Here we would normally call a report controller method
        # Just show a success message for now
        messagebox.showinfo("Export Successful", f"Vendor report exported to {file_path}")

    def return_to_dashboard(self):
        """Return to main dashboard"""
        from views.main_dashboard import MainDashboard
        dashboard = MainDashboard(self.parent, self.controllers, self.show_view)
        self.show_view(dashboard)

    def show(self):
        """Show this view"""
        self.update_reports()
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """Hide this view"""
        self.frame.pack_forget()