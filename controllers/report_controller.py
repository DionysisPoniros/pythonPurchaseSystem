# controllers/report_controller.py
from datetime import datetime
import numpy as np
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

        year = year or datetime.now().year
        return self.budget_controller.calculate_budget_usage(year)

    def generate_monthly_spending(self, year=None):
        """Generate monthly spending report data"""
        if not self.purchase_controller:
            raise RuntimeError("Purchase controller not set. Call set_controllers first.")

        year = year or datetime.now().year
        purchases = self.purchase_controller.get_purchase_by_year(year)

        # Initialize monthly data
        monthly_data = {m: 0 for m in range(1, 13)}

        # Calculate monthly totals
        for purchase in purchases:
            try:
                purchase_date = datetime.strptime(purchase.date, "%Y-%m-%d")
                if purchase_date.year == year:
                    month = purchase_date.month
                    monthly_data[month] += purchase.get_total()
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

    def generate_vendor_spending(self, year=None):
        """Generate vendor spending report data"""
        if not self.purchase_controller or not self.vendor_controller:
            raise RuntimeError("Controllers not set. Call set_controllers first.")

        year = year or datetime.now().year
        purchases = self.purchase_controller.get_purchase_by_year(year)

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

            vendor_data[vendor_id]["total_spent"] += purchase.get_total()
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

    def export_budget_report(self, year, file_path):
        """Export budget report to CSV"""
        try:
            budget_data = self.generate_budget_summary(year)
            monthly_data = self.generate_monthly_spending(year)

            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)

                # Write header
                writer.writerow(["Budget Report", f"Fiscal Year: {year}"])
                writer.writerow([])

                # Write summary
                writer.writerow(["Budget Summary"])
                writer.writerow(["Budget", "Amount", "Spent", "Remaining", "Percent Used"])

                total_budget = 0
                total_spent = 0

                for data in budget_data:
                    writer.writerow([
                        data["name"],
                        f"${data['amount']:.2f}",
                        f"${data['spent']:.2f}",
                        f"${data['remaining']:.2f}",
                        f"{data['percent']:.1f}%"
                    ])

                    total_budget += data["amount"]
                    total_spent += data["spent"]

                total_remaining = total_budget - total_spent
                total_percent = (total_spent / total_budget * 100) if total_budget > 0 else 0

                writer.writerow([
                    "TOTAL",
                    f"${total_budget:.2f}",
                    f"${total_spent:.2f}",
                    f"${total_remaining:.2f}",
                    f"{total_percent:.1f}%"
                ])

                # Write monthly breakdown
                writer.writerow([])
                writer.writerow(["Monthly Breakdown"])
                writer.writerow(["Month", "Amount"])

                for data in monthly_data:
                    writer.writerow([data["month"], f"${data['amount']:.2f}"])

                writer.writerow(["TOTAL", f"${sum(data['amount'] for data in monthly_data):.2f}"])

            return True, "Report exported successfully"

        except Exception as e:
            return False, f"Export failed: {str(e)}"