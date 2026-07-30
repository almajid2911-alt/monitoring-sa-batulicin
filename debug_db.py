import sqlite3

def check_db():
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tables: {tables}")
    
    for table_tuple in tables:
        table_name = table_tuple[0]
        cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        count = cursor.fetchone()[0]
        print(f"Rows in {table_name}: {count}")
        
        cursor.execute(f"PRAGMA table_info('{table_name}')")
        columns = [i[1] for i in cursor.fetchall()]
        print(f"Columns in {table_name}: {columns}")
        
        if count > 0:
            cursor.execute(f'SELECT status, status_morning, count(*) FROM "{table_name}" GROUP BY status, status_morning')
            group_counts = cursor.fetchall()
            print(f"Group counts (status, status_morning, count) for {table_name}:")
            for gc in group_counts:
                print(f"  {gc}")
    
    conn.close()

if __name__ == "__main__":
    check_db()
