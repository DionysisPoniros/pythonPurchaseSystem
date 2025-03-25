# controllers/vendor_controller.py
from models.vendor import Vendor

class VendorController:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_all_vendors(self):
        """Get all vendors as Vendor objects"""
        vendors_data = self.db_manager.get_vendors()
        return [Vendor.from_dict(v) for v in vendors_data]

    def get_vendor_by_id(self, vendor_id):
        """Get a vendor by ID"""
        vendors = self.db_manager.get_vendors()
        vendor_data = next((v for v in vendors if v.get("id") == vendor_id), None)
        if vendor_data:
            return Vendor.from_dict(vendor_data)
        return None

    def add_vendor(self, vendor):
        """Add a new vendor"""
        vendors = self.db_manager.get_vendors()

        # Check if vendor name already exists
        if any(v.get("name") == vendor.name for v in vendors):
            return False, "A vendor with this name already exists"

        result = self.db_manager.save_vendor(vendor.to_dict())
        if result:
            return True, "Vendor added successfully"
        return False, "Failed to add vendor"

    def update_vendor(self, vendor):
        """Update an existing vendor"""
        vendors = self.db_manager.get_vendors()

        # Check if vendor name already exists (for a different vendor)
        if any(v.get("name") == vendor.name and v.get("id") != vendor.id for v in vendors):
            return False, "A vendor with this name already exists"

        result = self.db_manager.save_vendor(vendor.to_dict())
        if result:
            # Update vendor name in purchases
            self.update_vendor_name_in_purchases(vendor.id, vendor.name)
            return True, "Vendor updated successfully"

        return False, "Vendor not found"

    def update_vendor_name_in_purchases(self, vendor_id, vendor_name):
        """Update vendor name in all related purchases"""
        purchases = self.db_manager.get_purchases()
        updated = False

        for purchase in purchases:
            if purchase.get("vendor_id") == vendor_id:
                purchase["vendor_name"] = vendor_name
                self.db_manager.save_purchase(purchase)
                updated = True

    def delete_vendor(self, vendor_id):
        """Delete a vendor by ID"""
        return self.db_manager.delete_vendor(vendor_id)

    def get_vendor_names(self):
        """Get a list of all vendor names"""
        return [vendor.name for vendor in self.get_all_vendors()]