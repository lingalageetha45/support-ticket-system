import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    AGENT = "agent"
    CUSTOMER = "customer"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationType(str, enum.Enum):
    TICKET_CREATED = "ticket_created"
    TICKET_ASSIGNED = "ticket_assigned"
    TICKET_REASSIGNED = "ticket_reassigned"
    TICKET_STATUS_CHANGED = "ticket_status_changed"
    NEW_COMMENT = "new_comment"
    TICKET_RESOLVED = "ticket_resolved"
    TICKET_CLOSED = "ticket_closed"
    SLA_BREACHED = "sla_breached"


STATUS_TRANSITIONS = {
    TicketStatus.OPEN: [TicketStatus.IN_PROGRESS],
    TicketStatus.IN_PROGRESS: [TicketStatus.RESOLVED],
    TicketStatus.RESOLVED: [
        TicketStatus.CLOSED,
        TicketStatus.OPEN,
    ],
    TicketStatus.CLOSED: [],
}


SLA_HOURS = {
    TicketPriority.LOW: 72,
    TicketPriority.MEDIUM: 48,
    TicketPriority.HIGH: 24,
    TicketPriority.CRITICAL: 4,
}