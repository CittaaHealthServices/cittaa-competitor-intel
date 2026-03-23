"""
Content Playbook Advisor
Generates LinkedIn + Instagram post recommendations for Cittaa
using competitor intelligence context and Gemini 2.5 Pro.
"""
import json
import logging
from datetime import datetime

import google.generativeai as genai
from app.config import settings

logger = logging.getLogger(__name__)

try:
    genai.configure(api_key=settings.gemini_api_key)
except Exception:
    pass

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

Brand voice: Warm, professional, science-backed, de-stigmatizing, relatable.

Primary lead goal: Get HR managers / CHROs to request a demo or DM for corporate pricing.
Secondary goal: Build brand trust + community among working professionals.
"""


async def generate_content_recommendations(competitor_summaries: list) -> dict:
    """Generate LinkedIn + Instagram post recommendations using Gemini AI"""

    competitor_lines = []
    for comp in competitor_summaries[:10]:
        name = comp.get("name", "")
        posture = comp.get("posture") or "unknown"
        kw = ", ".join((comp.get("keywords") or [])[:4]) or "mental health"
        competitor_lines.append(f"  - {name}: strategic posture={posture}, topics={kw}")
    competitor_context = "\n".join(competitor_lines) or "  (no competitor data yet)"

    prompt = f"""You are a senior B2B content strategist specialising in Indian SaaS and healthtech brands.

ABOUT CITTAA:
{CITTAA_CONTEXT}

COMPETITOR LANDSCAPE (what rivals are currently doing):
{competitor_context}

YOUR TASK:
Create a complete Content Playbook for Cittaa's LinkedIn and Instagram pages.
Goals: maximum engagement + lead generation for corporate EAP clients.

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
    {{"tactic": "Tactic name", "platform": "LinkedIn|Instagram|Both", "description": "Concrete 1-sentence how-to"}},
    {{"tactic": "Tactic name", "platform": "LinkedIn|Instagram|Both", "description": "..."}}
  ]
}}

Rules:
- Generate exactly 7 post types for LinkedIn and 7 for Instagram
- Every sample_post must be 100% ready to copy-paste — no placeholders in them
- Focus on Indian corporate mental health context (HR, CHRO, burnout, EAP, World Mental Health Day, etc.)
- Make at least 2 LinkedIn post types specifically designed to generate HR/CHRO demo requests
- competitor_gaps must reference actual gaps vs the competitors listed above
- lead_gen_tactics: give 5 specific tactics
"""

    try:
        model = genai.GenerativeModel("gemini-2.5-pro")
        response = model.generate_content(prompt)
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
                    "why_it_works": "Short relatable reels about Monday anxiety get massive shares among working professionals, organically reaching Cittaa's core audience.",
                    "hook_formula": "\"That feeling when...\" + [hyper-relatable work scenario]",
                    "example_hook": "That feeling when you've replied to 47 Slack messages and it's only 10 AM 😮‍💨",
                    "body_template": "Scene: [relatable work moment]\nTwist: [Cittaa reframe or tip]\nEnding: [warm, non-preachy CTA]",
                    "cta": "Save this for your next Monday morning 💛",
                    "hashtags": ["#WorkplaceWellness", "#MentalHealthMatters", "#BurnoutRecovery", "#TherapyWorks", "#CitttaaCares", "#SelfCare", "#IndianProfessionals"],
                    "sample_post": "That Sunday night anxiety hitting different lately? 😮‍💨\n\nYour nervous system is trying to tell you something.\n\nYou don't have to white-knuckle through another week alone. Talking to someone really does help — and it doesn't have to be complicated.\n\nSwipe to see 3 things you can do tonight ✨\n\nLink in bio to connect with a Cittaa counsellor 💛"
                }
            ]
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
            {"tactic": "Therapist Q&A Lives", "platform": "Instagram", "description": "Weekly 20-minute Instagram Live with a Cittaa therapist answering anonymous questions — builds trust and drives sign-ups."}
        ]
    }
