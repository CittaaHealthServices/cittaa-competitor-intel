"""
Background task scheduler - runs scrapers every N hours, sends digests
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.database import AsyncSessionLocal
from app.models import Competitor, Post, ScrapingLog, Insight
from app.scrapers import scrape_linkedin, scrape_twitter, scrape_instagram, scrape_youtube, scrape_news, scrape_blog
from app.ai.gemini import analyze_post, generate_weekly_insights
from app.config import settings

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")


async def scrape_all_competitors():
    """Main scraping job - runs every 6 hours"""
    logger.info("🔍 Starting competitor scraping run...")
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Competitor).where(Competitor.is_active == True))
        competitors = result.scalars().all()

        for competitor in competitors:
            await scrape_competitor(competitor, db)

    logger.info("✅ Scraping run complete")


async def scrape_competitor(competitor, db: AsyncSession):
    """Scrape all platforms for a single competitor"""
    comp_dict = {
        "id": competitor.id,
        "name": competitor.name,
        "website": competitor.website,
        "linkedin_slug": competitor.linkedin_slug,
        "twitter_handle": competitor.twitter_handle,
        "instagram_handle": competitor.instagram_handle,
        "youtube_channel": competitor.youtube_channel,
        "news_keywords": competitor.news_keywords or [competitor.name],
    }

    scrapers = {
        "linkedin": scrape_linkedin,
        "twitter": scrape_twitter,
        "instagram": scrape_instagram,
        "youtube": scrape_youtube,
        "news": scrape_news,
        "blog": scrape_blog,
    }

    total_saved = 0
    for platform, scraper_fn in scrapers.items():
        log = ScrapingLog(
            competitor_id=competitor.id,
            competitor_name=competitor.name,
            platform=platform,
            status="running"
        )
        db.add(log)
        await db.commit()

        try:
            posts = await scraper_fn(comp_dict)
            saved = await save_posts(posts, db)
            total_saved += saved

            log.status = "success"
            log.posts_found = saved
            log.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Scraping failed [{competitor.name}/{platform}]: {e}")
            log.status = "failed"
            log.error_message = str(e)[:500]
            log.completed_at = datetime.now(timezone.utc)

        await db.commit()

    # Update last scraped
    await db.execute(
        update(Competitor)
        .where(Competitor.id == competitor.id)
        .values(last_scraped_at=datetime.now(timezone.utc))
    )
    await db.commit()
    logger.info(f"  ✓ {competitor.name}: {total_saved} new posts saved")

    # Self-monitoring alert: if this IS Cittaa, check for high-importance or negative posts
    if competitor.name.lower() == "cittaa" and total_saved > 0:
        await _check_self_monitoring_alerts(competitor, db)


async def save_posts(posts: list, db: AsyncSession) -> int:
    """Save posts to DB, skip duplicates, run AI analysis"""
    saved = 0
    for post_data in posts:
        try:
            # Check duplicate
            existing = await db.execute(
                select(Post).where(Post.post_id == post_data.get("post_id"))
            )
            if existing.scalar_one_or_none():
                continue

            # Run AI analysis
            content = f"{post_data.get('title', '')} {post_data.get('content', '')}".strip()
            if content and len(content) > 20:
                try:
                    analysis = await analyze_post(
                        content,
                        post_data["competitor_name"],
                        post_data["platform"]
                    )
                    post_data.update(analysis)
                except Exception as e:
                    logger.warning(f"AI analysis skipped: {e}")

            post = Post(
                competitor_id=post_data.get("competitor_id"),
                competitor_name=post_data.get("competitor_name"),
                platform=post_data.get("platform"),
                post_id=post_data.get("post_id"),
                author_name=post_data.get("author_name"),
                author_type=post_data.get("author_type", "company"),
                title=post_data.get("title"),
                content=post_data.get("content"),
                url=post_data.get("url"),
                image_url=post_data.get("image_url"),
                likes=post_data.get("likes", 0),
                comments=post_data.get("comments", 0),
                shares=post_data.get("shares", 0),
                views=post_data.get("views", 0),
                sentiment=post_data.get("sentiment", "neutral"),
                ai_summary=post_data.get("ai_summary"),
                ai_tags=post_data.get("ai_tags", []),
                ai_importance_score=post_data.get("ai_importance_score", 5.0),
                is_viral=post_data.get("is_viral", False),
                published_at=post_data.get("published_at"),
            )
            db.add(post)
            await db.commit()
            saved += 1

        except Exception as e:
            logger.error(f"Failed to save post: {e}")
            await db.rollback()
            continue

    return saved


async def _check_self_monitoring_alerts(competitor, db: AsyncSession):
    """Check if Cittaa's own recent posts need an immediate alert email."""
    try:
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        result = await db.execute(
            select(Post)
            .where(
                Post.competitor_id == competitor.id,
                Post.scraped_at >= one_hour_ago,
            )
            .order_by(Post.ai_importance_score.desc())
            .limit(10)
        )
        recent_posts = result.scalars().all()

        # Flag posts worth alerting about
        alert_posts = [
            p for p in recent_posts
            if (p.ai_importance_score or 0) >= 7.0 or p.sentiment == "negative" or p.is_viral
        ]
        if not alert_posts:
            return

        from app.email.digest import _send_email, _build_email_html
        html = _build_email_html(
            title="🚨 Cittaa Brand Alert",
            subtitle=f"{len(alert_posts)} important mention(s) about Cittaa just detected",
            ai_summary=(
                f"Cittaa has {len(alert_posts)} new high-priority mention(s) that need your attention. "
                "Check the posts below and take action if needed."
            ),
            posts=alert_posts,
            insights=[]
        )
        _send_email(
            [settings.ADMIN_EMAIL],
            f"🚨 Cittaa Brand Alert — {len(alert_posts)} important mention(s)",
            html
        )
        logger.info(f"🚨 Self-monitoring alert sent: {len(alert_posts)} important Cittaa posts detected")
    except Exception as e:
        logger.error(f"Self-monitoring alert failed: {e}")


