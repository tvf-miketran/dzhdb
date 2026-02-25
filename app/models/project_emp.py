from app import db
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


class ProjectMember(db.Model):
    __tablename__ = "project_members"

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
        nullable=False
    )

    role_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('roles.id', ondelete='SET NULL'),
        nullable=True
    )

    #Esimated Effort in percentage
    allocation_percent = db.Column(db.Integer, nullable=False)

    joined_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        nullable=True
    )

    # Relationships
    project = db.relationship(
        'Project',
        back_populates='project_members'
    )

    employee = db.relationship(
        'Employee',
        back_populates='project_members'
    )

    role = db.relationship(
        'Role',
        backref='project_members',
        foreign_keys=[role_id]
    )

    def __repr__(self):
        return f"<ProjectMember {self.user_id} - {self.project_id}>"
