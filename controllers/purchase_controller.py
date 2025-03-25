# controllers/purchase_controller.py
from datetime import datetime
from models.purchase import Purchase


class PurchaseController:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_all_purchases(self):
        """Get all purchases as Purchase objects"""
        purchases_data = self.db_manager.get_purchases()
        return [Purchase.from_dict(p) for p in purchases_data]

    def get_purchase_by_id(self, purchase_id):
        """Get a purchase by ID"""
        purchases = self.db_manager.get_purchases()
        purchase_data = next((p for p in purchases if p.get("id") == purchase_id), None)
        if purchase_data:
            return Purchase.from_dict(purchase_data)
        return None

    def add_purchase(self, purchase):
        """Add a new purchase"""
        result = self.db_manager.save_purchase(purchase.to_dict())
        return result is not None

    def update_purchase(self, purchase):
        """Update an existing purchase"""
        result = self.db_manager.save_purchase(purchase.to_dict())
        return result is not None

    def delete_purchase(self, purchase_id):
        """Delete a purchase by ID"""
        success, message = self.db_manager.delete_purchase(purchase_id)
        return success

    def get_purchase_by_year(self, year):
        """Get purchases for a specific year"""
        return [p for p in self.get_all_purchases()
                if datetime.strptime(p.date, "%Y-%m-%d").year == year]

    def get_current_year_purchases(self):
        """Get purchases from the current year"""
        current_year = datetime.now().year
        return self.get_purchase_by_year(current_year)

    def count_pending_orders(self):
        """Count purchases with pending items"""
        return sum(1 for p in self.get_all_purchases() if not p.is_received())

    def calculate_ytd_spending(self):
        """Calculate year-to-date spending"""
        return sum(p.get_total() for p in self.get_current_year_purchases())

    def receive_items(self, purchase_id, item_indices, received_status):
        """Mark items as received or not received"""
        purchase = self.get_purchase_by_id(purchase_id)
        if not purchase:
            return False

        for idx in item_indices:
            if 0 <= idx < len(purchase.line_items):
                purchase.line_items[idx]["received"] = received_status

        self.update_purchase(purchase)
        return True

    # New methods for approval workflow
    def approve_purchase(self, purchase_id, approver):
        """Approve a purchase"""
        purchase = self.get_purchase_by_id(purchase_id)
        if not purchase:
            return False, "Purchase not found"

        purchase.approve(approver)
        result = self.update_purchase(purchase)
        if result:
            return True, "Purchase approved successfully"
        return False, "Failed to approve purchase"

    def reject_purchase(self, purchase_id, approver, notes=""):
        """Reject a purchase"""
        purchase = self.get_purchase_by_id(purchase_id)
        if not purchase:
            return False, "Purchase not found"

        purchase.reject(approver, notes)
        result = self.update_purchase(purchase)
        if result:
            return True, "Purchase rejected successfully"
        return False, "Failed to reject purchase"

    def get_purchases_by_approval_status(self, status="Pending"):
        """Get purchases by approval status"""
        return [p for p in self.get_all_purchases() if p.status == status]