import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { searchApi } from '../api/endpoints'
import ProductCard from '../components/ProductCard'

const SORTS = [
  { value: '', label: 'Relevance' },
  { value: 'price_asc', label: 'Price: Low to High' },
  { value: 'price_desc', label: 'Price: High to Low' },
  { value: 'rating_desc', label: 'Top Rated' },
  { value: 'newest', label: 'Newest' },
]

export default function Search() {
  const [params, setParams] = useSearchParams()
  const q = params.get('q') || ''
  const [sort, setSort] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    searchApi
      .search(q, sort)
      .then((d) => setResults(d.results || d || []))
      .finally(() => setLoading(false))
  }, [q, sort])

  return (
    <div className="container page">
      <div className="between row" style={{ marginBottom: 16 }}>
        <h1 className="page-title" style={{ margin: 0 }}>
          {q ? `Results for "${q}"` : 'Search'}
        </h1>
        <select value={sort} onChange={(e) => setSort(e.target.value)} style={{ width: 220 }}>
          {SORTS.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="empty">Searching...</div>
      ) : (
        <div className="grid products-grid">
          {results.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      )}
      {!loading && results.length === 0 && (
        <div className="empty">No results found.</div>
      )}
    </div>
  )
}
