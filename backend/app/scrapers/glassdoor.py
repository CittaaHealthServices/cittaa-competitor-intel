"""
Glassdoor + AmbitionBox Employee Intelligence
Scrapes employee reviews — current & former — to surface culture signals,
management quality, work-life balance, and exit patterns.

Data sources:
  • Glassdoor (global, English)
  • AmbitionBox (India-primary, very active for Indian startups)
  • Indeed (fallback)
"""
import httpx
import logging
import re
import json
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# AmbitionBox company slugs for Indian competitors
AMBITIONBOX_SLUGS = {
    "YourDOST":         "yourdost",
    "Wysa":             "wysa",
    "Amaha":            "amaha-health",
    "MindPeers":        "mindpeers",
    "HeartItOut":       "heart-it-out",
    "Lissun":           "lissun",
    "Silver Oak Health":"silver-oak-health",
    "Cittaa":           "cittaa",
}

# Glassdoor company slugs / search terms
GLASSDOOR_SLUGS = {
    "Wysa":             "Wysa-EI4_IE3298046",
    "YourDOST":         "YourDOST-EI4_IE2278847",
    "Amaha":            "InnerHour-EI4_IE2800680",
    "Talkspace":        "Talkspace-EI4_IE942887",
    "BetterHelp":       "BetterHelp-EI4_IE2069767",
    "Headspace":        "Headspace-EI4_IE1261359",
    "Calm":             "Calm-EI4_IE1791235",
}


async def scrape_employee_reviews(competitor: dict) -> Dict:
    """
    Main entry — returns structured employee intelligence dict.
    Includes: overall ratings, current vs former employee sentiment,
    top pros/cons, management score, culture highlights.
    """
    name = competitor["name"]
    result = {
        "competitor_name": name,
        "ambitionbox": None,
        "glassdoor": None,
        "overall_sentiment": "unknown",
        "key_pros": [],
        "key_cons": [],
        "current_employee_score": None,
        "former_employee_score": None,
        "culture_score": None,
        "management_score": None,
        "work_life_score": None,
        "growth_score": None,
        "employee_count_est": None,
        "reviews_summary": "",
        "exit_signals": [],       # patterns in why people leave
        "join_signals": [],       # why people join
        "red_flags": [],          # serious culture/mgmt issues
    }

    # Try AmbitionBox first (India-primary)
    ab_data = await _scrape_ambitionbox(name, competitor)
    if ab_data:
        result["ambitionbox"] = ab_data
        result["culture_score"] = ab_data.get("culture_rating")
        result["work_life_score"] = ab_data.get("work_life_rating")
        result["management_score"] = ab_data.get("management_rating")
        result["growth_score"] = ab_data.get("growth_rating")
        result["key_pros"].extend(ab_data.get("top_pros", []))
        result["key_cons"].extend(ab_data.get("top_cons", []))

    # Try Glassdoor
    gd_data = await _scrape_glassdoor(name, competitor)
    if gd_data:
        result["glassdoor"] = gd_data
        if not result["culture_score"]:
            result["culture_score"] = gd_data.get("culture_rating")
        if not result["work_life_score"]:
            result["work_life_score"] = gd_data.get("work_life_rating")
        result["key_pros"].extend(gd_data.get("top_pros", []))
        result["key_cons"].extend(gd_data.get("top_cons", []))

    # Deduplicate pros/cons
    result["key_pros"] = list(dict.fromkeys(result["key_pros"]))[:8]
    result["key_cons"] = list(dict.fromkeys(result["key_cons"]))[:8]

    # Derive overall sentiment
    overall_rating = None
    if ab_data and ab_data.get("overall_rating"):
        overall_rating = ab_data["overall_rating"]
    elif gd_data and gd_data.get("overall_rating"):
        overall_rating = gd_data["overall_rating"]

    if overall_rating:
        if overall_rating >= 4.0:
            result["overall_sentiment"] = "positive"
        elif overall_rating >= 3.0:
            result["overall_sentiment"] = "mixed"
        else:
            result["overall_sentiment"] = "negative"

    # Derive exit + join signals from cons/pros
    result["exit_signals"] = _extract_exit_signals(result["key_cons"])
    result["join_signals"] = _extract_join_signals(result["key_pros"])
    result["red_flags"] = _detect_red_flags(result["key_cons"], result.get("management_score"))

    return result


