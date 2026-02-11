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
        backref='project_members'
    )

    def __repr__(self):
        return f"<ProjectMember {self.user_id} - {self.project_id}>"
