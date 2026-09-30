"""Seed initial data: admin, agent, categories."""
from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User
from app.models.category import TicketCategory
from app.models.enums import UserRole, UserStatus


def seed():
    db = SessionLocal()
    try:
        # Admin
        if not db.query(User).filter(User.email == "admin@support.com").first():
            admin = User(
                email="admin@support.com",
                full_name="System Admin",
                hashed_password=get_password_hash("Admin@12345"),
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                is_active=True,
            )
            db.add(admin)
            print("Created admin@support.com / Admin@12345")

        # Agent
        if not db.query(User).filter(User.email == "agent@support.com").first():
            agent = User(
                email="agent@support.com",
                full_name="Support Agent",
                hashed_password=get_password_hash("Agent@12345"),
                role=UserRole.AGENT,
                status=UserStatus.ACTIVE,
                is_active=True,
            )
            db.add(agent)
            print("Created agent@support.com / Agent@12345")

        # Customer
        if not db.query(User).filter(User.email == "customer@example.com").first():
            customer = User(
                email="customer@example.com",
                full_name="Demo Customer",
                hashed_password=get_password_hash("Customer@12345"),
                role=UserRole.CUSTOMER,
                status=UserStatus.ACTIVE,
                is_active=True,
            )
            db.add(customer)
            print("Created customer@example.com / Customer@12345")

        categories = [
            ("Technical Support", "Technical issues and troubleshooting"),
            ("Billing", "Billing and payment related queries"),
            ("Account", "Account management and access issues"),
            ("Product Issue", "Product bugs and feature requests"),
            ("General", "General inquiries"),
        ]
        for name, desc in categories:
            if not db.query(TicketCategory).filter(TicketCategory.name == name).first():
                db.add(TicketCategory(name=name, description=desc, is_active=True))
                print(f"Created category: {name}")

        db.commit()
        print("Seed completed successfully.")
    except Exception as e:
        db.rollback()
        print(f"Seed error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
