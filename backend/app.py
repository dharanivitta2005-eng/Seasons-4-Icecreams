from flask import Flask, jsonify, request, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import os

app = Flask(__name__)

# Development secret. Change this before deploying.
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(32)

CORS(
    app,
    origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    supports_credentials=True
)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False
)

DATABASE = os.path.join(
    os.path.dirname(__file__),
    "icecreams.db"
)


# DATABASE CONNECTION

def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


# CREATE DATABASE TABLES AND MIGRATE EXISTING TABLES

def initialize_database():

    connection = get_db_connection()

    # Products table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT,
            description TEXT,
            stock_quantity INTEGER NOT NULL DEFAULT 10
        )
    """)

    # Add inventory column to existing products tables.
    product_columns = [
        row["name"] for row in connection.execute(
            "PRAGMA table_info(products)"
        ).fetchall()
    ]
    if "stock_quantity" not in product_columns:
        connection.execute(
            "ALTER TABLE products ADD COLUMN stock_quantity INTEGER NOT NULL DEFAULT 10"
        )

    # Users table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'customer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Add role column to older databases.
    user_columns = [row["name"] for row in connection.execute(
        "PRAGMA table_info(users)"
    ).fetchall()]
    if "role" not in user_columns:
        connection.execute(
            "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'customer'"
        )

    # Orders table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_amount REAL NOT NULL,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'Placed',
            user_id INTEGER REFERENCES users(id)
        )
    """)

    # Add user_id to an existing orders table if necessary
    order_columns = [
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(orders)"
        ).fetchall()
    ]

    if "user_id" not in order_columns:
        connection.execute("""
            ALTER TABLE orders
            ADD COLUMN user_id INTEGER REFERENCES users(id)
        """)

    # Order items table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    """)

    # Create or migrate cart table
    cart_exists = connection.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='cart'
    """).fetchone()

    if cart_exists:

        cart_columns = connection.execute(
            "PRAGMA table_info(cart)"
        ).fetchall()

        column_names = [row["name"] for row in cart_columns]

        product_is_primary_key = any(
            row["name"] == "product_id" and row["pk"] == 1
            for row in cart_columns
        )

        if "user_id" not in column_names or product_is_primary_key:

            connection.execute(
                "ALTER TABLE cart RENAME TO cart_old"
            )

            connection.execute("""
                CREATE TABLE cart (
                    user_id INTEGER,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    PRIMARY KEY (user_id, product_id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            """)

            old_columns = [
                row["name"]
                for row in connection.execute(
                    "PRAGMA table_info(cart_old)"
                ).fetchall()
            ]

            if "product_id" in old_columns and "quantity" in old_columns:
                connection.execute("""
                    INSERT INTO cart (user_id, product_id, quantity)
                    SELECT NULL, product_id, quantity
                    FROM cart_old
                """)

            connection.execute("DROP TABLE cart_old")

    else:

        connection.execute("""
            CREATE TABLE cart (
                user_id INTEGER,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                PRIMARY KEY (user_id, product_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

    # Insert sample products only if the product table is empty
    count = connection.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    if count == 0:

        sample_products = [
            ("Chocolate Ice Cream", 50, "Cups", "Rich chocolate flavour"),
            ("Vanilla Ice Cream", 40, "Cups", "Classic vanilla flavour"),
            ("Strawberry Ice Cream", 60, "Cups", "Fresh strawberry flavour")
        ]

        connection.executemany("""
            INSERT INTO products (name, price, category, description)
            VALUES (?, ?, ?, ?)
        """, sample_products)

            # Create admin only when environment credentials are configured.
        admin_email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
        admin_password = os.environ.get("ADMIN_PASSWORD")
        admin_name = os.environ.get("ADMIN_NAME", "Seasons 4 Admin")

        if admin_email and admin_password:
            existing_admin = connection.execute(
                "SELECT id FROM users WHERE email = ?", (admin_email,)
            ).fetchone()

            if existing_admin is None:
                connection.execute(
                    "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, 'admin')",
                    (admin_name, admin_email, generate_password_hash(admin_password))
                )

    connection.commit()
    connection.close()


# LOGIN PROTECTION DECORATOR

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return jsonify({
                "error": "Please login first"
            }), 401

        return function(*args, **kwargs)

    return wrapper


def admin_required(function):
    @wraps(function)
    @login_required
    def wrapper(*args, **kwargs):
        connection = get_db_connection()
        user = connection.execute(
            "SELECT role FROM users WHERE id = ?", (session["user_id"],)
        ).fetchone()
        connection.close()
        if user is None or user["role"] != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return function(*args, **kwargs)
    return wrapper


# HOME API

@app.route("/")
def home():
    return "Welcome to Seasons 4 Ice Creams Backend!"


# REGISTER API

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({
            "error": "All fields are required"
        }), 400

    if len(password) < 8:
        return jsonify({
            "error": "Password must contain at least 8 characters"
        }), 400

    hashed_password = generate_password_hash(password)

    connection = get_db_connection()

    try:

        cursor = connection.execute("""
            INSERT INTO users (name, email, password)
            VALUES (?, ?, ?)
        """, (name, email, hashed_password))

        connection.commit()

        user_id = cursor.lastrowid

        # Automatically login after registration
        session.clear()
        session["user_id"] = user_id
        session["user_name"] = name

        return jsonify({
            "message": "Registration successful!",
            "user": {
                "id": user_id,
                "name": name,
                "email": email
            }
        }), 201

    except sqlite3.IntegrityError:

        return jsonify({
            "error": "This email is already registered"
        }), 409

    finally:
        connection.close()


# LOGIN API

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "error": "Email and password are required"
        }), 400

    connection = get_db_connection()

    user = connection.execute("""
        SELECT * FROM users WHERE email = ?
    """, (email,)).fetchone()

    connection.close()

    if user is None or not check_password_hash(
        user["password"], password
    ):

        return jsonify({
            "error": "Invalid email or password"
        }), 401

    session.clear()
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["role"] = user["role"]

    return jsonify({
        "message": "Login successful!",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    })


# CHECK CURRENT LOGIN

@app.route("/api/me", methods=["GET"])
@login_required
def current_user():

    connection = get_db_connection()

    user = connection.execute("""
        SELECT id, name, email
        FROM users
        WHERE id = ?
    """, (session["user_id"],)).fetchone()

    connection.close()

    if user is None:
        session.clear()
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "logged_in": True,
        "user": dict(user)
    })


