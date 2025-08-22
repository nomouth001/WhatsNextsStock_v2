import sys
import argparse
import getpass
from pathlib import Path

# 실행 경로 무관하게 프로젝트 루트를 모듈 경로에 추가
try:
    _ROOT = Path(__file__).resolve().parents[1]
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))
except Exception:
    pass


def main() -> int:
    try:
        from app import create_app
        from models import db, User
    except Exception as e:
        print(f"[ERROR] 앱/모델 임포트 실패: {e}")
        return 2

    parser = argparse.ArgumentParser(description="관리자(또는 임의 사용자) 비밀번호 변경 스크립트")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--username", help="대상 사용자명")
    g.add_argument("--email", help="대상 이메일")
    parser.add_argument("--new-password", dest="new_password", help="새 비밀번호(미지정 시 안전하게 입력받음)")
    args = parser.parse_args()

    # 비밀번호 입력(확인 포함)
    if args.new_password:
        new_password = args.new_password
    else:
        pw1 = getpass.getpass("새 비밀번호 입력: ")
        pw2 = getpass.getpass("새 비밀번호 확인: ")
        if pw1 != pw2:
            print("[ERROR] 비밀번호가 일치하지 않습니다.")
            return 1
        new_password = pw1

    # 간단 강도 점검(선택)
    if len(new_password) < 8:
        print("[WARN] 8자 미만의 비밀번호입니다. 보안을 위해 더 길게 설정하는 것을 권장합니다.")

    app = create_app()
    with app.app_context():
        # 사용자 조회
        user: User | None = None
        if args.username:
            user = User.query.filter_by(username=args.username).first()
        else:
            user = User.query.filter_by(email=args.email).first()

        if not user:
            print("[ERROR] 대상 사용자를 찾지 못했습니다.")
            return 3

        # 비밀번호 변경
        try:
            user.set_password(new_password)
            db.session.commit()
            print(f"[OK] 사용자(id={user.id}, username={user.username}) 비밀번호가 변경되었습니다.")
            return 0
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] 비밀번호 변경 실패: {e}")
            return 4


if __name__ == "__main__":
    sys.exit(main())


