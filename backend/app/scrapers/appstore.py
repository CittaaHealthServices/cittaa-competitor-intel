"""
App Store Intelligence — Google Play Store + Apple App Store
Fetches ratings, review counts, recent user reviews, and app metadata.
No API key needed — uses public endpoints.
"""
import httpx
import logging
import hashlib
import re
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Known app IDs for competitors (Google Play package names)
GOOGLE_PLAY_IDS = {
    "YourDOST":   "com.yourdost.app",
    "Wysa":       "bot.touchkin",
    "Amaha":      "com.theinnerhour",   # InnerHour rebranded to Amaha
    "MindPeers":  "com.mindpeers.app",
    "HeartItOut": "com.heartitout.app",
    "Lissun":     "com.lissun.app",
    "Talkspace":  "com.talkspace.talkspaceapp",
    "BetterHelp": "com.betterhelp",
    "Headspace":  "com.getsomeheadspace.android",
    "Calm":       "com.calm.android",
    "Cittaa":           "in.cittaa.app",
    "Silver Oak Health": "com.silveroakhealth.ewap",
}

# Apple App Store IDs
APPLE_APP_IDS = {
    "YourDOST":   "1037348913",
    "Wysa":       "1166585565",
    "Amaha":      "1118436464",         # InnerHour / Amaha app
    "Headspace":  "493145008",
    "Calm":       "571800810",
    "Talkspace":  "661829386",
    "BetterHelp":        "968289966",
    "Silver Oak Health": "1536714073",
}


async def scrape_appstore_intel(competitor: dict) -> Dict:
    """Fetch app store intelligence for a competitor. Returns structured dict."""
    name = competitor["name"]
    intel = {
        "competitor_name": name,
        "google_play": None,
        "apple_store": None,
    }

    # Google Play
    gplay_id = GOOGLE_PLAY_IDS.get(name)
    if gplay_id:
        try:
            intel["google_play"] = await _fetch_google_play(gplay_id, name)
        except Exception as e:
            logger.warning(f"Google Play fetch failed for {name}: {e}")

    # Apple App Store
    apple_id = APPLE_APP_IDS.get(name)
    if apple_id:
        try:
            intel["apple_store"] = await _fetch_apple_store(apple_id, name)
        except Exception as e:
            logger.warning(f"Apple Store fetch failed for {name}: {e}")

    # If no hardcoded IDs, try to find the app via search
    if not intel["google_play"]:
        try:
            intel["google_play"] = await _search_google_play(name)
        except Exception as e:
            logger.warning(f"Google Play search failed for {name}: {e}")

    return intel


async def scrape_appstore_posts(competitor: dict) -> List[Dict]:
    """Return app store data as posts for the main feed."""
    posts = []
    intel = await scrape_appstore_intel(competitor)

    for store_key, store_data in [("google_play", intel.get("google_play")), ("apple_store", intel.get("apple_store"))]:
        if not store_data:
            continue

        platform_label = "Google Play" if store_key == "google_play" else "App Store"
        rating = store_data.get("rating", 0)
        reviews_count = store_data.get("reviews_count", 0)
        installs = store_data.get("installs", "")
        version = store_data.get("version", "")
        last_updated = store_data.get("last_updated", "")

        summary = (
            f"{competitor['name']} on {platform_label}: "
            f"Rating {rating}/5 from {reviews_count:,} reviews. "
            f"{f'Installs: {installs}. ' if installs else ''}"
            f"{f'Version: {version}. ' if version else ''}"
            f"{f'Last updated: {last_updated}.' if last_updated else ''}"
        )

        post_id = hashlib.md5(f"appstore_{store_key}_{competitor['name']}".encode()).hexdigest()
        posts.append({
            "competitor_id": competitor.get("id"),
            "competitor_name": competitor["name"],
            "platform": "appstore",
            "post_id": f"app_{post_id}",
            "author_name": platform_label,
            "author_type": "media",
            "title": f"{competitor['name']} — {platform_label} App Stats",
            "content": summary,
            "url": store_data.get("url", ""),
            "published_at": datetime.now(timezone.utc),
            "extra": store_data,  # full structured data
        })

        # Add top reviews as individual posts
        for review in store_data.get("top_reviews", [])[:3]:
            rev_id = hashlib.md5(review.get("id", review.get("text", ""))[:50].encode()).hexdigest()
            posts.append({
                "competitor_id": competitor.get("id"),
                "competitor_name": competitor["name"],
                "platform": "appstore",
                "post_id": f"rev_{rev_id}",
                "author_name": review.get("author", "User"),
                "author_type": "user_review",
                "title": f"User Review — {competitor['name']} ({platform_label})",
                "content": f"{'⭐' * int(review.get('rating', 5))} {review.get('text', '')}",
                "url": store_data.get("url", ""),
                "published_at": datetime.now(timezone.utc),
            })

    return posts


