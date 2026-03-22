"""
Deep Search scraper — performs Google searches for each competitor to find
press releases, funding news, product launches, job postings, interviews,
and any web content that RSS feeds might miss.

Uses:
  1. Google Custom Search JSON API (if GOOGLE_SEARCH_API_KEY + GOOGLE_SEARCH_CX set)
  2. Google News RSS (broad queries) as fallback
  3. DuckDuckGo search (always free) as second fallback
"""
import httpx
import feedparser
import logging
import hashlib
from datetime import datetime, timezone
from typing import List, Dict
from bs4 import BeautifulSoup
from app.config import settings

logger = logging.getLogger(__name__)

# Deep search query templates for each competitor
SEARCH_QUERIES = [
    '"{name}" funding raised',
    '"{name}" product launch new feature',
    '"{name}" partnership deal',
    '"{name}" hiring jobs',
    '"{name}" press release',
    '"{name}" mental health India',
    '"{name}" review user experience',
    '"{name}" CEO founder interview',
    '"{name}" award recognition',
    '"{name}" expansion growth',
]


async def scrape_deep_search(competitor: dict) -> List[Dict]:
    """Run multiple Google/DuckDuckGo queries for rich competitor intel."""
    posts = []
    name = competitor["name"]

    # Pick top 3 query templates to avoid too many requests
    queries = [q.format(name=name) for q in SEARCH_QUERIES[:4]]

    for query in queries:
        # Try Google Custom Search first
        if settings.GOOGLE_SEARCH_API_KEY and settings.GOOGLE_SEARCH_CX:
            try:
                results = await _google_custom_search(query, competitor)
                posts.extend(results)
                continue
            except Exception as e:
                logger.warning(f"Google Custom Search failed for '{query}': {e}")

        # Fallback: Google News RSS
        try:
            results = await _google_news_search(query, competitor)
            posts.extend(results)
        except Exception as e:
            logger.warning(f"Google News search failed for '{query}': {e}")

        # Second fallback: DuckDuckGo
        if not posts:
            try:
                results = await _duckduckgo_search(query, competitor)
                posts.extend(results)
            except Exception as e:
                logger.warning(f"DuckDuckGo search failed for '{query}': {e}")

    return _deduplicate(posts)


async def _google_custom_search(query: str, competitor: dict) -> List[Dict]:
    """Use Google Custom Search JSON API (requires API key + CX)"""
    posts = []
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": settings.GOOGLE_SEARCH_API_KEY,
        "cx": settings.GOOGLE_SEARCH_CX,
        "q": query,
        "num": 5,
        "dateRestrict": "m1",  # Last 1 month
        "lr": "lang_en",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
        if response.status_code != 200:
            return posts

        data = response.json()
        for item in data.get("items", []):
            post_id = hashlib.md5(item.get("link", "").encode()).hexdigest()
            snippet = item.get("snippet", "")
            title = item.get("title", "")

            # Fetch the actual page content for richer data
            content = snippet
            try:
                page_content = await _fetch_article_text(item.get("link", ""))
                if page_content:
                    content = page_content[:1500]
            except Exception:
                pass

            posts.append({
                "competitor_id": competitor.get("id"),
                "competitor_name": competitor["name"],
                "platform": "search",
                "post_id": f"gcs_{post_id}",
                "author_name": item.get("displayLink", "Web"),
                "author_type": "media",
                "title": title,
                "content": content,
                "url": item.get("link", ""),
                "published_at": None,
            })

    return posts


async def _google_news_search(query: str, competitor: dict) -> List[Dict]:
    """Use Google News RSS for search queries"""
    rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
    posts = []

    async with httpx.AsyncClient(timeout=12.0) as client:
        response = await client.get(rss_url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; CittaaBot/1.0)"
        })
        feed = feedparser.parse(response.text)

        for entry in feed.entries[:5]:
            content = entry.get("summary", "") or entry.get("description", "")
            soup = BeautifulSoup(content, "html.parser")
            content = soup.get_text(separator=" ", strip=True)

            post_id = hashlib.md5(entry.get("link", "").encode()).hexdigest()
            pub_date = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

            posts.append({
                "competitor_id": competitor.get("id"),
                "competitor_name": competitor["name"],
                "platform": "search",
                "post_id": f"gnr_{post_id}",
                "author_name": entry.get("source", {}).get("title", "News") if hasattr(entry.get("source", {}), "get") else "News",
                "author_type": "media",
                "title": entry.get("title", ""),
                "content": content,
                "url": entry.get("link", ""),
                "published_at": pub_date,
            })

    return posts


async def _duckduckgo_search(query: str, competitor: dict) -> List[Dict]:
    """Scrape DuckDuckGo search results (no API key needed)"""
    posts = []
    url = "https://html.duckduckgo.com/html/"

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        response = await client.post(url, data={"q": query, "kl": "in-en"}, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
            "Content-Type": "application/x-www-form-urlencoded",
        })
        if response.status_code != 200:
            return posts

        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.find_all("div", class_="result")

        for result in results[:5]:
            title_tag = result.find("a", class_="result__a")
            snippet_tag = result.find("a", class_="result__snippet")
            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            link = title_tag.get("href", "")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

            post_id = hashlib.md5(link.encode()).hexdigest()
            posts.append({
                "competitor_id": competitor.get("id"),
                "competitor_name": competitor["name"],
                "platform": "search",
                "post_id": f"ddg_{post_id}",
                "author_name": "Web Search",
                "author_type": "media",
                "title": title,
                "content": snippet,
                "url": link,
                "published_at": datetime.now(timezone.utc),
            })

    return posts


async def _fetch_article_text(url: str) -> str:
    """Fetch and extract clean text from an article URL"""
    if not url or not url.startswith("http"):
        return ""
    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; CittaaBot/1.0)"
            })
            if response.status_code != 200:
                return ""
            soup = BeautifulSoup(response.text, "html.parser")
            # Remove nav, footer, scripts
            for tag in soup(["nav", "footer", "script", "style", "aside", "header"]):
                tag.decompose()
            # Prefer article/main content
            article = soup.find("article") or soup.find("main") or soup.find("div", {"class": lambda x: x and "content" in str(x).lower()})
            if article:
                return article.get_text(separator=" ", strip=True)[:2000]
            return soup.get_text(separator=" ", strip=True)[:1500]
    except Exception:
        return ""


def _deduplicate(posts: List[Dict]) -> List[Dict]:
    seen = set()
    unique = []
    for post in posts:
        key = post.get("post_id", post.get("url", ""))
        if key and key not in seen:
            seen.add(key)
            unique.append(post)
    return unique
