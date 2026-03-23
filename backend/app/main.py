"""
Cittaa Competitor Intelligence — FastAPI Backend
"""
from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timezone, timedelta
import logging
import os

from app.database import init_db, get_db
from app.models import Post, Competitor, Insight, CompetitorIntel
from app.schemas import DashboardStats
from app.routers import competitors, posts, insights
from app.routers import intel as intel_router
from app.config import settings, DEFAULT_COMPETITORS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup & shutdown — all errors are caught so healthcheck always passes"""
    logger.info("🚀 Starting Cittaa Competitor Intel API...")

    # DB init — non-fatal so the app starts even if DB isn't ready yet
    try:
        await init_db()
        logger.info("✅ Database initialized")

        from app.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            count = await db.execute(select(func.count(Competitor.id)))
            if count.scalar() == 0:
                for comp_data in DEFAULT_COMPETITORS:
                    db.add(Competitor(**comp_data))
                await db.commit()
                logger.info(f"✅ Seeded {len(DEFAULT_COMPETITORS)} default competitors")
    except Exception as e:
        logger.warning(f"⚠️ DB init skipped (will retry on first request): {e}")

    # Scheduler — non-fatal
    try:
        from app.tasks.scheduler import start_scheduler
        start_scheduler()
        logger.info("✅ Scheduler started")
    except Exception as e:
        logger.warning(f"⚠️ Scheduler not started: {e}")

    yield  # App is running — healthcheck passes from here

    logger.info("👋 Shutting down...")
    try:
        from app.tasks.scheduler import scheduler
        if scheduler.running:
            scheduler.shutdown()
    except Exception:
        pass


app = FastAPI(
    title="Cittaa Competitor Intelligence",
    description="Real-time competitive intelligence platform for Cittaa — tracking mental health competitors across all platforms",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
origins = settings.ALLOWED_ORIGINS.split(",") if "," in settings.ALLOWED_ORIGINS else [settings.ALLOWED_ORIGINS]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(competitors.router, prefix="/api")
app.include_router(posts.router, prefix="/api")
app.include_router(insights.router, prefix="/api")
app.include_router(intel_router.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "service": "Cittaa Competitor Intel",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/dashboard/stats", response_model=DashboardStats)
async def dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Get dashboard overview stats"""
    now = datetime.now(timezone.utc)
    today = now - timedelta(hours=24)
    week = now - timedelta(days=7)

    posts_today = await db.execute(select(func.count(Post.id)).where(Post.scraped_at >= today))
    posts_week = await db.execute(select(func.count(Post.id)).where(Post.scraped_at >= week))
    active_competitors = await db.execute(select(func.count(Competitor.id)).where(Competitor.is_active == True))
    viral_posts = await db.execute(select(func.count(Post.id)).where(Post.scraped_at >= week, Post.is_viral == True))
    critical_alerts = await db.execute(select(func.count(Insight.id)).where(Insight.importance.in_(["critical", "high"]), Insight.is_read == False))

    # Top platform this week
    platform_result = await db.execute(
        select(Post.platform, func.count(Post.id).label("c"))
        .where(Post.scraped_at >= week)
        .group_by(Post.platform)
        .order_by(desc("c"))
        .limit(1)
    )
    top_platform_row = platform_result.fetchone()
    top_platform = top_platform_row[0] if top_platform_row else "N/A"

    # Sentiment breakdown
    sentiment_result = await db.execute(
        select(Post.sentiment, func.count(Post.id).label("c"))
        .where(Post.scraped_at >= week)
        .group_by(Post.sentiment)
    )
    sentiment_data = {row[0]: row[1] for row in sentiment_result.fetchall()}

    # Last scrape time
    last_post = await db.execute(select(Post.scraped_at).order_by(desc(Post.scraped_at)).limit(1))
    last_scraped = last_post.scalar()

    return DashboardStats(
        total_posts_today=posts_today.scalar() or 0,
        total_posts_week=posts_week.scalar() or 0,
        active_competitors=active_competitors.scalar() or 0,
        top_platform=top_platform,
        viral_posts=viral_posts.scalar() or 0,
        critical_alerts=critical_alerts.scalar() or 0,
        last_scraped=last_scraped,
        sentiment_breakdown=sentiment_data
    )


@app.post("/api/scrape/trigger-all")
async def trigger_all_scraping(background_tasks: BackgroundTasks):
    """Manually trigger scraping for all competitors"""
    from app.tasks.scheduler import scrape_all_competitors
    background_tasks.add_task(scrape_all_competitors)
    return {"message": "Scraping started for all competitors", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/api/email/send-digest")
async def send_digest_now(background_tasks: BackgroundTasks):
    """Manually send daily digest email"""
    from app.email.digest import send_daily_digest_email
    background_tasks.add_task(send_daily_digest_email)
    return {"message": "Daily digest email queued"}


# Serve React frontend (after build)
frontend_dir = "/app/frontend/dist"
if os.path.exists(frontend_dir):
    app.mount("/assets", StaticFiles(directory=f"{frontend_dir}/assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        index_path = f"{frontend_dir}/index.html"
        return FileResponse(index_path)
