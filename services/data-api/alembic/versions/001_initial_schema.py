"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2025-01-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Initial empty migration - tables will be added in Story 22.2"""
    pass


def downgrade() -> None:
    """Rollback initial migration"""
    pass

