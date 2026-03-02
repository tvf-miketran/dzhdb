"""Change role_id to role_ids array and remove unique constraint from ticket_id

Revision ID: change_role_id_to_array
Revises: 5f504cf7cae4
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'change_role_id_to_array'
down_revision = '5f504cf7cae4'
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Remove unique constraint from ticket_id (if exists)
    op.execute("""
        ALTER TABLE tickets 
        DROP CONSTRAINT IF EXISTS tickets_ticket_id_key
    """)
    
    # Step 2: Drop the unique index on ticket_id (if exists)
    op.execute("""
        DROP INDEX IF EXISTS ix_tickets_ticket_id
    """)
    
    # Step 3: Check if role_ids column already exists
    # If it doesn't exist, create it. If it exists, we skip this step.
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'tickets' AND column_name = 'role_ids'
    """))
    
    if result.fetchone() is None:
        # role_ids column doesn't exist, so we need to add it
        # First add the new column
        op.add_column('tickets', sa.Column('role_ids', postgresql.ARRAY(sa.String()), nullable=True, default=[]))
        
        # Check if role_id column still exists and copy data
        result2 = conn.execute(sa.text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'tickets' AND column_name = 'role_id'
        """))
        
        if result2.fetchone() is not None:
            # Copy data from role_id to role_ids (as array)
            op.execute("""
                UPDATE tickets 
                SET role_ids = ARRAY[role_id::text]::uuid[] 
                WHERE role_id IS NOT NULL
            """)
            # Drop the old role_id column
            op.drop_column('tickets', 'role_id')
    else:
        # role_ids already exists, just check if we need to drop role_id
        result3 = conn.execute(sa.text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'tickets' AND column_name = 'role_id'
        """))
        
        if result3.fetchone() is not None:
            # Copy data from role_id to role_ids before dropping
            op.execute("""
                UPDATE tickets 
                SET role_ids = ARRAY[role_id::text]::uuid[] 
                WHERE role_id IS NOT NULL AND (role_ids IS NULL OR role_ids = '{}')
            """)
            # Drop the old role_id column
            op.drop_column('tickets', 'role_id')


def downgrade():
    # Step 1: Add back role_id column
    op.add_column('tickets', sa.Column('role_id', sa.String(), nullable=True))
    
    # Copy data from role_ids array back to role_id (first element)
    op.execute("""
        UPDATE tickets 
        SET role_id = role_ids[1]::text 
        WHERE role_ids IS NOT NULL AND array_length(role_ids, 1) > 0
    """)
    
    # Drop the role_ids column
    op.drop_column('tickets', 'role_ids')
    
    # Add unique constraint back to ticket_id
    op.execute("ALTER TABLE tickets ADD CONSTRAINT tickets_ticket_id_key UNIQUE (ticket_id)")
    
    # Recreate the unique index
    op.execute("CREATE UNIQUE INDEX ix_tickets_ticket_id ON tickets (ticket_id)")

