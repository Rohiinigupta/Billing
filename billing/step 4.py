import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io

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

    # Insert order items
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
    return order_id, subtotal, tax_amount, total

def get_order_details(order_id):
    con = get_connection()
    df = pd.read_sql("""
        SELECT item_name, unit_price, quantity, gst_rate, line_subtotal, line_tax, line_total
        FROM order_items WHERE order_id=?""", con, params=(order_id,))
    order = pd.read_sql("SELECT * FROM orders WHERE id=?", con, params=(order_id,))
    con.close()
    return order.iloc[0], df

# ----------------- PDF Helper -----------------
def generate_pdf(order, items_df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "Restaurant Bill", ln=True, align="C")
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 8, f"Order ID: {order['id']} | Date: {order['created_at']}", ln=True)
    pdf.cell(200, 8, f"Mode: {order['order_mode']} | Payment: {order['payment_method']}", ln=True)
    pdf.cell(200, 8, f"Customer: {order['customer_name']}", ln=True)

    # Table Header
    pdf.set_font("Arial", "B", 10)
    pdf.cell(60, 8, "Item", 1)
    pdf.cell(20, 8, "Qty", 1, align="C")
    pdf.cell(30, 8, "Price", 1, align="R")
    pdf.cell(30, 8, "GST%", 1, align="R")
    pdf.cell(30, 8, "Total", 1, align="R")
    pdf.ln()

    # Items
    pdf.set_font("Arial", size=10)
    for _, row in items_df.iterrows():
        pdf.cell(60, 8, row['item_name'], 1)
        pdf.cell(20, 8, str(row['quantity']), 1, align="C")
        pdf.cell(30, 8, f"{row['unit_price']:.2f}", 1, align="R")
        pdf.cell(30, 8, f"{row['gst_rate']}%", 1, align="R")
        pdf.cell(30, 8, f"{row['line_total']:.2f}", 1, align="R")
        pdf.ln()

    # Totals
    pdf.ln(5)
    pdf.cell(200, 8, f"Subtotal: ₹{order['subtotal']:.2f}", ln=True, align="R")
    pdf.cell(200, 8, f"GST: ₹{order['tax_amount']:.2f}", ln=True, align="R")
    pdf.cell(200, 8, f"Discount: ₹{order['discount_amount']:.2f}", ln=True, align="R")
    pdf.cell(200, 8, f"Grand Total: ₹{order['total_amount']:.2f}", ln=True, align="R")

    pdf_output = io.BytesIO()
    pdf.output(pdf_output, "F")
    pdf_output.seek(0)
    return pdf_output

# ----------------- UI -----------------
st.set_page_config(page_title="Billing System", layout="wide")
st.title("Bill Generation & Export")

# Example: place an order
order_mode = st.radio("Order Type", ["DINE_IN", "TAKEAWAY"])
customer = st.text_input("Customer Name (optional)")

menu = get_menu()
menu['qty'] = 0

st.subheader("Select Items")
for i, row in menu.iterrows():
    menu.at[i, 'qty'] = st.number_input(
        f"{row['item_name']} ({row['price']} ₹, GST {row['gst_rate']}%)",
        0, 10, 0, key=f"item_{row['id']}"
    )

order_items = menu[menu['qty'] > 0]

if not order_items.empty:
    subtotal = (order_items['qty'] * order_items['price']).sum()
    tax = (order_items['qty'] * order_items['price'] * order_items['gst_rate']/100).sum()
    discount = st.number_input("Discount (₹)", min_value=0.0, step=10.0)
    total = subtotal + tax - discount

    st.write("### Bill Breakdown")
    st.write(f"Subtotal: ₹{subtotal:.2f} | GST: ₹{tax:.2f} | Discount: ₹{discount:.2f} | Total: ₹{total:.2f}")

    payment = st.selectbox("Payment Method", ["CASH","CARD","UPI","OTHER"])

    if st.button("Confirm & Generate Bill"):
        order_id, _, _, _ = save_order(order_mode, payment, order_items, discount, customer)
        st.success(f"Order #{order_id} saved!")

        order, items_df = get_order_details(order_id)

        # Show bill on screen
        st.subheader("Itemized Bill")
        st.table(items_df[['item_name','quantity','unit_price','gst_rate','line_total']])
        st.write(f"Subtotal: ₹{order['subtotal']:.2f}")
        st.write(f"GST: ₹{order['tax_amount']:.2f}")
        st.write(f"Discount: ₹{order['discount_amount']:.2f}")
        st.write(f"Final Total: ₹{order['total_amount']:.2f}")

        # Export options
        pdf_file = generate_pdf(order, items_df)
        st.download_button("Download Bill as PDF", pdf_file, file_name=f"bill_{order_id}.pdf")

        csv_file = items_df.to_csv(index=False).encode("utf-8")
        st.download_button("Export Items as CSV", csv_file, file_name=f"bill_{order_id}.csv")

        json_file = items_df.to_json(orient="records").encode("utf-8")
        st.download_button("Export Items as JSON", json_file, file_name=f"bill_{order_id}.json")
