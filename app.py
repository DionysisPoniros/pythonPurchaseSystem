from tkinter import ttk
import tkinter as tk
from tkinter import messagebox
from database.db_manager import DatabaseManager
from database.models import Base
from controllers.purchase_controller import PurchaseController
from controllers.vendor_controller import VendorController
from controllers.budget_controller import BudgetController
from controllers.report_controller import ReportController
from views.main_dashboard import MainDashboard
import os



class PurchaseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Purchase Management System")
        self.root.geometry("900x700")
        self.root.minsize(900, 700)
        
        # Initialize database manager
        self.db_manager = DatabaseManager()

        # Initialize controllers
        self.controllers = {
            "purchase": PurchaseController(self.db_manager),
            "vendor": VendorController(self.db_manager),
            "budget": BudgetController(self.db_manager),
            "report": ReportController(self.db_manager)
        }

        # Set up controller cross-references
        self.controllers["budget"].set_purchase_controller(self.controllers["purchase"])
        self.controllers["report"].set_controllers(
            self.controllers["purchase"],
            self.controllers["budget"],
            self.controllers["vendor"]
        )

        # Create main frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Setup menu
        self.setup_menu()

        # Initialize views
        self.current_view = None
        self.dashboard = MainDashboard(self.main_frame, self.controllers, self.show_view)

        # Default view
        self.show_view(self.dashboard)
    def setup_styles(self):
        # Create custom styles
        style = ttk.Style()
        
        # Configure a modern theme
        style.theme_use('clam')  # Or 'alt' depending on platform
        
        # Custom button style
        style.configure('TButton', 
                        font=('Arial', 10),
                        padding=6, 
                        relief="flat",
                        background="#4e79a7")
        
        # Custom treeview style
        style.configure("Treeview", 
                        background="#f5f5f5",
                        fieldbackground="#f5f5f5", 
                        rowheight=25)
        
        style.configure("Treeview.Heading", 
                        font=('Arial', 10, 'bold'))

    def setup_menu(self):
        """Set up the application menu"""
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Database menu
        db_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Database", menu=db_menu)
        db_menu.add_command(label="Database Management", command=self.show_db_management)
        db_menu.add_command(label="Backup Database", command=self.backup_database)
        db_menu.add_command(label="Restore from Backup", command=self.restore_database)  # New option
        db_menu.add_command(label="View Statistics", command=self.show_db_stats)

    def show_view(self, view):
        """Switch to the specified view"""
        if self.current_view:
            self.current_view.hide()
        self.current_view = view
        self.current_view.show()

    def backup_database(self):
        """Create a backup of the database"""
        success, message = self.db_manager.backup_database()
        if success:
            messagebox.showinfo("Backup Successful", message)
        else:
            messagebox.showerror("Backup Failed", message)

    def show_db_management(self):
        """Show database management dialog"""
        from database.sample_data import generate_sample_data

        dialog = tk.Toplevel(self.root)
        dialog.title("Database Management")
        dialog.geometry("400x350")  # Slightly taller to accommodate the new button
        dialog.transient(self.root)
        dialog.grab_set()

        # Create frame for buttons
        btn_frame = tk.Frame(dialog, padx=20, pady=20)
        btn_frame.pack(fill=tk.BOTH, expand=True)

        def regenerate_data():
            if messagebox.askyesno("Confirm Regenerate",
                                   "This will ERASE all existing data and generate new sample data. Continue?"):
                try:
                    # Drop and recreate tables
                    from database.models import Base
                    self.db_manager.engine.dispose()
                    Base.metadata.drop_all(self.db_manager.engine)
                    Base.metadata.create_all(self.db_manager.engine)

                    # Generate new data
                    generate_sample_data()
                    messagebox.showinfo("Success", "Sample data regenerated successfully.")

                    # Refresh the dashboard
                    self.show_view(self.dashboard)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to regenerate data: {str(e)}")

        tk.Label(btn_frame, text="Database Management", font=("Arial", 14, "bold")).pack(pady=(0, 20))

        tk.Button(btn_frame, text="Backup Database", width=20, height=2,
                  command=self.backup_database).pack(pady=10)

        tk.Button(btn_frame, text="Restore from Backup", width=20, height=2,
                  command=self.restore_database).pack(pady=10)  # New button

        tk.Button(btn_frame, text="Regenerate Sample Data", width=20, height=2,
                  command=regenerate_data).pack(pady=10)

        tk.Button(btn_frame, text="View Database Statistics", width=20, height=2,
                  command=self.show_db_stats).pack(pady=10)

        tk.Button(btn_frame, text="Close", width=20,
                  command=dialog.destroy).pack(pady=20)

    def show_db_stats(self):
        """Show database statistics"""
        stats = self.db_manager.get_db_stats()

        dialog = tk.Toplevel(self.root)
        dialog.title("Database Statistics")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()

        # Create frame for content
        content_frame = tk.Frame(dialog, padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(content_frame, text="Database Statistics",
                 font=("Arial", 14, "bold")).pack(pady=(0, 20))

        # Record counts section
        record_frame = tk.LabelFrame(content_frame, text="Record Counts", padx=10, pady=10)
        record_frame.pack(fill=tk.X, pady=10)

        for i, (key, value) in enumerate([
            ("Vendors", stats["vendors"]),
            ("Budgets", stats["budgets"]),
            ("Purchases", stats["purchases"]),
            ("Line Items", stats["line_items"]),
            ("Budget Allocations", stats["budget_allocations"]),
            ("Yearly Budget Amounts", stats["yearly_budget_amounts"])
        ]):
            row = i // 2
            col = i % 2 * 2

            tk.Label(record_frame, text=f"{key}:").grid(row=row, column=col, sticky="w", padx=5, pady=5)
            tk.Label(record_frame, text=str(value), font=("Arial", 10, "bold")).grid(
                row=row, column=col + 1, sticky="w", padx=5, pady=5)

        # Purchase statistics section
        purchase_frame = tk.LabelFrame(content_frame, text="Purchase Statistics", padx=10, pady=10)
        purchase_frame.pack(fill=tk.X, pady=10)

        for i, (key, value) in enumerate([
            ("Pending Purchases", stats["pending_purchases"]),
            ("Approved Purchases", stats["approved_purchases"]),
            ("Rejected Purchases", stats["rejected_purchases"])
        ]):
            tk.Label(purchase_frame, text=f"{key}:").grid(row=i, column=0, sticky="w", padx=5, pady=5)
            tk.Label(purchase_frame, text=str(value), font=("Arial", 10, "bold")).grid(
                row=i, column=1, sticky="w", padx=5, pady=5)

        # Close button
        tk.Button(content_frame, text="Close", width=20,
                  command=dialog.destroy).pack(pady=20)

    def restore_database(self):
        """Restore database from a backup"""
        from tkinter import filedialog

        # Backup directory
        backup_dir = "backups"

        # Show file selection dialog
        backup_path = filedialog.askopenfilename(
            initialdir=backup_dir,
            title="Select Backup File",
            filetypes=[("Database files", "*.db"), ("All files", "*.*")]
        )

        if not backup_path:
            return  # User cancelled

        # Confirm before restoring
        if messagebox.askyesno("Confirm Restore",
                               "This will REPLACE your current database with the selected backup. Continue?"):
            success, message = self.db_manager.restore_from_backup(backup_path)

            if success:
                messagebox.showinfo("Restore Successful", message)
                # Refresh the dashboard
                self.show_view(self.dashboard)
            else:
                messagebox.showerror("Restore Failed", message)



def main():
    root = tk.Tk()
    app = PurchaseApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()