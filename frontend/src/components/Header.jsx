import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { cartApi } from '../api/endpoints'

export default function Header() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [q, setQ] = useState('')
  const [cartCount, setCartCount] = useState(0)

  useEffect(() => {
    if (!user) {
      setCartCount(0)
      return
    }
    cartApi
      .get()
      .then((c) => setCartCount(c.total_items || 0))
      .catch(() => setCartCount(0))
  }, [user])

  const onSearch = (e) => {
    e.preventDefault()
    navigate(`/search?q=${encodeURIComponent(q)}`)
  }

  return (
    <header className="header">
      <div className="container header-inner">
        <Link to="/" className="logo">
          SmartShop
        </Link>
        <form className="search-bar" onSubmit={onSearch}>
          <input
            placeholder="Search products..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <button type="submit">Search</button>
        </form>
        <div className="nav-actions">
          <Link to="/cart" style={{ position: 'relative', fontWeight: 600 }}>
            🛒 Cart
            {cartCount > 0 && (
              <span className="badge" style={{ position: 'absolute', top: -8, right: -14 }}>
                {cartCount}
              </span>
            )}
          </Link>
          <Link to="/wishlist">♡ Wishlist</Link>
          {user ? (
            <>
              <Link to="/orders">Orders</Link>
              <Link to="/profile">{user.first_name || user.email}</Link>
              <button className="ghost" onClick={logout}>
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="secondary" style={{ padding: '8px 14px', borderRadius: 8 }}>
                Login
              </Link>
              <Link to="/register" style={{ padding: '8px 14px', borderRadius: 8 }}>
                Sign up
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
