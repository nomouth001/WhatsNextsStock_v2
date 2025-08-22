import os
import logging
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship

# 데이터베이스 객체 생성
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """사용자 모델"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_withdrawn = db.Column(db.Boolean, default=False)
    withdrawn_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        """비밀번호 설정"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """비밀번호 확인"""
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """전체 이름 반환"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def __repr__(self):
        return f'<User {self.username}>'

# StockList 모델 주석 처리 (더 이상 사용하지 않음)
# class StockList(db.Model):
#     """주식 리스트 모델 (KOSPI, KOSDAQ, US 구분)"""
#     __tablename__ = 'stock_lists'
#     
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     market_type = db.Column(db.String(10), nullable=False)  # 'KOSPI', 'KOSDAQ', 'US'
#     description = db.Column(db.Text)
#     is_active = db.Column(db.Boolean, default=True)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
#     
#     # 관계 설정
#     stocks = relationship('Stock', back_populates='stock_list', cascade='all, delete-orphan')
#     
#     def __repr__(self):
#         return f'<StockList {self.name} ({self.market_type})>'

class Stock(db.Model):
    """개별 주식 모델"""
    __tablename__ = 'stocks'
    
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20), nullable=False)
    company_name = db.Column(db.String(200))
    market_type = db.Column(db.String(10), nullable=False)  # 'US', 'KOSPI', 'KOSDAQ'
    # stock_list_id 외래키 제거
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정 제거
    # stock_list = relationship('StockList', back_populates='stocks')
    
    def __repr__(self):
        return f'<Stock {self.ticker} - {self.company_name} ({self.market_type})>'

class NewsletterSubscription(db.Model):
    """뉴스레터 구독 설정 모델 (이메일 기반)
    - 사용자 계정 없이도 구독 가능: email 필수, user_id 선택
    """
    __tablename__ = 'newsletter_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    frequency = db.Column(db.String(20), default='daily')  # 'daily', 'weekly', 'monthly'
    send_time = db.Column(db.Time, default=datetime.strptime('09:00:00', '%H:%M:%S').time())
    include_charts = db.Column(db.Boolean, default=True)
    include_summary = db.Column(db.Boolean, default=True)
    include_technical_analysis = db.Column(db.Boolean, default=True)
    unsubscribe_token = db.Column(db.String(100), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정 (선택적)
    user = relationship('User', backref='newsletter_subscription', foreign_keys=[user_id])
    
    def __repr__(self):
        return f'<NewsletterSubscription {self.email} - {self.frequency}>'

class NewsletterContent(db.Model):
    """뉴스레터 내용 저장 모델"""
    __tablename__ = 'newsletter_contents'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    market_type = db.Column(db.String(10), nullable=False)  # 'KOSPI', 'KOSDAQ', 'US', 'COMBINED'
    primary_market = db.Column(db.String(10))  # 'KOSPI', 'KOSDAQ', 'US' (COMBINED인 경우)
    timeframe = db.Column(db.String(10), nullable=False)  # 'd', 'w', 'm'
    newsletter_type = db.Column(db.String(20), nullable=False)  # 'korean', 'us', 'combined', 'auto'
    html_content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 관계 설정
    user = relationship('User', backref='newsletter_contents')
    
    def __repr__(self):
        return f'<NewsletterContent {self.user_id} - {self.market_type} - {self.newsletter_type}>'

class EmailLog(db.Model):
    """이메일 발송 로그 모델"""
    __tablename__ = 'email_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    email_type = db.Column(db.String(50), nullable=False)  # 'newsletter', 'verification', etc.
    subject = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='sent')  # 'sent', 'failed'
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    error_message = db.Column(db.Text)
    
    # 관계 설정
    user = relationship('User', backref='email_logs')
    
    def __repr__(self):
        return f'<EmailLog {self.user_id} - {self.email_type} - {self.status}>'

class EmailMessage(db.Model):
    """SendGrid 이메일 발송 메시지 트래킹"""
    __tablename__ = 'email_messages'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    to = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    template = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')  # pending, sent, delivered, bounced, failed
    sendgrid_message_id = db.Column(db.String(255), index=True)
    attempt_count = db.Column(db.Integer, default=0)
    last_error = db.Column(db.Text)
    sent_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    idempotency_key = db.Column(db.String(100), unique=True)
    job_id = db.Column(db.String(100), index=True)
    newsletter_id = db.Column(db.Integer)
    edition_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    user = relationship('User', backref='email_messages')
    events = relationship('EmailEvent', back_populates='message', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<EmailMessage to={self.to} subject={self.subject} status={self.status}>'

class EmailEvent(db.Model):
    """SendGrid 이벤트 웹훅 수집"""
    __tablename__ = 'email_events'

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('email_messages.id'))
    event = db.Column(db.String(50), nullable=False)  # processed, delivered, open, click, bounce, spamreport, unsubscribe
    reason = db.Column(db.Text)
    sg_event_id = db.Column(db.String(255), unique=True)
    occurred_at = db.Column(db.DateTime, default=datetime.utcnow)
    raw_payload = db.Column(db.Text)

    # 관계
    message = relationship('EmailMessage', back_populates='events')

    def __repr__(self):
        return f'<EmailEvent {self.event} sg_event_id={self.sg_event_id}>'

class EmailSuppression(db.Model):
    """바운스/스팸 등 억제 리스트"""
    __tablename__ = 'email_suppressions'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    reason = db.Column(db.String(100))  # bounce, spamreport, unsubscribe
    detail = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<EmailSuppression {self.email} reason={self.reason}>'

# CSVUploadHistory 모델 주석 처리 (더 이상 사용하지 않음)
# class CSVUploadHistory(db.Model):
#     """CSV 업로드 히스토리"""
#     __tablename__ = 'csv_upload_history'
#     
#     id = db.Column(db.Integer, primary_key=True)
#     filename = db.Column(db.String(255), nullable=False)
#     market_type = db.Column(db.String(10), nullable=False)  # 'KOSPI', 'KOSDAQ', 'US'
#     market_subtype = db.Column(db.String(10))  # 'KOSPI', 'KOSDAQ' (한국인 경우), None (US인 경우)
#     stocks_count = db.Column(db.Integer, default=0)
#     success_count = db.Column(db.Integer, default=0)
#     error_count = db.Column(db.Integer, default=0)
#     uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
#     upload_status = db.Column(db.String(20), default='processing')  # 'processing', 'completed', 'failed'
#     error_message = db.Column(db.Text)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     
#     def __repr__(self):
#         return f'<CSVUpload {self.filename} - {self.market_type}>' 