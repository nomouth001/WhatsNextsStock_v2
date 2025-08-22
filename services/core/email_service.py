import os
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from flask import current_app
from models import EmailSuppression
from flask import render_template
from premailer import transform


class EmailService:
    """
    SendGrid 기반 이메일 발송 서비스 (동기, MVP)

    환경 변수/설정 사용:
    - app.config['SENDGRID_API_KEY']
    - app.config['EMAIL_FROM_EMAIL']
    - app.config['EMAIL_FROM_NAME']
    - app.config['EMAIL_REPLY_TO']
    - app.config['SENDGRID_SANDBOX_MODE']
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _get_config(self) -> Dict[str, Any]:
        app = current_app
        return {
            'api_key': app.config.get('SENDGRID_API_KEY'),
            'from_email': app.config.get('EMAIL_FROM_EMAIL'),
            'from_name': app.config.get('EMAIL_FROM_NAME', 'WhatsNextStock'),
            'reply_to': app.config.get('EMAIL_REPLY_TO') or app.config.get('EMAIL_FROM_EMAIL'),
            'sandbox': bool(app.config.get('SENDGRID_SANDBOX_MODE', False)),
        }

    def render_newsletter_html(self, title: str, recipient_name: str, body_html: str, unsubscribe_url: str = '#', inline_css: bool = True) -> str:
        raw = render_template('email/newsletter_email.html', title=title, recipient_name=recipient_name, body_html=body_html, unsubscribe_url=unsubscribe_url)
        return transform(raw) if inline_css else raw

    def send_html_email(
        self,
        to_email: str,
        subject: str,
        html: str,
        categories: Optional[List[str]] = None,
        custom_args: Optional[Dict[str, str]] = None,
        sandbox_override: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """HTML 이메일 단건 발송

        반환: {'status_code': int, 'message_id': Optional[str], 'error': Optional[str]}
        """
        cfg = self._get_config()
        api_key = cfg['api_key']
        if not api_key:
            return {'status_code': 0, 'message_id': None, 'error': 'SENDGRID_API_KEY not configured'}

        # 억제 리스트 체크
        try:
            suppress = EmailSuppression.query.filter_by(email=to_email).first()
            if suppress:
                return {'status_code': 0, 'message_id': None, 'error': f'suppressed: {suppress.reason}'}
        except Exception:
            # DB 미초기화 등은 무시하고 진행
            pass

        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, Email, To, Content, Personalization, Category, Header
        except Exception as e:
            return {'status_code': 0, 'message_id': None, 'error': f'sendgrid import failed: {e}'}

        from_email = Email(email=cfg['from_email'], name=cfg['from_name'])
        to = To(email=to_email)

        message = Mail(from_email=from_email, to_emails=to, subject=subject, html_content=html)

        # reply-to
        if cfg.get('reply_to'):
            try:
                message.reply_to = Email(cfg['reply_to'])
            except Exception:
                pass

        # categories
        if categories:
            for c in categories:
                try:
                    message.add_category(Category(c))
                except Exception:
                    pass

        # custom args (X-SMTPAPI custom args -> sendgrid v3 headers는 custom_args 사용)
        if custom_args:
            try:
                message.custom_args = custom_args
            except Exception:
                # 무시
                pass

        # sandbox mode
        sandbox_mode = cfg['sandbox'] if sandbox_override is None else bool(sandbox_override)
        if sandbox_mode:
            try:
                message.mail_settings = getattr(message, 'mail_settings', None) or type('MailSettings', (), {})()
                # sendgrid.helpers.mail에서 SandBoxMode 설정 방식
                from sendgrid.helpers.mail import MailSettings, SandBoxMode
                ms = MailSettings()
                ms.sandbox_mode = SandBoxMode(True)
                message.mail_settings = ms
            except Exception:
                pass

        try:
            sg = sendgrid.SendGridAPIClient(api_key)
            response = sg.send(message)
            message_id = None
            try:
                message_id = response.headers.get('X-Message-Id') or response.headers.get('X-Message-ID')
            except Exception:
                pass

            self.logger.info(f"[EmailService] send status={response.status_code} message_id={message_id}")
            # 내부 발송 기록 생성 시도 (모델이 사용할 수 있는 환경에서만)
            try:
                from models import db, EmailMessage
                msg = EmailMessage(
                    to=to_email,
                    subject=subject,
                    template='newsletter_email',
                    status='sent' if getattr(response, 'status_code', 0) in (200, 202) else 'failed',
                    sendgrid_message_id=message_id,
                )
                db.session.add(msg)
                db.session.commit()
            except Exception:
                # 데이터베이스 미초기화 환경 등은 무시
                pass

            return {
                'status_code': getattr(response, 'status_code', -1),
                'message_id': message_id,
                'error': None if getattr(response, 'status_code', 0) in (200, 202) else getattr(response, 'body', None)
            }
        except Exception as e:
            self.logger.error(f"[EmailService] send failed: {e}")
            return {'status_code': 0, 'message_id': None, 'error': str(e)}

    def send_bulk_html(
        self,
        recipients: List[Dict[str, str]],
        subject: str,
        html: str,
        batch_size: int = 500,
        max_retries: int = 4
    ) -> Dict[str, Any]:
        """간단한 배치 발송(동기 루프, 지수 백오프 재시도 포함). 비동기 큐는 후속 도입.
        recipients: [{"email": "a@b.com"}, ...]
        """
        import time
        results: Dict[str, Any] = { 'total': len(recipients), 'sent': 0, 'failed': 0 }
        delay_schedule = [60, 300, 1800, 7200]  # 1m,5m,30m,2h

        for i in range(0, len(recipients), batch_size):
            batch = recipients[i:i+batch_size]
            for r in batch:
                to_email = r.get('email')
                attempt = 0
                while attempt <= max_retries:
                    attempt += 1
                    res = self.send_html_email(to_email, subject, html)
                    if res.get('status_code') in (200, 202):
                        results['sent'] += 1
                        break
                    else:
                        if attempt > max_retries:
                            results['failed'] += 1
                            break
                        # 429/5xx만 백오프 대상로 보는 것이 바람직하지만 여기선 단순 처리
                        time.sleep(delay_schedule[min(attempt-1, len(delay_schedule)-1)])
        return results

    def send_bulk_newsletter(
        self,
        recipients: List[Dict[str, str]],
        subject: str,
        body_html: str,
        *,
        newsletter_id: Optional[int] = None,
        edition_date: Optional[datetime] = None,
        inline_css: bool = True,
    ) -> Dict[str, Any]:
        """개인화 구독 해지 링크와 수신자 이름을 포함해 뉴스레터를 대량 발송한다.

        recipients: [{ 'email': str, 'name': Optional[str], 'unsubscribe_url': Optional[str] }]
        """
        results: Dict[str, Any] = { 'total': len(recipients), 'sent': 0, 'failed': 0 }
        for r in recipients:
            try:
                to_email = r.get('email')
                if not to_email:
                    results['failed'] += 1
                    continue
                recipient_name = r.get('name') or '구독자'
                unsubscribe_url = r.get('unsubscribe_url') or '#'

                html_wrapped = self.render_newsletter_html(
                    title=subject,
                    recipient_name=recipient_name,
                    body_html=body_html,
                    unsubscribe_url=unsubscribe_url,
                    inline_css=inline_css
                )

                res = self.send_html_email(to_email=to_email, subject=subject, html=html_wrapped, categories=['newsletter_broadcast'])
                if res.get('status_code') in (200, 202):
                    results['sent'] += 1
                    # 뉴스레터 메타데이터 보강
                    if newsletter_id and res.get('message_id'):
                        try:
                            from models import db, EmailMessage
                            msg = EmailMessage.query.filter_by(sendgrid_message_id=res['message_id']).first()
                            if msg:
                                msg.newsletter_id = newsletter_id
                                if edition_date:
                                    msg.edition_date = edition_date
                                db.session.commit()
                        except Exception:
                            pass
                else:
                    results['failed'] += 1
            except Exception:
                results['failed'] += 1
                continue
        return results


