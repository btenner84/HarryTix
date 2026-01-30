# HarryTix Deployment Guide

Deploy your ticket price tracker to Railway (free tier available).

## Quick Deploy to Railway

### 1. Create Railway Account
Go to [railway.app](https://railway.app) and sign up with GitHub.

### 2. Deploy Backend

```bash
# In the backend folder
cd backend

# Login to Railway CLI (install first: npm install -g @railway/cli)
railway login

# Create new project
railway init

# Add PostgreSQL database
railway add --plugin postgresql

# Deploy
railway up
```

Or use the Railway Dashboard:
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose this repo and select `/backend` folder
4. Add PostgreSQL: Click "New" → "Database" → "PostgreSQL"
5. Railway auto-detects the Dockerfile and deploys

### 3. Set Environment Variables

In Railway Dashboard, go to your backend service → Variables:

```
DATABASE_URL=<auto-set by Railway PostgreSQL>
ALLOWED_ORIGINS=https://your-frontend-url.railway.app,http://localhost:5173
```

### 4. Deploy Frontend

```bash
cd frontend

# Create new Railway service in same project
railway init

# Deploy
railway up
```

Set the environment variable:
```
VITE_API_URL=https://your-backend-url.railway.app
```

### 5. Get Your URLs

Railway will give you URLs like:
- Backend: `https://harrytix-backend-xxxx.railway.app`
- Frontend: `https://harrytix-frontend-xxxx.railway.app`

## Alternative: Vercel for Frontend

Frontend can also deploy to Vercel for free:

```bash
cd frontend
npx vercel
```

Set environment variable in Vercel dashboard:
```
VITE_API_URL=https://your-railway-backend.railway.app
```

## Your Ticket Data

The database will auto-seed with your 27 tickets:

| Set | Date | Section | Qty | Cost/Ticket |
|-----|------|---------|-----|-------------|
| A | Sept 2 | 200s Row 1 | 4 | $471.25 |
| B | Sept 19 | Left GA | 6 | $490.67 |
| C | Sept 18 | Section 112 | 8 | $324.88 |
| D | Oct 9 | Left GA | 5 | $433.20 |
| E | Sept 25 | 100s (solos) | 4 | $368.00 |

**Total: 27 tickets | $11,066 invested**

## API Endpoints

Once deployed, your API will be available at:

- `GET /api/comparison` - Price comparison for all sets
- `GET /api/inventory` - Your ticket inventory
- `GET /api/listings/live-inventory` - Live prices from Vivid Seats
- `GET /health` - Health check

## Costs

- **Railway Free Tier**: $5/month credit (enough for this app)
- **Vercel Free Tier**: Unlimited for hobby projects
- **Total**: $0/month for basic usage
