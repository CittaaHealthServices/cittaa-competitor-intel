"""
Strategic Intelligence Analyzer
Uses Gemini AI to synthesize all competitor signals (hiring, tech stack,
employee sentiment, funding, app store) into strategic intelligence:

- Strategic posture: Aggressive / Scaling / Consolidating / Pivoting / Struggling
- Top strategic signals (what they're actually doing right now)
- Predicted next moves (next 3–6 months)
- Threat level to Cittaa (Low / Medium / High / Critical)
- Hiring strategy breakdown (what skill clusters = what strategic intent)
- SWOT from competitive lens (Cittaa's angle)
"""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

POSTURE_COLORS = {
    "Aggressive":    "#FF4757",   # red — growing hard
    "Scaling":       "#FF6B35",   # orange — steady growth
    "Consolidating": "#2EC4B6",   # teal — stable, optimizing
    "Pivoting":      "#F7B731",   # yellow — changing direction
    "Struggling":    "#94a3b8",   # grey — in trouble
}


async def analyze_strategy(competitor: dict, intel: dict) -> Dict:
    """
    Main entry — accepts a competitor dict + all gathered intel,
    returns a structured strategic intelligence report.
    """
    name = competitor.get("name", "Unknown")

    # Build a rich context for the AI
    context = _build_context(name, intel)

    try:
        from app.ai.gemini import _get_client, settings
        client = _get_client()
        if not client:
            return _fallback_strategy(name, intel)

        prompt = f"""You are a competitive intelligence analyst for Cittaa, an Indian mental health platform.
Analyze the following competitor intelligence data for {name} and produce a structured JSON report.

COMPETITOR DATA:
{context}

Return ONLY a valid JSON object (no markdown, no explanation) with this exact structure:
{{
  "strategic_posture": "one of: Aggressive|Scaling|Consolidating|Pivoting|Struggling",
  "posture_reason": "1-2 sentence explanation of why",
  "threat_level": "one of: Low|Medium|High|Critical",
  "threat_reason": "1-2 sentence explanation of threat to Cittaa specifically",
  "top_signals": [
    "signal 1 — specific, data-backed observation",
    "signal 2",
    "signal 3",
    "signal 4",
    "signal 5"
  ],
  "predicted_moves": [
    "Predicted move 1 in next 3-6 months",
    "Predicted move 2",
    "Predicted move 3"
  ],
  "hiring_strategy": "1-2 sentences on what their hiring pattern reveals about strategy",
  "employee_intel": "1-2 sentences on what employee sentiment reveals about internal health",
  "competitive_advantage": "their biggest strength vs Cittaa",
  "competitive_weakness": "their biggest weakness vs Cittaa",
  "cittaa_opportunity": "the best opportunity for Cittaa given this competitor's weakness",
  "watch_out_for": "the one thing Cittaa should watch out for from this competitor"
}}"""

        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )
        text = response.text.strip()

        # Clean up any markdown
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip().strip("```")

        import json
        result = json.loads(text)
        result["competitor_name"] = name
        result["analyzed_at"] = datetime.now(timezone.utc).isoformat()
        return result

    except Exception as e:
        logger.warning(f"Strategy AI analysis failed for {name}: {e}")
        return _fallback_strategy(name, intel)


