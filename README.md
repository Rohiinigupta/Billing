Restaurant Billing System

A Python-based billing and reporting system for restaurants.  
Supports **Dine-In & Takeaway orders**, automated **bill generation with GST/discounts**,  
and **reporting with exports**.  

Built using:
- **Python**
- **Streamlit / Tkinter** (for UI)
- **SQLite3** (database for menu, orders, items)
- **Pandas** (reporting & CSV exports)
- **fpdf / reportlab** (optional: PDF bills)


Features
**Menu Management** (Add/Edit menu items with GST %)  
**Order Management** (Dine-In / Takeaway, add/remove items, calculate totals)  
**Billing** (Itemized bill, subtotal + GST + discounts, multiple payment modes)  
**Data Storage** (All transactions stored in SQLite database)  
**Reports Module** (Daily/Weekly/Monthly sales, top-selling items)  
**Exports** (CSV, optional PDF bills)


##Project Structure
restaurant_billing/
│── init_db.py # Initialize database (menu, orders, order_items tables)
│── billing_app.py # Main application (UI + order management)
│── reports.py # Reports module (sales summary, exports)
│── restaurant_billing.db # SQLite database (auto-created)
│── requirements.txt # Dependencies
│── README.md # Documentation



## Installation

1. **Clone repo / download project**
   git clone https://github.com/yourname/restaurant-billing.git
   cd restaurant-billing
Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate   # On Mac/Linux
venv\Scripts\activate      # On Windows

Install dependencies
pip install -r requirements.txt

Usage

1. Initialize Database
python init_db.py

2. Run Application
If Streamlit version
streamlit run billing_app.py

If Tkinter version
python billing_app.py
3. Generate Reports
python reports.py

Reports
The system generates:
Daily Sales Summary
Weekly & Monthly Sales
Top Selling Items

Future Improvements
Role-based access (Admin vs Cashier)
Inventory management
Customer database & loyalty program
Dashboard with sales charts

License
MIT License – free to use and modify.

