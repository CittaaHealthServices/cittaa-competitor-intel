import React, { useState, useEffect } from 'react'
import { getCompetitors, addCompetitor, deleteCompetitor, scrapeCompetitor, seedCompetitors } from '../services/api'
import { Globe, Linkedin, Twitter, Instagram, Youtube, RefreshCw, Plus, Trash2, CheckCircle, Loader } from 'lucide-react'

function CompetitorCard({ comp, onScrape, onDelete }) {
  const [scraping, setScraping] = useState(false)

  const handleScrape = async () => {
    setScraping(true)
    try { await onScrape(comp.id) } finally { setScraping(false) }
  }

  const categoryColor = comp.category === 'International'
    ? 'bg-purple-100 text-purple-700'
    : comp.category === 'Self'
    ? 'bg-[#2EC4B6]/10 text-[#0b6e6e] border border-[#2EC4B6]/30'
    : 'bg-teal-100 text-teal-700'

  return (
    <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 fade-in hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-bold text-gray-800">{comp.name}</h3>
          <p className="text-gray-500 text-xs mt-0.5">{comp.description}</p>
        </div>
        <span className={`text-xs font-semibold px-2 py-1 rounded-full ${categoryColor}`}>{comp.category}</span>
      </div>

      {/* Social handles */}
      <div className="flex flex-wrap gap-2 mb-4">
        {comp.linkedin_slug && (
          <a href={`https://linkedin.com/company/${comp.linkedin_slug}`} target="_blank" rel="noreferrer"
            className="flex items-center gap-1 text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100">
            <Linkedin size={11} /> LinkedIn
          </a>
        )}
        {comp.twitter_handle && (
          <a href={`https://twitter.com/${comp.twitter_handle}`} target="_blank" rel="noreferrer"
            className="flex items-center gap-1 text-xs px-2 py-1 bg-sky-50 text-sky-700 rounded-lg hover:bg-sky-100">
            <Twitter size={11} /> @{comp.twitter_handle}
          </a>
        )}
        {comp.instagram_handle && (
          <a href={`https://instagram.com/${comp.instagram_handle}`} target="_blank" rel="noreferrer"
            className="flex items-center gap-1 text-xs px-2 py-1 bg-pink-50 text-pink-700 rounded-lg hover:bg-pink-100">
            <Instagram size={11} /> IG
          </a>
        )}
        {comp.website && (
          <a href={comp.website} target="_blank" rel="noreferrer"
            className="flex items-center gap-1 text-xs px-2 py-1 bg-gray-50 text-gray-600 rounded-lg hover:bg-gray-100">
            <Globe size={11} /> Website
          </a>
        )}
      </div>

      <div className="flex items-center justify-between">
        <div className="text-xs text-gray-400">
          <span className="font-semibold text-[#2EC4B6]">{comp.post_count || 0}</span> posts tracked
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleScrape}
            disabled={scraping}
            className="flex items-center gap-1 text-xs px-3 py-1.5 bg-[#1a1a2e] text-white rounded-lg hover:bg-[#2a2a4e] transition disabled:opacity-60"
          >
            {scraping ? <Loader size={11} className="animate-spin" /> : <RefreshCw size={11} />}
            Scrape
          </button>
          <button
            onClick={() => onDelete(comp.id)}
            className="flex items-center gap-1 text-xs px-3 py-1.5 bg-red-50 text-red-500 rounded-lg hover:bg-red-100 transition"
          >
            <Trash2 size={11} />
          </button>
        </div>
      </div>
    </div>
  )
}

