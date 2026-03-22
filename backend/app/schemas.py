from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Any
from datetime import datetime

# --- Competitor Schemas ---
class CompetitorBase(BaseModel):
    name: str
    website: Optional[str] = None
    linkedin_slug: Optional[str] = None
    twitter_handle: Optional[str] = None
    instagram_handle: Optional[str] = None
    youtube_channel: Optional[str] = None
    news_keywords: Optional[List[str]] = []
    category: Optional[str] = "National"
    description: Optional[str] = None

class CompetitorCreate(CompetitorBase):
    pass

class CompetitorResponse(CompetitorBase):
    id: int
    is_active: bool
    last_scraped_at: Optional[datetime] = None
    created_at: datetime
    post_count: Optional[int] = 0

    class Config:
        from_attributes = True

# --- Post Schemas ---
class PostResponse(BaseModel):
    id: int
    competitor_id: int
    competitor_name: str
    platform: str
    author_name: Optional[str] = None
    author_type: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    likes: int = 0
    comments: int = 0
    shares: int = 0
    views: int = 0
    sentiment: str = "neutral"
    ai_summary: Optional[str] = None
    ai_tags: Optional[List[str]] = []
    ai_importance_score: float = 0.0
    is_viral: bool = False
    published_at: Optional[datetime] = None
    scraped_at: datetime

    class Config:
        from_attributes = True

# --- Insight Schemas ---
class InsightResponse(BaseModel):
    id: int
    insight_type: str
    title: str
    content: str
    competitor_names: List[str] = []
    platform: Optional[str] = None
    importance: str = "medium"
    action_items: List[str] = []
    generated_at: datetime
    is_read: bool = False

    class Config:
        from_attributes = True

# --- Dashboard Stats ---
class DashboardStats(BaseModel):
    total_posts_today: int
    total_posts_week: int
    active_competitors: int
    top_platform: str
    viral_posts: int
    critical_alerts: int
    last_scraped: Optional[datetime] = None
    sentiment_breakdown: dict

# --- Scrape Request ---
class ScrapeRequest(BaseModel):
    competitor_id: Optional[int] = None  # None = scrape all
    platforms: Optional[List[str]] = None  # None = all platforms

# --- Alert Rule ---
class AlertRuleCreate(BaseModel):
    name: str
    keywords: List[str] = []
    competitor_ids: List[int] = []
    platforms: List[str] = []
    min_importance_score: float = 7.0
    email_alert: bool = True
