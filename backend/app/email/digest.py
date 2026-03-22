"""
Email digest system - sends daily & weekly HTML emails to the Cittaa team
"""
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone, timedelta
from typing import List
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Post, Insight, Competitor
from app.ai.gemini import generate_daily_digest_html
from app.config import settings

logger = logging.getLogger(__name__)

CITTAA_GREEN = "#2EC4B6"
CITTAA_DARK = "#1a1a2e"

PLATFORM_COLORS = {
    "linkedin": "#0077B5",
    "twitter": "#1DA1F2",
    "instagram": "#E1306C",
    "youtube": "#FF0000",
    "news": "#FF6B35",
    "blog": "#6C63FF",
    "press_release": "#F7B731"
}

PLATFORM_ICONS = {
    "linkedin": "in",
    "twitter": "𝕏",
    "instagram": "📸",
    "youtube": "▶",
    "news": "📰",
    "blog": "✍",
    "press_release": "📣"
}

IMPORTANCE_COLORS = {
    "critical": "#FF4757",
    "high": "#FF6B35",
    "medium": "#FFA502",
    "low": "#2ED573"
}


def _build_email_html(title: str, subtitle: str, ai_summary: str, posts: list, insights: list) -> str:
    """Build beautiful HTML email"""

    # Build post cards
    post_cards = ""
    for post in posts[:15]:
        platform = post.platform if hasattr(post, 'platform') else post.get('platform', 'news')
        color = PLATFORM_COLORS.get(platform, "#888")
        icon = PLATFORM_ICONS.get(platform, "📌")
        competitor = post.competitor_name if hasattr(post, 'competitor_name') else post.get('competitor_name', '')
        post_title = (post.title or post.content or '')[:80] if hasattr(post, 'title') else post.get('title', post.get('content', ''))[:80]
        summary = (post.ai_summary or post.content or '')[:200] if hasattr(post, 'ai_summary') else post.get('ai_summary', post.get('content', ''))[:200]
        url = post.url if hasattr(post, 'url') else post.get('url', '#')
        score = post.ai_importance_score if hasattr(post, 'ai_importance_score') else post.get('ai_importance_score', 5.0)
        tags = post.ai_tags if hasattr(post, 'ai_tags') else post.get('ai_tags', [])
        tags_html = " ".join([f'<span style="background:{CITTAA_GREEN};color:white;padding:2px 8px;border-radius:10px;font-size:11px;margin-right:4px;">{t}</span>' for t in (tags or [])[:3]])

        post_cards += f"""
        <div style="background:white;border-radius:12px;padding:16px;margin-bottom:12px;border-left:4px solid {color};box-shadow:0 2px 8px rgba(0,0,0,0.06);">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <span style="background:{color};color:white;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600;">{icon} {platform.upper()}</span>
                <span style="color:#666;font-size:12px;font-weight:600;">{competitor} &nbsp;·&nbsp; Score: {score:.1f}/10</span>
            </div>
            <p style="margin:0 0 6px 0;font-weight:600;font-size:14px;color:{CITTAA_DARK};">{post_title}</p>
            <p style="margin:0 0 10px 0;font-size:13px;color:#555;line-height:1.5;">{summary}...</p>
            {tags_html}
            <a href="{url}" style="display:inline-block;margin-top:10px;color:{CITTAA_GREEN};font-size:12px;text-decoration:none;font-weight:600;">View Post →</a>
        </div>
        """

    # Build insight cards
    insight_cards = ""
    for insight in insights[:5]:
        ins_type = insight.insight_type if hasattr(insight, 'insight_type') else insight.get('insight_type', 'trend')
        ins_title = insight.title if hasattr(insight, 'title') else insight.get('title', '')
        ins_content = insight.content if hasattr(insight, 'content') else insight.get('content', '')
        importance = insight.importance if hasattr(insight, 'importance') else insight.get('importance', 'medium')
        imp_color = IMPORTANCE_COLORS.get(importance, "#FFA502")
        type_emoji = {"trend": "📈", "threat": "⚠️", "opportunity": "💡", "alert": "🚨"}.get(ins_type, "📌")

        insight_cards += f"""
        <div style="background:white;border-radius:12px;padding:16px;margin-bottom:12px;border-left:4px solid {imp_color};box-shadow:0 2px 8px rgba(0,0,0,0.06);">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <span style="font-weight:700;font-size:13px;color:{CITTAA_DARK};">{type_emoji} {ins_type.upper()}</span>
                <span style="background:{imp_color};color:white;padding:2px 10px;border-radius:10px;font-size:11px;font-weight:600;">{importance.upper()}</span>
            </div>
            <p style="margin:0 0 6px 0;font-weight:600;font-size:14px;color:{CITTAA_DARK};">{ins_title}</p>
            <p style="margin:0;font-size:13px;color:#555;line-height:1.5;">{ins_content[:300]}</p>
        </div>
        """

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f0f4f8;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f4f8;padding:24px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">

  <!-- Header -->
  <tr><td style="background:linear-gradient(135deg,{CITTAA_DARK} 0%,#16213e 100%);border-radius:16px 16px 0 0;padding:32px 32px 24px;">
    <h1 style="margin:0;color:white;font-size:28px;font-weight:800;font-family:'Georgia',serif;">
      <span style="color:{CITTAA_GREEN};">Cittaa</span> Intel
    </h1>
    <p style="margin:6px 0 0;color:#aaa;font-size:14px;">{subtitle}</p>
    <p style="margin:4px 0 0;color:#666;font-size:12px;">{datetime.now(timezone.utc).strftime('%B %d, %Y')}</p>
  </td></tr>

  <!-- AI Summary -->
  <tr><td style="background:{CITTAA_GREEN};padding:20px 32px;">
    <p style="margin:0;color:white;font-size:13px;font-weight:600;letter-spacing:0.5px;text-transform:uppercase;">🤖 AI Executive Summary</p>
    <p style="margin:8px 0 0;color:white;font-size:14px;line-height:1.7;opacity:0.95;">{ai_summary}</p>
  </td></tr>

  <!-- Body -->
  <tr><td style="background:#f8fafc;padding:24px 32px;">

    <!-- Insights -->
    {"<h2 style='margin:0 0 16px;font-size:16px;color:" + CITTAA_DARK + ";font-weight:700;'>⚡ Strategic Insights</h2>" + insight_cards if insight_cards else ""}

    <!-- Posts -->
    <h2 style="margin:20px 0 16px;font-size:16px;color:{CITTAA_DARK};font-weight:700;">🔍 Latest Competitor Activity</h2>
    {post_cards if post_cards else '<p style="color:#888;font-size:14px;">No new posts found in this period.</p>'}

  </td></tr>

  <!-- Footer -->
  <tr><td style="background:{CITTAA_DARK};border-radius:0 0 16px 16px;padding:20px 32px;text-align:center;">
    <p style="margin:0;color:#888;font-size:12px;">
      Powered by <strong style="color:{CITTAA_GREEN};">Cittaa Intel</strong> · AI by Google Gemini<br>
      <a href="#" style="color:{CITTAA_GREEN};text-decoration:none;">View Dashboard</a> &nbsp;·&nbsp;
      <a href="mailto:sairam@cittaa.in" style="color:#888;text-decoration:none;">sairam@cittaa.in</a>
    </p>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>
