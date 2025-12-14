import { useState } from 'react'
import SearchBar from './components/SearchBar'
import SearchResults from './components/SearchResults'
import Stats from './components/Stats'
import { searchConversations, getStats, Conversation, Stats as StatsType } from './api'
import './App.css'

function App() {
  const [results, setResults] = useState<Conversation[]>([])
  const [stats, setStats] = useState<StatsType | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')

  const handleSearch = async (searchQuery: string, filters?: {
    limit?: number
    threshold?: number
    role?: string
  }) => {
    if (!searchQuery.trim()) {
      setError('Please enter a search query')
      return
    }

    setLoading(true)
    setError(null)
    setQuery(searchQuery)

    try {
      const data = await searchConversations(searchQuery, filters)
      setResults(data.results)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed')
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const data = await getStats()
      setStats(data)
    } catch (err) {
      console.error('Failed to load stats:', err)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="header-icon">🔍</div>
          <div className="header-text">
            <h1>
              <span className="header-title-main">Vector Search</span>
              <span className="header-badge">AI-Powered</span>
            </h1>
            <p className="subtitle">Semantic search over conversation embeddings</p>
          </div>
        </div>
      </header>

      <main className="app-main">
        <SearchBar onSearch={handleSearch} loading={loading} />
        
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {query && (
          <div className="results-header">
            <h2>Results for: "{query}"</h2>
            {results.length > 0 && (
              <span className="results-count">{results.length} result(s)</span>
            )}
          </div>
        )}

        {loading ? (
          <div className="loading">Searching...</div>
        ) : (
          <SearchResults results={results} />
        )}

        <Stats stats={stats} onLoad={loadStats} />
      </main>
    </div>
  )
}

export default App

