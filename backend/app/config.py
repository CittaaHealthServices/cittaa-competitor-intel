from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Cittaa Competitor Intel"
    DEBUG: bool = False
    SECRET_KEY: str = "cittaa-secret-key-change-in-production"

    # Database — use POSTGRES_URL to avoid collision with Railway's shared DATABASE_URL (MongoDB)
    POSTGRES_URL: str = "postgresql://postgres:password@localhost:5432/cittaa_intel"

    # Gemini AI
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-pro"

    # Email — uses your existing Railway shared variables (Resend)
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "sairam@cittaa.in"
    RESEND_FROM_NAME: str = "Cittaa Intel"
    ADMIN_EMAIL: str = "sairam@cittaa.in"   # digest recipient (shared var)

    # Scraping
    SCRAPE_INTERVAL_HOURS: int = 6
    NEWS_API_KEY: str = ""
    YOUTUBE_API_KEY: str = ""
    TWITTER_BEARER_TOKEN: str = ""

    # Google Search (for deep web research — optional but recommended)
    # Get from: console.cloud.google.com → Custom Search JSON API
    # GOOGLE_SEARCH_CX: your Programmable Search Engine ID (cx)
    GOOGLE_SEARCH_API_KEY: str = ""
    GOOGLE_SEARCH_CX: str = ""

    # CORS
    ALLOWED_ORIGINS: str = "*"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Default competitor list for Cittaa (mental health / EdTech wellness space)
DEFAULT_COMPETITORS = [
    # ─── CITTAA SELF-MONITORING ────────────────────────────────────────────────
    # Track your own brand mentions, press, and social activity so you see
    # how YOU compare alongside competitors in the same dashboard.
    {
        "name": "Cittaa",
        "website": "https://cittaa.in",
        "linkedin_slug": "cittaa",
        "twitter_handle": "cittaa_in",
        "instagram_handle": "cittaa.in",
        "youtube_channel": "cittaa",
        "news_keywords": ["Cittaa", "Cittaa mental health", "cittaa.in", "Cittaa wellness"],
        "category": "Self",
        "description": "Cittaa — our own brand (self-monitoring)"
    },
    # ─── NATIONAL COMPETITORS ─────────────────────────────────────────────────
    {
        "name": "YourDOST",
        "website": "https://yourdost.com",
        "linkedin_slug": "yourdost",
        "twitter_handle": "YourDOST",
        "instagram_handle": "yourdost",
        "youtube_channel": "yourdost",
        "news_keywords": ["YourDOST", "yourdost mental health"],
        "category": "National",
        "description": "Indian mental health & emotional wellness platform"
    },
    {
        "name": "Wysa",
        "website": "https://wysa.io",
        "linkedin_slug": "wysa-inc",
        "twitter_handle": "wysabuddy",
        "instagram_handle": "wysa.io",
        "youtube_channel": "wysabuddy",
        "news_keywords": ["Wysa", "Wysa AI mental health"],
        "category": "National",
        "description": "AI-powered mental health chatbot & therapy platform"
    },
    {
        "name": "InnerHour",
        "website": "https://theinnerhour.com",
        "linkedin_slug": "the-innerhour",
        "twitter_handle": "theinnerhour",
        "instagram_handle": "theinnerhour",
        "youtube_channel": "innerhour",
        "news_keywords": ["InnerHour", "Inner Hour mental health"],
        "category": "National",
        "description": "Mental wellness & self-help platform"
    },
    {
        "name": "MindPeers",
        "website": "https://mindpeers.co",
        "linkedin_slug": "mindpeers",
        "twitter_handle": "MindPeersHQ",
        "instagram_handle": "mindpeers.co",
        "youtube_channel": "mindpeers",
        "news_keywords": ["MindPeers", "mindpeers mental health India"],
        "category": "National",
        "description": "Corporate mental health & employee wellness platform"
    },
    {
        "name": "HeartItOut",
        "website": "https://heartitout.in",
        "linkedin_slug": "heart-it-out",
        "twitter_handle": "heartitout",
        "instagram_handle": "heartitout.in",
        "youtube_channel": "heartitout",
        "news_keywords": ["HeartItOut", "Heart It Out counselling"],
        "category": "National",
        "description": "Online counselling & therapy platform"
    },
    {
        "name": "Lissun",
        "website": "https://lissun.com",
        "linkedin_slug": "lissun",
        "twitter_handle": "lissun_in",
        "instagram_handle": "lissun.app",
        "youtube_channel": "lissun",
        "news_keywords": ["Lissun", "Lissun mental health"],
        "category": "National",
        "description": "Mental health platform for young adults"
    },
    {
        "name": "Talkspace",
        "website": "https://talkspace.com",
        "linkedin_slug": "talkspace",
        "twitter_handle": "Talkspace",
        "instagram_handle": "talkspace",
        "youtube_channel": "talkspace",
        "news_keywords": ["Talkspace", "Talkspace therapy"],
        "category": "International",
        "description": "Online therapy platform (USA)"
    },
    {
        "name": "BetterHelp",
        "website": "https://betterhelp.com",
        "linkedin_slug": "betterhelp",
        "twitter_handle": "BetterHelp",
        "instagram_handle": "betterhelp",
        "youtube_channel": "betterhelp",
        "news_keywords": ["BetterHelp", "BetterHelp online therapy"],
        "category": "International",
        "description": "World's largest online therapy platform"
    },
    {
        "name": "Headspace",
        "website": "https://headspace.com",
        "linkedin_slug": "headspace",
        "twitter_handle": "headspace",
        "instagram_handle": "headspace",
        "youtube_channel": "headspace",
        "news_keywords": ["Headspace", "Headspace meditation"],
        "category": "International",
        "description": "Mindfulness & meditation app"
    },
    {
        "name": "Calm",
        "website": "https://calm.com",
        "linkedin_slug": "calm",
        "twitter_handle": "calm",
        "instagram_handle": "calm",
        "youtube_channel": "calm",
        "news_keywords": ["Calm app", "Calm meditation sleep"],
        "category": "International",
        "description": "Sleep, meditation & relaxation app"
    }
]
