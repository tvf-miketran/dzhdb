from app import db
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


class Logwork(db.Model):
    __tablename__ = "logworks"

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('employees.id', ondelete='CASCADE'),
        nullable=False
    )

    project_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('projects.id', ondelete='CASCADE'),
        nullable=True,
        index=True,
    )

    loghours = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    month = db.Column(
        db.String(2),
        nullable=False,
        index=True
    )

    year = db.Column(
        db.String(4),
        nullable=False,
        index=True,
        default='2026'
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

    # Relationships
    employee = db.relationship(
        'Employee',
        back_populates='logworks'
    )

    project = db.relationship(
        'Project',
        back_populates='logworks'
    )

    def __repr__(self):
        return f"<Logwork {self.id} - {self.loghours}h in Month {self.month} Project {self.project_id}>"