function AddCompetitorModal({ onClose, onAdd }) {
  const [form, setForm] = useState({
    name: '', website: '', linkedin_slug: '', twitter_handle: '',
    instagram_handle: '', youtube_channel: '', category: 'National', description: ''
  })
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await onAdd({ ...form, news_keywords: [form.name] })
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-6 w-full max-w-lg shadow-2xl">
        <h2 className="font-bold text-lg mb-4">Add Competitor</h2>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2">
              <label className="text-xs text-gray-500 mb-1 block">Company Name *</label>
              <input required value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#2EC4B6]" placeholder="e.g. MindPeers" />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Website</label>
              <input value={form.website} onChange={e => setForm(p => ({ ...p, website: e.target.value }))}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#2EC4B6]" placeholder="https://..." />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">LinkedIn Slug</label>
              <input value={form.linkedin_slug} onChange={e => setForm(p => ({ ...p, linkedin_slug: e.target.value }))}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#2EC4B6]" placeholder="company-slug" />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Twitter Handle</label>
              <input value={form.twitter_handle} onChange={e => setForm(p => ({ ...p, twitter_handle: e.target.value }))}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#2EC4B6]" placeholder="@handle" />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Instagram Handle</label>
              <input value={form.instagram_handle} onChange={e => setForm(p => ({ ...p, instagram_handle: e.target.value }))}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#2EC4B6]" placeholder="@handle" />
            </div>
            <div className="col-span-2">
              <label className="text-xs text-gray-500 mb-1 block">Category</label>
              <select value={form.category} onChange={e => setForm(p => ({ ...p, category: e.target.value }))}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#2EC4B6]">
                <option>National</option>
                <option>International</option>
                <option>Self</option>
              </select>
            </div>
            <div className="col-span-2">
              <label className="text-xs text-gray-500 mb-1 block">Description</label>
              <input value={form.description} onChange={e => setForm(p => ({ ...p, description: e.target.value }))}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#2EC4B6]" placeholder="Short description" />
            </div>
          </div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="flex-1 py-2 border rounded-xl text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
            <button type="submit" disabled={loading}
              className="flex-1 py-2 bg-[#2EC4B6] text-white rounded-xl text-sm font-semibold hover:bg-[#0b6e6e] transition disabled:opacity-60">
              {loading ? 'Adding...' : 'Add Competitor'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function Competitors() {
  const [competitors, setCompetitors] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [seeding, setSeeding] = useState(false)
  const [toast, setToast] = useState('')
  const [filter, setFilter] = useState('All')

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 3000) }

  const load = async () => {
    const r = await getCompetitors()
    setCompetitors(r.data)
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const handleAdd = async (data) => {
    await addCompetitor(data)
    showToast('✅ Competitor added!')
    load()
  }

  const handleDelete = async (id) => {
    if (!confirm('Remove this competitor from monitoring?')) return
    await deleteCompetitor(id)
    showToast('Competitor removed')
    load()
  }

  const handleScrape = async (id) => {
    await scrapeCompetitor(id)
    showToast('🔍 Scraping started...')
  }

  const handleSeed = async () => {
    setSeeding(true)
    const r = await seedCompetitors()
    showToast(`✅ ${r.data.message}`)
    setSeeding(false)
    load()
  }

  const filtered = filter === 'All' ? competitors : competitors.filter(c => c.category === filter)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#1a1a2e]">Competitors</h1>
          <p className="text-gray-500 text-sm mt-1">{competitors.length} companies being tracked</p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleSeed} disabled={seeding}
            className="flex items-center gap-1.5 px-3 py-2 bg-gray-100 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-200 transition disabled:opacity-60">
            {seeding ? <Loader size={14} className="animate-spin" /> : <CheckCircle size={14} />}
            Load Defaults
          </button>
          <button onClick={() => setShowModal(true)}
            className="flex items-center gap-1.5 px-3 py-2 bg-[#2EC4B6] text-white rounded-xl text-sm font-semibold hover:bg-[#0b6e6e] transition">
            <Plus size={14} /> Add Competitor
          </button>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 flex-wrap">
        {[
          { label: 'All', emoji: '' },
          { label: 'Self', emoji: '🏠' },
          { label: 'National', emoji: '🇮🇳' },
          { label: 'International', emoji: '🌍' },
        ].map(({ label, emoji }) => (
          <button key={label} onClick={() => setFilter(label)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition ${filter === label ? 'bg-[#1a1a2e] text-white' : 'bg-white text-gray-500 hover:bg-gray-100'}`}>
            {emoji && <span className="mr-1">{emoji}</span>}{label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="w-8 h-8 border-4 border-[#2EC4B6] border-t-transparent rounded-full animate-spin" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl">
          <p className="text-gray-400 mb-4">No competitors added yet</p>
          <button onClick={handleSeed} className="px-4 py-2 bg-[#2EC4B6] text-white rounded-xl text-sm font-semibold hover:bg-[#0b6e6e]">
            Load Default Competitors
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map(c => (
            <CompetitorCard key={c.id} comp={c} onScrape={handleScrape} onDelete={handleDelete} />
          ))}
        </div>
      )}

      {showModal && <AddCompetitorModal onClose={() => setShowModal(false)} onAdd={handleAdd} />}

      {toast && (
        <div className="fixed bottom-6 right-6 bg-[#1a1a2e] text-white px-4 py-3 rounded-xl shadow-xl z-50 fade-in text-sm">{toast}</div>
      )}
    </div>
  )
}
