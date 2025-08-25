import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = "restaurant_billing.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def get_menu():
    con = get_connection()
    df = pd.read_sql("SELECT id, item_name, category, price, gst_rate FROM menu WHERE is_active=1", con)
    con.close()
    return df

def upload_menu(df):
    con = get_connection()
    cur = con.cursor()
    for _, row in df.iterrows():
        cur.execute("""
            INSERT OR REPLACE INTO menu (id, item_name, category, price, gst_rate, is_active, created_at)
            VALUES ((SELECT id FROM menu WHERE item_name=?), ?, ?, ?, ?, 1, datetime('now'))
        """, (row['item_name'], row['item_name'], row['category'], row['price'], row['gst_rate']))
    con.commit()
    con.close()

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
st.title("🍴 Restaurant Billing System")

menu_tabs = st.tabs(["Admin: Upload Menu", "New Order"])

# -------- Admin Tab --------
with menu_tabs[0]:
    st.subheader("📥 Upload Menu (CSV)")
    st.info("CSV must have columns: item_name, category, price, gst_rate")
    file = st.file_uploader("Upload Menu CSV", type="csv")
    if file:
        df = pd.read_csv(file)
        if set(["item_name","category","price","gst_rate"]).issubset(df.columns):
            upload_menu(df)
            st.success("✅ Menu uploaded successfully!")
            st.dataframe(get_menu())
        else:
            st.error("CSV missing required columns.")

# -------- Order Tab --------
with menu_tabs[1]:
    st.subheader("🧾 Create New Order")

    order_mode = st.radio("Order Type", ["DINE_IN", "TAKEAWAY"])
    customer = st.text_input("Customer Name (optional)")
    
  
    menu = get_menu()
    menu['qty'] = 0
    st.write("### Menu")
    for i, row in menu.iterrows():
        menu.at[i, 'qty'] = st.number_input(
            f"{row['item_name']} ({row['price']} ₹, GST {row['gst_rate']}%)",
            0, 20, 0, key=f"item_{row['id']}"
        )

    order_items = menu[menu['qty'] > 0]

    if not order_items.empty:
        st.write("### Order Summary")
        st.dataframe(order_items[['item_name','qty','price','gst_rate']])

        subtotal = (order_items['qty'] * order_items['price']).sum()
        tax = (order_items['qty'] * order_items['price'] * order_items['gst_rate']/100).sum()
        total = subtotal + tax

        st.metric("Subtotal", f"₹{subtotal:.2f}")
        st.metric("Tax", f"₹{tax:.2f}")
        st.metric("Total", f"₹{total:.2f}")

        payment = st.selectbox("Payment Method", ["CASH","CARD","UPI","OTHER"])

        if st.button("Confirm & Save Order"):
            oid = save_order(order_mode, payment, order_items, customer=customer)
            st.success(f"✅ Order #{oid} saved successfully!")
