import React, { useState, useEffect } from 'react'
import { formatDistanceToNow } from 'date-fns'
import {
  Linkedin, Instagram, Copy, Check, RefreshCw,
  Zap, Target, Clock, TrendingUp, Lightbulb,
  ChevronDown, ChevronUp, Calendar, Hash, BarChart2, AlertCircle,
  Search, Globe, FileText, Link, AlertTriangle, CheckCircle2, ArrowUpRight
} from 'lucide-react'
import { getContentRecommendations } from '../services/api'

// ─── Helpers ──────────────────────────────────────────────────────────────────

const PURPOSE_CONFIG = {
  leads:       { label: 'Lead Gen',   bg: 'bg-green-100',  text: 'text-green-700',  dot: 'bg-green-500' },
  engagement:  { label: 'Engagement', bg: 'bg-blue-100',   text: 'text-blue-700',   dot: 'bg-blue-500'  },
  awareness:   { label: 'Awareness',  bg: 'bg-purple-100', text: 'text-purple-700', dot: 'bg-purple-500'},
  trust:       { label: 'Trust',      bg: 'bg-yellow-100', text: 'text-yellow-700', dot: 'bg-yellow-500'},
}

const FORMAT_CONFIG = {
  carousel:      { emoji: '🎠', label: 'Carousel' },
  'single-image':{ emoji: '🖼', label: 'Image' },
  text:          { emoji: '📝', label: 'Text' },
  poll:          { emoji: '📊', label: 'Poll' },
  document:      { emoji: '📄', label: 'Document' },
  video:         { emoji: '🎬', label: 'Video' },
  reel:          { emoji: '🎥', label: 'Reel' },
  story:         { emoji: '⭕', label: 'Story' },
}

const DAY_COLORS = {
  Monday:    '#6C63FF',
  Tuesday:   '#0077B5',
  Wednesday: '#E1306C',
  Thursday:  '#0077B5',
  Friday:    '#2EC4B6',
  Saturday:  '#E1306C',
  Sunday:    '#F7B731',
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch { /* clipboard not available */ }
  }
  return (
    <button
      onClick={handleCopy}
      className={`flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg font-medium transition
        ${copied
          ? 'bg-green-100 text-green-700'
          : 'bg-gray-100 text-gray-500 hover:bg-gray-200 hover:text-gray-700'}`}
    >
      {copied ? <><Check size={11} /> Copied!</> : <><Copy size={11} /> Copy post</>}
    </button>
  )
}

function PurposeBadge({ purpose }) {
  const cfg = PURPOSE_CONFIG[purpose] || PURPOSE_CONFIG.awareness
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full ${cfg.bg} ${cfg.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
      {cfg.label}
    </span>
  )
}

