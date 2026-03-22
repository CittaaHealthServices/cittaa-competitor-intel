"""
News & Blog scraper - Uses NewsAPI + Google News RSS + direct website scraping
"""
import feedparser
import httpx
import logging
from datetime import datetime, timezone
from typing import List, Dict
from bs4 import BeautifulSoup
import hashlib

logger = logging.getLogger(__name__)

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

async def scrape_news(competitor: dict) -> List[Dict]:
    """Scrape news articles from Google News RSS and NewsAPI"""
    posts = []
    keywords = competitor.get("news_keywords", [competitor["name"]])

    for keyword in keywords[:3]:  # Limit to avoid rate limiting
        try:
            rss_posts = await _scrape_google_news(keyword, competitor)
            posts.extend(rss_posts)
        except Exception as e:
            logger.error(f"Google News RSS error for {competitor['name']}: {e}")

    return _deduplicate(posts)


async def _scrape_google_news(keyword: str, competitor: dict) -> List[Dict]:
    """Scrape Google News RSS feed"""
    url = GOOGLE_NEWS_RSS.format(query=keyword.replace(" ", "+"))
    posts = []

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; CittaaBot/1.0)"
            })
            feed = feedparser.parse(response.text)

            for entry in feed.entries[:10]:
                content = entry.get("summary", "") or entry.get("description", "")
                # Clean HTML from content
                if content:
                    soup = BeautifulSoup(content, "html.parser")
                    content = soup.get_text(separator=" ", strip=True)

                post_id = hashlib.md5(entry.get("link", "").encode()).hexdigest()
                pub_date = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    import time
                    pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

                posts.append({
                    "competitor_id": competitor.get("id"),
                    "competitor_name": competitor["name"],
                    "platform": "news",
                    "post_id": f"news_{post_id}",
                    "author_name": entry.get("source", {}).get("title", "News Source") if hasattr(entry.get("source", {}), "get") else "News Source",
                    "author_type": "media",
                    "title": entry.get("title", ""),
                    "content": content,
                    "url": entry.get("link", ""),
                    "published_at": pub_date
                })
    except Exception as e:
        logger.error(f"RSS fetch error: {e}")

    return posts


async def scrape_blog(competitor: dict) -> List[Dict]:
    """Try to scrape competitor blog RSS feeds"""
    posts = []
    website = competitor.get("website", "")
    if not website:
        return posts

    blog_rss_patterns = [
        f"{website}/feed",
        f"{website}/rss",
        f"{website}/blog/feed",
        f"{website}/blog/rss.xml",
        f"{website}/rss.xml"
    ]

    for rss_url in blog_rss_patterns:
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(rss_url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; CittaaBot/1.0)"
                })
                if response.status_code == 200 and ("xml" in response.headers.get("content-type", "") or "rss" in response.text[:200].lower()):
                    feed = feedparser.parse(response.text)
                    for entry in feed.entries[:5]:
                        content = entry.get("content", [{}])[0].get("value", "") if entry.get("content") else entry.get("summary", "")
                        if content:
                            soup = BeautifulSoup(content, "html.parser")
                            content = soup.get_text(separator=" ", strip=True)[:1000]

                        post_id = hashlib.md5(entry.get("link", "").encode()).hexdigest()
                        pub_date = None
                        if hasattr(entry, "published_parsed") and entry.published_parsed:
                            pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

                        posts.append({
                            "competitor_id": competitor.get("id"),
                            "competitor_name": competitor["name"],
                            "platform": "blog",
                            "post_id": f"blog_{post_id}",
                            "author_name": competitor["name"],
                            "author_type": "company",
                            "title": entry.get("title", ""),
                            "content": content,
                            "url": entry.get("link", ""),
                            "published_at": pub_date
                        })
                    if posts:
                        break
        except Exception:
            continue

    return posts


def _deduplicate(posts: List[Dict]) -> List[Dict]:
    seen = set()
    unique = []
    for post in posts:
        key = post.get("post_id", post.get("url", ""))
        if key and key not in seen:
            seen.add(key)
            unique.append(post)
    return unique
