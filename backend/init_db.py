import sqlite3
import os

# Connect to the correct database
DATABASE = os.path.join(os.path.dirname(__file__), "icecreams.db")

connection = sqlite3.connect(DATABASE)
cursor = connection.cursor()

# Create products table
cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    description TEXT,
    category TEXT
)
""")

# Add image_url column if it does not already exist
columns = [
    column[1]
    for column in cursor.execute("PRAGMA table_info(products)").fetchall()
]

if "image_url" not in columns:
    cursor.execute("ALTER TABLE products ADD COLUMN image_url TEXT")


# All products from Seasons 4 menu
# Bulk Packs are intentionally excluded.

products = [

    # CONES
    ("Blackcurrant Ripple", 30, "Blackcurrant ripple cone", "Cones"),
    ("Strawberry Ripple", 30, "Strawberry ripple cone", "Cones"),
    ("Chocolate Ripple", 35, "Chocolate ripple cone", "Cones"),
    ("Butterscotch", 40, "Butterscotch cone", "Cones"),
    ("Chocolate", 40, "Chocolate cone", "Cones"),
    ("Strawberry", 40, "Strawberry cone", "Cones"),
    ("Italian Bounty", 50, "Italian Bounty cone", "Cones"),
    ("Cookies N Cream", 50, "Cookies and cream cone", "Cones"),
    ("Nutty Caramel", 50, "Nutty caramel cone", "Cones"),
    ("Belgian Dark Chocolate", 50, "Belgian dark chocolate cone", "Cones"),
    ("Choco Brownie", 60, "Chocolate brownie cone", "Cones"),

    # CUPS
    ("Vanilla - 100 ml", 15, "Vanilla ice cream cup, 100 ml", "Cups"),
    ("Vanilla - 70 ml", 10, "Vanilla ice cream cup, 70 ml", "Cups"),
    ("Vanilla - 50 ml", 7, "Vanilla ice cream cup, 50 ml", "Cups"),

    ("Strawberry - 100 ml", 15, "Strawberry ice cream cup, 100 ml", "Cups"),
    ("Strawberry - 70 ml", 10, "Strawberry ice cream cup, 70 ml", "Cups"),
    ("Strawberry - 50 ml", 7, "Strawberry ice cream cup, 50 ml", "Cups"),

    ("Green Pista - 70 ml", 10, "Green pista ice cream cup, 70 ml", "Cups"),
    ("Green Pista - 50 ml", 7, "Green pista ice cream cup, 50 ml", "Cups"),

    ("Mango - 70 ml", 10, "Mango ice cream cup, 70 ml", "Cups"),
    ("Mango - 50 ml", 7, "Mango ice cream cup, 50 ml", "Cups"),

    ("Tutti Frutti - 70 ml", 10, "Tutti frutti ice cream cup, 70 ml", "Cups"),
    ("Tutti Frutti - 50 ml", 7, "Tutti frutti ice cream cup, 50 ml", "Cups"),

    ("Butterscotch - 100 ml", 20, "Butterscotch ice cream cup, 100 ml", "Cups"),
    ("Butterscotch - 50 ml", 10, "Butterscotch ice cream cup, 50 ml", "Cups"),

    ("Choco Nut - 100 ml", 20, "Choco nut ice cream cup, 100 ml", "Cups"),

    # SUNDAES - 170 ml
    ("Banana Berry", 40, "Banana berry sundae, 170 ml", "Sundaes"),
    ("Choco Vanilla", 40, "Choco vanilla sundae, 170 ml", "Sundaes"),
    ("Mango Ripple", 45, "Mango ripple sundae, 170 ml", "Sundaes"),
    ("Chocolate Ripple", 45, "Chocolate ripple sundae, 170 ml", "Sundaes"),
    ("Blackcurrant Ripple", 45, "Blackcurrant ripple sundae, 170 ml", "Sundaes"),
    ("Raspberry Ripple", 45, "Raspberry ripple sundae, 170 ml", "Sundaes"),
    ("Cake Fantasy", 50, "Cake fantasy sundae, 170 ml", "Sundaes"),
    ("American Dry Fruit", 60, "American dry fruit sundae, 170 ml", "Sundaes"),
    ("Arabian Delight", 60, "Arabian delight sundae, 170 ml", "Sundaes"),
    ("Kaju Kishmish", 60, "Kaju kishmish sundae, 170 ml", "Sundaes"),
    ("Honey Almond", 60, "Honey almond sundae, 170 ml", "Sundaes"),
    ("Caramel Crunch", 60, "Caramel crunch sundae, 170 ml", "Sundaes"),
    ("Belgian Dark Chocolate", 60, "Belgian dark chocolate sundae, 170 ml", "Sundaes"),
    ("Chappan Bhog", 60, "Chappan bhog sundae, 170 ml", "Sundaes"),
    ("Italian Bounty", 60, "Italian bounty sundae, 170 ml", "Sundaes"),

    # DOLLY
    ("Mango Dolly - 70 ml", 20, "Mango dolly ice cream, 70 ml", "Dolly"),
    ("Raspberry Dolly - 70 ml", 20, "Raspberry dolly ice cream, 70 ml", "Dolly"),

    # MILKEEZ
    ("Orange Milkeez - 70 ml", 15, "Orange milkeez, 70 ml", "Milkeez"),
    ("Blackcurrant Milkeez - 70 ml", 15, "Blackcurrant milkeez, 70 ml", "Milkeez"),
    ("Mango Milkeez - 70 ml", 15, "Mango milkeez, 70 ml", "Milkeez"),

    # KULFI
    ("Pista Kulfi - 60 ml", 40, "Pista kulfi, 60 ml", "Kulfi"),
    ("Mango Kulfi - 60 ml", 40, "Mango kulfi, 60 ml", "Kulfi"),

    # CANDIES
    ("Chocobar - 70 ml", 25, "Chocolate chocobar, 70 ml", "Candies"),
    ("Chocobar - 45 ml", 15, "Chocolate chocobar, 45 ml", "Candies"),
    ("Chocofest - 80 ml", 40, "Chocofest candy, 80 ml", "Candies"),
    ("Hoccofest - 80 ml", 45, "Hoccofest candy, 80 ml", "Candies"),
    ("Mango Juicy - 70 ml", 10, "Mango juicy candy, 70 ml", "Candies"),
    ("Orange Juicy - 70 ml", 10, "Orange juicy candy, 70 ml", "Candies"),
    ("Blackcurrant Juicy - 70 ml", 10, "Blackcurrant juicy candy, 70 ml", "Candies"),

    # NOVELTIES
    ("Vanilla Ball", 25, "Vanilla ball novelty", "Novelties"),
    ("Strawberry Fruit", 25, "Strawberry fruit novelty", "Novelties"),
    ("Mango Fruit", 30, "Mango fruit novelty", "Novelties"),
    ("Swinger", 40, "Swinger novelty", "Novelties"),
    ("Chowpaty Kulfi", 40, "Chowpaty kulfi novelty", "Novelties"),
    ("Premium Cassata", 50, "Premium cassata novelty", "Novelties"),
    ("Matka Kulfi", 60, "Matka kulfi novelty", "Novelties"),
    ("Black Forest", 70, "Black forest novelty", "Novelties"),
    ("Red Velvet", 70, "Red velvet novelty", "Novelties"),
    ("Choco Brownie", 70, "Choco brownie novelty", "Novelties"),

    # CARRY HOME TUBS - 1000 ml
    ("Vanilla - 1000 ml", 220, "Vanilla carry home tub, 1000 ml", "Carry Home Tubs"),
    ("Strawberry - 1000 ml", 220, "Strawberry carry home tub, 1000 ml", "Carry Home Tubs"),
    ("Green Pista - 1000 ml", 220, "Green pista carry home tub, 1000 ml", "Carry Home Tubs"),
    ("Mango - 1000 ml", 220, "Mango carry home tub, 1000 ml", "Carry Home Tubs"),
    ("Chocolate - 1000 ml", 230, "Chocolate carry home tub, 1000 ml", "Carry Home Tubs"),
    ("Cake Fantasy - 1000 ml", 250, "Cake fantasy carry home tub, 1000 ml", "Carry Home Tubs"),
    ("Tutti Frutti - 1000 ml", 260, "Tutti frutti carry home tub, 1000 ml", "Carry Home Tubs"),
    ("Choco Nut - 1000 ml", 280, "Choco nut carry home tub, 1000 ml", "Carry Home Tubs"),
    ("Butterscotch - 1000 ml", 280, "Butterscotch carry home tub, 1000 ml", "Carry Home Tubs"),
    ("Pista Nut - 1000 ml", 300, "Pista nut carry home tub, 1000 ml", "Carry Home Tubs"),
    ("Kaju Kishmish - 1000 ml", 300, "Kaju kishmish carry home tub, 1000 ml", "Carry Home Tubs"),

    # CARRY HOME TUBS - 600 ml
    ("Vanilla - 600 ml", 135, "Vanilla carry home tub, 600 ml", "Carry Home Tubs"),
    ("Strawberry - 600 ml", 135, "Strawberry carry home tub, 600 ml", "Carry Home Tubs"),
    ("Green Pista - 600 ml", 135, "Green pista carry home tub, 600 ml", "Carry Home Tubs"),
    ("Mango - 600 ml", 135, "Mango carry home tub, 600 ml", "Carry Home Tubs"),
    ("Chocolate - 600 ml", 140, "Chocolate carry home tub, 600 ml", "Carry Home Tubs"),
    ("Cake Fantasy - 600 ml", 160, "Cake fantasy carry home tub, 600 ml", "Carry Home Tubs"),
    ("Tutti Frutti - 600 ml", 145, "Tutti frutti carry home tub, 600 ml", "Carry Home Tubs"),
    ("Choco Nut - 600 ml", 190, "Choco nut carry home tub, 600 ml", "Carry Home Tubs"),
    ("Butterscotch - 600 ml", 160, "Butterscotch carry home tub, 600 ml", "Carry Home Tubs"),
    ("Pista Nut - 600 ml", 190, "Pista nut carry home tub, 600 ml", "Carry Home Tubs"),
    ("Kaju Kishmish - 600 ml", 190, "Kaju kishmish carry home tub, 600 ml", "Carry Home Tubs"),
    ("Chappan Bhog - 600 ml", 190, "Chappan bhog carry home tub, 600 ml", "Carry Home Tubs"),
    ("Honey Almond - 600 ml", 190, "Honey almond carry home tub, 600 ml", "Carry Home Tubs"),
    ("American Dry Fruit - 600 ml", 190, "American dry fruit carry home tub, 600 ml", "Carry Home Tubs"),
    ("Caramel Crunch - 600 ml", 190, "Caramel crunch carry home tub, 600 ml", "Carry Home Tubs"),
    ("Italian Bounty - 600 ml", 190, "Italian bounty carry home tub, 600 ml", "Carry Home Tubs"),
    ("Belgian Dark Chocolate - 600 ml", 190, "Belgian dark chocolate carry home tub, 600 ml", "Carry Home Tubs"),

    # BUY 1 GET 1 FREE - 700 ml
    ("Vanilla - B1G1 700 ml", 210, "Buy 1 Get 1 Free vanilla, 700 ml", "Buy 1 Get 1 Free"),
    ("Strawberry - B1G1 700 ml", 210, "Buy 1 Get 1 Free strawberry, 700 ml", "Buy 1 Get 1 Free"),
    ("Green Pista - B1G1 700 ml", 210, "Buy 1 Get 1 Free green pista, 700 ml", "Buy 1 Get 1 Free"),
    ("Mango - B1G1 700 ml", 210, "Buy 1 Get 1 Free mango, 700 ml", "Buy 1 Get 1 Free"),
    ("Tutti Frutti - B1G1 700 ml", 240, "Buy 1 Get 1 Free tutti frutti, 700 ml", "Buy 1 Get 1 Free"),
    ("Cake Fantasy - B1G1 700 ml", 250, "Buy 1 Get 1 Free cake fantasy, 700 ml", "Buy 1 Get 1 Free"),
    ("Chocolate - B1G1 700 ml", 250, "Buy 1 Get 1 Free chocolate, 700 ml", "Buy 1 Get 1 Free"),
    ("Butterscotch - B1G1 700 ml", 270, "Buy 1 Get 1 Free butterscotch, 700 ml", "Buy 1 Get 1 Free"),
    ("Black Current Nut - B1G1 700 ml", 270, "Buy 1 Get 1 Free black current nut, 700 ml", "Buy 1 Get 1 Free"),
    ("Choco Nut - B1G1 700 ml", 280, "Buy 1 Get 1 Free choco nut, 700 ml", "Buy 1 Get 1 Free"),
    ("Kaju Kishmish - B1G1 700 ml", 280, "Buy 1 Get 1 Free kaju kishmish, 700 ml", "Buy 1 Get 1 Free"),
    ("Pista Nut - B1G1 700 ml", 300, "Buy 1 Get 1 Free pista nut, 700 ml", "Buy 1 Get 1 Free"),
    ("Italian Bounty - B1G1 700 ml", 300, "Buy 1 Get 1 Free Italian bounty, 700 ml", "Buy 1 Get 1 Free"),
    ("Chappan Bhog - B1G1 700 ml", 300, "Buy 1 Get 1 Free chappan bhog, 700 ml", "Buy 1 Get 1 Free"),
    ("American Dry Fruit - B1G1 700 ml", 300, "Buy 1 Get 1 Free American dry fruit, 700 ml", "Buy 1 Get 1 Free"),
    ("Belgian Dark Chocolate - B1G1 700 ml", 300, "Buy 1 Get 1 Free Belgian dark chocolate, 700 ml", "Buy 1 Get 1 Free"),
    ("Caramel Crunch - B1G1 700 ml", 300, "Buy 1 Get 1 Free caramel crunch, 700 ml", "Buy 1 Get 1 Free"),
    ("Arabian Delight - B1G1 700 ml", 300, "Buy 1 Get 1 Free Arabian delight, 700 ml", "Buy 1 Get 1 Free")
]


# Insert products without creating duplicates
added_count = 0

for product in products:

    existing = cursor.execute("""
        SELECT id FROM products
        WHERE name = ? AND price = ? AND category = ?
    """, (product[0], product[1], product[3])).fetchone()

    if existing is None:
        cursor.execute("""
            INSERT INTO products (name, price, description, category)
            VALUES (?, ?, ?, ?)
        """, product)

        added_count += 1


connection.commit()

# Display total products
total = cursor.execute("SELECT COUNT(*) FROM products").fetchone()[0]

connection.close()

print("Seasons 4 database updated successfully!")
print("New products added:", added_count)
print("Total products in database:", total)