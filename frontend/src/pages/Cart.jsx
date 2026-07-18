import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { cartApi } from '../api/endpoints'
import { useAuth } from '../context/AuthContext'

function price(n) {
  return `$${(Number(n) || 0).toFixed(2)}`
}

export default function Cart() {
  const { user } = useAuth()
  const [cart, setCart] = useState(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    if (user) load()
  }, [user])

  const load = () => cartApi.get().then(setCart).catch((e) => setErr(e.message))

  const updateQty = (id, qty) => {
    if (qty < 1) return
    cartApi.updateItem(id, qty).then(load)
  }
  const remove = (id) => cartApi.removeItem(id).then(load)
  const clear = () => cartApi.clear().then(load)

  if (!user) return <div className="container page empty">Please log in to view your cart.</div>
  if (!cart) return <div className="container page empty">Loading cart...</div>

  return (
    <div className="container page">
      <div className="between row">
        <h1 className="page-title" style={{ margin: 0 }}>
          Your cart
        </h1>
        {cart.items.length > 0 && (
          <button className="ghost danger" onClick={clear}>
            Clear cart
          </button>
        )}
      </div>

      {err && <div className="error-msg">{err}</div>}

      {cart.items.length === 0 ? (
        <div className="empty">
          Cart is empty. <Link to="/products" style={{ color: 'var(--primary)' }}>Browse products</Link>
        </div>
      ) : (
        <>
          <div className="card" style={{ marginTop: 16 }}>
            {cart.items.map((item) => (
              <div className="cart-item" key={item.id}>
                <div className="product-thumb" style={{ width: 64, aspectRatio: '1/1', fontSize: 28 }}>
                  🛍️
                </div>
                <div style={{ flex: 1 }}>
                  <Link to={`/product/${item.product.slug}`} style={{ fontWeight: 600 }}>
                    {item.product.name}
                  </Link>
                  {item.customizations?.length > 0 && (
                    <div className="muted" style={{ fontSize: 12 }}>
                      {item.customizations
                        .map((c) => `Option ${c.option_id}: [${(c.value_ids || [c.value_id]).join(', ')}]`)
                        .join(' | ')}
                    </div>
                  )}
                  <div className="muted" style={{ fontSize: 13 }}>
                    {price(item.price_at_add)} each
                  </div>
                </div>
                <div className="qty">
                  <button onClick={() => updateQty(item.id, item.quantity - 1)}>−</button>
                  <span>{item.quantity}</span>
                  <button onClick={() => updateQty(item.id, item.quantity + 1)}>+</button>
                </div>
                <div style={{ minWidth: 80, textAlign: 'right', fontWeight: 700 }}>
                  {price(item.total_price)}
                </div>
                <button className="ghost danger" onClick={() => remove(item.id)}>
                  ✕
                </button>
              </div>
            ))}
          </div>

          <div className="card" style={{ padding: 20, marginTop: 16 }}>
            <div className="between row">
              <span>
                {cart.total_items} item(s)
              </span>
              <strong style={{ fontSize: 20 }}>Total: {price(cart.total_price)}</strong>
            </div>
            <div className="row" style={{ marginTop: 16, justifyContent: 'flex-end' }}>
              <Link to="/checkout" style={{ padding: '10px 20px', borderRadius: 8 }}>
                Checkout
              </Link>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
