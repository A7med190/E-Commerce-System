import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import {
  productsApi,
  cartApi,
  wishlistApi,
  reviewsApi,
} from '../api/endpoints'
import { useAuth } from '../context/AuthContext'

function price(n) {
  return `$${Number(n).toFixed(2)}`
}

export default function ProductDetail() {
  const { slug } = useParams()
  const { user } = useAuth()
  const [product, setProduct] = useState(null)
  const [customizations, setCustomizations] = useState([])
  const [reviews, setReviews] = useState([])
  const [selected, setSelected] = useState({})
  const [quantity, setQuantity] = useState(1)
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    setMsg('')
    setErr('')
    Promise.all([
      productsApi.detail(slug),
      productsApi.customizations(slug),
      reviewsApi.list(''),
    ])
      .then(([p, cust, rev]) => {
        setProduct(p)
        setCustomizations(cust)
        setReviews(rev.results || rev || [])
        const initial = {}
        cust.forEach((c) => {
          const def = c.option.values.find((v) => v.is_default)
          if (def) initial[c.option.id] = def.id
        })
        setSelected(initial)
      })
      .finally(() => setLoading(false))
  }, [slug])

  const totalModifier = customizations.reduce((sum, c) => {
    const vid = selected[c.option.id]
    const val = c.option.values.find((v) => v.id === vid)
    if (!val || !val.price_modifier) return sum
    if (val.modifier_type === 'fixed') return sum + Number(val.price_modifier)
    if (val.modifier_type === 'percent')
      return sum + (Number(product.base_price) * Number(val.price_modifier)) / 100
    return sum
  }, 0)

  const unitPrice = Number(product ? product.base_price : 0) + totalModifier
  const lineTotal = unitPrice * quantity

  const selectValue = (optionId, valueId, isMulti, allowMultiple) => {
    setSelected((prev) => {
      if (isMulti) {
        const cur = prev[optionId] ? [].concat(prev[optionId]) : []
        if (cur.includes(valueId)) return { ...prev, [optionId]: cur.filter((x) => x !== valueId) }
        return { ...prev, [optionId]: allowMultiple ? [...cur, valueId] : [valueId] }
      }
      return { ...prev, [optionId]: valueId }
    })
  }

  const addToCart = async () => {
    setErr('')
    setMsg('')
    if (!user) {
      setErr('Please log in to add items to your cart.')
      return
    }
    const customizationPayload = Object.entries(selected)
      .filter(([, v]) => v)
      .map(([optionId, v]) => ({
        option_id: Number(optionId),
        value_ids: Array.isArray(v) ? v : [v],
      }))
    try {
      await cartApi.addItem({
        product_id: product.id,
        quantity,
        customizations: customizationPayload,
      })
      setMsg('Added to cart!')
    } catch (e) {
      setErr(e.message)
    }
  }

  const addToWishlist = async () => {
    if (!user) {
      setErr('Please log in to use the wishlist.')
      return
    }
    try {
      await wishlistApi.addItem(product.id)
      setMsg('Added to wishlist!')
    } catch (e) {
      setErr(e.message)
    }
  }

  if (loading) return <div className="container page empty">Loading...</div>
  if (!product) return <div className="container page empty">Product not found.</div>

  return (
    <div className="container page">
      <div className="grid detail-grid">
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div className="product-thumb" style={{ aspectRatio: '4 / 3', fontSize: 90 }}>
            🛍️
          </div>
        </div>

        <div>
          <div className="row between">
            <h1 style={{ fontSize: 28 }}>{product.name}</h1>
            {product.is_featured && <span className="badge">Featured</span>}
          </div>
          <div className="muted" style={{ margin: '4px 0 10px' }}>
            {product.category_name}
          </div>
          <div className="price" style={{ fontSize: 24, marginBottom: 12 }}>
            {price(unitPrice)}
          </div>
          {product.average_rating > 0 && (
            <div className="rating" style={{ marginBottom: 12 }}>
              ★ {Number(product.average_rating).toFixed(1)} ({product.review_count} reviews)
            </div>
          )}
          <p className="muted" style={{ marginBottom: 18 }}>
            {product.description}
          </p>

          {customizations.map((c) => (
            <div className="option-group" key={c.id}>
              <h4>
                {c.option.name}
                {c.is_required && <span className="muted"> *</span>}
              </h4>
              <div className="option-values">
                {c.option.values.map((v) => {
                  const isActive =
                    Array.isArray(selected[c.option.id])
                      ? selected[c.option.id].includes(v.id)
                      : selected[c.option.id] === v.id
                  const mod =
                    v.price_modifier && v.price_modifier !== '0'
                      ? ` (+${v.modifier_type === 'percent' ? v.price_modifier + '%' : '$' + v.price_modifier})`
                      : ''
                  return (
                    <span
                      key={v.id}
                      className={`chip ${isActive ? 'active' : ''}`}
                      onClick={() =>
                        selectValue(
                          c.option.id,
                          v.id,
                          c.option.option_type === 'multi_select',
                          c.option.option_type === 'multi_select'
                        )
                      }
                    >
                      {v.value}
                      {mod}
                    </span>
                  )
                })}
              </div>
            </div>
          ))}

          <div className="field" style={{ marginTop: 16 }}>
            <label>Quantity</label>
            <div className="qty">
              <button onClick={() => setQuantity((q) => Math.max(1, q - 1))}>−</button>
              <span style={{ minWidth: 30, textAlign: 'center' }}>{quantity}</span>
              <button onClick={() => setQuantity((q) => q + 1)}>+</button>
            </div>
          </div>

          <div className="row" style={{ marginTop: 8 }}>
            <strong>Total: {price(lineTotal)}</strong>
          </div>

          {err && <div className="error-msg">{err}</div>}
          {msg && <div className="ok-msg">{msg}</div>}

          <div className="row" style={{ marginTop: 12 }}>
            <button onClick={addToCart}>Add to cart</button>
            <button className="secondary" onClick={addToWishlist}>
              ♡ Save
            </button>
          </div>
        </div>
      </div>

      <div className="card" style={{ padding: 20, marginTop: 28 }}>
        <h2 className="page-title" style={{ fontSize: 20 }}>
          Reviews
        </h2>
        {reviews.length === 0 ? (
          <div className="muted">No reviews yet.</div>
        ) : (
          reviews.map((r) => (
            <div key={r.id} style={{ padding: '12px 0', borderTop: '1px solid var(--border)' }}>
              <div className="row between">
                <strong>{r.user_email}</strong>
                <span className="rating">{'★'.repeat(r.rating)}</span>
              </div>
              <p style={{ marginTop: 6 }}>{r.comment}</p>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
