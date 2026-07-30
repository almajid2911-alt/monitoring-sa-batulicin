from app import app, db, Order
from sqlalchemy import func

with app.app_context():
    # Show top 20 rows' raw data to see column names and values
    rows = Order.query.limit(20).all()
    print("ALL STATUSES IN DB:", db.session.query(Order.status, func.count()).group_by(Order.status).all())
    
    if rows:
        print("SAMPLE STATUS:", rows[0].status)
    else:
        print("NO DATA FOUND IN DB")
