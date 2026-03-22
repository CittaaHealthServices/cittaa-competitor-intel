import React, { useState, useEffect } from 'react'
import { getPosts, getCompetitors } from '../services/api'
import { formatDistanceToNow } from 'date-fns'
import { ExternalLink, ThumbsUp, MessageCircle, Share2, Eye } from 'lucide-react'
import { PLATFORM_META } from '../App'

const SENTIMENT_CONFIG = {
  positive: { color: '#2EC4B6', label: '😊 Positive', bg: 'bg-teal-50 text-teal-700' },
  neutral:  { color: '#94a3b8', label: '😐 Neutral',  bg: 'bg-gray-50 text-gray-600' },
  negative: { color: '#FF4757', label: '😟 Negative', bg: 'bg-red-50 text-red-600' },
}

function PostItem({ post }) {
  const [expanded, setExpanded] = useState(false)
  const meta = PLATFORM_META[post.platform] || { label: post.platform, color: '#888', emoji: '📌' }
  const sent = SENTIMENT_CONFIG[post.sentiment] || SENTIMENT_CONFIG.neutral
  const score = post.ai_importance_score || 0

  const scoreColor = score >= 8 ? 'bg-red-100 text-red-600' : score >= 6 ? 'bg-orange-100 text-orange-600' : 'bg-green-100 text-green-600'

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden fade-in hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-50">
        <span className="px-2 py-1 rounded-full text-white text-xs font-semibold" style={{ background: meta.color }}>
          {meta.emoji} {meta.label}
        </span>
        <span className="font-semibold text-sm text-gray-700">{post.competitor_name}</span>
        {post.author_type && post.author_type !== 'company' && (
          <span className="text-xs text-gray-400 bg-gray-50 px-2 py-0.5 rounded-full">{post.author_name || post.author_type}</span>
        )}
        <div className="ml-auto flex items-center gap-2">
          {post.is_viral && <span className="text-xs bg-orange-100 text-orange-600 px-2 py-0.5 rounded-full font-semibold">🔥 Viral</span>}
          <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${scoreColor}`}>⚡ {score.toFixed(1)}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full ${sent.bg}`}>{sent.label}</span>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 py-3">
        {post.title && <p className="font-semibold text-sm text-gray-800 mb-2">{post.title}</p>}

        {post.ai_summary && (
          <div className="bg-[#2EC4B6]/5 border border-[#2EC4B6]/20 rounded-xl px-3 py-2 mb-3">
            <p className="text-xs text-[#0b6e6e] font-semibold mb-0.5">🤖 AI Summary</p>
            <p className="text-sm text-gray-700">{post.ai_summary}</p>
          </div>
        )}

        {post.content && (
          <div>
            <p className={`text-sm text-gray-600 leading-relaxed ${expanded ? '' : 'line-clamp-3'}`}>{post.content}</p>
            {post.content.length > 200 && (
              <button onClick={() => setExpanded(p => !p)} className="text-xs text-[#2EC4B6] mt-1 font-medium hover:underline">
                {expanded ? 'Show less' : 'Show more'}
              </button>
            )}
          </div>
        )}

        {post.ai_tags && post.ai_tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {post.ai_tags.map(tag => (
              <span key={tag} className="text-xs bg-[#2EC4B6]/10 text-[#2EC4B6] px-2 py-0.5 rounded-full">{tag}</span>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-50/50 border-t border-gray-50">
        <div className="flex items-center gap-4 text-gray-400 text-xs">
          {post.likes > 0 && <span className="flex items-center gap-1"><ThumbsUp size={11} /> {post.likes.toLocaleString()}</span>}
          {post.comments > 0 && <span className="flex items-center gap-1"><MessageCircle size={11} /> {post.comments.toLocaleString()}</span>}
          {post.shares > 0 && <span className="flex items-center gap-1"><Share2 size={11} /> {post.shares.toLocaleString()}</span>}
          {post.views > 0 && <span className="flex items-center gap-1"><Eye size={11} /> {post.views.toLocaleString()}</span>}
        </div>
        <div className="flex items-center gap-3">
          {post.published_at && (
            <span className="text-xs text-gray-400">{formatDistanceToNow(new Date(post.published_at), { addSuffix: true })}</span>
          )}
          {post.url && (
            <a href={post.url} target="_blank" rel="noreferrer"
              className="flex items-center gap-1 text-xs text-[#2EC4B6] hover:underline font-medium">
              View <ExternalLink size={10} />
            </a>
          )}
        </div>
      </div>
    </div>
  )
}

export default function Feed() {
  const [posts, setPosts] = useState([])
  const [competitors, setCompetitors] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ platform: '', competitor_id: '', sentiment: '', days: 7, min_score: 0 })
  const [page, setPage] = useState(1)

  const load = async () => {
    setLoading(true)
    try {
      const [p, c] = await Promise.all([
        getPosts({ ...filters, page, page_size: 20 }),
        getCompetitors()
      ])
      setPosts(p.data)
      setCompetitors(c.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [filters, page])

  const handleFilter = (key, value) => {
    setFilters(p => ({ ...p, [key]: value }))
    setPage(1)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[#1a1a2e]">Live Feed</h1>
        <p className="text-gray-500 text-sm mt-1">Real-time competitor activity across all platforms</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <select value={filters.platform} onChange={e => handleFilter('platform', e.target.value)}
            className="border rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[#2EC4B6]">
            <option value="">All Platforms</option>
            {Object.entries(PLATFORM_META).map(([k, v]) => (
              <option key={k} value={k}>{v.emoji} {v.label}</option>
            ))}
          </select>

          <select value={filters.competitor_id} onChange={e => handleFilter('competitor_id', e.target.value)}
            className="border rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[#2EC4B6]">
            <option value="">All Competitors</option>
            {competitors.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>

          <select value={filters.sentiment} onChange={e => handleFilter('sentiment', e.target.value)}
            className="border rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[#2EC4B6]">
            <option value="">All Sentiments</option>
            <option value="positive">😊 Positive</option>
            <option value="neutral">😐 Neutral</option>
            <option value="negative">😟 Negative</option>
          </select>

          <select value={filters.days} onChange={e => handleFilter('days', parseInt(e.target.value))}
            className="border rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[#2EC4B6]">
            <option value={1}>Last 24h</option>
            <option value={7}>Last 7 days</option>
            <option value={14}>Last 14 days</option>
            <option value={30}>Last 30 days</option>
          </select>

          <select value={filters.min_score} onChange={e => handleFilter('min_score', parseFloat(e.target.value))}
            className="border rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[#2EC4B6]">
            <option value={0}>All Scores</option>
            <option value={5}>Score ≥ 5</option>
            <option value={7}>Score ≥ 7 (High)</option>
            <option value={9}>Score ≥ 9 (Critical)</option>
          </select>
        </div>
      </div>

      {/* Posts */}
      {loading ? (
        <div className="flex justify-center py-16">
          <div className="w-8 h-8 border-4 border-[#2EC4B6] border-t-transparent rounded-full animate-spin" />
        </div>
      ) : posts.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl">
          <p className="text-4xl mb-3">🔍</p>
          <p className="text-gray-500">No posts found. Try adjusting filters or click "Scrape Now" to fetch data.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {posts.map(p => <PostItem key={p.id} post={p} />)}
          <div className="flex justify-center gap-3 pt-4">
            <button disabled={page === 1} onClick={() => setPage(p => p - 1)}
              className="px-4 py-2 bg-white border rounded-xl text-sm disabled:opacity-40 hover:bg-gray-50">← Prev</button>
            <span className="px-4 py-2 text-sm text-gray-500">Page {page}</span>
            <button disabled={posts.length < 20} onClick={() => setPage(p => p + 1)}
              className="px-4 py-2 bg-white border rounded-xl text-sm disabled:opacity-40 hover:bg-gray-50">Next →</button>
          </div>
        </div>
      )}
    </div>
  )
}
