"""
Funding & Company Intelligence — tracks funding rounds, valuations, investors.
Funding = war chest for growth. Know when competitors raise → they'll spend on ads,
hiring, and new features in the next 6-12 months.
"""
import httpx
import feedparser
import logging
import hashlib
import re
from datetime import datetime, timezone
from typing import List, Dict
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Known Crunchbase slugs
CRUNCHBASE_SLUGS = {
    "YourDOST":   "yourdost",
    "Wysa":       "wysa",
    "InnerHour":  "the-innerhour",
    "MindPeers":  "mindpeers",
    "HeartItOut": "heart-it-out",
    "Lissun":     "lissun",
    "Talkspace":  "talkspace",
    "BetterHelp": "betterhelp",
    "Headspace":  "headspace",
    "Calm":       "calm",
    "Cittaa":     "cittaa",
}

# Known funding data (as fallback if scraping fails)
KNOWN_FUNDING = {
    "YourDOST":   {"total": "$4M", "last_round": "Series A", "year": 2017},
    "Wysa":       {"total": "$20M", "last_round": "Series B", "year": 2022},
    "InnerHour":  {"total": "Undisclosed", "last_round": "Seed", "year": 2019},
    "MindPeers":  {"total": "$1.2M", "last_round": "Seed", "year": 2022},
    "Talkspace":  {"total": "$110M+", "last_round": "NASDAQ Listed", "year": 2021},
    "BetterHelp": {"total": "Part of Teladoc ($18.5B acq.)", "last_round": "Acquired", "year": 2015},
    "Headspace":  {"total": "$400M+", "last_round": "Series C", "year": 2021},
    "Calm":       {"total": "$218M", "last_round": "Series B", "year": 2020},
}


async def scrape_funding(competitor: dict) -> List[Dict]:
    """Scrape funding & company intelligence from Crunchbase + news."""
    posts = []
    name = competitor["name"]

    # 1. Try Crunchbase public page
    try:
        cb_posts = await _scrape_crunchbase(name, competitor)
        posts.extend(cb_posts)
    except Exception as e:
        logger.warning(f"Crunchbase scrape failed for {name}: {e}")

    # 2. Search funding news via Google News
    try:
        news_posts = await _search_funding_news(name, competitor)
        posts.extend(news_posts)
    except Exception as e:
        logger.warning(f"Funding news search failed for {name}: {e}")

    # 3. Use known funding data as a baseline post
    if not posts and name in KNOWN_FUNDING:
        fund = KNOWN_FUNDING[name]
        post_id = hashlib.md5(f"funding_known_{name}".encode()).hexdigest()
        posts.append({
            "competitor_id": competitor.get("id"),
            "competitor_name": name,
            "platform": "funding",
            "post_id": f"fund_{post_id}",
            "author_name": "Crunchbase",
            "author_type": "media",
            "title": f"💰 Funding Profile: {name}",
            "content": (
                f"{name} has raised {fund['total']} in funding. "
                f"Last known round: {fund['last_round']} ({fund['year']}). "
                f"With this war chest, expect continued investment in product, hiring, and marketing."
            ),
            "url": f"https://crunchbase.com/organization/{CRUNCHBASE_SLUGS.get(name, name.lower())}",
            "published_at": datetime.now(timezone.utc),
        })

    return posts


async def _scrape_crunchbase(name: str, competitor: dict) -> List[Dict]:
    """Scrape Crunchbase public organization page."""
    posts = []
    slug = CRUNCHBASE_SLUGS.get(name, name.lower().replace(" ", "-"))
    url = f"https://www.crunchbase.com/organization/{slug}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code not in (200, 301, 302):
            return posts

        text = resp.text

        # Extract funding total
        funding_match = re.search(r'Total Funding Amount.*?\$?([\d,\.]+[MBK]?)', text, re.DOTALL | re.IGNORECASE)
        employees_match = re.search(r'(\d+[-–]\d+|\d+,\d+|\d+)\s+employees', text, re.IGNORECASE)
        founded_match = re.search(r'Founded.*?(\d{4})', text, re.DOTALL)
        last_round_match = re.search(r'(Series [A-Z]|Seed|Pre-Seed|Series A|Series B|Series C|IPO|Acquired)', text)

        content_parts = [f"{name} company intelligence from Crunchbase."]
        if funding_match:
            content_parts.append(f"Total funding: ${funding_match.group(1)}.")
        if last_round_match:
            content_parts.append(f"Last round: {last_round_match.group(1)}.")
        if employees_match:
            content_parts.append(f"Team size: {employees_match.group(1)} employees.")
        if founded_match:
            content_parts.append(f"Founded: {founded_match.group(1)}.")

        if len(content_parts) > 1:
            post_id = hashlib.md5(f"cb_{name}".encode()).hexdigest()
            posts.append({
                "competitor_id": competitor.get("id"),
                "competitor_name": name,
                "platform": "funding",
                "post_id": f"cb_{post_id}",
                "author_name": "Crunchbase",
                "author_type": "media",
                "title": f"💰 Company Profile: {name}",
                "content": " ".join(content_parts),
                "url": url,
                "published_at": datetime.now(timezone.utc),
            })

    return posts


async def _search_funding_news(name: str, competitor: dict) -> List[Dict]:
    """Search Google News for funding announcements."""
    queries = [
        f'"{name}" funding raised million',
        f'"{name}" series investment',
        f'"{name}" acquires acquired merger',
    ]
    posts = []

    for query in queries:
        rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-IN&gl=IN"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(rss_url, headers={"User-Agent": "Mozilla/5.0 (compatible; FeedBot/1.0)"})
                feed = feedparser.parse(resp.text)

                for entry in feed.entries[:3]:
                    title = entry.get("title", "")
                    if not any(kw in title.lower() for kw in ["fund", "raise", "million", "invest", "acqui", "series"]):
                        continue

                    content = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(strip=True)
                    link = entry.get("link", "")
                    post_id = hashlib.md5(link.encode()).hexdigest()

                    pub_date = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

                    posts.append({
                        "competitor_id": competitor.get("id"),
                        "competitor_name": name,
                        "platform": "funding",
                        "post_id": f"fund_news_{post_id}",
                        "author_name": entry.get("source", {}).get("title", "News") if isinstance(entry.get("source"), dict) else "News",
                        "author_type": "media",
                        "title": f"💰 {title}",
                        "content": content,
                        "url": link,
                        "published_at": pub_date or datetime.now(timezone.utc),
                    })
        except Exception:
            continue

    return posts
