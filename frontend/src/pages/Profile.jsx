import { useState, useEffect } from 'react'
import { authApi } from '../api/endpoints'
import { useAuth } from '../context/AuthContext'

export default function Profile() {
  const { user, setUser } = useAuth()
  const [addresses, setAddresses] = useState([])
  const [form, setForm] = useState({ street: '', city: '', state: '', zip_code: '', country: '', address_type: 'shipping' })
  const [pw, setPw] = useState({ old_password: '', new_password: '', new_password_confirm: '' })
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')

  const loadAddresses = () => authApi.addresses().then((d) => setAddresses(d.results || d || []))

  useEffect(() => {
    if (user) loadAddresses()
  }, [user])

  if (!user) return <div className="container page empty">Please log in.</div>

  const set = (k, obj, setter) => (e) => setter({ ...obj, [k]: e.target.value })

  const addAddress = async (e) => {
    e.preventDefault()
    setErr('')
    setMsg('')
    try {
      await authApi.createAddress(form)
      setForm({ street: '', city: '', state: '', zip_code: '', country: '', address_type: 'shipping' })
      setMsg('Address added.')
      loadAddresses()
    } catch (e) {
      setErr(e.message)
    }
  }

  const delAddress = (id) => authApi.deleteAddress(id).then(loadAddresses)

  const changePw = async (e) => {
    e.preventDefault()
    setErr('')
    setMsg('')
    try {
      await authApi.changePassword(pw)
      setPw({ old_password: '', new_password: '', new_password_confirm: '' })
      setMsg('Password changed.')
    } catch (e) {
      setErr(e.message)
    }
  }

  return (
    <div className="container page">
      <h1 className="page-title">Profile</h1>
      <div className="card" style={{ padding: 20, marginBottom: 20 }}>
        <p>
          <strong>{user.first_name} {user.last_name}</strong>
        </p>
        <p className="muted">{user.email}</p>
        <p className="muted">Role: {user.role}</p>
      </div>

      <div className="card" style={{ padding: 20, marginBottom: 20 }}>
        <h3 style={{ marginBottom: 12 }}>Addresses</h3>
        {addresses.length === 0 && <div className="muted" style={{ marginBottom: 12 }}>No addresses yet.</div>}
        {addresses.map((a) => (
          <div key={a.id} className="between row" style={{ padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
            <span>
              {a.address_type}: {a.street}, {a.city}, {a.state} {a.zip_code}, {a.country}
            </span>
            <button className="ghost danger" onClick={() => delAddress(a.id)}>
              ✕
            </button>
          </div>
        ))}

        <form onSubmit={addAddress} style={{ marginTop: 16 }}>
          <h4 style={{ marginBottom: 10 }}>Add address</h4>
          <div className="row">
            <div className="field" style={{ flex: 2 }}>
              <label>Street</label>
              <input value={form.street} onChange={set('street', form, setForm)} required />
            </div>
            <div className="field" style={{ flex: 1 }}>
              <label>City</label>
              <input value={form.city} onChange={set('city', form, setForm)} required />
            </div>
          </div>
          <div className="row">
            <div className="field" style={{ flex: 1 }}>
              <label>State</label>
              <input value={form.state} onChange={set('state', form, setForm)} />
            </div>
            <div className="field" style={{ flex: 1 }}>
              <label>Zip</label>
              <input value={form.zip_code} onChange={set('zip_code', form, setForm)} required />
            </div>
            <div className="field" style={{ flex: 1 }}>
              <label>Country</label>
              <input value={form.country} onChange={set('country', form, setForm)} required />
            </div>
            <div className="field" style={{ flex: 1 }}>
              <label>Type</label>
              <select value={form.address_type} onChange={set('address_type', form, setForm)}>
                <option value="shipping">shipping</option>
                <option value="billing">billing</option>
              </select>
            </div>
          </div>
          <button type="submit">Add address</button>
        </form>
      </div>

      <div className="card" style={{ padding: 20 }}>
        <h3 style={{ marginBottom: 12 }}>Change password</h3>
        <form onSubmit={changePw}>
          <div className="field">
            <label>Current password</label>
            <input type="password" value={pw.old_password} onChange={set('old_password', pw, setPw)} required />
          </div>
          <div className="row">
            <div className="field" style={{ flex: 1 }}>
              <label>New password</label>
              <input type="password" value={pw.new_password} onChange={set('new_password', pw, setPw)} required />
            </div>
            <div className="field" style={{ flex: 1 }}>
              <label>Confirm</label>
              <input
                type="password"
                value={pw.new_password_confirm}
                onChange={set('new_password_confirm', pw, setPw)}
                required
              />
            </div>
          </div>
          {msg && <div className="ok-msg">{msg}</div>}
          {err && <div className="error-msg">{err}</div>}
          <button type="submit">Update password</button>
        </form>
      </div>
    </div>
  )
}
