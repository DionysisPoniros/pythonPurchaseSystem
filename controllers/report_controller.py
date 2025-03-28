# controllers/report_controller.py
from datetime import datetime
from database.models import Purchase, Budget, Vendor, PurchaseBudget
from sqlalchemy.orm import joinedload
import csv
import os

class ReportController:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.purchase_controller = None
        self.budget_controller = None
        self.vendor_controller = None

    def set_controllers(self, purchase_controller, budget_controller, vendor_controller):
        """Set references to other controllers"""
        self.purchase_controller = purchase_controller
        self.budget_controller = budget_controller
        self.vendor_controller = vendor_controller

    def generate_budget_summary(self, year=None):
        """Generate budget summary report data"""
        if not self.budget_controller:
            raise RuntimeError("Budget controller not set. Call set_controllers first.")

        return self.budget_controller.calculate_budget_usage(year)

    def generate_monthly_spending(self, year=None):
        """Generate monthly spending report data"""
        year = year or datetime.now().year
        session = self.db_manager.Session()
        
        try:
            # Query purchases for the year with their line items
            purchases = session.query(Purchase).filter(
                Purchase.date.like(f"{year}%")
            ).options(joinedload(Purchase.line_items)).all()
            
            # Initialize monthly data
            monthly_data = {m: 0 for m in range(1, 13)}
            
            # Calculate monthly totals
            for purchase in purchases:
                try:
                    purchase_date = datetime.strptime(purchase.date, "%Y-%m-%d")
                    if purchase_date.year == year:
                        month = purchase_date.month
                        # Calculate total for this purchase
                        total = 0
                        for line_item in purchase.line_items:
                            total += line_item.quantity * line_item.unit_price
                        monthly_data[month] += total
                except (ValueError, AttributeError):
                    # Skip purchases with invalid dates
                    continue
            
            # Format result
            result = []
            months = ["January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]
            
            for month_num, amount in monthly_data.items():
                result.append({
                    "month_num": month_num,
                    "month": months[month_num - 1],
                    "amount": amount
                })
            
            return sorted(result, key=lambda x: x["month_num"])
        finally:
            session.close()

    def generate_vendor_spending(self, year=None):
        """Generate vendor spending report data"""
        year = year or datetime.now().year
        session = self.db_manager.Session()
        
        try:
            # Query purchases for the year with their line items
            purchases = session.query(Purchase).filter(
                Purchase.date.like(f"{year}%")
            ).options(joinedload(Purchase.line_items)).all()
            
            # Calculate vendor data
            vendor_data = {}
            
            for purchase in purchases:
                vendor_id = purchase.vendor_id
                if vendor_id not in vendor_data:
                    vendor_data[vendor_id] = {
                        "name": purchase.vendor_name,
                        "total_spent": 0,
                        "purchase_count": 0
                    }
                
                # Calculate total for this purchase
                total = 0
                for line_item in purchase.line_items:
                    total += line_item.quantity * line_item.unit_price
                
                vendor_data[vendor_id]["total_spent"] += total
                vendor_data[vendor_id]["purchase_count"] += 1
            
            # Format result
            result = []
            for vendor_id, data in vendor_data.items():
                avg_order = data["total_spent"] / data["purchase_count"] if data["purchase_count"] > 0 else 0
                
                result.append({
                    "vendor_id": vendor_id,
                    "name": data["name"],
                    "total_spent": data["total_spent"],
                    "purchase_count": data["purchase_count"],
                    "avg_order": avg_order
                })
            
            return sorted(result, key=lambda x: x["total_spent"], reverse=True)
        finally:
            session.close()

    def export_budget_report(self, year, file_path):
        """Export budget report to CSV"""
        try:
            budget_data = self.generate_budget_summary(year)
            monthly_data = self.generate_monthly_spending(year)
            
            from utils.exporters import CSVExporter
            return CSVExporter.export_budget_report(budget_data, monthly_data, year, file_path)
        except Exception as e:
            return False, f"Export failed: {str(e)}"

    def export_vendor_report(self, year, file_path):
        """Export vendor report to CSV"""
        try:
            vendor_data = self.generate_vendor_spending(year)
            
            from utils.exporters import CSVExporter
            return CSVExporter.export_vendor_report(vendor_data, year, file_path)
        except Exception as e:
            return False, f"Export failed: {str(e)}"