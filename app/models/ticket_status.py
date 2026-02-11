from app import db
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


class TicketStatus(db.Model):
    __tablename__ = "ticket_statuses"

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    status_id = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True
    )

    name = db.Column(db.String(255), nullable=False)

    # ==========================================
    # RELATIONSHIPS
    # ==========================================
    
    # Weak relationship: Tickets can have a ticket type
    tickets = db.relationship(
        'Ticket',
        back_populates='ticket_statuses'
    )

    def __repr__(self):
        return f"<TicketStatus {self.status_id}: {self.name}>"