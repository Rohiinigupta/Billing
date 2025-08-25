import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = "restaurant_billing.db"

# ----------------- DB Helpers -----------------
def get_connection():
    return sqlite3.connect(DB_PATH)

def get_menu():
    con = get_connection()
    df = pd.read_sql("SELECT id, item_name, category, price, gst_rate FROM menu WHERE is_active=1", con)
    con.close()
    return df

def save_order(order_mode, payment_method, items, discount=0.0, customer=""):
    con = get_connection()
    cur = con.cursor()

    subtotal = sum(row['qty'] * row['price'] for _, row in items.iterrows())
    tax_amount = sum(row['qty'] * row['price'] * row['gst_rate']/100 for _, row in items.iterrows())
    total = subtotal + tax_amount - discount

    cur.execute("""INSERT INTO orders 
        (order_mode, customer_name, subtotal, discount_amount, tax_amount, total_amount,
         payment_method, amount_paid, change_due, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (order_mode, customer, subtotal, discount, tax_amount, total,
         payment_method, total, 0, datetime.now().isoformat())
    )
    order_id = cur.lastrowid

    for _, row in items.iterrows():
        line_sub = row['price'] * row['qty']
        line_tax = line_sub * row['gst_rate']/100
        line_total = line_sub + line_tax
        cur.execute("""INSERT INTO order_items 
            (order_id, menu_id, item_name, unit_price, gst_rate, quantity, line_subtotal, line_tax, line_total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (order_id, row['id'], row['item_name'], row['price'], row['gst_rate'],
             row['qty'], line_sub, line_tax, line_total)
        )
    con.commit()
    con.close()
    return order_id

# ----------------- UI -----------------
st.set_page_config(page_title="Restaurant Billing", layout="wide")
st.title("Order Management")

# Order Mode + Customer
order_mode = st.radio("Order Type", ["DINE_IN", "TAKEAWAY"])
customer = st.text_input("Customer Name (optional)")

# Load Menu
menu = get_menu()
menu['qty'] = 0

st.subheader("Select Items")
for i, row in menu.iterrows():
    menu.at[i, 'qty'] = st.number_input(
        f"{row['item_name']} ({row['price']} ₹, GST {row['gst_rate']}%)",
        0, 20, 0, key=f"item_{row['id']}"
    )

# Filter selected items
order_items = menu[menu['qty'] > 0]

if not order_items.empty:
    st.subheader("🛒 Order Summary")
    st.dataframe(order_items[['item_name','qty','price','gst_rate']])

    subtotal = (order_items['qty'] * order_items['price']).sum()
    tax = (order_items['qty'] * order_items['price'] * order_items['gst_rate']/100).sum()

    discount = st.number_input("Discount (₹)", min_value=0.0, step=10.0)
    total = subtotal + tax - discount

    st.markdown(f"""
    ### Bill Breakdown
    - Subtotal: **₹{subtotal:.2f}**
    - GST: **₹{tax:.2f}**
    - Discount: **₹{discount:.2f}**
    - Final Total: **₹{total:.2f}**
    """)

    payment = st.selectbox("Payment Method", ["CASH","CARD","UPI","OTHER"])

    if st.button("Confirm & Save Order"):
        oid = save_order(order_mode, payment, order_items, discount, customer)
        st.success(f"Order #{oid} saved successfully! Final Total = ₹{total:.2f}")
