"""empty message

Revision ID: 3a99f89842f4
Revises: 74d0e5687625
Create Date: 2019-03-19 08:27:26.160051

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '3a99f89842f4'
down_revision = '74d0e5687625'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('account_settings', sa.Column('parking_place_required', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('account_settings', 'parking_place_required')
    # ### end Alembic commands ###