import sqlite3

def find_pending():
    conn = sqlite3.connect('orders.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT track_order, status_morning, catatan FROM \"order\" WHERE status_morning LIKE '%PENDING%' OR catatan LIKE '%Pending%'")
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} pending records:")
    for row in rows:
        print(f"TR: {row['track_order']} | SM: {row['status_morning']} | Cat: {row['catatan']}")
    
    conn.close()

if __name__ == "__main__":
    find_pending()