async def scrape_employee_review_posts(competitor: dict) -> List[Dict]:
    """Returns review data as posts for the main feed."""
    posts = []
    data = await scrape_employee_reviews(competitor)

    if not data.get("ambitionbox") and not data.get("glassdoor"):
        return posts

    # Summary post
    sources = []
    if data.get("ambitionbox"):
        ab = data["ambitionbox"]
        sources.append(f"AmbitionBox {ab.get('overall_rating', '?')}/5 ({ab.get('total_reviews', 0)} reviews)")
    if data.get("glassdoor"):
        gd = data["glassdoor"]
        sources.append(f"Glassdoor {gd.get('overall_rating', '?')}/5 ({gd.get('total_reviews', 0)} reviews)")

    sentiment_emoji = {"positive": "😊", "mixed": "😐", "negative": "😟"}.get(data["overall_sentiment"], "😐")
    pros_text = " • ".join(data["key_pros"][:4]) if data["key_pros"] else "No data"
    cons_text = " • ".join(data["key_cons"][:4]) if data["key_cons"] else "No data"

    content = (
        f"Employee Sentiment: {sentiment_emoji} {data['overall_sentiment'].title()}\n"
        f"Sources: {' | '.join(sources)}\n"
        f"Top Pros: {pros_text}\n"
        f"Top Cons: {cons_text}"
    )
    if data["red_flags"]:
        content += f"\n⚠️ Red Flags: {' • '.join(data['red_flags'][:3])}"

    post_id = hashlib.md5(f"employee_{competitor['name']}".encode()).hexdigest()
    posts.append({
        "competitor_id": competitor.get("id"),
        "competitor_name": competitor["name"],
        "platform": "employee",
        "post_id": f"emp_{post_id}",
        "author_name": "Employee Intelligence",
        "author_type": "analysis",
        "title": f"{competitor['name']} — Employee Sentiment Report",
        "content": content,
        "url": data.get("ambitionbox", {}).get("url", "") if data.get("ambitionbox") else "",
        "published_at": datetime.now(timezone.utc),
        "extra": data,
    })

    return posts


# ──────────────────────────────────────────────────────────────
# AmbitionBox Scraper
# ──────────────────────────────────────────────────────────────

async def _scrape_ambitionbox(name: str, competitor: dict) -> Optional[Dict]:
    """Scrape AmbitionBox company page for employee reviews."""
    slug = AMBITIONBOX_SLUGS.get(name)

    # Try known slug first
    if slug:
        data = await _fetch_ambitionbox_page(slug)
        if data:
            return data

    # Fallback: search AmbitionBox
    slug = await _search_ambitionbox(name)
    if slug:
        return await _fetch_ambitionbox_page(slug)

    return None


async def _fetch_ambitionbox_page(slug: str) -> Optional[Dict]:
    url = f"https://www.ambitionbox.com/reviews/{slug}-reviews"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9",
        "Referer": "https://www.ambitionbox.com/",
    }
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, "html.parser")
            return _parse_ambitionbox(soup, url)
    except Exception as e:
        logger.debug(f"AmbitionBox fetch failed for {slug}: {e}")
        return None


def _parse_ambitionbox(soup: BeautifulSoup, url: str) -> Dict:
    data = {"url": url, "top_pros": [], "top_cons": [], "current_reviews": [], "former_reviews": []}

    # Overall rating
    rating_el = soup.find("span", class_=re.compile(r"ratingNum|overallRating|rating__count"))
    if not rating_el:
        # Try JSON-LD
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                jd = json.loads(script.string or "")
                if "aggregateRating" in jd:
                    data["overall_rating"] = float(jd["aggregateRating"].get("ratingValue", 0))
                    data["total_reviews"] = int(jd["aggregateRating"].get("reviewCount", 0))
                    break
            except Exception:
                pass
    else:
        try:
            data["overall_rating"] = float(rating_el.get_text(strip=True).split()[0])
        except Exception:
            pass

    # Sub-ratings
    _extract_sub_ratings(soup, data, platform="ambitionbox")

    # Pros and cons from reviews
    pros_els = soup.find_all(class_=re.compile(r"pros|like"))
    cons_els = soup.find_all(class_=re.compile(r"cons|dislike"))

    for el in pros_els[:10]:
        text = el.get_text(strip=True)
        if len(text) > 10 and len(text) < 200:
            data["top_pros"].append(text)

    for el in cons_els[:10]:
        text = el.get_text(strip=True)
        if len(text) > 10 and len(text) < 200:
            data["top_cons"].append(text)

    # Employee type tags
    for review_el in soup.find_all(class_=re.compile(r"review-card|reviewCard")):
        emp_type = review_el.find(class_=re.compile(r"employeeType|emp-type|currentFormer"))
        rating_val = review_el.find(class_=re.compile(r"rating|star"))
        pros = review_el.find(class_=re.compile(r"pros"))
        cons = review_el.find(class_=re.compile(r"cons"))

        review_entry = {
            "pros": pros.get_text(strip=True)[:300] if pros else "",
            "cons": cons.get_text(strip=True)[:300] if cons else "",
            "rating": _extract_rating_from_el(rating_val),
        }

        if emp_type and "former" in emp_type.get_text(strip=True).lower():
            data["former_reviews"].append(review_entry)
        else:
            data["current_reviews"].append(review_entry)

    data["top_pros"] = list(dict.fromkeys(data["top_pros"]))[:6]
    data["top_cons"] = list(dict.fromkeys(data["top_cons"]))[:6]
    return data


