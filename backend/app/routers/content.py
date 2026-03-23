"""
Content Playbook Router
Serves AI-generated LinkedIn + Instagram post recommendations for Cittaa.
Caches results to avoid repeated Gemini calls.
"""
import json
import logging
import os
from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import Competitor, CompetitorIntel
from app.scrapers.content_advisor import generate_content_recommendations

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content", tags=["content"])

CACHE_FILE = "/tmp/cittaa_content_recommendations.json"
CACHE_TTL_HOURS = 24  # Regenerate at most once per day


def _cache_is_fresh() -> bool:
    if not os.path.exists(CACHE_FILE):
        return False
    try:
        with open(CACHE_FILE) as f:
            data = json.load(f)
        ts = data.get("generated_at")
        if not ts:
            return False
        age_hours = (datetime.utcnow() - datetime.fromisoformat(ts)).total_seconds() / 3600
        return age_hours < CACHE_TTL_HOURS
    except Exception:
        return False


@router.get("/recommendations")
async def get_content_recommendations(force_refresh: bool = False):
    """
    Returns AI-generated LinkedIn + Instagram post recommendations.
    Results are cached for 24 hours. Pass ?force_refresh=true to regenerate.
    """
    if not force_refresh and _cache_is_fresh():
        try:
            with open(CACHE_FILE) as f:
                return json.load(f)
        except Exception:
            pass

    # Build competitor context from DB
    try:
        async with AsyncSessionLocal() as db:
            comps = (await db.execute(select(Competitor))).scalars().all()
            intel_rows = (await db.execute(select(CompetitorIntel))).scalars().all()

        intel_map = {row.competitor_id: row for row in intel_rows}
        summaries = []
        for comp in comps:
            intel = intel_map.get(comp.id)
            summaries.append({
                "name": comp.name,
                "posture": getattr(intel, "strategic_posture", None),
                "keywords": comp.news_keywords or [],
                "category": comp.category,
            })
    except Exception as e:
        logger.warning(f"Could not load competitors for content recommendations: {e}")
        summaries = []

    result = await generate_content_recommendations(summaries)

    # Cache to disk
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(result, f)
    except Exception as e:
        logger.warning(f"Could not cache content recommendations: {e}")

    return result
