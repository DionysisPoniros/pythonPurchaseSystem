import uuid


class Vendor:
    def __init__(self, id=None, name="", contact="", phone="", email="", address=""):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.contact = contact
        self.phone = phone
        self.email = email
        self.address = address

    @classmethod
    def from_dict(cls, data):
        """Create a Vendor object from a dictionary"""
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            contact=data.get("contact", ""),
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            address=data.get("address", "")
        )

    def to_dict(self):
        """Convert Vendor object to a dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "contact": self.contact,
            "phone": self.phone,
            "email": self.email,
            "address": self.address
        }