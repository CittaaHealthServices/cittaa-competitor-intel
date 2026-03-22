from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import Competitor, Post
from app.schemas import CompetitorCreate, CompetitorResponse
from app.config import DEFAULT_COMPETITORS
from typing import List

router = APIRouter(prefix="/competitors", tags=["competitors"])


@router.get("/", response_model=List[CompetitorResponse])
async def list_competitors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Competitor).order_by(Competitor.category, Competitor.name))
    competitors = result.scalars().all()

    # Add post counts
    out = []
    for c in competitors:
        count_result = await db.execute(select(func.count(Post.id)).where(Post.competitor_id == c.id))
        count = count_result.scalar() or 0
        comp_dict = {col.name: getattr(c, col.name) for col in c.__table__.columns}
        comp_dict["post_count"] = count
        out.append(comp_dict)

    return out


@router.post("/", response_model=CompetitorResponse)
async def add_competitor(data: CompetitorCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Competitor).where(Competitor.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Competitor already exists")

    competitor = Competitor(**data.model_dump())
    db.add(competitor)
    await db.commit()
    await db.refresh(competitor)
    return competitor


@router.put("/{competitor_id}", response_model=CompetitorResponse)
async def update_competitor(competitor_id: int, data: CompetitorCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
    competitor = result.scalar_one_or_none()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(competitor, key, value)

    await db.commit()
    await db.refresh(competitor)
    return competitor


@router.delete("/{competitor_id}")
async def delete_competitor(competitor_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
    competitor = result.scalar_one_or_none()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    competitor.is_active = False
    await db.commit()
    return {"message": f"{competitor.name} deactivated"}


@router.post("/seed")
async def seed_default_competitors(db: AsyncSession = Depends(get_db)):
    """Seed default competitors for Cittaa"""
    added = 0
    for comp_data in DEFAULT_COMPETITORS:
        existing = await db.execute(select(Competitor).where(Competitor.name == comp_data["name"]))
        if not existing.scalar_one_or_none():
            competitor = Competitor(**comp_data)
            db.add(competitor)
            added += 1

    await db.commit()
    return {"message": f"Seeded {added} competitors", "total": len(DEFAULT_COMPETITORS)}


@router.post("/{competitor_id}/scrape")
async def trigger_scrape(competitor_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Manually trigger scraping for a specific competitor"""
    result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
    competitor = result.scalar_one_or_none()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    from app.tasks.scheduler import scrape_competitor
    background_tasks.add_task(scrape_competitor, competitor, db)
    return {"message": f"Scraping started for {competitor.name}"}
