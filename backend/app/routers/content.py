"""
Content Playbook Router
Serves AI-generated LinkedIn + Instagram + SEO recommendations for Cittaa.

Strategy:
- First load (no cache): return fallback data instantly, trigger Gemini in background
- force_refresh=true: return stale/fallback instantly, regenerate in background
- Cache fresh (<24h): return cache immediately
- Frontend polls /status to know when AI generation is complete
"""
import asyncio
import json
import logging
import os
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import Competitor, CompetitorIntel
from app.scrapers.content_advisor import generate_content_recommendations, _fallback_recommendations

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content", tags=["content"])

CACHE_FILE     = "/tmp/cittaa_content_recommendations.json"
PENDING_FILE   = "/tmp/cittaa_content_generating.flag"
CACHE_TTL_HOURS = 24


# ─── Cache helpers ────────────────────────────────────────────────────────────

def _cache_is_fresh() -> bool:
    if not os.path.exists(CACHE_FILE):
        return False
    try:
        data = _load_cache()
        if not data:
            return False
        ts = data.get("generated_at")
        if not ts:
            return False
        age_h = (datetime.utcnow() - datetime.fromisoformat(ts)).total_seconds() / 3600
        return age_h < CACHE_TTL_HOURS
    except Exception:
        return False


def _load_cache() -> dict | None:
    try:
        with open(CACHE_FILE) as f:
            return json.load(f)
    except Exception:
        return None


def _save_cache(data: dict):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning(f"Could not write content cache: {e}")


def _is_generating() -> bool:
    return os.path.exists(PENDING_FILE)


def _set_generating(flag: bool):
    if flag:
        try:
            open(PENDING_FILE, "w").close()
        except Exception:
            pass
    else:
        try:
            os.remove(PENDING_FILE)
        except Exception:
            pass


# ─── Background AI generation ─────────────────────────────────────────────────

async def _generate_in_background(summaries: list):
    """Run Gemini generation and save to cache. Called as a background task."""
    _set_generating(True)
    try:
        result = await generate_content_recommendations(summaries)
        result["generated_at"] = datetime.utcnow().isoformat()
        result["ai_generated"] = True
        _save_cache(result)
        logger.info("✅ Content recommendations generated and cached.")
    except Exception as e:
        logger.error(f"Background content generation failed: {e}")
    finally:
        _set_generating(False)


async def _get_competitor_summaries() -> list:
    try:
        async with AsyncSessionLocal() as db:
            comps = (await db.execute(select(Competitor))).scalars().all()
            intel_rows = (await db.execute(select(CompetitorIntel))).scalars().all()
        intel_map = {row.competitor_id: row for row in intel_rows}
        return [
            {
                "name": comp.name,
                "posture": getattr(intel_map.get(comp.id), "strategic_posture", None),
                "keywords": comp.news_keywords or [],
                "category": comp.category,
            }
            for comp in comps
        ]
    except Exception as e:
        logger.warning(f"Could not load competitor summaries: {e}")
        return []


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/recommendations")
async def get_content_recommendations(
    force_refresh: bool = False,
    background_tasks: BackgroundTasks = None,
):
    """
    Returns content + SEO recommendations.
    - Always responds instantly (cached, stale, or fallback data).
    - When AI generation is needed, triggers it in the background.
    - Frontend can poll /api/content/status to know when fresh AI data is ready.
    """
    # Serve fresh cache immediately
    if not force_refresh and _cache_is_fresh():
        data = _load_cache()
        if data:
            data["generating"] = False
            return data

    # Load stale cache or fallback to return immediately
    stale = _load_cache()
    response_data = stale if stale else _fallback_recommendations()
    response_data["generating"] = True  # tell frontend AI is working in background

    # Kick off background AI generation if not already running
    if not _is_generating() and background_tasks is not None:
        summaries = await _get_competitor_summaries()
        background_tasks.add_task(_generate_in_background, summaries)
        logger.info("🚀 Background content generation started.")

    return response_data


@router.get("/status")
async def get_generation_status():
    """Poll this to know if background AI generation is complete."""
    generating = _is_generating()
    cache_exists = os.path.exists(CACHE_FILE)
    ai_ready = cache_exists and not generating

    ts = None
    if cache_exists:
        data = _load_cache()
        ts = data.get("generated_at") if data else None

    return {
        "generating": generating,
        "ai_ready": ai_ready,
        "generated_at": ts,
    }
