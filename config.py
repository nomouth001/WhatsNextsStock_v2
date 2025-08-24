import os
from datetime import timedelta

class Config:
    """기본 설정"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///stock_newsletter.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 세션 설정
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # 파일 업로드 설정
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads'
    
    # 주식 데이터 디렉토리
    STOCK_LISTS_DIR = 'stock_lists'
    
    # 로깅 설정
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    
    # Google AI API 설정
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

    # 이메일/SendGrid 설정
    EMAIL_PROVIDER = os.environ.get('EMAIL_PROVIDER', 'sendgrid')
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    EMAIL_FROM_EMAIL = os.environ.get('SENDGRID_FROM_EMAIL') or os.environ.get('FROM_EMAIL')
    EMAIL_FROM_NAME = os.environ.get('SENDGRID_FROM_NAME', 'WhatsNextStock')
    EMAIL_REPLY_TO = os.environ.get('EMAIL_REPLY_TO') or EMAIL_FROM_EMAIL
    # 문자열 환경변수 기반 부울 처리
    SENDGRID_SANDBOX_MODE = str(os.environ.get('SENDGRID_SANDBOX_MODE', 'False')).lower() in ('1','true','yes')
    SENDGRID_EVENT_PUBLIC_KEY = os.environ.get('SENDGRID_EVENT_PUBLIC_KEY')

    # 퍼블릭 베이스 URL (절대 링크 생성용)
    # 운영 기본값: https://whatsnextstock.com
    PUBLIC_BASE_URL = os.environ.get('PUBLIC_BASE_URL', 'https://whatsnextstock.com')

class DevelopmentConfig(Config):
    """개발 환경 설정"""
    DEBUG = True

class ProductionConfig(Config):
    """운영 환경 설정"""
    DEBUG = False

# 기본 설정으로 개발 환경 사용
class DefaultConfig(DevelopmentConfig):
    pass

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DefaultConfig
}

# 현재 환경 설정
current_config = os.environ.get('FLASK_ENV', 'development') 