async def generate_weekly_report():
    """Run every Monday morning - generate strategic weekly insights"""
    logger.info("📊 Generating weekly insights report...")
    async with AsyncSessionLocal() as db:
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        result = await db.execute(
            select(Post).where(Post.scraped_at >= week_ago).order_by(Post.ai_importance_score.desc()).limit(100)
        )
        posts = result.scalars().all()

        if not posts:
            logger.info("No posts found for weekly report")
            return

        # Get competitor names
        comp_result = await db.execute(select(Competitor.name).where(Competitor.is_active == True))
        comp_names = [r[0] for r in comp_result.fetchall()]

        # Build summary for AI
        posts_summary = "\n".join([
            f"[{p.platform.upper()}] {p.competitor_name}: {p.ai_summary or p.content[:200] or p.title or ''}"
            for p in posts[:50]
        ])

        # Generate insights
        weekly_data = await generate_weekly_insights(posts_summary, comp_names)

        if weekly_data:
            for trend in weekly_data.get("key_trends", [])[:5]:
                insight = Insight(
                    insight_type="trend",
                    title=trend if isinstance(trend, str) else trend.get("title", str(trend)),
                    content=trend if isinstance(trend, str) else trend.get("description", ""),
                    competitor_names=comp_names,
                    importance="medium",
                    generated_at=datetime.now(timezone.utc)
                )
                db.add(insight)

            for threat in weekly_data.get("threats", [])[:3]:
                insight = Insight(
                    insight_type="threat",
                    title=threat if isinstance(threat, str) else threat.get("title", str(threat)),
                    content=threat if isinstance(threat, str) else threat.get("description", ""),
                    competitor_names=comp_names,
                    importance="high",
                    generated_at=datetime.now(timezone.utc)
                )
                db.add(insight)

            for opp in weekly_data.get("opportunities", [])[:3]:
                insight = Insight(
                    insight_type="opportunity",
                    title=opp if isinstance(opp, str) else opp.get("title", str(opp)),
                    content=opp if isinstance(opp, str) else opp.get("description", ""),
                    competitor_names=comp_names,
                    importance="high",
                    generated_at=datetime.now(timezone.utc)
                )
                db.add(insight)

            await db.commit()

        # Send email digest
        from app.email.digest import send_weekly_digest
        await send_weekly_digest(posts, weekly_data)
        logger.info("✅ Weekly report generated and sent")


async def send_daily_digest():
    """Daily email digest at 8 AM IST"""
    logger.info("📧 Sending daily digest...")
    from app.email.digest import send_daily_digest_email
    await send_daily_digest_email()


def start_scheduler():
    """Start all background jobs"""
    # Scrape every 6 hours
    scheduler.add_job(
        scrape_all_competitors,
        CronTrigger(hour="0,6,12,18", minute=0, timezone="Asia/Kolkata"),
        id="scrape_competitors",
        replace_existing=True
    )

    # Daily email digest at 8:30 AM IST
    scheduler.add_job(
        send_daily_digest,
        CronTrigger(hour=8, minute=30, timezone="Asia/Kolkata"),
        id="daily_digest",
        replace_existing=True
    )

    # Weekly insights report every Monday at 9 AM IST
    scheduler.add_job(
        generate_weekly_report,
        CronTrigger(day_of_week="mon", hour=9, minute=0, timezone="Asia/Kolkata"),
        id="weekly_report",
        replace_existing=True
    )

    scheduler.start()
    logger.info("✅ Scheduler started: scraping every 6h, daily digest at 8:30 AM IST, weekly report Mondays")
