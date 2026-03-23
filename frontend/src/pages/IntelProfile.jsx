import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'
import {
  ExternalLink, RefreshCw, ArrowLeft, Star, Download,
  Briefcase, DollarSign, Code2, Smartphone, Users,
  TrendingUp, ChevronDown, ChevronUp, AlertCircle
} from 'lucide-react'
import {
  getCompetitors, getCompetitorIntel, refreshCompetitorIntel,
  getCompetitorJobs, getCompetitorFundingNews, getAppStoreReviews
} from '../services/api'

function RatingStars({ rating, max = 5 }) {
  const pct = Math.round((rating / max) * 100)
  return (
    <div className="flex items-center gap-2">
      <div className="flex gap-0.5">
        {[1, 2, 3, 4, 5].map(i => (
          <Star
            key={i}
            size={14}
            fill={i <= Math.round(rating) ? '#F7B731' : 'none'}
            stroke={i <= Math.round(rating) ? '#F7B731' : '#ccc'}
          />
        ))}
      </div>
      <span className="font-bold text-gray-800">{rating?.toFixed(1)}</span>
    </div>
  )
}

function StatCard({ label, value, sub, color = '#2EC4B6', icon: Icon }) {
  return (
    <div className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-400 mb-1">{label}</p>
          <p className="text-2xl font-bold text-gray-800">{value ?? '—'}</p>
          {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
        </div>
        {Icon && (
          <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ background: `${color}20` }}>
            <Icon size={18} style={{ color }} />
          </div>
        )}
      </div>
    </div>
  )
}

