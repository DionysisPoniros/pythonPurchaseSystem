# controllers/purchase_controller.py
import csv
import uuid
from datetime import datetime
from sqlalchemy.orm import joinedload, selectinload
# Import related models needed for relationships and CSV import
from database.models import Purchase, LineItem, PurchaseBudget, Vendor, Budget


class PurchaseController:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_all_purchases(self):
        """Get all purchases directly as ORM objects with eager loading of relationships"""
        session = self.db_manager.Session()
        try:
            # Eager load line_items, budgets (with nested budget object), and vendor
            return session.query(Purchase).options(
                joinedload(Purchase.line_items),
                selectinload(Purchase.budgets).joinedload(PurchaseBudget.budget),
                joinedload(Purchase.vendor)
            ).all()
        finally:
            session.close()

    def get_purchase_by_id(self, purchase_id):
        """Get a purchase by ID with relationships eagerly loaded"""
        session = self.db_manager.Session()
        try:
            # Eager load line_items, budgets (with nested budget object), and vendor
            return session.query(Purchase).filter(
                Purchase.id == purchase_id
            ).options(
                joinedload(Purchase.line_items),
                selectinload(Purchase.budgets).joinedload(PurchaseBudget.budget),
                joinedload(Purchase.vendor)
            ).first()
        finally:
            session.close()

    def add_purchase(self, purchase_data):
        """Add a new purchase from form data"""
        session = self.db_manager.Session()
        try:
            # Create new purchase object
            new_purchase = Purchase(
                id=str(uuid.uuid4()),
                order_number=purchase_data.get("order_number", ""),
                invoice_number=purchase_data.get("invoice_number", ""),
                date=purchase_data.get("date", datetime.now().strftime("%Y-%m-%d")),
                vendor_id=purchase_data.get("vendor_id"),
                vendor_name=purchase_data.get("vendor_name", ""),
                status=purchase_data.get("status", "Pending"),
                approver=purchase_data.get("approver", ""),
                approval_date=purchase_data.get("approval_date"),
                notes=purchase_data.get("notes", "")
            )

            # Add line items
            for item_data in purchase_data.get("line_items", []):
                line_item = LineItem(
                    id=str(uuid.uuid4()),
                    description=item_data.get("description", ""),
                    quantity=item_data.get("quantity", 1),
                    unit_price=item_data.get("unit_price", 0.0),
                    received=item_data.get("received", False)
                )
                new_purchase.line_items.append(line_item)

            # Add budget allocations
            for budget_alloc in purchase_data.get("budgets", []):
                if budget_alloc.get("budget_id"):
                    purchase_budget = PurchaseBudget(
                        id=str(uuid.uuid4()),
                        budget_id=budget_alloc.get("budget_id"),
                        amount=budget_alloc.get("amount", 0.0)
                    )
                    new_purchase.budgets.append(purchase_budget)

            session.add(new_purchase)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error adding purchase: {str(e)}")
            return False
        finally:
            session.close()

    def update_purchase(self, purchase_id, updated_data):
        """Update an existing purchase"""
        session = self.db_manager.Session()
        try:
            # Fetch purchase with relationships needed for deletion/update
            purchase = session.query(Purchase).options(
                joinedload(Purchase.line_items),
                joinedload(Purchase.budgets)
            ).filter(Purchase.id == purchase_id).first()

            if not purchase:
                return False

            # Update purchase fields
            purchase.order_number = updated_data.get("order_number", purchase.order_number)
            purchase.invoice_number = updated_data.get("invoice_number", purchase.invoice_number)
            purchase.date = updated_data.get("date", purchase.date)
            purchase.vendor_id = updated_data.get("vendor_id", purchase.vendor_id)
            purchase.vendor_name = updated_data.get("vendor_name", purchase.vendor_name)
            purchase.status = updated_data.get("status", purchase.status)
            purchase.approver = updated_data.get("approver", purchase.approver)
            purchase.approval_date = updated_data.get("approval_date", purchase.approval_date)
            purchase.notes = updated_data.get("notes", purchase.notes)

            # Efficiently update line items: delete old, add new
            # Delete existing line items associated with the purchase
            for item in purchase.line_items:
                session.delete(item)
            # Clear the collection proxy to reflect the deletion
            purchase.line_items.clear()
            session.flush() # Ensure deletions are processed before adding new items

            # Add new line items
            for item_data in updated_data.get("line_items", []):
                line_item = LineItem(
                    id=str(uuid.uuid4()),
                    purchase_id=purchase_id, # Explicitly set purchase_id
                    description=item_data.get("description", ""),
                    quantity=item_data.get("quantity", 1),
                    unit_price=item_data.get("unit_price", 0.0),
                    received=item_data.get("received", False)
                )
                session.add(line_item) # Add directly to session

            # Efficiently update budget allocations: delete old, add new
            # Delete existing budget allocations
            for alloc in purchase.budgets:
                session.delete(alloc)
            # Clear the collection proxy
            purchase.budgets.clear()
            session.flush() # Ensure deletions are processed

            # Add new budget allocations
            for budget_alloc in updated_data.get("budgets", []):
                if budget_alloc.get("budget_id"):
                    purchase_budget = PurchaseBudget(
                        id=str(uuid.uuid4()),
                        purchase_id=purchase_id, # Explicitly set purchase_id
                        budget_id=budget_alloc.get("budget_id"),
                        amount=budget_alloc.get("amount", 0.0)
                    )
                    session.add(purchase_budget) # Add directly to session

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error updating purchase: {str(e)}")
            return False
        finally:
            session.close()

    def delete_purchase(self, purchase_id):
        """Delete a purchase by ID"""
        session = self.db_manager.Session()
        try:
            # Cascade delete should handle related LineItem and PurchaseBudget
            purchase = session.query(Purchase).filter(Purchase.id == purchase_id).first()
            if purchase:
                session.delete(purchase)
                session.commit()
                return True, "Purchase deleted successfully"
            return False, "Purchase not found"
        except Exception as e:
            session.rollback()
            return False, f"Error deleting purchase: {str(e)}"
        finally:
            session.close()

    def get_purchase_by_year(self, year):
        """Get purchases for a specific year with relationships eagerly loaded"""
        session = self.db_manager.Session()
        try:
            # Use SQL LIKE for filtering and eager load relationships
            return session.query(Purchase).filter(
                Purchase.date.like(f"{year}%")
            ).options(
                joinedload(Purchase.line_items),
                selectinload(Purchase.budgets).joinedload(PurchaseBudget.budget),
                joinedload(Purchase.vendor)
            ).all()
        finally:
            session.close()

    def get_current_year_purchases(self):
        """Get purchases from the current year"""
        return self.get_purchase_by_year(datetime.now().year)

    def count_pending_orders(self):
        """Count purchases with pending items using efficient query"""
        session = self.db_manager.Session()
        try:
             # Count purchases where not all line items are received
             # This might require a more complex query or iteration as before,
             # but ensure relationships are loaded if iterating.
             # For simplicity, retaining iteration with eager loading:
            purchases = session.query(Purchase).options(joinedload(Purchase.line_items)).all()
            # Filter in Python after loading
            pending_count = sum(1 for p in purchases if p.line_items and not all(item.received for item in p.line_items))
            return pending_count
        finally:
            session.close()

    # _is_fully_received helper can be removed if the logic is handled within count_pending_orders or model methods directly
    # def _is_fully_received(self, purchase): ... (removed for simplicity)

    def calculate_ytd_spending(self):
        """Calculate year-to-date spending"""
        session = self.db_manager.Session()
        try:
            current_year = datetime.now().year
            # Query purchases with line items for the current year
            purchases = session.query(Purchase).filter(
                Purchase.date.like(f"{current_year}%")
            ).options(joinedload(Purchase.line_items)).all()

            # Calculate total spending using the model's get_total method if available and safe,
            # or iterate through loaded line items.
            total = sum(purchase.get_total() for purchase in purchases)
            return total
        finally:
            session.close()

    # _calculate_purchase_total helper can likely be removed, rely on purchase.get_total()
    # def _calculate_purchase_total(self, purchase): ... (removed for simplicity)

    def receive_items(self, purchase_id, item_indices, received_status):
        """Mark items as received or not received"""
        session = self.db_manager.Session()
        try:
            # Load purchase and relevant line items efficiently
            purchase = session.query(Purchase).options(
                joinedload(Purchase.line_items)
            ).filter(Purchase.id == purchase_id).first()

            if not purchase:
                return False

            # Ensure line_items are loaded and accessible as a list
            line_items_list = list(purchase.line_items)

            updated = False
            for idx in item_indices:
                if 0 <= idx < len(line_items_list):
                    if line_items_list[idx].received != received_status:
                         line_items_list[idx].received = received_status
                         updated = True

            if updated:
                session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error receiving items: {str(e)}")
            return False
        finally:
            session.close()

    def approve_purchase(self, purchase_id, approver):
        """Approve a purchase"""
        session = self.db_manager.Session()
        try:
            purchase = session.query(Purchase).filter(Purchase.id == purchase_id).first()
            if not purchase:
                return False, "Purchase not found"

            if purchase.status == "Pending": # Only approve if pending
                purchase.status = "Approved"
                purchase.approver = approver
                purchase.approval_date = datetime.now().strftime("%Y-%m-%d")
                session.commit()
                return True, "Purchase approved successfully"
            else:
                return False, f"Purchase status is already {purchase.status}"
        except Exception as e:
            session.rollback()
            return False, f"Failed to approve purchase: {str(e)}"
        finally:
            session.close()

    def reject_purchase(self, purchase_id, approver, notes=""):
        """Reject a purchase"""
        session = self.db_manager.Session()
        try:
            purchase = session.query(Purchase).filter(Purchase.id == purchase_id).first()
            if not purchase:
                return False, "Purchase not found"

            if purchase.status == "Pending": # Only reject if pending
                purchase.status = "Rejected"
                purchase.approver = approver
                purchase.approval_date = datetime.now().strftime("%Y-%m-%d")
                purchase.notes = notes
                session.commit()
                return True, "Purchase rejected successfully"
            else:
                 return False, f"Purchase status is already {purchase.status}"
        except Exception as e:
            session.rollback()
            return False, f"Failed to reject purchase: {str(e)}"
        finally:
            session.close()

    def get_purchases_by_approval_status(self, status="Pending"):
        """Get purchases by approval status with relationships eagerly loaded"""
        session = self.db_manager.Session()
        try:
             # Eager load relationships needed for displaying these purchases
            return session.query(Purchase).filter(Purchase.status == status).options(
                joinedload(Purchase.line_items),
                selectinload(Purchase.budgets).joinedload(PurchaseBudget.budget),
                joinedload(Purchase.vendor)
            ).all()
        finally:
            session.close()

    def import_purchases_from_csv(self, file_path):
        """Import purchases from a CSV file"""
        session = self.db_manager.Session()
        try:
            imported_count = 0
            error_count = 0
            skipped_count = 0
            processed_orders = set() # Keep track of processed order numbers

            # Pre-fetch existing vendors and budgets for efficiency
            vendors_dict = {v.name: v.id for v in session.query(Vendor).all()}
            budgets_dict = {b.code: b.id for b in session.query(Budget).all()}
            existing_orders = {p.order_number for p in session.query(Purchase.order_number).all()}


            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile: # Added encoding
                reader = csv.DictReader(csvfile)
                if not reader.fieldnames:
                     return False, "CSV file is empty or header is missing."

                # Normalize headers (lowercase, strip spaces)
                reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]
                required_headers = ['order number', 'vendor', 'date']
                # Case-insensitive check for required headers
                if not all(req in reader.fieldnames for req in required_headers):
                     missing = [req for req in required_headers if req not in reader.fieldnames]
                     return False, f"Missing required CSV headers: {', '.join(missing)}"


                for row_num, row in enumerate(reader, start=2): # Start from row 2 (after header)
                    # Normalize row keys
                    row = {k.strip().lower(): v.strip() for k, v in row.items()}

                    order_number = row.get('order number', '').strip()

                    # Skip if required fields are missing for this row
                    if not order_number or not row.get('vendor') or not row.get('date'):
                        print(f"Skipping row {row_num}: Missing required fields (Order Number, Vendor, or Date).")
                        error_count += 1
                        continue

                    # Skip if order number already exists in DB or this batch
                    if order_number in existing_orders or order_number in processed_orders:
                        print(f"Skipping row {row_num}: Order Number '{order_number}' already exists.")
                        skipped_count += 1
                        continue

                    try:
                        # --- Vendor Handling ---
                        vendor_name = row.get('vendor', '').strip()
                        vendor_id = vendors_dict.get(vendor_name)

                        if not vendor_id:
                            # Create new vendor if not found
                            vendor_id = str(uuid.uuid4())
                            new_vendor = Vendor(
                                id=vendor_id,
                                name=vendor_name,
                            )
                            session.add(new_vendor)
                            vendors_dict[vendor_name] = vendor_id # Add to cache
                            print(f"Row {row_num}: Created new vendor '{vendor_name}'.")


                        # --- Date Parsing ---
                        date_str = row.get('date', '').strip()
                        date_formats = ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y/%m/%d"]
                        parsed_date = None
                        for fmt in date_formats:
                            try:
                                parsed_date = datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
                                break
                            except ValueError:
                                continue
                        if not parsed_date:
                            print(f"Skipping row {row_num}: Could not parse date '{date_str}'. Using today's date.")
                            # error_count += 1 # Decide if this counts as error or just use today
                            # continue
                            parsed_date = datetime.now().strftime("%Y-%m-%d")


                        # --- Create Purchase ---
                        purchase = Purchase(
                            id=str(uuid.uuid4()),
                            order_number=order_number,
                            invoice_number=row.get('invoice number', ''),
                            date=parsed_date,
                            vendor_id=vendor_id,
                            vendor_name=vendor_name, # Store name for easier display
                            status='Pending', # Default status for imported items
                        )
                        session.add(purchase)
                        session.flush() # Get purchase.id


                        # --- Line Item Handling ---
                        description = row.get('description', '').strip()
                        if description:
                            try:
                                quantity = int(float(row.get('quantity', '1'))) # Allow float then convert
                                unit_price = float(row.get('unit price', '0.0'))
                                if quantity <= 0 or unit_price < 0:
                                    raise ValueError("Quantity must be positive, Unit Price must be non-negative.")
                            except (ValueError, TypeError) as ve:
                                print(f"Skipping line item in row {row_num}: Invalid quantity or price - {ve}. Using defaults (1, 0.0).")
                                quantity = 1
                                unit_price = 0.0
                                # Decide if row should be skipped entirely if item data is bad
                                # error_count += 1
                                # continue # Skip whole row?

                            line_item = LineItem(
                                id=str(uuid.uuid4()),
                                purchase_id=purchase.id,
                                description=description,
                                quantity=quantity,
                                unit_price=unit_price,
                                received=False # Default for imported items
                            )
                            session.add(line_item)


                        # --- Budget Allocation Handling ---
                        budget_code = row.get('budget code', '').strip()
                        if budget_code:
                            budget_id = budgets_dict.get(budget_code)
                            if budget_id:
                                try:
                                    amount = float(row.get('amount', '0.0'))
                                    if amount <= 0:
                                        # If amount is required and invalid, skip budget alloc or whole row?
                                        print(f"Warning in row {row_num}: Budget amount '{row.get('amount')}' is invalid or zero. Skipping budget allocation.")
                                    else:
                                         purchase_budget = PurchaseBudget(
                                             id=str(uuid.uuid4()),
                                             purchase_id=purchase.id,
                                             budget_id=budget_id,
                                             amount=amount
                                         )
                                         session.add(purchase_budget)
                                except (ValueError, TypeError):
                                    print(f"Warning in row {row_num}: Invalid budget amount '{row.get('amount')}'. Skipping budget allocation.")
                            else:
                                print(f"Warning in row {row_num}: Budget code '{budget_code}' not found. Skipping budget allocation.")


                        processed_orders.add(order_number) # Mark order as processed in this batch
                        imported_count += 1

                    except Exception as e:
                        session.rollback() # Rollback transaction for this specific row
                        print(f"Error processing row {row_num} (Order: {order_number}): {str(e)}. Rolling back row.")
                        error_count += 1
                        # Need to re-add vendor to cache if it was created in this failed transaction?
                        # Or simply let the next row try again if the vendor is repeated.
                        # For simplicity, we don't handle the cache rollback here.
                        continue # Move to the next row

            # --- Final Commit ---
            session.commit() # Commit all successfully processed rows
            final_message = f"Import completed: {imported_count} purchases imported."
            if skipped_count > 0:
                final_message += f" {skipped_count} orders skipped (already existed)."
            if error_count > 0:
                final_message += f" {error_count} rows encountered errors (see console logs)."

            return True, final_message

        except FileNotFoundError:
            return False, f"Import failed: File not found at {file_path}"
        except Exception as e:
            session.rollback() # Rollback any partial commits if error happens outside row loop
            print(f"Critical import error: {str(e)}")
            return False, f"Import failed: {str(e)}"
        finally:
            session.close()