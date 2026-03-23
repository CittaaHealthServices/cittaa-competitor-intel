"""
Content Playbook Advisor
Generates LinkedIn + Instagram post recommendations AND SEO strategy for Cittaa
using competitor intelligence context and Gemini 2.5 Pro.
"""
import asyncio
import json
import logging
from datetime import datetime
from functools import partial

logger = logging.getLogger(__name__)


def _get_model():
    """Lazy-load Gemini model — never crashes startup if key is missing."""
    try:
        import google.generativeai as genai
        from app.config import settings
        genai.configure(api_key=settings.GEMINI_API_KEY)
        return genai.GenerativeModel(settings.GEMINI_MODEL)
    except Exception as e:
        logger.warning(f"Gemini model unavailable for content advisor: {e}")
        return None

CITTAA_CONTEXT = """
Cittaa (cittaa.in) is an Indian B2B + B2C mental wellness platform.

B2B: Corporate EAP (Employee Assistance Program) — sells to HR managers, CHROs, and
     corporate wellness heads at mid-to-large Indian companies. Provides therapy access,
     mental wellness assessments, workshops, and counselor support for employees.

B2C: Individual therapy and counseling for working professionals across India.

Key USPs:
- India-first, culturally-sensitive approach
- Vernacular / regional language support
- Affordable corporate plan pricing vs. global competitors
- Evidence-based therapy (CBT, DBT, mindfulness)
- Quick onboarding for corporates

Website: cittaa.in
Brand voice: Warm, professional, science-backed, de-stigmatizing, relatable.

Primary goal: Get HR managers / CHROs to request a demo for corporate EAP pricing.
Secondary goal: Individual therapy sign-ups from working professionals.
"""


