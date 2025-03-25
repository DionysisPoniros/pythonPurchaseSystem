import uuid
from datetime import datetime


class Budget:
    def __init__(self, id=None, code="", name="", description="", yearly_amount=None):
        self.id = id or str(uuid.uuid4())
        self.code = code
        self.name = name
        self.description = description
        self.yearly_amount = yearly_amount or {}

    @classmethod
    def from_dict(cls, data):
        """Create a Budget object from a dictionary"""
        return cls(
            id=data.get("id"),
            code=data.get("code", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            yearly_amount=data.get("yearly_amount", {})
        )

    def to_dict(self):
        """Convert Budget object to a dictionary"""
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "yearly_amount": self.yearly_amount
        }

    def get_amount_for_year(self, year=None):
        """Get budget amount for specified year"""
        year = year or str(datetime.now().year)
        return self.yearly_amount.get(str(year), 0)