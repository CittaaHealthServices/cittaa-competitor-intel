"""
Jobs & Hiring Intelligence — tracks what roles competitors are hiring for.
Hiring signals reveal strategy: hiring ML engineers = AI product coming,
hiring BD in schools = EdTech expansion, hiring therapists = scaling supply side.
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


async def scrape_jobs(competitor: dict) -> List[Dict]:
    """Scrape job postings for a competitor from multiple sources."""
    posts = []
    name = competitor["name"]

    sources = [
        _scrape_linkedin_jobs,
        _scrape_indeed_jobs,
        _scrape_naukri_jobs,
        _scrape_website_careers,
    ]

    for source_fn in sources:
        try:
            results = await source_fn(name, competitor)
            posts.extend(results)
        except Exception as e:
            logger.warning(f"Jobs scrape failed [{name}/{source_fn.__name__}]: {e}")

    return _deduplicate(posts)


async def _scrape_linkedin_jobs(name: str, competitor: dict) -> List[Dict]:
    """Search LinkedIn Jobs for open roles."""
    posts = []
    url = f"https://www.linkedin.com/jobs/search/?keywords={name.replace(' ', '+')}&location=India"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
        "Accept": "text/html,application/xhtml+xml",
    }
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            return posts

        soup = BeautifulSoup(resp.text, "html.parser")
        job_cards = soup.find_all("div", class_=re.compile("base-card"))

        for card in job_cards[:8]:
            title_el = card.find(["h3", "h4"], class_=re.compile("base-search-card__title"))
            location_el = card.find("span", class_=re.compile("job-search-card__location"))
            link_el = card.find("a", class_=re.compile("base-card__full-link"))

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            location = location_el.get_text(strip=True) if location_el else ""
            link = link_el.get("href", "") if link_el else url

            # Analyze what this hire signals strategically
            signal = _analyze_job_signal(title)

            post_id = hashlib.md5(f"job_li_{name}_{title}".encode()).hexdigest()
            posts.append({
                "competitor_id": competitor.get("id"),
                "competitor_name": name,
                "platform": "jobs",
                "post_id": f"job_li_{post_id}",
                "author_name": "LinkedIn Jobs",
                "author_type": "hiring",
                "title": f"🧑‍💼 Hiring: {title} — {name}",
                "content": f"{name} is hiring a {title}{f' in {location}' if location else ''}. {signal}",
                "url": link,
                "published_at": datetime.now(timezone.utc),
            })

    return posts


async def _scrape_indeed_jobs(name: str, competitor: dict) -> List[Dict]:
    """Search Indeed for open roles via RSS."""
    posts = []
    rss_url = f"https://in.indeed.com/rss?q={name.replace(' ', '+')}&l=India&sort=date"

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(rss_url, headers={"User-Agent": "Mozilla/5.0 (compatible; FeedBot/1.0)"})
        feed = feedparser.parse(resp.text)

        for entry in feed.entries[:8]:
            title = entry.get("title", "")
            if name.lower() not in title.lower() and name.lower() not in entry.get("summary", "").lower():
                continue

            signal = _analyze_job_signal(title)
            link = entry.get("link", "")
            post_id = hashlib.md5(link.encode()).hexdigest()

            pub_date = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

            posts.append({
                "competitor_id": competitor.get("id"),
                "competitor_name": name,
                "platform": "jobs",
                "post_id": f"job_in_{post_id}",
                "author_name": "Indeed",
                "author_type": "hiring",
                "title": f"🧑‍💼 Hiring: {title}",
                "content": f"{name} job opening: {title}. {signal}",
                "url": link,
                "published_at": pub_date or datetime.now(timezone.utc),
            })

    return posts


async def _scrape_naukri_jobs(name: str, competitor: dict) -> List[Dict]:
    """Search Naukri.com for open roles (India's top job board)."""
    posts = []
    url = f"https://www.naukri.com/{name.lower().replace(' ', '-')}-jobs"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        "Accept": "text/html,application/xhtml+xml",
    }
    async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            return posts

        soup = BeautifulSoup(resp.text, "html.parser")
        job_cards = soup.find_all("article", class_=re.compile("jobTuple"))

        for card in job_cards[:6]:
            title_el = card.find("a", class_=re.compile("title"))
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            link = title_el.get("href", url)
            signal = _analyze_job_signal(title)
            post_id = hashlib.md5(f"naukri_{name}_{title}".encode()).hexdigest()

            posts.append({
                "competitor_id": competitor.get("id"),
                "competitor_name": name,
                "platform": "jobs",
                "post_id": f"job_nk_{post_id}",
                "author_name": "Naukri",
                "author_type": "hiring",
                "title": f"🧑‍💼 Hiring: {title} — {name}",
                "content": f"{name} is hiring a {title}. {signal}",
                "url": link,
                "published_at": datetime.now(timezone.utc),
            })

    return posts


