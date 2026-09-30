import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="card login-card">
        <h1 style={{ marginBottom: '0.5rem', textAlign: 'center' }}>Support Tickets</h1>
        <p style={{ textAlign: 'center', color: '#6b7280', marginBottom: '1.5rem' }}>Sign in to your account</p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="you@example.com" />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          {error && <p className="error">{error}</p>}
          <button className="btn btn-primary" style={{ width: '100%', marginTop: '0.5rem' }} disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        <p style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.9rem' }}>
          Don't have an account? <Link to="/register">Register</Link>
        </p>
        <div style={{ marginTop: '1.5rem', padding: '0.75rem', background: '#f0f9ff', borderRadius: '0.5rem', fontSize: '0.8rem' }}>
          <strong>Demo accounts:</strong><br />
          Admin: admin@support.com / Admin@12345<br />
          Agent: agent@support.com / Agent@12345<br />
          Customer: customer@example.com / Customer@12345
        </div>
      </div>
    </div>
  )
}
