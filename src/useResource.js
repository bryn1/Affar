import { useCallback, useEffect, useState } from 'react'

// useResource — the one rows/loading/error + reload(useCallback) scaffold the
// list views repeated verbatim (MC 11502 R3b P4-frontend). `deps` is the
// original reload-callback dep list (typically [token]): the fetch re-runs
// exactly when the per-view scaffold re-ran it before. `setError` is returned
// because mutation handlers report their failures into the same channel.
// A view whose loader deviates from this shape (clears error before fetch,
// resets on param change, or has no reload at all) keeps its own scaffold —
// converting it would change observable behaviour, which this wave forbids.
export function useResource(listFn, deps = []) {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const reload = useCallback(() => {
    setLoading(true)
    listFn().then((d) => setRows(d || [])).catch((e) => setError(e.message)).finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
  useEffect(() => { reload() }, [reload])

  return { rows, loading, error, setError, reload }
}
