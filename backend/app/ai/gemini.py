"""
Gemini AI analysis engine — lazy import so missing API key never crashes startup
"""
import logging
import json
import re
import asyncio
from functools import partial
from app.config import settings

logger = logging.getLogger(__name__)

def _get_model():
    """Lazy-load Gemini model only when needed."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        return genai.GenerativeModel(settings.GEMINI_MODEL)
    except Exception as e:
        logger.warning(f"Gemini model unavailable: {e}")
        return None


async def analyze_post(post_content: str, competitor_name: str, platform: str) -> dict:
    """Analyze a competitor post with Gemini AI."""
    if not settings.GEMINI_API_KEY:
        return _default_analysis()

    model = _get_model()
    if not model:
        return _default_analysis()

    prompt = f"""You are a competitive intelligence analyst for Cittaa, an Indian mental health & wellness platform for students and employees.

Analyze this {platform} post from competitor "{competitor_name}":

---
{post_content[:3000]}
---

Provide a JSON response with:
1. "summary": 2-3 sentence summary of what this post is about and why it matters to Cittaa
2. "sentiment": one of "positive", "neutral", "negative" (toward the competitor's brand)
3. "tags": list of 3-5 relevant tags (e.g., "product launch", "fundraising", "hiring", "new feature", "partnership", "thought leadership", "mental health awareness", "pricing")
4. "importance_score": float 0-10 (10=critical for Cittaa to know about; 1=generic content)
5. "is_viral_potential": boolean - true if this post seems to be gaining significant traction
6. "insights_for_cittaa": 1-2 specific actionable insights for how Cittaa can respond or capitalize
7. "category": one of "Product Update", "Company News", "Thought Leadership", "Marketing Campaign", "Hiring", "Partnership", "Award/Recognition", "Funding", "General"

Return ONLY valid JSON, no markdown.
"""
    try:
        # Run blocking Gemini call in thread pool to avoid blocking asyncio event loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, partial(model.generate_content, prompt))
        text = response.text.strip()
        text = re.sub(r"```json\n?", "", text)
        text = re.sub(r"```\n?", "", text)
        result = json.loads(text)
        return {
            "ai_summary": result.get("summary", ""),
            "sentiment": result.get("sentiment", "neutral"),
            "ai_tags": result.get("tags", []),
            "ai_importance_score": float(result.get("importance_score", 5.0)),
            "is_viral": result.get("is_viral_potential", False),
            "insights_for_cittaa": result.get("insights_for_cittaa", ""),
            "category": result.get("category", "General")
        }
    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        return _default_analysis()


async def generate_weekly_insights(posts_summary: str, competitor_names: list) -> dict:
    """Generate weekly strategic insights from all competitor activity."""
    if not settings.GEMINI_API_KEY:
        return {}

    model = _get_model()
    if not model:
        return {}

    prompt = f"""You are a senior competitive intelligence analyst for Cittaa, an Indian mental health & wellness platform (cittaa.in).

Here's a summary of what Cittaa's competitors have been doing this week:
Competitors analyzed: {', '.join(competitor_names)}

Activity summary:
{posts_summary[:5000]}

Generate a strategic intelligence report with:
1. "key_trends": Top 3-5 trends you see across competitors this week
2. "threats": Top 2-3 threats to Cittaa from competitor activity
3. "opportunities": Top 2-3 opportunities Cittaa can capitalize on
4. "recommended_actions": 3-5 specific things Cittaa's team should do NOW
5. "content_ideas": 3 content/campaign ideas Cittaa should create based on competitor gaps
6. "executive_summary": 3-4 sentence high-level summary for the CEO

Return ONLY valid JSON, no markdown.
"""
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, partial(model.generate_content, prompt))
        text = response.text.strip()
        text = re.sub(r"```json\n?", "", text)
        text = re.sub(r"```\n?", "", text)
        return json.loads(text)
    except Exception as e:
        logger.error(f"Gemini weekly insights failed: {e}")
        return {}


async def generate_daily_digest_html(posts: list, insights: list) -> str:
    """Generate digest summary text using Gemini."""
    if not settings.GEMINI_API_KEY or not posts:
        return ""

    model = _get_model()
    if not model:
        return ""

    posts_text = "\n".join([
        f"- [{p['platform']}] {p['competitor_name']}: {p.get('ai_summary', p.get('content', ''))[:200]}"
        for p in posts[:20]
    ])

    prompt = f"""Create a concise competitive intelligence email digest for Cittaa's team.

Today's highlights from competitor monitoring:
{posts_text}

Key insights:
{chr(10).join([i.get('title', '') for i in insights[:5]])}

Write a 200-word executive summary that:
1. Highlights the most important competitor moves today
2. Flags any urgent actions needed
3. Has an upbeat, strategic tone

Keep it scannable. Plain text only, no HTML.
"""
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, partial(model.generate_content, prompt))
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini digest generation failed: {e}")
        return "Daily competitor monitoring complete. Check your dashboard for details."


def _default_analysis():
    return {
        "ai_summary": "",
        "sentiment": "neutral",
        "ai_tags": [],
        "ai_importance_score": 5.0,
        "is_viral": False,
        "insights_for_cittaa": "",
        "category": "General"
    }
