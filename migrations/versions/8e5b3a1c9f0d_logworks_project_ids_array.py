"""logworks replace project_id FK with project_ids UUID array

Revision ID: 8e5b3a1c9f0d
Revises: 7d2f8f10c2ab
Create Date: 2026-04-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '8e5b3a1c9f0d'
down_revision = '7d2f8f10c2ab'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Drop old FK, unique constraint, index, and single project_id column
    with op.batch_alter_table('logworks', schema=None) as batch_op:
        batch_op.drop_constraint('logworks_project_id_fkey', type_='foreignkey')
        batch_op.drop_constraint('uq_logworks_user_project_month_year', type_='unique')
        batch_op.drop_index('ix_logworks_project_id')
        batch_op.drop_column('project_id')

    # 2. Add project_ids UUID[] column (nullable, no constraint yet)
    with op.batch_alter_table('logworks', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'project_ids',
                postgresql.ARRAY(sa.UUID()),
                nullable=True,
                server_default='{}',
            )
        )

    # 3. Backfill project_ids from project_members for every row
    op.execute("""
        UPDATE logworks l
        SET project_ids = COALESCE(
            (
                SELECT ARRAY_AGG(DISTINCT pm.project_id ORDER BY pm.project_id)
                FROM project_members pm
                WHERE pm.user_id = l.user_id
            ),
            '{}'::uuid[]
        )
    """)

    # 4. Deduplicate rows so only one row per (user_id, month, year) remains.
    #    Keep the row with the lowest id; sum loghours across duplicates.
    op.execute("""
        UPDATE logworks l
        SET loghours = sub.total_hours
        FROM (
            SELECT
                MIN(id::text)::uuid AS keep_id,
                user_id,
                month,
                year,
                SUM(loghours) AS total_hours
            FROM logworks
            GROUP BY user_id, month, year
            HAVING COUNT(*) > 1
        ) sub
        WHERE l.id = sub.keep_id
    """)

    op.execute("""
        DELETE FROM logworks l
        WHERE l.id::text NOT IN (
            SELECT MIN(id::text)
            FROM logworks
            GROUP BY user_id, month, year
        )
    """)

    # 5. Now safe to add unique constraint and GIN index
    with op.batch_alter_table('logworks', schema=None) as batch_op:
        batch_op.create_unique_constraint(
            'uq_logworks_user_month_year',
            ['user_id', 'month', 'year'],
        )

    op.create_index(
        'ix_logworks_project_ids',
        'logworks',
        ['project_ids'],
        postgresql_using='gin',
    )


def downgrade():
    op.drop_index('ix_logworks_project_ids', table_name='logworks')

    with op.batch_alter_table('logworks', schema=None) as batch_op:
        batch_op.drop_constraint('uq_logworks_user_month_year', type_='unique')
        batch_op.drop_column('project_ids')

    with op.batch_alter_table('logworks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('project_id', sa.UUID(), nullable=True))
        batch_op.create_index(
            batch_op.f('ix_logworks_project_id'), ['project_id'], unique=False
        )
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
