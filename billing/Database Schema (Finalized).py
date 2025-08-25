-- orders table
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_mode TEXT CHECK(order_mode IN ('dine-in', 'takeaway')),
    customer_name TEXT,
    subtotal REAL,
    discount_amount REAL,
    tax_amount REAL,
    total_amount REAL,
    payment_method TEXT,
    amount_paid REAL,
    change_due REAL,
    created_at TEXT DEFAULT (datetime('now')) -- ISO8601 timestamp
);

-- order_items table
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    menu_id INTEGER,
    item_name TEXT,
    unit_price REAL,
    gst_rate REAL,
    quantity INTEGER,
    line_subtotal REAL,
    line_tax REAL,
    line_total REAL,
    FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY(menu_id) REFERENCES menu(id)
);

