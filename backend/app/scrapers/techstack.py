"""
Tech Stack Intelligence — detect what technologies competitors use.
Reveals: hosting, analytics, CRM, email marketing, chat tools,
app frameworks, CDN, payment gateways, etc.
Signals: Mixpanel = data-driven, Intercom = customer success focus,
Salesforce = enterprise sales motion, etc.
"""
import httpx
import logging
import hashlib
import re
from datetime import datetime, timezone
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Technology fingerprints — pattern → (category, tech name, strategic signal)
TECH_FINGERPRINTS = {
    # Analytics
    r"google-analytics|gtag\.js|UA-\d+|G-[A-Z0-9]+": ("Analytics", "Google Analytics", "Basic web analytics"),
    r"mixpanel": ("Analytics", "Mixpanel", "🎯 Product analytics — data-driven growth team"),
    r"amplitude": ("Analytics", "Amplitude", "🎯 Advanced product analytics — measuring funnel & retention"),
    r"segment\.com|segment\.io": ("Analytics", "Segment", "🎯 Customer data platform — sophisticated data stack"),
    r"heap\.io|heap\.js": ("Analytics", "Heap", "🎯 Auto-capture analytics — optimizing every interaction"),
    r"hotjar": ("Analytics", "Hotjar", "👁 Heatmaps & session recordings — UX optimization"),
    r"clarity\.ms|microsoft\.com/clarity": ("Analytics", "Microsoft Clarity", "👁 Heatmaps & session recordings"),
    r"fullstory": ("Analytics", "FullStory", "👁 Digital experience analytics"),
    r"posthog": ("Analytics", "PostHog", "🎯 Open-source product analytics"),

    # Marketing & CRM
    r"hubspot": ("CRM/Marketing", "HubSpot", "🏢 Inbound marketing & CRM — B2B sales motion"),
    r"salesforce|pardot": ("CRM/Marketing", "Salesforce", "🏢 Enterprise CRM — targeting large B2B deals"),
    r"intercom": ("Support/Chat", "Intercom", "💬 Customer messaging — strong customer success focus"),
    r"freshdesk|freshworks": ("Support/Chat", "Freshdesk", "💬 Customer support platform"),
    r"zendesk": ("Support/Chat", "Zendesk", "💬 Enterprise customer support"),
    r"drift\.com": ("Support/Chat", "Drift", "💬 Conversational marketing"),
    r"crisp\.chat": ("Support/Chat", "Crisp", "💬 Live chat & support"),
    r"tawk\.to": ("Support/Chat", "Tawk.to", "💬 Live chat — cost-conscious team"),

    # Email Marketing
    r"mailchimp": ("Email", "Mailchimp", "📧 Email marketing — mass campaigns"),
    r"sendgrid": ("Email", "SendGrid", "📧 Transactional + marketing email"),
    r"klaviyo": ("Email", "Klaviyo", "📧 E-commerce email automation"),
    r"customer\.io": ("Email", "Customer.io", "📧 Behavioral email — sophisticated onboarding"),
    r"brevo|sendinblue": ("Email", "Brevo", "📧 Marketing automation"),

    # Payments
    r"razorpay": ("Payments", "Razorpay", "💳 India payments — targeting Indian market"),
    r"stripe": ("Payments", "Stripe", "💳 Global payments — international expansion"),
    r"paytm": ("Payments", "Paytm", "💳 Indian payments gateway"),
    r"cashfree": ("Payments", "Cashfree", "💳 India-first payments"),
    r"instamojo": ("Payments", "Instamojo", "💳 Indian SMB payments"),
    r"ccavenue": ("Payments", "CCAvenue", "💳 Indian enterprise payments"),

    # Frontend Framework
    r'"react"|react-dom|__react': ("Frontend", "React", "⚛️ React-based frontend"),
    r'"vue"|vue\.js|vue@': ("Frontend", "Vue.js", "⚛️ Vue.js frontend"),
    r'"angular"|angular/core': ("Frontend", "Angular", "⚛️ Angular frontend — likely enterprise"),
    r'next\.js|_next/': ("Frontend", "Next.js", "⚛️ Next.js — SEO-optimized React"),
    r"nuxt|__nuxt": ("Frontend", "Nuxt.js", "⚛️ Nuxt.js — SSR Vue"),
    r"flutter_web": ("Frontend", "Flutter Web", "📱 Flutter — cross-platform focus"),

    # Backend/Infra
    r"nginx": ("Infrastructure", "Nginx", "🖥 Nginx web server"),
    r"cloudflare": ("CDN/Security", "Cloudflare", "🛡 Cloudflare — DDoS protection & CDN"),
    r"fastly": ("CDN/Security", "Fastly", "🌐 Fastly CDN — performance-focused"),
    r"amazonaws\.com|aws\.amazon": ("Cloud", "AWS", "☁️ AWS infrastructure"),
    r"googleapis\.com|appspot\.com": ("Cloud", "Google Cloud", "☁️ Google Cloud infrastructure"),
    r"azure\.com|azurewebsites": ("Cloud", "Azure", "☁️ Microsoft Azure infrastructure"),

    # Firebase / Backend as a Service
    r"firebase|firebaseapp\.com": ("BaaS", "Firebase", "🔥 Firebase — rapid development, no custom backend"),
    r"supabase": ("BaaS", "Supabase", "🔥 Supabase — open-source Firebase alternative"),

    # Ad Platforms
    r"facebook\.net|fbq\(|fbevents": ("Advertising", "Facebook Pixel", "📣 Facebook/Instagram ads running"),
    r"googletagmanager|gtm\.js": ("Advertising", "Google Tag Manager", "📣 Tag management — running multiple ad campaigns"),
    r"ads\.linkedin\.com|linkedin.*insight": ("Advertising", "LinkedIn Ads", "📣 LinkedIn ads — B2B targeting"),
    r"tiktok.*pixel|analytics\.tiktok": ("Advertising", "TikTok Ads", "📣 TikTok advertising — Gen Z targeting"),

    # AI/ML
    r"openai|gpt-|chatgpt": ("AI", "OpenAI", "🤖 Using OpenAI/GPT — AI-powered features"),
    r"dialogflow": ("AI", "Dialogflow", "🤖 Google conversational AI — chatbot features"),
    r"rasa\.com": ("AI", "Rasa", "🤖 Open-source NLP chatbot"),
    r"botpress": ("AI", "Botpress", "🤖 Botpress chatbot platform"),

    # SEO / Performance
    r"schema\.org": ("SEO", "Schema.org", "🔍 Structured data — SEO-optimized"),
    r"ahrefs": ("SEO", "Ahrefs", "🔍 SEO tooling — content marketing investment"),

    # Mobile
    r"appsflyer": ("Mobile Marketing", "AppsFlyer", "📱 Mobile attribution — running app install campaigns"),
    r"branch\.io": ("Mobile Marketing", "Branch", "📱 Deep linking & mobile attribution"),
    r"onesignal": ("Notifications", "OneSignal", "🔔 Push notifications — engagement campaigns"),
    r"clevertap": ("Notifications", "CleverTap", "🔔 Mobile analytics & engagement — Indian unicorn tool"),
    r"moengage": ("Notifications", "MoEngage", "🔔 Customer engagement platform — Indian startup"),
    r"webengage": ("Notifications", "WebEngage", "🔔 Multi-channel engagement — India-focused"),
}


