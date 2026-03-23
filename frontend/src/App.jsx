import React, { useState } from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Globe2, Zap, Settings, Bell,
  Menu, X, RefreshCw, Mail, ChevronRight, Search, BookOpen
} from 'lucide-react'
import Dashboard from './pages/Dashboard'
import Competitors from './pages/Competitors'
import Feed from './pages/Feed'
import InsightsPage from './pages/Insights'
import SettingsPage from './pages/SettingsPage'
import IntelProfile from './pages/IntelProfile'
import ContentPlaybook from './pages/ContentPlaybook'
import { triggerScrapeAll, sendDigestNow } from './services/api'

const PLATFORM_META = {
  linkedin:      { label: 'LinkedIn',   color: '#0077B5', emoji: '💼' },
  twitter:       { label: 'Twitter/X',  color: '#1DA1F2', emoji: '𝕏' },
  instagram:     { label: 'Instagram',  color: '#E1306C', emoji: '📸' },
  youtube:       { label: 'YouTube',    color: '#FF0000', emoji: '▶' },
  news:          { label: 'News',       color: '#FF6B35', emoji: '📰' },
  blog:          { label: 'Blog',       color: '#6C63FF', emoji: '✍' },
  press_release: { label: 'Press',      color: '#F7B731', emoji: '📣' },
  search:        { label: 'Web Search', color: '#34A853', emoji: '🔍' },
  appstore:      { label: 'App Store',  color: '#007AFF', emoji: '📱' },
  jobs:          { label: 'Jobs',       color: '#6C63FF', emoji: '🧑‍💼' },
  funding:       { label: 'Funding',    color: '#F7B731', emoji: '💰' },
  techstack:     { label: 'Tech Stack', color: '#6D28D9', emoji: '🔬' },
  employee:      { label: 'Employee',   color: '#FF6B8A', emoji: '👥' },
  strategy:      { label: 'Strategy',  color: '#6D28D9', emoji: '🎯' },
}

export { PLATFORM_META }

function Sidebar({ isOpen, setIsOpen }) {
  const navItems = [
    { to: '/',            icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/competitors', icon: Globe2,           label: 'Competitors' },
    { to: '/feed',        icon: Zap,              label: 'Live Feed' },
    { to: '/intel',       icon: Search,           label: 'Deep Intel' },
    { to: '/content',     icon: BookOpen,         label: 'Content Lab' },
    { to: '/insights',    icon: Bell,             label: 'Insights' },
    { to: '/settings',    icon: Settings,         label: 'Settings' },
  ]

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/50 z-20 lg:hidden" onClick={() => setIsOpen(false)} />
      )}

      <aside className={`
        fixed top-0 left-0 h-full z-30 flex flex-col
        bg-[#1a1a2e] text-white transition-all duration-300
        ${isOpen ? 'w-64' : 'w-16'}
        lg:w-64 lg:relative lg:translate-x-0
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-5 border-b border-white/10">
          <div className="w-8 h-8 rounded-lg bg-[#2EC4B6] flex items-center justify-center flex-shrink-0">
            <span className="text-white font-bold text-sm">C</span>
          </div>
          <div className={`${isOpen ? 'block' : 'hidden'} lg:block`}>
            <span className="cittaa-brand text-xl text-[#2EC4B6]">Cittaa</span>
            <span className="text-white/60 text-xs block -mt-0.5">Competitor Intel</span>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-2 py-4 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group
                 ${isActive
                   ? 'bg-[#2EC4B6] text-white font-semibold'
                   : 'text-white/60 hover:bg-white/10 hover:text-white'}`
              }
            >
              <Icon size={18} className="flex-shrink-0" />
              <span className={`${isOpen ? 'block' : 'hidden'} lg:block text-sm`}>{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Bottom branding */}
        <div className={`px-4 py-4 border-t border-white/10 ${isOpen ? 'block' : 'hidden'} lg:block`}>
          <p className="text-white/30 text-xs">Powered by Google Gemini AI</p>
          <p className="text-[#2EC4B6] text-xs">sairam@cittaa.in</p>
        </div>
      </aside>
    </>
  )
}

function Header({ setIsOpen }) {
  const [scraping, setScraping] = useState(false)
  const [emailing, setEmailing] = useState(false)
  const [toast, setToast] = useState('')

  const showToast = (msg) => {
    setToast(msg)
    setTimeout(() => setToast(''), 3000)
  }

  const handleScrape = async () => {
    setScraping(true)
    try {
      await triggerScrapeAll()
      showToast('🔍 Scraping started for all competitors...')
    } catch (e) {
      showToast('⚠️ Could not start scraping')
    } finally {
      setScraping(false)
    }
  }

  const handleDigest = async () => {
    setEmailing(true)
    try {
      await sendDigestNow()
      showToast('📧 Daily digest email queued!')
    } catch (e) {
      showToast('⚠️ Could not send digest')
    } finally {
      setEmailing(false)
    }
  }

  return (
    <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between sticky top-0 z-10">
      <div className="flex items-center gap-3">
        <button onClick={() => setIsOpen(p => !p)} className="lg:hidden p-1.5 rounded-lg hover:bg-gray-100">
          <Menu size={20} />
        </button>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 bg-[#2EC4B6] rounded-full pulse-live"></span>
          <span className="text-sm text-gray-500">Live Monitoring Active</span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={handleScrape}
          disabled={scraping}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-[#1a1a2e] text-white rounded-lg text-sm font-medium hover:bg-[#2a2a4e] transition disabled:opacity-60"
        >
          <RefreshCw size={14} className={scraping ? 'animate-spin' : ''} />
          <span className="hidden sm:inline">Scrape Now</span>
        </button>
        <button
          onClick={handleDigest}
          disabled={emailing}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-[#2EC4B6] text-white rounded-lg text-sm font-medium hover:bg-[#0b6e6e] transition disabled:opacity-60"
        >
          <Mail size={14} />
          <span className="hidden sm:inline">Send Digest</span>
        </button>
      </div>

      {/* Toast */}
      {toast && (
        <div className="fixed bottom-6 right-6 bg-[#1a1a2e] text-white px-4 py-3 rounded-xl shadow-xl z-50 fade-in text-sm">
          {toast}
        </div>
      )}
    </header>
  )
}

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <BrowserRouter>
      <div className="flex h-screen bg-[#f0f4f8] overflow-hidden">
        <Sidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          <Header setIsOpen={setSidebarOpen} />
          <main className="flex-1 overflow-y-auto p-4 lg:p-6">
            <Routes>
              <Route path="/"                element={<Dashboard />} />
              <Route path="/competitors"     element={<Competitors />} />
              <Route path="/feed"            element={<Feed />} />
              <Route path="/intel"           element={<IntelProfile />} />
              <Route path="/intel/:competitorId" element={<IntelProfile />} />
              <Route path="/content"        element={<ContentPlaybook />} />
              <Route path="/insights"        element={<InsightsPage />} />
              <Route path="/settings"        element={<SettingsPage />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  )
}
