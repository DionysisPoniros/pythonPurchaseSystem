class LineItem:
    def __init__(self, description="", quantity=1, unit_price=0.0, received=False):
        self.description = description
        self.quantity = quantity
        self.unit_price = unit_price
        self.received = received

    @classmethod
    def from_dict(cls, data):
        """Create a LineItem object from a dictionary"""
        return cls(
            description=data.get("description", ""),
            quantity=data.get("quantity", 1),
            unit_price=data.get("unit_price", 0.0),
            received=data.get("received", False)
        )

    def to_dict(self):
        """Convert LineItem object to a dictionary"""
        return {
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "received": self.received
        }

    def get_total(self):
        """Calculate total price for this line item"""
        return self.quantity * self.unit_price