import sqlite3
import os
import sys

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "orders.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# List tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cur.fetchall()]
print("Tables:", tables)

table_name = tables[0] if tables else None
if not table_name:
    print("No tables found!")
    conn.close()
    sys.exit(1)

# Count total rows
cur.execute(f'SELECT COUNT(*) FROM "{table_name}"')
total = cur.fetchone()[0]
print(f"Total rows in DB: {total}")

# Search for partial match AOi
track_id = "AOi4260407093146766c19260"
print(f"\nSearching for: {track_id}")

# Try with the partial core digits
slices = [
    track_id,
    track_id.upper(),
    track_id.lower(),
    "4260407093146766c19260",
    "146766c19260",
    "AOi426040709",
]

for s in slices:
    cur.execute(f'SELECT track_order, status, status_morning, tim FROM "{table_name}" WHERE track_order LIKE ?', (f'%{s}%',))
    rows = cur.fetchall()
    if rows:
        print(f"\nFound with pattern '{s}':")
        for r in rows:
            print(dict(r))
        break
else:
    print("Order NOT FOUND in DB with any pattern.")

# Show sample of AOi orders in DB for comparison
print("\nSample AOi orders in DB (last 5):")
cur.execute(f'SELECT track_order, status, status_morning FROM "{table_name}" WHERE track_order LIKE "AOi%" ORDER BY id DESC LIMIT 5')
for r in cur.fetchall():
    print(dict(r))

conn.close()
