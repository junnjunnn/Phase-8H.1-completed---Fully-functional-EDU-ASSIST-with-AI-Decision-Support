import React, { useEffect, useState, useRef } from 'react'
import apiClient from '../services/api'

export default function AdviserSelect({ value, onChange, placeholder = 'Search adviser...', required = false, initialLabel = '' }) {
  const [query, setQuery] = useState('')
  const [options, setOptions] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [label, setLabel] = useState(initialLabel)
  const debounceRef = useRef(null)

  useEffect(() => {
    // If there's an initial selected id but no label, fetch it
    if (value && !initialLabel) {
      let mounted = true
      apiClient.get(`/auth/users/${value}/`).then((res) => {
        if (!mounted) return
        const u = res.data
        const full = `${u.first_name || ''} ${u.last_name || ''}`.trim() || u.username
        setLabel(full)
      }).catch(() => {
        if (!mounted) return
        setLabel('')
      })
      return () => { mounted = false }
    }
    setLabel(initialLabel || '')
  }, [value, initialLabel])

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (!query) {
      setOptions([])
      setLoading(false)
      setError('')
      return
    }
    setLoading(true)
    setError('')
    debounceRef.current = setTimeout(() => {
      apiClient.get('/auth/advisers/', { params: { q: query } }).then((res) => {
        setOptions(res.data || [])
      }).catch((e) => {
        setError('Could not load advisers')
      }).finally(() => setLoading(false))
    }, 300)
    return () => clearTimeout(debounceRef.current)
  }, [query])

  function handleSelect(opt) {
    setLabel(opt ? opt.full_name || `${opt.first_name || ''} ${opt.last_name || ''}`.trim() || opt.username : '')
    onChange(opt ? opt.id : null)
    setOptions([])
    setQuery('')
  }

  return (
    <div className="adviser-select">
      <input
        type="text"
        placeholder={placeholder}
        value={label || query}
        onChange={(e) => { setQuery(e.target.value); setLabel('') }}
        aria-label="Adviser search"
        required={required}
      />
      {loading ? <div className="small-muted">Searching…</div> : null}
      {error ? <div className="form-error">{error}</div> : null}
      {!loading && !error && options.length === 0 && query ? <div className="small-muted">No advisers</div> : null}
      {!loading && options.length > 0 ? (
        <ul className="adviser-options" style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {options.map((opt) => (
            <li key={opt.id}>
              <button type="button" className="link-button" onClick={() => handleSelect(opt)} style={{ padding: '0.25rem 0' }}>{opt.full_name || `${opt.first_name || ''} ${opt.last_name || ''}`.trim() || opt.username}</button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  )
}
