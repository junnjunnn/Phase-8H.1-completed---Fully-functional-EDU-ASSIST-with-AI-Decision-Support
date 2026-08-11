import React from 'react'

export function FilterBar({ title, children }) {
  return (
    <section className="panel-card report-filter-bar">
      <div className="section-header">
        <div>
          <p className="eyebrow">Filters</p>
          <h2>{title}</h2>
        </div>
      </div>
      <div className="filter-bar-content">{children}</div>
    </section>
  )
}

export function KpiCard({ label, value, tone = 'primary' }) {
  return (
    <article className={`kpi-card kpi-card--${tone}`}>
      <p className="kpi-label">{label}</p>
      <p className="kpi-value">{value}</p>
    </article>
  )
}

export function SearchBar({ value, onChange, placeholder, ariaLabel }) {
  return (
    <label className="search-bar">
      <input
        type="search"
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        aria-label={ariaLabel}
      />
    </label>
  )
}

export function SectionHeader({ eyebrow, title }) {
  return (
    <div className="section-header report-section-header">
      <p className="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
    </div>
  )
}
