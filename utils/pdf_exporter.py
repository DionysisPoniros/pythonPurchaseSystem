# utils/pdf_exporter.py
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime


class PDFExporter:
    @staticmethod
    def export_budget_report(budget_data, monthly_data, year, file_path):
        """Export budget report to PDF file"""
        try:
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []

            # Title
            title_style = styles["Heading1"]
            elements.append(Paragraph(f"Budget Report - Fiscal Year {year}", title_style))
            elements.append(Spacer(1, 12))

            # Current date
            date_style = styles["Normal"]
            current_date = datetime.now().strftime("%B %d, %Y")
            elements.append(Paragraph(f"Generated on: {current_date}", date_style))
            elements.append(Spacer(1, 24))

            # Budget Summary
            elements.append(Paragraph("Budget Summary", styles["Heading2"]))
            elements.append(Spacer(1, 12))

            # Prepare data for budget summary table
            budget_table_data = [["Budget", "Amount", "Spent", "Remaining", "Percent Used"]]

            total_budget = 0
            total_spent = 0

            for data in budget_data:
                budget_table_data.append([
                    data["name"],
                    f"${data['amount']:,.2f}",
                    f"${data['spent']:,.2f}",
                    f"${data['remaining']:,.2f}",
                    f"{data['percent']:.1f}%"
                ])
                total_budget += data["amount"]
                total_spent += data["spent"]

            # Add total row
            total_remaining = total_budget - total_spent
            total_percent = (total_spent / total_budget * 100) if total_budget > 0 else 0

            budget_table_data.append([
                "TOTAL",
                f"${total_budget:,.2f}",
                f"${total_spent:,.2f}",
                f"${total_remaining:,.2f}",
                f"{total_percent:.1f}%"
            ])

            # Create budget summary table
            budget_table = Table(budget_table_data, colWidths=[200, 80, 80, 80, 80])
            budget_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
            ]))

            elements.append(budget_table)
            elements.append(Spacer(1, 24))

            # Monthly Breakdown
            elements.append(Paragraph("Monthly Spending Breakdown", styles["Heading2"]))
            elements.append(Spacer(1, 12))

            # Prepare data for monthly table
            monthly_table_data = [["Month", "Amount"]]
            monthly_total = 0

            for data in monthly_data:
                monthly_table_data.append([
                    data["month"],
                    f"${data['amount']:,.2f}"
                ])
                monthly_total += data["amount"]

            # Add total row
            monthly_table_data.append([
                "TOTAL",
                f"${monthly_total:,.2f}"
            ])

            # Create monthly breakdown table
            monthly_table = Table(monthly_table_data, colWidths=[200, 100])
            monthly_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
            ]))

            elements.append(monthly_table)

            # Build the PDF
            doc.build(elements)

            return True, "Report exported successfully to PDF"

        except Exception as e:
            return False, f"Export failed: {str(e)}"

    @staticmethod
    def export_vendor_report(vendor_data, year, file_path):
        """Export vendor report to PDF file"""
        try:
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []

            # Title
            title_style = styles["Heading1"]
            elements.append(Paragraph(f"Vendor Spending Report - Year {year}", title_style))
            elements.append(Spacer(1, 12))

            # Current date
            date_style = styles["Normal"]
            current_date = datetime.now().strftime("%B %d, %Y")
            elements.append(Paragraph(f"Generated on: {current_date}", date_style))
            elements.append(Spacer(1, 24))

            # Vendor Spending
            elements.append(Paragraph("Vendor Spending Summary", styles["Heading2"]))
            elements.append(Spacer(1, 12))

            # Prepare data for vendor table
            vendor_table_data = [["Vendor", "Total Spent", "Number of Orders", "Avg Order Value"]]
            total_spent = 0
            total_orders = 0

            for data in vendor_data:
                vendor_table_data.append([
                    data["name"],
                    f"${data['total_spent']:,.2f}",
                    str(data["purchase_count"]),
                    f"${data['avg_order']:,.2f}"
                ])
                total_spent += data["total_spent"]
                total_orders += data["purchase_count"]

            # Add total row
            avg_order = total_spent / total_orders if total_orders > 0 else 0
            vendor_table_data.append([
                "TOTAL",
                f"${total_spent:,.2f}",
                str(total_orders),
                f"${avg_order:,.2f}"
            ])

            # Create vendor table
            vendor_table = Table(vendor_table_data, colWidths=[200, 100, 100, 100])
            vendor_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
            ]))

            elements.append(vendor_table)

            # Build the PDF
            doc.build(elements)

            return True, "Vendor report exported successfully to PDF"

        except Exception as e:
            return False, f"Export failed: {str(e)}"