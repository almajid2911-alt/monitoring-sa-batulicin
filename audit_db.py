from app import app, db, Order
from sqlalchemy import func

with app.app_context():
    # Show all statuses and counts
    counts = db.session.query(Order.status, func.count()).group_by(Order.status).all()
    print("STATUS COUNTS:", counts)
    
    # Show status_date_parsed values for "Potensi" statuses
    potensi_dates = db.session.query(Order.status_date_parsed, func.count()).filter(Order.status.in_(["VALSTART", "ACTCOMP", "VALCOMP"])).group_by(Order.status_date_parsed).all()
    print("POTENSI DATES:", potensi_dates)
