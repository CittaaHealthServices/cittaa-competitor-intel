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
    SEARCH = "search"        # Deep Google/web search results
    APPSTORE = "appstore"    # Google Play + Apple App Store
    JOBS = "jobs"            # LinkedIn Jobs, Indeed, Naukri
    FUNDING = "funding"      # Crunchbase, funding news
    TECHSTACK = "techstack"  # Website technology detection
    EMPLOYEE = "employee"    # Glassdoor + AmbitionBox employee reviews
    STRATEGY = "strategy"    # AI-generated strategic intelligence

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


class CompetitorIntel(Base):
    """Stores structured deep intelligence per competitor — refreshed periodically."""
    __tablename__ = "competitor_intel"

    id = Column(Integer, primary_key=True, index=True)
    competitor_id = Column(Integer, nullable=False, index=True, unique=True)
    competitor_name = Column(String(255), nullable=False)

    # App Store
    google_play_rating = Column(Float)
    google_play_reviews = Column(Integer)
    google_play_installs = Column(String(50))
    google_play_version = Column(String(50))
    google_play_last_updated = Column(String(50))
    google_play_url = Column(String(500))
    apple_rating = Column(Float)
    apple_reviews = Column(Integer)
    apple_version = Column(String(50))
    apple_last_updated = Column(String(50))
    apple_url = Column(String(500))
    top_reviews = Column(JSON, default=[])

    # Funding
    total_funding = Column(String(100))
    last_round = Column(String(100))
    last_round_year = Column(Integer)
    investors = Column(JSON, default=[])
    crunchbase_url = Column(String(500))

    # Hiring
    open_roles = Column(JSON, default=[])          # list of {title, platform, signal, url}
    hiring_signals = Column(JSON, default=[])       # unique strategic signals detected
    total_open_roles = Column(Integer, default=0)

    # Tech Stack
    technologies = Column(JSON, default=[])         # [{name, category, signal}]
    tech_categories = Column(JSON, default={})      # {category: [tech_name, ...]}

    # ── Employee Intelligence (Glassdoor + AmbitionBox) ──────────────────────
    # Ratings
    ambitionbox_rating = Column(Float)
    ambitionbox_reviews_count = Column(Integer)
    ambitionbox_culture_rating = Column(Float)
    ambitionbox_work_life_rating = Column(Float)
    ambitionbox_management_rating = Column(Float)
    ambitionbox_growth_rating = Column(Float)
    ambitionbox_url = Column(String(500))

    glassdoor_rating = Column(Float)
    glassdoor_reviews_count = Column(Integer)
    glassdoor_culture_rating = Column(Float)
    glassdoor_work_life_rating = Column(Float)
    glassdoor_management_rating = Column(Float)
    glassdoor_url = Column(String(500))

    # Sentiment synthesis
    employee_overall_sentiment = Column(String(20))  # positive / mixed / negative
    employee_key_pros = Column(JSON, default=[])      # top things employees like
    employee_key_cons = Column(JSON, default=[])      # top complaints
    exit_signals = Column(JSON, default=[])           # why people leave
    join_signals = Column(JSON, default=[])           # why people join
    employee_red_flags = Column(JSON, default=[])     # serious issues
    current_employee_score = Column(Float)
    former_employee_score = Column(Float)

    # ── Strategic Intelligence (AI-synthesized) ───────────────────────────────
    strategic_posture = Column(String(50))            # Aggressive/Scaling/Consolidating/Pivoting/Struggling
    posture_reason = Column(Text)
    threat_level = Column(String(20))                 # Low/Medium/High/Critical
    threat_reason = Column(Text)
    top_signals = Column(JSON, default=[])            # list of 5 strategic signals
    predicted_moves = Column(JSON, default=[])        # next 3-6 months predictions
    hiring_strategy_insight = Column(Text)
    employee_strategy_insight = Column(Text)
    competitive_advantage = Column(Text)
    competitive_weakness = Column(Text)
    cittaa_opportunity = Column(Text)
    watch_out_for = Column(Text)
    strategy_analyzed_at = Column(DateTime(timezone=True))

    # Meta
    last_refreshed_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
