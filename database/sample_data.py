# database/sample_data.py
import uuid
import random
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from database.models import Vendor, Budget, YearlyBudgetAmount, Purchase, LineItem, PurchaseBudget


def generate_sample_data():
    """Generate sample data for the purchase system"""
    db_manager = DatabaseManager()
    session = db_manager.Session()
    
    try:
        # Generate vendors
        vendors = generate_vendors(session)
        
        # Generate budgets
        budgets = generate_budgets(session)
        
        # Generate purchases
        generate_purchases(session, vendors, budgets)
        
        # Commit all changes
        session.commit()
        print("Sample data generation completed.")
    except Exception as e:
        session.rollback()
        print(f"Error generating sample data: {str(e)}")
    finally:
        session.close()


def generate_vendors(session):
    """Generate sample vendors data"""
    vendors = [
        Vendor(
            id=str(uuid.uuid4()),
            name="Office Supplies Co.",
            contact="John Smith",
            phone="555-123-4567",
            email="john@officesupplies.com",
            address="123 Main St."
        ),
        Vendor(
            id=str(uuid.uuid4()),
            name="Tech Solutions Inc.",
            contact="Alice Johnson",
            phone="555-987-6543",
            email="alice@techsolutions.com",
            address="456 Tech Blvd."
        ),
        Vendor(
            id=str(uuid.uuid4()),
            name="Furniture World",
            contact="Bob Brown",
            phone="555-456-7890",
            email="bob@furnitureworld.com",
            address="789 Oak Ave."
        ),
        Vendor(
            id=str(uuid.uuid4()),
            name="Paper Products Ltd.",
            contact="Carol Davis",
            phone="555-222-3333",
            email="carol@paperproducts.com",
            address="321 Pine St."
        ),
        Vendor(
            id=str(uuid.uuid4()),
            name="Electronics Warehouse",
            contact="David Wilson",
            phone="555-444-5555",
            email="david@electronicswarehouse.com",
            address="654 Elm St."
        )
    ]
    
    # Add vendors to session
    for vendor in vendors:
        session.add(vendor)
    
    # Flush to get IDs
    session.flush()
    
    return vendors


def generate_budgets(session):
    """Generate sample budgets data"""
    current_year = datetime.now().year
    
    budget_data = [
        {
            "code": "OFC-SUP",
            "name": "Office Supplies",
            "description": "General office supplies and consumables",
            "yearly_amount": {str(current_year): 25000, str(current_year - 1): 22500}
        },
        {
            "code": "IT-EQUIP",
            "name": "IT Equipment",
            "description": "Computers, peripherals, and technology",
            "yearly_amount": {str(current_year): 50000, str(current_year - 1): 45000}
        },
        {
            "code": "FURN",
            "name": "Furniture",
            "description": "Office furniture and fixtures",
            "yearly_amount": {str(current_year): 30000, str(current_year - 1): 35000}
        },
        {
            "code": "MKT",
            "name": "Marketing",
            "description": "Marketing materials and services",
            "yearly_amount": {str(current_year): 40000, str(current_year - 1): 38000}
        },
        {
            "code": "TRAVEL",
            "name": "Travel",
            "description": "Business travel expenses",
            "yearly_amount": {str(current_year): 35000, str(current_year - 1): 40000}
        }
    ]
    
    budgets = []
    
    for data in budget_data:
        # Create budget
        budget = Budget(
            id=str(uuid.uuid4()),
            code=data["code"],
            name=data["name"],
            description=data["description"]
        )
        session.add(budget)
        session.flush()  # Flush to get ID
        
        # Add yearly amounts
        for year, amount in data["yearly_amount"].items():
            yearly_amount = YearlyBudgetAmount(
                id=str(uuid.uuid4()),
                budget_id=budget.id,
                year=year,
                amount=amount
            )
            session.add(yearly_amount)
        
        budgets.append(budget)
    
    # Flush to ensure all IDs are available
    session.flush()
    
    return budgets


