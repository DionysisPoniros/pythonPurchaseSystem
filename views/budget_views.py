import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from models.budget import Budget
from utils.table_utils import configure_treeview

class BudgetListView:
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

        tk.Label(header_frame, text="Budget Management",
                 font=("Arial", 14, "bold")).pack(side=tk.LEFT)

        # Year selector
        year_frame = tk.Frame(header_frame)
        year_frame.pack(side=tk.RIGHT)

        tk.Label(year_frame, text="Fiscal Year:").pack(side=tk.LEFT)
        self.year_var = tk.StringVar(value=str(self.current_year))
        year_options = [str(y) for y in range(self.current_year - 5, self.current_year + 6)]
        year_dropdown = ttk.Combobox(year_frame, textvariable=self.year_var, values=year_options, width=6)
        year_dropdown.pack(side=tk.LEFT, padx=5)

        # Table frame
        table_frame = tk.Frame(self.frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Create treeview for budgets
        columns = ("ID", "Code", "Name", "Amount", "Spent", "Remaining", "Percent")
        self.budget_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.budget_tree = configure_treeview(self.budget_tree)
        # Set column headings
        for col in columns:
            self.budget_tree.heading(col, text=col)

        # Hide ID column
        self.budget_tree.column("ID", width=0, stretch=tk.NO)
        self.budget_tree.column("Code", width=80)
        self.budget_tree.column("Name", width=200)
        self.budget_tree.column("Amount", width=100)
        self.budget_tree.column("Spent", width=100)
        self.budget_tree.column("Remaining", width=100)
        self.budget_tree.column("Percent", width=100)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.budget_tree.yview)
        self.budget_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.budget_tree.pack(fill="both", expand=True)

        # Button frame
        button_frame = tk.Frame(self.frame)
        button_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Button(button_frame, text="Add Budget",
                  command=self.add_budget).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Edit Budget",
                  command=self.edit_budget).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Delete Budget",
                  command=self.delete_budget).pack(side=tk.LEFT, padx=5)

        # Bind year dropdown to update display
        self.year_var.trace_add("write", self.update_budget_display)

    def update_budget_display(self, *args):
        """Update budget display based on selected year"""
        self.budget_tree.delete(*self.budget_tree.get_children())

        selected_year = int(self.year_var.get())

        # Set up purchase controller reference if needed
        if self.controllers["budget"].purchase_controller is None:
            self.controllers["budget"].set_purchase_controller(self.controllers["purchase"])

        # Get budget usage data
        budget_data = self.controllers["budget"].calculate_budget_usage(selected_year)

        # Insert budget data
        for i, data in enumerate(budget_data):
            # Add row tags for styling
            row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            
            # Add status tag based on percentage
            if data['percent'] > 90:
                status_tag = 'pending'  # Red for near limit
            elif data['percent'] > 75:
                status_tag = 'partial'  # Yellow for warning
            else:
                status_tag = 'approved'  # Green for good
            
            self.budget_tree.insert("", "end", values=(
                data["id"],
                data["code"],
                data["name"],
                f"${data['amount']:,.2f}",
                f"${data['spent']:,.2f}",
                f"${data['remaining']:,.2f}",
                f"{data['percent']:.1f}%"
            ), tags=(row_tag, status_tag))

    def add_budget(self):
        """Open dialog to add a new budget"""
        self.open_budget_dialog()

    def edit_budget(self):
        """Open dialog to edit selected budget"""
        selected_item = self.budget_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No budget selected")
            return

        budget_id = self.budget_tree.item(selected_item, "values")[0]
        budget = self.controllers["budget"].get_budget_by_id(budget_id)

        if not budget:
            messagebox.showerror("Error", "Budget not found")
            return

        self.open_budget_dialog(budget)

    def delete_budget(self):
        """Delete selected budget"""
        selected_item = self.budget_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No budget selected")
            return

        budget_id = self.budget_tree.item(selected_item, "values")[0]

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this budget?"):
            success, message = self.controllers["budget"].delete_budget(budget_id)

            if success:
                messagebox.showinfo("Success", message)
                self.update_budget_display()
            else:
                messagebox.showerror("Error", message)

    def open_budget_dialog(self, budget=None):
        """Open dialog to add or edit a budget"""
        is_edit = budget is not None

        dialog = tk.Toplevel(self.parent)
        dialog.title("Edit Budget" if is_edit else "Add Budget")
        dialog.geometry("500x300")
        dialog.resizable(False, False)
        dialog.transient(self.parent)
        dialog.grab_set()

        # Budget form
        form_frame = tk.Frame(dialog, padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(form_frame, text="Budget Code:").grid(row=0, column=0, sticky="w", pady=5)
        code_var = tk.StringVar(value=budget.code if is_edit else "")
        code_entry = tk.Entry(form_frame, textvariable=code_var, width=10)
        code_entry.grid(row=0, column=1, sticky="w", pady=5)

        tk.Label(form_frame, text="Budget Name:").grid(row=1, column=0, sticky="w", pady=5)
        name_var = tk.StringVar(value=budget.name if is_edit else "")
        name_entry = tk.Entry(form_frame, textvariable=name_var, width=30)
        name_entry.grid(row=1, column=1, sticky="w", pady=5)

        tk.Label(form_frame, text="Description:").grid(row=2, column=0, sticky="w", pady=5)
        desc_var = tk.StringVar(value=budget.description if is_edit else "")
        desc_entry = tk.Entry(form_frame, textvariable=desc_var, width=40)
        desc_entry.grid(row=2, column=1, sticky="w", pady=5)

        # Year amount frame
        selected_year = self.year_var.get()
        year_amount_frame = tk.LabelFrame(form_frame, text=f"Budget Amount for {selected_year}")
        year_amount_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)

        tk.Label(year_amount_frame, text="Amount:").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        amount_var = tk.StringVar()

        if is_edit and selected_year in budget.yearly_amount:
            amount_var.set(str(budget.yearly_amount[selected_year]))
        else:
            amount_var.set("0.00")

        amount_entry = tk.Entry(year_amount_frame, textvariable=amount_var, width=15)
        amount_entry.grid(row=0, column=1, sticky="w", pady=5, padx=5)

        # Buttons
        button_frame = tk.Frame(form_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)

        def save_budget():
            code = code_var.get().strip()
            name = name_var.get().strip()
            amount_str = amount_var.get().strip()

            if not code:
                messagebox.showerror("Error", "Budget code is required")
                return

            if not name:
                messagebox.showerror("Error", "Budget name is required")
                return

            try:
                amount = float(amount_str)
                if amount < 0:
                    raise ValueError("Amount must be positive")
            except ValueError:
                messagebox.showerror("Error", "Amount must be a valid number")
                return

            if is_edit:
                # Update existing budget
                budget.code = code
                budget.name = name
                budget.description = desc_var.get().strip()

                # Ensure yearly_amount exists
                if not hasattr(budget, "yearly_amount") or budget.yearly_amount is None:
                    budget.yearly_amount = {}

                budget.yearly_amount[selected_year] = amount

                success, message = self.controllers["budget"].update_budget(budget)
            else:
                # Create new budget
                yearly_amount = {selected_year: amount}
                new_budget = Budget(
                    code=code,
                    name=name,
                    description=desc_var.get().strip(),
                    yearly_amount=yearly_amount
                )

                success, message = self.controllers["budget"].add_budget(new_budget)

            if success:
                dialog.destroy()
                messagebox.showinfo("Success", message)
                self.update_budget_display()
            else:
                messagebox.showerror("Error", message)

        tk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Save", command=save_budget).pack(side=tk.RIGHT, padx=5)

        # Focus on code field
        code_entry.focus_set()

    def return_to_dashboard(self):
        """Return to main dashboard"""
        from views.main_dashboard import MainDashboard
        dashboard = MainDashboard(self.parent, self.controllers, self.show_view)
        self.show_view(dashboard)

    def show(self):
        """Show this view"""
        self.update_budget_display()
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """Hide this view"""
        self.frame.pack_forget()