def _build_context(name: str, intel: dict) -> str:
    """Build a rich text context from all intel sources."""
    lines = [f"Competitor: {name}"]

    # App store
    app = intel.get("app_store", {})
    gp = app.get("google_play") or {}
    ap = app.get("apple") or {}
    if gp:
        lines.append(f"Google Play: {gp.get('rating')}/5 stars, {gp.get('reviews_count', 0):,} reviews, {gp.get('installs', 'N/A')} installs")
    if ap:
        lines.append(f"Apple App Store: {ap.get('rating')}/5 stars, {ap.get('reviews_count', 0):,} reviews")

    # Funding
    funding = intel.get("funding", {})
    if funding.get("total"):
        lines.append(f"Total Funding: {funding['total']}, Last Round: {funding.get('last_round', 'N/A')} ({funding.get('last_round_year', 'N/A')})")
        if funding.get("investors"):
            lines.append(f"Investors: {', '.join(funding['investors'][:5])}")

    # Hiring
    hiring = intel.get("hiring", {})
    if hiring.get("total_open_roles"):
        lines.append(f"Open Roles: {hiring['total_open_roles']} positions")
        if hiring.get("hiring_signals"):
            lines.append(f"Hiring Signals: {', '.join(hiring['hiring_signals'][:5])}")
        if hiring.get("open_roles"):
            role_titles = [r.get("title", "") for r in hiring["open_roles"][:10]]
            lines.append(f"Sample Roles: {', '.join(role_titles)}")

    # Tech stack
    tech = intel.get("tech_stack", {})
    if tech.get("technologies"):
        techs = [t["name"] if isinstance(t, dict) else t for t in tech["technologies"][:15]]
        lines.append(f"Tech Stack: {', '.join(techs)}")

    # Employee sentiment
    emp = intel.get("employee_sentiment", {})
    if emp:
        ab = emp.get("ambitionbox") or {}
        gd = emp.get("glassdoor") or {}
        if ab.get("overall_rating") or gd.get("overall_rating"):
            rating_str = f"AmbitionBox: {ab.get('overall_rating', '?')}/5" if ab.get("overall_rating") else ""
            if gd.get("overall_rating"):
                rating_str += f" | Glassdoor: {gd.get('overall_rating', '?')}/5"
            lines.append(f"Employee Rating: {rating_str}")
        if emp.get("key_pros"):
            lines.append(f"Employee Pros: {', '.join(emp['key_pros'][:4])}")
        if emp.get("key_cons"):
            lines.append(f"Employee Cons: {', '.join(emp['key_cons'][:4])}")
        if emp.get("exit_signals"):
            lines.append(f"Why Employees Leave: {', '.join(emp['exit_signals'])}")
        if emp.get("red_flags"):
            lines.append(f"Red Flags: {', '.join(emp['red_flags'])}")

    # Recent posts (news/LinkedIn activity)
    recent_posts = intel.get("recent_posts", [])
    if recent_posts:
        post_summaries = [p.get("ai_summary") or p.get("title") or "" for p in recent_posts[:5] if p.get("ai_summary") or p.get("title")]
        if post_summaries:
            lines.append(f"Recent Activity: {' | '.join(post_summaries)}")

    return "\n".join(lines)


def _fallback_strategy(name: str, intel: dict) -> Dict:
    """Rule-based fallback when AI is unavailable."""
    hiring = intel.get("hiring", {})
    funding = intel.get("funding", {})
    emp = intel.get("employee_sentiment", {})
    app = intel.get("app_store", {})

    signals = []
    posture = "Consolidating"

    # Hiring-based signals
    total_roles = hiring.get("total_open_roles", 0)
    if total_roles > 15:
        posture = "Aggressive"
        signals.append(f"Actively hiring ({total_roles} open roles) — aggressive expansion")
    elif total_roles > 8:
        posture = "Scaling"
        signals.append(f"Moderate hiring ({total_roles} open roles) — steady scaling")
    elif total_roles == 0:
        signals.append("No open roles detected — possibly conserving resources")

    # Funding signals
    if funding.get("last_round_year") and funding["last_round_year"] >= 2023:
        signals.append(f"Recently funded ({funding.get('last_round', '')}) — growth capital available")
        if posture == "Consolidating":
            posture = "Scaling"

    # App store signals
    gp = (app.get("google_play") or {})
    if gp.get("rating") and gp["rating"] >= 4.2:
        signals.append(f"Strong app ratings ({gp['rating']}/5) — good product-market fit")
    elif gp.get("rating") and gp["rating"] < 3.5:
        signals.append(f"Low app ratings ({gp['rating']}/5) — product issues")

    # Employee signals
    if emp.get("overall_sentiment") == "negative":
        signals.append("Negative employee sentiment — internal culture issues")
        if posture == "Aggressive":
            posture = "Pivoting"
    elif emp.get("overall_sentiment") == "positive":
        signals.append("High employee satisfaction — stable team")

    # Threat level
    threat = "Medium"
    if total_roles > 15 and funding.get("total"):
        threat = "High"
    elif total_roles == 0 and emp.get("overall_sentiment") == "negative":
        threat = "Low"

    return {
        "competitor_name": name,
        "strategic_posture": posture,
        "posture_reason": f"Based on {total_roles} open roles and available funding signals.",
        "threat_level": threat,
        "threat_reason": "Assessed from hiring velocity, funding, and market positioning.",
        "top_signals": signals[:5] or ["Insufficient data for signal analysis"],
        "predicted_moves": ["Continue current growth trajectory", "Focus on product improvements"],
        "hiring_strategy": hiring.get("hiring_signals", [""])[0] if hiring.get("hiring_signals") else "No hiring data",
        "employee_intel": emp.get("overall_sentiment", "unknown") + " employee sentiment",
        "competitive_advantage": "Unknown — insufficient data",
        "competitive_weakness": "Unknown — insufficient data",
        "cittaa_opportunity": "Monitor closely and identify gaps in their offering",
        "watch_out_for": "Rapid scaling that could capture Cittaa's target market",
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }
