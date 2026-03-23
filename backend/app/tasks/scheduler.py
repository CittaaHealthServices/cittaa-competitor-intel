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
from app.models import Competitor, Post, ScrapingLog, Insight, CompetitorIntel
from app.scrapers import scrape_linkedin, scrape_twitter, scrape_instagram, scrape_youtube, scrape_news, scrape_blog
from app.scrapers.search import scrape_deep_search
from app.scrapers.appstore import scrape_appstore_posts, scrape_appstore_intel
from app.scrapers.jobs import scrape_jobs
from app.scrapers.funding import scrape_funding
from app.scrapers.techstack import scrape_techstack, get_techstack_structured
from app.scrapers.glassdoor import scrape_employee_reviews, scrape_employee_review_posts
from app.scrapers.strategy import analyze_strategy
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
        "linkedin":  scrape_linkedin,
        "twitter":   scrape_twitter,
        "instagram": scrape_instagram,
        "youtube":   scrape_youtube,
        "news":      scrape_news,
        "blog":      scrape_blog,
        "search":    scrape_deep_search,
        "appstore":  scrape_appstore_posts,
        "jobs":      scrape_jobs,
        "funding":   scrape_funding,
        "techstack": scrape_techstack,
        "employee":  scrape_employee_review_posts,
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


async def refresh_deep_intel():
    """Refresh structured deep intel (app store, funding, techstack) — runs daily."""
    logger.info("🔬 Refreshing deep competitor intelligence...")
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Competitor).where(Competitor.is_active == True))
        competitors = result.scalars().all()

        for competitor in competitors:
            comp_dict = {
                "id": competitor.id,
                "name": competitor.name,
                "website": competitor.website,
                "linkedin_slug": competitor.linkedin_slug,
            }
            try:
                await _upsert_competitor_intel(comp_dict, db)
            except Exception as e:
                logger.error(f"Deep intel refresh failed for {competitor.name}: {e}")

    logger.info("✅ Deep intel refresh complete")


