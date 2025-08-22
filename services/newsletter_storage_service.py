import os
import logging
from datetime import datetime
from typing import Dict, Optional

from models import db, NewsletterContent


class NewsletterStorageService:
    """뉴스레터 저장 책임 통합 서비스

    - HTML 파일 저장(static/newsletters)
    - 콘텐츠 DB 저장(NewsletterContent)
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def save_html_file(self, html_content: str, kind: str, primary: Optional[str] = None) -> str:
        """렌더된 뉴스레터 HTML을 파일로 저장하고 경로를 반환한다."""
        try:
            base_dir = os.path.join("static", "newsletters")
            os.makedirs(base_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = f"_{primary}" if primary else ""
            filename = f"Newsletter_{kind}{suffix}_{timestamp}.html"
            filepath = os.path.join(base_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.logger.info(f"Newsletter HTML saved: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Failed to save newsletter HTML: {e}")
            return ""

    def save_to_db(self, user_id: int, newsletter_data: Dict, newsletter_type: str) -> None:
        """뉴스레터 내용을 DB에 저장한다."""
        try:
            import json
            summary = newsletter_data.get('summary')
            summary_json = json.dumps(summary, ensure_ascii=False) if isinstance(summary, dict) else str(summary)

            content = NewsletterContent(
                user_id=user_id,
                market_type=newsletter_data.get('market'),
                primary_market=newsletter_data.get('primary_market'),
                timeframe=newsletter_data.get('timeframe'),
                newsletter_type=newsletter_type,
                html_content=newsletter_data.get('html'),
                summary=summary_json,
                generated_at=datetime.now()
            )

            db.session.add(content)
            db.session.commit()
            self.logger.info(f"뉴스레터 DB 저장 완료: user={user_id}, type={newsletter_type}")
        except Exception as e:
            self.logger.error(f"뉴스레터 DB 저장 실패: {e}")
            db.session.rollback()
            raise


