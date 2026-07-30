from app import app, db, Order
from sqlalchemy import func

with app.app_context():
    # Get all unique status_morning values
    status_mornings = db.session.query(Order.status_morning, func.count()).group_by(Order.status_morning).all()
    print("Unique STATUS MORNING in DB:")
    for sm, count in status_mornings:
        print(f"  '{sm}' : {count}")
    
    # Get all unique status values
    statuses = db.session.query(Order.status, func.count()).group_by(Order.status).all()
    print("\nUnique STATUS in DB:")
    for s, count in statuses:
        print(f"  '{s}' : {count}")

    # Find rows with PROSES SETTING
    p_setting = Order.query.filter(Order.status_morning.ilike('%SETTING%')).all()
    print(f"\nRows with 'SETTING' in status_morning: {len(p_setting)}")
    for r in p_setting[:10]:
        print(f"  ID: {r.id}, Status: {r.status}, Morning: {r.status_morning}, TIM: {r.tim}, Dispatch: {r.dispatch_date}")
    
    # Specifically check if there are WAPPR rows with SETTING
    wappr_setting = Order.query.filter(Order.status == 'WAPPR', Order.status_morning.ilike('%SETTING%')).all()
    print(f"\nWAPPR rows with 'SETTING' in status_morning: {len(wappr_setting)}")
