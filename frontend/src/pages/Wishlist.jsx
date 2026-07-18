import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { wishlistApi } from '../api/endpoints'
import { useAuth } from '../context/AuthContext'
import ProductCard from '../components/ProductCard'

export default function Wishlist() {
  const { user } = useAuth()
  const [wishlist, setWishlist] = useState(null)

  useEffect(() => {
    if (user) load()
  }, [user])

  const load = () => wishlistApi.get().then(setWishlist)
  const remove = (id) => wishlistApi.removeItem(id).then(load)

  if (!user) return <div className="container page empty">Please log in to view your wishlist.</div>
  if (!wishlist) return <div className="container page empty">Loading...</div>

  return (
    <div className="container page">
      <h1 className="page-title">Wishlist ({wishlist.item_count})</h1>
      {wishlist.items.length === 0 ? (
        <div className="empty">
          Nothing saved yet. <Link to="/products" style={{ color: 'var(--primary)' }}>Browse products</Link>
        </div>
      ) : (
        <div className="grid products-grid">
          {wishlist.items.map((item) => (
            <div key={item.id} style={{ position: 'relative' }}>
              <ProductCard product={item.product} />
              <button
                className="ghost danger"
                style={{ position: 'absolute', top: 8, right: 8, padding: '4px 8px' }}
                onClick={() => remove(item.id)}
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
