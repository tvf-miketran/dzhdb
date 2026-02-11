from app import db
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


class Bank(db.Model):
    __tablename__ = "banks"

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    name = db.Column(db.String(255), nullable=False, unique=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # ==========================================
    # RELATIONSHIPS
    # ==========================================
   
    # Weak ownership - Projects can exist without bank
    projects = db.relationship(
        'Project',
        back_populates='bank'
    )

    def __repr__(self):
        return f"<Bank {self.name}>"