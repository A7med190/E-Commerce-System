import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { productsApi, categoriesApi } from '../api/endpoints'
import ProductCard from '../components/ProductCard'

const SORTS = [
  { value: '', label: 'Default' },
  { value: 'price_asc', label: 'Price: Low to High' },
  { value: 'price_desc', label: 'Price: High to Low' },
  { value: '-average_rating', label: 'Top Rated' },
  { value: '-created_at', label: 'Newest' },
]

export default function Products() {
  const [params, setParams] = useSearchParams()
  const category = params.get('category') || ''
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [sort, setSort] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    categoriesApi.list().then((d) => setCategories(d.results || d || []))
  }, [])

  useEffect(() => {
    setLoading(true)
    productsApi
      .list({ category, ordering: sort })
      .then((d) => setProducts(d.results || []))
      .finally(() => setLoading(false))
  }, [category, sort])

  return (
    <div className="container page">
      <div className="between row" style={{ marginBottom: 16 }}>
        <h1 className="page-title" style={{ margin: 0 }}>
          {category ? `Category: ${category}` : 'All products'}
        </h1>
        <select value={sort} onChange={(e) => setSort(e.target.value)} style={{ width: 220 }}>
          {SORTS.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
      </div>

      <div className="row" style={{ flexWrap: 'wrap', marginBottom: 20 }}>
        <button
          className={!category ? 'secondary' : 'ghost'}
          onClick={() => setParams({})}
        >
          All
        </button>
        {categories.map((c) => (
          <button
            key={c.id}
            className={category === c.slug ? 'secondary' : 'ghost'}
            onClick={() => setParams({ category: c.slug })}
          >
            {c.name}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="empty">Loading...</div>
      ) : (
        <div className="grid products-grid">
          {products.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      )}
      {!loading && products.length === 0 && (
        <div className="empty">No products found.</div>
      )}
    </div>
  )
}
