from app import db
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    role_id = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True
    )

    name = db.Column(db.String(255), nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Note: tickets relationship removed - using role_ids array in Ticket instead
    # Roles can be accessed through Ticket.role_ids

    def __repr__(self):
        return f"<Role {self.name}>"