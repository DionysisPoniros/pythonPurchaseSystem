from models.vendor import Vendor


class VendorController:
    def __init__(self, data_manager):
        self.data_manager = data_manager

    def get_all_vendors(self):
        """Get all vendors as Vendor objects"""
        vendors_data = self.data_manager.get_vendors()
        return [Vendor.from_dict(v) for v in vendors_data]

    def get_vendor_by_id(self, vendor_id):
        """Get a vendor by ID"""
        vendors = self.data_manager.get_vendors()
        vendor_data = next((v for v in vendors if v.get("id") == vendor_id), None)
        if vendor_data:
            return Vendor.from_dict(vendor_data)
        return None

    def add_vendor(self, vendor):
        """Add a new vendor"""
        vendors = self.data_manager.get_vendors()

        # Check if vendor name already exists
        if any(v.get("name") == vendor.name for v in vendors):
            return False, "A vendor with this name already exists"

        vendors.append(vendor.to_dict())
        self.data_manager.save_vendors(vendors)
        return True, "Vendor added successfully"

    def update_vendor(self, vendor):
        """Update an existing vendor"""
        vendors = self.data_manager.get_vendors()

        # Check if vendor name already exists (for a different vendor)
        if any(v.get("name") == vendor.name and v.get("id") != vendor.id for v in vendors):
            return False, "A vendor with this name already exists"

        for i, v in enumerate(vendors):
            if v.get("id") == vendor.id:
                vendors[i] = vendor.to_dict()
                self.data_manager.save_vendors(vendors)

                # Update vendor name in purchases
                self.update_vendor_name_in_purchases(vendor.id, vendor.name)
                return True, "Vendor updated successfully"

        return False, "Vendor not found"

    def update_vendor_name_in_purchases(self, vendor_id, vendor_name):
        """Update vendor name in all related purchases"""
        purchases = self.data_manager.get_purchases()
        updated = False

        for purchase in purchases:
            if purchase.get("vendor_id") == vendor_id:
                purchase["vendor_name"] = vendor_name
                updated = True

        if updated:
            self.data_manager.save_purchases(purchases)

    def delete_vendor(self, vendor_id):
        """Delete a vendor by ID"""
        # First check if vendor is used in any purchases
        purchases = self.data_manager.get_purchases()
        if any(p.get("vendor_id") == vendor_id for p in purchases):
            return False, "Cannot delete vendor that is used in purchases"

        vendors = self.data_manager.get_vendors()
        initial_count = len(vendors)
        vendors = [v for v in vendors if v.get("id") != vendor_id]

        if len(vendors) < initial_count:
            self.data_manager.save_vendors(vendors)
            return True, "Vendor deleted successfully"

        return False, "Vendor not found"

    def get_vendor_names(self):
        """Get a list of all vendor names"""
        return [vendor.name for vendor in self.get_all_vendors()]