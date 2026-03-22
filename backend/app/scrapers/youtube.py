"""
YouTube scraper - Uses YouTube Data API v3 + public RSS feeds
"""
import httpx
import feedparser
import logging
from datetime import datetime, timezone
from typing import List, Dict
import hashlib
from app.config import settings

logger = logging.getLogger(__name__)


async def scrape_youtube(competitor: dict) -> List[Dict]:
    """Scrape YouTube channel videos"""
    posts = []
    channel = competitor.get("youtube_channel", "")
    if not channel:
        return posts

    # Try YouTube RSS (no API key needed)
    try:
        rss_posts = await _scrape_youtube_rss(channel, competitor)
        posts.extend(rss_posts)
    except Exception as e:
        logger.warning(f"YouTube RSS failed for {competitor['name']}: {e}")

    # YouTube API v3 (if key available)
    if settings.YOUTUBE_API_KEY and not posts:
        try:
            api_posts = await _scrape_youtube_api(channel, competitor)
            posts.extend(api_posts)
        except Exception as e:
            logger.warning(f"YouTube API failed for {competitor['name']}: {e}")

    return posts


async def _scrape_youtube_rss(channel_name: str, competitor: dict) -> List[Dict]:
    """Scrape YouTube channel via RSS - requires channel ID"""
    posts = []

    # First try to get channel ID from channel name
    channel_id = await _get_channel_id(channel_name)
    if not channel_id:
        return posts

    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(rss_url)
        if response.status_code != 200:
            return posts

        feed = feedparser.parse(response.text)
        for entry in feed.entries[:10]:
            content = entry.get("summary", "") or entry.get("media_description", "")
            video_id = entry.get("yt_videoid", "")
            post_id = video_id or hashlib.md5(entry.get("link", "").encode()).hexdigest()

            pub_date = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

            # Get thumbnail
            media = entry.get("media_thumbnail", [{}])
            image_url = media[0].get("url", "") if media else ""

            # Extract view/like counts if available
            stats = entry.get("media_starrating", {})

            posts.append({
                "competitor_id": competitor.get("id"),
                "competitor_name": competitor["name"],
                "platform": "youtube",
                "post_id": f"yt_{post_id}",
                "author_name": feed.feed.get("title", competitor["name"]),
                "author_type": "company",
                "title": entry.get("title", ""),
                "content": content[:1000],
                "url": f"https://youtube.com/watch?v={video_id}" if video_id else entry.get("link", ""),
                "image_url": image_url,
                "published_at": pub_date
            })

    return posts


async def _get_channel_id(channel_name: str) -> str:
    """Try to resolve channel ID from channel name"""
    url = f"https://www.youtube.com/@{channel_name}"
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
            })
            if response.status_code == 200:
                import re
                # Extract channel ID from page
                match = re.search(r'"channelId":"(UC[a-zA-Z0-9_-]{22})"', response.text)
                if match:
                    return match.group(1)
                # Also try externalId
                match = re.search(r'"externalId":"(UC[a-zA-Z0-9_-]{22})"', response.text)
                if match:
                    return match.group(1)
    except Exception as e:
        logger.warning(f"Could not resolve YouTube channel ID for {channel_name}: {e}")
    return ""


async def _scrape_youtube_api(channel_name: str, competitor: dict) -> List[Dict]:
    """Scrape via YouTube Data API v3"""
    posts = []
    api_key = settings.YOUTUBE_API_KEY

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Search for channel
        search_resp = await client.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "q": channel_name,
                "type": "channel",
                "key": api_key,
                "maxResults": 1
            }
        )
        items = search_resp.json().get("items", [])
        if not items:
            return posts

        channel_id = items[0].get("id", {}).get("channelId", "")
        if not channel_id:
            return posts

        # Get recent videos
        videos_resp = await client.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "channelId": channel_id,
                "type": "video",
                "order": "date",
                "maxResults": 10,
                "key": api_key
            }
        )

        for item in videos_resp.json().get("items", []):
            snippet = item.get("snippet", {})
            video_id = item.get("id", {}).get("videoId", "")
            pub_date = None
            if snippet.get("publishedAt"):
                pub_date = datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00"))

            posts.append({
                "competitor_id": competitor.get("id"),
                "competitor_name": competitor["name"],
                "platform": "youtube",
                "post_id": f"yt_api_{video_id}",
                "author_name": snippet.get("channelTitle", competitor["name"]),
                "author_type": "company",
                "title": snippet.get("title", ""),
                "content": snippet.get("description", "")[:500],
                "url": f"https://youtube.com/watch?v={video_id}",
                "image_url": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                "published_at": pub_date
            })

    return posts