async def _search_ambitionbox(name: str) -> Optional[str]:
    """Search AmbitionBox to find the company slug."""
    search_url = f"https://www.ambitionbox.com/api/v3/companies/search?query={name.replace(' ', '+')}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(search_url, headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
            })
            if resp.status_code == 200:
                data = resp.json()
                companies = data.get("data", {}).get("companies", [])
                if companies:
                    return companies[0].get("companySlug")
    except Exception:
        pass

    # Fallback: web search
    try:
        search_url = f"https://www.ambitionbox.com/reviews/{name.lower().replace(' ', '-')}-reviews"
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            resp = await client.get(search_url, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                return name.lower().replace(' ', '-')
    except Exception:
        pass

    return None


# ──────────────────────────────────────────────────────────────
# Glassdoor Scraper
# ──────────────────────────────────────────────────────────────

async def _scrape_glassdoor(name: str, competitor: dict) -> Optional[Dict]:
    """Scrape Glassdoor company reviews page."""
    slug = GLASSDOOR_SLUGS.get(name)

    if slug:
        url = f"https://www.glassdoor.co.in/Reviews/{slug}-reviews-SRCH_KE0,{len(name)}.htm"
        data = await _fetch_glassdoor_page(url, name)
        if data:
            return data

    # Fallback: search via Google
    data = await _search_glassdoor_via_search(name)
    return data


async def _fetch_glassdoor_page(url: str, name: str) -> Optional[Dict]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, "html.parser")
            return _parse_glassdoor(soup, url)
    except Exception as e:
        logger.debug(f"Glassdoor fetch failed for {name}: {e}")
        return None


def _parse_glassdoor(soup: BeautifulSoup, url: str) -> Dict:
    data = {"url": url, "top_pros": [], "top_cons": []}

    # Try JSON-LD for aggregate rating
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            jd = json.loads(script.string or "")
            items = [jd] if isinstance(jd, dict) else jd if isinstance(jd, list) else []
            for item in items:
                agg = item.get("aggregateRating", {})
                if agg:
                    data["overall_rating"] = float(agg.get("ratingValue", 0))
                    data["total_reviews"] = int(str(agg.get("reviewCount", "0")).replace(",", ""))
                    break
        except Exception:
            pass

    # Sub-ratings
    _extract_sub_ratings(soup, data, platform="glassdoor")

    # Pros and cons
    for el in soup.find_all(attrs={"data-test": re.compile(r"pros|cons")}):
        text = el.get_text(strip=True)
        if "pros" in (el.get("data-test", "") or "").lower():
            if len(text) > 10:
                data["top_pros"].append(text[:200])
        elif "cons" in (el.get("data-test", "") or "").lower():
            if len(text) > 10:
                data["top_cons"].append(text[:200])

    # Alternative selectors
    if not data["top_pros"]:
        for el in soup.find_all(class_=re.compile(r"pros|goodReview")):
            text = el.get_text(strip=True)
            if 10 < len(text) < 300:
                data["top_pros"].append(text)

    if not data["top_cons"]:
        for el in soup.find_all(class_=re.compile(r"cons|badReview")):
            text = el.get_text(strip=True)
            if 10 < len(text) < 300:
                data["top_cons"].append(text)

    data["top_pros"] = list(dict.fromkeys(data["top_pros"]))[:6]
    data["top_cons"] = list(dict.fromkeys(data["top_cons"]))[:6]
    return data


