import os
import json
import random
from datetime import datetime, timedelta
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from database import init_db, get_db, DATABASE_URL
from models import OrderCreate, OrderStatusUpdate, OrderETAUpdate

app = FastAPI(title="Sushi Dojo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Twilio config from environment variables
TWILIO_SID   = os.environ.get("TWILIO_SID")
TWILIO_TOKEN = os.environ.get("TWILIO_TOKEN")
TWILIO_FROM  = os.environ.get("TWILIO_FROM")

def send_sms(to_phone: str, message: str):
    """Send SMS via Twilio. Silently fails if not configured."""
    if not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM]):
        print(f"[SMS skipped - Twilio not configured] To: {to_phone} | {message}")
        return
    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        # Normalize phone number
        phone = to_phone.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if not phone.startswith("+"):
            phone = "+1" + phone
        client.messages.create(body=message, from_=TWILIO_FROM, to=phone)
        print(f"[SMS sent] To: {phone}")
    except Exception as e:
        print(f"[SMS error] {e}")

THANK_YOU_MESSAGES = [
    "🙏 Thank you so much for dining with us today, {name}! Your support means the world to our little kitchen. We hope every bite brought you joy — see you again soon! 🍣",
    "💛 {name}, it was our pleasure to cook for you today! At Sushi Dojo, every order is made with love and care. Thank you for being our guest — you're always welcome here! 🍱",
    "🌸 {name}, thank you for choosing Sushi Dojo! We pour our heart into every roll we make. We hope the food made your day a little brighter. Until next time! 🥢",
    "✨ What a joy it is to cook for guests like you, {name}! Thank you for your order — we hope to see you again very soon at Sushi Dojo! 🍣",
    "🎋 {name}, your order has been delivered with care! Thank you for trusting us with your meal today. Wishing you a wonderful rest of your day! 🙏",
]

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
    if isinstance(row, dict):
        return dict(row)
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
    items_json = json.dumps([item.model_dump() for item in order.items])

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

    # SMS 1: Order confirmation
    item_list = ", ".join([f"{i.quantity}x {i.name}" for i in order.items])
    send_sms(order.phone,
        f"🍣 Hi {order.customer_name}! Order #{str(order_id).zfill(4)} received at Sushi Dojo.\n"
        f"Items: {item_list}\nTotal: ${order.total:.2f}\n"
        f"We'll start preparing shortly and text you when it's ready!"
    )

    new_order = {
        "id": order_id,
        "customer_name": order.customer_name,
        "order_type": order.order_type,
        "address": order.address,
        "phone": order.phone,
        "items": [item.model_dump() for item in order.items],
        "total": order.total,
        "notes": order.notes,
        "status": "pending"
    }

    await manager.broadcast({"type": "new_order", "order": new_order})
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
            "created_at": str(d["created_at"]),
            "eta": d.get("eta")
        })
    cursor.close()
    db.close()
    return orders

@app.patch("/orders/{order_id}/status")
async def update_order_status(order_id: int, update: OrderStatusUpdate):
    db = get_db()
    cursor = db.cursor()

    # Fetch order info for SMS
    if DATABASE_URL:
        cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
    else:
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    row = cursor.fetchone()
    order = row_to_dict(row, cursor) if row else None

    # Update status (and ETA if provided)
    if update.eta_minutes and DATABASE_URL:
        eta_time = (datetime.now() + timedelta(minutes=update.eta_minutes)).strftime("%I:%M %p")
        cursor.execute("UPDATE orders SET status = %s, eta = %s WHERE id = %s", (update.status, eta_time, order_id))
    elif update.eta_minutes:
        eta_time = (datetime.now() + timedelta(minutes=update.eta_minutes)).strftime("%I:%M %p")
        cursor.execute("UPDATE orders SET status = ?, eta = ? WHERE id = ?", (update.status, eta_time, order_id))
    elif DATABASE_URL:
        cursor.execute("UPDATE orders SET status = %s WHERE id = %s", (update.status, order_id))
        eta_time = None
    else:
        cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (update.status, order_id))
        eta_time = None

    db.commit()
    cursor.close()
    db.close()

    # Send SMS based on new status
    if order:
        name = order["customer_name"]
        phone = order["phone"]
        oid = str(order_id).zfill(4)

        if update.status == "preparing" and eta_time:
            send_sms(phone,
                f"👨‍🍳 Hi {name}! We're now preparing your order #{oid}.\n"
                f"Estimated ready time: {eta_time}.\n"
                f"We'll text you as soon as it's done! 🍣"
            )
        elif update.status == "ready":
            order_type = order.get("order_type", "pickup")
            if order_type == "delivery":
                send_sms(phone,
                    f"✅ {name}, your order #{oid} is ready and on its way! "
                    f"Our driver will arrive shortly. Thank you for your patience! 🛵"
                )
            else:
                send_sms(phone,
                    f"✅ {name}, your order #{oid} is READY for pickup! "
                    f"Please come collect it at Sushi Dojo. We can't wait to see you! 🍣"
                )
        elif update.status == "delivered":
            msg = random.choice(THANK_YOU_MESSAGES).format(name=name)
            send_sms(phone, msg)

    await manager.broadcast({"type": "order_updated", "order_id": order_id, "status": update.status, "eta": eta_time if update.eta_minutes else None})
    return {"success": True, "order_id": order_id, "status": update.status}

@app.patch("/orders/{order_id}/eta")
async def update_eta(order_id: int, update: OrderETAUpdate):
    """Update ETA and send customer a heads-up SMS."""
    db = get_db()
    cursor = db.cursor()

    eta_time = (datetime.now() + timedelta(minutes=update.eta_minutes)).strftime("%I:%M %p")

    if DATABASE_URL:
        cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
    else:
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    row = cursor.fetchone()
    order = row_to_dict(row, cursor) if row else None

    if DATABASE_URL:
        cursor.execute("UPDATE orders SET eta = %s WHERE id = %s", (eta_time, order_id))
    else:
        cursor.execute("UPDATE orders SET eta = ? WHERE id = ?", (eta_time, order_id))

    db.commit()
    cursor.close()
    db.close()

    if order:
        send_sms(order["phone"],
            f"⏰ Hi {order['customer_name']}! A quick update on your order #{str(order_id).zfill(4)} — "
            f"we're running a little behind. New estimated ready time: {eta_time}. "
            f"Thank you so much for your patience! 🙏"
        )

    await manager.broadcast({"type": "eta_updated", "order_id": order_id, "eta": eta_time})
    return {"success": True, "eta": eta_time}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
