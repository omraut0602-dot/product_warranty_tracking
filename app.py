import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
from dateutil.relativedelta import relativedelta

app = Flask(__name__)
app.secret_key = "warranty_secret_key"

def init_db():
    conn = sqlite3.connect("warranty.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            brand TEXT NOT NULL,
            purchase_date TEXT NOT NULL,
            warranty_period INTEGER NOT NULL
        )
    """)

    conn.commit()
    conn.close()

@app.route("/view-products")
def view_products():
    if not session.get("logged_in"):
        return redirect("/login")
    conn = sqlite3.connect("warranty.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()

    conn.close()

    products = []

    today = datetime.today().date()

    for row in rows:
        product = dict(row)

        purchase_date = datetime.strptime(
            product["purchase_date"], "%Y-%m-%d"
        ).date()

        expiry_date = purchase_date + relativedelta(
            months=product["warranty_period"]
        )

        if expiry_date >= today:
            status = "Active"
        else:
            status = "Expired"

        product["expiry_date"] = expiry_date.strftime("%Y-%m-%d")
        product["status"] = status

        products.append(product)

    return render_template("view_products.html", products=products)

@app.route("/delete-product/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    if not session.get("logged_in"):
        return redirect("/login")
    conn = sqlite3.connect("warranty.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM products WHERE id = ?",
        (product_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("view_products"))    

@app.route("/track-warranty")
def track_warranty():
    if not session.get("logged_in"):
        return redirect("/login")
    conn = sqlite3.connect("warranty.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    conn.close()

    warranty_data = []

    today = datetime.today().date()

    for product in products:
        purchase_date = datetime.strptime(
            product["purchase_date"], "%Y-%m-%d"
        ).date()

        warranty_months = int(product["warranty_period"])

        expiry_date = purchase_date + relativedelta(
            months=warranty_months
        )

        days_left = (expiry_date - today).days

        if days_left < 0:
            status = "Expired"
        elif days_left <= 30:
            status = "Expiring Soon"
        else:
            status = "Active"

        warranty_data.append({
            "product_name": product["product_name"],
            "brand": product["brand"],
            "purchase_date": product["purchase_date"],
            "warranty_period": warranty_months,
            "expiry_date": expiry_date.strftime("%Y-%m-%d"),
            "days_left": days_left,
            "status": status
        })

    return render_template(
        "track_warranty.html",
        products=warranty_data
    )
@app.route("/edit-product/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):

    if not session.get("logged_in"):
        return redirect("/login")

    conn = sqlite3.connect("warranty.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == "POST":

        product_name = request.form["product_name"]
        brand = request.form["brand"]
        purchase_date = request.form["purchase_date"]
        warranty_period = request.form["warranty_period"]

        cursor.execute("""
            UPDATE products
            SET product_name = ?,
                brand = ?,
                purchase_date = ?,
                warranty_period = ?
            WHERE id = ?
        """, (
            product_name,
            brand,
            purchase_date,
            warranty_period,
            product_id
        ))

        conn.commit()
        conn.close()

        return redirect("/view-products")

    cursor.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    )

    product = cursor.fetchone()

    conn.close()

    return render_template(
        "edit_product.html",
        product=product
    )    

@app.route("/")
def home():
    conn = sqlite3.connect("warranty.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]

    active_warranties = 0
    expired_warranties = 0

    cursor.execute("SELECT purchase_date, warranty_period FROM products")
    products = cursor.fetchall()

    today = datetime.today()

    for purchase_date, warranty_period in products:
        purchase = datetime.strptime(purchase_date, "%Y-%m-%d")
        expiry = purchase + relativedelta(months=warranty_period)

        if expiry >= today:
            active_warranties += 1
        else:
            expired_warranties += 1

    conn.close()

    return render_template(
        "index.html",
        total_products=total_products,
        active_warranties=active_warranties,
        expired_warranties=expired_warranties
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "1234":
            session["logged_in"] = True
            return redirect("/")

        else:
            return render_template(
                "login.html",
                error="Invalid username or password"
            )

    return render_template("login.html")
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/add-product", methods=["GET", "POST"])
def add_product():
    if not session.get("logged_in"):
        return redirect("/login")
    if request.method == "POST":
        product_name = request.form["product_name"]
        brand = request.form["brand"]
        purchase_date = request.form["purchase_date"]
        warranty_period = request.form["warranty_period"]

        conn = sqlite3.connect("warranty.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO products
            (product_name, brand, purchase_date, warranty_period)
            VALUES (?, ?, ?, ?)
        """, (product_name, brand, purchase_date, warranty_period))

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("add_product.html")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)