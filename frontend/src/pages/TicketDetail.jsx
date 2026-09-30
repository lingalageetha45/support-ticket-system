
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'

export default function TicketDetail() {
  const { id } = useParams()

  const [ticket, setTicket] = useState(null)
  const [comments, setComments] = useState([])
  const [newComment, setNewComment] = useState('')
  const [status, setStatus] = useState('')
  const [posting, setPosting] = useState(false)
  const [commentMessage, setCommentMessage] = useState('')
  const [commentError, setCommentError] = useState('')

  const { isAgent } = useAuth()

  const load = async () => {
    try {
      const ticketResponse = await api.get(`/tickets/${id}`)

      setTicket(ticketResponse.data.data)
      setStatus(ticketResponse.data.data.status)

      const commentsResponse = await api.get(
        `/tickets/${id}/comments`
      )

      setComments(commentsResponse.data.data)
    } catch (error) {
      console.error('Unable to load ticket:', error)
    }
  }

  useEffect(() => {
    load()
  }, [id])

  const addComment = async (e) => {
    e.preventDefault()

    const message = newComment.trim()

    if (!message) {
      setCommentError('Please enter a comment.')
      return
    }

    setPosting(true)
    setCommentMessage('')
    setCommentError('')

    try {
      await api.post(`/tickets/${id}/comments`, {
        message,
      })

      setNewComment('')
      setCommentMessage('Comment posted successfully.')

      await load()
    } catch (error) {
      console.error('Unable to post comment:', error)

      const responseData = error.response?.data

      setCommentError(
        responseData?.message ||
        responseData?.detail ||
        (typeof responseData === 'string'
          ? responseData
          : responseData
            ? JSON.stringify(responseData)
            : '') ||
        'Unable to post comment.'
      )
    } finally {
      setPosting(false)
    }
  }

  const changeStatus = async () => {
    try {
      await api.post(`/tickets/${id}/status`, {
        status,
      })

      setCommentMessage('')
      setCommentError('')

      await load()
    } catch (error) {
      console.error('Unable to update status:', error)

      alert(
        error.response?.data?.message ||
        error.response?.data?.detail ||
        'Unable to update ticket status.'
      )
    }
  }

  if (!ticket) {
    return <p>Loading...</p>
  }

  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: '1.5rem',
        }}
      >
        <div>
          <h1>{ticket.title}</h1>

          <p
            style={{
              color: '#6b7280',
              marginTop: '0.25rem',
            }}
          >
            {ticket.ticket_number}
          </p>
        </div>

        <div
          style={{
            display: 'flex',
            gap: '0.5rem',
          }}
        >
          <span className={`badge badge-${ticket.status}`}>
            {ticket.status.replace('_', ' ')}
          </span>

          <span className={`badge badge-${ticket.priority}`}>
            {ticket.priority}
          </span>
        </div>
      </div>

      <div
        className="card"
        style={{
          marginBottom: '1.5rem',
        }}
      >
        <p style={{ whiteSpace: 'pre-wrap' }}>
          {ticket.description}
        </p>

        <div
          style={{
            marginTop: '1rem',
            fontSize: '0.875rem',
            color: '#6b7280',
          }}
        >
          Created:{' '}
          {new Date(ticket.created_at).toLocaleString()}

          {ticket.due_date && (
            <>
              {' '}
              · Due:{' '}
              {new Date(ticket.due_date).toLocaleString()}
            </>
          )}
        </div>
      </div>

      {isAgent && (
        <div
          className="card"
          style={{
            marginBottom: '1.5rem',
          }}
        >
          <h3 style={{ marginBottom: '0.75rem' }}>
            Update Status
          </h3>

          <div
            style={{
              display: 'flex',
              gap: '0.75rem',
            }}
          >
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="open">Open</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>

            <button
              className="btn btn-primary"
              onClick={changeStatus}
            >
              Update
            </button>
          </div>
        </div>
      )}

      <div className="card">
        <h3 style={{ marginBottom: '1rem' }}>
          Comments
        </h3>

        {comments.length === 0 && (
          <p style={{ color: '#6b7280' }}>
            No comments yet.
          </p>
        )}

        {comments.map((c) => (
          <div
            key={c.id}
            style={{
              padding: '0.75rem 0',
              borderBottom: '1px solid #e5e7eb',
            }}
          >
            <div style={{ fontWeight: 500 }}>
              {c.user?.full_name || 'User'}

              {c.is_internal && (
                <span
                  className="badge"
                  style={{
                    marginLeft: '0.5rem',
                  }}
                >
                  internal
                </span>
              )}
            </div>

            <p
              style={{
                marginTop: '0.25rem',
                whiteSpace: 'pre-wrap',
              }}
            >
              {c.message}
            </p>

            <div
              style={{
                fontSize: '0.75rem',
                color: '#6b7280',
                marginTop: '0.25rem',
              }}
            >
              {new Date(c.created_at).toLocaleString()}
            </div>
          </div>
        ))}

        {commentMessage && (
          <div
            style={{
              marginTop: '1rem',
              padding: '0.75rem',
              background: '#dcfce7',
              color: '#166534',
              borderRadius: '6px',
            }}
          >
            {commentMessage}
          </div>
        )}

        {commentError && (
          <div
            style={{
              marginTop: '1rem',
              padding: '0.75rem',
              background: '#fee2e2',
              color: '#b91c1c',
              borderRadius: '6px',
              whiteSpace: 'pre-wrap',
            }}
          >
            {commentError}
          </div>
        )}

        {ticket.status !== 'closed' && (
          <form
            onSubmit={addComment}
            style={{ marginTop: '1rem' }}
          >
            <div className="form-group">
              <textarea
                rows={3}
                value={newComment}
                onChange={(e) => {
                  setNewComment(e.target.value)
                  setCommentMessage('')
                  setCommentError('')
                }}
                placeholder="Add a comment..."
                required
              />
            </div>

            <button
              className="btn btn-primary"
              type="submit"
              disabled={posting}
            >
              {posting ? 'Posting...' : 'Post Comment'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
