"""Alembic migration script for database schema version 0.2."""

import sqlalchemy as sa
from alembic import op

# Revision identifiers used by Alembic
revision = '0.2'
down_revision = '0.1'
depends_on = None


def upgrade() -> None:
    """Upgrade the database schema"""

    # Add a new column for tracking Slurm job IDs
    op.add_column('log_data', sa.Column('jobid', sa.Integer(), nullable=True))

    # Introduce a new view with unique package loads modulo job ID
    op.execute("""
        CREATE VIEW unique_loads AS
            SELECT DISTINCT
                package,
                version,
                jobid,
                max(time) as time
            FROM log_data
            WHERE jobid IS NOT NULL
            GROUP BY
                jobid,
                version,
                package;
       """)

    # Update existing views to include job ID information
    op.execute("""
        CREATE OR REPLACE VIEW package_count AS
            SELECT
                package,
                COUNT(*) AS total,
                max(time) AS lastload
            FROM
                unique_loads
            GROUP BY
                package
            ORDER BY
                package;
       """)

    op.execute("""
        CREATE OR REPLACE VIEW package_version_count AS
            SELECT
                package,
                version,
                COUNT(*) AS total,
                max(time) AS lastload
            FROM
                unique_loads
            GROUP BY
                package,
                version
            ORDER BY package, version;
    """)


def downgrade() -> None:
    """Revert changes made to the database schema while upgrading"""

    # Remove views and colums that are new to this version
    op.drop_column('log_data', 'jobid')
    op.drop_table('unique_loads')

    # Restore old views to their original version
    op.execute("""
           CREATE OR REPLACE VIEW package_count AS
               SELECT
                   package,
                   COUNT(*) AS total,
                   max(time) AS lastload
               FROM
                   log_data
               GROUP BY
                   package
               ORDER BY package;
       """)

    op.execute("""
           CREATE OR REPLACE VIEW package_version_count AS
               SELECT
                   package,
                   version,
                   COUNT(*) AS total,
                   max(time) AS lastload
               FROM
                   log_data
               GROUP BY
                   package,
                   version
               ORDER BY package, version;
       """)
