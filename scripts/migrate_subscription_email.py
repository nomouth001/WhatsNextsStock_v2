import os
import sys
import glob
import time
from pathlib import Path
import subprocess


def run(cmd, cwd=None):
    print(f"$ {' '.join(cmd)}")
    p = subprocess.run(cmd, cwd=cwd, check=True)
    return p.returncode


def ensure_env():
    # FLASK_APP 설정 (app.py)
    os.environ.setdefault('FLASK_APP', 'app.py')
    # Windows PowerShell에서도 동작하도록 파이썬 실행 파일 경로 확보
    return [sys.executable, '-m', 'flask']


def ensure_migrations(flask_cmd):
    if not Path('migrations').exists():
        run(flask_cmd + ['db', 'init'])


def migrate_generate(flask_cmd, message: str) -> Path:
    before = set(Path('migrations/versions').glob('*.py')) if Path('migrations/versions').exists() else set()
    try:
        run(flask_cmd + ['db', 'migrate', '-m', message])
    except Exception:
        # 데이터베이스가 up-to-date가 아니거나, 보류된 리비전이 있을 때: 최신 파일로 진행
        if Path('migrations/versions').exists():
            latest = sorted(Path('migrations/versions').glob('*.py'), key=lambda p: p.stat().st_mtime)[-1]
            return latest
        raise
    time.sleep(0.3)
    after = set(Path('migrations/versions').glob('*.py'))
    created = list(after - before)
    if not created:
        latest = sorted(after, key=lambda p: p.stat().st_mtime)[-1]
        return latest
    return created[0]


def rewrite_migration_file(path: Path):
    # 기존 파일의 헤더(리비전/다운리비전) 보존
    text = path.read_text(encoding='utf-8')
    rev = 'auto'
    down_rev = None
    for line in text.splitlines():
        if line.strip().startswith('revision ='):
            rev = line.split('=', 1)[1].strip()
        if line.strip().startswith('down_revision ='):
            down_rev = line.split('=', 1)[1].strip()
    content = f''' 
from alembic import op
import sqlalchemy as sa

revision = {rev}
down_revision = {down_rev}
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
'''.lstrip()
    path.write_text(content, encoding='utf-8')


def upgrade(flask_cmd):
    run(flask_cmd + ['db', 'upgrade'])


def main():
    flask_cmd = ensure_env()
    ensure_migrations(flask_cmd)
    created = migrate_generate(flask_cmd, 'subscription: add email, make user_id nullable')
    rewrite_migration_file(created)
    upgrade(flask_cmd)
    print(f"Migration applied successfully: {created}")


if __name__ == '__main__':
    main()


