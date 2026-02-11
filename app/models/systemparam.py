from app import db
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


class SystemParameter(db.Model):
    __tablename__ = "system_parameters"

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    param_key = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True
    )

    param_value = db.Column(
        db.Text,
        nullable=False
    )

    description = db.Column(db.Text, nullable=True)

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

    def __repr__(self):
        return f"<SystemParameter {self.param_key}: {self.param_value}>"