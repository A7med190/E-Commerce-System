import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="container page" style={{ textAlign: 'center', paddingTop: 80 }}>
      <h1 style={{ fontSize: 72, fontWeight: 800, color: 'var(--primary)' }}>404</h1>
      <p className="muted" style={{ fontSize: 18, marginBottom: 24 }}>
        Page not found
      </p>
      <Link to="/" style={{ padding: '10px 20px', borderRadius: 8 }}>
        Go home
      </Link>
    </div>
  )
}
