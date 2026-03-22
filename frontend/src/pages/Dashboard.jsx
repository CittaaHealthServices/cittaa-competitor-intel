import React, { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts'
import { getDashboardStats, getTopPosts, getPlatformBreakdown, getCompetitorActivity, getSentimentData, getInsights } from '../services/api'
import { TrendingUp, Globe2, Zap, AlertCircle, Eye, ThumbsUp, MessageCircle, Share2, ChevronRight } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { PLATFORM_META } from '../App'

const COLORS = ['#2EC4B6', '#1a1a2e', '#FF6B35', '#6C63FF', '#FF0000', '#1DA1F2', '#F7B731']

function StatCard({ icon: Icon, label, value, sub, color = '#2EC4B6' }) {
  return (
    <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 fade-in">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-gray-500 text-sm font-medium">{label}</p>
          <p className="text-3xl font-bold mt-1" style={{ color }}>{value ?? '—'}</p>
          {sub && <p className="text-gray-400 text-xs mt-1">{sub}</p>}
        </div>
        <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: color + '20' }}>
          <Icon size={20} style={{ color }} />
        </div>
      </div>
    </div>
  )
}

function PostCard({ post }) {
  const meta = PLATFORM_META[post.platform] || { label: post.platform, color: '#888', emoji: '📌' }
  const score = post.ai_importance_score || 0

  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 fade-in hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-3">
        <span
          className="px-2 py-1 rounded-full text-white text-xs font-semibold"
          style={{ background: meta.color }}
        >
          {meta.emoji} {meta.label}
        </span>
        <div className="flex items-center gap-2">
          {post.is_viral && (
            <span className="px-2 py-1 bg-orange-100 text-orange-600 rounded-full text-xs font-semibold">🔥 Viral</span>
          )}
          <span className="text-xs font-semibold px-2 py-1 rounded-full"
            style={{
              background: score >= 8 ? '#FF475720' : score >= 6 ? '#FFA50220' : '#2EC4B620',
              color: score >= 8 ? '#FF4757' : score >= 6 ? '#FFA502' : '#2EC4B6'
            }}
          >
            ⚡ {score.toFixed(1)}
          </span>
        </div>
      </div>

      <p className="font-semibold text-sm text-gray-800 mb-1">{post.competitor_name}</p>
      <p className="text-gray-600 text-sm line-clamp-2 mb-3">
        {post.ai_summary || post.content || post.title || '—'}
      </p>

      {post.ai_tags && post.ai_tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {post.ai_tags.slice(0, 3).map(tag => (
            <span key={tag} className="bg-[#2EC4B6]/10 text-[#2EC4B6] text-xs px-2 py-0.5 rounded-full">{tag}</span>
          ))}
        </div>
      )}

      <div className="flex items-center justify-between text-gray-400 text-xs">
        <div className="flex items-center gap-3">
          {post.likes > 0 && <span className="flex items-center gap-1"><ThumbsUp size={11} /> {post.likes}</span>}
          {post.comments > 0 && <span className="flex items-center gap-1"><MessageCircle size={11} /> {post.comments}</span>}
          {post.shares > 0 && <span className="flex items-center gap-1"><Share2 size={11} /> {post.shares}</span>}
        </div>
        {post.published_at && (
          <span>{formatDistanceToNow(new Date(post.published_at), { addSuffix: true })}</span>
        )}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [topPosts, setTopPosts] = useState([])
  const [platformData, setPlatformData] = useState([])
  const [competitorData, setCompetitorData] = useState([])
  const [sentimentData, setSentimentData] = useState([])
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const [s, p, pl, ca, sent, ins] = await Promise.all([
          getDashboardStats(),
          getTopPosts(7, 8),
          getPlatformBreakdown(7),
          getCompetitorActivity(7),
          getSentimentData(7),
          getInsights({ days: 7 })
        ])
        setStats(s.data)
        setTopPosts(p.data)
        setPlatformData(pl.data.map(d => ({ ...d, name: PLATFORM_META[d.platform]?.label || d.platform })))
        setCompetitorData(ca.data)
        setSentimentData([
          { name: 'Positive', value: sent.data.find(d => d.sentiment === 'positive')?.count || 0, color: '#2EC4B6' },
          { name: 'Neutral', value: sent.data.find(d => d.sentiment === 'neutral')?.count || 0, color: '#94a3b8' },
          { name: 'Negative', value: sent.data.find(d => d.sentiment === 'negative')?.count || 0, color: '#FF4757' },
        ])
        setAlerts(ins.data.filter(i => ['high', 'critical'].includes(i.importance)).slice(0, 3))
      } catch (e) {
        console.error('Dashboard load error:', e)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <div className="w-10 h-10 border-4 border-[#2EC4B6] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-gray-500 text-sm">Loading intelligence data...</p>
      </div>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Page title */}
      <div>
        <h1 className="text-2xl font-bold text-[#1a1a2e]">
          <span className="cittaa-brand text-[#2EC4B6]">Cittaa</span> Intelligence Dashboard
        </h1>
        <p className="text-gray-500 text-sm mt-1">Monitoring {stats?.active_competitors || 0} competitors across all platforms · Updated every 6 hours</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard icon={Eye}          label="Posts Today"       value={stats?.total_posts_today}  color="#2EC4B6" />
        <StatCard icon={TrendingUp}   label="Posts This Week"   value={stats?.total_posts_week}   color="#1a1a2e" />
        <StatCard icon={Globe2}       label="Competitors"       value={stats?.active_competitors} color="#6C63FF" />
        <StatCard icon={Zap}          label="Viral Posts"       value={stats?.viral_posts}        color="#FF6B35" />
        <StatCard icon={AlertCircle}  label="Critical Alerts"   value={stats?.critical_alerts}    color="#FF4757" />
        <StatCard icon={TrendingUp}   label="Top Platform"      value={stats?.top_platform?.toUpperCase() || '—'} color="#F7B731" />
      </div>

      {/* Alerts banner */}
      {alerts.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-4">
          <h3 className="font-semibold text-red-700 text-sm mb-2">⚠️ High Priority Alerts</h3>
          {alerts.map(a => (
            <div key={a.id} className="text-sm text-red-600 flex items-start gap-2 mb-1">
              <ChevronRight size={14} className="mt-0.5 flex-shrink-0" />
              <span>{a.title}</span>
            </div>
          ))}
        </div>
      )}

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* Platform breakdown */}
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-700 mb-4 text-sm">Posts by Platform</h3>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={platformData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <XAxis dataKey="name" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }} />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {platformData.map((entry, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Competitor activity */}
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-700 mb-4 text-sm">Competitor Activity (7d)</h3>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={competitorData.slice(0, 6)} layout="vertical" margin={{ top: 0, right: 10, left: 50, bottom: 0 }}>
              <XAxis type="number" tick={{ fontSize: 10 }} />
              <YAxis type="category" dataKey="competitor" tick={{ fontSize: 9 }} width={50} />
              <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }} />
              <Bar dataKey="total_posts" fill="#2EC4B6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Sentiment pie */}
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-700 mb-4 text-sm">Sentiment Breakdown</h3>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={sentimentData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} dataKey="value">
                {sentimentData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(v, n) => [v, n]} contentStyle={{ borderRadius: 8, fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-4 mt-2">
            {sentimentData.map(s => (
              <div key={s.name} className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full" style={{ background: s.color }} />
                <span className="text-xs text-gray-500">{s.name}: {s.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top posts */}
      <div>
        <h2 className="text-lg font-bold text-[#1a1a2e] mb-3">🔥 Top Posts This Week</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          {topPosts.length > 0
            ? topPosts.map(p => <PostCard key={p.id} post={p} />)
            : <p className="text-gray-400 text-sm col-span-4 py-8 text-center">No posts found yet. Click "Scrape Now" to start monitoring.</p>
          }
        </div>
      </div>
    </div>
  )
}