"""


def _send_email(to_addresses: List[str], subject: str, html_body: str):
    """Send email via SMTP"""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP not configured. Email not sent.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Cittaa Intel <{settings.SMTP_USER}>"
        msg["To"] = ", ".join(to_addresses)
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, to_addresses, msg.as_string())

        logger.info(f"Email sent to {to_addresses}")
        return True
    except Exception as e:
        logger.error(f"Email sending failed: {e}")
        return False


async def send_daily_digest_email():
    """Build and send daily digest"""
    async with AsyncSessionLocal() as db:
        yesterday = datetime.now(timezone.utc) - timedelta(hours=24)

        posts_result = await db.execute(
            select(Post)
            .where(Post.scraped_at >= yesterday)
            .order_by(Post.ai_importance_score.desc())
            .limit(20)
        )
        posts = posts_result.scalars().all()

        insights_result = await db.execute(
            select(Insight)
            .where(Insight.generated_at >= yesterday)
            .order_by(Insight.importance.desc())
            .limit(5)
        )
        insights = insights_result.scalars().all()

        posts_dicts = [{"platform": p.platform, "competitor_name": p.competitor_name,
                        "ai_summary": p.ai_summary, "content": p.content} for p in posts]
        insights_dicts = [{"title": i.title} for i in insights]

        ai_summary = await generate_daily_digest_html(posts_dicts, insights_dicts)

        html = _build_email_html(
            title="Daily Competitor Intel",
            subtitle=f"Daily Intelligence Report · {len(posts)} updates across {len(set(p.competitor_name for p in posts))} competitors",
            ai_summary=ai_summary or "Monitoring complete. Check your dashboard for the latest competitor updates.",
            posts=posts,
            insights=insights
        )

        recipients = [r.strip() for r in settings.DIGEST_RECIPIENTS.split(",")]
        today = datetime.now(timezone.utc).strftime("%b %d")
        _send_email(recipients, f"🔍 Cittaa Daily Intel — {today}", html)


async def send_weekly_digest(posts: list, weekly_data: dict):
    """Build and send weekly digest"""
    summary = weekly_data.get("executive_summary", "Weekly competitive intelligence report complete.")
    insights_list = []

    for trend in weekly_data.get("key_trends", [])[:3]:
        insights_list.append({"insight_type": "trend", "title": str(trend), "content": str(trend), "importance": "medium"})
    for threat in weekly_data.get("threats", [])[:2]:
        insights_list.append({"insight_type": "threat", "title": str(threat), "content": str(threat), "importance": "high"})
    for opp in weekly_data.get("opportunities", [])[:2]:
        insights_list.append({"insight_type": "opportunity", "title": str(opp), "content": str(opp), "importance": "high"})

    html = _build_email_html(
        title="Weekly Competitor Intel",
        subtitle=f"Weekly Strategic Report · {len(posts)} posts analyzed",
        ai_summary=summary,
        posts=posts[:10],
        insights=insights_list
    )

    recipients = [r.strip() for r in settings.DIGEST_RECIPIENTS.split(",")]
    week = datetime.now(timezone.utc).strftime("Week of %b %d")
    _send_email(recipients, f"📊 Cittaa Weekly Intel — {week}", html)
