import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    email: '',
    first_name: '',
    last_name: '',
    phone: '',
    password: '',
    password_confirm: '',
  })
  const [err, setErr] = useState('')

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setErr('')
    try {
      await register(form)
      navigate('/')
    } catch (e) {
      setErr(e.data ? JSON.stringify(e.data) : e.message)
    }
  }

  return (
    <div className="container">
      <div className="card auth-wrap">
        <h1 className="page-title" style={{ textAlign: 'center' }}>
          Create account
        </h1>
        <form onSubmit={submit}>
          <div className="field">
            <label>Email</label>
            <input type="email" value={form.email} onChange={set('email')} required />
          </div>
          <div className="row">
            <div className="field" style={{ flex: 1 }}>
              <label>First name</label>
              <input value={form.first_name} onChange={set('first_name')} />
            </div>
            <div className="field" style={{ flex: 1 }}>
              <label>Last name</label>
              <input value={form.last_name} onChange={set('last_name')} />
            </div>
          </div>
          <div className="field">
            <label>Phone</label>
            <input value={form.phone} onChange={set('phone')} />
          </div>
          <div className="field">
            <label>Password</label>
            <input type="password" value={form.password} onChange={set('password')} required />
          </div>
          <div className="field">
            <label>Confirm password</label>
            <input
              type="password"
              value={form.password_confirm}
              onChange={set('password_confirm')}
              required
            />
          </div>
          {err && <div className="error-msg">{err}</div>}
          <button style={{ width: '100%' }}>Sign up</button>
        </form>
        <p className="muted" style={{ textAlign: 'center', marginTop: 16 }}>
          Have an account? <Link to="/login" style={{ color: 'var(--primary)' }}>Login</Link>
        </p>
      </div>
    </div>
  )
}
