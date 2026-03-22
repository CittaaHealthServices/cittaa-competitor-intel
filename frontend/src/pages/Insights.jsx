import React, { useState, useEffect } from 'react'
import { getInsights, markInsightRead, generateWeeklyInsights } from '../services/api'
import { formatDistanceToNow } from 'date-fns'
import { TrendingUp, AlertTriangle, Lightbulb, Zap, CheckCircle, RefreshCw } from 'lucide-react'

const INSIGHT_CONFIG = {
  trend:       { icon: TrendingUp,   color: '#2EC4B6', bg: 'bg-teal-50 border-teal-200',   label: 'Trend' },
  threat:      { icon: AlertTriangle, color: '#FF4757', bg: 'bg-red-50 border-red-200',      label: 'Threat' },
  opportunity: { icon: Lightbulb,    color: '#FFA502', bg: 'bg-orange-50 border-orange-200', label: 'Opportunity' },
  alert:       { icon: Zap,          color: '#6C63FF', bg: 'bg-purple-50 border-purple-200', label: 'Alert' },
}

const IMPORTANCE_BADGE = {
  critical: 'bg-red-100 text-red-700',
  high:     'bg-orange-100 text-orange-700',
  medium:   'bg-yellow-100 text-yellow-700',
  low:      'bg-green-100 text-green-700',
}

function InsightCard({ insight, onRead }) {
  const config = INSIGHT_CONFIG[insight.insight_type] || INSIGHT_CONFIG.trend
  const Icon = config.icon
  const imp = IMPORTANCE_BADGE[insight.importance] || IMPORTANCE_BADGE.medium

  return (
    <div className={`bg-white rounded-2xl border-2 ${config.bg} p-5 fade-in ${insight.is_read ? 'opacity-60' : ''}`}>
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: config.color + '20' }}>
          <Icon size={18} style={{ color: config.color }} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <span className="font-bold text-xs uppercase" style={{ color: config.color }}>{config.label}</span>
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${imp}`}>
              {insight.importance?.toUpperCase()}
            </span>
            {!insight.is_read && (
              <span className="w-2 h-2 bg-[#2EC4B6] rounded-full ml-auto flex-shrink-0" title="Unread" />
            )}
          </div>

          <h3 className="font-bold text-gray-800 text-sm mb-2">{insight.title}</h3>
          <p className="text-gray-600 text-sm leading-relaxed">{insight.content}</p>

          {insight.action_items && insight.action_items.length > 0 && (
            <div className="mt-3 p-3 bg-white rounded-xl">
              <p className="text-xs font-semibold text-gray-500 mb-2">Action Items:</p>
              {insight.action_items.map((a, i) => (
                <p key={i} className="text-sm text-gray-700 flex items-start gap-2">
                  <span className="text-[#2EC4B6] font-bold">→</span> {a}
                </p>
              ))}
            </div>
          )}

          {insight.competitor_names && insight.competitor_names.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-3">
              {insight.competitor_names.map(n => (
                <span key={n} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{n}</span>
              ))}
            </div>
          )}

          <div className="flex items-center justify-between mt-3">
            <span className="text-xs text-gray-400">
              {formatDistanceToNow(new Date(insight.generated_at), { addSuffix: true })}
            </span>
            {!insight.is_read && (
              <button onClick={() => onRead(insight.id)}
                className="flex items-center gap-1 text-xs text-[#2EC4B6] hover:underline font-medium">
                <CheckCircle size={12} /> Mark read
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function InsightsPage() {
  const [insights, setInsights] = useState([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [filter, setFilter] = useState('all')
  const [toast, setToast] = useState('')

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 3000) }

  const load = async () => {
    const r = await getInsights({ days: 30 })
    setInsights(r.data)
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const handleRead = async (id) => {
    await markInsightRead(id)
    setInsights(p => p.map(i => i.id === id ? { ...i, is_read: true } : i))
  }

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      await generateWeeklyInsights()
      showToast('📊 Generating weekly insights... check back in a few minutes')
      setTimeout(load, 5000)
    } finally {
      setGenerating(false)
    }
  }

  const filtered = filter === 'all' ? insights : insights.filter(i => i.insight_type === filter)
  const unread = insights.filter(i => !i.is_read).length

  const TYPES = [
    { key: 'all',         label: 'All',           count: insights.length },
    { key: 'threat',      label: '⚠️ Threats',    count: insights.filter(i => i.insight_type === 'threat').length },
    { key: 'opportunity', label: '💡 Opportunities', count: insights.filter(i => i.insight_type === 'opportunity').length },
    { key: 'trend',       label: '📈 Trends',     count: insights.filter(i => i.insight_type === 'trend').length },
    { key: 'alert',       label: '🚨 Alerts',     count: insights.filter(i => i.insight_type === 'alert').length },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#1a1a2e]">
            Insights
            {unread > 0 && <span className="ml-2 text-sm bg-[#2EC4B6] text-white px-2 py-0.5 rounded-full">{unread} new</span>}
          </h1>
          <p className="text-gray-500 text-sm mt-1">AI-generated strategic intelligence for Cittaa</p>
        </div>
        <button onClick={handleGenerate} disabled={generating}
          className="flex items-center gap-1.5 px-4 py-2 bg-[#1a1a2e] text-white rounded-xl text-sm font-semibold hover:bg-[#2a2a4e] transition disabled:opacity-60">
          <RefreshCw size={14} className={generating ? 'animate-spin' : ''} />
          Generate Weekly Report
        </button>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {TYPES.map(t => (
          <button key={t.key} onClick={() => setFilter(t.key)}
            className={`flex-shrink-0 flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-medium transition ${
              filter === t.key ? 'bg-[#1a1a2e] text-white' : 'bg-white text-gray-500 hover:bg-gray-100'
            }`}>
            {t.label}
            {t.count > 0 && <span className="text-xs opacity-70">({t.count})</span>}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="w-8 h-8 border-4 border-[#2EC4B6] border-t-transparent rounded-full animate-spin" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl">
          <p className="text-4xl mb-3">💡</p>
          <p className="text-gray-500 mb-4">No insights yet. Generate a weekly report or let the scraper run.</p>
          <button onClick={handleGenerate} className="px-4 py-2 bg-[#2EC4B6] text-white rounded-xl text-sm font-semibold hover:bg-[#0b6e6e]">
            Generate Now
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {filtered.map(i => <InsightCard key={i.id} insight={i} onRead={handleRead} />)}
        </div>
      )}

      {toast && (
        <div className="fixed bottom-6 right-6 bg-[#1a1a2e] text-white px-4 py-3 rounded-xl shadow-xl z-50 fade-in text-sm">{toast}</div>
      )}
    </div>
  )
}
