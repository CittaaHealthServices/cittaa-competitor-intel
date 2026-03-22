# Deployment Guide — Cittaa Intel

## Prerequisites
- GitHub account
- Railway account (free tier works)
- Gemini API key (free at makersuite.google.com)
- Gmail account for email digests

---

## Step 1: Push to GitHub

```bash
cd cittaa-competitor-intel

# Initialize git
git init
git add .
git commit -m "feat: initial Cittaa Competitor Intel platform"

# Create GitHub repo (you can do this from github.com or gh CLI)
gh repo create cittaa-competitor-intel --public --push --source=.
# OR manually:
# git remote add origin https://github.com/YOUR_USERNAME/cittaa-competitor-intel.git
# git push -u origin main
```

---

## Step 2: Deploy on Railway

### Option A: One-click from GitHub (Recommended)
1. Go to https://railway.app → New Project
2. Choose "Deploy from GitHub Repo"
3. Select `cittaa-competitor-intel`
4. Railway auto-detects the Dockerfile ✅

### Option B: Railway CLI
```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

---

## Step 3: Add PostgreSQL on Railway
1. In Railway project → "+ New" → Database → PostgreSQL
2. `DATABASE_URL` is automatically set in your app's environment ✅

---

## Step 4: Set Environment Variables on Railway

Go to: Railway Dashboard → Your service → Variables tab

**Required:**
```
GEMINI_API_KEY=AIzaSy...your_gemini_key
SMTP_USER=sairam@cittaa.in
SMTP_PASSWORD=xxxx xxxx xxxx xxxx    ← Gmail App Password
DIGEST_RECIPIENTS=sairam@cittaa.in
```

**Optional (for richer data):**
```
TWITTER_BEARER_TOKEN=AAAA...
YOUTUBE_API_KEY=AIzaSy...
```

---

## Step 5: Set Up GitHub Actions (Auto-deploy)

1. Railway Dashboard → Settings → Tokens → Create Token
2. GitHub repo → Settings → Secrets and variables → Actions → New secret:
   - `RAILWAY_TOKEN` = paste your Railway token
   - `RAILWAY_APP_URL` = your Railway app URL (e.g. https://cittaa-intel.up.railway.app)

Now every `git push` to `main` auto-deploys! 🚀

---

## Step 6: First Run

After deployment:
1. Visit your Railway app URL
2. Click "Scrape Now" button to kick off first scraping run
3. Wait ~5-10 minutes for first data to appear
4. Click "Send Digest" to test email

OR via API:
```bash
# Seed default competitors
curl -X POST https://your-app.railway.app/api/competitors/seed

# Trigger scraping
curl -X POST https://your-app.railway.app/api/scrape/trigger-all
```

---

## Gmail App Password Setup

1. Enable 2-Factor Authentication on your Google account
2. Go to: Google Account → Security → App Passwords
3. Select app: "Mail", device: "Other" → type "Cittaa Intel"
4. Copy the 16-character password
5. Set as `SMTP_PASSWORD` in Railway variables

---

## Getting Gemini API Key

1. Go to https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Set as `GEMINI_API_KEY` in Railway variables

Free tier: 15 requests/minute, 1 million tokens/day — sufficient for monitoring.
