"""
Instagram scraper - uses public profile pages + Google Image search RSS
"""
import httpx
import logging
from datetime import datetime, timezone
from typing import List, Dict
from bs4 import BeautifulSoup
import hashlib
import json
import re

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}


async def scrape_instagram(competitor: dict) -> List[Dict]:
    """Scrape Instagram public posts"""
    posts = []
    handle = competitor.get("instagram_handle", "")
    if not handle:
        return posts

    # Try public Instagram page
    try:
        ig_posts = await _scrape_public_profile(handle, competitor)
        posts.extend(ig_posts)
    except Exception as e:
        logger.warning(f"Instagram scrape failed for {competitor['name']}: {e}")

    # Fallback to Google News search for Instagram activity
    if not posts:
        try:
            news_posts = await _search_instagram_activity(competitor)
            posts.extend(news_posts)
        except Exception as e:
            logger.warning(f"Instagram news fallback failed: {e}")

    return posts


async def _scrape_public_profile(handle: str, competitor: dict) -> List[Dict]:
    """Attempt to scrape public Instagram profile"""
    posts = []
    url = f"https://www.instagram.com/{handle}/"

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=HEADERS) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return posts

            # Extract shared data from page scripts
            soup = BeautifulSoup(response.text, "html.parser")

            # Look for JSON-LD or meta tags
            og_description = soup.find("meta", property="og:description")
            og_image = soup.find("meta", property="og:image")
            title_tag = soup.find("meta", property="og:title")

            if og_description:
                content = og_description.get("content", "")
                post_id = hashlib.md5(f"ig_{handle}".encode()).hexdigest()
                posts.append({
                    "competitor_id": competitor.get("id"),
                    "competitor_name": competitor["name"],
                    "platform": "instagram",
                    "post_id": f"ig_profile_{post_id}",
                    "author_name": competitor["name"],
                    "author_type": "company",
                    "title": title_tag.get("content", f"{competitor['name']} on Instagram") if title_tag else f"{competitor['name']} on Instagram",
                    "content": content,
                    "url": url,
                    "image_url": og_image.get("content", "") if og_image else "",
                    "published_at": datetime.now(timezone.utc)
                })

            # Try to extract inline JSON data
            scripts = soup.find_all("script", type="text/javascript")
            for script in scripts:
                script_text = script.string or ""
                if "window.__additionalDataLoaded" in script_text or '"edge_owner_to_timeline_media"' in script_text:
                    try:
                        # Extract edges/posts
                        match = re.search(r'"edges":\s*(\[.*?\])', script_text, re.DOTALL)
                        if match:
                            edges = json.loads(match.group(1))
                            for edge in edges[:8]:
                                node = edge.get("node", {})
                                caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
                                caption = caption_edges[0].get("node", {}).get("text", "") if caption_edges else ""
                                shortcode = node.get("shortcode", "")
                                post_id = hashlib.md5(shortcode.encode()).hexdigest()
                                timestamp = node.get("taken_at_timestamp")
                                pub_date = datetime.fromtimestamp(timestamp, tz=timezone.utc) if timestamp else None

                                posts.append({
                                    "competitor_id": competitor.get("id"),
                                    "competitor_name": competitor["name"],
                                    "platform": "instagram",
                                    "post_id": f"ig_{post_id}",
                                    "author_name": competitor["name"],
                                    "author_type": "company",
                                    "content": caption[:1000],
                                    "url": f"https://www.instagram.com/p/{shortcode}/",
                                    "image_url": node.get("thumbnail_src", ""),
                                    "likes": node.get("edge_media_preview_like", {}).get("count", 0),
                                    "comments": node.get("edge_media_to_comment", {}).get("count", 0),
                                    "published_at": pub_date
                                })
                    except Exception:
                        pass

    except Exception as e:
        logger.error(f"Instagram profile scrape error: {e}")

    return posts


async def _search_instagram_activity(competitor: dict) -> List[Dict]:
    """Search Google News for Instagram activity"""
    import feedparser
    query = f'site:instagram.com "{competitor["name"]}"'
    rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en&gl=IN"
    posts = []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(rss_url)
            feed = feedparser.parse(response.text)

            for entry in feed.entries[:5]:
                if "instagram.com" in entry.get("link", ""):
                    content = entry.get("summary", "")
                    soup = BeautifulSoup(content, "html.parser")
                    content = soup.get_text(strip=True)
                    post_id = hashlib.md5(entry.get("link", "").encode()).hexdigest()

                    posts.append({
                        "competitor_id": competitor.get("id"),
                        "competitor_name": competitor["name"],
                        "platform": "instagram",
                        "post_id": f"ig_g_{post_id}",
                        "author_name": competitor["name"],
                        "author_type": "company",
                        "title": entry.get("title", ""),
                        "content": content,
                        "url": entry.get("link", ""),
                        "published_at": datetime.now(timezone.utc)
                    })
    except Exception as e:
        logger.error(f"Instagram Google search error: {e}")

    return posts
