"""
중복 종목 정리 스크립트 (소프트 삭제 정책 유지)

기능:
- 동일 (ticker, market_type) 조합에 대해 가장 최근 레코드 1개만 활성화로 유지
- 나머지는 비활성화(is_active=False)로 전환
- ticker는 대문자/공백 정규화하여 비교

사용법 (프로젝트 루트에서):
  - python -m scripts.cleanup_stocks

주의:
- 애플리케이션 컨텍스트 필요. app.py의 create_app()을 사용합니다.
"""

import sys
from collections import defaultdict
from datetime import datetime

from app import create_app
from models import db, Stock


def normalize_ticker(raw: str) -> str:
    if raw is None:
        return ''
    return str(raw).strip().upper()


def main() -> int:
    app = create_app()
    with app.app_context():
        stocks = Stock.query.order_by(Stock.created_at.desc()).all()

        groups = defaultdict(list)
        for s in stocks:
            key = (normalize_ticker(s.ticker), (s.market_type or '').strip().upper())
            groups[key].append(s)

        to_deactivate = []
        to_normalize = []

        for (ticker, market_type), items in groups.items():
            # 최신 1개만 활성화 유지
            # created_at 내림차순으로 이미 로드됨
            keep = None
            for idx, item in enumerate(items):
                # 티커/마켓 정규화 반영
                changed = False
                if item.ticker != ticker:
                    item.ticker = ticker
                    changed = True
                if (item.market_type or '').strip().upper() != market_type:
                    item.market_type = market_type
                    changed = True
                if changed:
                    to_normalize.append(item)

                if idx == 0:
                    keep = item
                    if not item.is_active:
                        item.is_active = True
                else:
                    if item.is_active:
                        item.is_active = False
                        to_deactivate.append(item)

        db.session.commit()

        print(f"정규화 적용: {len(to_normalize)}건, 비활성화 처리: {len(to_deactivate)}건")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())


