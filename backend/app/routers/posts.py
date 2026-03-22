from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.database import get_db
from app.models import Post
from app.schemas import PostResponse
from typing import List, Optional
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("/", response_model=List[PostResponse])
async def list_posts(
    competitor_id: Optional[int] = None,
    platform: Optional[str] = None,
    sentiment: Optional[str] = None,
    days: int = Query(default=7, ge=1, le=90),
    min_score: float = Query(default=0.0, ge=0.0, le=10.0),
    is_viral: Optional[bool] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=5, le=100),
    db: AsyncSession = Depends(get_db)
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    query = select(Post).where(Post.scraped_at >= since)

    if competitor_id:
        query = query.where(Post.competitor_id == competitor_id)
    if platform:
        query = query.where(Post.platform == platform)
    if sentiment:
        query = query.where(Post.sentiment == sentiment)
    if min_score > 0:
        query = query.where(Post.ai_importance_score >= min_score)
    if is_viral is not None:
        query = query.where(Post.is_viral == is_viral)

    query = query.order_by(desc(Post.ai_importance_score), desc(Post.scraped_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/viral", response_model=List[PostResponse])
async def get_viral_posts(days: int = 7, db: AsyncSession = Depends(get_db)):
    """Get viral/high-impact posts"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(Post)
        .where(Post.scraped_at >= since, Post.is_viral == True)
        .order_by(desc(Post.ai_importance_score))
        .limit(10)
    )
    return result.scalars().all()


@router.get("/top", response_model=List[PostResponse])
async def get_top_posts(days: int = 7, limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Get highest importance posts"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(Post)
        .where(Post.scraped_at >= since)
        .order_by(desc(Post.ai_importance_score))
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/platform-breakdown")
async def platform_breakdown(days: int = 7, db: AsyncSession = Depends(get_db)):
    """Post count breakdown by platform"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(Post.platform, func.count(Post.id).label("count"))
        .where(Post.scraped_at >= since)
        .group_by(Post.platform)
        .order_by(desc("count"))
    )
    return [{"platform": row[0], "count": row[1]} for row in result.fetchall()]


@router.get("/competitor-activity")
async def competitor_activity(days: int = 7, db: AsyncSession = Depends(get_db)):
    """Post activity per competitor"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            Post.competitor_name,
            func.count(Post.id).label("total"),
            func.avg(Post.ai_importance_score).label("avg_score")
        )
        .where(Post.scraped_at >= since)
        .group_by(Post.competitor_name)
        .order_by(desc("total"))
    )
    return [
        {"competitor": row[0], "total_posts": row[1], "avg_importance": round(float(row[2] or 0), 2)}
        for row in result.fetchall()
    ]


@router.get("/sentiment-timeline")
async def sentiment_timeline(days: int = 7, db: AsyncSession = Depends(get_db)):
    """Sentiment breakdown over time"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(Post.sentiment, func.count(Post.id).label("count"))
        .where(Post.scraped_at >= since)
        .group_by(Post.sentiment)
    )
    return [{"sentiment": row[0], "count": row[1]} for row in result.fetchall()]
