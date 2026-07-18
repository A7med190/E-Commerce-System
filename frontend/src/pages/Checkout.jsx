import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { cartApi, authApi, ordersApi } from '../api/endpoints'
import { useAuth } from '../context/AuthContext'

function price(n) {
  return `$${(Number(n) || 0).toFixed(2)}`
}

export default function Checkout() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [cart, setCart] = useState(null)
  const [addresses, setAddresses] = useState([])
  const [shippingId, setShippingId] = useState('')
  const [billingId, setBillingId] = useState('')
  const [notes, setNotes] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!user) return
    cartApi.get().then(setCart)
    authApi.addresses().then((d) => {
      const list = d.results || d || []
      setAddresses(list)
      if (list.length) setShippingId(list[0].id)
    })
  }, [user])

  const submit = async (e) => {
    e.preventDefault()
    setErr('')
    if (!shippingId) {
      setErr('Please add a shipping address first.')
      return
    }
    setBusy(true)
    try {
      const order = await ordersApi.create({
        shipping_address_id: shippingId,
        billing_address_id: billingId || undefined,
        notes,
      })
      navigate(`/orders/${order.id}`)
    } catch (e) {
      setErr(e.message)
    } finally {
      setBusy(false)
    }
  }

  if (!user) return <div className="container page empty">Please log in to checkout.</div>
  if (!cart) return <div className="container page empty">Loading...</div>
  if (cart.items.length === 0)
    return <div className="container page empty">Your cart is empty.</div>

  return (
    <div className="container page">
      <h1 className="page-title">Checkout</h1>
      <div className="grid detail-grid">
        <div className="card" style={{ padding: 20 }}>
          <h3 style={{ marginBottom: 12 }}>Order summary</h3>
          {cart.items.map((i) => (
            <div key={i.id} className="between row" style={{ padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
              <span>
                {i.product.name} × {i.quantity}
              </span>
              <strong>{price(i.total_price)}</strong>
            </div>
          ))}
          <div className="between row" style={{ marginTop: 12 }}>
            <span>Total</span>
            <strong style={{ fontSize: 20 }}>{price(cart.total_price)}</strong>
          </div>
        </div>

        <form className="card" style={{ padding: 20 }} onSubmit={submit}>
          <h3 style={{ marginBottom: 12 }}>Shipping address</h3>
          {addresses.length === 0 ? (
            <div className="muted">
              No addresses. Add one in your <a href="/profile" style={{ color: 'var(--primary)' }}>profile</a>.
            </div>
          ) : (
            <div className="field">
              <select value={shippingId} onChange={(e) => setShippingId(e.target.value)}>
                {addresses.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.street}, {a.city} ({a.address_type})
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="field">
            <label>Billing address (optional)</label>
            <select value={billingId} onChange={(e) => setBillingId(e.target.value)}>
              <option value="">Same as shipping</option>
              {addresses.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.street}, {a.city}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Notes</label>
            <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} />
          </div>

          {err && <div className="error-msg">{err}</div>}
          <button style={{ width: '100%' }} disabled={busy || addresses.length === 0}>
            {busy ? 'Placing order...' : 'Place order'}
          </button>
        </form>
      </div>
    </div>
  )
}
