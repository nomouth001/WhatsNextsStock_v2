from flask import Blueprint, request, jsonify, current_app
import logging
from models import db, EmailMessage, EmailEvent, EmailSuppression
from datetime import datetime
import json
import base64

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.exceptions import InvalidSignature
    _CRYPTO_OK = True
except Exception:
    _CRYPTO_OK = False

webhooks_bp = Blueprint('webhooks', __name__)


def _verify_sendgrid_signature(headers, body_bytes) -> bool:
    """SendGrid Event Webhook 서명 검증(Ed25519). 개발 단계에서는 우회 가능.
    문서: https://docs.sendgrid.com/for-developers/tracking-events/event
    """
    public_key = current_app.config.get('SENDGRID_EVENT_PUBLIC_KEY')
    signature = headers.get('X-Twilio-Email-Event-Webhook-Signature')
    timestamp = headers.get('X-Twilio-Email-Event-Webhook-Timestamp')
    if not public_key or not signature or not timestamp:
        logging.warning('[Webhook] 서명 검증 비활성화(키/헤더 누락). 개발용 우회 처리합니다.')
        return True
    if not _CRYPTO_OK:
        logging.warning('[Webhook] cryptography 미설치로 검증 우회')
        return True
    try:
        pk_bytes = base64.b64decode(public_key)
        verify_key = Ed25519PublicKey.from_public_bytes(pk_bytes)
        sig_bytes = base64.b64decode(signature)
        message = (timestamp.encode('utf-8') + body_bytes)
        verify_key.verify(sig_bytes, message)
        return True
    except InvalidSignature:
        logging.error('[Webhook] 서명 검증 실패 (InvalidSignature)')
        return False
    except Exception as e:
        logging.error(f'[Webhook] 서명 검증 예외: {e}')
        return False


@webhooks_bp.route('/sendgrid/events', methods=['POST'])
def handle_sendgrid_events():
    try:
        if not _verify_sendgrid_signature(request.headers, request.data):
            return jsonify({'success': False, 'message': 'invalid signature'}), 400

        events = request.get_json(force=True, silent=True)
        if not isinstance(events, list):
            return jsonify({'success': False, 'message': 'invalid payload'}), 400

        saved = 0
        for ev in events:
            try:
                event_type = ev.get('event')
                sg_event_id = ev.get('sg_event_id') or ev.get('event_id')
                occurred_at = ev.get('timestamp')
                if isinstance(occurred_at, (int, float)):
                    occurred_dt = datetime.utcfromtimestamp(occurred_at)
                else:
                    occurred_dt = datetime.utcnow()

                # 메시지 매핑: sg_message_id / smtp-id (각괄호 제거)
                raw_msg_id = ev.get('sg_message_id') or ev.get('smtp-id') or ''
                msg_id_clean = str(raw_msg_id).strip('<>') if raw_msg_id else None

                email_message = None
                if msg_id_clean:
                    email_message = EmailMessage.query.filter_by(sendgrid_message_id=msg_id_clean).first()

                # 이벤트 중복 차단
                if sg_event_id and EmailEvent.query.filter_by(sg_event_id=sg_event_id).first():
                    continue

                email_event = EmailEvent(
                    message_id=email_message.id if email_message else None,
                    event=event_type or 'unknown',
                    reason=ev.get('reason'),
                    sg_event_id=sg_event_id,
                    occurred_at=occurred_dt,
                    raw_payload=json.dumps(ev, ensure_ascii=False)
                )
                db.session.add(email_event)

                # 상태 전이
                if email_message:
                    if event_type == 'delivered':
                        email_message.status = 'delivered'
                        email_message.delivered_at = occurred_dt
                    elif event_type == 'bounce':
                        email_message.status = 'bounced'
                        email_message.last_error = ev.get('reason')
                        # 바운스 억제 리스트 추가
                        try:
                            to_email = ev.get('email')
                            if to_email:
                                if not EmailSuppression.query.filter_by(email=to_email).first():
                                    db.session.add(EmailSuppression(email=to_email, reason='bounce', detail=ev.get('reason')))
                        except Exception:
                            pass
                    elif event_type in ('dropped', 'deferred'):
                        email_message.status = event_type

                saved += 1
            except Exception as ie:
                logging.warning(f"[Webhook] 이벤트 처리 실패: {ie}")

        db.session.commit()
        return jsonify({'success': True, 'saved': saved})
    except Exception as e:
        logging.error(f"[Webhook] 오류: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


