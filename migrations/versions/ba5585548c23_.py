"""empty message

Revision ID: ba5585548c23
Revises: 5c0c94d8f1c3
Create Date: 2024-10-06 17:32:53.358742

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ba5585548c23'
down_revision = '5c0c94d8f1c3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('campaign',
    sa.Column('campaign_id', sa.BigInteger(), nullable=False),
    sa.Column('campaign_name', sa.String(length=255), nullable=False),
    sa.Column('campaign_type', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('campaign_id')
    )
    op.create_table('ad_group',
    sa.Column('ad_group_id', sa.BigInteger(), nullable=False),
    sa.Column('ad_group_name', sa.String(length=255), nullable=False),
    sa.Column('campaign_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['campaign_id'], ['campaign.campaign_id'], ),
    sa.PrimaryKeyConstraint('ad_group_id')
    )
    op.create_table('ad_group_stats',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('ad_group_id', sa.BigInteger(), nullable=False),
    sa.Column('device', sa.String(length=50), nullable=False),
    sa.Column('impressions', sa.Integer(), nullable=False),
    sa.Column('clicks', sa.Integer(), nullable=False),
    sa.Column('conversions', sa.Float(), nullable=False),
    sa.Column('cost', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['ad_group_id'], ['ad_group.ad_group_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('ad_group_stats')
    op.drop_table('ad_group')
    op.drop_table('campaign')
    # ### end Alembic commands ###
