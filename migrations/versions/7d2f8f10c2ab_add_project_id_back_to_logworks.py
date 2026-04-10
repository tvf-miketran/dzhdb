"""add project_id back to logworks

Revision ID: 7d2f8f10c2ab
Revises: e3c9a1f4b2d7
Create Date: 2026-04-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7d2f8f10c2ab'
down_revision = 'e3c9a1f4b2d7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('logworks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('project_id', sa.UUID(), nullable=True))
        batch_op.create_index(batch_op.f('ix_logworks_project_id'), ['project_id'], unique=False)
        batch_op.create_unique_constraint(
            'uq_logworks_user_project_month_year',
            ['user_id', 'project_id', 'month', 'year'],
        )
        batch_op.create_foreign_key(
            batch_op.f('logworks_project_id_fkey'),
            'projects',
            ['project_id'],
            ['id'],
            ondelete='CASCADE',
        )


def downgrade():
    with op.batch_alter_table('logworks', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('logworks_project_id_fkey'), type_='foreignkey')
        batch_op.drop_constraint('uq_logworks_user_project_month_year', type_='unique')
        batch_op.drop_index(batch_op.f('ix_logworks_project_id'))
        batch_op.drop_column('project_id')