import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: `${BASE_URL}/api`,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
})

// Dashboard
export const getDashboardStats = () => api.get('/dashboard/stats')

// Competitors
export const getCompetitors = () => api.get('/competitors/')
export const addCompetitor = (data) => api.post('/competitors/', data)
export const updateCompetitor = (id, data) => api.put(`/competitors/${id}`, data)
export const deleteCompetitor = (id) => api.delete(`/competitors/${id}`)
export const scrapeCompetitor = (id) => api.post(`/competitors/${id}/scrape`)
export const seedCompetitors = () => api.post('/competitors/seed')

// Posts
export const getPosts = (params = {}) => api.get('/posts/', { params })
export const getViralPosts = (days = 7) => api.get('/posts/viral', { params: { days } })
export const getTopPosts = (days = 7, limit = 10) => api.get('/posts/top', { params: { days, limit } })
export const getPlatformBreakdown = (days = 7) => api.get('/posts/platform-breakdown', { params: { days } })
export const getCompetitorActivity = (days = 7) => api.get('/posts/competitor-activity', { params: { days } })
export const getSentimentData = (days = 7) => api.get('/posts/sentiment-timeline', { params: { days } })
export const getSelfMonitorPosts = (days = 7) => api.get('/posts/self-monitor', { params: { days } })

// Insights
export const getInsights = (params = {}) => api.get('/insights/', { params })
export const markInsightRead = (id) => api.post(`/insights/${id}/read`)
export const generateWeeklyInsights = () => api.post('/insights/generate-weekly')

// Deep Intel
export const getAllIntel = () => api.get('/intel/')
export const getCompetitorIntel = (id) => api.get(`/intel/${id}`)
export const refreshCompetitorIntel = (id) => api.post(`/intel/${id}/refresh`)
export const refreshAllIntel = () => api.post('/intel/refresh-all')
export const getCompetitorJobs = (id) => api.get(`/intel/${id}/jobs`)
export const getCompetitorFundingNews = (id) => api.get(`/intel/${id}/funding-news`)
export const getAppStoreReviews = (id) => api.get(`/intel/${id}/appstore-reviews`)

// Content Playbook
export const getContentRecommendations = (forceRefresh = false) =>
  api.get('/content/recommendations', { params: { force_refresh: forceRefresh }, timeout: 60000 })

// Actions
export const triggerScrapeAll = () => api.post('/scrape/trigger-all')
export const sendDigestNow = () => api.post('/email/send-digest')

export default api
