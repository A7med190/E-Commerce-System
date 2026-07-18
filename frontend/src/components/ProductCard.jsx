import { Link } from 'react-router-dom'

function price(n) {
  return `$${Number(n).toFixed(2)}`
}

export default function ProductCard({ product }) {
  return (
    <Link to={`/product/${product.slug}`} className="card product-card">
      <div className="product-thumb">🛍️</div>
      <div className="product-card-body">
        <div className="product-name">{product.name}</div>
        <div className="product-cat">{product.category_name}</div>
        {product.average_rating > 0 && (
          <div className="rating">
            ★ {Number(product.average_rating).toFixed(1)} ({product.review_count})
          </div>
        )}
        <div className="price">{price(product.base_price)}</div>
        {product.is_featured && <span className="badge">Featured</span>}
      </div>
    </Link>
  )
}
