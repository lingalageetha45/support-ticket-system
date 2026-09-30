"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-09-21
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("role", sa.Enum("admin", "agent", "customer", name="userrole"), nullable=False),
        sa.Column("status", sa.Enum("active", "inactive", name="userstatus"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_status", "users", ["status"])

    op.create_table(
        "ticket_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ticket_categories_id", "ticket_categories", ["id"])
    op.create_index("ix_ticket_categories_name", "ticket_categories", ["name"], unique=True)
    op.create_index("ix_ticket_categories_is_active", "ticket_categories", ["is_active"])

    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_number", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.Enum("open", "in_progress", "resolved", "closed", name="ticketstatus"), nullable=False),
        sa.Column("priority", sa.Enum("low", "medium", "high", "critical", name="ticketpriority"), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("assigned_agent_id", sa.Integer(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assigned_agent_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["ticket_categories.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tickets_ticket_number", "tickets", ["ticket_number"], unique=True)
    op.create_index("ix_tickets_status", "tickets", ["status"])
    op.create_index("ix_tickets_priority", "tickets", ["priority"])
    op.create_index("ix_tickets_customer_id", "tickets", ["customer_id"])
    op.create_index("ix_tickets_assigned_agent_id", "tickets", ["assigned_agent_id"])
    op.create_index("ix_tickets_category_id", "tickets", ["category_id"])
    op.create_index("ix_tickets_due_date", "tickets", ["due_date"])
    op.create_index("ix_tickets_created_at", "tickets", ["created_at"])

    op.create_table(
        "ticket_comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_internal", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ticket_comments_ticket_id", "ticket_comments", ["ticket_id"])
    op.create_index("ix_ticket_comments_user_id", "ticket_comments", ["user_id"])

    op.create_table(
        "ticket_attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("uploaded_by_id", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=100), nullable=False),
        sa.Column("mime_type", sa.String(length=150), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ticket_attachments_ticket_id", "ticket_attachments", ["ticket_id"])

    op.create_table(
        "ticket_status_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("old_status", sa.Enum("open", "in_progress", "resolved", "closed", name="ticketstatus", create_type=False), nullable=True),
        sa.Column("new_status", sa.Enum("open", "in_progress", "resolved", "closed", name="ticketstatus", create_type=False), nullable=False),
        sa.Column("changed_by_id", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["changed_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ticket_status_history_ticket_id", "ticket_status_history", ["ticket_id"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=True),
        sa.Column("type", sa.Enum("ticket_created", "ticket_assigned", "ticket_reassigned", "ticket_status_changed", "new_comment", "ticket_resolved", "ticket_closed", "sla_breached", name="notificationtype"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=500), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_refresh_tokens_token", "refresh_tokens", ["token"], unique=True)


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_table("audit_logs")
    op.drop_table("notifications")
    op.drop_table("ticket_status_history")
    op.drop_table("ticket_attachments")
    op.drop_table("ticket_comments")
    op.drop_table("tickets")
    op.drop_table("ticket_categories")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS notificationtype")
    op.execute("DROP TYPE IF EXISTS ticketpriority")
    op.execute("DROP TYPE IF EXISTS ticketstatus")
    op.execute("DROP TYPE IF EXISTS userstatus")
    op.execute("DROP TYPE IF EXISTS userrole")
