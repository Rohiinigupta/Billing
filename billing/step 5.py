import sqlite3
from datetime import datetime

DB_PATH = "restaurant_billing.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

# Save completed order + items
def save_order(order_mode, payment_method, items_df, discount=0.0, customer=""):
    con = get_connection()
    cur = con.cursor()

    # ---- totals ----
    subtotal = sum(row['qty'] * row['price'] for _, row in items_df.iterrows())
    tax_amount = sum(row['qty'] * row['price'] * row['gst_rate']/100 for _, row in items_df.iterrows())
    total = subtotal + tax_amount - discount

    # ---- insert into orders ----
    cur.execute("""
        INSERT INTO orders 
        (order_mode, customer_name, subtotal, discount_amount, tax_amount, total_amount, 
         payment_method, amount_paid, change_due, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        order_mode, customer, subtotal, discount, tax_amount, total,
        payment_method, total, 0, datetime.now().isoformat()
    ))
    order_id = cur.lastrowid

    # ---- insert each item ----
    for _, row in items_df.iterrows():
        line_sub = row['price'] * row['qty']
        line_tax = line_sub * row['gst_rate']/100
        line_total = line_sub + line_tax
        cur.execute("""
            INSERT INTO order_items 
            (order_id, menu_id, item_name, unit_price, gst_rate, quantity, line_subtotal, line_tax, line_total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_id, row['id'], row['item_name'], row['price'], row['gst_rate'],
            row['qty'], line_sub, line_tax, line_total
        ))

    con.commit()
    con.close()
    return order_id

# Retrieve order + items later
def get_order_details(order_id):
    con = get_connection()
    order = con.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    items = con.execute("SELECT * FROM order_items WHERE order_id=?", (order_id,)).fetchall()
    con.close()
    return order, items
