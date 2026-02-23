from app import db
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    name = db.Column(db.String(255), nullable=False)

    pm_name = db.Column(db.String(255), nullable=False)

    project_link = db.Column(db.Text, nullable=True)

    project_id = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True
    )

    # ==========================================
    # FOREIGN KEYS
    # ==========================================

    bank_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('banks.id', ondelete='SET NULL'),
        nullable=True  # Projects can exist without bank
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # ==========================================
    # RELATIONSHIPS
    # ==========================================
    
    # Optional: Project belongs to a bank
    bank = db.relationship(
        'Bank',
        back_populates='projects'
    )

    # Project owns its members
    # Xóa project → Xóa tất cả project members (liên kết)
    project_members = db.relationship(
        'ProjectMember',
        back_populates='project',
        cascade='all, delete-orphan'
    )

    # Project owns its tickets
    # Xóa project → Xóa tất cả tickets
    tickets = db.relationship(
        'Ticket',
        back_populates='project',
        cascade='all, delete-orphan'
    )

    # # Project owns its logwork records
    # # Xóa project → Xóa tất cả logwork của project
    # logworks = db.relationship(
    #     'Logwork',
    #     back_populates='project',
    #     cascade='all, delete-orphan'
    # )

    def __repr__(self):
        return f"<Project {self.name}>"