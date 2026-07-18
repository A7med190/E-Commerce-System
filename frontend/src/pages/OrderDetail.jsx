import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ordersApi } from '../api/endpoints'
import { useAuth } from '../context/AuthContext'

function price(n) {
  return `$${(Number(n) || 0).toFixed(2)}`
}

export default function OrderDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (user) ordersApi.detail(id).then(setOrder).finally(() => setLoading(false))
    else setLoading(false)
  }, [id, user])

  if (!user) return <div className="container page empty">Please log in.</div>
  if (loading) return <div className="container page empty">Loading...</div>
  if (!order) return <div className="container page empty">Order not found.</div>

  return (
    <div className="container page">
      <h1 className="page-title">Order {order.order_number}</h1>
      <div className="badge" style={{ marginBottom: 16 }}>
        {order.status}
      </div>

      <div className="card" style={{ padding: 20, marginBottom: 16 }}>
        <table className="table">
          <thead>
            <tr>
              <th>Product</th>
              <th>Qty</th>
              <th>Price</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            {order.items.map((i) => (
              <tr key={i.id}>
                <td>{i.product_name}</td>
                <td>{i.quantity}</td>
                <td>{price(i.product_price)}</td>
                <td>{price(i.total)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="row between" style={{ marginTop: 16 }}>
          <span>Subtotal: {price(order.subtotal)}</span>
          <span>Tax: {price(order.tax)}</span>
          <span>Shipping: {price(order.shipping_cost)}</span>
          <strong>Total: {price(order.total)}</strong>
        </div>
      </div>

      <div className="card" style={{ padding: 20 }}>
        <h3 style={{ marginBottom: 10 }}>Shipping address</h3>
        <p className="muted">
          {order.shipping_address.street}, {order.shipping_address.city},{' '}
          {order.shipping_address.state} {order.shipping_address.zip_code},{' '}
          {order.shipping_address.country}
        </p>
        <h3 style={{ margin: '16px 0 10px' }}>Status history</h3>
        {order.status_history.map((h, idx) => (
          <div key={idx} className="muted" style={{ fontSize: 13 }}>
            {h.status} — {new Date(h.created_at).toLocaleString()}
          </div>
        ))}
      </div>

      <Link to="/orders" className="ghost" style={{ display: 'inline-block', marginTop: 16 }}>
        ← Back to orders
      </Link>
    </div>
  )
}
