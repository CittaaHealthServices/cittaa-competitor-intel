"""
Deep Competitor Intelligence API — serves structured app store, funding,
hiring, and tech stack data for the Intel Profile page.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from typing import List, Optional

from app.database import get_db
from app.models import Competitor, CompetitorIntel, Post

router = APIRouter(prefix="/intel", tags=["intel"])


@router.get("/")
async def list_intel(db: AsyncSession = Depends(get_db)):
    """Get deep intel for all competitors."""
    result = await db.execute(
        select(CompetitorIntel).order_by(CompetitorIntel.competitor_name)
    )
    rows = result.scalars().all()
    return [_serialize_intel(r) for r in rows]


@router.get("/{competitor_id}")
async def get_competitor_intel(competitor_id: int, db: AsyncSession = Depends(get_db)):
    """Get deep intel for a specific competitor."""
    result = await db.execute(
        select(CompetitorIntel).where(CompetitorIntel.competitor_id == competitor_id)
    )
    row = result.scalar_one_or_none()

    if not row:
        # Return empty structure with competitor name if available
        comp_result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
        comp = comp_result.scalar_one_or_none()
        if not comp:
            raise HTTPException(status_code=404, detail="Competitor not found")
        return {
            "competitor_id": competitor_id,
            "competitor_name": comp.name,
            "last_refreshed_at": None,
            "empty": True,
            "message": "No deep intel yet. Click 'Refresh Intel' to fetch data."
        }

    return _serialize_intel(row)


@router.post("/{competitor_id}/refresh")
async def refresh_intel(competitor_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Manually trigger deep intel refresh for a competitor."""
    comp_result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
    comp = comp_result.scalar_one_or_none()
    if not comp:
        raise HTTPException(status_code=404, detail="Competitor not found")

    comp_dict = {
        "id": comp.id,
        "name": comp.name,
        "website": comp.website,
        "linkedin_slug": comp.linkedin_slug,
    }

    async def _refresh():
        from app.database import AsyncSessionLocal
        from app.tasks.scheduler import _upsert_competitor_intel
        async with AsyncSessionLocal() as session:
            await _upsert_competitor_intel(comp_dict, session)

    background_tasks.add_task(_refresh)
    return {"message": f"Deep intel refresh started for {comp.name}", "competitor_id": competitor_id}


@router.post("/refresh-all")
async def refresh_all_intel(background_tasks: BackgroundTasks):
    """Trigger deep intel refresh for all competitors."""
    from app.tasks.scheduler import refresh_deep_intel
    background_tasks.add_task(refresh_deep_intel)
    return {"message": "Deep intel refresh started for all competitors"}


@router.get("/{competitor_id}/jobs")
async def get_competitor_jobs(competitor_id: int, db: AsyncSession = Depends(get_db)):
    """Get recent job posts for a competitor from the posts table."""
    result = await db.execute(
        select(Post)
        .where(Post.competitor_id == competitor_id, Post.platform == "jobs")
        .order_by(Post.scraped_at.desc())
        .limit(50)
    )
    posts = result.scalars().all()
    return [_serialize_post(p) for p in posts]


@router.get("/{competitor_id}/appstore-reviews")
async def get_appstore_reviews(competitor_id: int, db: AsyncSession = Depends(get_db)):
    """Get app store review posts for a competitor."""
    result = await db.execute(
        select(Post)
        .where(Post.competitor_id == competitor_id, Post.platform == "appstore")
        .order_by(Post.scraped_at.desc())
        .limit(30)
    )
    posts = result.scalars().all()
    return [_serialize_post(p) for p in posts]


@router.get("/{competitor_id}/funding-news")
async def get_funding_news(competitor_id: int, db: AsyncSession = Depends(get_db)):
    """Get funding news posts for a competitor."""
    result = await db.execute(
        select(Post)
        .where(Post.competitor_id == competitor_id, Post.platform == "funding")
        .order_by(Post.scraped_at.desc())
        .limit(20)
    )
    posts = result.scalars().all()
    return [_serialize_post(p) for p in posts]


def _serialize_intel(row: CompetitorIntel) -> dict:
    return {
        "id": row.id,
        "competitor_id": row.competitor_id,
        "competitor_name": row.competitor_name,
        "app_store": {
            "google_play": {
                "rating": row.google_play_rating,
                "reviews_count": row.google_play_reviews,
                "installs": row.google_play_installs,
                "version": row.google_play_version,
                "last_updated": row.google_play_last_updated,
                "url": row.google_play_url,
            } if row.google_play_rating else None,
            "apple": {
                "rating": row.apple_rating,
                "reviews_count": row.apple_reviews,
                "version": row.apple_version,
                "last_updated": row.apple_last_updated,
                "url": row.apple_url,
            } if row.apple_rating else None,
            "top_reviews": row.top_reviews or [],
        },
        "funding": {
            "total": row.total_funding,
            "last_round": row.last_round,
            "last_round_year": row.last_round_year,
            "investors": row.investors or [],
            "crunchbase_url": row.crunchbase_url,
        },
        "hiring": {
            "open_roles": row.open_roles or [],
            "hiring_signals": row.hiring_signals or [],
            "total_open_roles": row.total_open_roles or 0,
        },
        "tech_stack": {
            "technologies": row.technologies or [],
            "categories": row.tech_categories or {},
            "total_detected": len(row.technologies or []),
        },
        "last_refreshed_at": row.last_refreshed_at.isoformat() if row.last_refreshed_at else None,
    }


def _serialize_post(p: Post) -> dict:
    return {
        "id": p.id,
        "title": p.title,
        "content": p.content,
        "url": p.url,
        "author_name": p.author_name,
        "author_type": p.author_type,
        "platform": p.platform,
        "sentiment": p.sentiment,
        "ai_summary": p.ai_summary,
        "ai_tags": p.ai_tags or [],
        "ai_importance_score": p.ai_importance_score,
        "published_at": p.published_at.isoformat() if p.published_at else None,
        "scraped_at": p.scraped_at.isoformat() if p.scraped_at else None,
    }