function SectionHeader({ title, icon: Icon, color = '#2EC4B6', count }) {
  return (
    <div className="flex items-center gap-2 mb-4">
      {Icon && (
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${color}20` }}>
          <Icon size={16} style={{ color }} />
        </div>
      )}
      <h2 className="font-bold text-gray-800">{title}</h2>
      {count !== undefined && (
        <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">{count}</span>
      )}
    </div>
  )
}

function AppStoreSection({ intel }) {
  const appStore = intel?.app_store
  const gp = appStore?.google_play
  const ap = appStore?.apple
  const reviews = appStore?.top_reviews || []

  if (!gp && !ap) return (
    <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
      <SectionHeader title="App Store Intelligence" icon={Smartphone} color="#34A853" />
      <p className="text-sm text-gray-400">No app store data yet. Refresh intel to fetch.</p>
    </div>
  )

  return (
    <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
      <SectionHeader title="App Store Intelligence" icon={Smartphone} color="#34A853" />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
        {gp && (
          <div className="bg-gray-50 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lg">🤖</span>
              <span className="font-semibold text-sm text-gray-700">Google Play</span>
              {gp.url && <a href={gp.url} target="_blank" rel="noreferrer" className="ml-auto"><ExternalLink size={13} className="text-gray-400 hover:text-gray-700" /></a>}
            </div>
            <RatingStars rating={gp.rating} />
            <div className="mt-2 space-y-1 text-xs text-gray-500">
              {gp.reviews_count > 0 && <p>{gp.reviews_count?.toLocaleString()} reviews</p>}
              {gp.installs && <p>📥 {gp.installs} installs</p>}
              {gp.version && <p>v{gp.version}</p>}
              {gp.last_updated && <p>Updated: {gp.last_updated}</p>}
            </div>
          </div>
        )}
        {ap && (
          <div className="bg-gray-50 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lg">🍎</span>
              <span className="font-semibold text-sm text-gray-700">App Store (iOS)</span>
              {ap.url && <a href={ap.url} target="_blank" rel="noreferrer" className="ml-auto"><ExternalLink size={13} className="text-gray-400 hover:text-gray-700" /></a>}
            </div>
            <RatingStars rating={ap.rating} />
            <div className="mt-2 space-y-1 text-xs text-gray-500">
              {ap.reviews_count > 0 && <p>{ap.reviews_count?.toLocaleString()} ratings</p>}
              {ap.version && <p>v{ap.version}</p>}
              {ap.last_updated && <p>Updated: {ap.last_updated?.slice(0, 10)}</p>}
            </div>
          </div>
        )}
      </div>

      {reviews.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-500 mb-2">TOP USER REVIEWS</p>
          <div className="space-y-2">
            {reviews.slice(0, 3).map((r, i) => (
              <div key={i} className="bg-yellow-50 border border-yellow-100 rounded-xl p-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-semibold text-gray-700">{r.author || 'User'}</span>
                  <span className="text-yellow-500 text-xs">{'⭐'.repeat(Math.min(r.rating || 5, 5))}</span>
                </div>
                <p className="text-xs text-gray-600 leading-relaxed">{r.text}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function FundingSection({ intel, fundingPosts }) {
  const funding = intel?.funding

  return (
    <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
      <SectionHeader title="Funding & Company Intelligence" icon={DollarSign} color="#F7B731" />

      {(funding?.total || funding?.last_round) && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-5">
          {funding.total && (
            <div className="bg-yellow-50 rounded-xl p-3">
              <p className="text-xs text-gray-400">Total Raised</p>
              <p className="font-bold text-gray-800 text-lg">{funding.total}</p>
            </div>
          )}
          {funding.last_round && (
            <div className="bg-yellow-50 rounded-xl p-3">
              <p className="text-xs text-gray-400">Last Round</p>
              <p className="font-bold text-gray-800">{funding.last_round}</p>
              {funding.last_round_year && <p className="text-xs text-gray-400">{funding.last_round_year}</p>}
            </div>
          )}
          {funding.crunchbase_url && (
            <div className="flex items-center">
              <a href={funding.crunchbase_url} target="_blank" rel="noreferrer"
                className="flex items-center gap-1 text-xs text-[#2EC4B6] hover:underline font-medium">
                View on Crunchbase <ExternalLink size={11} />
              </a>
            </div>
          )}
        </div>
      )}

      {fundingPosts.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-500 mb-2">FUNDING NEWS</p>
          <div className="space-y-2">
            {fundingPosts.slice(0, 5).map((p, i) => (
              <div key={i} className="flex items-start gap-3 py-2 border-b border-gray-50 last:border-0">
                <span className="text-lg flex-shrink-0">💰</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-700 line-clamp-1">{p.title?.replace('💰 ', '')}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{p.author_name}</p>
                </div>
                {p.url && (
                  <a href={p.url} target="_blank" rel="noreferrer">
                    <ExternalLink size={13} className="text-gray-300 hover:text-gray-600 flex-shrink-0 mt-0.5" />
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {!funding?.total && fundingPosts.length === 0 && (
        <p className="text-sm text-gray-400">No funding data yet. Refresh intel to fetch.</p>
      )}
    </div>
  )
}

function HiringSection({ intel, jobPosts }) {
  const hiring = intel?.hiring
  const [expanded, setExpanded] = useState(false)
  const signals = hiring?.hiring_signals || []
  const roles = hiring?.open_roles || []
  const displayRoles = expanded ? roles : roles.slice(0, 6)

  return (
    <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
      <SectionHeader
        title="Hiring Intelligence"
        icon={Briefcase}
        color="#6C63FF"
        count={hiring?.total_open_roles > 0 ? `${hiring.total_open_roles} open roles` : undefined}
      />

      {signals.length > 0 && (
        <div className="mb-4">
          <p className="text-xs font-semibold text-gray-500 mb-2">STRATEGIC SIGNALS</p>
          <div className="space-y-2">
            {signals.slice(0, 5).map((sig, i) => (
              <div key={i} className="bg-purple-50 border border-purple-100 rounded-xl px-3 py-2">
                <p className="text-xs text-purple-800">{sig}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {(roles.length > 0 || jobPosts.length > 0) && (
        <div>
          <p className="text-xs font-semibold text-gray-500 mb-2">OPEN ROLES</p>
          <div className="space-y-2">
            {displayRoles.map((role, i) => {
              const title = typeof role === 'string' ? role : (role.title || '').replace('🧑‍💼 Hiring: ', '')
              const platform = typeof role === 'object' ? role.platform : ''
              const url = typeof role === 'object' ? role.url : ''
              const signal = typeof role === 'object' ? role.signal : ''
              const signalText = signal ? signal.split('. ').slice(1).join('. ') : ''
              return (
                <div key={i} className="flex items-start gap-3 py-2 border-b border-gray-50 last:border-0">
                  <span className="text-base flex-shrink-0">🧑‍💼</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-700 line-clamp-1">{title}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      {platform && <span className="text-xs text-gray-400">{platform}</span>}
                      {signalText && <span className="text-xs text-purple-500 line-clamp-1">{signalText}</span>}
                    </div>
                  </div>
                  {url && (
                    <a href={url} target="_blank" rel="noreferrer">
                      <ExternalLink size={13} className="text-gray-300 hover:text-gray-600 flex-shrink-0 mt-0.5" />
                    </a>
                  )}
                </div>
              )
            })}
          </div>
          {roles.length > 6 && (
            <button
              onClick={() => setExpanded(p => !p)}
              className="mt-3 flex items-center gap-1 text-xs text-[#2EC4B6] hover:underline font-medium"
            >
              {expanded ? <><ChevronUp size={13} /> Show less</> : <><ChevronDown size={13} /> Show {roles.length - 6} more roles</>}
            </button>
          )}
        </div>
      )}

      {signals.length === 0 && roles.length === 0 && jobPosts.length === 0 && (
        <p className="text-sm text-gray-400">No hiring data yet. Refresh intel to fetch.</p>
      )}
    </div>
  )
}

function TechStackSection({ intel }) {
  const ts = intel?.tech_stack
  const categories = ts?.categories || {}
  const technologies = ts?.technologies || []

  const CATEGORY_COLORS = {
    'Analytics': '#4F46E5',
    'CRM/Marketing': '#0891B2',
    'Support/Chat': '#059669',
    'Email': '#D97706',
    'Payments': '#DC2626',
    'Frontend': '#7C3AED',
    'Cloud': '#2563EB',
    'BaaS': '#EA580C',
    'Advertising': '#DB2777',
    'AI': '#6D28D9',
    'Mobile Marketing': '#0D9488',
    'Notifications': '#B45309',
    'Infrastructure': '#475569',
    'CDN/Security': '#1D4ED8',
    'Mobile': '#15803D',
    'SEO': '#92400E',
    'Backend': '#1E293B',
  }

  if (technologies.length === 0) return (
    <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
      <SectionHeader title="Tech Stack" icon={Code2} color="#6D28D9" />
      <p className="text-sm text-gray-400">No tech stack data yet. Refresh intel to fetch.</p>
    </div>
  )

  return (
    <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
      <SectionHeader title="Tech Stack" icon={Code2} color="#6D28D9" count={`${technologies.length} detected`} />

      {/* Signals first */}
      {technologies.filter(t => t.signal && !t.signal.includes('Basic') && !t.signal.includes('web server') && !t.signal.includes('protection')).length > 0 && (
        <div className="mb-4">
          <p className="text-xs font-semibold text-gray-500 mb-2">STRATEGIC SIGNALS</p>
          <div className="space-y-1.5">
            {technologies
              .filter(t => t.signal && !t.signal.startsWith('🔧') && !t.signal.startsWith('🖥') && !t.signal.startsWith('🛡') && !t.signal.startsWith('⚛️') && !t.signal.startsWith('☁️') && !t.signal.startsWith('🔥') && !t.signal.startsWith('🌐'))
              .slice(0, 6)
              .map((t, i) => (
                <div key={i} className="flex items-center gap-2 bg-indigo-50 border border-indigo-100 rounded-lg px-3 py-1.5">
                  <span className="text-xs text-indigo-700">{t.signal}</span>
                  <span className="ml-auto text-xs text-indigo-400 bg-indigo-100 px-1.5 py-0.5 rounded-full">{t.name}</span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Tech by category */}
      <div className="space-y-3">
        {Object.entries(categories).map(([cat, techs]) => {
          const color = CATEGORY_COLORS[cat] || '#64748B'
          return (
            <div key={cat}>
              <p className="text-xs font-semibold text-gray-500 mb-1.5">{cat.toUpperCase()}</p>
              <div className="flex flex-wrap gap-2">
                {techs.map(t => (
                  <span key={t} className="text-xs px-2.5 py-1 rounded-full font-medium"
                    style={{ background: `${color}15`, color, border: `1px solid ${color}30` }}>
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default function IntelProfile() {
  const { competitorId } = useParams()
  const navigate = useNavigate()
  const [competitors, setCompetitors] = useState([])
  const [intel, setIntel] = useState(null)
  const [jobs, setJobs] = useState([])
  const [fundingNews, setFundingNews] = useState([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [selectedId, setSelectedId] = useState(competitorId ? parseInt(competitorId) : null)

  const load = async (id) => {
    setLoading(true)
    try {
      const [intelRes, jobsRes, fundingRes, compsRes] = await Promise.all([
        getCompetitorIntel(id).catch(() => ({ data: null })),
        getCompetitorJobs(id).catch(() => ({ data: [] })),
        getCompetitorFundingNews(id).catch(() => ({ data: [] })),
        getCompetitors().catch(() => ({ data: [] })),
      ])
      setIntel(intelRes.data)
      setJobs(jobsRes.data || [])
      setFundingNews(fundingRes.data || [])
      setCompetitors(compsRes.data || [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (selectedId) {
      load(selectedId)
      navigate(`/intel/${selectedId}`, { replace: true })
    } else {
      // Load competitors list
      getCompetitors().then(r => {
        setCompetitors(r.data || [])
        setLoading(false)
      }).catch(() => setLoading(false))
    }
  }, [selectedId])

  const handleRefresh = async () => {
    if (!selectedId) return
    setRefreshing(true)
    try {
      await refreshCompetitorIntel(selectedId)
      setTimeout(() => load(selectedId), 2000) // wait 2s then reload
    } catch (e) {
      console.error('Refresh failed', e)
    } finally {
      setTimeout(() => setRefreshing(false), 2000)
    }
  }

  const currentComp = competitors.find(c => c.id === selectedId)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#1a1a2e]">Deep Intel</h1>
          <p className="text-gray-500 text-sm mt-1">App ratings, funding, hiring signals & tech stack</p>
        </div>
        {selectedId && (
          <div className="flex items-center gap-2">
            <button onClick={() => { setSelectedId(null); setIntel(null) }}
              className="flex items-center gap-1.5 px-3 py-2 bg-white border border-gray-200 rounded-xl text-sm hover:bg-gray-50 transition">
              <ArrowLeft size={14} /> All Competitors
            </button>
            <button onClick={handleRefresh} disabled={refreshing}
              className="flex items-center gap-1.5 px-3 py-2 bg-[#1a1a2e] text-white rounded-xl text-sm hover:bg-[#2a2a4e] transition disabled:opacity-60">
              <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
              {refreshing ? 'Refreshing...' : 'Refresh Intel'}
            </button>
          </div>
        )}
      </div>

      {/* Competitor selector */}
      {!selectedId && (
        <div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {competitors.map(comp => (
              <button key={comp.id} onClick={() => setSelectedId(comp.id)}
                className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm text-left hover:shadow-md hover:border-[#2EC4B6]/40 transition group">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-8 h-8 rounded-xl bg-[#2EC4B6]/10 flex items-center justify-center">
                    <span className="text-sm font-bold text-[#2EC4B6]">{comp.name[0]}</span>
                  </div>
                  <div>
                    <p className="font-semibold text-sm text-gray-800 group-hover:text-[#2EC4B6]">{comp.name}</p>
                    <p className="text-xs text-gray-400">{comp.category}</p>
                  </div>
                </div>
                <p className="text-xs text-gray-400 line-clamp-1">{comp.website || 'No website'}</p>
              </button>
            ))}
          </div>
          {loading && (
            <div className="flex justify-center py-12">
              <div className="w-8 h-8 border-4 border-[#2EC4B6] border-t-transparent rounded-full animate-spin" />
            </div>
          )}
        </div>
      )}

      {/* Profile View */}
      {selectedId && (
        <>
          {/* Competitor header */}
          <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-[#2EC4B6]/10 flex items-center justify-center">
                <span className="text-xl font-bold text-[#2EC4B6]">{currentComp?.name?.[0] || '?'}</span>
              </div>
              <div className="flex-1">
                <h2 className="font-bold text-xl text-gray-800">{currentComp?.name}</h2>
                <div className="flex items-center gap-3 mt-1">
                  {currentComp?.category && (
                    <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">{currentComp.category}</span>
                  )}
                  {currentComp?.website && (
                    <a href={currentComp.website} target="_blank" rel="noreferrer"
                      className="text-xs text-[#2EC4B6] hover:underline flex items-center gap-1">
                      {currentComp.website} <ExternalLink size={10} />
                    </a>
                  )}
                </div>
              </div>
              {intel?.last_refreshed_at && (
                <div className="text-right">
                  <p className="text-xs text-gray-400">Last updated</p>
                  <p className="text-xs text-gray-500 font-medium">{formatDistanceToNow(new Date(intel.last_refreshed_at), { addSuffix: true })}</p>
                </div>
              )}
            </div>
          </div>

          {loading ? (
            <div className="flex justify-center py-16">
              <div className="w-8 h-8 border-4 border-[#2EC4B6] border-t-transparent rounded-full animate-spin" />
            </div>
          ) : intel?.empty ? (
            <div className="text-center py-16 bg-white rounded-2xl border border-gray-100">
              <p className="text-4xl mb-3">🔬</p>
              <p className="font-semibold text-gray-700 mb-1">No deep intel yet</p>
              <p className="text-sm text-gray-400 mb-5">{intel.message}</p>
              <button onClick={handleRefresh} disabled={refreshing}
                className="flex items-center gap-2 px-5 py-2.5 bg-[#2EC4B6] text-white rounded-xl text-sm font-medium hover:bg-[#0b6e6e] transition mx-auto disabled:opacity-60">
                <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
                Fetch Deep Intel Now
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Quick stats bar */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <StatCard
                  label="Google Play Rating"
                  value={intel?.app_store?.google_play?.rating ? `${intel.app_store.google_play.rating?.toFixed(1)} / 5` : '—'}
                  sub={intel?.app_store?.google_play?.reviews_count ? `${intel.app_store.google_play.reviews_count?.toLocaleString()} reviews` : undefined}
                  icon={Smartphone}
                  color="#34A853"
                />
                <StatCard
                  label="Total Funding"
                  value={intel?.funding?.total || '—'}
                  sub={intel?.funding?.last_round ? `${intel.funding.last_round} ${intel.funding.last_round_year || ''}` : undefined}
                  icon={DollarSign}
                  color="#F7B731"
                />
                <StatCard
                  label="Open Roles"
                  value={intel?.hiring?.total_open_roles || 0}
                  sub="hiring signals detected"
                  icon={Users}
                  color="#6C63FF"
                />
                <StatCard
                  label="Tech Detected"
                  value={intel?.tech_stack?.total_detected || 0}
                  sub="technologies identified"
                  icon={Code2}
                  color="#6D28D9"
                />
              </div>

              {/* Main sections */}
              <AppStoreSection intel={intel} />
              <FundingSection intel={intel} fundingPosts={fundingNews} />
              <HiringSection intel={intel} jobPosts={jobs} />
              <TechStackSection intel={intel} />
            </div>
          )}
        </>
      )}
    </div>
  )
}
