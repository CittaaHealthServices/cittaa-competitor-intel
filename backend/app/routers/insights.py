from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update
from app.database import get_db
from app.models import Insight
from app.schemas import InsightResponse
from typing import List
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/", response_model=List[InsightResponse])
async def list_insights(
    insight_type: str = None,
    days: int = 30,
    db: AsyncSession = Depends(get_db)
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    query = select(Insight).where(Insight.generated_at >= since)
    if insight_type:
        query = query.where(Insight.insight_type == insight_type)
    query = query.order_by(desc(Insight.generated_at))
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/{insight_id}/read")
async def mark_read(insight_id: int, db: AsyncSession = Depends(get_db)):
    await db.execute(update(Insight).where(Insight.id == insight_id).values(is_read=True))
    await db.commit()
    return {"message": "Marked as read"}


@router.post("/generate-weekly")
async def trigger_weekly_insights(background_tasks: BackgroundTasks):
    """Manually trigger weekly insights generation"""
    from app.tasks.scheduler import generate_weekly_report
    background_tasks.add_task(generate_weekly_report)
    return {"message": "Weekly insights generation started"}
