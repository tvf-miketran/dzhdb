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

    loghours = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    log_date = db.Column(
        db.Date,
        nullable=False,
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

    # Relationships
    # project = db.relationship(
    #     'Project',
    #     backref='logworks'
    # )

    employee = db.relationship(
        'Employee',
        back_populates='logworks'
    )

    def __repr__(self):
        return f"<Logwork {self.id} - {self.loghours}h on {self.log_date}>"