async def _scrape_website_careers(name: str, competitor: dict) -> List[Dict]:
    """Try to scrape the competitor's own careers page."""
    posts = []
    website = competitor.get("website", "")
    if not website:
        return posts

    careers_urls = [
        f"{website}/careers",
        f"{website}/jobs",
        f"{website}/about/careers",
        f"{website}/work-with-us",
    ]

    for careers_url in careers_urls:
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(careers_url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; CittaaBot/1.0)"
                })
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                # Look for job listings
                headings = soup.find_all(["h2", "h3", "h4", "li"], string=re.compile(
                    r"(engineer|developer|therapist|counselor|designer|manager|analyst|marketing|sales|ops|lead|senior|intern)",
                    re.IGNORECASE
                ))

                for h in headings[:5]:
                    title = h.get_text(strip=True)
                    if len(title) < 5 or len(title) > 100:
                        continue
                    signal = _analyze_job_signal(title)
                    post_id = hashlib.md5(f"careers_{name}_{title}".encode()).hexdigest()
                    posts.append({
                        "competitor_id": competitor.get("id"),
                        "competitor_name": name,
                        "platform": "jobs",
                        "post_id": f"job_web_{post_id}",
                        "author_name": f"{name} Careers",
                        "author_type": "hiring",
                        "title": f"🧑‍💼 Hiring: {title} — {name}",
                        "content": f"{name} is actively hiring: {title}. {signal}",
                        "url": careers_url,
                        "published_at": datetime.now(timezone.utc),
                    })

                if posts:
                    break
        except Exception:
            continue

    return posts


def _analyze_job_signal(title: str) -> str:
    """Translate a job title into a strategic signal for Cittaa."""
    title_lower = title.lower()
    signals = {
        ("machine learning", "ml engineer", "ai engineer", "nlp", "data scientist"):
            "🤖 Strategic Signal: Building AI/ML capabilities — likely developing AI-powered therapy features.",
        ("android", "ios", "mobile", "flutter", "react native"):
            "📱 Strategic Signal: Expanding mobile app — expect new mobile features soon.",
        ("school", "university", "campus", "student", "education"):
            "🎓 Strategic Signal: Targeting student/EdTech segment — direct competition with Cittaa's core market.",
        ("b2b", "enterprise", "corporate", "hr", "employee wellness"):
            "🏢 Strategic Signal: Expanding into corporate wellness — watch for B2B product launch.",
        ("therapist", "counsellor", "psychologist", "psychiatrist"):
            "🧠 Strategic Signal: Scaling therapist supply — preparing for growth in therapy sessions.",
        ("growth", "performance marketing", "seo", "content", "social media"):
            "📣 Strategic Signal: Investing in marketing — expect more aggressive user acquisition campaigns.",
        ("product manager", "product lead"):
            "🚀 Strategic Signal: Building product team — new features or vertical likely in pipeline.",
        ("partnerships", "business development", "bd"):
            "🤝 Strategic Signal: Pursuing partnerships — could be hospital networks, corporates, or insurers.",
        ("data", "analytics", "bi", "insights"):
            "📊 Strategic Signal: Investing in analytics — preparing for data-driven product decisions.",
        ("international", "global", "overseas"):
            "🌍 Strategic Signal: International expansion planned.",
    }

    for keywords, signal in signals.items():
        if any(k in title_lower for k in keywords):
            return signal

    return "📋 Active hiring — team is growing."


def _deduplicate(posts: List[Dict]) -> List[Dict]:
    seen = set()
    unique = []
    for post in posts:
        key = post.get("post_id", post.get("title", ""))
        if key and key not in seen:
            seen.add(key)
            unique.append(post)
    return unique
