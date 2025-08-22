from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo


_scheduler: Optional[BackgroundScheduler] = None


def _resolve_admin_user_id(app) -> Optional[int]:
    try:
        from models import User
        admin = User.query.filter_by(is_admin=True).first()
        if admin:
            return admin.id
        any_user = User.query.first()
        return any_user.id if any_user else None
    except Exception:
        return None


def _send_combined_newsletter(app, primary_market: str, tz_name: str) -> None:
    """통합 뉴스레터 생성 후 활성 구독자에게 발송(시장 타임존 기준 날짜 표기)."""
    logger = logging.getLogger(__name__)
    with app.app_context():
        try:
            from models import NewsletterSubscription, User
            from flask import url_for
            from services.newsletter_generation_service import NewsletterGenerationService
            from services.core.email_service import EmailService

            # 1) 생성 (DB 저장 위해 관리자 사용자에 귀속)
            admin_user_id = _resolve_admin_user_id(app)
            svc = NewsletterGenerationService()
            data = svc.generate_combined_newsletter(timeframe='d', primary_market=primary_market, user_id=admin_user_id)

            # 2) 발송 대상 수집
            subs = NewsletterSubscription.query.filter_by(is_active=True).all()
            if not subs:
                logger.info(f"[Scheduler] 활성 구독자 없음 - 발송 스킵 ({primary_market})")
                return

            # 3) 제목/본문 준비 (시장 타임존 날짜)
            tz = ZoneInfo(tz_name)
            local_today = datetime.now(tz).strftime('%Y-%m-%d')
            subject = f"WhatsNextStock 글로벌 뉴스레터 — {primary_market} — {local_today}"

            email_service = EmailService()

            sent, failed = 0, 0
            for sub in subs:
                try:
                    user: Optional[User] = sub.user
                    if not user or not user.email:
                        continue
                    unsubscribe_url = '#'
                    try:
                        if sub.unsubscribe_token:
                            # 외부 URL 생성: 컨텍스트 내에서 url_for 사용 가능
                            unsubscribe_url = url_for('newsletter.unsubscribe', token=sub.unsubscribe_token, _external=True)
                    except Exception:
                        pass

                    html_wrapped = email_service.render_newsletter_html(
                        title=subject,
                        recipient_name=(user.get_full_name() if user else '구독자'),
                        body_html=data.get('html', ''),
                        unsubscribe_url=unsubscribe_url,
                        inline_css=True
                    )

                    res = email_service.send_html_email(
                        to_email=user.email,
                        subject=subject,
                        html=html_wrapped,
                        categories=['newsletter_auto']
                    )
                    if res.get('status_code') in (200, 202):
                        sent += 1
                    else:
                        failed += 1
                except Exception as ie:
                    logger.warning(f"[Scheduler] 개별 발송 실패: {ie}")
                    failed += 1
            logger.info(f"[Scheduler] 통합 뉴스레터 발송 완료({primary_market}) - sent={sent}, failed={failed}")
        except Exception as e:
            logger.error(f"[Scheduler] 통합 뉴스레터 발송 오류({primary_market}): {e}")


def start_scheduler(app) -> None:
    """APScheduler 시작: ET/KST 각각 17:30에 통합 뉴스레터 발송.
    - 미국장: America/New_York 17:30 → primary_market='US'
    - 한국장: Asia/Seoul 17:30 → primary_market='kospi'
    """
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    logger = logging.getLogger(__name__)
    _scheduler = BackgroundScheduler(timezone=ZoneInfo('UTC'))

    # 미국장 ET 17:30
    _scheduler.add_job(
        _send_combined_newsletter,
        trigger=CronTrigger(hour=17, minute=30, timezone=ZoneInfo('America/New_York')),
        args=[app, 'US', 'America/New_York'],
        id='send_combined_newsletter_us',
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=300,
    )

    # 한국장 KST 17:30
    _scheduler.add_job(
        _send_combined_newsletter,
        trigger=CronTrigger(hour=17, minute=30, timezone=ZoneInfo('Asia/Seoul')),
        args=[app, 'kospi', 'Asia/Seoul'],
        id='send_combined_newsletter_korea',
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=300,
    )

    _scheduler.start()
    logger.info("[Scheduler] APScheduler started (US 17:30 ET, KOREA 17:30 KST)")


