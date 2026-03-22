"""
LinkedIn scraper - scrapes public company pages & uses search for employee posts.
Note: LinkedIn heavily restricts scraping. This uses public endpoints only.
For production, consider using Proxycurl API (paid) or PhantomBuster.
"""
import httpx
import logging
from datetime import datetime, timezone
from typing import List, Dict
from bs4 import BeautifulSoup
import hashlib
import asyncio

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

async def scrape_linkedin(competitor: dict) -> List[Dict]:
    """
    Scrape LinkedIn company page posts.
    Uses public RSS/JSON endpoints where available.
    """
    posts = []
    slug = competitor.get("linkedin_slug", "")
    if not slug:
        return posts

    # Try public LinkedIn company feed via unofficial endpoint
    try:
        company_posts = await _scrape_company_page(slug, competitor)
        posts.extend(company_posts)
    except Exception as e:
        logger.warning(f"LinkedIn company scrape failed for {competitor['name']}: {e}")

    # Use Google News RSS as a proxy for LinkedIn mentions
    try:
        linkedin_news = await _search_linkedin_via_google(competitor)
        posts.extend(linkedin_news)
    except Exception as e:
        logger.warning(f"LinkedIn Google search failed for {competitor['name']}: {e}")

    return posts


async def _scrape_company_page(slug: str, competitor: dict) -> List[Dict]:
    """Attempt to scrape public LinkedIn company page"""
    posts = []
    url = f"https://www.linkedin.com/company/{slug}/posts/"

    try:
        async with httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=True,
            headers=HEADERS
        ) as client:
            response = await client.get(url)

            if response.status_code != 200:
                logger.warning(f"LinkedIn returned {response.status_code} for {slug}")
                return posts

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract structured data if available
            scripts = soup.find_all("script", type="application/ld+json")
            for script in scripts:
                try:
                    import json
                    data = json.loads(script.string or "")
                    if isinstance(data, dict) and data.get("@type") == "Organization":
                        description = data.get("description", "")
                        if description:
                            post_id = hashlib.md5(f"li_{slug}_org".encode()).hexdigest()
                            posts.append({
                                "competitor_id": competitor.get("id"),
                                "competitor_name": competitor["name"],
                                "platform": "linkedin",
                                "post_id": f"li_{post_id}",
                                "author_name": competitor["name"],
                                "author_type": "company",
                                "title": f"{competitor['name']} - Company Overview",
                                "content": description,
                                "url": url,
                                "published_at": datetime.now(timezone.utc)
                            })
                except Exception:
                    pass

            # Try to extract post content from page
            post_elements = soup.find_all("div", {"class": lambda x: x and "feed-shared-update" in str(x)})
            for elem in post_elements[:10]:
                text = elem.get_text(separator=" ", strip=True)
                if len(text) > 50:
                    post_id = hashlib.md5(text[:100].encode()).hexdigest()
                    posts.append({
                        "competitor_id": competitor.get("id"),
                        "competitor_name": competitor["name"],
                        "platform": "linkedin",
                        "post_id": f"li_{post_id}",
                        "author_name": competitor["name"],
                        "author_type": "company",
                        "content": text[:1000],
                        "url": url,
                        "published_at": datetime.now(timezone.utc)
                    })

    except Exception as e:
        logger.error(f"LinkedIn scrape error: {e}")

    return posts


async def _search_linkedin_via_google(competitor: dict) -> List[Dict]:
    """Use Google to find recent LinkedIn posts from the competitor"""
    import feedparser

    query = f'site:linkedin.com "{competitor["name"]}" mental health'
    rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en&gl=IN"

    posts = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(rss_url)
            feed = feedparser.parse(response.text)

            for entry in feed.entries[:5]:
                if "linkedin.com" in entry.get("link", ""):
                    content = entry.get("summary", "") or entry.get("description", "")
                    soup = BeautifulSoup(content, "html.parser")
                    content = soup.get_text(separator=" ", strip=True)

                    post_id = hashlib.md5(entry.get("link", "").encode()).hexdigest()
                    posts.append({
                        "competitor_id": competitor.get("id"),
                        "competitor_name": competitor["name"],
                        "platform": "linkedin",
                        "post_id": f"li_g_{post_id}",
                        "author_name": competitor["name"],
                        "author_type": "company",
                        "title": entry.get("title", ""),
                        "content": content,
                        "url": entry.get("link", ""),
                        "published_at": datetime.now(timezone.utc)
                    })
    except Exception as e:
        logger.error(f"Google LinkedIn search error: {e}")

    return posts
