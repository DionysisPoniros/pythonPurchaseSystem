# database/models.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey, Table, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# Association table for purchase-budget many-to-many relationship
purchase_budget_association = Table(
    'purchase_budget_association',
    Base.metadata,
    Column('id', String, primary_key=True),
    Column('purchase_id', String, ForeignKey('purchases.id')),
    Column('budget_id', String, ForeignKey('budgets.id')),
    Column('amount', Float)
)


class Vendor(Base):
    __tablename__ = 'vendors'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    contact = Column(String)
    phone = Column(String)
    email = Column(String)
    address = Column(String)

    # Relationships
    purchases = relationship("Purchase", back_populates="vendor")

    def __init__(self, id=None, name="", contact="", phone="", email="", address=""):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.contact = contact
        self.phone = phone
        self.email = email
        self.address = address

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "contact": self.contact,
            "phone": self.phone,
            "email": self.email,
            "address": self.address
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            contact=data.get("contact", ""),
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            address=data.get("address", "")
        )


class Budget(Base):
    __tablename__ = 'budgets'

    id = Column(String, primary_key=True)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)

    # Relationships
    yearly_amounts = relationship("YearlyBudgetAmount", back_populates="budget", cascade="all, delete-orphan")
    purchases = relationship("PurchaseBudget", back_populates="budget")

    def __init__(self, id=None, code="", name="", description=""):
        self.id = id or str(uuid.uuid4())
        self.code = code
        self.name = name
        self.description = description

    def to_dict(self):
        yearly_amount = {}
        for amount in self.yearly_amounts:
            yearly_amount[amount.year] = amount.amount

        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "yearly_amount": yearly_amount
        }

    @classmethod
    def from_dict(cls, data):
        budget = cls(
            id=data.get("id"),
            code=data.get("code", ""),
            name=data.get("name", ""),
            description=data.get("description", "")
        )
        return budget

    def get_amount_for_year(self, year=None):
        year = year or str(datetime.now().year)
        for yearly_amount in self.yearly_amounts:
            if yearly_amount.year == year:
                return yearly_amount.amount
        return 0


class YearlyBudgetAmount(Base):
    __tablename__ = 'yearly_budget_amounts'

    id = Column(String, primary_key=True)
    budget_id = Column(String, ForeignKey('budgets.id'))
    year = Column(String, nullable=False)
    amount = Column(Float, default=0.0)

    # Relationships
    budget = relationship("Budget", back_populates="yearly_amounts")

    def __init__(self, id=None, budget_id=None, year=None, amount=0.0):
        self.id = id or str(uuid.uuid4())
        self.budget_id = budget_id
        self.year = year
        self.amount = amount


class LineItem(Base):
    __tablename__ = 'line_items'

    id = Column(String, primary_key=True)
    purchase_id = Column(String, ForeignKey('purchases.id'))
    description = Column(String)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, default=0.0)
    received = Column(Boolean, default=False)

    # Relationships
    purchase = relationship("Purchase", back_populates="line_items")

    def __init__(self, id=None, purchase_id=None, description="", quantity=1, unit_price=0.0, received=False):
        self.id = id or str(uuid.uuid4())
        self.purchase_id = purchase_id
        self.description = description
        self.quantity = quantity
        self.unit_price = unit_price
        self.received = received

    def get_total(self):
        return self.quantity * self.unit_price

    def to_dict(self):
        return {
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "received": self.received
        }


class PurchaseBudget(Base):
    __tablename__ = 'purchase_budgets'

    id = Column(String, primary_key=True)
    purchase_id = Column(String, ForeignKey('purchases.id'))
    budget_id = Column(String, ForeignKey('budgets.id'))
    amount = Column(Float, default=0.0)

    # Relationships
    purchase = relationship("Purchase", back_populates="budgets")
    budget = relationship("Budget", back_populates="purchases")

    def __init__(self, id=None, purchase_id=None, budget_id=None, amount=0.0):
        self.id = id or str(uuid.uuid4())
        self.purchase_id = purchase_id
        self.budget_id = budget_id
        self.amount = amount

    def to_dict(self):
        return {
            "budget_id": self.budget_id,
            "amount": self.amount
        }


class Purchase(Base):
    __tablename__ = 'purchases'

    id = Column(String, primary_key=True)
    order_number = Column(String)
    invoice_number = Column(String)
    date = Column(String)
    vendor_id = Column(String, ForeignKey('vendors.id'))
    vendor_name = Column(String)
    status = Column(String, default="Pending")  # Pending, Approved, Rejected
    approver = Column(String)
    approval_date = Column(String)
    notes = Column(Text)

    # Relationships
    vendor = relationship("Vendor", back_populates="purchases")
    line_items = relationship("LineItem", back_populates="purchase", cascade="all, delete-orphan")
    budgets = relationship("PurchaseBudget", back_populates="purchase", cascade="all, delete-orphan")

    def __init__(self, id=None, order_number="", invoice_number="", date=None,
                 vendor_id=None, vendor_name="", status="Pending", approver="",
                 approval_date=None, notes=""):
        self.id = id or str(uuid.uuid4())
        self.order_number = order_number
        self.invoice_number = invoice_number
        self.date = date or datetime.now().strftime("%Y-%m-%d")
        self.vendor_id = vendor_id
        self.vendor_name = vendor_name
        self.status = status
        self.approver = approver
        self.approval_date = approval_date
        self.notes = notes

    def to_dict(self):
        return {
            "id": self.id,
            "order_number": self.order_number,
            "invoice_number": self.invoice_number,
            "date": self.date,
            "vendor_id": self.vendor_id,
            "vendor_name": self.vendor_name,
            "line_items": [item.to_dict() for item in self.line_items],
            "budgets": [budget.to_dict() for budget in self.budgets],
            "status": self.status,
            "approver": self.approver,
            "approval_date": self.approval_date,
            "notes": self.notes
        }

    def get_total(self):
        return sum(item.get_total() for item in self.line_items)

    def is_received(self):
        if not self.line_items:
            return False
        return all(item.received for item in self.line_items)

    def is_partially_received(self):
        if not self.line_items:
            return False
        return any(item.received for item in self.line_items) and not self.is_received()

    def get_status(self):
        if self.is_received():
            return "Received"
        elif self.is_partially_received():
            return "Partial"
        else:
            return "Pending"

    def approve(self, approver):
        self.status = "Approved"
        self.approver = approver
        self.approval_date = datetime.now().strftime("%Y-%m-%d")

    def reject(self, approver, notes=""):
        self.status = "Rejected"
        self.approver = approver
        self.approval_date = datetime.now().strftime("%Y-%m-%d")
        self.notes = notes