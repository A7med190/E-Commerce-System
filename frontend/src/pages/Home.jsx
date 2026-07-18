import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { productsApi, categoriesApi } from '../api/endpoints'
import ProductCard from '../components/ProductCard'

export default function Home() {
  const [featured, setFeatured] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      productsApi.list({ featured: 'true' }),
      categoriesApi.list(),
    ])
      .then(([p, c]) => {
        setFeatured(p.results || [])
        setCategories(c.results || c || [])
      })
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="container page">
      <div className="hero">
        <h1>Design it your way</h1>
        <p>Customizable products, built to order. Pick options, see live pricing, and check out in minutes.</p>
      </div>

      <h2 className="page-title">Shop by category</h2>
      <div className="grid products-grid" style={{ marginBottom: 36 }}>
        {(categories.results || categories || []).map((c) => (
          <Link key={c.id} to={`/products?category=${c.slug}`} className="card product-card">
            <div className="product-thumb">📦</div>
            <div className="product-card-body">
              <div className="product-name">{c.name}</div>
              <div className="product-cat">{c.product_count} products</div>
            </div>
          </Link>
        ))}
      </div>

      <h2 className="page-title">Featured products</h2>
      {loading ? (
        <div className="empty">Loading...</div>
      ) : (
        <div className="grid products-grid">
          {featured.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      )}
      {!loading && featured.length === 0 && <div className="empty">No featured products yet.</div>}
    </div>
  )
}