# LOGOUT API

@app.route("/api/logout", methods=["POST"])
@login_required
def logout():

    session.clear()

    return jsonify({
        "message": "Logged out successfully!"
    })


# GET PRODUCTS API

@app.route("/api/products", methods=["GET"])
def get_products():

    connection = get_db_connection()

    products = connection.execute(
        "SELECT * FROM products"
    ).fetchall()

    connection.close()

    return jsonify([
        dict(product) for product in products
    ])


# ADD TO CART API

@app.route("/api/cart", methods=["POST"])
@login_required
def add_to_cart():

    data = request.get_json(silent=True) or {}

    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    if not isinstance(product_id, int) or isinstance(product_id, bool):
        return jsonify({"error": "Valid product ID is required"}), 400

    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
        return jsonify({"error": "Quantity must be positive"}), 400

    user_id = session["user_id"]

    connection = get_db_connection()

    product = connection.execute(
        "SELECT id, stock_quantity FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    if product is None:
        connection.close()
        return jsonify({"error": "Product not found"}), 404

    existing = connection.execute(
        "SELECT quantity FROM cart WHERE user_id = ? AND product_id = ?",
        (user_id, product_id)
    ).fetchone()
    already_in_cart = existing["quantity"] if existing else 0

    if already_in_cart + quantity > product["stock_quantity"]:
        connection.close()
        return jsonify({
            "error": f"Only {product['stock_quantity']} units are currently available."
        }), 409

    connection.execute("""
        INSERT INTO cart (user_id, product_id, quantity)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, product_id)
        DO UPDATE SET quantity = quantity + excluded.quantity
    """, (user_id, product_id, quantity))

    connection.commit()
    connection.close()

    return jsonify({
        "message": "Product added to cart!"
    }), 201


# VIEW CART API

@app.route("/api/cart", methods=["GET"])
@login_required
def get_cart():

    connection = get_db_connection()

    cart_items = connection.execute("""
        SELECT
            cart.product_id,
            products.name,
            products.price,
            cart.quantity,
            products.price * cart.quantity AS subtotal
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.user_id = ?
    """, (session["user_id"],)).fetchall()

    total = sum(item["subtotal"] for item in cart_items)

    connection.close()

    return jsonify({
        "items": [dict(item) for item in cart_items],
        "total": total
    })


# UPDATE CART QUANTITY API

@app.route("/api/cart/<int:product_id>", methods=["PUT"])
@login_required
def update_cart_quantity(product_id):

    data = request.get_json(silent=True) or {}

    quantity = data.get("quantity")

    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
        return jsonify({"error": "Quantity must be at least 1"}), 400

    connection = get_db_connection()

    product = connection.execute(
        "SELECT stock_quantity FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    if product is None:
        connection.close()
        return jsonify({"error": "Product not found"}), 404
    if quantity > product["stock_quantity"]:
        connection.close()
        return jsonify({
            "error": f"Only {product['stock_quantity']} units are currently available."
        }), 409

    cursor = connection.execute("""
        UPDATE cart
        SET quantity = ?
        WHERE product_id = ? AND user_id = ?
    """, (quantity, product_id, session["user_id"]))

    connection.commit()
    connection.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Cart item not found"}), 404

    return jsonify({
        "message": "Quantity updated successfully!"
    })


# REMOVE FROM CART API

@app.route("/api/cart/<int:product_id>", methods=["DELETE"])
@login_required
def remove_from_cart(product_id):

    connection = get_db_connection()

    cursor = connection.execute("""
        DELETE FROM cart
        WHERE product_id = ? AND user_id = ?
    """, (product_id, session["user_id"]))

    connection.commit()
    connection.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Cart item not found"}), 404

    return jsonify({
        "message": "Product removed from cart!"
    })


# PLACE ORDER API

@app.route("/api/orders", methods=["POST"])
@login_required
def place_order():

    connection = get_db_connection()

    try:

        user_id = session["user_id"]

        cart_items = connection.execute("""
            SELECT
                cart.product_id,
                products.name,
                products.price,
                cart.quantity,
                products.price * cart.quantity AS subtotal
            FROM cart
            JOIN products ON cart.product_id = products.id
            WHERE cart.user_id = ?
        """, (user_id,)).fetchall()

        if not cart_items:
            return jsonify({
                "error": "Your cart is empty!"
            }), 400

        # Validate all cart quantities against current stock before creating the order.
        for item in cart_items:
            stock_row = connection.execute(
                "SELECT stock_quantity FROM products WHERE id = ?",
                (item["product_id"],)
            ).fetchone()
            if stock_row is None or item["quantity"] > stock_row["stock_quantity"]:
                available = stock_row["stock_quantity"] if stock_row else 0
                return jsonify({
                    "error": f"Not enough stock for {item['name']}. Available: {available}"
                }), 409

        total = sum(item["subtotal"] for item in cart_items)

        cursor = connection.execute("""
            INSERT INTO orders (total_amount, user_id)
            VALUES (?, ?)
        """, (total, user_id))

        order_id = cursor.lastrowid

        for item in cart_items:

            connection.execute("""
                INSERT INTO order_items (
                    order_id,
                    product_id,
                    product_name,
                    price,
                    quantity,
                    subtotal
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                order_id,
                item["product_id"],
                item["name"],
                item["price"],
                item["quantity"],
                item["subtotal"]
            ))

            connection.execute(
                "UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?",
                (item["quantity"], item["product_id"])
            )

        connection.execute("""
            DELETE FROM cart WHERE user_id = ?
        """, (user_id,))

        connection.commit()

        return jsonify({
            "message": "Order placed successfully!",
            "order_id": order_id,
            "total_amount": total,
            "status": "Placed"
        }), 201

    except Exception as error:

        connection.rollback()

        return jsonify({
            "error": str(error)
        }), 500

    finally:
        connection.close()


# GET ORDER HISTORY API

@app.route("/api/orders", methods=["GET"])
@login_required
def get_orders():

    connection = get_db_connection()

    orders = connection.execute("""
        SELECT *
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
    """, (session["user_id"],)).fetchall()

    result = []

    for order in orders:

        items = connection.execute("""
            SELECT *
            FROM order_items
            WHERE order_id = ?
        """, (order["id"],)).fetchall()

        result.append({
            "id": order["id"],
            "total_amount": order["total_amount"],
            "order_date": order["order_date"],
            "status": order["status"],
            "items": [dict(item) for item in items]
        })

    connection.close()

    return jsonify(result)




# ======================== ADMIN DASHBOARD APIs ========================

@app.route("/api/admin/dashboard", methods=["GET"])
@admin_required
def admin_dashboard():
    connection = get_db_connection()
    stats = {
        "total_products": connection.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        "total_customers": connection.execute("SELECT COUNT(*) FROM users WHERE role = 'customer'").fetchone()[0],
        "total_orders": connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        "total_revenue": connection.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders").fetchone()[0]
    }
    recent = connection.execute("""
        SELECT orders.id, orders.total_amount, orders.order_date, orders.status,
               users.name AS customer_name, users.email
        FROM orders LEFT JOIN users ON orders.user_id = users.id
        ORDER BY orders.id DESC LIMIT 5
    """).fetchall()
    connection.close()
    return jsonify({"stats": stats, "recent_orders": [dict(row) for row in recent]})


@app.route("/api/admin/products", methods=["GET"])
@admin_required
def admin_get_products():
    connection = get_db_connection()
    rows = connection.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    connection.close()
    return jsonify([dict(row) for row in rows])


@app.route("/api/admin/products", methods=["POST"])
@admin_required
def admin_add_product():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    category = str(data.get("category", "")).strip()
    description = str(data.get("description", "")).strip()
    try:
        stock_quantity = int(data.get("stock_quantity", 10))
        if stock_quantity < 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Stock quantity must be zero or greater"}), 400
    try:
        price = float(data.get("price"))
    except (TypeError, ValueError):
        return jsonify({"error": "Enter a valid product price"}), 400
    if not name or not category or price <= 0:
        return jsonify({"error": "Name, category and positive price are required"}), 400
    connection = get_db_connection()
    cursor = connection.execute(
        "INSERT INTO products (name, price, category, description, stock_quantity) VALUES (?, ?, ?, ?, ?)",
        (name, price, category, description, stock_quantity)
    )
    connection.commit()
    product_id = cursor.lastrowid
    connection.close()
    return jsonify({"message": "Product added", "product_id": product_id}), 201


@app.route("/api/admin/products/<int:product_id>", methods=["PUT"])
@admin_required
def admin_update_product(product_id):
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    category = str(data.get("category", "")).strip()
    description = str(data.get("description", "")).strip()
    try:
        stock_quantity = int(data.get("stock_quantity", 10))
        if stock_quantity < 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Stock quantity must be zero or greater"}), 400
    try:
        price = float(data.get("price"))
    except (TypeError, ValueError):
        return jsonify({"error": "Enter a valid product price"}), 400
    if not name or not category or price <= 0:
        return jsonify({"error": "Name, category and positive price are required"}), 400
    connection = get_db_connection()
    cursor = connection.execute("""
        UPDATE products
        SET name = ?, price = ?, category = ?, description = ?, stock_quantity = ?
        WHERE id = ?
    """, (name, price, category, description, stock_quantity, product_id))
    connection.commit()
    connection.close()
    if cursor.rowcount == 0:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"message": "Product updated successfully"})


@app.route("/api/admin/products/<int:product_id>", methods=["DELETE"])
@admin_required
def admin_delete_product(product_id):
    connection = get_db_connection()
    exists = connection.execute(
        "SELECT id FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    if exists is None:
        connection.close()
        return jsonify({"error": "Product not found"}), 404
    ordered = connection.execute(
        "SELECT 1 FROM order_items WHERE product_id = ? LIMIT 1", (product_id,)
    ).fetchone()
    if ordered:
        connection.close()
        return jsonify({"error": "Product belongs to an order; edit it instead of deleting."}), 409
    connection.execute("DELETE FROM cart WHERE product_id = ?", (product_id,))
    connection.execute("DELETE FROM products WHERE id = ?", (product_id,))
    connection.commit()
    connection.close()
    return jsonify({"message": "Product deleted successfully"})


@app.route("/api/admin/products/<int:product_id>/stock", methods=["PUT"])
@admin_required
def admin_update_stock(product_id):
    data = request.get_json(silent=True) or {}
    try:
        quantity = int(data.get("stock_quantity"))
        if quantity < 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Enter a stock quantity of zero or greater"}), 400

    connection = get_db_connection()
    cursor = connection.execute(
        "UPDATE products SET stock_quantity = ? WHERE id = ?",
        (quantity, product_id)
    )
    connection.commit()
    connection.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Product not found"}), 404

    return jsonify({
        "message": "Stock updated successfully",
        "stock_quantity": quantity,
        "availability": "In Stock" if quantity > 0 else "Out of Stock"
    })


@app.route("/api/admin/orders", methods=["GET"])
@admin_required
def admin_get_orders():
    connection = get_db_connection()
    orders = connection.execute("""
        SELECT orders.id, orders.total_amount, orders.order_date, orders.status,
               orders.user_id, users.name AS customer_name, users.email
        FROM orders LEFT JOIN users ON orders.user_id = users.id
        ORDER BY orders.id DESC
    """).fetchall()
    result = []
    for order in orders:
        item_rows = connection.execute("""
            SELECT product_name, price, quantity, subtotal
            FROM order_items WHERE order_id = ?
        """, (order["id"],)).fetchall()
        item = dict(order)
        item["items"] = [dict(row) for row in item_rows]
        result.append(item)
    connection.close()
    return jsonify(result)


@app.route("/api/admin/orders/<int:order_id>/status", methods=["PUT"])
@admin_required
def admin_update_order_status(order_id):
    data = request.get_json(silent=True) or {}
    status = str(data.get("status", "")).strip()
    allowed = {"Placed", "Processing", "Dispatched", "Delivered", "Cancelled"}
    if status not in allowed:
        return jsonify({"error": "Invalid order status"}), 400
    connection = get_db_connection()
    cursor = connection.execute(
        "UPDATE orders SET status = ? WHERE id = ?", (status, order_id)
    )
    connection.commit()
    connection.close()
    if cursor.rowcount == 0:
        return jsonify({"error": "Order not found"}), 404
    return jsonify({"message": "Order status updated", "status": status})


@app.route("/api/admin/customers", methods=["GET"])
@admin_required
def admin_get_customers():
    connection = get_db_connection()
    rows = connection.execute("""
        SELECT users.id, users.name, users.email, users.created_at,
               COUNT(orders.id) AS order_count,
               COALESCE(SUM(orders.total_amount), 0) AS total_spent
        FROM users LEFT JOIN orders ON orders.user_id = users.id
        WHERE users.role = 'customer'
        GROUP BY users.id ORDER BY users.id DESC
    """).fetchall()
    connection.close()
    return jsonify([dict(row) for row in rows])


# START SERVER

if __name__ == "__main__":

    initialize_database()

    print("Database initialized successfully!")

    app.run(debug=True)