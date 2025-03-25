from datetime import datetime
import uuid


class Purchase:
    def __init__(self, id=None, order_number="", invoice_number="", date=None,
                 vendor_id=None, vendor_name="", line_items=None, budgets=None):
        self.id = id or str(uuid.uuid4())
        self.order_number = order_number
        self.invoice_number = invoice_number
        self.date = date or datetime.now().strftime("%Y-%m-%d")
        self.vendor_id = vendor_id
        self.vendor_name = vendor_name
        self.line_items = line_items or []
        self.budgets = budgets or []

    @classmethod
    def from_dict(cls, data):
        """Create a Purchase object from a dictionary"""
        return cls(
            id=data.get("id"),
            order_number=data.get("order_number", ""),
            invoice_number=data.get("invoice_number", ""),
            date=data.get("date"),
            vendor_id=data.get("vendor_id"),
            vendor_name=data.get("vendor_name", ""),
            line_items=data.get("line_items", []),
            budgets=data.get("budgets", [])
        )

    def to_dict(self):
        """Convert Purchase object to a dictionary"""
        return {
            "id": self.id,
            "order_number": self.order_number,
            "invoice_number": self.invoice_number,
            "date": self.date,
            "vendor_id": self.vendor_id,
            "vendor_name": self.vendor_name,
            "line_items": self.line_items,
            "budgets": self.budgets
        }

    def get_total(self):
        """Calculate the total amount of the purchase"""
        return sum(item.get("quantity", 0) * item.get("unit_price", 0)
                   for item in self.line_items)

    def is_received(self):
        """Check if all items have been received"""
        if not self.line_items:
            return False
        return all(item.get("received", False) for item in self.line_items)

    def is_partially_received(self):
        """Check if some items have been received"""
        if not self.line_items:
            return False
        return any(item.get("received", False) for item in self.line_items) and not self.is_received()

    def get_status(self):
        """Get the status of the purchase"""
        if self.is_received():
            return "Received"
        elif self.is_partially_received():
            return "Partial"
        else:
            return "Pending"