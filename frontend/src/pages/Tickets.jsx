import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'

export default function Tickets() {
  const [tickets, setTickets] = useState([])
  const [meta, setMeta] = useState({})
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
    search: '',
    page: 1,
  })
  const [categories, setCategories] = useState([])
  const [showCreate, setShowCreate] = useState(false)
  const [loading, setLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [form, setForm] = useState({
    title: '',
    description: '',
    category_id: '',
    priority: 'medium',
  })

  const { user } = useAuth()

  const load = () => {
    setLoading(true)
    setError('')

    const params = {
      page: filters.page,
      page_size: 20,
    }

    if (filters.status) params.status = filters.status
    if (filters.priority) params.priority = filters.priority
    if (filters.search) params.search = filters.search

    api
      .get('/tickets', { params })
      .then((res) => {
        setTickets(res.data.data)
        setMeta(res.data.meta)
      })
      .catch(() => {
        setError('Unable to load tickets.')
      })
      .finally(() => {
        setLoading(false)
      })
  }

  useEffect(() => {
    load()

    api
      .get('/categories')
      .then((res) => setCategories(res.data.data))
      .catch(() => setCategories([]))
  }, [filters])

  const createTicket = async (e) => {
    e.preventDefault()
    setCreating(true)
    setError('')
    setSuccess('')

    try {
      await api.post('/tickets', {
        ...form,
        category_id: Number(form.category_id),
      })

      setShowCreate(false)

      setForm({
        title: '',
        description: '',
        category_id: '',
        priority: 'medium',
      })

      setSuccess('Ticket created successfully.')
      load()
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'Unable to create ticket. Please try again.'
      )
    } finally {
      setCreating(false)
    }
  }

  const updateFilter = (field, value) => {
    setFilters((current) => ({
      ...current,
      [field]: value,
      page: 1,
    }))
  }

  const clearFilters = () => {
    setFilters({
      status: '',
      priority: '',
      search: '',
      page: 1,
    })
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Support Tickets</h1>
          <p className="page-subtitle">
            View and manage support requests.
          </p>
        </div>

        {user?.role === 'customer' && (
          <button
            className="btn btn-primary"
            onClick={() => {
              setShowCreate(!showCreate)
              setError('')
              setSuccess('')
            }}
          >
            {showCreate ? 'Cancel' : '+ New Ticket'}
          </button>
        )}
      </div>

      {success && (
        <div className="alert alert-success">
          {success}
        </div>
      )}

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {showCreate && (
        <div className="card ticket-create-card">
          <div className="card-header">
            <h2 className="section-title">Create New Ticket</h2>
            <p className="section-description">
              Provide the details of your support request.
            </p>
          </div>

          <div className="card-body">
            <form onSubmit={createTicket}>
              <div className="form-group">
                <label className="form-label">Ticket Title</label>
                <input
                  className="form-control"
                  value={form.title}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      title: e.target.value,
                    })
                  }
                  placeholder="Example: Internet connection issue"
                  required
                  minLength={5}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Description</label>
                <textarea
                  className="form-control"
                  value={form.description}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      description: e.target.value,
                    })
                  }
                  placeholder="Describe the issue in detail..."
                  required
                  minLength={10}
                />
              </div>

              <div className="ticket-form-grid">
                <div className="form-group">
                  <label className="form-label">Category</label>

                  <select
                    className="form-control"
                    value={form.category_id}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        category_id: e.target.value,
                      })
                    }
                    required
                  >
                    <option value="">Select category</option>

                    {categories.map((category) => (
                      <option key={category.id} value={category.id}>
                        {category.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Priority</label>

                  <select
                    className="form-control"
                    value={form.priority}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        priority: e.target.value,
                      })
                    }
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
              </div>

              <div className="ticket-form-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowCreate(false)}
                >
                  Cancel
                </button>

                <button
                  className="btn btn-primary"
                  type="submit"
                  disabled={creating}
                >
                  {creating ? 'Creating...' : 'Create Ticket'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="card filters-card">
        <div className="filters-header">
          <div>
            <h2 className="section-title">Find Tickets</h2>
            <p className="section-description">
              Search and filter your support requests.
            </p>
          </div>

          {(filters.status ||
            filters.priority ||
            filters.search) && (
            <button
              className="btn btn-secondary"
              onClick={clearFilters}
            >
              Clear Filters
            </button>
          )}
        </div>

        <div className="ticket-filters">
          <div className="filter-field search-field">
            <label className="form-label">Search</label>
            <input
              className="form-control"
              placeholder="Search ticket number or title..."
              value={filters.search}
              onChange={(e) =>
                updateFilter('search', e.target.value)
              }
            />
          </div>

          <div className="filter-field">
            <label className="form-label">Status</label>
            <select
              className="form-control"
              value={filters.status}
              onChange={(e) =>
                updateFilter('status', e.target.value)
              }
            >
              <option value="">All Status</option>
              <option value="open">Open</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>
          </div>

          <div className="filter-field">
            <label className="form-label">Priority</label>
            <select
              className="form-control"
              value={filters.priority}
              onChange={(e) =>
                updateFilter('priority', e.target.value)
              }
            >
              <option value="">All Priority</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
        </div>
      </div>

      <div className="ticket-list-header">
        <div>
          <h2 className="section-title">Tickets</h2>
          <p className="section-description">
            {meta.total ?? tickets.length} ticket
            {(meta.total ?? tickets.length) === 1 ? '' : 's'} found
          </p>
        </div>
      </div>

      <div className="card ticket-table-card">
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>Ticket</th>
                <th>Title</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Created</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={5}>
                    <div className="empty-state">
                      <div className="empty-state-title">
                        Loading tickets
                      </div>
                      <p className="empty-state-text">
                        Please wait...
                      </p>
                    </div>
                  </td>
                </tr>
              ) : tickets.length === 0 ? (
                <tr>
                  <td colSpan={5}>
                    <div className="empty-state">
                      <div className="empty-state-title">
                        No tickets found
                      </div>
                      <p className="empty-state-text">
                        Try changing your filters or create a new ticket.
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                tickets.map((ticket) => (
                  <tr key={ticket.id}>
                    <td>
                      <Link
                        to={`/tickets/${ticket.id}`}
                        className="ticket-number"
                      >
                        {ticket.ticket_number}
                      </Link>
                    </td>

                    <td>
                      <Link
                        to={`/tickets/${ticket.id}`}
                        className="ticket-title-link"
                      >
                        {ticket.title}
                      </Link>
                    </td>

                    <td>
                      <span
                        className={`badge badge-${ticket.status}`}
                      >
                        {ticket.status.replace('_', ' ')}
                      </span>
                    </td>

                    <td>
                      <span
                        className={`badge badge-${ticket.priority}`}
                      >
                        {ticket.priority}
                      </span>
                    </td>

                    <td>
                      {new Date(
                        ticket.created_at
                      ).toLocaleDateString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {meta.total_pages > 1 && (
        <div className="pagination">
          <button
            className="btn btn-secondary"
            disabled={filters.page <= 1}
            onClick={() =>
              setFilters({
                ...filters,
                page: filters.page - 1,
              })
            }
          >
            ← Previous
          </button>

          <span className="pagination-info">
            Page {meta.page} of {meta.total_pages}
          </span>

          <button
            className="btn btn-secondary"
            disabled={filters.page >= meta.total_pages}
            onClick={() =>
              setFilters({
                ...filters,
                page: filters.page + 1,
              })
            }
          >
            Next →
          </button>
        </div>
      )}
    </div>
  )
}