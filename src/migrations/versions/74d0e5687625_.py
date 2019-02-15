"""empty message

Revision ID: 74d0e5687625
Revises: 9e71e759b9d8
Create Date: 2019-02-14 14:28:05.109293

"""
import datetime

import sqlalchemy as sa
from alembic import op
# revision identifiers, used by Alembic.
from sqlalchemy import table, select

revision = '74d0e5687625'
down_revision = '9e71e759b9d8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    account_settings = op.create_table('account_settings',
                                       sa.Column('id', sa.Integer(), nullable=False),
                                       sa.Column('time_created', sa.DateTime(), nullable=True),
                                       sa.Column('time_updated', sa.DateTime(), nullable=True),
                                       sa.Column('user_id', sa.Integer(), nullable=False),
                                       sa.Column('auto_load_parking_place_gps_location', sa.Boolean(), nullable=True),
                                       sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
                                       sa.PrimaryKeyConstraint('id')
                                       )

    # Data migration

    users = table(
        'users',
        sa.Column('id', sa.Integer()),
    )

    users_result = op.get_bind().execute(
        select([users])
    )

    for u in users_result:
        date = datetime.datetime.utcnow()
        op.get_bind().execute(
            account_settings.insert().values(user_id=u[0],
                                             auto_load_parking_place_gps_location=0,
                                             time_created=date.strftime('%Y-%m-%d %H:%M:%S'))
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('account_settings')
    # ### end Alembic commands ###