async def _upsert_competitor_intel(comp_dict: dict, db: AsyncSession):
    """Fetch and store structured intel for one competitor."""
    from sqlalchemy import insert
    name = comp_dict["name"]
    comp_id = comp_dict["id"]

    # App store
    appstore_data = {}
    try:
        intel = await scrape_appstore_intel(comp_dict)
        gp = intel.get("google_play") or {}
        ap = intel.get("apple_store") or {}
        appstore_data = {
            "google_play_rating": gp.get("rating"),
            "google_play_reviews": gp.get("reviews_count"),
            "google_play_installs": gp.get("installs"),
            "google_play_version": gp.get("version"),
            "google_play_last_updated": gp.get("last_updated"),
            "google_play_url": gp.get("url"),
            "apple_rating": ap.get("rating"),
            "apple_reviews": ap.get("reviews_count"),
            "apple_version": ap.get("version"),
            "apple_last_updated": ap.get("last_updated"),
            "apple_url": ap.get("url"),
            "top_reviews": gp.get("top_reviews", []) or [],
        }
    except Exception as e:
        logger.warning(f"App store intel failed for {name}: {e}")

    # Jobs
    jobs_data = {}
    try:
        job_posts = await scrape_jobs(comp_dict)
        open_roles = [
            {"title": p["title"].replace("🧑‍💼 Hiring: ", "").split(" — ")[0], "platform": p["author_name"], "signal": p["content"], "url": p.get("url", "")}
            for p in job_posts[:20]
        ]
        hiring_signals = list(set([
            p["content"].split(". ")[-1] for p in job_posts
            if "Strategic Signal" in p.get("content", "")
        ]))[:10]
        jobs_data = {
            "open_roles": open_roles,
            "hiring_signals": hiring_signals,
            "total_open_roles": len(open_roles),
        }
    except Exception as e:
        logger.warning(f"Jobs intel failed for {name}: {e}")

    # Tech stack
    tech_data = {}
    try:
        ts = await get_techstack_structured(comp_dict)
        tech_data = {
            "technologies": ts.get("technologies", []),
            "tech_categories": {k: [t["name"] for t in v] for k, v in ts.get("categories", {}).items()},
        }
    except Exception as e:
        logger.warning(f"Tech stack intel failed for {name}: {e}")

    # Employee Intelligence (Glassdoor + AmbitionBox)
    employee_data = {}
    try:
        emp = await scrape_employee_reviews(comp_dict)
        ab = emp.get("ambitionbox") or {}
        gd = emp.get("glassdoor") or {}
        employee_data = {
            "ambitionbox_rating": ab.get("overall_rating"),
            "ambitionbox_reviews_count": ab.get("total_reviews"),
            "ambitionbox_culture_rating": ab.get("culture_rating"),
            "ambitionbox_work_life_rating": ab.get("work_life_rating"),
            "ambitionbox_management_rating": ab.get("management_rating"),
            "ambitionbox_growth_rating": ab.get("growth_rating"),
            "ambitionbox_url": ab.get("url"),
            "glassdoor_rating": gd.get("overall_rating"),
            "glassdoor_reviews_count": gd.get("total_reviews"),
            "glassdoor_culture_rating": gd.get("culture_rating"),
            "glassdoor_work_life_rating": gd.get("work_life_rating"),
            "glassdoor_management_rating": gd.get("management_rating"),
            "glassdoor_url": gd.get("url"),
            "employee_overall_sentiment": emp.get("overall_sentiment"),
            "employee_key_pros": emp.get("key_pros", []),
            "employee_key_cons": emp.get("key_cons", []),
            "exit_signals": emp.get("exit_signals", []),
            "join_signals": emp.get("join_signals", []),
            "employee_red_flags": emp.get("red_flags", []),
            "current_employee_score": emp.get("current_employee_score"),
            "former_employee_score": emp.get("former_employee_score"),
        }
    except Exception as e:
        logger.warning(f"Employee intel failed for {name}: {e}")

    # Strategic Intelligence (AI synthesis)
    strategy_data = {}
    try:
        # Build a summary intel dict for the strategy analyzer
        summary_intel = {
            "app_store": {
                "google_play": appstore_data if appstore_data.get("google_play_rating") else None,
                "apple": {"rating": appstore_data.get("apple_rating"), "reviews_count": appstore_data.get("apple_reviews")} if appstore_data.get("apple_rating") else None,
            },
            "funding": {
                "total": appstore_data.get("total_funding") or jobs_data.get("total_funding"),
                "last_round": jobs_data.get("last_round"),
                "last_round_year": jobs_data.get("last_round_year"),
                "investors": jobs_data.get("investors", []),
            },
            "hiring": {
                "total_open_roles": jobs_data.get("total_open_roles", 0),
                "hiring_signals": jobs_data.get("hiring_signals", []),
                "open_roles": jobs_data.get("open_roles", []),
            },
            "tech_stack": {
                "technologies": tech_data.get("technologies", []),
            },
            "employee_sentiment": {
                "overall_sentiment": employee_data.get("employee_overall_sentiment"),
                "key_pros": employee_data.get("employee_key_pros", []),
                "key_cons": employee_data.get("employee_key_cons", []),
                "exit_signals": employee_data.get("exit_signals", []),
                "red_flags": employee_data.get("employee_red_flags", []),
                "ambitionbox": {"overall_rating": employee_data.get("ambitionbox_rating")},
                "glassdoor": {"overall_rating": employee_data.get("glassdoor_rating")},
            },
        }
        strat = await analyze_strategy(comp_dict, summary_intel)
        strategy_data = {
            "strategic_posture": strat.get("strategic_posture"),
            "posture_reason": strat.get("posture_reason"),
            "threat_level": strat.get("threat_level"),
            "threat_reason": strat.get("threat_reason"),
            "top_signals": strat.get("top_signals", []),
            "predicted_moves": strat.get("predicted_moves", []),
            "hiring_strategy_insight": strat.get("hiring_strategy"),
            "employee_strategy_insight": strat.get("employee_intel"),
            "competitive_advantage": strat.get("competitive_advantage"),
            "competitive_weakness": strat.get("competitive_weakness"),
            "cittaa_opportunity": strat.get("cittaa_opportunity"),
            "watch_out_for": strat.get("watch_out_for"),
            "strategy_analyzed_at": datetime.now(timezone.utc),
        }
    except Exception as e:
        logger.warning(f"Strategy intel failed for {name}: {e}")

    # Merge all data
    intel_values = {
        "competitor_id": comp_id,
        "competitor_name": name,
        "last_refreshed_at": datetime.now(timezone.utc),
        **appstore_data,
        **jobs_data,
        **tech_data,
        **employee_data,
        **strategy_data,
    }

    # Upsert
    existing = await db.execute(
        select(CompetitorIntel).where(CompetitorIntel.competitor_id == comp_id)
    )
    existing_row = existing.scalar_one_or_none()

    if existing_row:
        for key, val in intel_values.items():
            if key not in ("competitor_id",) and val is not None:
                setattr(existing_row, key, val)
    else:
        db.add(CompetitorIntel(**intel_values))

    await db.commit()
    logger.info(f"  ✓ Deep intel refreshed for {name}")


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

    # Deep intel refresh every day at 3 AM IST (low-traffic)
    scheduler.add_job(
        refresh_deep_intel,
        CronTrigger(hour=3, minute=0, timezone="Asia/Kolkata"),
        id="deep_intel_refresh",
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
