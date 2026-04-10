"""seed odc lead admin account

Revision ID: e3c9a1f4b2d7
Revises: aa88fb4d3022
Create Date: 2026-04-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from werkzeug.security import generate_password_hash


# revision identifiers, used by Alembic.
revision = 'e3c9a1f4b2d7'
down_revision = 'aa88fb4d3022'
branch_labels = None
depends_on = None


ACCOUNT_VN_FULL_NAME = 'ODC LEAD'
ACCOUNT_EN_FULL_NAME = 'ODC LEAD'
ACCOUNT_EMPLOYEE_ID = 'LEAD'
ACCOUNT_DESCRIPTION = ''
ACCOUNT_EMAIL = 'odc.lead@techvify.com.vn'
ACCOUNT_PASSWORD = '123456'
ACCOUNT_AUTHORIZE_ROLE = 'ADMIN'


def upgrade():
    bind = op.get_bind()

    existing_count = bind.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM employees
            WHERE email = :email OR "employeeId" = :employee_id
            """
        ),
        {
            'email': ACCOUNT_EMAIL,
            'employee_id': ACCOUNT_EMPLOYEE_ID,
        },
    ).scalar_one()

    if existing_count:
        return

    bind.execute(
        sa.text(
            """
            INSERT INTO employees (
                id,
                vn_full_name,
                en_full_name,
                "employeeId",
                description,
                email,
                password,
                authorize_role,
                status
            )
            VALUES (
                gen_random_uuid(),
                :vn_full_name,
                :en_full_name,
                :employee_id,
                :description,
                :email,
                :password,
                :authorize_role,
                :status
            )
            """
        ),
        {
            'vn_full_name': ACCOUNT_VN_FULL_NAME,
            'en_full_name': ACCOUNT_EN_FULL_NAME,
            'employee_id': ACCOUNT_EMPLOYEE_ID,
            'description': ACCOUNT_DESCRIPTION,
            'email': ACCOUNT_EMAIL,
            'password': generate_password_hash(ACCOUNT_PASSWORD, method='scrypt'),
            'authorize_role': ACCOUNT_AUTHORIZE_ROLE,
            'status': True,
        },
    )


def downgrade():
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            DELETE FROM employees
            WHERE email = :email AND "employeeId" = :employee_id
            """
        ),
        {
            'email': ACCOUNT_EMAIL,
            'employee_id': ACCOUNT_EMPLOYEE_ID,
        },
    )