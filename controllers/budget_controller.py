# controllers/budget_controller.py
from datetime import datetime
from database.models import Budget, YearlyBudgetAmount, PurchaseBudget, Purchase
from sqlalchemy.orm import joinedload
import uuid

class BudgetController:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.purchase_controller = None  # Will be set after initialization

    def set_purchase_controller(self, purchase_controller):
        """Set the purchase controller reference"""
        self.purchase_controller = purchase_controller

    def get_all_budgets(self):
        """Get all budgets with eager loading of yearly amounts"""
        session = self.db_manager.Session()
        try:
            return session.query(Budget).options(joinedload(Budget.yearly_amounts)).all()
        finally:
            session.close()

    def get_budget_by_id(self, budget_id):
        """Get a budget by ID with eager loading of yearly amounts"""
        session = self.db_manager.Session()
        try:
            return session.query(Budget).filter(Budget.id == budget_id).options(
                joinedload(Budget.yearly_amounts)
            ).first()
        finally:
            session.close()

    def add_budget(self, budget_data):
        """Add a new budget with yearly amounts"""
        session = self.db_manager.Session()
        try:
            # Check if budget code already exists
            existing = session.query(Budget).filter(Budget.code == budget_data.get('code')).first()
            if existing:
                return False, "A budget with this code already exists"
            
            # Extract yearly amount data before creating budget
            yearly_amount_data = budget_data.pop('yearly_amount', {}) if 'yearly_amount' in budget_data else {}
            
            # Create new budget without yearly amount
            budget = Budget(
                id=budget_data.get('id') or str(uuid.uuid4()),
                code=budget_data.get('code', ''),
                name=budget_data.get('name', ''),
                description=budget_data.get('description', '')
            )
            
            session.add(budget)
            session.flush()  # Flush to get ID
            
            # Now add yearly amounts as separate objects
            for year, amount in yearly_amount_data.items():
                yearly_amount = YearlyBudgetAmount(
                    id=str(uuid.uuid4()),
                    budget_id=budget.id,
                    year=str(year),
                    amount=float(amount)
                )
                session.add(yearly_amount)
            
            session.commit()
            return True, "Budget added successfully"
        except Exception as e:
            session.rollback()
            return False, f"Failed to add budget: {str(e)}"
        finally:
            session.close()

    def update_budget(self, budget_data):
        """Update an existing budget with yearly amounts"""
        session = self.db_manager.Session()
        try:
            budget_id = budget_data.get('id')
            if not budget_id:
                return False, "Budget ID is required"
            
            # Check if budget exists
            budget = session.query(Budget).filter(Budget.id == budget_id).first()
            if not budget:
                return False, "Budget not found"
            
            # Check if budget code already exists (for a different budget)
            code = budget_data.get('code')
            existing = session.query(Budget).filter(
                Budget.code == code, Budget.id != budget_id
            ).first()
            
            if existing:
                return False, "A budget with this code already exists"
            
            # Update budget fields
            budget.code = budget_data.get('code', budget.code)
            budget.name = budget_data.get('name', budget.name)
            budget.description = budget_data.get('description', budget.description)
            
            # Handle yearly amounts
            yearly_amount_data = budget_data.get('yearly_amount', {})
            if yearly_amount_data:
                # For each year in the data
                for year, amount in yearly_amount_data.items():
                    # Check if this year already exists
                    existing_amount = session.query(YearlyBudgetAmount).filter(
                        YearlyBudgetAmount.budget_id == budget_id,
                        YearlyBudgetAmount.year == str(year)
                    ).first()
                    
                    if existing_amount:
                        # Update existing amount
                        existing_amount.amount = float(amount)
                    else:
                        # Create new yearly amount
                        new_amount = YearlyBudgetAmount(
                            id=str(uuid.uuid4()),
                            budget_id=budget_id,
                            year=str(year),
                            amount=float(amount)
                        )
                        session.add(new_amount)
            
            session.commit()
            return True, "Budget updated successfully"
        except Exception as e:
            session.rollback()
            return False, f"Failed to update budget: {str(e)}"
        finally:
            session.close()

    def delete_budget(self, budget_id):
        """Delete a budget by ID"""
        session = self.db_manager.Session()
        try:
            # Check if budget is used in any purchases
            purchase_budgets = session.query(PurchaseBudget).filter(
                PurchaseBudget.budget_id == budget_id
            ).count()
            
            if purchase_budgets > 0:
                return False, "Cannot delete budget that is used in purchases"
            
            # Delete budget and its yearly amounts
            budget = session.query(Budget).filter(Budget.id == budget_id).first()
            if budget:
                session.delete(budget)
                session.commit()
                return True, "Budget deleted successfully"
            
            return False, "Budget not found"
        except Exception as e:
            session.rollback()
            return False, f"Failed to delete budget: {str(e)}"
        finally:
            session.close()

    def get_budget_options(self):
        """Get a list of budget options for dropdowns"""
        return [(b.id, b.name) for b in self.get_all_budgets()]

    def calculate_budget_usage(self, year=None):
        """Calculate budget usage for a specific year"""
        year = year or datetime.now().year
        session = self.db_manager.Session()
        
        try:
            # Get all budgets with their yearly amounts
            budgets = session.query(Budget).options(joinedload(Budget.yearly_amounts)).all()
            
            # Get all purchases for the year with their budget allocations
            purchases = session.query(Purchase).filter(
                Purchase.date.like(f"{year}%")
            ).options(joinedload(Purchase.budgets)).all()
            
            # Calculate spent amounts for each budget
            budget_spent = {}
            for purchase in purchases:
                for budget_alloc in purchase.budgets:
                    budget_id = budget_alloc.budget_id
                    amount = budget_alloc.amount
                    budget_spent[budget_id] = budget_spent.get(budget_id, 0) + amount
            
            # Build usage data
            result = []
            for budget in budgets:
                budget_amount = 0
                # Find the yearly amount for this year
                for yearly_amount in budget.yearly_amounts:
                    if yearly_amount.year == str(year):
                        budget_amount = yearly_amount.amount
                        break
                
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
        except Exception as e:
            print(f"Error calculating budget usage: {str(e)}")
            return []
        finally:
            session.close()