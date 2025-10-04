"""Create job_requests table

Revision ID: 1a2b3c4d5e6f
Revises: 
Create Date: 2025-10-03 22:23:31.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create job_requests table
    op.create_table(
        'job_requests',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('job_id', sa.Integer(), sa.ForeignKey('job_postings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('worker_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('client_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.UniqueConstraint('job_id', 'worker_id', name='uq_job_worker')
    )
    
    # Create indexes
    op.create_index('idx_job_requests_job_id', 'job_requests', ['job_id'])
    op.create_index('idx_job_requests_worker_id', 'job_requests', ['worker_id'])
    op.create_index('idx_job_requests_client_id', 'job_requests', ['client_id'])
    op.create_index('idx_job_requests_status', 'job_requests', ['status'])

def downgrade():
    # Drop indexes
    op.drop_index('idx_job_requests_status', 'job_requests')
    op.drop_index('idx_job_requests_client_id', 'job_requests')
    op.drop_index('idx_job_requests_worker_id', 'job_requests')
    op.drop_index('idx_job_requests_job_id', 'job_requests')
    
    # Drop table
    op.drop_table('job_requests')
