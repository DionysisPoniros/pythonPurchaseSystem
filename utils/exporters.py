import csv
import os


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
                    total = purchase.get_total()
                    status = purchase.get_status()

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