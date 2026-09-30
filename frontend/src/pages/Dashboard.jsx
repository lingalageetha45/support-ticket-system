import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')
  const { user } = useAuth()

  useEffect(() => {
    api
      .get('/dashboard/stats')
      .then((res) => setStats(res.data.data))
      .catch(() => setError('Unable to load dashboard statistics.'))
  }, [])

  if (error) {
    return (
      <div className="page">
        <div className="alert alert-error">{error}</div>
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="page">
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-title">Loading dashboard</div>
            <p className="empty-state-text">
              Please wait while we load your ticket statistics.
            </p>
          </div>
        </div>
      </div>
    )
  }

  const ticketStats = [
    {
      label: 'Total Tickets',
      value: stats.total_tickets,
      description: 'All tickets',
    },
    {
      label: 'Open',
      value: stats.open_tickets,
      description: 'Waiting for action',
      className: 'dashboard-blue',
    },
    {
      label: 'In Progress',
      value: stats.in_progress_tickets,
      description: 'Currently being handled',
      className: 'dashboard-orange',
    },
    {
      label: 'Resolved',
      value: stats.resolved_tickets,
      description: 'Ready for closure',
      className: 'dashboard-green',
    },
    {
      label: 'Closed',
      value: stats.closed_tickets,
      description: 'Completed tickets',
    },
    {
      label: 'Overdue',
      value: stats.overdue_tickets,
      description: 'Past SLA deadline',
      className: 'dashboard-red',
    },
    {
      label: 'Critical',
      value: stats.critical_tickets,
      description: 'Highest priority',
      className: 'dashboard-purple',
    },
  ]

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">
            Welcome back, {user?.full_name || user?.email || 'User'}.
            Here's an overview of your support activity.
          </p>
        </div>

        <Link to="/tickets" className="btn btn-primary">
          View Tickets
        </Link>
      </div>

      <div className="dashboard-section-title">
        Ticket Overview
      </div>

      <div className="stats-grid dashboard-stats">
        {ticketStats.map((item) => (
          <div
            key={item.label}
            className={`stat-card dashboard-stat-card ${item.className || ''}`}
          >
            <div className="stat-label">{item.label}</div>
            <div className="stat-value">{item.value}</div>
            <div className="stat-description">{item.description}</div>
          </div>
        ))}
      </div>

      {user?.role === 'admin' && (
        <>
          <div className="dashboard-section-title">
            User Overview
          </div>

          <div className="stats-grid dashboard-stats dashboard-admin-stats">
            <div className="stat-card dashboard-stat-card">
              <div className="stat-label">Customers</div>
              <div className="stat-value">{stats.total_customers}</div>
              <div className="stat-description">
                Registered customers
              </div>
            </div>

            <div className="stat-card dashboard-stat-card">
              <div className="stat-label">Agents</div>
              <div className="stat-value">{stats.total_agents}</div>
              <div className="stat-description">
                Support agents
              </div>
            </div>

            <div className="stat-card dashboard-stat-card dashboard-green">
              <div className="stat-label">Active Agents</div>
              <div className="stat-value">{stats.active_agents}</div>
              <div className="stat-description">
                Currently available
              </div>
            </div>
          </div>
        </>
      )}

      {user?.role === 'agent' && (
        <>
          <div className="dashboard-section-title">
            My Work
          </div>

          <div className="stats-grid dashboard-stats dashboard-agent-stats">
            <div className="stat-card dashboard-stat-card dashboard-blue">
              <div className="stat-label">My Open</div>
              <div className="stat-value">{stats.my_open_tickets}</div>
              <div className="stat-description">
                Tickets needing attention
              </div>
            </div>

            <div className="stat-card dashboard-stat-card dashboard-red">
              <div className="stat-label">My Overdue</div>
              <div className="stat-value">{stats.my_overdue_tickets}</div>
              <div className="stat-description">
                Tickets past SLA
              </div>
            </div>

            <div className="stat-card dashboard-stat-card dashboard-green">
              <div className="stat-label">My Resolved</div>
              <div className="stat-value">{stats.my_resolved_tickets}</div>
              <div className="stat-description">
                Recently resolved
              </div>
            </div>
          </div>
        </>
      )}

      <div className="dashboard-action-card">
        <div>
          <h2>Manage support tickets</h2>
          <p>
            View, search, update and manage your support tickets.
          </p>
        </div>

        <Link to="/tickets" className="btn btn-primary">
          Open Tickets
        </Link>
      </div>
    </div>
  )
}