async def scrape_techstack(competitor: dict) -> List[Dict]:
    """Detect technology stack from competitor website."""
    posts = []
    name = competitor["name"]
    website = competitor.get("website", "")

    if not website:
        return posts

    tech_found = await _detect_technologies(website, name)

    if not tech_found:
        return posts

    # Group by category
    categories = {}
    for tech in tech_found:
        cat = tech["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(tech["name"])

    # Build summary content
    content_lines = [f"🔬 Tech stack detected for {name}:"]
    signals = []
    for tech in tech_found:
        content_lines.append(f"• {tech['name']} ({tech['category']})")
        if tech.get("signal") and "Basic" not in tech["signal"]:
            signals.append(tech["signal"])

    if signals:
        content_lines.append("\n📊 Strategic Signals:")
        for sig in signals[:5]:
            content_lines.append(f"• {sig}")

    post_id = hashlib.md5(f"techstack_{name}".encode()).hexdigest()
    posts.append({
        "competitor_id": competitor.get("id"),
        "competitor_name": name,
        "platform": "techstack",
        "post_id": f"tech_{post_id}",
        "author_name": "Tech Intelligence",
        "author_type": "media",
        "title": f"🔬 Tech Stack: {name}",
        "content": "\n".join(content_lines),
        "url": website,
        "published_at": datetime.now(timezone.utc),
        "extra": {
            "technologies": tech_found,
            "categories": categories,
            "total_detected": len(tech_found),
        }
    })

    return posts


async def get_techstack_structured(competitor: dict) -> Dict:
    """Return structured tech stack data for the deep profile page."""
    name = competitor["name"]
    website = competitor.get("website", "")

    if not website:
        return {"competitor_name": name, "technologies": [], "categories": {}}

    tech_found = await _detect_technologies(website, name)

    categories = {}
    for tech in tech_found:
        cat = tech["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(tech)

    return {
        "competitor_name": name,
        "website": website,
        "technologies": tech_found,
        "categories": categories,
        "total_detected": len(tech_found),
        "detected_at": datetime.now(timezone.utc).isoformat(),
    }


async def _detect_technologies(website: str, name: str) -> List[Dict]:
    """Fetch website and run all fingerprint checks."""
    tech_found = []
    seen_names = set()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    # Normalize website URL
    if not website.startswith("http"):
        website = f"https://{website}"

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(website, headers=headers)
            if resp.status_code != 200:
                return tech_found

            # Check response headers for server info
            server = resp.headers.get("server", "")
            x_powered = resp.headers.get("x-powered-by", "")
            header_text = f"{server} {x_powered}".lower()

            if "nginx" in header_text:
                tech_found.append({"name": "Nginx", "category": "Infrastructure", "signal": "🖥 Nginx web server", "source": "headers"})
                seen_names.add("Nginx")
            if "cloudflare" in header_text or "cf-ray" in resp.headers:
                tech_found.append({"name": "Cloudflare", "category": "CDN/Security", "signal": "🛡 Cloudflare protection", "source": "headers"})
                seen_names.add("Cloudflare")
            if "php" in header_text:
                tech_found.append({"name": "PHP", "category": "Backend", "signal": "🔧 PHP backend", "source": "headers"})
                seen_names.add("PHP")

            page_text = resp.text
            soup = BeautifulSoup(page_text, "html.parser")

            # Check all scripts and page source
            all_scripts = " ".join([s.get("src", "") for s in soup.find_all("script")])
            inline_scripts = " ".join([s.get_text() for s in soup.find_all("script") if not s.get("src")])
            meta_tags = " ".join([str(m) for m in soup.find_all("meta")])
            link_tags = " ".join([l.get("href", "") for l in soup.find_all("link")])

            full_text = f"{page_text} {all_scripts} {inline_scripts} {meta_tags} {link_tags}"

            # Check each fingerprint
            for pattern, (category, tech_name, signal) in TECH_FINGERPRINTS.items():
                if tech_name in seen_names:
                    continue
                try:
                    if re.search(pattern, full_text, re.IGNORECASE):
                        tech_found.append({
                            "name": tech_name,
                            "category": category,
                            "signal": signal,
                            "source": "page",
                        })
                        seen_names.add(tech_name)
                except re.error:
                    continue

            # Check for app store links (mobile presence)
            if "play.google.com" in page_text or "apps.apple.com" in page_text:
                if "Mobile App" not in seen_names:
                    has_android = "play.google.com" in page_text
                    has_ios = "apps.apple.com" in page_text
                    if has_android and has_ios:
                        tech_found.append({"name": "iOS + Android Apps", "category": "Mobile", "signal": "📱 Cross-platform mobile presence", "source": "links"})
                    elif has_android:
                        tech_found.append({"name": "Android App", "category": "Mobile", "signal": "📱 Android app available", "source": "links"})
                    elif has_ios:
                        tech_found.append({"name": "iOS App", "category": "Mobile", "signal": "📱 iOS app available", "source": "links"})

            # Check for structured data / JSON-LD
            json_ld = soup.find_all("script", type="application/ld+json")
            if json_ld and "Schema.org" not in seen_names:
                tech_found.append({"name": "Schema.org", "category": "SEO", "signal": "🔍 Rich structured data for SEO", "source": "schema"})
                seen_names.add("Schema.org")

            # Also try /robots.txt for clues
            try:
                robots_resp = await client.get(f"{website.rstrip('/')}/robots.txt", headers=headers, timeout=5.0)
                if robots_resp.status_code == 200:
                    robots_text = robots_resp.text.lower()
                    if "sitemap" in robots_text and "Sitemap" not in seen_names:
                        tech_found.append({"name": "XML Sitemap", "category": "SEO", "signal": "🔍 XML sitemap — SEO investment", "source": "robots"})
                        seen_names.add("Sitemap")
            except Exception:
                pass

    except Exception as e:
        logger.warning(f"Tech stack detection failed for {name}: {e}")

    return tech_found
