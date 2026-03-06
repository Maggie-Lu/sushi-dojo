# 🍣 Sushi Dojo — Online Ordering System v2.0

A full-stack restaurant ordering system with real-time kitchen dashboard and SMS notifications.

Built with: **Python FastAPI** (backend) + **HTML/JS** (frontend) + **SQLite/PostgreSQL** (database) + **Twilio** (SMS) + **WebSockets** (real-time)

---

## 📁 Project Structure

```
sushi-dojo/
├── backend/
│   ├── main.py           # FastAPI app — all API routes + SMS logic
│   ├── models.py         # Pydantic data models
│   ├── database.py       # SQLite (local) / PostgreSQL (production)
│   ├── requirements.txt  # Python dependencies
│   ├── Procfile          # Railway startup command
│   └── .gitignore
├── frontend/
│   ├── index.html        # Redirects to customer.html (required by Netlify)
│   ├── customer.html     # Customer ordering page
│   ├── kitchen.html      # Kitchen dashboard
│   └── config.js         # ⚠️ API URLs — update this after deploying backend!
└── README.md
```

---

## 🖥️ Run Locally

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Open `frontend/customer.html` and `frontend/kitchen.html` in your browser.

> **Note:** SMS will be skipped locally unless you set Twilio environment variables.

---

## 🚀 Full Deployment Guide

### Step 1 — Push Code to GitHub

1. Create account at **github.com**
2. Create new repository (e.g. `sushi-dojo`)
3. Upload all project files (drag & drop works on GitHub)
4. Every time you update code, update the files on GitHub → Railway auto-redeploys

---

### Step 2 — Deploy Backend on Railway

1. Sign up at **railway.app** using your GitHub account
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your repository
4. In **Settings** → **Source** → set **Root Directory** to `backend`
5. In **Settings** → **Networking** → click **"Generate Domain"**
6. Copy your public URL → e.g. `https://your-app.up.railway.app`

> ⚠️ **Common errors encountered:**
> - `runtime.txt` specifying Python 3.11.0 → Railway couldn't install it → **delete `runtime.txt`**
> - Pydantic v1 incompatible with Python 3.13 → use **Pydantic v2.9.2 + FastAPI 0.115.0**
> - Port mismatch → always use `$PORT` in Procfile, Railway sets this automatically (usually 8080)

---

### Step 3 — Add Environment Variables on Railway

Go to your Railway service → **Variables** tab → add these:

| Variable | Value | Notes |
|----------|-------|-------|
| `TWILIO_SID` | `ACxxxxxxxxxxxx` | From Twilio Console |
| `TWILIO_TOKEN` | `xxxxxxxxxx` | From Twilio Console → keep secret! |
| `TWILIO_FROM` | `+1xxxxxxxxxx` | Your Twilio phone number |
| `DATABASE_URL` | auto-set | Only if you add PostgreSQL (see Step 4) |

> ⚠️ **Security:** Never commit credentials to GitHub. Always use Railway environment variables.
> Regenerate your Twilio Auth Token periodically for security.

---

### Step 4 — Add PostgreSQL on Railway (Recommended)

Without PostgreSQL, orders reset every time Railway restarts the server.

1. In your Railway project → click **"+ New"** → **"Database"** → **"PostgreSQL"**
2. Railway automatically sets `DATABASE_URL` environment variable
3. The app detects this and switches from SQLite to PostgreSQL automatically ✅

---

### Step 5 — Update Frontend Config

Open `frontend/config.js` and update with your Railway URL:

```javascript
const CONFIG = {
  API: "https://YOUR-APP.up.railway.app",
  WS:  "wss://YOUR-APP.up.railway.app/ws",
};
```

> `ws://` becomes `wss://` (secure WebSocket) on the internet — important!

---

### Step 6 — Deploy Frontend on Netlify

1. Sign up at **netlify.com**
2. Go to your project → **Deploys** section
3. Drag and drop the entire `frontend/` **folder** onto the drop zone
4. Netlify requires an `index.html` file — our `index.html` auto-redirects to `customer.html`
5. Your URLs will be:
   - Customer page: `https://your-site.netlify.app` (or `/customer.html`)
   - Kitchen dashboard: `https://your-site.netlify.app/kitchen.html`

> ⚠️ **Common errors encountered:**
> - Dragging individual files instead of the folder → Netlify rejects it → drag the whole folder
> - Missing `index.html` → Netlify shows "Page not found" → always include `index.html`
> - Old `config.js` with `localhost` → menu won't load → always update `config.js` before uploading

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/menu` | Get full menu |
| POST | `/orders` | Place a new order → sends confirmation SMS |
| GET | `/orders` | Get all orders |
| PATCH | `/orders/{id}/status` | Update status → sends SMS per status |
| PATCH | `/orders/{id}/eta` | Update ETA only → sends delay SMS |
| WS | `/ws` | Real-time WebSocket for kitchen dashboard |

---

## 📱 SMS Flow (Twilio)

| Trigger | SMS Sent |
|---------|----------|
| Order placed | Confirmation with items + total |
| "Start Preparing" clicked | Preparing now + estimated ready time |
| ETA updated | Apology + new estimated time |
| "Mark as Ready" clicked | Ready for pickup / on the way |
| "Delivered/Picked Up" clicked | Warm thank you message |

---

## 🔔 Kitchen Dashboard Features

- **Persistent sound alert** — triple beep every 8 seconds for new pending orders
- **Flashing browser tab** — shows "🔴 NEW ORDER!" until acknowledged
- **Alert stops** automatically when "Start Preparing" is clicked
- **ETA time picker** — select 10/15/20/25/30/40/50/60 min when starting prep
- **Update ETA button** — send customer a delay notification anytime
- **Live order cards** — real-time updates via WebSocket
- **Order timer** — shows elapsed time, turns red after 20 minutes

---

## 🛠️ Tech Stack Explained

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend | FastAPI (Python) | Fast, modern, easy to read |
| Database | SQLite → PostgreSQL | SQLite for local dev, PostgreSQL for production |
| Real-time | WebSockets | Orders appear instantly without page refresh |
| SMS | Twilio | Industry standard, ~$0.01 per SMS |
| Frontend hosting | Netlify | Free, drag-and-drop deployment |
| Backend hosting | Railway | Free tier, auto-deploys from GitHub |

---

## 💰 Running Costs

| Service | Cost |
|---------|------|
| Railway (backend) | Free tier: $5 credit/month |
| Netlify (frontend) | Free forever |
| Twilio (SMS) | ~$0.01 per SMS |
| PostgreSQL on Railway | Free tier included |
| Custom domain (optional) | ~$12/year |

---

## 🗺️ Future Improvements (v3.0 ideas)

- [ ] Payment integration (Stripe)
- [ ] Customer loyalty / marketing SMS campaigns
- [ ] Order history & sales reporting dashboard
- [ ] Kitchen receipt printer (PrintNode)
- [ ] Custom domain name
- [ ] Menu management UI (edit dishes without code)
- [ ] Multi-language support

---

## 👩‍💻 Development Notes

- Pydantic v2 uses `.model_dump()` — not `.dict()` (v1 syntax)
- Railway uses Python 3.13 by default — avoid old packages incompatible with it
- WebSocket URL must use `wss://` (not `ws://`) in production
- Always set `CORS allow_origins=["*"]` for cross-origin frontend/backend
- SQLite resets on Railway restart → use PostgreSQL for persistent data
