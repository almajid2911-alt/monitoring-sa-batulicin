import sqlite3

def check_columns():
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(\"order\")")
    columns = [i[1] for i in cursor.fetchall()]
    print(f"Columns: {columns}")
    
    conn.close()

if __name__ == "__main__":
    check_columns()
