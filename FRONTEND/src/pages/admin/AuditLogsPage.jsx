import { useEffect, useMemo, useState } from 'react'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import { getApiErrorMessage } from '../../services/api'
import { getAuditLogs } from '../../services/auditService'

export function AuditLogsPage() {
  const [logs, setLogs] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    const timer = setTimeout(async () => {
      setLoading(true)
      setError('')
      try {
        const data = await getAuditLogs({ search, ordering: '-timestamp', page_size: 100 })
        if (!active) return
        setLogs(Array.isArray(data) ? data : data.results || [])
      } catch (err) {
        if (!active) return
        setError(getApiErrorMessage(err))
      } finally {
        if (active) setLoading(false)
      }
    }, 300)

    return () => {
      active = false
      clearTimeout(timer)
    }
  }, [search])

  const lastUpdated = useMemo(() => {
    if (!logs.length) return 'No recent log entries.'
    return `Showing ${logs.length} entries from the most recent activity.`
  }, [logs.length])

  return (
    <div className="page-stack audit-page">
      <PageHeader
        eyebrow="Administration"
        title="Audit logs"
        description="Review recent system activity, user actions, and reporting events across EDU ASSIST."
        actions={null}
      />

      <div className="panel-card">
        <div className="panel-header">
          <div className="search-input-group">
            <span className="search-icon" aria-hidden="true">🔎</span>
            <input
              aria-label="Search audit logs"
              placeholder="Search by action, module, user, or object"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
          <p className="section-description">{lastUpdated}</p>
        </div>

        {error ? <ErrorBanner message={error} /> : null}

        {loading ? (
          <div className="table-skeleton-grid">
            {Array.from({ length: 6 }).map((_, index) => (
              <div key={index} className="table-skeleton-card" />
            ))}
          </div>
        ) : null}

        {!loading && !error && logs.length === 0 ? (
          <EmptyState title="No audit records" message="There are no audit logs that match the current filter." />
        ) : null}

        {!loading && logs.length > 0 ? (
          <div className="table-card">
            <table className="records-table">
              <thead>
                <tr>
                  <th scope="col">Timestamp</th>
                  <th scope="col">User</th>
                  <th scope="col">Action</th>
                  <th scope="col">Module</th>
                  <th scope="col">Object</th>
                  <th scope="col">IP address</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td>{new Date(log.timestamp).toLocaleString()}</td>
                    <td>{log.user_username || 'System'}</td>
                    <td>{log.action}</td>
                    <td>{log.module}</td>
                    <td>{log.object_type ? `${log.object_type}${log.object_id ? ` (${log.object_id})` : ''}` : log.object_id || '—'}</td>
                    <td>{log.ip_address || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>
    </div>
  )
}
