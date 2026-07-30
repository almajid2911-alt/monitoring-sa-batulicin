import sqlite3

def check_order(order_id):
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, status, status_morning, keterangan FROM \"order\" WHERE id=?", (order_id,))
    order = cursor.fetchone()
    
    if order:
        print(f"Order ID: {order[0]}")
        print(f"Status: {order[1]}")
        print(f"Status Morning: {order[2]}")
        print(f"Keterangan: {order[3]}")
    else:
        print(f"Order {order_id} not found")
    
    conn.close()

if __name__ == "__main__":
    check_order('AOi4260401123616348386c80')
