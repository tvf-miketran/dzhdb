"""merge_heads

Revision ID: 45506c0634b6
Revises: add_role_to_members, add_year_to_logwork
Create Date: 2026-02-25 07:37:13.106472

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '45506c0634b6'
down_revision = ('add_role_to_members', 'add_year_to_logwork')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
