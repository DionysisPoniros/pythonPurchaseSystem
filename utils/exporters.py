# utils/exporters.py
import csv
import os
from datetime import datetime

class CSVExporter:
    @staticmethod
    def export_purchases(purchases, file_path):
        """Export purchases to CSV file"""
        try:
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)

                # Write header
                writer.writerow(["Order Number", "Date", "Vendor", "Invoice Number", "Total Amount", "Status"])

                # Write data
                for purchase in purchases:
                    # Calculate total for this purchase
                    total = 0
                    if hasattr(purchase, 'line_items') and purchase.line_items:
                        for line_item in purchase.line_items:
                            total += line_item.quantity * line_item.unit_price
                    
                    status = "Pending"
                    if hasattr(purchase, 'line_items') and purchase.line_items:
                        if all(item.received for item in purchase.line_items):
                            status = "Received"
                        elif any(item.received for item in purchase.line_items):
                            status = "Partial"

                    writer.writerow([
                        purchase.order_number,
                        purchase.date,
                        purchase.vendor_name,
                        purchase.invoice_number,
                        f"${total:.2f}",
                        status
                    ])

            return True, f"Purchases exported to {file_path}"

        except Exception as e:
            return False, f"Export failed: {str(e)}"

    @staticmethod
    def export_vendors(vendors, file_path):
        """Export vendors to CSV file"""
        try:
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)

                # Write header
                writer.writerow(["Name", "Contact", "Phone", "Email", "Address"])

                # Write data
                for vendor in vendors:
                    writer.writerow([
                        vendor.name,
                        vendor.contact,
                        vendor.phone,
                        vendor.email,
                        vendor.address
                    ])

            return True, f"Vendors exported to {file_path}"

        except Exception as e:
            return False, f"Export failed: {str(e)}"

    @staticmethod
    def export_budget_report(budget_data, monthly_data, year, file_path):
        """Export budget report to CSV"""
        try:
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

    @staticmethod
    def export_vendor_report(vendor_data, year, file_path):
        """Export vendor report to CSV"""
        try:
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)

                # Write header
                writer.writerow(["Vendor Spending Report", f"Year: {year}"])
                writer.writerow([])

                # Write vendor data
                writer.writerow(["Vendor Spending Summary"])
                writer.writerow(["Vendor", "Total Spent", "Number of Orders", "Avg Order Value"])

                total_spent = 0
                total_orders = 0

                for data in vendor_data:
                    writer.writerow([
                        data["name"],
                        f"${data['total_spent']:.2f}",
                        data["purchase_count"],
                        f"${data['avg_order']:.2f}"
                    ])

                    total_spent += data["total_spent"]
                    total_orders += data["purchase_count"]

                # Add total row
                avg_order = total_spent / total_orders if total_orders > 0 else 0
                writer.writerow([
                    "TOTAL",
                    f"${total_spent:.2f}",
                    total_orders,
                    f"${avg_order:.2f}"
                ])

            return True, "Vendor report exported successfully"

        except Exception as e:
            return False, f"Export failed: {str(e)}"