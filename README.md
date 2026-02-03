# HarryTix - Ticket Price Tracker

Track live ticket prices for your Harry Styles MSG tickets across StubHub, SeatGeek, and Vivid Seats.

## Quick Start

### Using Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# The app will be available at:
# - Frontend: http://localhost:5173
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Manual Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start postgres (or use docker)
docker run -d --name harrytix-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=harrytix -p 5432:5432 postgres:15-alpine

# Run database migrations
alembic upgrade head

# Seed the database with your ticket inventory
python seed_data.py

# Find event IDs for your shows
python find_events.py

# Start the server
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

## Setting Up Event IDs

The system uses **web scraping** (no API keys needed!), but you need to tell it which events to track.

### Step 1: Find Event IDs

Run the helper script:
```bash
cd backend
python find_events.py
```

Or find them manually:
1. **StubHub**: Go to the event page, ID is in URL: `stubhub.com/event/[EVENT_ID]`
2. **SeatGeek**: Go to event page, ID is at end of URL: `seatgeek.com/.../[EVENT_ID]`
3. **Vivid Seats**: Go to event page: `vividseats.com/production/[EVENT_ID]`

### Step 2: Add IDs to Database

```bash
# Update event 1 (Sept 18 show) with platform IDs
curl -X PUT http://localhost:8000/api/events/1 \
  -H "Content-Type: application/json" \
  -d '{
    "stubhub_event_id": "105234567",
    "seatgeek_event_id": "6234567",
    "vividseats_event_id": "4234567"
  }'
```

Repeat for each of your 5 events.

## How It Works

- **No API keys required** - uses web scraping
- **Hourly updates** - scheduler runs every hour automatically
- **Rate limited** - 10 requests/min per platform (respectful scraping)
- **Auto-refresh UI** - frontend polls every 5 minutes

## Features

- **Dashboard**: Overview of all tickets, costs, and projected revenue
- **Inventory**: Detailed view of your ticket holdings with market comparisons
- **Analytics**: Price trend charts and platform comparisons
- **Hourly Updates**: Automatic price collection every hour
- **Auto-Refresh**: UI updates every 5 minutes

## Your Inventory

| Set | Event | Section | Qty | Cost | Target Range |
|-----|-------|---------|-----|------|--------------|
| A | Aug/Sept MSG | Sec 200s Row 1 | 4 | $1,885 | $800-$1,400 |
| B | Sat Sept 19 | GA/PIT | 6 | $2,944 | $800-$1,300 |
| C | Fri Sept 18 | Sec 112 | 8 | $2,599 | $700-$1,200 |
| D | Fri Oct 9 | GA/PIT | 5 | $2,166 | $800-$1,350 |
| E | Fri Sept 25 | Lower 100s | 4 | $1,472 | $750-$1,300 |
| F | Sat Oct 17 | Sec 109 Row 4 | 1 | $368 | $750-$1,300 |
| G | Sat Oct 17 | GA Pit | 5 | $2,166 | $800-$1,350 |
| H | Sat Oct 17 | Sec 114 Row 21 | 2 | $736 | $750-$1,300 |

**Total: 35 tickets | $14,336 invested**

## Deployment to Railway

1. Create a Railway project
2. Add PostgreSQL database
3. Deploy backend from GitHub
4. Deploy frontend
5. That's it! No API keys to configure.

See `backend/railway.toml` for configuration.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| GET /api/inventory | List all tickets with market data |
| GET /api/listings/current?event_id=X | Current listings for event |
| GET /api/analytics/revenue | Revenue projections |
| GET /api/analytics/price-history | Price trends for charts |
| PUT /api/events/{id} | Update event with platform IDs |

## Troubleshooting

**No listings appearing?**
- Make sure you've added event IDs (run `python find_events.py`)
- Check logs: `docker-compose logs backend`
- Platforms may block if too many requests - wait an hour

**Scraping blocked?**
- The scrapers use standard browser headers
- Rate limiting is built in (10 req/min)
- If blocked, data will appear on next hourly run
