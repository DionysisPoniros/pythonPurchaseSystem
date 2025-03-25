from datetime import datetime
from models.budget import Budget


class BudgetController:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.purchase_controller = None  # Will be set after initialization

    def set_purchase_controller(self, purchase_controller):
        """Set the purchase controller reference"""
        self.purchase_controller = purchase_controller

    def get_all_budgets(self):
        """Get all budgets as Budget objects"""
        budgets_data = self.data_manager.get_budgets()
        return [Budget.from_dict(b) for b in budgets_data]

    def get_budget_by_id(self, budget_id):
        """Get a budget by ID"""
        budgets = self.data_manager.get_budgets()
        budget_data = next((b for b in budgets if b.get("id") == budget_id), None)
        if budget_data:
            return Budget.from_dict(budget_data)
        return None

    def add_budget(self, budget):
        """Add a new budget"""
        budgets = self.data_manager.get_budgets()

        # Check if budget code already exists
        if any(b.get("code") == budget.code for b in budgets):
            return False, "A budget with this code already exists"

        budgets.append(budget.to_dict())
        self.data_manager.save_budgets(budgets)
        return True, "Budget added successfully"

    def update_budget(self, budget):
        """Update an existing budget"""
        budgets = self.data_manager.get_budgets()

        # Check if budget code already exists (for a different budget)
        if any(b.get("code") == budget.code and b.get("id") != budget.id for b in budgets):
            return False, "A budget with this code already exists"

        for i, b in enumerate(budgets):
            if b.get("id") == budget.id:
                budgets[i] = budget.to_dict()
                self.data_manager.save_budgets(budgets)
                return True, "Budget updated successfully"

        return False, "Budget not found"

    def delete_budget(self, budget_id):
        """Delete a budget by ID"""
        # First check if budget is used in any purchases
        purchases = self.data_manager.get_purchases()
        if any(any(b.get("budget_id") == budget_id for b in p.get("budgets", [])) for p in purchases):
            return False, "Cannot delete budget that is used in purchases"

        budgets = self.data_manager.get_budgets()
        initial_count = len(budgets)
        budgets = [b for b in budgets if b.get("id") != budget_id]

        if len(budgets) < initial_count:
            self.data_manager.save_budgets(budgets)
            return True, "Budget deleted successfully"

        return False, "Budget not found"

    def get_budget_options(self):
        """Get a list of budget options for dropdowns"""
        return [(b.id, b.name) for b in self.get_all_budgets()]

    def calculate_budget_usage(self, year=None):
        """Calculate budget usage for a specific year"""
        year = year or datetime.now().year

        if not self.purchase_controller:
            raise RuntimeError("Purchase controller not set. Call set_purchase_controller first.")

        budgets = self.get_all_budgets()
        purchases = self.purchase_controller.get_purchase_by_year(year)

        # Calculate spent amounts for each budget
        budget_spent = {}
        for purchase in purchases:
            for budget_alloc in purchase.budgets:
                budget_id = budget_alloc.get("budget_id")
                amount = budget_alloc.get("amount", 0)
                budget_spent[budget_id] = budget_spent.get(budget_id, 0) + amount

        # Build usage data
        result = []
        for budget in budgets:
            budget_amount = budget.get_amount_for_year(str(year))
            spent = budget_spent.get(budget.id, 0)
            remaining = budget_amount - spent

            # Calculate percentage used
            percent = (spent / budget_amount * 100) if budget_amount > 0 else 0

            result.append({
                "id": budget.id,
                "code": budget.code,
                "name": budget.name,
                "amount": budget_amount,
                "spent": spent,
                "remaining": remaining,
                "percent": percent
            })

        return result