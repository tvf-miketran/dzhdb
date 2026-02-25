"""Add role_id to project_members table

Revision ID: add_role_to_members
Revises: remove_logdate_add_month
Create Date: 2026-02-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_role_to_members'
down_revision = 'remove_logdate_add_month'
branch_labels = None
depends_on = None


def upgrade():
    # Add role_id column to project_members table
    op.add_column('project_members', sa.Column(
        'role_id',
        postgresql.UUID(as_uuid=True),
        nullable=True
    ))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_project_members_role_id',
        'project_members',
        'roles',
        ['role_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    # Remove the foreign key constraint
    op.drop_constraint('fk_project_members_role_id', 'project_members', type_='foreignkey')
    
    # Remove the role_id column
    op.drop_column('project_members', 'role_id')
