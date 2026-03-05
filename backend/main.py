import os
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from database import init_db, get_db, DATABASE_URL
from models import OrderCreate, OrderStatusUpdate

app = FastAPI(title="Sushi Dojo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

def row_to_dict(row, cursor=None):
    """Convert a DB row to dict regardless of SQLite or PostgreSQL."""
    if isinstance(row, dict):
        return dict(row)
    # SQLite row - use cursor description
    cols = [d[0] for d in cursor.description]
    return dict(zip(cols, row))

@app.on_event("startup")
async def startup():
    init_db()

@app.get("/menu")
def get_menu():
    return {
        "categories": [
            {
                "name": "Signature Rolls",
                "items": [
                    {"id": 1, "name": "Dragon Roll", "description": "Shrimp tempura, avocado, cucumber topped with avocado & eel sauce", "price": 16.00, "emoji": "🐉"},
                    {"id": 2, "name": "Rainbow Roll", "description": "Crab, cucumber topped with assorted sashimi", "price": 17.00, "emoji": "🌈"},
                    {"id": 3, "name": "Spider Roll", "description": "Soft shell crab, avocado, cucumber, spicy mayo", "price": 15.00, "emoji": "🕷️"},
                    {"id": 4, "name": "Volcano Roll", "description": "Salmon, cream cheese, jalapeño, baked with spicy mayo", "price": 16.50, "emoji": "🌋"},
                ]
            },
            {
                "name": "Nigiri & Sashimi",
                "items": [
                    {"id": 5, "name": "Salmon Nigiri", "description": "Fresh Atlantic salmon over seasoned rice (2 pcs)", "price": 7.00, "emoji": "🍣"},
                    {"id": 6, "name": "Tuna Nigiri", "description": "Premium bluefin tuna over seasoned rice (2 pcs)", "price": 8.00, "emoji": "🍣"},
                    {"id": 7, "name": "Yellowtail Sashimi", "description": "Fresh hamachi, 5 slices", "price": 12.00, "emoji": "🐟"},
                    {"id": 8, "name": "Omakase Sashimi", "description": "Chef's selection of 12 premium slices", "price": 28.00, "emoji": "✨"},
                ]
            },
            {
                "name": "Appetizers",
                "items": [
                    {"id": 9,  "name": "Edamame", "description": "Steamed soybeans with sea salt", "price": 5.00, "emoji": "🫘"},
                    {"id": 10, "name": "Miso Soup", "description": "Traditional dashi broth with tofu & wakame", "price": 4.00, "emoji": "🍵"},
                    {"id": 11, "name": "Gyoza", "description": "Pan-fried pork & vegetable dumplings (6 pcs)", "price": 8.00, "emoji": "🥟"},
                    {"id": 12, "name": "Agedashi Tofu", "description": "Crispy tofu in savory dashi broth", "price": 7.00, "emoji": "🍜"},
                ]
            },
            {
                "name": "Drinks",
                "items": [
                    {"id": 13, "name": "Sake (Hot)", "description": "Traditional Japanese rice wine", "price": 6.00, "emoji": "🍶"},
                    {"id": 14, "name": "Matcha Latte", "description": "Ceremonial grade matcha with steamed milk", "price": 5.00, "emoji": "🍵"},
                    {"id": 15, "name": "Ramune Soda", "description": "Japanese marble soda, assorted flavors", "price": 3.50, "emoji": "🫧"},
                    {"id": 16, "name": "Japanese Beer", "description": "Sapporo or Asahi", "price": 6.00, "emoji": "🍺"},
                ]
            }
        ]
    }

@app.post("/orders")
async def create_order(order: OrderCreate):
    db = get_db()
    cursor = db.cursor()

    items_json = json.dumps([item.dict() for item in order.items])

    if DATABASE_URL:
        cursor.execute("""
            INSERT INTO orders (customer_name, order_type, address, phone, items, total, notes, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending') RETURNING id
        """, (order.customer_name, order.order_type, order.address, order.phone, items_json, order.total, order.notes))
        order_id = cursor.fetchone()["id"]
    else:
        cursor.execute("""
            INSERT INTO orders (customer_name, order_type, address, phone, items, total, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
        """, (order.customer_name, order.order_type, order.address, order.phone, items_json, order.total, order.notes))
        order_id = cursor.lastrowid

    db.commit()
    cursor.close()
    db.close()

    new_order = {
        "id": order_id,
        "customer_name": order.customer_name,
        "order_type": order.order_type,
        "address": order.address,
        "phone": order.phone,
        "items": order.items,
        "total": order.total,
        "notes": order.notes,
        "status": "pending"
    }

    await manager.broadcast({"type": "new_order", "order": {
        **new_order,
        "items": [item.dict() for item in order.items]
    }})
    return new_order

@app.get("/orders")
def get_orders():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
    rows = cursor.fetchall()

    orders = []
    for row in rows:
        d = row_to_dict(row, cursor)
        orders.append({
            "id": d["id"],
            "customer_name": d["customer_name"],
            "order_type": d["order_type"],
            "address": d.get("address"),
            "phone": d["phone"],
            "items": json.loads(d["items"]),
            "total": d["total"],
            "notes": d.get("notes"),
            "status": d["status"],
            "created_at": str(d["created_at"])
        })

    cursor.close()
    db.close()
    return orders

@app.patch("/orders/{order_id}/status")
async def update_order_status(order_id: int, update: OrderStatusUpdate):
    db = get_db()
    cursor = db.cursor()

    if DATABASE_URL:
        cursor.execute("UPDATE orders SET status = %s WHERE id = %s", (update.status, order_id))
    else:
        cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (update.status, order_id))

    db.commit()
    cursor.close()
    db.close()

    await manager.broadcast({"type": "order_updated", "order_id": order_id, "status": update.status})
    return {"success": True, "order_id": order_id, "status": update.status}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
