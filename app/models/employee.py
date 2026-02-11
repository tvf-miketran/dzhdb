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

    vn_full_name = db.Column(db.String(255), nullable=False)
    
    en_full_name = db.Column(db.String(255), nullable=False)

    employeeId = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True
    )

    description = db.Column(db.Text, nullable=True)

    email = db.Column(db.String(255), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)

    authorize_role = db.Column(
        db.Enum(
            "MEMBER",
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

    # ==========================================
    # RELATIONSHIPS
    # ==========================================
    
    # Employee owns their project memberships
    # Xóa employee → Xóa tất cả project memberships
    project_members = db.relationship(
        'ProjectMember',
        back_populates='employee',
        cascade='all, delete-orphan'
    )

    # Weak relationship: Employee assigned to tickets
    # Xóa employee → Tickets vẫn còn, chỉ mất assignment (user_id = NULL)
    tickets = db.relationship(
        'Ticket',
        back_populates='employee'
        # No cascade delete - tickets exist independently
    )

    # Employee owns their logwork records
    # Xóa employee → Xóa tất cả logwork của employee đó
    logworks = db.relationship(
        'Logwork',
        back_populates='employee',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f"<Employee {self.en_full_name}>"