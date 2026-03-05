# 🍣 Sushi Dojo — Ordering System

Full-stack restaurant ordering system with real-time kitchen dashboard.

---

## 🖥️ Run Locally

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
Open `frontend/customer.html` and `frontend/kitchen.html` in your browser.

---

## 🚀 Deploy to the Internet

### Step 1 — Push to GitHub
1. Create a free account at github.com
2. Create a new repository called `sushi-dojo`
3. Upload all files (drag & drop works on GitHub)

### Step 2 — Deploy Backend on Railway
1. Go to railway.app → sign up with GitHub
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `sushi-dojo` repo
4. Set the **Root Directory** to `backend`
5. Railway auto-detects Python and deploys!
6. Go to Settings → Networking → "Generate Domain"
7. Copy your URL e.g. `https://sushi-dojo-production.railway.app`

### Step 3 — Add PostgreSQL on Railway (optional but recommended)
1. In your Railway project, click "+ New" → "Database" → "PostgreSQL"
2. Railway automatically sets the DATABASE_URL environment variable
3. Your data will now persist permanently ✅

### Step 4 — Update Frontend Config
Open `frontend/config.js` and update with your Railway URL:
```javascript
API: "https://YOUR-APP-NAME.railway.app",
WS:  "wss://YOUR-APP-NAME.railway.app/ws",
```
Comment out the localhost lines above.

### Step 5 — Deploy Frontend on Netlify
1. Go to netlify.com → sign up
2. Drag and drop your entire `frontend/` folder onto the Netlify dashboard
3. Netlify gives you a URL like `https://sushi-dojo.netlify.app` 🎉

---

## 📁 Project Structure
```
sushi-dojo/
├── backend/
│   ├── main.py           # FastAPI app
│   ├── models.py         # Data models
│   ├── database.py       # SQLite (local) / PostgreSQL (production)
│   ├── requirements.txt
│   ├── Procfile          # Railway startup command
│   └── runtime.txt       # Python version
├── frontend/
│   ├── config.js         # ← Update this with your Railway URL!
│   ├── customer.html     # Customer ordering page
│   └── kitchen.html      # Kitchen dashboard
└── README.md
```

---

## 🔌 API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/menu` | Get full menu |
| POST | `/orders` | Place a new order |
| GET | `/orders` | Get all orders |
| PATCH | `/orders/{id}/status` | Update order status |
| WS | `/ws` | Real-time WebSocket |
