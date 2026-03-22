# Cittaa Competitor Intelligence Platform

> Real-time competitive intelligence for Cittaa — tracking 10+ mental health competitors across LinkedIn, Twitter, Instagram, YouTube, News, and Blogs. Powered by Google Gemini AI.

---

## Features

- **Multi-platform monitoring**: LinkedIn, Twitter/X, Instagram, YouTube, News, Blogs, Press Releases
- **AI-powered analysis**: Every post analyzed by Gemini 1.5 Flash for importance, sentiment, tags & Cittaa-specific insights
- **Live dashboard**: Real-time charts, competitor activity, sentiment breakdown
- **Viral detection**: Automatic flagging of high-engagement posts
- **Email digests**: Beautiful daily + weekly HTML emails at 8:30 AM IST
- **Strategic insights**: AI-generated threats, opportunities & action items
- **10 competitors pre-loaded**: YourDOST, Wysa, InnerHour, MindPeers, HeartItOut, Lissun, Talkspace, BetterHelp, Headspace, Calm

---

## Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/cittaa-competitor-intel.git
cd cittaa-competitor-intel
```

### 2. Set up environment
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 3. Run locally with Docker
```bash
docker-compose up --build
# App runs at http://localhost:8000
```

---

## Deploy to Railway

### Step 1: Create Railway project
1. Go to [railway.app](https://railway.app) and log in
2. Click **New Project → Deploy from GitHub repo**
3. Select your `cittaa-competitor-intel` repository

### Step 2: Add PostgreSQL database
1. In your Railway project, click **New Service → Database → PostgreSQL**
2. Railway will auto-inject `DATABASE_URL` into your app

### Step 3: Set environment variables
In Railway Dashboard → Your Service → Variables, add:
```
GEMINI_API_KEY=your_key_here
SMTP_USER=sairam@cittaa.in
SMTP_PASSWORD=your_gmail_app_password
DIGEST_RECIPIENTS=sairam@cittaa.in
```

### Step 4: GitHub Actions (auto-deploy)
1. In Railway: Settings → Tokens → Generate token
2. In GitHub repo: Settings → Secrets → Add `RAILWAY_TOKEN`
3. Add `RAILWAY_APP_URL` = your Railway app URL
4. Every push to `main` auto-deploys!

---

## Architecture

```
cittaa-competitor-intel/
├── backend/                 # FastAPI Python backend
│   └── app/
│       ├── main.py          # FastAPI app entry point
│       ├── models.py        # SQLAlchemy DB models
│       ├── scrapers/        # Platform scrapers
│       │   ├── linkedin.py
│       │   ├── twitter.py
│       │   ├── instagram.py
│       │   ├── youtube.py
│       │   └── news.py
│       ├── ai/gemini.py     # Google Gemini integration
│       ├── tasks/scheduler.py  # APScheduler background jobs
│       └── email/digest.py  # Email digest builder
├── frontend/                # React + Vite dashboard
│   └── src/
│       ├── pages/           # Dashboard, Feed, Competitors, Insights
│       └── services/api.js  # API client
├── Dockerfile               # Multi-stage build
├── docker-compose.yml       # Local development
└── railway.toml             # Railway deployment config
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/dashboard/stats` | Dashboard overview stats |
| GET | `/api/competitors/` | List all competitors |
| POST | `/api/competitors/seed` | Seed default competitors |
| POST | `/api/competitors/{id}/scrape` | Trigger scrape for one competitor |
| GET | `/api/posts/` | Get posts with filters |
| GET | `/api/posts/top` | Top posts by AI importance score |
| GET | `/api/posts/viral` | Viral posts |
| GET | `/api/insights/` | AI-generated insights |
| POST | `/api/scrape/trigger-all` | Trigger all scrapers |
| POST | `/api/email/send-digest` | Send digest email now |

---

## Scraping Schedule

| Job | Schedule |
|-----|----------|
| Competitor scraping | Every 6 hours (IST) |
| Daily email digest | 8:30 AM IST |
| Weekly insights report | Monday 9:00 AM IST |

---

## Competitors Tracked

**National (India):** YourDOST, Wysa, InnerHour, MindPeers, HeartItOut, Lissun
**International:** Talkspace, BetterHelp, Headspace, Calm

Add more via dashboard → Competitors → Add Competitor

---

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy, PostgreSQL
- **AI**: Google Gemini 1.5 Flash
- **Scraping**: httpx, BeautifulSoup4, feedparser, Playwright
- **Frontend**: React 18, Vite, Tailwind CSS, Recharts
- **Deployment**: Railway + GitHub Actions
- **Email**: SMTP (Gmail)

---

Built with ❤️ for Cittaa · [cittaa.in](https://cittaa.in)
