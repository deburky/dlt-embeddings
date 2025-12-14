import { useState, FormEvent } from 'react'
import './SearchBar.css'

interface SearchBarProps {
  onSearch: (query: string, filters?: {
    limit?: number
    threshold?: number
    role?: string
  }) => void
  loading: boolean
}

function SearchBar({ onSearch, loading }: SearchBarProps) {
  const [query, setQuery] = useState('')
  const [limit, setLimit] = useState(10)
  const [threshold, setThreshold] = useState(0.3)
  const [role, setRole] = useState('')

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      onSearch(query, {
        limit,
        threshold,
        role: role || undefined,
      })
    }
  }

  return (
    <form className="search-bar" onSubmit={handleSubmit}>
      <div className="search-input-group">
        <input
          type="text"
          className="search-input"
          placeholder="Search conversations... (e.g., 'How do I install Python?')"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={loading}
        />
        <button type="submit" className="search-button" disabled={loading || !query.trim()}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      <div className="search-filters">
        <div className="filter-group">
          <label htmlFor="limit">Limit:</label>
          <input
            id="limit"
            type="number"
            min="1"
            max="100"
            value={limit}
            onChange={(e) => setLimit(parseInt(e.target.value) || 10)}
            disabled={loading}
          />
        </div>

        <div className="filter-group">
          <label htmlFor="threshold">Threshold:</label>
          <input
            id="threshold"
            type="number"
            min="0"
            max="1"
            step="0.1"
            value={threshold}
            onChange={(e) => setThreshold(parseFloat(e.target.value) || 0)}
            disabled={loading}
          />
        </div>

        <div className="filter-group">
          <label htmlFor="role">Role:</label>
          <select
            id="role"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            disabled={loading}
          >
            <option value="">All</option>
            <option value="user">User</option>
            <option value="assistant">Assistant</option>
            <option value="tool">Tool</option>
          </select>
        </div>
      </div>
    </form>
  )
}

export default SearchBar

