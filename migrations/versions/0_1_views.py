"""Alembic migration script for database schema version 0.1 with custom views enabled."""

from alembic import op

# Revision identifiers used by Alembic
revision = '0.1.views'
down_revision = None
depends_on = '0.1'


def upgrade() -> None:
    """Upgrade the database schema"""

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
    """Revert changes made to the database schema while upgrading"""

    op.execute("DROP VIEW package_count;")
    op.execute("DROP VIEW package_version_count;")
