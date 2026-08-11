import { useEffect, useRef } from 'react'

export function useRoleAwareAutoLoad({
  enabled = true,
  loading,
  filters,
  setFilters,
  queryFilters = {},
  getDefaultFilters,
  onLoad,
  dependencies = [],
}) {
  const lastAppliedRef = useRef(null)

  useEffect(() => {
    if (!enabled || loading) {
      return
    }

    const hasQueryValues = Object.values(queryFilters).some((value) => value !== '' && value !== null && value !== undefined)
    const hasFilterValues = Object.values(filters).some((value) => value !== '' && value !== null && value !== undefined)
    const nextFilters = hasQueryValues ? { ...filters, ...queryFilters } : hasFilterValues ? null : getDefaultFilters?.()

    if (!nextFilters) {
      return
    }

    const serialized = JSON.stringify(nextFilters)
    if (lastAppliedRef.current === serialized) {
      return
    }

    lastAppliedRef.current = serialized
    setFilters(nextFilters)
    onLoad?.(nextFilters)
  }, [enabled, loading, filters, JSON.stringify(queryFilters), getDefaultFilters, onLoad, ...dependencies])
}
