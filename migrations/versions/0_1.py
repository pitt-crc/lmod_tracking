"""Database schema migration for schema version 0.1."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.mysql import DATETIME

# Revision identifiers used by Alembic
revision = '0.1'
down_revision = None
depends_on = None


def upgrade() -> None:
    """Upgrade from previous database versions to the current revision"""

    op.create_table(
        'log_data',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('logname', sa.String(255), nullable=False),
        sa.Column('time', DATETIME(fsp=6), nullable=False),
        sa.Column('host', sa.String(255), nullable=False),
        sa.Column('user', sa.String(50), nullable=False),
        sa.Column('module', sa.String(100), nullable=False),
        sa.Column('path', sa.String(4096), nullable=False),
        sa.Column('version', sa.String(150), nullable=False),
        sa.Column('package', sa.String(100), nullable=False),
        sa.UniqueConstraint('time', 'host', 'user', 'module', name='unq_log_entry')
    )


def downgrade() -> None:
    """Downgrade from the current database versions to the previous revision"""

    raise RuntimeError('There is no database revision below version 0.1.')
