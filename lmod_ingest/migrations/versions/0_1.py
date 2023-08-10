"""Alembic schema migration for database schema version 0.1."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.mysql import DATETIME

# Revision identifiers used by Alembic
revision = '0.1'
down_revision = None
depends_on = None


def upgrade() -> None:
    """Upgrade the database to this schema version"""

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

    op.execute("""
        CREATE VIEW package_count AS
            SELECT
                package,
                COUNT(*) AS total,
                time AS lastload
            FROM
                log_data
            GROUP BY
                package
            ORDER BY package DESC;
    """)

    op.execute("""
        CREATE VIEW package_version_count AS
            SELECT
                package,
                version,
                COUNT(*) AS total,
                time AS lastload
            FROM
                log_data
            GROUP BY
                package,
                version
            ORDER BY package, version DESC;
    """)


def downgrade() -> None:
    """Undo changes implemented when upgrading to this schema version"""

    op.execute("DROP TABLE log_data;")
    op.execute("DROP VIEW package_count;")
    op.execute("DROP VIEW package_version_count;")
