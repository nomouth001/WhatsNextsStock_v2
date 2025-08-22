# app.py - 메인 애플리케이션 파일

import logging
import os
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, session, flash, redirect, url_for, request, g, jsonify
from flask_login import LoginManager, current_user, login_required
from flask_migrate import Migrate
from config import DevelopmentConfig
from models import db, User, Stock
from dotenv import load_dotenv
from datetime import datetime

# 로그 디렉토리 생성
try:
    if not os.path.exists('logs'):
        os.makedirs('logs', exist_ok=True)
except Exception:
    pass

# 개선된 로깅 설정
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'encoding': 'utf-8'
        },
    },
    'handlers': {
        # 기존 RotatingFileHandler 설정은 보존
        # 'file': {
        #     'class': 'logging.handlers.RotatingFileHandler',
        #     'filename': 'logs/app.log',
        #     'maxBytes': 5 * 1024 * 1024,  # 5MB
        #     'backupCount': 5,
        #     'encoding': 'utf-8',
        #     'formatter': 'standard',
        #     'level': 'INFO'
        # },
        'file': {
            'class': 'concurrent_log_handler.ConcurrentRotatingFileHandler',
            'filename': 'logs/app.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'encoding': 'utf-8',
            'formatter': 'standard',
            'level': 'INFO',
            'mode': 'a',
            'delay': True
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'INFO'
        }
    },
    'loggers': {
        'yfinance': {
            'level': 'WARNING',  # DEBUG → WARNING으로 변경
            'handlers': ['file', 'console'],
            'propagate': False
        },
        'peewee': {
            'level': 'WARNING',  # DEBUG → WARNING으로 변경
            'handlers': ['file', 'console'],
            'propagate': False
        },
        'urllib3': {
            'level': 'WARNING',  # HTTP 요청 로그 제거
            'handlers': ['file', 'console'],
            'propagate': False
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file', 'console']
    }
}

# 로깅 설정 적용 (로깅 초기화 단일 진입점)
import logging.config
# 리로더 보조 프로세스에서 파일 핸들러 중복 생성 방지
_is_reloader_child = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
_is_debug = str(os.getenv('FLASK_DEBUG', '')).lower() in ('1', 'true')
if _is_reloader_child or not _is_debug:
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger(__name__)
    logger.info(f"FLASK_ENV={os.getenv('FLASK_ENV')} WERKZEUG_RUN_MAIN={os.getenv('WERKZEUG_RUN_MAIN')} PID={os.getpid()}")
else:
    # 리로더 부모 프로세스에서는 파일 핸들러 미설정
    logger = logging.getLogger(__name__)

# 메인 로거 설정
logger = logging.getLogger(__name__)

def create_app():
    """Flask 앱 팩토리 함수"""
    # .env 로드 (환경변수 미설정 시 .env 사용)
    try:
        load_dotenv()
    except Exception:
        pass
    app = Flask(__name__)
    
    # 설정 로드
    app.config.from_object(DevelopmentConfig)
    
    # 전역 템플릿 컨텍스트: now()
    @app.context_processor
    def _inject_now():
        return {'now': datetime.now}
    
    # 데이터베이스 초기화
    db.init_app(app)
    
    # 마이그레이션 초기화
    migrate = Migrate(app, db)
    
    # 로그인 매니저 설정
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '로그인이 필요합니다.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    # 애플리케이션 컨텍스트에서 테이블 생성
    with app.app_context():
        db.create_all()
        # DB 경로 및 활성 종목 카운트 로깅 (심층 추적)
        try:
            from sqlalchemy import text
            logger.info(f"DB_PATH={db.engine.url.database}")
            for m in ['US','KOSPI','KOSDAQ']:
                # 테이블명 수정: stock → stocks
                cnt = db.session.execute(text("SELECT COUNT(*) FROM stocks WHERE market_type=:m AND is_active=1"), {'m': m}).scalar()
                logger.info(f"ACTIVE_COUNT[{m}]={cnt}")
        except Exception as e:
            logger.warning(f"DB 상태 로깅 실패: {e}")
    
    # 라우트 등록
    from routes.auth_routes import auth_bp
    from routes.admin_routes import admin_bp
    from routes.stock_routes import stock_bp
    from routes.user_routes import user_bp
    from routes.analysis_routes import analysis_bp
    from routes.newsletter_routes import newsletter_bp
    from routes.webhook_routes import webhooks_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(stock_bp, url_prefix='/stock')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(analysis_bp, url_prefix='/analysis')
    app.register_blueprint(newsletter_bp, url_prefix='/newsletter')
    app.register_blueprint(webhooks_bp, url_prefix='/webhooks')
    
    # 스케줄러 시작 (리로더 보조 프로세스 중복 기동 방지)
    try:
        from services.core.scheduler_service import start_scheduler
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
            start_scheduler(app)
    except Exception as e:
        logger.warning(f"스케줄러 시작 실패(무시하고 계속): {e}")

    # 메인 라우트
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.is_admin:
                return redirect(url_for('admin.home'))
            else:
                return redirect(url_for('user.home'))
        return redirect(url_for('auth.login'))
    
    return app

# 앱 실행
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True) 