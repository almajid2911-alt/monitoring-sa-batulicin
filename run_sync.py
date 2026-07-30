from app import app, db, sync_orders
import os

with app.app_context():
    # Ensure tables are created (just in case)
    db.create_all()
    print("Syncing orders...")
    count = sync_orders()
    print(f"Synced {count} rows.")