async def generate_content_recommendations(competitor_summaries: list) -> dict:
    """Generate LinkedIn + Instagram + SEO recommendations using Gemini AI"""

    competitor_lines = []
    for comp in competitor_summaries[:10]:
        name = comp.get("name", "")
        posture = comp.get("posture") or "unknown"
        kw = ", ".join((comp.get("keywords") or [])[:4]) or "mental health"
        competitor_lines.append(f"  - {name}: posture={posture}, topics={kw}")
    competitor_context = "\n".join(competitor_lines) or "  (no competitor data yet)"

    prompt = f"""You are a senior B2B content + SEO strategist specialising in Indian SaaS and healthtech brands.

ABOUT CITTAA:
{CITTAA_CONTEXT}

COMPETITOR LANDSCAPE:
{competitor_context}

YOUR TASK:
Create a complete Growth Playbook for Cittaa covering LinkedIn, Instagram, AND SEO.
Goals: maximum engagement + lead generation for corporate EAP clients + organic search traffic.

Return ONLY a valid JSON object with this exact schema (no markdown, no explanation):

{{
  "generated_at": "{datetime.utcnow().isoformat()}",
  "linkedin": {{
    "strategy": "2-sentence strategy for LinkedIn",
    "content_pillars": ["pillar1", "pillar2", "pillar3", "pillar4", "pillar5"],
    "posting_frequency": "e.g. 4-5 times per week",
    "best_times": ["Tuesday 9–10 AM IST", "Thursday 12–1 PM IST"],
    "post_types": [
      {{
        "type": "Post Type Name",
        "purpose": "one of: engagement | leads | awareness | trust",
        "format": "one of: carousel | text | single-image | poll | document | video",
        "why_it_works": "1-sentence explanation",
        "hook_formula": "Formula e.g. [Shocking stat] + [consequence for HR]",
        "example_hook": "A ready-to-use hook line for mental health / wellness space",
        "body_template": "Template with [PLACEHOLDERS] for easy customisation",
        "cta": "The exact call-to-action text",
        "hashtags": ["#HashtagOne", "#HashtagTwo", "#HashtagThree", "#HashtagFour", "#HashtagFive"],
        "sample_post": "A 150–200 word complete ready-to-copy LinkedIn post. Professional tone."
      }}
    ]
  }},
  "instagram": {{
    "strategy": "2-sentence strategy for Instagram",
    "content_pillars": ["pillar1", "pillar2", "pillar3", "pillar4", "pillar5"],
    "posting_frequency": "e.g. 5-6 times per week",
    "best_times": ["Monday 7–9 PM IST", "Friday 6–8 PM IST"],
    "post_types": [
      {{
        "type": "Post Type Name",
        "purpose": "one of: engagement | leads | awareness | trust",
        "format": "one of: carousel | reel | single-image | story",
        "why_it_works": "1-sentence explanation",
        "hook_formula": "Formula",
        "example_hook": "Ready-to-use hook",
        "body_template": "Caption template with [PLACEHOLDERS]",
        "cta": "Call-to-action",
        "hashtags": ["#Tag1", "#Tag2", "#Tag3", "#Tag4", "#Tag5", "#Tag6", "#Tag7"],
        "sample_post": "A 60–80 word complete ready-to-copy Instagram caption. Warm, relatable tone."
      }}
    ]
  }},
  "seo": {{
    "strategy": "2-sentence SEO strategy for cittaa.in covering both B2B EAP and B2C therapy audiences",
    "primary_keywords": [
      {{
        "keyword": "exact keyword phrase",
        "est_monthly_searches": "e.g. 1,000–5,000",
        "intent": "one of: commercial | informational | transactional | navigational",
        "difficulty": "one of: low | medium | high",
        "why_target": "1-sentence reason Cittaa should own this keyword"
      }}
    ],
    "long_tail_keywords": [
      {{
        "keyword": "long-tail keyword phrase (4-6 words)",
        "intent": "commercial | informational | transactional",
        "content_type": "blog post | landing page | FAQ | case study",
        "why_it_converts": "1-sentence explanation"
      }}
    ],
    "blog_content_ideas": [
      {{
        "title": "SEO-optimised blog post title",
        "target_keyword": "primary keyword for this post",
        "search_intent": "what the searcher wants",
        "why_it_ranks": "why Cittaa can rank for this",
        "estimated_traffic_potential": "low | medium | high",
        "outline": ["H2: Section 1", "H2: Section 2", "H2: Section 3", "H2: Section 4"]
      }}
    ],
    "content_clusters": [
      {{
        "pillar_page": "Pillar page topic and title",
        "target_keyword": "main pillar keyword",
        "supporting_articles": ["Supporting article 1 title", "Supporting article 2 title", "Supporting article 3 title", "Supporting article 4 title"]
      }}
    ],
    "on_page_seo_tips": [
      {{
        "tip": "Specific actionable on-page SEO tip for cittaa.in",
        "priority": "one of: high | medium | low",
        "effort": "one of: quick-win | medium | long-term"
      }}
    ],
    "technical_seo_wins": [
      "Quick technical SEO improvement Cittaa should implement",
      "...",
      "..."
    ],
    "competitor_keyword_gaps": [
      {{
        "keyword": "keyword competitors rank for but Cittaa doesn't",
        "competitor": "which competitor ranks for it",
        "opportunity": "how Cittaa can beat them"
      }}
    ],
    "local_seo_tips": [
      "India / city-specific SEO tip relevant to mental health / EAP",
      "...",
      "..."
    ],
    "meta_formulas": {{
      "title_tag": "Formula for page title tags e.g. [Primary Keyword] | [Benefit] | Cittaa",
      "meta_description": "Formula for meta descriptions with character guidance",
      "example_homepage_title": "Ready-to-use title tag for cittaa.in homepage",
      "example_homepage_meta": "Ready-to-use meta description for cittaa.in homepage"
    }}
  }},
  "content_calendar": [
    {{"day": "Monday",    "platform": "Instagram", "type": "Post Type", "theme": "Short theme description"}},
    {{"day": "Tuesday",   "platform": "LinkedIn",  "type": "Post Type", "theme": "Short theme description"}},
    {{"day": "Wednesday", "platform": "Instagram", "type": "Post Type", "theme": "Short theme description"}},
    {{"day": "Thursday",  "platform": "LinkedIn",  "type": "Post Type", "theme": "Short theme description"}},
    {{"day": "Friday",    "platform": "LinkedIn",  "type": "Post Type", "theme": "Short theme description"}},
    {{"day": "Saturday",  "platform": "Instagram", "type": "Post Type", "theme": "Short theme description"}}
  ],
  "competitor_gaps": [
    "Gap 1: Specific content angle competitors are ignoring that Cittaa can own",
    "Gap 2: ...",
    "Gap 3: ...",
    "Gap 4: ..."
  ],
  "lead_gen_tactics": [
    {{"tactic": "Tactic name", "platform": "LinkedIn|Instagram|Both|SEO", "description": "Concrete 1-sentence how-to"}},
    {{"tactic": "Tactic name", "platform": "LinkedIn|Instagram|Both|SEO", "description": "..."}}
  ]
}}

Rules:
- Generate exactly 7 post types for LinkedIn and 7 for Instagram
- Every sample_post must be 100% ready to copy-paste — no placeholders in them
- Focus on Indian corporate mental health context (HR, CHRO, burnout, EAP, World Mental Health Day, etc.)
- Make at least 2 LinkedIn post types specifically designed to generate HR/CHRO demo requests
- competitor_gaps must reference actual gaps vs the competitors listed above
- lead_gen_tactics: give 6 specific tactics (include at least 1 SEO tactic)
- For SEO: give 8 primary keywords, 8 long-tail keywords, 6 blog ideas, 3 content clusters, 6 on-page tips, 4 technical wins, 4 competitor keyword gaps, 3 local SEO tips
- SEO keywords must be realistic for an Indian mental health brand — include both English and Hinglish phrases
- Blog content ideas must target keywords that competitors are weak on
"""

    from app.config import settings
    if not settings.GEMINI_API_KEY:
        logger.warning("No GEMINI_API_KEY set — returning fallback content recommendations")
        return _fallback_recommendations()

    model = _get_model()
    if not model:
        return _fallback_recommendations()

    try:
        # Run blocking Gemini call in thread pool — never block the asyncio event loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, partial(model.generate_content, prompt))
        text = response.text.strip()

        # Strip markdown code fences if present
        if "```" in text:
            parts = text.split("```")
            for part in parts:
                if part.startswith("json"):
                    text = part[4:].strip()
                    break
                elif part.strip().startswith("{"):
                    text = part.strip()
                    break

        result = json.loads(text)
        result["generated_at"] = datetime.utcnow().isoformat()
        return result

    except Exception as e:
        logger.error(f"Gemini content recommendations failed: {e}")
        return _fallback_recommendations()


