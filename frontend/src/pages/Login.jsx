import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setErr('')
    try {
      await login(email, password)
      navigate('/')
    } catch (e) {
      setErr(e.message)
    }
  }

  return (
    <div className="container">
      <div className="card auth-wrap">
        <h1 className="page-title" style={{ textAlign: 'center' }}>
          Welcome back
        </h1>
        <form onSubmit={submit}>
          <div className="field">
            <label>Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div className="field">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {err && <div className="error-msg">{err}</div>}
          <button style={{ width: '100%' }}>Login</button>
        </form>
        <p className="muted" style={{ textAlign: 'center', marginTop: 16 }}>
          No account? <Link to="/register" style={{ color: 'var(--primary)' }}>Sign up</Link>
        </p>
      </div>
    </div>
  )
}
