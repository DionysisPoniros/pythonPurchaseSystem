# database/db_manager.py
import os
import logging
import shutil
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from database.models import Base

# Import centralized settings
from config.settings import DATABASE_URL, DATABASE_FILE, BACKUP_DIR

# Set up logging
logging.basicConfig(
    filename='database.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('database_manager')


class DatabaseManager:
    def __init__(self, db_url=None):
        """Initialize the database manager"""
        from sqlalchemy.pool import QueuePool

        # Use the provided URL or default from settings
        self.db_url = db_url or DATABASE_URL
        self.db_file = DATABASE_FILE
        
        self.engine = create_engine(
            self.db_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600
        )
        self.Session = scoped_session(sessionmaker(bind=self.engine))

        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)
        logger.info(f"Database initialized at {self.db_file}")

    def _commit_session(self, session):
        """Commit session and handle exceptions"""
        try:
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error: {str(e)}")
            return False

    def backup_database(self, backup_dir=None):
        """Create a backup of the database file"""
        # Use the provided backup directory or default from settings
        backup_dir = backup_dir or BACKUP_DIR
        
        # Ensure backup directory exists
        os.makedirs(backup_dir, exist_ok=True)

        # Create timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"{os.path.splitext(self.db_file)[0]}_{timestamp}.db")

        try:
            # Copy the database file
            shutil.copy2(self.db_file, backup_path)
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
            logger.error(f"Error getting database stats: {str(e)}")
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
        try:
            # Close all connections to the database
            self.engine.dispose()

            # Create a temporary backup of current database just in case
            temp_backup = f"{self.db_file}.temp_backup"
            shutil.copy2(self.db_file, temp_backup)

            # Copy backup file to original location
            shutil.copy2(backup_path, self.db_file)

            # Recreate the engine and session factory
            self.engine = create_engine(self.db_url)
            self.Session = scoped_session(sessionmaker(bind=self.engine))

            logger.info(f"Database restored from backup: {backup_path}")
            return True, f"Database successfully restored from backup: {os.path.basename(backup_path)}"
        except Exception as e:
            logger.error(f"Restore failed: {str(e)}")
            return False, f"Restore failed: {str(e)}"