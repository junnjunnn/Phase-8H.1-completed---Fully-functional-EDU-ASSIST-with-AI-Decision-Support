import { useCallback, useEffect, useRef, useState } from 'react'

export function useAsyncDataLoader(loader, deps = [], initialValue = null) {
  const [data, setData] = useState(initialValue)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const activeRef = useRef(true)

  useEffect(() => () => {
    activeRef.current = false
  }, [])

  const reload = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const payload = await loader()
      if (activeRef.current) {
        setData(payload)
      }
      return payload
    } catch (err) {
      if (activeRef.current) {
        setError(err?.message || String(err))
      }
      throw err
    } finally {
      if (activeRef.current) {
        setLoading(false)
      }
    }
  }, [loader])

  useEffect(() => {
    reload()
  }, [reload, ...deps])

  return { data, setData, loading, error, setError, reload }
}
