from app import db
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    ticket_id = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True
    )

    ticket_link = db.Column(db.Text, nullable=True)

    # ==========================================
    # FOREIGN KEYS (FIXED)
    # ==========================================
    
    # Ticket belongs to Project (STRONG - required)
    # Xóa project → Xóa ticket
    project_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('projects.id', ondelete='CASCADE'),
        nullable=False
    )

    # Xóa role → Ticket vẫn còn, role_id = NULL
    role_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('roles.id', ondelete='SET NULL'),
        nullable=True
    )

    # Xóa employee → Ticket vẫn còn, employee_id = NULL
    employee_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('employees.id', ondelete='SET NULL'),
        nullable=True
    )

    ticket_type_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('ticket_types.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )

    ticket_status_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('ticket_statuses.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # ==========================================
    # RELATIONSHIPS (FIXED)
    # ==========================================
    
    # Ticket belongs to a project
    project = db.relationship(
        'Project',
        back_populates='tickets'
    )

    # Ticket has optional role
    role = db.relationship(
        'Role',
        back_populates='tickets'
    )

    # Ticket has optional assignee (employee)
    employee = db.relationship(
        'Employee',
        back_populates='tickets'
    )

    ticket_type = db.relationship(
        'TicketType',
        back_populates='tickets'
    )

    ticket_status = db.relationship(
        'TicketStatus',
        back_populates='tickets'
    )

    def __repr__(self):
        return f"<Ticket {self.ticket_id}>"