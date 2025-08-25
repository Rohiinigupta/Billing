import sqlite3
import pandas as pd

DB_PATH = "restaurant_billing.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

# --- Daily, Weekly, Monthly Sales ---
def sales_summary():
    con = get_connection()
    daily = pd.read_sql_query("""
        SELECT date(created_at) as day, SUM(total_amount) as total_sales, COUNT(*) as total_orders
        FROM orders
        GROUP BY date(created_at)
    """, con)

    weekly = pd.read_sql_query("""
        SELECT strftime('%Y-%W', created_at) as week, SUM(total_amount) as total_sales, COUNT(*) as total_orders
        FROM orders
        GROUP BY strftime('%Y-%W', created_at)
    """, con)

    monthly = pd.read_sql_query("""
        SELECT strftime('%Y-%m', created_at) as month, SUM(total_amount) as total_sales, COUNT(*) as total_orders
        FROM orders
        GROUP BY strftime('%Y-%m', created_at)
    """, con)

    con.close()
    return daily, weekly, monthly

# --- Most Sold Items ---
def most_sold_items(limit=10):
    con = get_connection()
    df = pd.read_sql_query(f"""
        SELECT item_name, SUM(quantity) as total_qty, SUM(line_total) as total_sales
        FROM order_items
        GROUP BY item_name
        ORDER BY total_qty DESC
        LIMIT {limit}
    """, con)
    con.close()
    return df

# --- Export any DataFrame as CSV ---
def export_report(df, filename="report.csv"):
    df.to_csv(filename, index=False)
    return filename
