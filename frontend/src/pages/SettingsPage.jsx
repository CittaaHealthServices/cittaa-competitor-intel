import React, { useState } from 'react'
import { Mail, Key, Clock, Bell, Save } from 'lucide-react'

function SettingSection({ title, icon: Icon, children }) {
  return (
    <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-gray-100">
        <Icon size={18} className="text-[#2EC4B6]" />
        <h3 className="font-semibold text-gray-700">{title}</h3>
      </div>
      {children}
    </div>
  )
}

export default function SettingsPage() {
  const [saved, setSaved] = useState(false)

  const showSaved = () => { setSaved(true); setTimeout(() => setSaved(false), 2000) }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-[#1a1a2e]">Settings</h1>
        <p className="text-gray-500 text-sm mt-1">Configure your Cittaa Intel monitoring preferences</p>
      </div>

      <SettingSection title="API Keys" icon={Key}>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Google Gemini API Key</label>
            <input type="password" placeholder="AIza..." defaultValue="•••••••••••••••"
              className="w-full border rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-[#2EC4B6]" />
            <p className="text-xs text-gray-400 mt-1">Used for AI analysis of all competitor posts</p>
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Twitter/X Bearer Token (optional)</label>
            <input type="password" placeholder="AAAA..." className="w-full border rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-[#2EC4B6]" />
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">YouTube Data API Key (optional)</label>
            <input type="password" placeholder="AIza..." className="w-full border rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-[#2EC4B6]" />
          </div>
        </div>
      </SettingSection>

      <SettingSection title="Email Digest" icon={Mail}>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">SMTP Host</label>
            <input defaultValue="smtp.gmail.com" className="w-full border rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-[#2EC4B6]" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">SMTP User</label>
              <input defaultValue="sairam@cittaa.in" className="w-full border rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-[#2EC4B6]" />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">SMTP Password</label>
              <input type="password" placeholder="App password" className="w-full border rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-[#2EC4B6]" />
            </div>
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Digest Recipients (comma-separated)</label>
            <input defaultValue="sairam@cittaa.in" className="w-full border rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-[#2EC4B6]" />
          </div>
        </div>
      </SettingSection>

      <SettingSection title="Scraping Schedule" icon={Clock}>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Scraping Frequency</label>
            <select className="w-full border rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-[#2EC4B6]">
              <option>Every 6 hours (Recommended)</option>
              <option>Every 3 hours</option>
              <option>Every 12 hours</option>
              <option>Daily</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Daily Digest Time</label>
            <input type="time" defaultValue="08:30" className="w-full border rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-[#2EC4B6]" />
            <p className="text-xs text-gray-400 mt-1">IST (Indian Standard Time)</p>
          </div>
        </div>
      </SettingSection>

      <SettingSection title="Alert Thresholds" icon={Bell}>
        <div className="space-y-4">
          <div>
            <label className="text-xs text-gray-500 mb-2 block">Minimum importance score for email alerts</label>
            <input type="range" min="1" max="10" defaultValue="7" className="w-full accent-[#2EC4B6]" />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>1 (All)</span><span>7 (High)</span><span>10 (Critical only)</span>
            </div>
          </div>
          <div className="space-y-2">
            {['Funding announcements', 'New product launches', 'Partnership news', 'Viral posts (10k+ reach)'].map(item => (
              <label key={item} className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" defaultChecked className="accent-[#2EC4B6]" />
                <span className="text-sm text-gray-700">{item}</span>
              </label>
            ))}
          </div>
        </div>
      </SettingSection>

      <button onClick={showSaved}
        className="flex items-center gap-2 px-6 py-2.5 bg-[#2EC4B6] text-white rounded-xl font-semibold hover:bg-[#0b6e6e] transition">
        <Save size={16} />
        {saved ? '✅ Saved!' : 'Save Settings'}
      </button>

      <div className="bg-[#1a1a2e] rounded-2xl p-5 text-white">
        <h3 className="font-bold mb-2 cittaa-brand text-[#2EC4B6] text-lg">Deployment Info</h3>
        <div className="space-y-1 text-sm text-white/70">
          <p>Backend: FastAPI on Railway · PostgreSQL managed DB</p>
          <p>Frontend: React + Vite served from backend</p>
          <p>AI Engine: Google Gemini 1.5 Flash</p>
          <p>Scraping: Every 6 hours · Digest: Daily at 8:30 AM IST</p>
        </div>
      </div>
    </div>
  )
}
