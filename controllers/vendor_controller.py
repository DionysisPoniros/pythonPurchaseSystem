# controllers/vendor_controller.py
from database.models import Vendor, Purchase
from sqlalchemy.orm import joinedload
import uuid

class VendorController:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_all_vendors(self):
        """Get all vendors as Vendor objects"""
        session = self.db_manager.Session()
        try:
            return session.query(Vendor).all()
        finally:
            session.close()

    def get_vendor_by_id(self, vendor_id):
        """Get a vendor by ID"""
        session = self.db_manager.Session()
        try:
            return session.query(Vendor).filter(Vendor.id == vendor_id).first()
        finally:
            session.close()

    def add_vendor(self, vendor_data):
        """Add a new vendor using SQLAlchemy models"""
        session = self.db_manager.Session()
        try:
            # Check if vendor name already exists
            existing = session.query(Vendor).filter(Vendor.name == vendor_data.get('name')).first()
            if existing:
                return False, "A vendor with this name already exists"
            
            # Create new vendor from data
            vendor = Vendor(
                id=vendor_data.get('id') or str(uuid.uuid4()),
                name=vendor_data.get('name', ''),
                contact=vendor_data.get('contact', ''),
                phone=vendor_data.get('phone', ''),
                email=vendor_data.get('email', ''),
                address=vendor_data.get('address', '')
            )
            
            session.add(vendor)
            session.commit()
            return True, "Vendor added successfully"
        except Exception as e:
            session.rollback()
            return False, f"Failed to add vendor: {str(e)}"
        finally:
            session.close()

    def update_vendor(self, vendor_data):
        """Update an existing vendor"""
        session = self.db_manager.Session()
        try:
            vendor_id = vendor_data.get('id')
            if not vendor_id:
                return False, "Vendor ID is required"
            
            # Check if vendor exists
            vendor = session.query(Vendor).filter(Vendor.id == vendor_id).first()
            if not vendor:
                return False, "Vendor not found"
            
            # Check if vendor name already exists (for a different vendor)
            name = vendor_data.get('name')
            existing = session.query(Vendor).filter(
                Vendor.name == name, Vendor.id != vendor_id
            ).first()
            if existing:
                return False, "A vendor with this name already exists"
            
            # Update vendor fields
            vendor.name = vendor_data.get('name', vendor.name)
            vendor.contact = vendor_data.get('contact', vendor.contact)
            vendor.phone = vendor_data.get('phone', vendor.phone)
            vendor.email = vendor_data.get('email', vendor.email)
            vendor.address = vendor_data.get('address', vendor.address)
            
            # Update vendor name in purchases
            purchases = session.query(Purchase).filter(Purchase.vendor_id == vendor_id).all()
            for purchase in purchases:
                purchase.vendor_name = vendor.name
            
            session.commit()
            return True, "Vendor updated successfully"
        except Exception as e:
            session.rollback()
            return False, f"Failed to update vendor: {str(e)}"
        finally:
            session.close()

    def delete_vendor(self, vendor_id):
        """Delete a vendor by ID"""
        session = self.db_manager.Session()
        try:
            # Check if vendor is used in purchases
            purchases = session.query(Purchase).filter(Purchase.vendor_id == vendor_id).count()
            if purchases > 0:
                return False, "Cannot delete vendor that is used in purchases"
            
            # Delete vendor
            vendor = session.query(Vendor).filter(Vendor.id == vendor_id).first()
            if vendor:
                session.delete(vendor)
                session.commit()
                return True, "Vendor deleted successfully"
            
            return False, "Vendor not found"
        except Exception as e:
            session.rollback()
            return False, f"Failed to delete vendor: {str(e)}"
        finally:
            session.close()

    def get_vendor_names(self):
        """Get a list of all vendor names"""
        session = self.db_manager.Session()
        try:
            vendors = session.query(Vendor).all()
            return [vendor.name for vendor in vendors]
        finally:
            session.close()