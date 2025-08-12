import axios from "axios"

const BASE = (process.env.REACT_APP_BACKEND_URL || import.meta?.env?.REACT_APP_BACKEND_URL || "")
const API = `${BASE}/api`

const get = (url, params) => axios.get(`${API}${url}`, { params }).then(r => r.data)
const post = (url, body) => axios.post(`${API}${url}`, body).then(r => r.data)
const put = (url, body) => axios.put(`${API}${url}`, body).then(r => r.data)
const del = (url) => axios.delete(`${API}${url}`).then(r => r.data)

// Marketdata
export const searchSymbols = (q, limit = 25) => get('/marketdata/symbols/search', { q, limit })
export const getBars = (symbol, interval = '1D', fr, to) => get('/marketdata/bars', { symbol, interval, fr, to })
export const getQuotes = (symbolsCsv) => get('/marketdata/quotes', { symbols: symbolsCsv })
export const getLogo = (symbol) => get('/marketdata/logo', { symbol })

// Watchlists
export const listWatchlists = () => get('/watchlists')
export const createWatchlist = (name, symbols=[]) => post('/watchlists', { name, symbols })
export const updateWatchlist = (id, patch) => put(`/watchlists/${id}`, patch)
export const deleteWatchlist = (id) => del(`/watchlists/${id}`)

// Columns
export const getColumnSchema = () => get('/columns/schema')
export const getColumnPresets = () => get('/columns/presets')
export const saveColumnPreset = (name, columns) => post('/columns/presets', { name, columns })
export const deleteColumnPreset = (name) => del(`/columns/presets/${name}`)

// Ratings
export const computeRatings = ({ symbols, rsWindowDays=63, asShortDays=21, asLongDays=63 }) => post('/ratings/compute', { symbols, rsWindowDays, asShortDays, asLongDays })

// Screener
export const getScreenerFilters = () => get('/screeners/filters')
export const runScreener = (payload) => post('/screeners/run', payload)

// Settings
export const getSettings = () => get('/settings')
export const saveSettings = (body) => post('/settings', body)

export const apiBase = API