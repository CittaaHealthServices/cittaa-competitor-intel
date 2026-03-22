"""
Twitter/X scraper - Uses Nitter RSS (public) as primary, Twitter API v2 as secondary
"""
import feedparser
import httpx
import logging
from datetime import datetime, timezone
from typing import List, Dict
import hashlib
from bs4 import BeautifulSoup
from app.config import settings

logger = logging.getLogger(__name__)

# Nitter instances (public Twitter proxies with RSS)
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.privacydev.net",
    "https://nitter.poast.org"
]


async def scrape_twitter(competitor: dict) -> List[Dict]:
    """Scrape Twitter/X activity via Nitter RSS or Twitter API"""
    posts = []
    handle = competitor.get("twitter_handle", "")
    if not handle:
        return posts

    handle = handle.lstrip("@")

    # Try Nitter RSS first (no auth required)
    for nitter_base in NITTER_INSTANCES:
        try:
            nitter_posts = await _scrape_nitter(handle, nitter_base, competitor)
            if nitter_posts:
                posts.extend(nitter_posts)
                break
        except Exception as e:
            logger.warning(f"Nitter {nitter_base} failed: {e}")
            continue

    # Fallback: Twitter API v2 Bearer token
    if not posts and settings.TWITTER_BEARER_TOKEN:
        try:
            api_posts = await _scrape_twitter_api(handle, competitor)
            posts.extend(api_posts)
        except Exception as e:
            logger.warning(f"Twitter API fallback failed: {e}")

    return posts


async def _scrape_nitter(handle: str, nitter_base: str, competitor: dict) -> List[Dict]:
    """Scrape via Nitter RSS feed"""
    rss_url = f"{nitter_base}/{handle}/rss"
    posts = []

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        response = await client.get(rss_url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; FeedBot/1.0)"
        })
        if response.status_code != 200:
            return posts

        feed = feedparser.parse(response.text)
        for entry in feed.entries[:15]:
            content = entry.get("description", "") or entry.get("summary", "")
            soup = BeautifulSoup(content, "html.parser")
            content = soup.get_text(separator=" ", strip=True)

            post_id = hashlib.md5(entry.get("link", "").encode()).hexdigest()
            pub_date = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

            # Detect retweets vs original
            author_type = "company" if handle.lower() in entry.get("author", "").lower() else "employee"
            if "RT @" in content:
                author_type = "retweet"

            posts.append({
                "competitor_id": competitor.get("id"),
                "competitor_name": competitor["name"],
                "platform": "twitter",
                "post_id": f"tw_{post_id}",
                "author_name": entry.get("author", handle),
                "author_type": author_type,
                "title": entry.get("title", "")[:200],
                "content": content[:1000],
                "url": entry.get("link", "").replace(nitter_base, "https://twitter.com"),
                "published_at": pub_date
            })

    return posts


async def _scrape_twitter_api(handle: str, competitor: dict) -> List[Dict]:
    """Scrape via Twitter API v2"""
    posts = []
    headers = {"Authorization": f"Bearer {settings.TWITTER_BEARER_TOKEN}"}

    # Get user ID first
    async with httpx.AsyncClient(timeout=10.0) as client:
        user_resp = await client.get(
            f"https://api.twitter.com/2/users/by/username/{handle}",
            headers=headers
        )
        if user_resp.status_code != 200:
            return posts

        user_id = user_resp.json().get("data", {}).get("id")
        if not user_id:
            return posts

        # Get recent tweets
        tweets_resp = await client.get(
            f"https://api.twitter.com/2/users/{user_id}/tweets",
            headers=headers,
            params={
                "max_results": 10,
                "tweet.fields": "created_at,public_metrics,text",
                "expansions": "author_id"
            }
        )
        if tweets_resp.status_code != 200:
            return posts

        for tweet in tweets_resp.json().get("data", []):
            metrics = tweet.get("public_metrics", {})
            post_id = tweet.get("id", "")
            pub_date = None
            if tweet.get("created_at"):
                pub_date = datetime.fromisoformat(tweet["created_at"].replace("Z", "+00:00"))

            posts.append({
                "competitor_id": competitor.get("id"),
                "competitor_name": competitor["name"],
                "platform": "twitter",
                "post_id": f"tw_api_{post_id}",
                "author_name": handle,
                "author_type": "company",
                "content": tweet.get("text", ""),
                "url": f"https://twitter.com/{handle}/status/{post_id}",
                "likes": metrics.get("like_count", 0),
                "comments": metrics.get("reply_count", 0),
                "shares": metrics.get("retweet_count", 0),
                "views": metrics.get("impression_count", 0),
                "published_at": pub_date
            })

    return posts