// ─── Post Type Card ───────────────────────────────────────────────────────────
function PostTypeCard({ post, platform, index }) {
  const [expanded, setExpanded] = useState(false)
  const fmtCfg = FORMAT_CONFIG[post.format] || { emoji: '📄', label: post.format }
  const platformColor = platform === 'linkedin' ? '#0077B5' : '#E1306C'

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      {/* Card header */}
      <div className="px-5 pt-5 pb-4">
        <div className="flex items-start justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center text-sm font-bold text-white flex-shrink-0"
              style={{ background: platformColor }}>
              {index + 1}
            </div>
            <h3 className="font-bold text-gray-800 text-sm leading-tight">{post.type}</h3>
          </div>
          <div className="flex items-center gap-1.5 flex-shrink-0">
            <PurposeBadge purpose={post.purpose} />
          </div>
        </div>

        {/* Format + Why it works */}
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full font-medium">
            {fmtCfg.emoji} {fmtCfg.label}
          </span>
        </div>
        <p className="text-xs text-gray-500 leading-relaxed mb-3">{post.why_it_works}</p>

        {/* Hook formula */}
        <div className="bg-gray-50 rounded-xl p-3 mb-3">
          <p className="text-xs font-semibold text-gray-400 mb-1">HOOK FORMULA</p>
          <p className="text-xs text-gray-600 font-medium">{post.hook_formula}</p>
          {post.example_hook && (
            <p className="text-xs text-gray-500 mt-1.5 italic">e.g. "{post.example_hook}"</p>
          )}
        </div>

        {/* CTA */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-gray-400">CTA:</span>
          <span className="text-xs text-gray-600">{post.cta}</span>
        </div>
      </div>

      {/* Expandable: sample post + hashtags */}
      <div className="border-t border-gray-50">
        <button
          onClick={() => setExpanded(p => !p)}
          className="w-full flex items-center justify-between px-5 py-3 text-xs font-semibold text-gray-500 hover:bg-gray-50 transition"
        >
          <span style={{ color: platformColor }}>
            {expanded ? 'Hide' : 'View'} sample post & hashtags
          </span>
          {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
        </button>

        {expanded && (
          <div className="px-5 pb-5 space-y-3">
            {/* Sample post */}
            {post.sample_post && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs font-semibold text-gray-400">READY-TO-USE POST</p>
                  <CopyButton text={post.sample_post} />
                </div>
                <div className="bg-gray-50 rounded-xl p-3.5 text-xs text-gray-700 leading-relaxed whitespace-pre-line">
                  {post.sample_post}
                </div>
              </div>
            )}

            {/* Hashtags */}
            {post.hashtags?.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-gray-400 mb-2 flex items-center gap-1">
                  <Hash size={11} /> HASHTAGS
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {post.hashtags.map((tag, i) => (
                    <span key={i} className="text-xs px-2 py-0.5 rounded-full font-medium"
                      style={{ background: `${platformColor}15`, color: platformColor, border: `1px solid ${platformColor}25` }}>
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Body template */}
            {post.body_template && (
              <div>
                <p className="text-xs font-semibold text-gray-400 mb-2">CONTENT TEMPLATE</p>
                <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-3 text-xs text-indigo-700 whitespace-pre-line leading-relaxed">
                  {post.body_template}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Platform Panel ───────────────────────────────────────────────────────────
function PlatformPanel({ data, platform }) {
  const isLinkedIn = platform === 'linkedin'
  const color = isLinkedIn ? '#0077B5' : '#E1306C'
  const Icon = isLinkedIn ? Linkedin : Instagram

  if (!data) return null

  return (
    <div className="space-y-5">
      {/* Strategy card */}
      <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-8 h-8 rounded-xl flex items-center justify-center" style={{ background: `${color}20` }}>
            <Icon size={16} style={{ color }} />
          </div>
          <h2 className="font-bold text-gray-800">
            {isLinkedIn ? 'LinkedIn Strategy' : 'Instagram Strategy'}
          </h2>
        </div>
        <p className="text-sm text-gray-600 leading-relaxed mb-4">{data.strategy}</p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {/* Posting frequency */}
          <div className="bg-gray-50 rounded-xl p-3">
            <div className="flex items-center gap-1.5 mb-1">
              <Clock size={12} className="text-gray-400" />
              <p className="text-xs font-semibold text-gray-400">FREQUENCY</p>
            </div>
            <p className="text-sm font-bold text-gray-700">{data.posting_frequency}</p>
          </div>

          {/* Best times */}
          <div className="bg-gray-50 rounded-xl p-3 md:col-span-2">
            <div className="flex items-center gap-1.5 mb-1">
              <Zap size={12} className="text-gray-400" />
              <p className="text-xs font-semibold text-gray-400">BEST POSTING TIMES</p>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {(data.best_times || []).map((t, i) => (
                <span key={i} className="text-xs font-medium px-2 py-0.5 rounded-full"
                  style={{ background: `${color}15`, color }}>
                  {t}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Content pillars */}
        {data.content_pillars?.length > 0 && (
          <div className="mt-4">
            <p className="text-xs font-semibold text-gray-400 mb-2">CONTENT PILLARS</p>
            <div className="flex flex-wrap gap-2">
              {data.content_pillars.map((p, i) => (
                <span key={i} className="text-xs px-3 py-1 rounded-full font-medium"
                  style={{ background: `${color}12`, color, border: `1px solid ${color}25` }}>
                  {p}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Post type cards */}
      <div>
        <h3 className="font-bold text-gray-700 mb-3 flex items-center gap-2">
          <BarChart2 size={15} style={{ color }} />
          Post Types ({data.post_types?.length || 0})
        </h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {(data.post_types || []).map((pt, i) => (
            <PostTypeCard key={i} post={pt} platform={platform} index={i} />
          ))}
        </div>
      </div>
    </div>
  )
}

// ─── Content Calendar ─────────────────────────────────────────────────────────
function ContentCalendar({ calendar }) {
  if (!calendar?.length) return null

  return (
    <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 rounded-xl bg-[#2EC4B6]/10 flex items-center justify-center">
          <Calendar size={16} className="text-[#2EC4B6]" />
        </div>
        <h2 className="font-bold text-gray-800">Weekly Content Calendar</h2>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {calendar.map((item, i) => {
          const isLinkedIn = item.platform?.toLowerCase().includes('linkedin')
          const isInstagram = item.platform?.toLowerCase().includes('instagram')
          const isBoth = isLinkedIn && isInstagram
          const color = isBoth ? '#6C63FF' : isLinkedIn ? '#0077B5' : '#E1306C'
          const platformEmoji = isBoth ? '🔗' : isLinkedIn ? '💼' : '📸'
          return (
            <div key={i} className="rounded-xl p-3 border" style={{ borderColor: `${color}30`, background: `${color}08` }}>
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-bold" style={{ color }}>{item.day}</p>
                <span className="text-base">{platformEmoji}</span>
              </div>
              <p className="text-xs font-semibold text-gray-700 mb-1 leading-tight">{item.type}</p>
              <p className="text-xs text-gray-400 leading-tight">{item.theme}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ─── Competitor Gaps ──────────────────────────────────────────────────────────
function CompetitorGaps({ gaps }) {
  if (!gaps?.length) return null
  return (
    <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 rounded-xl bg-amber-50 flex items-center justify-center">
          <Lightbulb size={16} className="text-amber-500" />
        </div>
        <h2 className="font-bold text-gray-800">Competitor Content Gaps</h2>
        <span className="ml-auto text-xs text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full font-medium">Cittaa can own these</span>
      </div>
      <div className="space-y-2">
        {gaps.map((gap, i) => (
          <div key={i} className="flex items-start gap-3 bg-amber-50 border border-amber-100 rounded-xl px-4 py-3">
            <span className="text-amber-500 font-bold text-sm flex-shrink-0 mt-0.5">{i + 1}</span>
            <p className="text-sm text-amber-800 leading-relaxed">{gap}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Lead Gen Tactics ─────────────────────────────────────────────────────────
function LeadGenTactics({ tactics }) {
  if (!tactics?.length) return null

  const PLATFORM_STYLE = {
    LinkedIn:   { color: '#0077B5', bg: 'bg-blue-50',  text: 'text-blue-700'  },
    Instagram:  { color: '#E1306C', bg: 'bg-pink-50',  text: 'text-pink-700'  },
    Both:       { color: '#6C63FF', bg: 'bg-purple-50',text: 'text-purple-700'},
  }

  return (
    <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 rounded-xl bg-green-50 flex items-center justify-center">
          <Target size={16} className="text-green-600" />
        </div>
        <h2 className="font-bold text-gray-800">Lead Generation Tactics</h2>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {tactics.map((t, i) => {
          const ps = PLATFORM_STYLE[t.platform] || PLATFORM_STYLE.Both
          return (
            <div key={i} className="border border-gray-100 rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <p className="font-semibold text-sm text-gray-800">{t.tactic}</p>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${ps.bg} ${ps.text}`}>
                  {t.platform}
                </span>
              </div>
              <p className="text-xs text-gray-500 leading-relaxed">{t.description}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ─── SEO Section ─────────────────────────────────────────────────────────────
function SeoSection({ seo }) {
  const [blogExpanded, setBlogExpanded] = useState({})
  const [clusterExpanded, setClusterExpanded] = useState({})

  if (!seo) return (
    <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-8 h-8 rounded-xl bg-green-50 flex items-center justify-center">
          <Search size={16} className="text-green-600" />
        </div>
        <h2 className="font-bold text-gray-800">SEO Strategy</h2>
      </div>
      <p className="text-sm text-gray-400">No SEO data yet. Click Regenerate with AI to generate.</p>
    </div>
  )

  const INTENT_CONFIG = {
    commercial:     { bg: 'bg-green-100',  text: 'text-green-700',  label: '💰 Commercial' },
    transactional:  { bg: 'bg-blue-100',   text: 'text-blue-700',   label: '🛒 Transactional' },
    informational:  { bg: 'bg-purple-100', text: 'text-purple-700', label: '📖 Informational' },
    navigational:   { bg: 'bg-gray-100',   text: 'text-gray-600',   label: '🗺 Navigational' },
  }
  const DIFF_CONFIG = {
    low:    { bg: 'bg-green-100',  text: 'text-green-700',  label: 'Low' },
    medium: { bg: 'bg-yellow-100', text: 'text-yellow-700', label: 'Medium' },
    high:   { bg: 'bg-red-100',    text: 'text-red-700',    label: 'High' },
  }
  const EFFORT_CONFIG = {
    'quick-win':  { bg: 'bg-teal-100',  text: 'text-teal-700',   label: '⚡ Quick Win' },
    'medium':     { bg: 'bg-blue-100',  text: 'text-blue-700',   label: '🔧 Medium' },
    'long-term':  { bg: 'bg-gray-100',  text: 'text-gray-600',   label: '🗓 Long-term' },
  }
  const PRIORITY_DOT = { high: 'bg-red-500', medium: 'bg-yellow-400', low: 'bg-gray-300' }

  return (
    <div className="space-y-5">
      {/* Strategy */}
      <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-8 h-8 rounded-xl bg-green-50 flex items-center justify-center">
            <Search size={16} className="text-green-600" />
          </div>
          <h2 className="font-bold text-gray-800">SEO Strategy</h2>
        </div>
        <p className="text-sm text-gray-600 leading-relaxed">{seo.strategy}</p>
      </div>

      {/* Meta tag formulas */}
      {seo.meta_formulas && (
        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-xl bg-indigo-50 flex items-center justify-center">
              <Globe size={16} className="text-indigo-600" />
            </div>
            <h2 className="font-bold text-gray-800">Homepage Meta Tags</h2>
            <span className="ml-auto text-xs bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full font-medium">Copy & use now</span>
          </div>
          <div className="space-y-3">
            <div>
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs font-semibold text-gray-400">TITLE TAG FORMULA</p>
              </div>
              <div className="bg-gray-50 rounded-xl px-4 py-2.5 text-xs text-gray-600 font-mono">{seo.meta_formulas.title_tag}</div>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-400 mb-1">META DESCRIPTION FORMULA</p>
              <div className="bg-gray-50 rounded-xl px-4 py-2.5 text-xs text-gray-600 font-mono">{seo.meta_formulas.meta_description}</div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <p className="text-xs font-semibold text-gray-400">HOMEPAGE TITLE</p>
                  <CopyButton text={seo.meta_formulas.example_homepage_title || ''} />
                </div>
                <div className="bg-green-50 border border-green-100 rounded-xl px-3 py-2.5 text-xs text-green-800 font-medium">
                  {seo.meta_formulas.example_homepage_title}
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <p className="text-xs font-semibold text-gray-400">HOMEPAGE META DESC</p>
                  <CopyButton text={seo.meta_formulas.example_homepage_meta || ''} />
                </div>
                <div className="bg-green-50 border border-green-100 rounded-xl px-3 py-2.5 text-xs text-green-800 leading-relaxed">
                  {seo.meta_formulas.example_homepage_meta}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Primary keywords */}
      {seo.primary_keywords?.length > 0 && (
        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-xl bg-blue-50 flex items-center justify-center">
              <Hash size={16} className="text-blue-600" />
            </div>
            <h2 className="font-bold text-gray-800">Primary Keywords</h2>
            <span className="ml-auto text-xs text-gray-400">{seo.primary_keywords.length} targets</span>
          </div>
          <div className="space-y-2">
            {seo.primary_keywords.map((kw, i) => {
              const intentCfg = INTENT_CONFIG[kw.intent] || INTENT_CONFIG.informational
              const diffCfg = DIFF_CONFIG[kw.difficulty] || DIFF_CONFIG.medium
              return (
                <div key={i} className="flex items-start gap-3 p-3 rounded-xl border border-gray-50 hover:bg-gray-50 transition">
                  <span className="text-xs font-bold text-gray-300 mt-0.5 w-4 flex-shrink-0">{i + 1}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <p className="text-sm font-semibold text-gray-800">{kw.keyword}</p>
                      <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${intentCfg.bg} ${intentCfg.text}`}>{intentCfg.label}</span>
                      <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${diffCfg.bg} ${diffCfg.text}`}>
                        {diffCfg.label} difficulty
                      </span>
                    </div>
                    <div className="flex items-center gap-3 flex-wrap">
                      <span className="text-xs text-gray-400">~{kw.est_monthly_searches} searches/mo</span>
                      <span className="text-xs text-gray-500">{kw.why_target}</span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Long-tail keywords */}
      {seo.long_tail_keywords?.length > 0 && (
        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-xl bg-purple-50 flex items-center justify-center">
              <TrendingUp size={16} className="text-purple-600" />
            </div>
            <h2 className="font-bold text-gray-800">Long-Tail Keywords</h2>
            <span className="ml-auto text-xs text-gray-400">Lower competition, high conversion</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {seo.long_tail_keywords.map((kw, i) => {
              const intentCfg = INTENT_CONFIG[kw.intent] || INTENT_CONFIG.informational
              return (
                <div key={i} className="border border-gray-100 rounded-xl p-3">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <p className="text-sm font-semibold text-gray-800 leading-tight">{kw.keyword}</p>
                    <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium flex-shrink-0 ${intentCfg.bg} ${intentCfg.text}`}>{intentCfg.label}</span>
                  </div>
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{kw.content_type}</span>
                  </div>
                  <p className="text-xs text-gray-500 leading-relaxed">{kw.why_it_converts}</p>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Blog content ideas */}
      {seo.blog_content_ideas?.length > 0 && (
        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-xl bg-orange-50 flex items-center justify-center">
              <FileText size={16} className="text-orange-500" />
            </div>
            <h2 className="font-bold text-gray-800">Blog Content Ideas</h2>
            <span className="ml-auto text-xs text-gray-400">{seo.blog_content_ideas.length} ideas</span>
          </div>
          <div className="space-y-3">
            {seo.blog_content_ideas.map((post, i) => {
              const isExp = blogExpanded[i]
              const trafficColor = post.estimated_traffic_potential === 'high' ? 'text-green-600 bg-green-50' : post.estimated_traffic_potential === 'medium' ? 'text-yellow-600 bg-yellow-50' : 'text-gray-500 bg-gray-100'
              return (
                <div key={i} className="border border-gray-100 rounded-xl overflow-hidden">
                  <button className="w-full flex items-start gap-3 p-4 text-left hover:bg-gray-50 transition" onClick={() => setBlogExpanded(p => ({ ...p, [i]: !p[i] }))}>
                    <span className="text-xs font-bold text-gray-300 mt-0.5 w-4 flex-shrink-0">{i + 1}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-800 leading-tight mb-1.5">{post.title}</p>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full font-medium">{post.target_keyword}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${trafficColor}`}>
                          {post.estimated_traffic_potential === 'high' ? '🔥' : post.estimated_traffic_potential === 'medium' ? '📈' : '📊'} {post.estimated_traffic_potential} traffic
                        </span>
                      </div>
                    </div>
                    {isExp ? <ChevronUp size={14} className="text-gray-400 flex-shrink-0 mt-1" /> : <ChevronDown size={14} className="text-gray-400 flex-shrink-0 mt-1" />}
                  </button>
                  {isExp && (
                    <div className="px-4 pb-4 space-y-3 border-t border-gray-50">
                      <p className="text-xs text-gray-500 pt-3"><span className="font-semibold">Search intent:</span> {post.search_intent}</p>
                      <p className="text-xs text-gray-500"><span className="font-semibold">Why it ranks:</span> {post.why_it_ranks}</p>
                      {post.outline?.length > 0 && (
                        <div>
                          <p className="text-xs font-semibold text-gray-400 mb-2">SUGGESTED OUTLINE</p>
                          <div className="space-y-1">
                            {post.outline.map((h, j) => (
                              <div key={j} className="flex items-center gap-2">
                                <span className="w-1 h-1 bg-indigo-400 rounded-full flex-shrink-0" />
                                <p className="text-xs text-indigo-700">{h}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Content clusters */}
      {seo.content_clusters?.length > 0 && (
        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-xl bg-teal-50 flex items-center justify-center">
              <Link size={16} className="text-teal-600" />
            </div>
            <h2 className="font-bold text-gray-800">Content Clusters</h2>
            <span className="ml-auto text-xs text-gray-400">Build topical authority</span>
          </div>
          <div className="space-y-3">
            {seo.content_clusters.map((cluster, i) => (
              <div key={i} className="border border-teal-100 bg-teal-50/30 rounded-xl overflow-hidden">
                <button className="w-full flex items-center gap-3 p-4 text-left hover:bg-teal-50 transition" onClick={() => setClusterExpanded(p => ({ ...p, [i]: !p[i] }))}>
                  <div className="w-7 h-7 rounded-lg bg-teal-100 flex items-center justify-center flex-shrink-0">
                    <span className="text-xs font-bold text-teal-700">P</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold text-gray-800 leading-tight">{cluster.pillar_page}</p>
                    <p className="text-xs text-teal-600 mt-0.5">Pillar: {cluster.target_keyword}</p>
                  </div>
                  <span className="text-xs text-gray-400 flex-shrink-0">{cluster.supporting_articles?.length || 0} articles</span>
                  {clusterExpanded[i] ? <ChevronUp size={13} className="text-gray-400" /> : <ChevronDown size={13} className="text-gray-400" />}
                </button>
                {clusterExpanded[i] && (
                  <div className="px-4 pb-4 space-y-1.5 border-t border-teal-100">
                    {(cluster.supporting_articles || []).map((art, j) => (
                      <div key={j} className="flex items-center gap-2 py-1">
                        <ArrowUpRight size={11} className="text-teal-400 flex-shrink-0" />
                        <p className="text-xs text-gray-600">{art}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* On-page tips + technical wins */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {seo.on_page_seo_tips?.length > 0 && (
          <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-xl bg-indigo-50 flex items-center justify-center">
                <CheckCircle2 size={16} className="text-indigo-600" />
              </div>
              <h2 className="font-bold text-gray-800 text-sm">On-Page SEO Tips</h2>
            </div>
            <div className="space-y-2.5">
              {seo.on_page_seo_tips.map((tip, i) => {
                const effortCfg = EFFORT_CONFIG[tip.effort] || EFFORT_CONFIG.medium
                const priorityDot = PRIORITY_DOT[tip.priority] || PRIORITY_DOT.medium
                return (
                  <div key={i} className="flex items-start gap-2.5">
                    <span className={`w-2 h-2 rounded-full flex-shrink-0 mt-1.5 ${priorityDot}`} />
                    <div className="flex-1">
                      <p className="text-xs text-gray-700 leading-relaxed">{tip.tip}</p>
                      <span className={`text-xs mt-1 inline-block px-1.5 py-0.5 rounded-full font-medium ${effortCfg.bg} ${effortCfg.text}`}>{effortCfg.label}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {(seo.technical_seo_wins?.length > 0 || seo.local_seo_tips?.length > 0) && (
          <div className="space-y-4">
            {seo.technical_seo_wins?.length > 0 && (
              <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-8 h-8 rounded-xl bg-gray-100 flex items-center justify-center">
                    <Zap size={16} className="text-gray-600" />
                  </div>
                  <h2 className="font-bold text-gray-800 text-sm">Technical Quick Wins</h2>
                </div>
                <div className="space-y-2">
                  {seo.technical_seo_wins.map((win, i) => (
                    <div key={i} className="flex items-start gap-2">
                      <span className="text-teal-500 mt-0.5 flex-shrink-0">✓</span>
                      <p className="text-xs text-gray-600 leading-relaxed">{win}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {seo.local_seo_tips?.length > 0 && (
              <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-8 h-8 rounded-xl bg-orange-50 flex items-center justify-center">
                    <span className="text-sm">🇮🇳</span>
                  </div>
                  <h2 className="font-bold text-gray-800 text-sm">India Local SEO</h2>
                </div>
                <div className="space-y-2">
                  {seo.local_seo_tips.map((tip, i) => (
                    <div key={i} className="flex items-start gap-2">
                      <span className="text-orange-400 mt-0.5 flex-shrink-0">📍</span>
                      <p className="text-xs text-gray-600 leading-relaxed">{tip}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Competitor keyword gaps */}
      {seo.competitor_keyword_gaps?.length > 0 && (
        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-xl bg-amber-50 flex items-center justify-center">
              <AlertTriangle size={16} className="text-amber-500" />
            </div>
            <h2 className="font-bold text-gray-800">Competitor Keyword Gaps</h2>
            <span className="ml-auto text-xs text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full font-medium">Steal their traffic</span>
          </div>
          <div className="space-y-2">
            {seo.competitor_keyword_gaps.map((gap, i) => (
              <div key={i} className="border border-amber-100 bg-amber-50/40 rounded-xl p-3.5">
                <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                  <p className="text-sm font-bold text-gray-800">{gap.keyword}</p>
                  <span className="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded-full">{gap.competitor} ranks here</span>
                </div>
                <p className="text-xs text-amber-800 leading-relaxed">💡 {gap.opportunity}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function ContentPlaybook() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [regenerating, setRegenerating] = useState(false)
  const [activeTab, setActiveTab] = useState('linkedin')
  const [error, setError] = useState(null)

  const load = async (forceRefresh = false) => {
    if (forceRefresh) setRegenerating(true)
    else setLoading(true)
    setError(null)
    try {
      const res = await getContentRecommendations(forceRefresh)
      setData(res.data)
    } catch (e) {
      setError('Could not load recommendations. Make sure the backend is running.')
      console.error(e)
    } finally {
      setLoading(false)
      setRegenerating(false)
    }
  }

  useEffect(() => { load(false) }, [])

  const tabs = [
    { id: 'linkedin',  label: 'LinkedIn',  icon: Linkedin,  color: '#0077B5' },
    { id: 'instagram', label: 'Instagram', icon: Instagram, color: '#E1306C' },
    { id: 'seo',       label: 'SEO',       icon: Search,    color: '#059669' },
    { id: 'calendar',  label: 'Calendar',  icon: Calendar,  color: '#2EC4B6' },
    { id: 'tactics',   label: 'Lead Gen',  icon: Target,    color: '#22C55E' },
  ]

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-[#1a1a2e]">Content Playbook</h1>
          <p className="text-gray-500 text-sm mt-1">
            AI-powered LinkedIn, Instagram & SEO playbook — built from competitor intelligence to drive engagement and organic leads
          </p>
        </div>
        <div className="flex items-center gap-2">
          {data?.generated_at && (
            <p className="text-xs text-gray-400">
              Updated {formatDistanceToNow(new Date(data.generated_at), { addSuffix: true })}
            </p>
          )}
          <button
            onClick={() => load(true)}
            disabled={regenerating || loading}
            className="flex items-center gap-1.5 px-4 py-2 bg-[#1a1a2e] text-white rounded-xl text-sm font-medium hover:bg-[#2a2a4e] transition disabled:opacity-60"
          >
            <RefreshCw size={14} className={regenerating ? 'animate-spin' : ''} />
            {regenerating ? 'Generating...' : 'Regenerate with AI'}
          </button>
        </div>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-24 bg-white rounded-2xl border border-gray-100">
          <div className="w-10 h-10 border-4 border-[#2EC4B6] border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-gray-500 font-medium">Generating your content playbook with AI...</p>
          <p className="text-gray-400 text-sm mt-1">Analysing competitor landscape & crafting post recommendations</p>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div className="bg-red-50 border border-red-100 rounded-2xl p-5 flex items-start gap-3">
          <AlertCircle size={18} className="text-red-500 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Content */}
      {data && !loading && (
        <>
          {/* Quick summary bar */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {[
              { label: 'LinkedIn Post Types',  value: data.linkedin?.post_types?.length || 0,           icon: Linkedin,  color: '#0077B5' },
              { label: 'Instagram Post Types', value: data.instagram?.post_types?.length || 0,          icon: Instagram, color: '#E1306C' },
              { label: 'SEO Keywords',         value: (data.seo?.primary_keywords?.length || 0) + (data.seo?.long_tail_keywords?.length || 0), icon: Search, color: '#059669' },
              { label: 'Blog Ideas',           value: data.seo?.blog_content_ideas?.length || 0,        icon: FileText,  color: '#F97316' },
              { label: 'Content Gaps Found',   value: data.competitor_gaps?.length || 0,                icon: Lightbulb, color: '#F7B731' },
              { label: 'Lead Gen Tactics',     value: data.lead_gen_tactics?.length || 0,               icon: Target,    color: '#22C55E' },
            ].map(({ label, value, icon: Icon, color }) => (
              <div key={label} className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs text-gray-400 mb-1">{label}</p>
                    <p className="text-2xl font-bold text-gray-800">{value}</p>
                  </div>
                  <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ background: `${color}20` }}>
                    <Icon size={17} style={{ color }} />
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Tabs */}
          <div className="flex gap-1 bg-white rounded-2xl p-1.5 border border-gray-100 shadow-sm w-fit">
            {tabs.map(({ id, label, icon: Icon, color }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition
                  ${activeTab === id
                    ? 'text-white shadow-sm'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'}`}
                style={activeTab === id ? { background: color } : {}}
              >
                <Icon size={14} />
                {label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          {activeTab === 'linkedin' && (
            <PlatformPanel data={data.linkedin} platform="linkedin" />
          )}
          {activeTab === 'instagram' && (
            <PlatformPanel data={data.instagram} platform="instagram" />
          )}
          {activeTab === 'seo' && (
            <SeoSection seo={data.seo} />
          )}
          {activeTab === 'calendar' && (
            <div className="space-y-5">
              <ContentCalendar calendar={data.content_calendar} />
              <CompetitorGaps gaps={data.competitor_gaps} />
            </div>
          )}
          {activeTab === 'tactics' && (
            <div className="space-y-5">
              <LeadGenTactics tactics={data.lead_gen_tactics} />
              <CompetitorGaps gaps={data.competitor_gaps} />
            </div>
          )}
        </>
      )}
    </div>
  )
}
