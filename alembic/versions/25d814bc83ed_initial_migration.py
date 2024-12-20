"""initial migration

Revision ID: 25d814bc83ed
Revises: 
Create Date: 2024-04-21 09:51:44.977108

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
import uuid
from app.utils.security import hash_password
from app.models.user_model import UserRole


# revision identifiers, used by Alembic.
revision: str = '25d814bc83ed'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('nickname', sa.String(length=50), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('first_name', sa.String(length=100), nullable=True),
    sa.Column('last_name', sa.String(length=100), nullable=True),
    sa.Column('bio', sa.String(length=500), nullable=True),
    sa.Column('profile_picture_url', sa.String(length=255), nullable=True),
    sa.Column('linkedin_profile_url', sa.String(length=255), nullable=True),
    sa.Column('github_profile_url', sa.String(length=255), nullable=True),
    sa.Column('role', sa.Enum('ANONYMOUS', 'AUTHENTICATED', 'MANAGER', 'ADMIN', name='UserRole', create_constraint=True), nullable=False),
    sa.Column('is_professional', sa.Boolean(), nullable=True),
    sa.Column('professional_status_updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('failed_login_attempts', sa.Integer(), nullable=True),
    sa.Column('is_locked', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('verification_token', sa.String(), nullable=True),
    sa.Column('email_verified', sa.Boolean(), nullable=False),
    sa.Column('hashed_password', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_nickname'), 'users', ['nickname'], unique=True)
    # Add 50 users -- Uncomment to test the user search in local 
    #insert_users()

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_users_nickname'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    # Clear the inserted users
    #clear_inserted_users() #-- Uncomment to test the user search in local 
    # ### end Alembic commands ###

def insert_users():
    """
    Inserts 50 users into the 'users' table with a mix of roles.
    """
    roles = [UserRole.ADMIN, UserRole.MANAGER, UserRole.AUTHENTICATED, UserRole.ANONYMOUS]

    for i in range(50):
        user_id = str(uuid.uuid4())
        nickname = f"user_{i}"
        email = f"user_{i}@example.com"
        hashed_password = hash_password("Password123!")
        role = roles[i % len(roles)]  # Rotate roles
        email_verified = role != UserRole.ANONYMOUS
        is_locked = role == UserRole.ANONYMOUS  # Lock anonymous users

        op.execute(
            text(
                """
                INSERT INTO users (
                    id, nickname, email, hashed_password, role, email_verified, is_locked, created_at, updated_at
                ) VALUES (
                    :id, :nickname, :email, :hashed_password, :role, :email_verified, :is_locked, now(), now()
                )
                """
            ).bindparams(
                id=user_id,
                nickname=nickname,
                email=email,
                hashed_password=hashed_password,
                role=role.name,
                email_verified=email_verified,
                is_locked=is_locked,
            )
        )


def clear_inserted_users():
    """
    Deletes the 50 inserted users based on their email pattern (user_0@example.com to user_49@example.com).
    """
    op.execute(
        text(
            """
            DELETE FROM users
            WHERE email LIKE 'user_%@example.com'
            """
        )
    )