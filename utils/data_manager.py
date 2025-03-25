import os
import json
import uuid
from datetime import datetime
import numpy as np
from config.settings import DATA_DIR, PURCHASES_FILE, VENDORS_FILE, BUDGETS_FILE


class DataManager:
    def __init__(self, data_dir=DATA_DIR):
        self.data_dir = data_dir
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        self.purchases_file = os.path.join(self.data_dir, PURCHASES_FILE)
        self.vendors_file = os.path.join(self.data_dir, VENDORS_FILE)
        self.budgets_file = os.path.join(self.data_dir, BUDGETS_FILE)

        # Generate test data if needed
        self.ensure_test_data()

    def load_data(self, file_path, default_data=None):
        """Load data from a JSON file"""
        if default_data is None:
            default_data = []

        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as file:
                    return json.load(file)
            except json.JSONDecodeError:
                return default_data
        return default_data

    def save_data(self, file_path, data):
        """Save data to a JSON file"""
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)

    def get_purchases(self):
        """Get all purchases"""
        return self.load_data(self.purchases_file, [])

    def save_purchases(self, purchases):
        """Save purchases data"""
        self.save_data(self.purchases_file, purchases)

    def get_vendors(self):
        """Get all vendors"""
        return self.load_data(self.vendors_file, [])

    def save_vendors(self, vendors):
        """Save vendors data"""
        self.save_data(self.vendors_file, vendors)

    def get_budgets(self):
        """Get all budgets"""
        return self.load_data(self.budgets_file, [])

    def save_budgets(self, budgets):
        """Save budgets data"""
        self.save_data(self.budgets_file, budgets)

    def ensure_test_data(self):
        """Generate test data if needed"""
        # Check if files already exist and have data
        if (os.path.exists(self.purchases_file) and os.path.exists(self.vendors_file) and
                os.path.exists(self.budgets_file)):
            purchases = self.get_purchases()
            vendors = self.get_vendors()
            budgets = self.get_budgets()

            if purchases and vendors and budgets:
                return  # Data already exists

        # Generate sample data
        self.generate_test_data()

    def generate_test_data(self):
        """Generate sample data for testing"""
        # Generate vendors
        vendors = [
            {"id": str(uuid.uuid4()), "name": "Office Supplies Co.", "contact": "John Smith",
             "phone": "555-123-4567", "email": "john@officesupplies.com", "address": "123 Main St."},
            {"id": str(uuid.uuid4()), "name": "Tech Solutions Inc.", "contact": "Alice Johnson",
             "phone": "555-987-6543", "email": "alice@techsolutions.com", "address": "456 Tech Blvd."},
            {"id": str(uuid.uuid4()), "name": "Furniture World", "contact": "Bob Brown",
             "phone": "555-456-7890", "email": "bob@furnitureworld.com", "address": "789 Oak Ave."},
            {"id": str(uuid.uuid4()), "name": "Paper Products Ltd.", "contact": "Carol Davis",
             "phone": "555-222-3333", "email": "carol@paperproducts.com", "address": "321 Pine St."},
            {"id": str(uuid.uuid4()), "name": "Electronics Warehouse", "contact": "David Wilson",
             "phone": "555-444-5555", "email": "david@electronicswarehouse.com", "address": "654 Elm St."}
        ]

        self.save_vendors(vendors)

        # Generate budgets
        current_year = datetime.now().year
        budgets = [
            {
                "id": str(uuid.uuid4()),
                "code": "OFC-SUP",
                "name": "Office Supplies",
                "description": "General office supplies and consumables",
                "yearly_amount": {str(current_year): 25000, str(current_year - 1): 22500}
            },
            {
                "id": str(uuid.uuid4()),
                "code": "IT-EQUIP",
                "name": "IT Equipment",
                "description": "Computers, peripherals, and technology",
                "yearly_amount": {str(current_year): 50000, str(current_year - 1): 45000}
            },
            {
                "id": str(uuid.uuid4()),
                "code": "FURN",
                "name": "Furniture",
                "description": "Office furniture and fixtures",
                "yearly_amount": {str(current_year): 30000, str(current_year - 1): 35000}
            },
            {
                "id": str(uuid.uuid4()),
                "code": "MKT",
                "name": "Marketing",
                "description": "Marketing materials and services",
                "yearly_amount": {str(current_year): 40000, str(current_year - 1): 38000}
            },
            {
                "id": str(uuid.uuid4()),
                "code": "TRAVEL",
                "name": "Travel",
                "description": "Business travel expenses",
                "yearly_amount": {str(current_year): 35000, str(current_year - 1): 40000}
            }
        ]

        self.save_budgets(budgets)

        # Generate purchases
        purchases = []

        # Sample items for each vendor
        vendor_items = {
            vendors[0]["id"]: [
                {"description": "Copy Paper (Case)", "unit_price": 45.99},
                {"description": "Ballpoint Pens (Box)", "unit_price": 12.99},
                {"description": "Sticky Notes (Pack)", "unit_price": 8.49},
                {"description": "Stapler", "unit_price": 15.99},
                {"description": "File Folders (Box)", "unit_price": 18.99}
            ],
            vendors[1]["id"]: [
                {"description": "Laptop Computer", "unit_price": 999.99},
                {"description": "Desktop Computer", "unit_price": 799.99},
                {"description": "Monitor", "unit_price": 249.99},
                {"description": "Keyboard", "unit_price": 59.99},
                {"description": "Mouse", "unit_price": 29.99}
            ],
            vendors[2]["id"]: [
                {"description": "Office Chair", "unit_price": 199.99},
                {"description": "Desk", "unit_price": 349.99},
                {"description": "Bookshelf", "unit_price": 179.99},
                {"description": "File Cabinet", "unit_price": 149.99},
                {"description": "Conference Table", "unit_price": 899.99}
            ],
            vendors[3]["id"]: [
                {"description": "Printer Paper (Case)", "unit_price": 42.99},
                {"description": "Notebooks (Pack)", "unit_price": 24.99},
                {"description": "Envelopes (Box)", "unit_price": 15.99},
                {"description": "Business Cards (Box)", "unit_price": 29.99},
                {"description": "Presentation Folders", "unit_price": 35.99}
            ],
            vendors[4]["id"]: [
                {"description": "Projector", "unit_price": 599.99},
                {"description": "Wireless Headphones", "unit_price": 129.99},
                {"description": "Webcam", "unit_price": 79.99},
                {"description": "Speakers", "unit_price": 89.99},
                {"description": "Power Strip", "unit_price": 24.99}
            ]
        }

        # Generate purchases for current and previous year
        for year in [current_year, current_year - 1]:
            num_purchases = 20 if year == current_year else 10

            for i in range(num_purchases):
                # Select random vendor
                vendor_index = np.random.randint(0, len(vendors))
                vendor = vendors[vendor_index]
                vendor_id = vendor["id"]

                # Generate date
                month = np.random.randint(1, 13)
                day = np.random.randint(1, 29)
                date = f"{year}-{month:02d}-{day:02d}"

                # Generate order number
                order_number = f"PO-{year}-{i + 1:04d}"

                # Generate invoice number (some might be missing)
                invoice_number = f"INV-{i + 1:05d}" if np.random.random() > 0.2 else ""

                # Generate 1-5 line items
                num_items = np.random.randint(1, 6)
                line_items = []

                for j in range(num_items):
                    item_index = np.random.randint(0, len(vendor_items[vendor_id]))
                    item = vendor_items[vendor_id][item_index]

                    quantity = np.random.randint(1, 11)

                    # Determine if received (older orders more likely to be received)
                    # All previous year orders are received
                    if year < current_year:
                        received = True
                    else:
                        received = np.random.random() > (0.1 + 0.5 * month / 12)

                    line_items.append({
                        "description": item["description"],
                        "quantity": quantity,
                        "unit_price": item["unit_price"],
                        "received": received
                    })

                # Calculate total
                total_amount = sum(item["quantity"] * item["unit_price"] for item in line_items)

                # Assign to 1-2 budgets
                num_budgets = min(np.random.randint(1, 3), len(budgets))
                budget_allocations = []

                if num_budgets == 1:
                    # Single budget gets 100%
                    budget_index = np.random.randint(0, len(budgets))
                    budget_allocations.append({
                        "budget_id": budgets[budget_index]["id"],
                        "amount": total_amount
                    })
                else:
                    # Split between two budgets
                    budget_indices = np.random.choice(len(budgets), num_budgets, replace=False)
                    split = np.random.random() * 0.7 + 0.15  # Split between 15/85 and 85/15

                    budget_allocations.append({
                        "budget_id": budgets[budget_indices[0]]["id"],
                        "amount": total_amount * split
                    })

                    budget_allocations.append({
                        "budget_id": budgets[budget_indices[1]]["id"],
                        "amount": total_amount * (1 - split)
                    })

                # Create purchase object
                purchase = {
                    "id": str(uuid.uuid4()),
                    "order_number": order_number,
                    "invoice_number": invoice_number,
                    "date": date,
                    "vendor_id": vendor_id,
                    "vendor_name": vendor["name"],
                    "line_items": line_items,
                    "budgets": budget_allocations
                }

                purchases.append(purchase)

        def import_purchases_from_csv(self, file_path):
            """Import purchases from a CSV file"""
            import csv
            from models.purchase import Purchase
            import uuid
            from datetime import datetime

            try:
                purchases = self.get_purchases()
                imported_count = 0
                error_count = 0

                with open(file_path, 'r', newline='') as csvfile:
                    reader = csv.DictReader(csvfile)

                    for row in reader:
                        try:
                            # Validate required fields
                            if not row.get('Order Number') or not row.get('Vendor') or not row.get('Date'):
                                error_count += 1
                                continue

                            # Find vendor ID
                            vendor_id = None
                            vendor_name = row.get('Vendor', '').strip()

                            for vendor in self.get_vendors():
                                if vendor.get('name') == vendor_name:
                                    vendor_id = vendor.get('id')
                                    break

                            if not vendor_id:
                                # Create new vendor if not found
                                vendor_id = str(uuid.uuid4())
                                new_vendor = {
                                    'id': vendor_id,
                                    'name': vendor_name,
                                    'contact': '',
                                    'phone': '',
                                    'email': '',
                                    'address': ''
                                }
                                vendors = self.get_vendors()
                                vendors.append(new_vendor)
                                self.save_vendors(vendors)

                            # Parse date
                            try:
                                date_value = row.get('Date', '').strip()
                                date_obj = datetime.strptime(date_value, "%Y-%m-%d")
                                date = date_obj.strftime("%Y-%m-%d")
                            except ValueError:
                                # Try another common format
                                try:
                                    date_obj = datetime.strptime(date_value, "%m/%d/%Y")
                                    date = date_obj.strftime("%Y-%m-%d")
                                except ValueError:
                                    # Use today's date if parsing fails
                                    date = datetime.now().strftime("%Y-%m-%d")

                            # Create line items
                            line_items = []
                            description = row.get('Description', '').strip()

                            if description:
                                try:
                                    quantity = int(row.get('Quantity', '1'))
                                    unit_price = float(row.get('Unit Price', '0.0'))
                                except ValueError:
                                    quantity = 1
                                    unit_price = 0.0

                                line_items.append({
                                    'description': description,
                                    'quantity': quantity,
                                    'unit_price': unit_price,
                                    'received': False
                                })

                            # Create budget allocations
                            budgets = []
                            budget_code = row.get('Budget Code', '').strip()

                            if budget_code:
                                budget_id = None
                                for budget in self.get_budgets():
                                    if budget.get('code') == budget_code:
                                        budget_id = budget.get('id')
                                        break

                                if budget_id:
                                    try:
                                        amount = float(row.get('Amount', '0.0'))
                                    except ValueError:
                                        amount = 0.0

                                    budgets.append({
                                        'budget_id': budget_id,
                                        'amount': amount
                                    })

                            # Create Purchase object
                            purchase = {
                                'id': str(uuid.uuid4()),
                                'order_number': row.get('Order Number', '').strip(),
                                'invoice_number': row.get('Invoice Number', '').strip(),
                                'date': date,
                                'vendor_id': vendor_id,
                                'vendor_name': vendor_name,
                                'line_items': line_items,
                                'budgets': budgets,
                                'status': 'Pending',
                                'approver': '',
                                'approval_date': None,
                                'notes': ''
                            }

                            purchases.append(purchase)
                            imported_count += 1

                        except Exception as e:
                            error_count += 1
                            continue

                # Save imported purchases
                self.save_purchases(purchases)

                return True, f"Import completed: {imported_count} purchases imported, {error_count} errors"

            except Exception as e:
                return False, f"Import failed: {str(e)}"

        self.save_purchases(purchases)