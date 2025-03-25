# database/db_manager.py
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from database.models import (
    Base, Vendor, Budget, YearlyBudgetAmount,
    Purchase, LineItem, PurchaseBudget
)

# Set up logging
logging.basicConfig(
    filename='database.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('database_manager')


class DatabaseManager:
    def __init__(self, db_path='purchase_system.db'):
        """Initialize the database manager"""
        from sqlalchemy.pool import QueuePool

        db_url = f'sqlite:///{db_path}'
        self.engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600
        )
        self.Session = scoped_session(sessionmaker(bind=self.engine))

        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)
        logger.info(f"Database initialized at {db_path}")

    def _commit_session(self, session):
        """Commit session and handle exceptions"""
        try:
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error: {str(e)}")
            return False

    # Vendor methods
    def get_vendors(self):
        """Get all vendors as dictionaries"""
        session = self.Session()
        try:
            vendors = session.query(Vendor).all()
            return [vendor.to_dict() for vendor in vendors]
        finally:
            session.close()

    def save_vendors(self, vendors_data):
        """Save multiple vendors to the database"""
        if not vendors_data:
            return True, "No vendors to save"

        session = self.Session()
        try:
            for vendor_data in vendors_data:
                # Check if vendor exists
                vendor = None
                if "id" in vendor_data:
                    vendor = session.query(Vendor).filter_by(id=vendor_data["id"]).first()

                if vendor:
                    # Update existing vendor
                    for key, value in vendor_data.items():
                        if key != "id":
                            setattr(vendor, key, value)
                else:
                    # Create new vendor
                    vendor = Vendor.from_dict(vendor_data)
                    session.add(vendor)

            if self._commit_session(session):
                return True, "Vendors saved successfully"
            return False, "Failed to save vendors"
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving vendors: {str(e)}")
            return False, f"Error saving vendors: {str(e)}"
        finally:
            session.close()

    def save_vendor(self, vendor_data):
        """Save a single vendor to the database"""
        session = self.Session()
        try:
            # Check if vendor exists
            vendor = None
            if "id" in vendor_data:
                vendor = session.query(Vendor).filter_by(id=vendor_data["id"]).first()

            if vendor:
                # Update existing vendor
                for key, value in vendor_data.items():
                    if key != "id":
                        setattr(vendor, key, value)
            else:
                # Create new vendor
                vendor = Vendor.from_dict(vendor_data)
                session.add(vendor)

            if self._commit_session(session):
                return vendor.to_dict()
            return None
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving vendor: {str(e)}")
            return None
        finally:
            session.close()

    def delete_vendor(self, vendor_id):
        """Delete a vendor by ID"""
        session = self.Session()
        try:
            vendor = session.query(Vendor).filter_by(id=vendor_id).first()
            if vendor:
                # Check if vendor is used in purchases
                purchases = session.query(Purchase).filter_by(vendor_id=vendor_id).count()
                if purchases > 0:
                    return False, "Cannot delete vendor that is used in purchases"

                session.delete(vendor)
                if self._commit_session(session):
                    return True, "Vendor deleted successfully"
            return False, "Vendor not found"
        finally:
            session.close()

    # Budget methods
    def get_budgets(self):
        """Get all budgets as dictionaries"""
        session = self.Session()
        try:
            budgets = session.query(Budget).all()
            return [budget.to_dict() for budget in budgets]
        finally:
            session.close()

    def save_budgets(self, budgets_data):
        """Save multiple budgets to the database"""
        if not budgets_data:
            return True, "No budgets to save"

        session = self.Session()
        try:
            for budget_data in budgets_data:
                self._save_budget(session, budget_data)

            if self._commit_session(session):
                return True, "Budgets saved successfully"
            return False, "Failed to save budgets"
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving budgets: {str(e)}")
            return False, f"Error saving budgets: {str(e)}"
        finally:
            session.close()

    def save_budget(self, budget_data):
        """Save a single budget to the database"""
        session = self.Session()
        try:
            budget = self._save_budget(session, budget_data)

            if self._commit_session(session):
                return budget.to_dict()
            return None
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving budget: {str(e)}")
            return None
        finally:
            session.close()

    def _save_budget(self, session, budget_data):
        """Helper method to save a budget (used by save_budget and save_budgets)"""
        # Check if budget exists
        budget = None
        if "id" in budget_data:
            budget = session.query(Budget).filter_by(id=budget_data["id"]).first()

        if budget:
            # Update existing budget
            budget.code = budget_data.get("code", budget.code)
            budget.name = budget_data.get("name", budget.name)
            budget.description = budget_data.get("description", budget.description)
        else:
            # Create new budget
            budget = Budget(
                id=budget_data.get("id"),
                code=budget_data.get("code", ""),
                name=budget_data.get("name", ""),
                description=budget_data.get("description", "")
            )
            session.add(budget)
            session.flush()  # Flush to get ID

        # Update yearly amounts
        yearly_amount_data = budget_data.get("yearly_amount", {})

        # Remove existing amounts
        session.query(YearlyBudgetAmount).filter_by(budget_id=budget.id).delete()

        # Add new amounts
        for year, amount in yearly_amount_data.items():
            yearly_amount = YearlyBudgetAmount(
                budget_id=budget.id,
                year=str(year),
                amount=float(amount)
            )
            session.add(yearly_amount)

        return budget

    def delete_budget(self, budget_id):
        """Delete a budget by ID"""
        session = self.Session()
        try:
            budget = session.query(Budget).filter_by(id=budget_id).first()
            if budget:
                # Check if budget is used in any purchases
                purchase_budgets = session.query(PurchaseBudget).filter_by(budget_id=budget_id).count()
                if purchase_budgets > 0:
                    return False, "Cannot delete budget that is used in purchases"

                session.delete(budget)
                if self._commit_session(session):
                    return True, "Budget deleted successfully"
            return False, "Budget not found"
        finally:
            session.close()

    # Purchase methods
    def get_purchases(self):
        """Get all purchases as dictionaries"""
        session = self.Session()
        try:
            purchases = session.query(Purchase).all()
            return [purchase.to_dict() for purchase in purchases]
        finally:
            session.close()

    def save_purchases(self, purchases_data):
        """Save multiple purchases to the database"""
        if not purchases_data:
            return True, "No purchases to save"

        session = self.Session()
        try:
            for purchase_data in purchases_data:
                self._save_purchase(session, purchase_data)

            if self._commit_session(session):
                return True, "Purchases saved successfully"
            return False, "Failed to save purchases"
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving purchases: {str(e)}")
            return False, f"Error saving purchases: {str(e)}"
        finally:
            session.close()

    def save_purchase(self, purchase_data):
        """Save a purchase to the database"""
        session = self.Session()
        try:
            purchase = self._save_purchase(session, purchase_data)

            if self._commit_session(session):
                return purchase.to_dict()
            return None
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving purchase: {str(e)}")
            return None
        finally:
            session.close()

    def _save_purchase(self, session, purchase_data):
        """Helper method to save a purchase (used by save_purchase and save_purchases)"""
        # Check if purchase exists
        purchase = None
        if "id" in purchase_data:
            purchase = session.query(Purchase).filter_by(id=purchase_data["id"]).first()

        if purchase:
            # Update existing purchase
            purchase.order_number = purchase_data.get("order_number", purchase.order_number)
            purchase.invoice_number = purchase_data.get("invoice_number", purchase.invoice_number)
            purchase.date = purchase_data.get("date", purchase.date)
            purchase.vendor_id = purchase_data.get("vendor_id", purchase.vendor_id)
            purchase.vendor_name = purchase_data.get("vendor_name", purchase.vendor_name)
            purchase.status = purchase_data.get("status", purchase.status)
            purchase.approver = purchase_data.get("approver", purchase.approver)
            purchase.approval_date = purchase_data.get("approval_date", purchase.approval_date)
            purchase.notes = purchase_data.get("notes", purchase.notes)

            # Delete existing line items and budget allocations
            session.query(LineItem).filter_by(purchase_id=purchase.id).delete()
            session.query(PurchaseBudget).filter_by(purchase_id=purchase.id).delete()
        else:
            # Create new purchase
            purchase = Purchase(
                id=purchase_data.get("id"),
                order_number=purchase_data.get("order_number", ""),
                invoice_number=purchase_data.get("invoice_number", ""),
                date=purchase_data.get("date"),
                vendor_id=purchase_data.get("vendor_id"),
                vendor_name=purchase_data.get("vendor_name", ""),
                status=purchase_data.get("status", "Pending"),
                approver=purchase_data.get("approver", ""),
                approval_date=purchase_data.get("approval_date"),
                notes=purchase_data.get("notes", "")
            )
            session.add(purchase)
            session.flush()  # Flush to get ID

        # Add line items
        line_items_data = purchase_data.get("line_items", [])
        for item_data in line_items_data:
            line_item = LineItem(
                purchase_id=purchase.id,
                description=item_data.get("description", ""),
                quantity=item_data.get("quantity", 1),
                unit_price=item_data.get("unit_price", 0.0),
                received=item_data.get("received", False)
            )
            session.add(line_item)

        # Add budget allocations
        budget_allocations = purchase_data.get("budgets", [])
        for allocation in budget_allocations:
            budget_id = allocation.get("budget_id")
            amount = allocation.get("amount", 0.0)

            if budget_id:
                purchase_budget = PurchaseBudget(
                    purchase_id=purchase.id,
                    budget_id=budget_id,
                    amount=amount
                )
                session.add(purchase_budget)

        return purchase

    def delete_purchase(self, purchase_id):
        """Delete a purchase by ID"""
        session = self.Session()
        try:
            purchase = session.query(Purchase).filter_by(id=purchase_id).first()
            if purchase:
                session.delete(purchase)
                if self._commit_session(session):
                    return True, "Purchase deleted successfully"
            return False, "Purchase not found"
        finally:
            session.close()

    def backup_database(self, backup_dir="backups"):
        """Create a backup of the database file"""
        import shutil
        from datetime import datetime

        # Ensure backup directory exists
        os.makedirs(backup_dir, exist_ok=True)

        # Create timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"purchase_system_{timestamp}.db")

        try:
            # Copy the database file
            shutil.copy2("purchase_system.db", backup_path)
            logger.info(f"Database backup created at {backup_path}")
            return True, f"Backup created at {backup_path}"
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            return False, f"Backup failed: {str(e)}"

    def get_db_stats(self):
        """Get database statistics"""
        from database.models import Vendor, Budget, Purchase, LineItem, PurchaseBudget, YearlyBudgetAmount

        session = self.Session()
        try:
            # Count records in each table
            stats = {
                "vendors": session.query(Vendor).count(),
                "budgets": session.query(Budget).count(),
                "purchases": session.query(Purchase).count(),
                "line_items": session.query(LineItem).count(),
                "budget_allocations": session.query(PurchaseBudget).count(),
                "yearly_budget_amounts": session.query(YearlyBudgetAmount).count()
            }

            # Get additional statistics
            pending_purchases = session.query(Purchase).filter_by(status="Pending").count()
            approved_purchases = session.query(Purchase).filter_by(status="Approved").count()
            rejected_purchases = session.query(Purchase).filter_by(status="Rejected").count()

            stats.update({
                "pending_purchases": pending_purchases,
                "approved_purchases": approved_purchases,
                "rejected_purchases": rejected_purchases
            })

            return stats
        except Exception as e:
            # Return empty stats if there's an error
            return {
                "vendors": 0, "budgets": 0, "purchases": 0, "line_items": 0,
                "budget_allocations": 0, "yearly_budget_amounts": 0,
                "pending_purchases": 0, "approved_purchases": 0, "rejected_purchases": 0
            }
        finally:
            session.close()

    def restore_from_backup(self, backup_path):
        """Restore database from a backup file"""
        import shutil
        import os

        try:
            # Close all connections to the database
            self.engine.dispose()

            # Original database path (extracted from connection string)
            original_db_path = self.engine.url.database

            # Create a temporary backup of current database just in case
            temp_backup = f"{original_db_path}.temp_backup"
            shutil.copy2(original_db_path, temp_backup)

            # Copy backup file to original location
            shutil.copy2(backup_path, original_db_path)

            # Recreate the engine and session factory
            self.engine = create_engine(f'sqlite:///{original_db_path}')
            self.Session = scoped_session(sessionmaker(bind=self.engine))

            logger.info(f"Database restored from backup: {backup_path}")
            return True, f"Database successfully restored from backup: {os.path.basename(backup_path)}"
        except Exception as e:
            logger.error(f"Restore failed: {str(e)}")
            return False, f"Restore failed: {str(e)}"