async def _fetch_google_play(package_id: str, name: str) -> Optional[Dict]:
    """Scrape Google Play Store page for app stats."""
    url = f"https://play.google.com/store/apps/details?id={package_id}&hl=en&gl=IN"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36",
        "Accept-Language": "en-IN,en;q=0.9",
    }

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract rating
        rating = None
        rating_el = soup.find("div", {"itemprop": "starRating"})
        if not rating_el:
            # Try aria-label pattern
            rating_match = re.search(r'Rated (\d+\.?\d*) stars', resp.text)
            if rating_match:
                rating = float(rating_match.group(1))

        # Extract from JSON-LD
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = json.loads(script.string or "")
                if data.get("@type") == "SoftwareApplication":
                    agg = data.get("aggregateRating", {})
                    return {
                        "package_id": package_id,
                        "rating": float(agg.get("ratingValue", 0)),
                        "reviews_count": int(str(agg.get("ratingCount", "0")).replace(",", "")),
                        "installs": data.get("interactionCount", ""),
                        "version": data.get("softwareVersion", ""),
                        "last_updated": data.get("dateModified", ""),
                        "description": data.get("description", "")[:500],
                        "url": url,
                        "top_reviews": await _fetch_google_play_reviews(package_id),
                    }
            except Exception:
                continue

        # Fallback: try to extract from page text
        rating_pattern = re.search(r'"(\d\.\d)" ratings', resp.text)
        installs_pattern = re.search(r'"(\d[\d,\+BKMT\.]+) downloads"', resp.text)

        return {
            "package_id": package_id,
            "rating": float(rating_pattern.group(1)) if rating_pattern else None,
            "reviews_count": 0,
            "installs": installs_pattern.group(1) if installs_pattern else "",
            "url": url,
            "top_reviews": [],
        }


async def _fetch_google_play_reviews(package_id: str) -> List[Dict]:
    """Fetch top reviews from Google Play."""
    reviews = []
    # Google Play reviews API (unofficial)
    url = "https://play.google.com/store/getreviews"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, data={
                "reviewType": "0",
                "pageNum": "0",
                "id": package_id,
                "reviewSortOrder": "4",  # Most helpful
                "hl": "en",
                "xhr": "1",
            }, headers={"Content-Type": "application/x-www-form-urlencoded"})

            if resp.status_code == 200:
                # Parse the response (it's a weird JSON format)
                text = resp.text.lstrip(")]}'\n")
                data = json.loads(text)
                review_list = data[0][2] if data and data[0] else []
                for r in review_list[:5]:
                    try:
                        reviews.append({
                            "id": r[0],
                            "author": r[1][0] if r[1] else "Anonymous",
                            "rating": r[2],
                            "text": r[4] if len(r) > 4 else "",
                            "date": r[5][0] if len(r) > 5 else "",
                        })
                    except Exception:
                        continue
    except Exception as e:
        logger.debug(f"Google Play reviews fetch failed: {e}")

    return reviews


async def _fetch_apple_store(app_id: str, name: str) -> Optional[Dict]:
    """Fetch app data from Apple App Store via iTunes API (free)."""
    url = f"https://itunes.apple.com/in/lookup?id={app_id}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            return None

        data = resp.json()
        results = data.get("results", [])
        if not results:
            return None

        app = results[0]
        return {
            "app_id": app_id,
            "rating": round(app.get("averageUserRating", 0), 1),
            "reviews_count": app.get("userRatingCount", 0),
            "version": app.get("version", ""),
            "last_updated": app.get("currentVersionReleaseDate", "")[:10],
            "installs": "",  # Not available on iOS
            "description": app.get("description", "")[:500],
            "url": app.get("trackViewUrl", ""),
            "price": app.get("formattedPrice", "Free"),
            "genres": app.get("genres", []),
            "top_reviews": [],
        }


async def _search_google_play(name: str) -> Optional[Dict]:
    """Search Google Play for the app if package ID not known."""
    query = f"{name} mental health"
    url = f"https://play.google.com/store/search?q={query.replace(' ', '+')}&c=apps&hl=en&gl=IN"
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Linux; Android 10) Chrome/120.0.0.0"
            })
            if resp.status_code != 200:
                return None

            # Extract first result's package ID
            match = re.search(r'/store/apps/details\?id=([\w\.]+)', resp.text)
            if match:
                package_id = match.group(1)
                return await _fetch_google_play(package_id, name)
    except Exception:
        pass
    return None
