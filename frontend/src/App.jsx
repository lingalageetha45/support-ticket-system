import { Routes, Route, Navigate, Link, NavLink } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Tickets from './pages/Tickets'
import TicketDetail from './pages/TicketDetail'
import Users from './pages/Users'

function Layout({ children }) {
  const { user, logout } = useAuth()

  return (
    <div className="app-shell">
      <header className="navbar">
        <Link to="/" className="logo">
          <span className="logo-icon">🎫</span>
          <span>Support Tickets</span>
        </Link>

        <nav className="main-nav">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              isActive ? 'nav-link active' : 'nav-link'
            }
          >
            Dashboard
          </NavLink>

          <NavLink
            to="/tickets"
            className={({ isActive }) =>
              isActive ? 'nav-link active' : 'nav-link'
            }
          >
            Tickets
          </NavLink>

          {user?.role === 'admin' && (
            <NavLink
              to="/users"
              className={({ isActive }) =>
                isActive ? 'nav-link active' : 'nav-link'
              }
            >
              Users
            </NavLink>
          )}
        </nav>

        <div className="navbar-user">
          <div className="user-details">
            <span className="user-name">
              {user?.full_name || 'User'}
            </span>

            <span className="user-role">
              {user?.role}
            </span>
          </div>

          <button
            className="btn btn-secondary"
            onClick={logout}
          >
            Logout
          </button>
        </div>
      </header>

      <main className="container">
        {children}
      </main>
    </div>
  )
}

function PrivateRoute({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="container">
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-title">
              Loading...
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <Layout>{children}</Layout>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route path="/register" element={<Register />} />

      <Route
        path="/"
        element={
          <PrivateRoute>
            <Dashboard />
          </PrivateRoute>
        }
      />

      <Route
        path="/tickets"
        element={
          <PrivateRoute>
            <Tickets />
          </PrivateRoute>
        }
      />

      <Route
        path="/tickets/:id"
        element={
          <PrivateRoute>
            <TicketDetail />
          </PrivateRoute>
        }
      />

      <Route
        path="/users"
        element={
          <PrivateRoute>
            <Users />
          </PrivateRoute>
        }
      />

      <Route
        path="*"
        element={<Navigate to="/" replace />}
      />
    </Routes>
  )
}