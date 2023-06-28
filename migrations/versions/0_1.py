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
        'user',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('name', sa.VARCHAR(100), nullable=False, unique=True, index=True),
        sa.PrimaryKeyConstraint('id'))

    op.create_table(
        'package',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('name', sa.VARCHAR(100), nullable=False, index=True),
        sa.Column('version', sa.VARCHAR(100), nullable=True),
        sa.Column('path', sa.VARCHAR(200), nullable=False, unique=True),
        sa.PrimaryKeyConstraint('id'))

    op.create_table(
        'host',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('name', sa.VARCHAR(100), nullable=False, unique=True, index=True),
        sa.PrimaryKeyConstraint('id'))

    op.create_table(
        'module_usage',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('host_id', sa.Integer(), nullable=False, index=True),
        sa.Column('package_id', sa.Integer(), nullable=False, index=True),
        sa.Column('load_time', DATETIME(fsp=6), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['host_id'], ['host.id'], ),
        sa.ForeignKeyConstraint(['package_id'], ['package.id'], ),
        sa.UniqueConstraint('user_id', 'host_id', 'package_id', 'load_time'),
        sa.PrimaryKeyConstraint('id'))


def downgrade() -> None:
    """Downgrade from the current database versions to the previous revision"""

    raise RuntimeError('There is no revision below this version to revert to.')