async def _search_glassdoor_via_search(name: str) -> Optional[Dict]:
    """Use search engines to find Glassdoor review data snippets."""
    try:
        # Try DuckDuckGo HTML search for Glassdoor reviews
        query = f"{name} glassdoor reviews site:glassdoor.co.in OR site:glassdoor.com"
        url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, "html.parser")
            result_els = soup.find_all(class_="result__snippet")

            for el in result_els[:3]:
                text = el.get_text(strip=True)
                # Try to extract rating from snippet text
                rating_match = re.search(r'(\d\.\d)\s*(?:out of 5|stars?|rating)', text, re.I)
                if rating_match:
                    return {
                        "url": "",
                        "overall_rating": float(rating_match.group(1)),
                        "total_reviews": None,
                        "top_pros": [],
                        "top_cons": [],
                        "source": "search_snippet",
                        "snippet": text[:300],
                    }
    except Exception as e:
        logger.debug(f"Glassdoor search fallback failed for {name}: {e}")

    return None


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def _extract_sub_ratings(soup: BeautifulSoup, data: dict, platform: str):
    """Extract culture, work-life, management, growth sub-ratings."""
    text_content = soup.get_text(separator=" ", strip=True).lower()

    # Pattern matching for sub-ratings in page text
    patterns = {
        "culture_rating":    r"(?:work culture|culture)[^\d]*(\d\.\d)",
        "work_life_rating":  r"(?:work.life balance|work-life)[^\d]*(\d\.\d)",
        "management_rating": r"(?:management|leadership)[^\d]*(\d\.\d)",
        "growth_rating":     r"(?:career growth|growth|promotions)[^\d]*(\d\.\d)",
        "salary_rating":     r"(?:salary|compensation|pay)[^\d]*(\d\.\d)",
    }
    for key, pattern in patterns.items():
        m = re.search(pattern, text_content)
        if m:
            try:
                data[key] = float(m.group(1))
            except Exception:
                pass


def _extract_rating_from_el(el) -> Optional[float]:
    if not el:
        return None
    text = el.get_text(strip=True)
    m = re.search(r'(\d\.?\d*)', text)
    if m:
        try:
            return float(m.group(1))
        except Exception:
            pass
    return None


def _extract_exit_signals(cons: List[str]) -> List[str]:
    """Patterns in cons that explain why employees leave."""
    signals = []
    exit_keywords = {
        "low salary": ["low salary", "underpaid", "poor pay", "compensation", "below market"],
        "poor management": ["bad management", "poor leadership", "toxic manager", "micromanagement"],
        "no growth": ["no career growth", "no promotion", "stagnant", "glass ceiling", "limited growth"],
        "work-life imbalance": ["long hours", "overworked", "no work life balance", "burnout", "weekend work"],
        "poor culture": ["toxic culture", "politics", "favouritism", "bias", "hostile"],
        "job instability": ["layoffs", "uncertainty", "unstable", "no job security"],
        "no learning": ["nothing to learn", "no training", "no skill development"],
    }
    text = " ".join(cons).lower()
    for signal, keywords in exit_keywords.items():
        if any(kw in text for kw in keywords):
            signals.append(signal)
    return signals[:5]


def _extract_join_signals(pros: List[str]) -> List[str]:
    """Patterns in pros that explain why people join."""
    signals = []
    join_keywords = {
        "mission-driven": ["mental health", "meaningful", "impact", "mission", "purpose"],
        "good culture": ["great culture", "friendly", "inclusive", "supportive", "collaborative"],
        "learning opportunities": ["learning", "growth", "skill development", "training", "mentorship"],
        "good salary": ["competitive salary", "good pay", "good compensation", "good benefits"],
        "flexibility": ["flexible", "remote", "wfh", "work from home", "autonomy"],
        "young & energetic": ["startup", "young team", "dynamic", "fast-paced", "energetic"],
    }
    text = " ".join(pros).lower()
    for signal, keywords in join_keywords.items():
        if any(kw in text for kw in keywords):
            signals.append(signal)
    return signals[:5]


def _detect_red_flags(cons: List[str], mgmt_score: Optional[float]) -> List[str]:
    """Detect serious red flags from cons."""
    flags = []
    text = " ".join(cons).lower()
    if any(w in text for w in ["sexual harassment", "unsafe", "discrimination", "illegal"]):
        flags.append("⚠️ Workplace safety concerns reported")
    if any(w in text for w in ["not paid", "salary delay", "unpaid", "dues"]):
        flags.append("⚠️ Salary payment issues reported")
    if any(w in text for w in ["layoff", "mass exit", "sudden termination"]):
        flags.append("⚠️ Layoff/instability signals")
    if mgmt_score and mgmt_score < 2.5:
        flags.append("⚠️ Very low management rating")
    if any(w in text for w in ["toxic", "politics", "favouritism", "nepotism"]):
        flags.append("⚠️ Toxic culture indicators")
    return flags