def generate_purchases(session, vendors, budgets):
    """Generate sample purchases data"""
    # Items for each vendor
    vendor_items = {
        vendors[0].id: [  # Office Supplies Co.
            {"description": "Copy Paper (Case)", "unit_price": 45.99},
            {"description": "Ballpoint Pens (Box)", "unit_price": 12.99},
            {"description": "Sticky Notes (Pack)", "unit_price": 8.49},
            {"description": "Stapler", "unit_price": 15.99},
            {"description": "File Folders (Box)", "unit_price": 18.99}
        ],
        vendors[1].id: [  # Tech Solutions Inc.
            {"description": "Laptop Computer", "unit_price": 999.99},
            {"description": "Desktop Computer", "unit_price": 799.99},
            {"description": "Monitor", "unit_price": 249.99},
            {"description": "Keyboard", "unit_price": 59.99},
            {"description": "Mouse", "unit_price": 29.99}
        ],
        vendors[2].id: [  # Furniture World
            {"description": "Office Chair", "unit_price": 199.99},
            {"description": "Desk", "unit_price": 349.99},
            {"description": "Bookshelf", "unit_price": 179.99},
            {"description": "File Cabinet", "unit_price": 149.99},
            {"description": "Conference Table", "unit_price": 899.99}
        ],
        vendors[3].id: [  # Paper Products Ltd.
            {"description": "Printer Paper (Case)", "unit_price": 42.99},
            {"description": "Notebooks (Pack)", "unit_price": 24.99},
            {"description": "Envelopes (Box)", "unit_price": 15.99},
            {"description": "Business Cards (Box)", "unit_price": 29.99},
            {"description": "Presentation Folders", "unit_price": 35.99}
        ],
        vendors[4].id: [  # Electronics Warehouse
            {"description": "Projector", "unit_price": 599.99},
            {"description": "Wireless Headphones", "unit_price": 129.99},
            {"description": "Webcam", "unit_price": 79.99},
            {"description": "Speakers", "unit_price": 89.99},
            {"description": "Power Strip", "unit_price": 24.99}
        ]
    }

    current_year = datetime.now().year

    # Generate purchases for current and previous year
    for year in [current_year, current_year - 1]:
        num_purchases = 20 if year == current_year else 10

        for i in range(num_purchases):
            # Select random vendor
            vendor_index = random.randint(0, len(vendors) - 1)
            vendor = vendors[vendor_index]
            vendor_id = vendor.id

            # Generate date
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            date = f"{year}-{month:02d}-{day:02d}"

            # Generate order number
            order_number = f"PO-{year}-{i + 1:04d}"

            # Generate invoice number (some might be missing)
            invoice_number = f"INV-{i + 1:05d}" if random.random() > 0.2 else ""

            # Approval status
            # Older purchases and some newer purchases are approved
            if year < current_year or random.random() > 0.7:
                status = "Approved"
                approver = "System Admin"
                approval_date = date
            else:
                status = "Pending"
                approver = ""
                approval_date = None

            # Create purchase
            purchase = Purchase(
                id=str(uuid.uuid4()),
                order_number=order_number,
                invoice_number=invoice_number,
                date=date,
                vendor_id=vendor_id,
                vendor_name=vendor.name,
                status=status,
                approver=approver,
                approval_date=approval_date,
                notes=""
            )
            
            session.add(purchase)
            session.flush()  # Flush to get ID

            # Generate 1-5 line items
            num_items = random.randint(1, 5)
            
            # Calculate total for budget allocation
            total_amount = 0
            
            for j in range(num_items):
                item_index = random.randint(0, len(vendor_items[vendor_id]) - 1)
                item = vendor_items[vendor_id][item_index]
                
                quantity = random.randint(1, 10)
                
                # Determine if received (older orders more likely to be received)
                if year < current_year:
                    received = True
                else:
                    received = random.random() > (0.1 + 0.5 * month / 12)
                
                line_item = LineItem(
                    id=str(uuid.uuid4()),
                    purchase_id=purchase.id,
                    description=item["description"],
                    quantity=quantity,
                    unit_price=item["unit_price"],
                    received=received
                )
                
                session.add(line_item)
                
                total_amount += quantity * item["unit_price"]
            
            # Assign to 1-2 budgets
            num_budgets = min(random.randint(1, 2), len(budgets))
            
            if num_budgets == 1:
                # Single budget gets 100%
                budget_index = random.randint(0, len(budgets) - 1)
                budget = budgets[budget_index]
                
                purchase_budget = PurchaseBudget(
                    id=str(uuid.uuid4()),
                    purchase_id=purchase.id,
                    budget_id=budget.id,
                    amount=total_amount
                )
                
                session.add(purchase_budget)
            else:
                # Split between two budgets
                budget_indices = random.sample(range(len(budgets)), num_budgets)
                split = random.random() * 0.7 + 0.15  # Split between 15/85 and 85/15
                
                purchase_budget1 = PurchaseBudget(
                    id=str(uuid.uuid4()),
                    purchase_id=purchase.id,
                    budget_id=budgets[budget_indices[0]].id,
                    amount=total_amount * split
                )
                
                purchase_budget2 = PurchaseBudget(
                    id=str(uuid.uuid4()),
                    purchase_id=purchase.id,
                    budget_id=budgets[budget_indices[1]].id,
                    amount=total_amount * (1 - split)
                )
                
                session.add(purchase_budget1)
                session.add(purchase_budget2)
            
    # Flush to ensure all data is processed
    session.flush()


if __name__ == "__main__":
    generate_sample_data()