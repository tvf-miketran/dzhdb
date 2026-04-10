"""revert logworks project_ids array to single project_id

Revision ID: b1f4d2a7c9e1
Revises: 8e5b3a1c9f0d
Create Date: 2026-04-10 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers, used by Alembic.
revision = 'b1f4d2a7c9e1'
down_revision = '8e5b3a1c9f0d'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

    with op.batch_alter_table('logworks', schema=None) as batch_op:
        batch_op.drop_constraint('uq_logworks_user_month_year', type_='unique')

    op.drop_index('ix_logworks_project_ids', table_name='logworks')

    with op.batch_alter_table('logworks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('project_id', sa.UUID(), nullable=True))

    select_rows_sql = sa.text("""
        SELECT id, user_id, project_ids, loghours, month, year, created_at, updated_at
        FROM logworks
    """)
    rows = bind.execute(select_rows_sql).mappings().all()

    expanded_rows = []
    for row in rows:
        project_ids = list(row.get('project_ids') or [])

        # Safety fallback for rows that somehow have empty project_ids.
        if not project_ids:
            fallback_pid = bind.execute(
                sa.text(
                    """
                    SELECT pm.project_id
                    FROM project_members pm
                    WHERE pm.user_id = :user_id
                    ORDER BY pm.created_at ASC NULLS LAST
                    LIMIT 1
                    """
                ),
                {"user_id": row['user_id']},
            ).scalar()
            if fallback_pid:
                project_ids = [fallback_pid]

        if not project_ids:
            expanded_rows.append(
                {
                    'id': row['id'],
                    'user_id': row['user_id'],
                    'project_id': None,
                    'loghours': row['loghours'],
                    'month': row['month'],
                    'year': row['year'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                }
            )
            continue

        for idx, pid in enumerate(project_ids):
            expanded_rows.append(
                {
                    'id': row['id'] if idx == 0 else uuid.uuid4(),
                    'user_id': row['user_id'],
                    'project_id': pid,
                    'loghours': row['loghours'],
                    'month': row['month'],
                    'year': row['year'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                }
            )

    bind.execute(sa.text('DELETE FROM logworks'))

    if expanded_rows:
        op.bulk_insert(
            sa.table(
                'logworks',
                sa.column('id', postgresql.UUID(as_uuid=True)),
                sa.column('user_id', postgresql.UUID(as_uuid=True)),
                sa.column('project_id', postgresql.UUID(as_uuid=True)),
                sa.column('loghours', sa.Numeric(10, 2)),
                sa.column('month', sa.String(length=2)),
                sa.column('year', sa.String(length=4)),
                sa.column('created_at', sa.DateTime(timezone=True)),
                sa.column('updated_at', sa.DateTime(timezone=True)),
            ),
            expanded_rows,
        )

    with op.batch_alter_table('logworks', schema=None) as batch_op:
        batch_op.drop_column('project_ids')

    with op.batch_alter_table('logworks', schema=None) as batch_op:
        batch_op.create_index('ix_logworks_project_id', ['project_id'], unique=False)
        batch_op.create_unique_constraint(
            'uq_logworks_user_project_month_year',
            ['user_id', 'project_id', 'month', 'year'],
        )
        batch_op.create_foreign_key(
            'logworks_project_id_fkey',
            'projects',
            ['project_id'],
            ['id'],
            ondelete='CASCADE',
        )


def downgrade():
    with op.batch_alter_table('logworks', schema=None) as batch_op:
        batch_op.drop_constraint('logworks_project_id_fkey', type_='foreignkey')
        batch_op.drop_constraint('uq_logworks_user_project_month_year', type_='unique')
        batch_op.drop_index('ix_logworks_project_id')

    with op.batch_alter_table('logworks', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'project_ids',
                postgresql.ARRAY(sa.UUID()),
                nullable=True,
                server_default='{}',
            )
        )

    op.execute("""
        UPDATE logworks
        SET project_ids = CASE
            WHEN project_id IS NULL THEN '{}'::uuid[]
            ELSE ARRAY[project_id]::uuid[]
        END
    """)

    with op.batch_alter_table('logworks', schema=None) as batch_op:
        batch_op.drop_column('project_id')

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
