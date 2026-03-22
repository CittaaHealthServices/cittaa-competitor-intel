from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum

class PlatformEnum(str, enum.Enum):
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    NEWS = "news"
    BLOG = "blog"
    PRESSRELEASE = "press_release"
    SEARCH = "search"  # Deep Google/web search results

class SentimentEnum(str, enum.Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"

class CategoryEnum(str, enum.Enum):
    NATIONAL = "National"
    INTERNATIONAL = "International"

class Competitor(Base):
    __tablename__ = "competitors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    website = Column(String(500))
    linkedin_slug = Column(String(255))
    twitter_handle = Column(String(255))
    instagram_handle = Column(String(255))
    youtube_channel = Column(String(255))
    news_keywords = Column(JSON, default=[])
    category = Column(String(50), default="National")
    description = Column(Text)
    logo_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    last_scraped_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    competitor_id = Column(Integer, nullable=False, index=True)
    competitor_name = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=False, index=True)
    post_id = Column(String(500), unique=True)
    author_name = Column(String(255))
    author_type = Column(String(50))  # 'company', 'founder', 'employee'
    title = Column(Text)
    content = Column(Text)
    url = Column(String(1000))
    image_url = Column(String(1000))
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    views = Column(Integer, default=0)
    sentiment = Column(String(20), default="neutral")
    ai_summary = Column(Text)
    ai_tags = Column(JSON, default=[])
    ai_importance_score = Column(Float, default=0.0)
    is_viral = Column(Boolean, default=False)
    published_at = Column(DateTime(timezone=True))
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())

class Insight(Base):
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True, index=True)
    insight_type = Column(String(100))  # 'trend', 'alert', 'opportunity', 'threat'
    title = Column(String(500))
    content = Column(Text)
    competitor_ids = Column(JSON, default=[])
    competitor_names = Column(JSON, default=[])
    platform = Column(String(50))
    importance = Column(String(20), default="medium")  # low, medium, high, critical
    action_items = Column(JSON, default=[])
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True))

class DigestLog(Base):
    __tablename__ = "digest_logs"

    id = Column(Integer, primary_key=True, index=True)
    digest_type = Column(String(50))  # 'daily', 'weekly'
    recipients = Column(JSON, default=[])
    posts_included = Column(Integer, default=0)
    insights_included = Column(Integer, default=0)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), default="sent")  # sent, failed
    error_message = Column(Text)

class ScrapingLog(Base):
    __tablename__ = "scraping_logs"

    id = Column(Integer, primary_key=True, index=True)
    competitor_id = Column(Integer, index=True)
    competitor_name = Column(String(255))
    platform = Column(String(50))
    status = Column(String(20))  # success, failed, partial
    posts_found = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    keywords = Column(JSON, default=[])
    competitor_ids = Column(JSON, default=[])  # empty = all
    platforms = Column(JSON, default=[])  # empty = all
    min_importance_score = Column(Float, default=7.0)
    email_alert = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
