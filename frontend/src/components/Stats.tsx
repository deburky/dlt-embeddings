import { useEffect, useState } from 'react'
import { Stats as StatsType } from '../api'
import './Stats.css'

interface StatsProps {
  stats: StatsType | null
  onLoad: () => void
}

function Stats({ stats, onLoad }: StatsProps) {
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    if (expanded && !stats) {
      onLoad()
    }
  }, [expanded, stats, onLoad])

  return (
    <div className="stats-section">
      <button
        className="stats-toggle"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? '▼' : '▶'} Database Statistics
      </button>

      {expanded && stats && (
        <div className="stats-content">
          <div className="stat-item">
            <span className="stat-label">Total Messages:</span>
            <span className="stat-value">{stats.total_messages.toLocaleString()}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">With Embeddings:</span>
            <span className="stat-value">{stats.messages_with_embeddings.toLocaleString()}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Coverage:</span>
            <span className="stat-value">
              {stats.total_messages > 0
                ? ((stats.messages_with_embeddings / stats.total_messages) * 100).toFixed(1)
                : 0}%
            </span>
          </div>

          <div className="role-distribution">
            <h3>Role Distribution</h3>
            <div className="role-stats">
              {Object.entries(stats.role_distribution).map(([role, count]) => (
                <div key={role} className="role-stat-item">
                  <span className="role-stat-label">{role}:</span>
                  <span className="role-stat-value">{count.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Stats



