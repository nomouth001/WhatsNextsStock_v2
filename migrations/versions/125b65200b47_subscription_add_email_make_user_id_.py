from alembic import op
import sqlalchemy as sa

revision = '125b65200b47'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1) email 컬럼 추가, user_id nullable 허용 (SQLite 호환 batch)
    with op.batch_alter_table('newsletter_subscriptions') as batch:
        batch.add_column(sa.Column('email', sa.String(255), nullable=True))
        batch.alter_column('user_id', existing_type=sa.Integer(), nullable=True)

    # 2) 기존 데이터 백필: users.email -> newsletter_subscriptions.email
    op.execute("""
        UPDATE newsletter_subscriptions
        SET email = (
            SELECT email FROM users
            WHERE users.id = newsletter_subscriptions.user_id
        )
        WHERE email IS NULL
    """)

    # 3) 백필 실패분(연결 사용자 없음) 임시 이메일 채움 (unique 보장)
    op.execute("""
        UPDATE newsletter_subscriptions
        SET email = 'unknown_' || id || '@example.local'
        WHERE email IS NULL
    """)

    # 4) email NOT NULL + UNIQUE 제약
    with op.batch_alter_table('newsletter_subscriptions') as batch:
        batch.alter_column('email', existing_type=sa.String(length=255), nullable=False)
        batch.create_unique_constraint('uq_newsletter_subscriptions_email', ['email'])


def downgrade():
    with op.batch_alter_table('newsletter_subscriptions') as batch:
        try:
            batch.drop_constraint('uq_newsletter_subscriptions_email', type_='unique')
        except Exception:
            pass
        batch.alter_column('user_id', existing_type=sa.Integer(), nullable=False)
        try:
            batch.drop_column('email')
        except Exception:
            pass
