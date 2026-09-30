# Support Ticket Management System

Complete full-stack Support Ticket Management System with **FastAPI** backend and **React** frontend.

## Features

### Authentication & Authorization
- JWT access + refresh tokens
- Password hashing (bcrypt)
- Role-based access: **Admin**, **Support Agent**, **Customer**
- Inactive users cannot authenticate
- Protected APIs with resource-level checks

### User Management (Admin)
- Create / list / get / update users
- Activate / deactivate users
- Change roles
- Unique emails enforced

### Ticket Management
- Create, list (pagination, search, sort, filter), get, update, assign, delete
- Status workflow: `Open → In Progress → Resolved → Closed` (with reopen support)
- Invalid transitions rejected
- SLA due dates by priority (Critical 4h, High 24h, Medium 48h, Low 72h)
- Overdue detection
- Assignment rules (inactive agents blocked, customers cannot assign)

### Comments & Attachments
- Add / list / edit own / delete own comments
- Admin moderation
- Closed tickets cannot receive comments until reopened
- File upload with MIME + extension + size validation

### Categories, Notifications, Dashboard, Audit
- Category CRUD + activate/deactivate
- Notifications for key events
- Role-aware dashboard statistics
- Immutable audit logs for critical actions

## Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Backend    | FastAPI, SQLAlchemy 2, Alembic, Pydantic |
| Database   | PostgreSQL 16                       |
| Auth       | JWT (python-jose), passlib/bcrypt   |
| Frontend   | React 18, Vite, React Router, Axios |
| Deploy     | Docker + Docker Compose             |

## Quick Start (Docker)

```bash
cd support-ticket-system
docker compose up --build
```

- **Frontend**: http://localhost:3000  
- **API Docs (Swagger)**: http://localhost:8000/docs  
- **ReDoc**: http://localhost:8000/redoc  
- **Health**: http://localhost:8000/health  

### Demo Accounts

| Role     | Email                  | Password       |
|----------|------------------------|----------------|
| Admin    | admin@support.com      | Admin@12345    |
| Agent    | agent@support.com      | Agent@12345    |
| Customer | customer@example.com   | Customer@12345 |

## Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Start PostgreSQL and update DATABASE_URL in .env
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
support-ticket-system/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Routes
│   │   ├── core/            # Config, security, database, exceptions
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── repositories/    # Data access
│   │   ├── services/        # Business logic (extendable)
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   ├── uploads/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── context/
│   │   └── services/
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.md
```

## API Overview

| Method | Endpoint                          | Description                | Roles          |
|--------|-----------------------------------|----------------------------|----------------|
| POST   | /api/v1/auth/register             | Register customer          | Public         |
| POST   | /api/v1/auth/login                | Login                      | Public         |
| POST   | /api/v1/auth/refresh              | Refresh tokens             | Public         |
| POST   | /api/v1/auth/logout               | Logout                     | Auth           |
| GET    | /api/v1/auth/me                   | Current user               | Auth           |
| POST   | /api/v1/auth/change-password      | Change password            | Auth           |
| *      | /api/v1/users/*                   | User management            | Admin          |
| *      | /api/v1/categories/*              | Categories                 | Admin / All    |
| *      | /api/v1/tickets/*                 | Ticket CRUD + assign/status| Role-scoped    |
| *      | /api/v1/tickets/{id}/comments/*   | Comments                   | Role-scoped    |
| *      | /api/v1/tickets/{id}/attachments/*| Attachments                | Role-scoped    |
| *      | /api/v1/notifications/*           | Notifications              | Auth           |
| GET    | /api/v1/dashboard/stats           | Dashboard stats            | Auth           |
| GET    | /api/v1/audit                     | Audit logs                 | Admin          |

## Business Rules Enforced

- Only authenticated users access protected APIs
- Inactive users cannot log in
- Customers see only their own tickets
- Agents see assigned + unassigned tickets
- Admins manage everything
- Inactive agents cannot receive tickets
- Invalid status transitions rejected
- Closed tickets cannot be modified (except reopen)
- Users can only edit/delete their own comments (admins can moderate)
- Invalid attachments rejected (MIME, extension, size)
- Duplicate emails blocked
- Inactive categories blocked for new tickets
- SLA calculated consistently from priority
- Critical actions audited with IP and metadata

## Testing

```bash
cd backend
pytest tests/ -v --cov=app
```

## Environment Variables

See `backend/.env.example`.

## License

MIT
