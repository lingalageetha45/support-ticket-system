# Entity Relationship Diagram

```
┌─────────────┐       ┌──────────────────┐       ┌─────────────────┐
│    users    │       │ ticket_categories│       │    tickets      │
├─────────────┤       ├──────────────────┤       ├─────────────────┤
│ id (PK)     │◄──┐   │ id (PK)          │◄──────│ id (PK)         │
│ email (UQ)  │   │   │ name (UQ)        │       │ ticket_number   │
│ full_name   │   │   │ description      │       │ title           │
│ role        │   │   │ is_active        │       │ description     │
│ status      │   │   │ created_at       │       │ status          │
│ is_active   │   │   │ updated_at       │       │ priority        │
│ created_at  │   │   └──────────────────┘       │ customer_id (FK)│──┐
│ updated_at  │   │                              │ assigned_agent  │──┤
└─────────────┘   │                              │ category_id (FK)│  │
      ▲           │                              │ due_date        │  │
      │           │                              │ created_at      │  │
      │           │                              │ resolved_at     │  │
      │           │                              │ closed_at       │  │
      │           │                              └─────────────────┘  │
      │           │                                       │           │
      │           │              ┌────────────────────────┤           │
      │           │              ▼                        ▼           │
      │           │   ┌──────────────────┐    ┌────────────────────┐  │
      │           │   │ ticket_comments  │    │ ticket_attachments │  │
      │           │   ├──────────────────┤    ├────────────────────┤  │
      │           └───│ user_id (FK)     │    │ uploaded_by_id(FK) │──┘
      │               │ ticket_id (FK)   │    │ ticket_id (FK)     │
      │               │ message          │    │ file_name          │
      │               │ is_internal      │    │ original_name      │
      │               │ created_at       │    │ mime_type          │
      │               └──────────────────┘    │ file_size          │
      │                                       │ storage_path       │
      │                                       └────────────────────┘
      │
      │   ┌──────────────────┐   ┌─────────────────┐   ┌──────────────┐
      ├───│  notifications   │   │   audit_logs    │   │refresh_tokens│
      │   ├──────────────────┤   ├─────────────────┤   ├──────────────┤
      │   │ user_id (FK)     │   │ user_id (FK)    │   │ user_id (FK) │
      │   │ ticket_id (FK)   │   │ action          │   │ token (UQ)   │
      │   │ type             │   │ entity          │   │ expires_at   │
      │   │ title, message   │   │ entity_id       │   │ is_revoked   │
      │   │ is_read          │   │ ip_address      │   └──────────────┘
      │   └──────────────────┘   │ metadata        │
      │                          └─────────────────┘
      │
      └────── ticket_status_history (ticket_id, changed_by_id, old/new status)
```

## Key Relationships

- User 1──* Ticket (as customer)
- User 1──* Ticket (as assigned agent)
- TicketCategory 1──* Ticket
- Ticket 1──* TicketComment
- Ticket 1──* TicketAttachment
- Ticket 1──* TicketStatusHistory
- User 1──* Notification
- User 1──* AuditLog
- User 1──* RefreshToken
