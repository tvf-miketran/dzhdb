from app import db
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    full_name = db.Column(db.String(255), nullable=False)

    employeeId = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True
    )

    password = db.Column(db.String(255), nullable=False)

    role = db.Column(
        db.Enum(
            "MEMBER",
            "ODC_LEAD",
            "ADMIN",
            name="employee_role"
        ),
        nullable=False,
        default="MEMBER"
    )

    status = db.Column(
        db.Boolean,
        nullable=False,
        default=True  # True = ACTIVE, False = INACTIVE
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