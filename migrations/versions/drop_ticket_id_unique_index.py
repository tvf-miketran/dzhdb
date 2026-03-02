"""Drop unique index on ticket_id to allow duplicates

Revision ID: drop_ticket_id_unique_index
Revises: change_role_id_to_array
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'drop_ticket_id_unique_index'
down_revision = 'change_role_id_to_array'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the unique index on ticket_id to allow duplicate ticket_ids
    op.execute("""
        DROP INDEX IF EXISTS ix_tickets_ticket_id
    """)
    
    # Also ensure the unique constraint is removed (if exists)
    op.execute("""
        ALTER TABLE tickets 
        DROP CONSTRAINT IF EXISTS tickets_ticket_id_key
    """)


def downgrade():
    # Recreate the unique index
    op.execute("CREATE UNIQUE INDEX ix_tickets_ticket_id ON tickets (ticket_id)")
    
    # Recreate the unique constraint
    op.execute("ALTER TABLE tickets ADD CONSTRAINT tickets_ticket_id_key UNIQUE (ticket_id)")