def _fallback_recommendations() -> dict:
    """Rule-based fallback when Gemini is unavailable"""
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "linkedin": {
            "strategy": "Position Cittaa as India's most trusted corporate mental wellness partner by educating HR leaders with data-driven content that makes the business case for employee wellbeing.",
            "content_pillars": [
                "Mental Health ROI for Business",
                "HR Leader Perspectives",
                "Employee Burnout & Productivity",
                "Cittaa Success Stories",
                "Industry Research & Stats"
            ],
            "posting_frequency": "4-5 times per week",
            "best_times": ["Tuesday 9–10 AM IST", "Thursday 12–1 PM IST"],
            "post_types": [
                {
                    "type": "Stat + Insight Carousel",
                    "purpose": "awareness",
                    "format": "carousel",
                    "why_it_works": "Data-led carousels get 3x saves vs single images, educating HR leaders who share them in leadership meetings.",
                    "hook_formula": "[Shocking % stat] + [what it costs Indian companies]",
                    "example_hook": "76% of Indian employees say work is their #1 source of stress. Here's what that's silently costing your company 👇",
                    "body_template": "Slide 1: [stat hook]\nSlide 2-5: [data points with context]\nSlide 6: [Cittaa solution]\nSlide 7: [CTA]",
                    "cta": "Tag an HR leader who needs to see this 👇",
                    "hashtags": ["#EmployeeWellbeing", "#MentalHealth", "#HRLeaders", "#CorporateWellness", "#EAP"],
                    "sample_post": "76% of Indian employees cite work as their biggest stressor.\n\nBut here's what most companies don't realise: untreated mental health issues cost Indian businesses ₹1.03 lakh crore annually in lost productivity.\n\nYet only 23% of Indian companies have a structured EAP in place.\n\nThat gap? That's where burnout, attrition, and presenteeism quietly drain your best people.\n\nAt Cittaa, we've seen firsthand how a simple, culturally-sensitive EAP can:\n✅ Reduce absenteeism by 28%\n✅ Improve team productivity scores\n✅ Cut attrition in high-stress roles\n\nIf you're an HR leader building a wellness strategy for 2025 — drop a comment or DM us. We'd love to share what's working."
                }
            ]
        },
        "instagram": {
            "strategy": "Build an emotionally resonant community for working professionals by making mental health feel normal, approachable, and actionable.",
            "content_pillars": [
                "Self-Care for Working Professionals",
                "Workplace Anxiety & Burnout",
                "Therapy Myths Busted",
                "Mindfulness Micro-Tips",
                "Community Stories"
            ],
            "posting_frequency": "5-6 times per week",
            "best_times": ["Monday 7–9 PM IST", "Friday 6–8 PM IST"],
            "post_types": [
                {
                    "type": "Relatable Reel",
                    "purpose": "engagement",
                    "format": "reel",
                    "why_it_works": "Short relatable reels about Monday anxiety get massive shares among working professionals.",
                    "hook_formula": "\"That feeling when...\" + [hyper-relatable work scenario]",
                    "example_hook": "That feeling when you've replied to 47 Slack messages and it's only 10 AM 😮‍💨",
                    "body_template": "Scene: [relatable work moment]\nTwist: [Cittaa reframe or tip]\nEnding: [warm CTA]",
                    "cta": "Save this for your next Monday morning 💛",
                    "hashtags": ["#WorkplaceWellness", "#MentalHealthMatters", "#BurnoutRecovery", "#TherapyWorks", "#CittaaCares", "#SelfCare", "#IndianProfessionals"],
                    "sample_post": "That Sunday night anxiety hitting different lately? 😮‍💨\n\nYour nervous system is trying to tell you something.\n\nYou don't have to white-knuckle through another week alone. Talking to someone really does help — and it doesn't have to be complicated.\n\nSwipe to see 3 things you can do tonight ✨\n\nLink in bio to connect with a Cittaa counsellor 💛"
                }
            ]
        },
        "seo": {
            "strategy": "Build topical authority for Indian corporate mental health and EAP-related searches by creating a content cluster strategy that targets high-intent HR decision-makers and individual therapy seekers simultaneously.",
            "primary_keywords": [
                {"keyword": "employee assistance program India", "est_monthly_searches": "1,000–5,000", "intent": "commercial", "difficulty": "medium", "why_target": "High-intent B2B buyers actively searching for EAP providers in India."},
                {"keyword": "corporate mental health program India", "est_monthly_searches": "500–2,000", "intent": "commercial", "difficulty": "low", "why_target": "Direct match for Cittaa's core B2B offering with low competition."},
                {"keyword": "online therapy India", "est_monthly_searches": "10,000–50,000", "intent": "transactional", "difficulty": "high", "why_target": "Massive B2C search volume; even 0.5% conversion is significant."},
                {"keyword": "mental health counselling for employees", "est_monthly_searches": "500–2,000", "intent": "commercial", "difficulty": "low", "why_target": "Specific corporate intent with low competitor SEO investment."},
                {"keyword": "employee wellness program", "est_monthly_searches": "2,000–8,000", "intent": "commercial", "difficulty": "medium", "why_target": "Broad corporate wellness intent that Cittaa can capture with EAP content."},
                {"keyword": "workplace stress management India", "est_monthly_searches": "1,000–3,000", "intent": "informational", "difficulty": "low", "why_target": "HR leaders searching for solutions — top of funnel for Cittaa's B2B pitch."},
                {"keyword": "online counselling for working professionals", "est_monthly_searches": "2,000–8,000", "intent": "transactional", "difficulty": "medium", "why_target": "Cittaa's exact B2C persona searching for therapy access."},
                {"keyword": "EAP benefits for companies", "est_monthly_searches": "200–1,000", "intent": "informational", "difficulty": "low", "why_target": "HR decision-makers researching EAP — prime content opportunity with demo CTA."}
            ],
            "long_tail_keywords": [
                {"keyword": "best employee assistance program for Indian companies", "intent": "commercial", "content_type": "landing page", "why_it_converts": "Bottom-of-funnel buyer ready to evaluate vendors."},
                {"keyword": "how to implement EAP in Indian companies", "intent": "informational", "content_type": "blog post", "why_it_converts": "HR decision-makers in research phase — perfect for a Cittaa guide with lead capture."},
                {"keyword": "online therapy for IT employees India", "intent": "transactional", "content_type": "landing page", "why_it_converts": "Niche segment (IT) with very high burnout rates and willingness to pay."},
                {"keyword": "mental health benefits for employees India", "intent": "commercial", "content_type": "blog post", "why_it_converts": "HR researching what to offer — positions Cittaa as the answer."},
                {"keyword": "signs of employee burnout HR manager", "intent": "informational", "content_type": "blog post", "why_it_converts": "HR persona article that leads naturally into EAP product pitch."},
                {"keyword": "affordable online therapy Hindi", "intent": "transactional", "content_type": "landing page", "why_it_converts": "Vernacular intent — Cittaa's unique India-first positioning wins here."},
                {"keyword": "corporate wellness program cost India", "intent": "commercial", "content_type": "FAQ", "why_it_converts": "Price-conscious buyers — a transparent pricing page ranks well and converts."},
                {"keyword": "difference between EAP and mental health insurance", "intent": "informational", "content_type": "blog post", "why_it_converts": "Educates buyers who conflate products — Cittaa becomes the trusted authority."}
            ],
            "blog_content_ideas": [
                {"title": "The Complete Guide to Employee Assistance Programs for Indian Companies in 2025", "target_keyword": "employee assistance program India", "search_intent": "HR managers wanting to understand and implement EAP", "why_it_ranks": "Comprehensive guide targeting low-competition keyword with high commercial intent", "estimated_traffic_potential": "high", "outline": ["H2: What is an EAP and why do Indian companies need one?", "H2: EAP vs traditional health insurance — key differences", "H2: How to choose the right EAP provider in India", "H2: Real ROI data from Indian companies using EAP"]},
                {"title": "10 Warning Signs of Employee Burnout Every HR Manager Should Know", "target_keyword": "signs of employee burnout HR manager", "search_intent": "HR managers noticing team stress and looking for guidance", "why_it_ranks": "Listicle format ranks easily; HR persona content gets high shares on LinkedIn", "estimated_traffic_potential": "high", "outline": ["H2: Why burnout is different from stress", "H2: The 10 early warning signs", "H2: What to do when you spot burnout in your team", "H2: How an EAP helps prevent burnout at scale"]},
                {"title": "Online Therapy for IT Professionals in India: What to Expect", "target_keyword": "online therapy for IT employees India", "search_intent": "Tech employees seeking affordable therapy options", "why_it_ranks": "Niche targeting with low competition; IT sector has massive therapy demand", "estimated_traffic_potential": "medium", "outline": ["H2: Why IT professionals face unique mental health challenges", "H2: How online therapy works in India", "H2: What a first therapy session looks like", "H2: How to access therapy through your company's EAP"]},
                {"title": "Mental Health ROI: How Indian Companies Are Measuring Wellness Program Success", "target_keyword": "corporate mental health program India ROI", "search_intent": "CHROs and CFOs wanting to justify wellness budgets", "why_it_ranks": "Data-driven content with business angle ranks well and attracts decision-makers", "estimated_traffic_potential": "medium", "outline": ["H2: Why measuring mental health ROI is now a board-level conversation", "H2: Key metrics Indian companies track", "H2: Case study: How one company reduced attrition by 30%", "H2: Free ROI calculator template"]},
                {"title": "Hindi Mein Online Therapy: Kaise Kaam Karta Hai? (Online Therapy in Hindi)", "target_keyword": "affordable online therapy Hindi", "search_intent": "Hindi-speaking professionals seeking therapy in their language", "why_it_ranks": "Zero competition for vernacular mental health content — Cittaa can dominate this niche", "estimated_traffic_potential": "medium", "outline": ["H2: Online therapy kya hai?", "H2: Hindi mein therapy lena kaisa hota hai?", "H2: Cittaa par Hindi counsellor kaise dhundhein", "H2: Pehla session ke liye kaise tayar karein"]},
                {"title": "EAP vs Mental Health Insurance: Which Is Right for Your Company?", "target_keyword": "difference between EAP and mental health insurance", "search_intent": "HR/finance decision-makers comparing options", "why_it_ranks": "Comparison content ranks well and captures buyers still in research phase", "estimated_traffic_potential": "medium", "outline": ["H2: What EAP covers vs what insurance covers", "H2: Cost comparison for Indian companies", "H2: Which option gets higher employee utilisation?", "H2: Can you have both? How they complement each other"]}
            ],
            "content_clusters": [
                {"pillar_page": "Employee Assistance Program (EAP) in India — The Definitive Guide", "target_keyword": "employee assistance program India", "supporting_articles": ["EAP Implementation Checklist for HR Teams", "EAP Utilisation Rates: What's Normal for Indian Companies?", "How to Communicate Your EAP to Employees", "EAP vs Wellness Apps: A Side-by-Side Comparison"]},
                {"pillar_page": "Online Therapy in India — Complete Guide for 2025", "target_keyword": "online therapy India", "supporting_articles": ["First Therapy Session: What to Expect", "How to Find the Right Therapist in India", "Online vs In-Person Therapy: Pros and Cons", "Is Online Therapy Covered by Indian Health Insurance?"]},
                {"pillar_page": "Corporate Mental Health Strategy for Indian Companies", "target_keyword": "corporate mental health program India", "supporting_articles": ["Building a Stigma-Free Workplace Culture", "Manager Training for Mental Health Support", "World Mental Health Day Campaign Ideas for Companies", "Measuring Employee Wellbeing: A Framework for HR"]}
            ],
            "on_page_seo_tips": [
                {"tip": "Add an FAQ section to every blog post targeting 2–3 long-tail question keywords (e.g. 'How much does EAP cost in India?')", "priority": "high", "effort": "quick-win"},
                {"tip": "Create a dedicated /eap landing page targeting 'employee assistance program India' with pricing, features, and a demo CTA above the fold", "priority": "high", "effort": "medium"},
                {"tip": "Add structured data (Organization, FAQPage, Article schema) across all blog posts to improve rich snippet eligibility", "priority": "high", "effort": "medium"},
                {"tip": "Optimise all image alt text with keywords — especially screenshots, therapist photos, and infographics", "priority": "medium", "effort": "quick-win"},
                {"tip": "Create a /blog/category/corporate-wellness/ hub page that links to all corporate content — builds topical authority signals", "priority": "medium", "effort": "medium"},
                {"tip": "Add internal links from every blog post to the EAP product/demo page with anchor text like 'corporate mental wellness program'", "priority": "high", "effort": "quick-win"}
            ],
            "technical_seo_wins": [
                "Ensure cittaa.in loads in under 2s on mobile — run PageSpeed Insights and fix LCP issues (compress images, lazy-load below fold)",
                "Add hreflang tags if planning Hindi/vernacular content pages to avoid duplicate content penalties",
                "Submit an XML sitemap to Google Search Console and verify all key pages are indexed",
                "Fix any broken links (404s) — especially from old blog posts that may have moved"
            ],
            "competitor_keyword_gaps": [
                {"keyword": "EAP provider India", "competitor": "YourDOST", "opportunity": "YourDOST ranks here but has poor on-page EAP content — Cittaa can outrank with a dedicated, detailed EAP hub page"},
                {"keyword": "employee mental health app India", "competitor": "Wysa", "opportunity": "Wysa dominates 'mental health app' but ignores HR decision-maker intent — Cittaa can win with B2B-focused content"},
                {"keyword": "corporate counselling services India", "competitor": "1to1help.net", "opportunity": "1to1help has outdated content — a modern, well-structured page from Cittaa can outrank"},
                {"keyword": "online therapy affordable India", "competitor": "MindPeers", "opportunity": "MindPeers has thin content on pricing pages — Cittaa can rank by publishing transparent pricing + comparison content"}
            ],
            "local_seo_tips": [
                "Create city-specific landing pages for high-demand metros: /therapy/bangalore, /therapy/mumbai, /therapy/delhi — target 'online therapy [city]' keywords",
                "Register and optimise a Google Business Profile for Cittaa's office locations to appear in local 'mental health counsellor near me' searches",
                "Get listed on IndiaMART, Justdial, and Sulekha for corporate wellness services — these rank well for B2B searches in India"
            ],
            "meta_formulas": {
                "title_tag": "[Primary Keyword] | [Key Benefit] | Cittaa — Max 60 characters",
                "meta_description": "[Empathetic hook addressing the pain point]. [Cittaa's unique solution in 1 sentence]. [CTA: Get a free demo / Start your journey]. Max 155 characters.",
                "example_homepage_title": "Employee Wellness & Online Therapy Platform | Cittaa",
                "example_homepage_meta": "Cittaa helps Indian companies build mentally healthy workplaces with EAP, therapy access & wellbeing programs. Trusted by 500+ HR teams. Book a free demo today."
            }
        },
        "content_calendar": [
            {"day": "Monday", "platform": "Instagram", "type": "Relatable Reel", "theme": "Monday motivation / Sunday anxiety"},
            {"day": "Tuesday", "platform": "LinkedIn", "type": "Stat + Insight Carousel", "theme": "Mental health ROI data for HR leaders"},
            {"day": "Wednesday", "platform": "Instagram", "type": "Myth-Busting Carousel", "theme": "Therapy misconceptions"},
            {"day": "Thursday", "platform": "LinkedIn", "type": "HR Leader Story", "theme": "How a company transformed wellness culture"},
            {"day": "Friday", "platform": "LinkedIn", "type": "Poll", "theme": "HR sentiment pulse on employee wellbeing"},
            {"day": "Saturday", "platform": "Instagram", "type": "Self-Care Tip", "theme": "Weekend recharge micro-tips"}
        ],
        "competitor_gaps": [
            "India-specific data: Most competitors use global stats. Cittaa can own India-specific workplace mental health research.",
            "Vernacular content: No competitor is creating Hindi/Tamil/Telugu mental health content — huge untapped reach.",
            "HR community building: Competitors focus on individuals; Cittaa can build a dedicated HR wellness community on LinkedIn.",
            "ROI calculators: No competitor offers a public mental health ROI tool — Cittaa could create a viral LinkedIn lead magnet."
        ],
        "lead_gen_tactics": [
            {"tactic": "Free EAP Readiness Audit", "platform": "LinkedIn", "description": "Post a '5 signs your company needs an EAP' carousel with a DM CTA for a free audit call."},
            {"tactic": "HR Wellness Benchmark Report", "platform": "LinkedIn", "description": "Publish a downloadable India Corporate Mental Health Benchmark PDF — gate it behind a form to capture HR leads."},
            {"tactic": "Story Poll Funnel", "platform": "Instagram", "description": "Use Instagram Story polls ('Does your company have an EAP?') to identify corporate professionals, then retarget via DM."},
            {"tactic": "World Mental Health Day Campaign", "platform": "Both", "description": "Run a 10-day countdown series in October with a dedicated hashtag, ending with a free corporate workshop offer."},
            {"tactic": "Therapist Q&A Lives", "platform": "Instagram", "description": "Weekly 20-minute Instagram Live with a Cittaa therapist answering anonymous questions — builds trust and drives sign-ups."},
            {"tactic": "SEO Lead Magnet Blog", "platform": "SEO", "description": "Publish 'The Complete EAP Guide for Indian Companies' — optimised for 'employee assistance program India' — with a gated PDF download that captures HR email leads."}
        ]
    }
