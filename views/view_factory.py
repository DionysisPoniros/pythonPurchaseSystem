# views/view_factory.py
import importlib
import inspect
import tkinter as tk

class ViewFactory:
    """
    Factory class to create views without direct imports.
    This helps avoid circular import issues between view modules.
    """
    _view_cache = {}
    
    @staticmethod
    def create_view(view_name, parent, controllers, show_view_callback, **kwargs):
        """
        Create a view instance by name.
        
        Args:
            view_name: The name of the view class
            parent: Parent widget
            controllers: Dict of controllers
            show_view_callback: Callback to switch views
            **kwargs: Additional parameters to pass to the view constructor
            
        Returns:
            Instance of the requested view
        """
        # First check if we've already imported this view class
        if view_name in ViewFactory._view_cache:
            view_class = ViewFactory._view_cache[view_name]
        else:
            # Try to dynamically import the view class
            view_class = ViewFactory._import_view_class(view_name)
            if view_class:
                ViewFactory._view_cache[view_name] = view_class
            else:
                raise ValueError(f"View class '{view_name}' not found")
        
        # Create and return the view instance
        return view_class(parent, controllers, show_view_callback, **kwargs)
    
    @staticmethod
    def _import_view_class(view_name):
        """
        Try to import a view class by name.
        Searches in standard locations based on naming conventions.
        
        Args:
            view_name: The name of the view class
            
        Returns:
            The view class if found, None otherwise
        """
        # Map of view class names to their likely module paths
        view_modules = {
            # Main views
            'MainDashboard': 'views.main_dashboard',
            
            # List views
            'PurchaseListView': 'views.purchase_views',
            'VendorListView': 'views.vendor_views',
            'BudgetListView': 'views.budget_views',
            
            # Form views
            'PurchaseFormView': 'views.purchase_views',
            
            # Report views
            'BudgetReportView': 'views.report_views',
            'VendorReportView': 'views.report_views',
            
            # Special views
            'ReceivingDashboardView': 'views.receiving_view',
            'ApprovalDashboardView': 'views.approval_view'
        }
        
        # Try to import from the mapped module
        if view_name in view_modules:
            module_path = view_modules[view_name]
            try:
                module = importlib.import_module(module_path)
                return getattr(module, view_name)
            except (ImportError, AttributeError) as e:
                print(f"Error importing {view_name} from {module_path}: {str(e)}")
        
        # If not in the map or import failed, try to guess the module path
        if 'View' in view_name:
            # For view classes ending with 'View', try views.view_name_lower
            base_name = view_name.replace('View', '').lower()
            module_path = f"views.{base_name}_views"
            try:
                module = importlib.import_module(module_path)
                return getattr(module, view_name)
            except (ImportError, AttributeError):
                pass
        
        # Last resort: try to find it in all views modules
        try:
            # This is a simplified approach - in a real app you might want to
            # scan all modules in the views package
            views_pkg = importlib.import_module("views")
            for module_name in getattr(views_pkg, "__all__", []):
                try:
                    module = importlib.import_module(f"views.{module_name}")
                    if hasattr(module, view_name):
                        return getattr(module, view_name)
                except (ImportError, AttributeError):
                    pass
        except ImportError:
            pass
        
        return None