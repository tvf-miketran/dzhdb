"""add role manager

Revision ID: aa88fb4d3022
Revises: drop_ticket_id_unique_index
Create Date: 2026-03-19 10:53:20.376244

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'aa88fb4d3022'
down_revision = 'drop_ticket_id_unique_index'
branch_labels = None
depends_on = None


def upgrade():
    # Add MANAGER to employee authorization enum.
    op.execute("ALTER TYPE employee_role ADD VALUE IF NOT EXISTS 'MANAGER'")


def downgrade():
    # PostgreSQL doesn't support removing enum values directly.
    # Recreate enum without MANAGER and map existing MANAGER rows to MEMBER.
    old_role = sa.Enum('MEMBER', 'ADMIN', name='employee_role_old')
    new_role = sa.Enum('MEMBER', 'ADMIN', name='employee_role')

    op.execute("UPDATE employees SET authorize_role = 'MEMBER' WHERE authorize_role = 'MANAGER'")

    old_role.create(op.get_bind(), checkfirst=False)
    op.execute(
        "ALTER TABLE employees ALTER COLUMN authorize_role TYPE employee_role_old "
        "USING authorize_role::text::employee_role_old"
    )
    op.execute("DROP TYPE employee_role")
    new_role.create(op.get_bind(), checkfirst=False)
    op.execute(
        "ALTER TABLE employees ALTER COLUMN authorize_role TYPE employee_role "
        "USING authorize_role::text::employee_role"
    )
    op.execute("DROP TYPE employee_role_old")
