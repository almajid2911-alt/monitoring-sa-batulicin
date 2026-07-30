import sqlite3

def check_order(order_id):
    conn = sqlite3.connect('orders.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM \"order\" WHERE track_order=?", (order_id,))
    order = cursor.fetchone()
    
    if order:
        print("Data in Database:")
        for key in order.keys():
            print(f"{key}: {order[key]}")
    else:
        print(f"Order {order_id} not found")
    
    conn.close()

if __name__ == "__main__":
    check_order('AOi4260401123616348386c80')
