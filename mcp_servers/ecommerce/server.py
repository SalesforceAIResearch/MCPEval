import os
import json
import sqlite3
import logging
from typing import Dict, Any, Optional, Literal

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize the MCP server
mcp = FastMCP("E-Commerce")

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------------------------------------------------------------------------
# Schema creation & seed data  (runs once on module load)
# ---------------------------------------------------------------------------
def _init_db() -> None:
    conn = _get_conn()
    cur = conn.cursor()

    # ---- tables ----------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            parent_category_id INTEGER REFERENCES categories(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            sku TEXT UNIQUE NOT NULL,
            category_id INTEGER REFERENCES categories(id),
            price REAL NOT NULL,
            stock_quantity INTEGER NOT NULL DEFAULT 0,
            description TEXT,
            weight_kg REAL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            tier TEXT DEFAULT 'standard',
            registration_date TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER REFERENCES customers(id),
            order_date TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            total_amount REAL NOT NULL,
            shipping_address TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY,
            order_id INTEGER REFERENCES orders(id),
            product_id INTEGER REFERENCES products(id),
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL
        )
    """)

    # ---- seed: categories ------------------------------------------------
    categories = [
        (1, "Electronics", None),
        (2, "Laptops", 1),
        (3, "Phones", 1),
        (4, "Accessories", 1),
        (5, "Office", None),
        (6, "Furniture", 5),
        (7, "Supplies", 5),
        (8, "Kitchen", None),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO categories (id, name, parent_category_id) VALUES (?, ?, ?)",
        categories,
    )

    # ---- seed: products --------------------------------------------------
    products = [
        # Laptops (cat 2)
        (1, "ProBook 15 Laptop", "LAP-001", 2, 1299.99, 25, "15.6-inch business laptop with Intel i7, 16 GB RAM, 512 GB SSD", 2.1),
        (2, "UltraSlim 13 Laptop", "LAP-002", 2, 999.99, 18, "13.3-inch ultraportable, AMD Ryzen 7, 16 GB RAM, 256 GB SSD", 1.2),
        (3, "GameMaster X1 Laptop", "LAP-003", 2, 1899.99, 7, "17.3-inch gaming laptop, RTX 4070, 32 GB RAM, 1 TB SSD", 3.0),
        (4, "BudgetNote 14 Laptop", "LAP-004", 2, 449.99, 40, "14-inch everyday laptop, Intel i5, 8 GB RAM, 256 GB SSD", 1.6),
        # Phones (cat 3)
        (5, "Galaxy Pro Max Phone", "PHN-001", 3, 1199.99, 35, "6.7-inch AMOLED, 256 GB, 50 MP triple camera", 0.23),
        (6, "Pixel Ultra Phone", "PHN-002", 3, 899.99, 22, "6.4-inch OLED, 128 GB, Google Tensor chip, 48 MP camera", 0.20),
        (7, "BudgetCall 5G Phone", "PHN-003", 3, 299.99, 60, "6.5-inch LCD, 64 GB, 5G capable, 12 MP dual camera", 0.19),
        (8, "FoldFlex Phone", "PHN-004", 3, 1799.99, 5, "7.6-inch foldable AMOLED, 512 GB, 50 MP camera", 0.27),
        # Accessories (cat 4)
        (9, "Wireless Noise-Cancelling Headphones", "ACC-001", 4, 249.99, 45, "Over-ear ANC headphones, 30 hr battery, Bluetooth 5.3", 0.25),
        (10, "USB-C Charging Hub 7-in-1", "ACC-002", 4, 59.99, 80, "7-port USB-C hub with HDMI, SD card, USB-A and PD charging", 0.12),
        (11, "Wireless Mouse Pro", "ACC-003", 4, 39.99, 100, "Ergonomic wireless mouse, 4000 DPI, USB-C rechargeable", 0.08),
        (12, "Laptop Stand Aluminum", "ACC-004", 4, 49.99, 55, "Adjustable aluminum laptop stand, fits up to 17-inch laptops", 0.95),
        (13, "Mechanical Keyboard RGB", "ACC-005", 4, 129.99, 30, "Full-size mechanical keyboard, Cherry MX switches, RGB backlight", 0.85),
        (14, "Phone Screen Protector Pack", "ACC-006", 4, 12.99, 200, "Tempered glass screen protector, 3-pack, universal fit", 0.05),
        # Furniture (cat 6)
        (15, "ErgoChair Pro Office Chair", "FUR-001", 6, 549.99, 12, "Ergonomic mesh office chair, lumbar support, adjustable armrests", 15.0),
        (16, "Standing Desk Electric", "FUR-002", 6, 699.99, 8, "Electric sit-stand desk, 60x30 inches, memory presets", 35.0),
        (17, "Bookshelf 5-Tier", "FUR-003", 6, 129.99, 20, "5-tier wooden bookshelf, 72 inches tall, walnut finish", 18.0),
        (18, "Filing Cabinet 3-Drawer", "FUR-004", 6, 189.99, 3, "Metal 3-drawer filing cabinet, lockable, black", 22.0),
        # Supplies (cat 7)
        (19, "Premium Copy Paper 5000 Sheets", "SUP-001", 7, 42.99, 150, "Letter size 8.5x11, 20 lb, 10 reams of 500 sheets", 23.0),
        (20, "Gel Pen Set 24-Pack", "SUP-002", 7, 18.99, 85, "Assorted color gel pens, 0.7 mm tip, smooth ink flow", 0.35),
        (21, "Sticky Notes Mega Pack", "SUP-003", 7, 14.99, 0, "3x3 inch sticky notes, 24 pads, assorted colors", 0.60),
        (22, "Binder Clips Assorted 120-Pack", "SUP-004", 7, 9.99, 110, "Assorted sizes binder clips, black, 120 count", 0.45),
        # Kitchen (cat 8)
        (23, "Smart Coffee Maker", "KIT-001", 8, 179.99, 15, "WiFi-enabled drip coffee maker, 12-cup, programmable, app control", 3.5),
        (24, "Chef Knife Set 8-Piece", "KIT-002", 8, 89.99, 25, "Stainless steel knife set with wooden block, 8 pieces", 2.8),
        (25, "Air Fryer XL 5.8 Qt", "KIT-003", 8, 119.99, 9, "Digital air fryer, 5.8 qt capacity, 8 presets, dishwasher-safe basket", 5.2),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO products (id, name, sku, category_id, price, stock_quantity, description, weight_kg) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        products,
    )

    # ---- seed: customers -------------------------------------------------
    customers = [
        (1, "Alice Johnson", "alice.johnson@email.com", "vip", "2022-01-15"),
        (2, "Bob Smith", "bob.smith@email.com", "premium", "2022-06-20"),
        (3, "Carol Davis", "carol.davis@email.com", "standard", "2023-03-10"),
        (4, "David Lee", "david.lee@email.com", "premium", "2022-11-05"),
        (5, "Emma Wilson", "emma.wilson@email.com", "standard", "2023-07-22"),
        (6, "Frank Martinez", "frank.martinez@email.com", "vip", "2021-09-01"),
        (7, "Grace Kim", "grace.kim@email.com", "standard", "2024-01-14"),
        (8, "Henry Brown", "henry.brown@email.com", "premium", "2023-05-30"),
        (9, "Isabel Chen", "isabel.chen@email.com", "standard", "2024-03-18"),
        (10, "James Taylor", "james.taylor@email.com", "vip", "2021-12-25"),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO customers (id, name, email, tier, registration_date) VALUES (?, ?, ?, ?, ?)",
        customers,
    )

    # ---- seed: orders ----------------------------------------------------
    orders = [
        (1, 1, "2024-11-01", "delivered", 1349.98, "123 Maple St, Springfield, IL 62701"),
        (2, 1, "2024-12-15", "delivered", 249.99, "123 Maple St, Springfield, IL 62701"),
        (3, 2, "2025-01-10", "shipped", 1059.98, "456 Oak Ave, Portland, OR 97201"),
        (4, 3, "2025-01-20", "processing", 539.97, "789 Pine Rd, Austin, TX 78701"),
        (5, 4, "2025-02-01", "delivered", 1899.99, "321 Elm Blvd, Denver, CO 80201"),
        (6, 5, "2025-02-10", "shipped", 89.97, "654 Cedar Ln, Seattle, WA 98101"),
        (7, 6, "2025-02-15", "delivered", 2499.97, "987 Birch Dr, Miami, FL 33101"),
        (8, 6, "2025-02-28", "pending", 179.99, "987 Birch Dr, Miami, FL 33101"),
        (9, 7, "2025-03-01", "processing", 329.98, "147 Walnut St, Boston, MA 02101"),
        (10, 8, "2025-03-05", "cancelled", 449.99, "258 Spruce Ave, Chicago, IL 60601"),
        (11, 2, "2025-03-10", "pending", 1199.99, "456 Oak Ave, Portland, OR 97201"),
        (12, 9, "2025-03-12", "shipped", 162.98, "369 Ash Ct, San Francisco, CA 94101"),
        (13, 10, "2025-03-15", "processing", 749.98, "741 Poplar Way, Nashville, TN 37201"),
        (14, 4, "2025-03-18", "pending", 59.99, "321 Elm Blvd, Denver, CO 80201"),
        (15, 1, "2025-03-20", "pending", 299.98, "123 Maple St, Springfield, IL 62701"),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO orders (id, customer_id, order_date, status, total_amount, shipping_address) VALUES (?, ?, ?, ?, ?, ?)",
        orders,
    )

    # ---- seed: order_items -----------------------------------------------
    order_items = [
        # Order 1  (Alice) - ProBook Laptop + USB-C Hub
        (1, 1, 1, 1, 1299.99),
        (2, 1, 10, 1, 59.99),
        # Order 2  (Alice) - Wireless Headphones
        (3, 2, 9, 1, 249.99),
        # Order 3  (Bob) - UltraSlim Laptop + USB-C Hub
        (4, 3, 2, 1, 999.99),
        (5, 3, 10, 1, 59.99),
        # Order 4  (Carol) - ErgoChair + Gel Pens + Sticky Notes
        (6, 4, 15, 1, 549.99),
        (7, 4, 20, 1, 18.99),
        # Order 5  (David) - GameMaster Laptop
        (8, 5, 3, 1, 1899.99),
        # Order 6  (Emma) - Chef Knife Set + Gel Pens + Binder Clips
        (9, 6, 24, 1, 89.99),
        (10, 6, 20, 1, 18.99),
        (11, 6, 22, 1, 9.99),
        # Order 7  (Frank) - Galaxy Pro Max + FoldFlex
        (12, 7, 5, 1, 1199.99),
        (13, 7, 8, 1, 1799.99),
        # Order 8  (Frank) - Smart Coffee Maker
        (14, 8, 23, 1, 179.99),
        # Order 9  (Grace) - BudgetCall Phone + Wireless Mouse
        (15, 9, 7, 1, 299.99),
        (16, 9, 11, 1, 39.99),
        # Order 10 (Henry) - BudgetNote Laptop  (cancelled)
        (17, 10, 4, 1, 449.99),
        # Order 11 (Bob) - Galaxy Pro Max Phone
        (18, 11, 5, 1, 1199.99),
        # Order 12 (Isabel) - Mechanical Keyboard + Laptop Stand + Screen Protector
        (19, 12, 13, 1, 129.99),
        (20, 12, 12, 1, 49.99),
        (21, 12, 14, 1, 12.99),
        # Order 13 (James) - Standing Desk + Laptop Stand
        (22, 13, 16, 1, 699.99),
        (23, 13, 12, 1, 49.99),
        # Order 14 (David) - USB-C Hub
        (24, 14, 10, 1, 59.99),
        # Order 15 (Alice) - BudgetCall Phone + Screen Protector
        (25, 15, 7, 1, 299.99),
        (26, 15, 14, 1, 12.99),
        # Additional items to bring total above 30
        (27, 4, 14, 2, 12.99),      # Carol order 4 - 2x screen protectors
        (28, 7, 9, 1, 249.99),       # Frank order 7 - headphones (total adjusted)
        (29, 9, 14, 3, 12.99),       # Grace order 9 - 3x screen protectors
        (30, 13, 11, 2, 39.99),      # James order 13 - 2x wireless mouse
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?, ?)",
        order_items,
    )

    conn.commit()
    conn.close()
    logger.info("E-Commerce database initialised at %s", DB_PATH)


# Run initialisation on module load
_init_db()

# ---------------------------------------------------------------------------
# Status-transition validation helper
# ---------------------------------------------------------------------------
_STATUS_ORDER = {
    "pending": 0,
    "processing": 1,
    "shipped": 2,
    "delivered": 3,
    "cancelled": 4,
}


def _valid_status_transition(current: str, new: str) -> bool:
    """Return True if transitioning from *current* to *new* is allowed.

    Rules:
    - Cannot move backwards in the normal flow (pending -> processing -> shipped -> delivered).
    - 'cancelled' can be reached from pending or processing only.
    - Once delivered or cancelled, no further changes are allowed.
    """
    if current == new:
        return False
    if current in ("delivered", "cancelled"):
        return False
    if new == "cancelled":
        return current in ("pending", "processing")
    return _STATUS_ORDER.get(new, -1) > _STATUS_ORDER.get(current, -1)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def search_products(
    query: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Search and filter products in the catalogue.

    Args:
        query: Free-text search term matched against product name and description.
        category: Category name to filter by (case-insensitive).
        min_price: Minimum price filter (inclusive).
        max_price: Maximum price filter (inclusive).
        in_stock: If true, return only products with stock_quantity > 0.
    """
    try:
        conn = _get_conn()
        clauses = []
        params = []

        if query:
            clauses.append("(p.name LIKE ? OR p.description LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])
        if category:
            clauses.append("LOWER(c.name) = LOWER(?)")
            params.append(category)
        if min_price is not None:
            clauses.append("p.price >= ?")
            params.append(min_price)
        if max_price is not None:
            clauses.append("p.price <= ?")
            params.append(max_price)
        if in_stock is True:
            clauses.append("p.stock_quantity > 0")
        elif in_stock is False:
            clauses.append("p.stock_quantity = 0")

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        sql = f"""
            SELECT p.id, p.name, p.sku, c.name AS category, p.price,
                   p.stock_quantity, p.description, p.weight_kg
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            {where}
            ORDER BY p.id
        """
        rows = conn.execute(sql, params).fetchall()
        conn.close()

        products = [dict(r) for r in rows]
        return {
            "status": "success",
            "total_results": len(products),
            "products": products,
        }
    except Exception as e:
        logger.error("search_products error: %s", e)
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def get_product_details(product_id: int) -> Dict[str, Any]:
    """
    Get full details for a single product including its category name.

    Args:
        product_id: The ID of the product to retrieve.
    """
    try:
        conn = _get_conn()
        row = conn.execute(
            """
            SELECT p.id, p.name, p.sku, c.name AS category, p.price,
                   p.stock_quantity, p.description, p.weight_kg
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = ?
            """,
            (product_id,),
        ).fetchone()
        conn.close()

        if not row:
            return {"status": "error", "error_message": f"Product with id {product_id} not found"}

        return {"status": "success", "product": dict(row)}
    except Exception as e:
        logger.error("get_product_details error: %s", e)
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def check_inventory(product_id: int) -> Dict[str, Any]:
    """
    Check stock level for a product and flag low-stock warnings.

    Args:
        product_id: The ID of the product to check.
    """
    try:
        conn = _get_conn()
        row = conn.execute(
            "SELECT id, name, sku, stock_quantity FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        conn.close()

        if not row:
            return {"status": "error", "error_message": f"Product with id {product_id} not found"}

        product = dict(row)
        qty = product["stock_quantity"]
        product["in_stock"] = qty > 0
        product["low_stock_warning"] = qty < 10
        if qty == 0:
            product["stock_status"] = "out_of_stock"
        elif qty < 10:
            product["stock_status"] = "low_stock"
        else:
            product["stock_status"] = "in_stock"

        return {"status": "success", "inventory": product}
    except Exception as e:
        logger.error("check_inventory error: %s", e)
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def list_categories(parent_category_id: Optional[int] = None) -> Dict[str, Any]:
    """
    List product categories, optionally filtered by parent category.

    Args:
        parent_category_id: If provided, return only direct children of this category.
    """
    try:
        conn = _get_conn()
        if parent_category_id is not None:
            rows = conn.execute(
                "SELECT id, name, parent_category_id FROM categories WHERE parent_category_id = ? ORDER BY id",
                (parent_category_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, name, parent_category_id FROM categories ORDER BY id"
            ).fetchall()
        conn.close()

        return {
            "status": "success",
            "total_results": len(rows),
            "categories": [dict(r) for r in rows],
        }
    except Exception as e:
        logger.error("list_categories error: %s", e)
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def create_order(
    customer_email: str,
    items: str,
    shipping_address: str,
) -> Dict[str, Any]:
    """
    Create a new order for a customer.

    The function validates that the customer exists, that each product exists and
    has sufficient stock, calculates the total from product prices, inserts the
    order and its line items, and decrements stock quantities.

    Args:
        customer_email: Email address of the customer placing the order.
        items: JSON string describing line items, e.g. '[{"product_id": 1, "quantity": 2}]'.
        shipping_address: Full shipping address for the order.
    """
    try:
        # Parse items
        try:
            item_list = json.loads(items)
        except json.JSONDecodeError as je:
            return {"status": "error", "error_message": f"Invalid items JSON: {je}"}

        if not isinstance(item_list, list) or len(item_list) == 0:
            return {"status": "error", "error_message": "items must be a non-empty JSON array"}

        conn = _get_conn()

        # Validate customer
        customer = conn.execute(
            "SELECT id FROM customers WHERE email = ?", (customer_email,)
        ).fetchone()
        if not customer:
            conn.close()
            return {"status": "error", "error_message": f"Customer with email '{customer_email}' not found"}

        customer_id = customer["id"]

        # Validate products and stock
        total_amount = 0.0
        validated_items = []
        for item in item_list:
            pid = item.get("product_id")
            qty = item.get("quantity")
            if pid is None or qty is None:
                conn.close()
                return {"status": "error", "error_message": "Each item must have 'product_id' and 'quantity'"}
            if not isinstance(qty, int) or qty <= 0:
                conn.close()
                return {"status": "error", "error_message": f"Invalid quantity {qty} for product_id {pid}"}

            product = conn.execute(
                "SELECT id, name, price, stock_quantity FROM products WHERE id = ?", (pid,)
            ).fetchone()
            if not product:
                conn.close()
                return {"status": "error", "error_message": f"Product with id {pid} not found"}
            if product["stock_quantity"] < qty:
                conn.close()
                return {
                    "status": "error",
                    "error_message": (
                        f"Insufficient stock for '{product['name']}' (id {pid}): "
                        f"requested {qty}, available {product['stock_quantity']}"
                    ),
                }

            line_total = product["price"] * qty
            total_amount += line_total
            validated_items.append(
                {"product_id": pid, "quantity": qty, "unit_price": product["price"], "line_total": line_total}
            )

        total_amount = round(total_amount, 2)

        # Insert order
        from datetime import date

        order_date = date.today().isoformat()
        cur = conn.execute(
            "INSERT INTO orders (customer_id, order_date, status, total_amount, shipping_address) VALUES (?, ?, 'pending', ?, ?)",
            (customer_id, order_date, total_amount, shipping_address),
        )
        order_id = cur.lastrowid

        # Insert order items and decrement stock
        for vi in validated_items:
            conn.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                (order_id, vi["product_id"], vi["quantity"], vi["unit_price"]),
            )
            conn.execute(
                "UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?",
                (vi["quantity"], vi["product_id"]),
            )

        conn.commit()
        conn.close()

        return {
            "status": "success",
            "order_id": order_id,
            "order_date": order_date,
            "total_amount": total_amount,
            "items": validated_items,
        }
    except Exception as e:
        logger.error("create_order error: %s", e)
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def get_order_details(order_id: int) -> Dict[str, Any]:
    """
    Get full details for an order including line items and customer name.

    Args:
        order_id: The ID of the order to retrieve.
    """
    try:
        conn = _get_conn()
        order_row = conn.execute(
            """
            SELECT o.id, o.order_date, o.status, o.total_amount, o.shipping_address,
                   cu.name AS customer_name, cu.email AS customer_email
            FROM orders o
            JOIN customers cu ON o.customer_id = cu.id
            WHERE o.id = ?
            """,
            (order_id,),
        ).fetchone()

        if not order_row:
            conn.close()
            return {"status": "error", "error_message": f"Order with id {order_id} not found"}

        items = conn.execute(
            """
            SELECT oi.id AS item_id, oi.product_id, p.name AS product_name, p.sku,
                   oi.quantity, oi.unit_price, (oi.quantity * oi.unit_price) AS line_total
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
            ORDER BY oi.id
            """,
            (order_id,),
        ).fetchall()
        conn.close()

        return {
            "status": "success",
            "order": dict(order_row),
            "items": [dict(i) for i in items],
        }
    except Exception as e:
        logger.error("get_order_details error: %s", e)
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def list_orders(
    customer_email: Optional[str] = None,
    status: Optional[Literal["pending", "processing", "shipped", "delivered", "cancelled"]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List orders with optional filters.

    Args:
        customer_email: Filter by customer email address.
        status: Filter by order status.
        date_from: Start date filter (inclusive, YYYY-MM-DD).
        date_to: End date filter (inclusive, YYYY-MM-DD).
    """
    try:
        conn = _get_conn()
        clauses = []
        params = []

        if customer_email:
            clauses.append("cu.email = ?")
            params.append(customer_email)
        if status:
            clauses.append("o.status = ?")
            params.append(status)
        if date_from:
            clauses.append("o.order_date >= ?")
            params.append(date_from)
        if date_to:
            clauses.append("o.order_date <= ?")
            params.append(date_to)

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        sql = f"""
            SELECT o.id, o.order_date, o.status, o.total_amount, o.shipping_address,
                   cu.name AS customer_name, cu.email AS customer_email
            FROM orders o
            JOIN customers cu ON o.customer_id = cu.id
            {where}
            ORDER BY o.order_date DESC
        """
        rows = conn.execute(sql, params).fetchall()
        conn.close()

        return {
            "status": "success",
            "total_results": len(rows),
            "orders": [dict(r) for r in rows],
        }
    except Exception as e:
        logger.error("list_orders error: %s", e)
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def get_customer_details(customer_email: str) -> Dict[str, Any]:
    """
    Get customer information along with an order history summary.

    Args:
        customer_email: The email address of the customer.
    """
    try:
        conn = _get_conn()
        customer = conn.execute(
            "SELECT id, name, email, tier, registration_date FROM customers WHERE email = ?",
            (customer_email,),
        ).fetchone()

        if not customer:
            conn.close()
            return {"status": "error", "error_message": f"Customer with email '{customer_email}' not found"}

        cid = customer["id"]

        summary = conn.execute(
            """
            SELECT COUNT(*) AS total_orders,
                   COALESCE(SUM(CASE WHEN status != 'cancelled' THEN total_amount ELSE 0 END), 0) AS total_spent,
                   COALESCE(SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END), 0) AS cancelled_orders,
                   MAX(order_date) AS last_order_date
            FROM orders
            WHERE customer_id = ?
            """,
            (cid,),
        ).fetchone()

        orders = conn.execute(
            """
            SELECT id, order_date, status, total_amount
            FROM orders WHERE customer_id = ?
            ORDER BY order_date DESC
            """,
            (cid,),
        ).fetchall()
        conn.close()

        return {
            "status": "success",
            "customer": dict(customer),
            "order_summary": dict(summary),
            "orders": [dict(o) for o in orders],
        }
    except Exception as e:
        logger.error("get_customer_details error: %s", e)
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def update_order_status(
    order_id: int,
    new_status: Literal["pending", "processing", "shipped", "delivered", "cancelled"],
) -> Dict[str, Any]:
    """
    Update the status of an order with transition validation.

    Allowed forward transitions: pending -> processing -> shipped -> delivered.
    Cancellation is only allowed from pending or processing.
    Cannot change status once delivered or cancelled.

    Args:
        order_id: The ID of the order to update.
        new_status: The target status.
    """
    try:
        conn = _get_conn()
        row = conn.execute(
            "SELECT id, status FROM orders WHERE id = ?", (order_id,)
        ).fetchone()

        if not row:
            conn.close()
            return {"status": "error", "error_message": f"Order with id {order_id} not found"}

        current_status = row["status"]

        if not _valid_status_transition(current_status, new_status):
            conn.close()
            return {
                "status": "error",
                "error_message": (
                    f"Invalid status transition from '{current_status}' to '{new_status}'. "
                    f"Allowed forward flow: pending -> processing -> shipped -> delivered. "
                    f"Cancellation is only allowed from pending or processing."
                ),
            }

        conn.execute(
            "UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id)
        )
        conn.commit()
        conn.close()

        return {
            "status": "success",
            "order_id": order_id,
            "previous_status": current_status,
            "new_status": new_status,
        }
    except Exception as e:
        logger.error("update_order_status error: %s", e)
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def get_sales_summary(
    date_from: str,
    date_to: str,
    group_by: Optional[Literal["product", "category", "customer"]] = None,
) -> Dict[str, Any]:
    """
    Get aggregate sales data for a date range, optionally grouped.

    Only non-cancelled orders are included.

    Args:
        date_from: Start date (inclusive, YYYY-MM-DD).
        date_to: End date (inclusive, YYYY-MM-DD).
        group_by: Optionally group results by 'product', 'category', or 'customer'.
    """
    try:
        conn = _get_conn()

        base_where = "WHERE o.status != 'cancelled' AND o.order_date >= ? AND o.order_date <= ?"
        params: list = [date_from, date_to]

        if group_by == "product":
            sql = f"""
                SELECT p.id AS product_id, p.name AS product_name, p.sku,
                       SUM(oi.quantity) AS total_quantity_sold,
                       SUM(oi.quantity * oi.unit_price) AS total_revenue,
                       COUNT(DISTINCT o.id) AS order_count
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                JOIN products p ON oi.product_id = p.id
                {base_where}
                GROUP BY p.id
                ORDER BY total_revenue DESC
            """
        elif group_by == "category":
            sql = f"""
                SELECT c.id AS category_id, c.name AS category_name,
                       SUM(oi.quantity) AS total_quantity_sold,
                       SUM(oi.quantity * oi.unit_price) AS total_revenue,
                       COUNT(DISTINCT o.id) AS order_count
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                JOIN products p ON oi.product_id = p.id
                LEFT JOIN categories c ON p.category_id = c.id
                {base_where}
                GROUP BY c.id
                ORDER BY total_revenue DESC
            """
        elif group_by == "customer":
            sql = f"""
                SELECT cu.id AS customer_id, cu.name AS customer_name, cu.email AS customer_email,
                       SUM(oi.quantity) AS total_items_purchased,
                       SUM(oi.quantity * oi.unit_price) AS total_spent,
                       COUNT(DISTINCT o.id) AS order_count
                FROM orders o
                JOIN customers cu ON o.customer_id = cu.id
                JOIN order_items oi ON o.id = oi.order_id
                {base_where}
                GROUP BY cu.id
                ORDER BY total_spent DESC
            """
        else:
            sql = f"""
                SELECT COUNT(DISTINCT o.id) AS total_orders,
                       SUM(oi.quantity) AS total_items_sold,
                       SUM(oi.quantity * oi.unit_price) AS total_revenue,
                       AVG(o.total_amount) AS average_order_value,
                       COUNT(DISTINCT o.customer_id) AS unique_customers
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                {base_where}
            """

        rows = conn.execute(sql, params).fetchall()
        conn.close()

        data = [dict(r) for r in rows]

        # Round monetary values
        for row_dict in data:
            for key in ("total_revenue", "total_spent", "average_order_value"):
                if key in row_dict and row_dict[key] is not None:
                    row_dict[key] = round(row_dict[key], 2)

        result: Dict[str, Any] = {
            "status": "success",
            "date_from": date_from,
            "date_to": date_to,
        }

        if group_by:
            result["group_by"] = group_by
            result["total_groups"] = len(data)
            result["groups"] = data
        else:
            result["summary"] = data[0] if data else {}

        return result
    except Exception as e:
        logger.error("get_sales_summary error: %s", e)
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def get_low_stock_products(threshold: int = 10) -> Dict[str, Any]:
    """
    List products whose stock quantity is below the given threshold.

    Args:
        threshold: Stock quantity threshold (default 10). Products with stock < threshold are returned.
    """
    try:
        conn = _get_conn()
        rows = conn.execute(
            """
            SELECT p.id, p.name, p.sku, c.name AS category, p.price,
                   p.stock_quantity, p.description
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.stock_quantity < ?
            ORDER BY p.stock_quantity ASC
            """,
            (threshold,),
        ).fetchall()
        conn.close()

        products = [dict(r) for r in rows]
        return {
            "status": "success",
            "threshold": threshold,
            "total_results": len(products),
            "products": products,
        }
    except Exception as e:
        logger.error("get_low_stock_products error: %s", e)
        return {"status": "error", "error_message": str(e)}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run()
