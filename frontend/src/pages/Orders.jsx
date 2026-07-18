import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { ordersApi, authApi } from '../api/endpoints'
import { useAuth } from '../context/AuthContext'

function price(n) {
  return `$${(Number(n) || 0).toFixed(2)}`
}

export default function Orders() {
  const { user } = useAuth()
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (user) {
      ordersApi.list().then((d) => setOrders(d.results || d || [])).finally(() => setLoading(false))
    } else setLoading(false)
  }, [user])

  if (!user) return <div className="container page empty">Please log in to view your orders.</div>

  return (
    <div className="container page">
      <h1 className="page-title">Your orders</h1>
      {loading ? (
        <div className="empty">Loading...</div>
      ) : orders.length === 0 ? (
        <div className="empty">No orders yet.</div>
      ) : (
        <div className="card">
          <table className="table">
            <thead>
              <tr>
                <th>Order #</th>
                <th>Date</th>
                <th>Status</th>
                <th>Total</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id}>
                  <td>{o.order_number}</td>
                  <td>{new Date(o.created_at).toLocaleDateString()}</td>
                  <td>
                    <span className="badge">{o.status}</span>
                  </td>
                  <td>{price(o.total)}</td>
                  <td>
                    <Link to={`/orders/${o.id}`} className="secondary" style={{ padding: '6px 12px' }}>
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
