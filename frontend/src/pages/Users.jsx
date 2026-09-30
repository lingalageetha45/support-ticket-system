
import { useEffect, useState } from 'react'
import api from '../services/api'

export default function Users() {
  const [users, setUsers] = useState([])
  const [meta, setMeta] = useState({})
  const [editingUser, setEditingUser] = useState(null)
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    role: 'customer',
  })
  const [loading, setLoading] = useState(false)
  const [actionUserId, setActionUserId] = useState(null)

  const loadUsers = () => {
    api.get('/users', { params: { page: 1, page_size: 50 } })
      .then((res) => {
        setUsers(res.data.data)
        setMeta(res.data.meta)
      })
      .catch(console.error)
  }

  useEffect(() => {
    loadUsers()
  }, [])

  const openEdit = (user) => {
    setEditingUser(user)
    setForm({
      full_name: user.full_name || '',
      email: user.email || '',
      role: user.role || 'customer',
    })
  }

  const closeEdit = () => {
    setEditingUser(null)
    setForm({
      full_name: '',
      email: '',
      role: 'customer',
    })
  }

  const handleSave = async (e) => {
    e.preventDefault()

    if (!editingUser) return

    setLoading(true)

    try {
      await api.patch(`/users/${editingUser.id}`, {
        full_name: form.full_name,
        email: form.email,
      })

      if (form.role !== editingUser.role) {
        await api.post(
          `/users/${editingUser.id}/change-role`,
          null,
          {
            params: { role: form.role },
          }
        )
      }

      closeEdit()
      loadUsers()
    } catch (error) {
      console.error(error)
      alert(
        error.response?.data?.message ||
        'Unable to update user'
      )
    } finally {
      setLoading(false)
    }
  }

  const handleStatusChange = async (user) => {
    setActionUserId(user.id)

    try {
      const action =
        user.status === 'active'
          ? 'deactivate'
          : 'activate'

      await api.post(`/users/${user.id}/${action}`)

      loadUsers()
    } catch (error) {
      console.error(error)
      alert(
        error.response?.data?.message ||
        `Unable to ${user.status === 'active' ? 'deactivate' : 'activate'} user`
      )
    } finally {
      setActionUserId(null)
    }
  }

  return (
    <div>
      <h1 style={{ marginBottom: '1.5rem' }}>
        User Management
      </h1>

      <div
        className="card"
        style={{ padding: 0, overflow: 'hidden' }}
      >
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>

          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.full_name}</td>

                <td>{u.email}</td>

                <td>
                  <span className="badge">
                    {u.role}
                  </span>
                </td>

                <td>
                  <span
                    className={`badge ${
                      u.status === 'active'
                        ? 'badge-resolved'
                        : 'badge-closed'
                    }`}
                  >
                    {u.status}
                  </span>
                </td>

                <td>
                  {new Date(
                    u.created_at
                  ).toLocaleDateString()}
                </td>

                <td>
                  <div
                    style={{
                      display: 'flex',
                      gap: '0.5rem',
                      alignItems: 'center',
                    }}
                  >
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => openEdit(u)}
                      style={{
                        padding: '0.35rem 0.7rem',
                        fontSize: '0.85rem',
                      }}
                    >
                      Edit
                    </button>

                    <button
                      type="button"
                      className="btn"
                      onClick={() => handleStatusChange(u)}
                      disabled={actionUserId === u.id}
                      style={{
                        padding: '0.35rem 0.7rem',
                        fontSize: '0.85rem',
                        background:
                          u.status === 'active'
                            ? '#fee2e2'
                            : '#dcfce7',
                        color:
                          u.status === 'active'
                            ? '#b91c1c'
                            : '#166534',
                        border: 'none',
                      }}
                    >
                      {actionUserId === u.id
                        ? 'Saving...'
                        : u.status === 'active'
                          ? 'Deactivate'
                          : 'Activate'}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {users.length === 0 && (
          <p style={{ padding: '1rem' }}>
            No users found.
          </p>
        )}
      </div>

      {meta?.total !== undefined && (
        <p
          style={{
            marginTop: '1rem',
            color: '#666',
            fontSize: '0.9rem',
          }}
        >
          Total users: {meta.total}
        </p>
      )}

      {editingUser && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.45)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '1rem',
          }}
        >
          <div
            className="card"
            style={{
              width: '100%',
              maxWidth: '450px',
              background: '#fff',
            }}
          >
            <h2 style={{ marginBottom: '1.5rem' }}>
              Edit User
            </h2>

            <form onSubmit={handleSave}>
              <div style={{ marginBottom: '1rem' }}>
                <label
                  style={{
                    display: 'block',
                    marginBottom: '0.4rem',
                    fontWeight: 600,
                  }}
                >
                  Full Name
                </label>

                <input
                  type="text"
                  value={form.full_name}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      full_name: e.target.value,
                    })
                  }
                  required
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label
                  style={{
                    display: 'block',
                    marginBottom: '0.4rem',
                    fontWeight: 600,
                  }}
                >
                  Email
                </label>

                <input
                  type="email"
                  value={form.email}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      email: e.target.value,
                    })
                  }
                  required
                />
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label
                  style={{
                    display: 'block',
                    marginBottom: '0.4rem',
                    fontWeight: 600,
                  }}
                >
                  Role
                </label>

                <select
                  value={form.role}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      role: e.target.value,
                    })
                  }
                >
                  <option value="customer">
                    Customer
                  </option>

                  <option value="agent">
                    Support Agent
                  </option>

                  <option value="admin">
                    Admin
                  </option>
                </select>
              </div>

              <div
                style={{
                  display: 'flex',
                  gap: '0.75rem',
                  justifyContent: 'flex-end',
                }}
              >
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={closeEdit}
                  disabled={loading}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={loading}
                >
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

