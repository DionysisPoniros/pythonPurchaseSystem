import tkinter as tk
from utils.data_manager import DataManager
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

        # Initialize data manager
        self.data_manager = DataManager()

        # Generate test data if needed
        self.generate_test_data()

        # Initialize controllers
        self.controllers = {
            "purchase": PurchaseController(self.data_manager),
            "vendor": VendorController(self.data_manager),
            "budget": BudgetController(self.data_manager),
            "report": ReportController(self.data_manager)
        }

        # Create main frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Initialize views
        self.current_view = None
        self.dashboard = MainDashboard(self.main_frame, self.controllers, self.show_view)

        # Default view
        self.show_view(self.dashboard)

    def show_view(self, view):
        """Switch to the specified view"""
        if self.current_view:
            self.current_view.hide()
        self.current_view = view
        self.current_view.show()

    def generate_test_data(self):
        """Generate test data if no data exists"""
        # This is just a placeholder - we moved this to DataManager and it gets
        # called from there when needed
        pass


def main():
    root = tk.Tk()
    app = PurchaseApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()