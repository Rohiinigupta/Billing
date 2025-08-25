"""
Restaurant Billing DB Initializer
Creates the SQLite database with tables: menu, orders, order_items, and seeds sample menu.
Usage:
    python init_db.py
This will create: restaurant_billing.db in the same folder.
"""
import sqlite3
from pathlib import Path
from textwrap import dedent

DB_PATH = Path("restaurant_billing.db")

schema_sql = "\nPRAGMA foreign_keys = ON;\n\n-- Menu: per-item GST (percentage) allows mixed-tax menus.\nCREATE TABLE IF NOT EXISTS menu (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    item_name TEXT NOT NULL UNIQUE,\n    category TEXT NOT NULL,\n    price REAL NOT NULL CHECK (price >= 0),\n    gst_rate REAL NOT NULL CHECK (gst_rate >= 0),\n    is_active INTEGER NOT NULL DEFAULT 1,\n    created_at TEXT NOT NULL DEFAULT (datetime('now')),\n    updated_at TEXT\n);\n\nCREATE INDEX IF NOT EXISTS idx_menu_category ON menu(category);\nCREATE INDEX IF NOT EXISTS idx_menu_active ON menu(is_active);\n\n-- Orders: supports Dine-In and Takeaway and saves payment info.\nCREATE TABLE IF NOT EXISTS orders (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    order_mode TEXT NOT NULL CHECK (order_mode IN ('DINE_IN','TAKEAWAY')),\n    table_no TEXT,                         -- optional: for dine-in\n    customer_name TEXT,\n    subtotal REAL NOT NULL DEFAULT 0,\n    discount_amount REAL NOT NULL DEFAULT 0,\n    tax_amount REAL NOT NULL DEFAULT 0,\n    total_amount REAL NOT NULL DEFAULT 0,\n    payment_method TEXT CHECK (payment_method IN ('CASH','CARD','UPI','OTHER')),\n    amount_paid REAL NOT NULL DEFAULT 0,\n    change_due REAL NOT NULL DEFAULT 0,\n    created_at TEXT NOT NULL,              -- ISO-8601 timestamp\n    notes TEXT\n);\n\nCREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);\nCREATE INDEX IF NOT EXISTS idx_orders_mode ON orders(order_mode);\n\n-- Order items: snapshot pricing & GST for auditability.\nCREATE TABLE IF NOT EXISTS order_items (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    order_id INTEGER NOT NULL,\n    menu_id INTEGER NOT NULL,\n    item_name TEXT NOT NULL,               -- snapshot of name at sale time\n    unit_price REAL NOT NULL,\n    gst_rate REAL NOT NULL,\n    quantity INTEGER NOT NULL CHECK (quantity > 0),\n    line_subtotal REAL NOT NULL,\n    line_tax REAL NOT NULL,\n    line_total REAL NOT NULL,\n    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,\n    FOREIGN KEY (menu_id) REFERENCES menu(id)\n);\n\nCREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);\n\n-- Optional helper view: denormalized order summary for reporting.\nCREATE VIEW IF NOT EXISTS v_order_summary AS\nSELECT \n    o.id AS order_id,\n    o.created_at,\n    o.order_mode,\n    o.table_no,\n    o.customer_name,\n    SUM(oi.line_subtotal) AS subtotal,\n    o.discount_amount,\n    SUM(oi.line_tax) AS tax_amount,\n    o.total_amount,\n    o.payment_method,\n    o.amount_paid,\n    o.change_due\nFROM orders o\nLEFT JOIN order_items oi ON oi.order_id = o.id\nGROUP BY o.id;\n"

seed_menu = [('Masala Dosa', 'Main Course', 120.0, 5.0), ('Paneer Tikka', 'Starter', 180.0, 5.0), ('Veg Fried Rice', 'Main Course', 150.0, 5.0), ('Butter Naan', 'Breads', 35.0, 5.0), ('Gulab Jamun (2 pc)', 'Desserts', 80.0, 5.0), ('Mineral Water 750ml', 'Beverages', 40.0, 18.0), ('Fresh Lime Soda', 'Beverages', 90.0, 18.0), ('Cold Coffee', 'Beverages', 140.0, 18.0)]

def init_db(db_path: Path):
    con = sqlite3.connect(db_path)
    try:
        con.executescript(schema_sql)
        cur = con.execute("SELECT COUNT(*) FROM menu")
        (count,) = cur.fetchone()
        if count == 0:
            con.executemany(
                "INSERT INTO menu (item_name, category, price, gst_rate) VALUES (?,?,?,?)",
                seed_menu
            )
        con.commit()
    finally:
        con.close()

if __name__ == "__main__":
    init_db(DB_PATH)
    print(f"✔ Database created at: {DB_PATH.resolve()}")
