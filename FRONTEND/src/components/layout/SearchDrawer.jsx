import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { searchPredictions, searchStudents, searchUsers } from '../../services/searchService'

export function SearchDrawer({ open, onClose }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState({ students: [], predictions: [], users: [] })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    const searchTerm = query.trim()

    async function fetchResults() {
      if (!open || !searchTerm) {
        setResults({ students: [], predictions: [], users: [] })
        setError('')
        setLoading(false)
        return
      }

      setLoading(true)
      setError('')

      try {
        const [students, predictions, users] = await Promise.all([
          searchStudents(searchTerm),
          searchPredictions(searchTerm),
          searchUsers(searchTerm),
        ])

        if (!active) return
        setResults({ students, predictions, users })
      } catch {
        if (!active) return
        setError('Unable to complete the search right now.')
      } finally {
        if (active) setLoading(false)
      }
    }

    const timer = setTimeout(() => {
      if (open) {
        fetchResults()
      }
    }, 250)

    return () => {
      active = false
      clearTimeout(timer)
    }
  }, [open, query])

  const studentCount = results.students.length
  const predictionCount = results.predictions.length
  const userCount = results.users.length
  const totalCount = studentCount + predictionCount + userCount

  return (
    <div className={`search-drawer ${open ? 'search-drawer--open' : ''}`} role="dialog" aria-modal="true" aria-label="Global search panel">
      <div className="drawer-panel search-panel">
        <div className="drawer-header">
          <div>
            <p className="eyebrow">Global search</p>
            <h2>Find students, predictions, and accounts</h2>
          </div>
          <button type="button" className="icon-button" onClick={onClose} aria-label="Close search">
            <XMarkIcon className="icon" />
          </button>
        </div>

        <div className="search-field-row">
          <MagnifyingGlassIcon className="icon icon--small" aria-hidden="true" />
          <input
            className="search-input"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search students, predictions, or users"
            aria-label="Search the system"
            autoFocus
          />
        </div>

        <div className="drawer-section">
          {loading ? (
            <div className="search-suggestions">
              <p>Searching for “{query}” …</p>
            </div>
          ) : error ? (
            <p className="error-text">{error}</p>
          ) : !query.trim() ? (
            <div className="search-suggestions">
              <p>Type a name, student ID, risk level, or username to locate records quickly.</p>
              <ul>
                <li>Search student names and IDs</li>
                <li>Search prediction risk levels</li>
                <li>Search staff usernames and emails</li>
              </ul>
            </div>
          ) : totalCount === 0 ? (
            <div className="search-suggestions">
              <p>No results were found for “{query}”.</p>
            </div>
          ) : (
            <div className="search-results">
              <div className="search-summary">
                <p>{totalCount} result{totalCount === 1 ? '' : 's'} found across {studentCount} student{studentCount === 1 ? '' : 's'}, {predictionCount} prediction{predictionCount === 1 ? '' : 's'}, and {userCount} account{userCount === 1 ? '' : 's'}.</p>
              </div>
              {studentCount > 0 ? (
                <section>
                  <p className="section-label">Students</p>
                  <ul className="search-list">
                    {results.students.slice(0, 5).map((student) => (
                      <li key={student.id}>
                        <Link to={`/students/${student.id}`} className="search-item" onClick={onClose}>
                          <span>{`${student.first_name || ''} ${student.last_name || ''}`.trim() || student.username}</span>
                          <small>{student.lrn ? `LRN ${student.lrn}` : student.email || 'No ID'}</small>
                        </Link>
                      </li>
                    ))}
                  </ul>
                </section>
              ) : null}

              {predictionCount > 0 ? (
                <section>
                  <p className="section-label">Predictions</p>
                  <ul className="search-list">
                    {results.predictions.slice(0, 5).map((prediction) => (
                      <li key={prediction.id}>
                        <Link to="/predictions" className="search-item" onClick={onClose}>
                          <span>{`${prediction.enrollment__student__first_name || ''} ${prediction.enrollment__student__last_name || ''}`.trim() || 'Prediction'}</span>
                          <small>{prediction.risk_level ? `${prediction.risk_level} risk` : 'Prediction record'}</small>
                        </Link>
                      </li>
                    ))}
                  </ul>
                </section>
              ) : null}

              {userCount > 0 ? (
                <section>
                  <p className="section-label">Accounts</p>
                  <ul className="search-list">
                    {results.users.slice(0, 5).map((account) => (
                      <li key={account.id}>
                        <Link to="/users" className="search-item" onClick={onClose}>
                          <span>{`${account.first_name || ''} ${account.last_name || ''}`.trim() || account.username}</span>
                          <small>{account.email || account.username}</small>
                        </Link>
                      </li>
                    ))}
                  </ul>
                </section>
              ) : null}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
