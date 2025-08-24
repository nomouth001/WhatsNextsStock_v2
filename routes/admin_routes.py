from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, Stock
from forms import CSVUploadForm
from services.core.unified_market_analysis_service import UnifiedMarketAnalysisService
# TODO: 2025-08-06 - NewsletterClassificationService는 UnifiedMarketAnalysisService로 대체되었으므로 주석 처리
# from services.newsletter_classification_service import NewsletterClassificationService
from datetime import datetime
import logging
from typing import Dict
# TODO: 2025-08-06 - 기본 지표 데이터 표시를 위해 TechnicalIndicatorsService와 DataReadingService 직접 사용
from services.technical_indicators_service import TechnicalIndicatorsService
from services.market.data_reading_service import DataReadingService
from services.market.market_data_orchestrator import MarketDataOrchestrator
from services.market.market_status_service import MarketStatusService
from services.market.file_management_service import FileManagementService
from services.analysis.crossover.detection import CrossoverDetector
from services.core.cache_service import CacheService
from services.core.email_service import EmailService
from services.newsletter_storage_service import NewsletterStorageService

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """관리자 권한 확인 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('관리자 권한이 필요합니다.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/home', methods=['GET'])
@login_required
@admin_required
def home():
    # 최소 변경: 완전한 컨텍스트를 구성하는 라우트로 리다이렉트
    return redirect(url_for('admin.home_with_market', market='us'))

    # MEMO: 아래는 기존 구현을 보존하기 위한 주석 처리된 코드입니다.
    # 향후 기존 방식으로 되돌리거나 일부 로직을 재사용해야 할 수 있으므로 삭제하지 않고 유지합니다.
    # --------------------------------------------------------------------------------
    # cache_service = CacheService()
    # cache_key = "admin_home_data"
    # cached_data = cache_service.get(cache_key)
    # if cached_data:
    #     # 캐시된 데이터에 upload_form 추가
    #     cached_data['upload_form'] = CSVUploadForm()
    #     try:
    #         logging.getLogger(__name__).info("render.context.keys.cached: %s", sorted(list(cached_data.keys())))
    #     except Exception:
    #         pass
    #     return render_template('admin/admin_home.html', **cached_data)
    # 
    # stocks = Stock.query.all()
    # stock_data = []
    # 
    # data_reader = DataReadingService()
    # indicator_service = TechnicalIndicatorsService()
    # crossover_detector = CrossoverDetector()
    # orchestrator = MarketDataOrchestrator()
    # 
    # for stock in stocks:
    #     # 없으면 다운로드, 있으면 기존 데이터 사용하도록 전체 워크플로우 실행
    #     result = orchestrator.process_stock_data_complete(stock.ticker, stock.market_type)
    #     if not result.success:
    #         continue
    # 
    #     ohlcv = data_reader.read_ohlcv_csv(stock.ticker, stock.market_type)
    #     if ohlcv.empty:
    #         continue
    # 
    #     latest_data = ohlcv.iloc[-1]
    #     indicators = indicator_service.read_indicators_csv(stock.ticker, stock.market_type)
    #     
    #     # SimplifiedCrossoverDetector를 사용한 실시간 크로스오버 분석
    #     cross_analysis = {}
    #     if not indicators.empty:
    #         cross_signals = crossover_detector.detect_all_signals(indicators)
    #         cross_analysis = {
    #             'ema_crossover_type': cross_signals.get('ema_analysis', {}).get('latest_crossover_type'),
    #             'ema_crossover_date': cross_signals.get('ema_analysis', {}).get('latest_crossover_date'),
    #             'ema_days_since': cross_signals.get('ema_analysis', {}).get('days_since_crossover'),
    #             'macd_crossover_type': cross_signals.get('macd_analysis', {}).get('latest_crossover_type'),
    #             'macd_crossover_date': cross_signals.get('macd_analysis', {}).get('latest_crossover_date'),
    #             'macd_days_since': cross_signals.get('macd_analysis', {}).get('days_since_crossover'),
    #             'ema_proximity': cross_signals.get('ema_analysis', {}).get('current_proximity'),
    #             'macd_proximity': cross_signals.get('macd_analysis', {}).get('current_proximity')
    #         }
    # 
    #     data = {
    #         'ticker': stock.ticker,
    #         'company_name': stock.company_name,
    #         'market_type': stock.market_type,
    #         'close': latest_data.get('Close', 0),
    #         'change': latest_data.get('Change', 0),
    #         'volume': latest_data.get('Volume', 0),
    #         'indicators': indicators.iloc[-1].to_dict() if not indicators.empty else {},
    #         'cross_info': cross_analysis
    #     }
    #     stock_data.append(data)
    # 
    # # 시장별 종목 수 계산
    # total_kospi_stocks = len([s for s in stock_data if s.get('market_type') == 'KOSPI'])
    # total_kosdaq_stocks = len([s for s in stock_data if s.get('market_type') == 'KOSDAQ'])
    # total_us_stocks = len([s for s in stock_data if s.get('market_type') == 'US'])
    # 
    # data_to_render = {
    #     "stocks": stock_data, 
    #     "upload_form": CSVUploadForm(),
    #     "total_kospi_stocks": total_kospi_stocks,
    #     "total_kosdaq_stocks": total_kosdaq_stocks,
    #     "total_us_stocks": total_us_stocks,
    #     "total_stocks": len(stock_data)
    # }
    # 
    # # 캐시 저장 시 wtforms 객체 제외 (pickle 오류 방지)
    # cache_data = {k: v for k, v in data_to_render.items() if k != 'upload_form'}
    # cache_service.set(cache_key, cache_data)
    # 
    # # 심층 추적: 템플릿 컨텍스트 키 로깅
    # try:
    #     logging.getLogger(__name__).info("render.context.keys: %s", sorted(list(data_to_render.keys())))
    # except Exception:
    #     pass
    # return render_template('admin/admin_home.html', **data_to_render)

@admin_bp.route('/home/<market>')
@login_required
@admin_required
def home_with_market(market='us'):
    """관리자 홈 페이지"""
    try:
        # market 파라미터 검증
        if market not in ['us', 'kospi', 'kosdaq']:
            market = 'us'
        
        # 시장별 설정
        market_type = 'US' if market == 'us' else 'KOSPI' if market == 'kospi' else 'KOSDAQ'
        market_name = '미국 주식 (US)' if market == 'us' else 'KOSPI' if market == 'kospi' else 'KOSDAQ'
        
        # 통계 데이터 수집
        total_users = User.query.filter_by(is_withdrawn=False).count()
        total_us_stocks = Stock.query.filter_by(market_type='US', is_active=True).count()
        total_kospi_stocks = Stock.query.filter_by(market_type='KOSPI', is_active=True).count()
        total_kosdaq_stocks = Stock.query.filter_by(market_type='KOSDAQ', is_active=True).count()
        
        # 현재 시장의 주식 목록 조회
        stocks = Stock.query.filter_by(market_type=market_type, is_active=True).all()
        
        if not stocks:
            # 최근 이메일/이벤트(간단 하이라이트) 추가 전달
            try:
                from models import EmailMessage, EmailEvent
                recent_email_messages = EmailMessage.query.order_by(EmailMessage.id.desc()).limit(20).all()
                recent_email_events = EmailEvent.query.order_by(EmailEvent.id.desc()).limit(20).all()
                try:
                    logging.info(
                        f"[ADMIN] recent counts (no-stocks branch): messages={len(recent_email_messages)}, events={len(recent_email_events)}"
                    )
                    if recent_email_messages:
                        m = recent_email_messages[0]
                        logging.info(
                            f"[ADMIN] recent message sample: id={getattr(m, 'id', None)}, to={getattr(m, 'to', None)}, subject={getattr(m, 'subject', None)}, status={getattr(m, 'status', None)}"
                        )
                except Exception:
                    pass
            except Exception:
                recent_email_messages, recent_email_events = [], []

            return render_template('admin/admin_home.html',
                                 title='관리자 홈',
                                 current_market=market,
                                 current_market_name=market_name,
                                 total_users=total_users,
                                 total_us_stocks=total_us_stocks,
                                 total_kospi_stocks=total_kospi_stocks,
                                 total_kosdaq_stocks=total_kosdaq_stocks,
                                 stocks=[],
                                 market_data={},
                                 indicators_data={},
                                 importance_scores={},
                                 market_summary={},
                                 multi_condition_counts={},
                                 display_date=datetime.now().strftime('%Y-%m-%d'),
                                 email_messages=recent_email_messages,
                                 email_events=recent_email_events)
        
        # 통합 서비스 사용하여 시장 분석
        unified_service = UnifiedMarketAnalysisService()
        
        # 데이터가 없는 경우를 대비해 먼저 데이터 다운로드 시도
        download_failed = False
        try:
            # 새로운 구조 사용: services/__init__.py의 래퍼 함수 사용
            from services import get_latest_ohlcv
            # 현재 시장의 주식 티커들
            tickers = [stock.ticker for stock in stocks]
            if tickers:
                # 데이터 다운로드 시도 (조용히 실패 허용)
                try:
                    # caller 인수 제거: 래퍼 시그니처는 (tickers, market_type)
                    results = get_latest_ohlcv(tickers, market_type)
                    # 성공 판단: 하나라도 close가 존재하면 성공으로 간주
                    try:
                        success_count = sum(1 for v in (results or {}).values() if v.get('close') is not None)
                    except Exception:
                        success_count = 0
                    if not results or success_count == 0:
                        download_failed = True
                        try:
                            flash('최신 주가 데이터 다운로드에 실패했습니다. 기존 저장 데이터를 표시합니다.', 'warning')
                        except Exception:
                            pass
                except Exception as e:
                    download_failed = True
                    logging.warning(f"데이터 다운로드 실패 (무시됨): {e}")
                    try:
                        flash('최신 주가 데이터 다운로드에 실패했습니다. 기존 저장 데이터를 표시합니다.', 'warning')
                    except Exception:
                        pass
        except Exception as e:
            logging.warning(f"데이터 다운로드 준비 실패 (무시됨): {e}")
            download_failed = True
            try:
                flash('최신 주가 데이터 다운로드에 실패했습니다. 기존 저장 데이터를 표시합니다.', 'warning')
            except Exception:
                pass
        
        # 2025-01-11: UMAS 결과를 먼저 생성하여 테이블 구성의 기반으로 사용
        # (이전에 비어있는 classification_results로 테이블을 만들어 공백이 발생했음)
        try:
            unified_result = unified_service.analyze_market_comprehensive(market, 'd')
            classification_results = unified_result.get('classification_results', {}) or {}
            market_summary = unified_result.get('summary', {}) or {}
        except Exception:
            classification_results = {}
            market_summary = {}

        # 템플릿용 기본 데이터 컨테이너 초기화
        ticker_results = {}
        market_data = {}
        indicators_data = {}
        importance_scores = {}
        display_date = datetime.now().strftime('%Y-%m-%d')

        # UMAS 분류 결과를 티커별로 재구성
        ticker_results = {}
        for cat, items in (classification_results or {}).items():
            if isinstance(items, list):
                for it in items:
                    t = it.get('ticker')
                    if t:
                        ticker_results[t] = it

        # UMAS 기반으로 테이블 데이터 구성 (필요 시 CSV 폴백 추가)
        for stock in stocks:
            ticker = stock.ticker
            it = ticker_results.get(ticker, {})
            latest = it.get('latest_data', {}) or {}
            cross = it.get('crossover_info', {}) or {}
            prox = it.get('proximity_info', {}) or {}
            macd = it.get('macd_analysis', {}) or {}

            # 폴백 1: UMAS latest_data가 비거나 핵심 키가 없으면 지표 CSV에서 최신행 보강
            if not latest or (not isinstance(latest, dict)) or (
                'EMA20' not in latest and 'EMA5' not in latest and 'Close' not in latest
            ):
                try:
                    indicator_service_fb = TechnicalIndicatorsService()
                    indicators_df_fb = indicator_service_fb.read_indicators_csv(ticker, market, 'd')
                    if indicators_df_fb is not None and not indicators_df_fb.empty:
                        latest = {**(latest or {}), **indicators_df_fb.iloc[-1].to_dict()}
                except Exception:
                    pass

            close_val = latest.get('Close', 0) or 0
            # [메모] 2025-08-19: 등락률 최신치 조회 경로 단일화
            # 기존 CSV 컬럼 직접 참조는 보존하되, 표준 함수 호출 결과를 우선 사용합니다.
            # 기존 코드:
            # change_pct = latest.get('Change_Percent', 0) or 0
            try:
                from services.technical_indicators_service import TechnicalIndicatorsService
                _tis_tmp = TechnicalIndicatorsService()
                change_pct = _tis_tmp.get_latest_change_percent(ticker, 'd', market_type)
            except Exception:
                change_pct = latest.get('Change_Percent', 0) or 0
            ema20 = latest.get('EMA20', 0) or 0
            ema40 = latest.get('EMA40', 0) or 0

            # 시장 데이터
            market_data[ticker] = {
                'close': close_val,
                'change_percent': change_pct,
                'volume': 0  # UMAS latest_data에는 Volume이 없으므로 0으로 표시
            }

            # 지표 데이터(최신행 그대로)
            indicators = {
                'ema5': latest.get('EMA5', 0),
                'ema20': ema20,
                'ema40': ema40,
                'macd_line': latest.get('MACD', 0),
                'macd_signal': latest.get('MACD_Signal', 0),
                'macd_histogram': latest.get('MACD_Histogram', 0),
                'rsi': latest.get('RSI', 0),
                'stoch_k': latest.get('Stoch_K', 0),
                'stoch_d': latest.get('Stoch_D', 0),
                'volume_ratio_5d': latest.get('Volume_Ratio_5d', 0),
                'volume_ratio_20d': latest.get('Volume_Ratio_20d', 0),
                'volume_ratio_40d': latest.get('Volume_Ratio_40d', 0),
                # [메모] 2025-08-19: 표시용 등락률은 표준 함수 결과 사용
                'change_percent': change_pct
            }

            # 분석 데이터(UMAS 신호에서 추출/계산)
            def _gap(close_v, ema_v):
                try:
                    if ema_v and isinstance(close_v, (int, float)) and isinstance(ema_v, (int, float)) and ema_v != 0:
                        return (close_v - ema_v) / ema_v * 100.0
                except Exception:
                    pass
                return 0

            analysis = {
                'ema_array_order': cross.get('ema_array_order', '분석불가'),
                'close_gap_ema20': _gap(close_val, ema20),
                'close_gap_ema40': _gap(close_val, ema40),
                'macd_signals': {
                    'latest_crossover_type': macd.get('latest_crossover_type'),
                    'latest_crossover_date': macd.get('latest_crossover_date'),
                    'days_since_crossover': macd.get('days_since_crossover'),
                    'proximity_type': (macd.get('current_proximity') if isinstance(macd, dict) else None) or prox.get('macd_proximity', 'no_proximity')
                },
                'ema_signals': {
                    'latest_crossover_type': cross.get('latest_crossover_type'),
                    'latest_crossover_date': cross.get('latest_crossover_date'),
                    'days_since_crossover': cross.get('days_since_crossover'),
                    'crossover_pair': cross.get('ema_pair'),
                    'proximity_type': prox.get('ema_proximity', 'no_proximity')
                }
            }

            # 폴백 2: 교차/근접 분석이 비어 있으면 CrossInfo CSV로 보강
            try:
                needs_fallback = not analysis.get('ema_array_order') or analysis.get('ema_array_order') == '분석불가'
                if needs_fallback:
                    from services.market.data_reading_service import DataReadingService as _DRS_FB
                    drs_fb = _DRS_FB()
                    crossinfo_df = drs_fb.read_crossinfo_csv(ticker, market)
                    if crossinfo_df is not None and not crossinfo_df.empty:
                        latest_cross = crossinfo_df.iloc[-1]
                        # MACD 근접 파싱 보조
                        def _parse_macd_proximity(val):
                            try:
                                if val is None:
                                    return 'no_proximity'
                                if isinstance(val, str) and val.strip().startswith('{'):
                                    import ast
                                    d = ast.literal_eval(val)
                                    if isinstance(d, dict):
                                        return d.get('type', 'no_proximity')
                                return str(val)
                            except Exception:
                                return 'no_proximity'
                        analysis = {
                            'ema_array_order': latest_cross.get('EMA_Array_Order', '분석불가'),
                            'close_gap_ema20': latest_cross.get('Close_Gap_EMA20', analysis.get('close_gap_ema20', 0.0)),
                            'close_gap_ema40': latest_cross.get('Close_Gap_EMA40', analysis.get('close_gap_ema40', 0.0)),
                            'macd_signals': {
                                'latest_crossover_type': latest_cross.get('MACD_Latest_Crossover_Type'),
                                'latest_crossover_date': latest_cross.get('MACD_Latest_Crossover_Date'),
                                'days_since_crossover': latest_cross.get('MACD_Days_Since_Crossover'),
                                'proximity_type': _parse_macd_proximity(latest_cross.get('MACD_Current_Proximity'))
                            },
                            'ema_signals': {
                                'latest_crossover_type': latest_cross.get('EMA_Latest_Crossover_Type'),
                                'latest_crossover_date': latest_cross.get('EMA_Latest_Crossover_Date'),
                                'days_since_crossover': latest_cross.get('EMA_Days_Since_Crossover'),
                                'crossover_pair': latest_cross.get('EMA_Crossover_Pair'),
                                'proximity_type': latest_cross.get('EMA_Current_Proximity', 'no_proximity')
                            }
                        }
            except Exception:
                pass

            indicators_data[ticker] = {
                'indicators': indicators,
                'analysis': analysis
            }

            importance_scores[ticker] = it.get('importance_score', 0) or 0

        # 표시 날짜는 오늘로 유지 (UMAS 캐시 시 생성시간 표시는 summary.generated_at 이용 가능)
        
        # TODO: 2025-08-06 - 기존 코드 주석 처리 (위에서 새로운 방식으로 대체됨)
        # # 시장 데이터와 지표 데이터를 ticker_results에서 추출
        # market_data = {}
        # indicators_data = {}
        # importance_scores = {}
        # 
        # # 각 주식별로 데이터 처리
        # for stock in stocks:
        #     ticker = stock.ticker
        #     if ticker in ticker_results:
        #         stock_result = ticker_results[ticker]
        #         
        #         # 시장 데이터 (OHLCV)
        #         if 'latest_data' in stock_result:
        #             latest_data = stock_result['latest_data']
        #             market_data[ticker] = {
        #                 'close': latest_data.get('Close', 0),
        #                 'change_percent': latest_data.get('change_percent', 0),
        #                 'volume': latest_data.get('Volume', 0)
        #             }
        #         
        #         # 지표 데이터
        #         indicators_data[ticker] = {
        #             'indicators': {
        #                 'ema5': latest_data.get('EMA5', 0),
        #                 'ema20': latest_data.get('EMA20', 0),
        #                 'ema40': latest_data.get('EMA40', 0),
        #                 'macd_line': latest_data.get('MACD', 0),
        #                 'macd_signal': latest_data.get('MACD_signal', 0),
        #                 'macd_histogram': latest_data.get('MACD_histogram', 0),
        #                 'rsi': latest_data.get('RSI', 0),
        #                 'stoch_k': latest_data.get('Stoch_K', 0),
        #                 'stoch_d': latest_data.get('Stoch_D', 0),
        #                 'volume_ratio_5d': latest_data.get('volume_ratio_5d', 0),
        #                 'volume_ratio_20d': latest_data.get('volume_ratio_20d', 0),
        #                 'volume_ratio_40d': latest_data.get('volume_ratio_40d', 0)
        #             },
        #             'analysis': {
        #                 'macd_signals': stock_result.get('crossover_info', {}),
        #                 'ema_signals': stock_result.get('proximity_info', {}),
        #                 'gap_ema20': latest_data.get('gap_ema20', 0),
        #                 'gap_ema40': latest_data.get('gap_ema40', 0),
        #                 'ema_array': {
        #                     'full_array': latest_data.get('ema_array', '')
        #                 }
        #             }
        #         }
        #         
        #         # 중요도 점수
        #         importance_scores[ticker] = stock_result.get('importance_score', 0)
        #     else:
        #         # 데이터가 없는 경우 기본값 설정
        #         market_data[ticker] = {'close': 0, 'change_percent': 0, 'volume': 0}
        #         indicators_data[ticker] = {
        #             'indicators': {
        #                 'ema5': 0, 'ema20': 0, 'ema40': 0,
        #                 'macd_line': 0, 'macd_signal': 0, 'macd_histogram': 0,
        #                 'rsi': 0, 'stoch_k': 0, 'stoch_d': 0,
        #                 'volume_ratio_5d': 0, 'volume_ratio_20d': 0, 'volume_ratio_40d': 0
        #             },
        #             'analysis': {
        #                 'macd_signals': {}, 'ema_signals': {},
        #                 'gap_ema20': 0, 'gap_ema40': 0,
        #                 'ema_array': {'full_array': ''}
        #             }
        #         }
        #         importance_scores[ticker] = 0
        
        # 표시할 데이터 날짜 계산 (UMAS 기반: 당일 표기)
        display_date = datetime.now().strftime('%Y-%m-%d')
        
        # 2025-01-11: 중복 분류 로직 제거 완료
        # UnifiedMarketAnalysisService에서 이미 올바른 classification_results와 market_summary 생성됨
        # 아래 직접 구현/재호출 로직은 제거하여 덮어쓰기를 방지
        
        # 2025-01-11: 검증된 admin API 패턴 적용
        logging.info(f"현재 시장 {market_type}에 {len(stocks)}개 종목 확인됨")
        
        # 최근 이메일/이벤트(간단 하이라이트)
        try:
            from models import EmailMessage, EmailEvent
            recent_email_messages = EmailMessage.query.order_by(EmailMessage.id.desc()).limit(20).all()
            recent_email_events = EmailEvent.query.order_by(EmailEvent.id.desc()).limit(20).all()
            try:
                logging.info(
                    f"[ADMIN] recent counts: messages={len(recent_email_messages)}, events={len(recent_email_events)}"
                )
                if recent_email_messages:
                    m = recent_email_messages[0]
                    logging.info(
                        f"[ADMIN] recent message sample: id={getattr(m, 'id', None)}, to={getattr(m, 'to', None)}, subject={getattr(m, 'subject', None)}, status={getattr(m, 'status', None)}"
                    )
            except Exception:
                pass
        except Exception:
            recent_email_messages, recent_email_events = [], []

        # 8개 다중 조건 카운트 계산 (현재 시장 종목만 필터)
        multi_condition_counts = {}
        try:
            from services.newsletter_classification_service import NewsletterClassificationService
            svc = NewsletterClassificationService()
            # 현재 시장만 스캔하여 I/O와 로그 축소
            lists = svc.get_multi_condition_stock_lists('d', market)
            current_tickers = {s.ticker for s in stocks}
            # 키 목록 고정
            keys = [
                'uptrend_macd_dead_cross_within_3d',
                'uptrend_ema_dead1_proximity',
                'uptrend_ema_dead1_today',
                'uptrend_ema_dead1_within_3d',
                'downtrend_macd_golden_cross_within_3d',
                'downtrend_ema_golden1_proximity',
                'downtrend_ema_golden1_today',
                'downtrend_ema_golden_within_3d'
            ]
            for k in keys:
                items = lists.get(k, []) or []
                multi_condition_counts[k] = sum(1 for it in items if it.get('ticker') in current_tickers)
        except Exception as e:
            logging.warning(f"다중 조건 카운트 계산 실패: {e}")
            multi_condition_counts = {}

        return render_template('admin/admin_home.html',
                             title='관리자 홈',
                             current_market=market,
                             current_market_name=market_name,
                             total_users=total_users,
                             total_us_stocks=total_us_stocks,
                             total_kospi_stocks=total_kospi_stocks,
                             total_kosdaq_stocks=total_kosdaq_stocks,
                             market_summary=market_summary,
                             stocks=stocks,
                             market_data=market_data,
                             indicators_data=indicators_data,
                             importance_scores=importance_scores,
                             multi_condition_counts=multi_condition_counts,
                             display_date=display_date,
                             email_messages=recent_email_messages,
                             email_events=recent_email_events)
                             
    except Exception as e:
        logging.error(f"관리자 홈페이지 오류: {e}")
        return render_template('error.html', error="데이터 로딩 중 오류가 발생했습니다.")

@admin_bp.route('/refresh_market_data', methods=['POST'])
@login_required
@admin_required
def refresh_market_data():
    try:
        # 한국/미국 주식 가져오기
        kospi_stocks = Stock.query.filter_by(market_type='KOSPI', is_active=True).all()
        kosdaq_stocks = Stock.query.filter_by(market_type='KOSDAQ', is_active=True).all()
        us_stocks = Stock.query.filter_by(market_type='US', is_active=True).all()
        
        # 시장별 데이터 갱신 (타임필터링 완전 제거)
        orchestrator = MarketDataOrchestrator()
        
        # 한국 주식 갱신 - KOSPI
        for stock in kospi_stocks:
            orchestrator.process_stock_data_complete(stock.ticker, 'KOSPI')
        
        # 한국 주식 갱신 - KOSDAQ  
        for stock in kosdaq_stocks:
            orchestrator.process_stock_data_complete(stock.ticker, 'KOSDAQ')
        
        # 미국 주식 갱신
        for stock in us_stocks:
            orchestrator.process_stock_data_complete(stock.ticker, 'US')
        
        # 갱신 후 데이터 다시 불러오기
        kospi_tickers = [stock.ticker for stock in kospi_stocks]
        kosdaq_tickers = [stock.ticker for stock in kosdaq_stocks]
        us_tickers = [stock.ticker for stock in us_stocks]
        
        # 최신 데이터 확인
        from services.market.data_reading_service import DataReadingService
        data_reading_service = DataReadingService()
        
        if kospi_tickers:
            data_reading_service.get_latest_ohlcv(kospi_tickers, 'KOSPI', caller='admin.refresh_market_data')
        if kosdaq_tickers:
            data_reading_service.get_latest_ohlcv(kosdaq_tickers, 'KOSDAQ', caller='admin.refresh_market_data')
        if us_tickers:
            data_reading_service.get_latest_ohlcv(us_tickers, 'US', caller='admin.refresh_market_data')
        
        return jsonify({'success': True, 'message': '주가 데이터가 성공적으로 갱신되었습니다.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """사용자 관리 페이지"""
    users = User.query.filter_by(is_withdrawn=False).all()
    return render_template('admin/users.html', title='사용자 관리', users=users)

@admin_bp.route('/delete-stocks', methods=['POST'])
@login_required
@admin_required
def delete_stocks():
    """선택된 주식들 삭제"""
    try:
        stock_ids = request.json.get('stock_ids', [])
        if not stock_ids:
            return jsonify({'success': False, 'message': '삭제할 주식을 선택해주세요.'})
        
        # 선택된 주식들을 비활성화
        stocks = Stock.query.filter(Stock.id.in_(stock_ids)).all()
        deleted_count = 0
        
        for stock in stocks:
            stock.is_active = False
            deleted_count += 1
        
        db.session.commit()
        # 캐시 무효화 및 상세 로깅
        try:
            CacheService().delete('admin_home_data')
            logging.info(f"[ADMIN.DELETE] 비활성화 {deleted_count}건, 캐시 무효화 완료: admin_home_data")
            logging.info(f"[ADMIN.DELETE] 티커: {[s.ticker for s in stocks]}")
        except Exception as e:
            logging.warning(f"[ADMIN.DELETE] 캐시 무효화 실패: {e}")
        
        return jsonify({
            'success': True, 
            'message': f'{deleted_count}개의 주식이 삭제되었습니다.'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'삭제 중 오류 발생: {str(e)}'})

@admin_bp.route('/download-stocks/<market_type>')
@login_required
@admin_required
def download_stocks(market_type):
    """주식 리스트 CSV 다운로드"""
    try:
        from flask import make_response
        import io
        import csv
        
        if market_type not in ['KOSPI', 'KOSDAQ', 'US']:
            flash('잘못된 시장 타입입니다.', 'error')
            return redirect(url_for('admin.home'))
        
        # 해당 시장의 활성화된 주식들 조회
        stocks = Stock.query.filter_by(
            market_type=market_type, 
            is_active=True
        ).order_by(Stock.ticker).all()
        
        # CSV 생성
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 헤더 작성
        writer.writerow(['ticker', 'company_name'])
        
        # 데이터 작성
        for stock in stocks:
            writer.writerow([stock.ticker, stock.company_name or ''])
        
        # 응답 생성
        response_data = output.getvalue()
        output.close()
        
        response = make_response(response_data)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename={market_type}_stocks.csv'
        
        return response
        
    except Exception as e:
        flash(f'다운로드 중 오류 발생: {str(e)}', 'error')
        return redirect(url_for('admin.home')) 

# 신규 기능: 화면의 전체 테이블을 CSV로 다운로드하는 엔드포인트 추가
# - 변경 기록: 2025-08-16, admin_home의 마켓 테이블 전체(행/컬럼) CSV 다운로드 지원
# - 주의: 화면 표 생성과 동일한 로직을 최대한 재사용하여 컬럼/값 불일치 방지
@admin_bp.route('/download-market-table/<market>')
@login_required
@admin_required
def download_market_table(market: str):
    """현재 admin 홈의 시장 테이블 전체를 CSV로 다운로드"""
    try:
        # 1) 파라미터 검증 및 시장 지정
        if market not in ['us', 'kospi', 'kosdaq']:
            market = 'us'
        market_type = 'US' if market == 'us' else 'KOSPI' if market == 'kospi' else 'KOSDAQ'

        # 2) 활성 종목 조회
        stocks = Stock.query.filter_by(market_type=market_type, is_active=True).order_by(Stock.ticker).all()

        # 3) 데이터 조립 (화면 표 생성 로직과 동일한 소스 재사용)
        from services.market.data_reading_service import DataReadingService
        from services.technical_indicators_service import TechnicalIndicatorsService
        data_reading_service = DataReadingService()
        technical_service = TechnicalIndicatorsService()

        # CrossInfo 파싱 보조 함수 (화면 로직과 동일)
        def parse_macd_proximity(proximity_value):
            if not proximity_value or proximity_value == 'no_proximity':
                return 'no_proximity'
            if isinstance(proximity_value, str) and proximity_value.startswith('{'):
                try:
                    import ast
                    proximity_dict = ast.literal_eval(proximity_value)
                    if isinstance(proximity_dict, dict):
                        return proximity_dict.get('type', 'no_proximity')
                except Exception:
                    pass
            return str(proximity_value)

        rows = []
        from datetime import datetime
        display_date = datetime.now().strftime('%Y-%m-%d')

        for stock in stocks:
            ticker = stock.ticker
            try:
                # OHLCV / Indicators 로드 (일봉)
                ohlcv_df = data_reading_service.read_ohlcv_csv(ticker, market, 'd')
                indicators_df = technical_service.read_indicators_csv(ticker, market, 'd')

                latest_ohlcv = ohlcv_df.iloc[-1] if not ohlcv_df.empty else None
                latest_ind = indicators_df.iloc[-1] if not indicators_df.empty else None

                # CrossInfo 로드 및 analysis 파생값 구성
                analysis = {}
                try:
                    crossinfo_df = data_reading_service.read_crossinfo_csv(ticker, market)
                    if not crossinfo_df.empty:
                        latest_cross = crossinfo_df.iloc[-1]
                        analysis.update({
                            'ema_array_order': latest_cross.get('EMA_Array_Order', '분석불가'),
                            'close_gap_ema20': latest_cross.get('Close_Gap_EMA20', 0.0),
                            'close_gap_ema40': latest_cross.get('Close_Gap_EMA40', 0.0),
                            'macd_signals': {
                                'latest_crossover_type': latest_cross.get('MACD_Latest_Crossover_Type'),
                                'latest_crossover_date': latest_cross.get('MACD_Latest_Crossover_Date'),
                                'days_since_crossover': latest_cross.get('MACD_Days_Since_Crossover'),
                                'proximity_type': parse_macd_proximity(latest_cross.get('MACD_Current_Proximity'))
                            },
                            'ema_signals': {
                                'latest_crossover_type': latest_cross.get('EMA_Latest_Crossover_Type'),
                                'latest_crossover_date': latest_cross.get('EMA_Latest_Crossover_Date'),
                                'days_since_crossover': latest_cross.get('EMA_Days_Since_Crossover'),
                                'crossover_pair': latest_cross.get('EMA_Crossover_Pair'),
                                'proximity_type': latest_cross.get('EMA_Current_Proximity', 'no_proximity')
                            }
                        })
                except Exception:
                    pass

                # CSV 한 행 구성 - 화면 컬럼과 동등한 정보
                # 변경 기록(2025-08-16): MACD/EMA 근접 컬럼을 분리하여 추가 (표와 동일한 개념)
                macd_proximity_type = analysis.get('macd_signals', {}).get('proximity_type', '')
                ema_proximity_type = analysis.get('ema_signals', {}).get('proximity_type', '')
                # [메모] 2025-08-19: 등락률 최신치 조회 경로 단일화
                # 기존 CSV 컬럼 직접 참조를 보존하되, 표준 함수 호출 결과를 우선 사용합니다.
                try:
                    from services.technical_indicators_service import TechnicalIndicatorsService
                    _tis_tmp = TechnicalIndicatorsService()
                    dl_change_pct = _tis_tmp.get_latest_change_percent(ticker, 'd', market_type)
                except Exception:
                    dl_change_pct = (float(latest_ind.get('Change_Percent')) if latest_ind is not None and 'Change_Percent' in latest_ind else '')

                row = {
                    'ticker': ticker,
                    'company_name': stock.company_name or '',
                    'close': (float(latest_ohlcv.get('Close')) if latest_ohlcv is not None and 'Close' in latest_ohlcv else ''),
                    # 기존 코드:
                    # 'change_percent': (float(latest_ind.get('Change_Percent')) if latest_ind is not None and 'Change_Percent' in latest_ind else ''),
                    # 표준 함수 결과 우선 적용
                    'change_percent': dl_change_pct,
                    'importance_score': 0,
                    'macd_latest_crossover_type': analysis.get('macd_signals', {}).get('latest_crossover_type', ''),
                    'macd_latest_crossover_date': analysis.get('macd_signals', {}).get('latest_crossover_date', ''),
                    'macd_days_since_crossover': analysis.get('macd_signals', {}).get('days_since_crossover', ''),
                    'ema_latest_crossover_type': analysis.get('ema_signals', {}).get('latest_crossover_type', ''),
                    'ema_crossover_pair': analysis.get('ema_signals', {}).get('crossover_pair', ''),
                    'ema_latest_crossover_date': analysis.get('ema_signals', {}).get('latest_crossover_date', ''),
                    'ema_days_since_crossover': analysis.get('ema_signals', {}).get('days_since_crossover', ''),
                    'ema_array_order': analysis.get('ema_array_order', ''),
                    'macd_proximity_type': macd_proximity_type,
                    'ema_proximity_type': ema_proximity_type,
                    'close_gap_ema20': analysis.get('close_gap_ema20', ''),
                    'close_gap_ema40': analysis.get('close_gap_ema40', ''),
                    'ema5': (float(latest_ind.get('EMA5')) if latest_ind is not None and 'EMA5' in latest_ind else ''),
                    'ema20': (float(latest_ind.get('EMA20')) if latest_ind is not None and 'EMA20' in latest_ind else ''),
                    'ema40': (float(latest_ind.get('EMA40')) if latest_ind is not None and 'EMA40' in latest_ind else ''),
                    'macd_line': (float(latest_ind.get('MACD')) if latest_ind is not None and 'MACD' in latest_ind else ''),
                    'macd_signal': (float(latest_ind.get('MACD_Signal')) if latest_ind is not None and 'MACD_Signal' in latest_ind else ''),
                    'macd_histogram': (float(latest_ind.get('MACD_Histogram')) if latest_ind is not None and 'MACD_Histogram' in latest_ind else ''),
                    'rsi': (float(latest_ind.get('RSI')) if latest_ind is not None and 'RSI' in latest_ind else ''),
                    'stoch_k': (float(latest_ind.get('Stoch_K')) if latest_ind is not None and 'Stoch_K' in latest_ind else ''),
                    'stoch_d': (float(latest_ind.get('Stoch_D')) if latest_ind is not None and 'Stoch_D' in latest_ind else ''),
                    'volume_ratio_5d': (float(latest_ind.get('Volume_Ratio_5d')) if latest_ind is not None and 'Volume_Ratio_5d' in latest_ind else ''),
                    'volume_ratio_20d': (float(latest_ind.get('Volume_Ratio_20d')) if latest_ind is not None and 'Volume_Ratio_20d' in latest_ind else ''),
                    'volume_ratio_40d': (float(latest_ind.get('Volume_Ratio_40d')) if latest_ind is not None and 'Volume_Ratio_40d' in latest_ind else ''),
                    'as_of_date': display_date
                }
                rows.append(row)

            except Exception as e:
                logging.error(f"[DOWNLOAD-MARKET-TABLE] {ticker} 처리 실패: {e}")
                # 실패 시에도 최소 식별 정보는 기록
                rows.append({'ticker': ticker, 'company_name': stock.company_name or '', 'as_of_date': display_date})

        # 4) CSV 생성 (화면 컬럼 순서를 반영)
        from flask import make_response
        import io
        import csv
        output = io.StringIO()
        writer = csv.writer(output)

        headers = [
            'ticker','company_name','close','change_percent','importance_score',
            'macd_latest_crossover_type','macd_latest_crossover_date','macd_days_since_crossover',
            'ema_latest_crossover_type','ema_crossover_pair','ema_latest_crossover_date','ema_days_since_crossover',
            'ema_array_order','macd_proximity_type','ema_proximity_type','close_gap_ema20','close_gap_ema40',
            'ema5','ema20','ema40','macd_line','macd_signal','macd_histogram','rsi','stoch_k','stoch_d',
            'volume_ratio_5d','volume_ratio_20d','volume_ratio_40d',
            'as_of_date'
        ]
        writer.writerow(headers)
        for r in rows:
            writer.writerow([r.get(h, '') for h in headers])

        response_data = output.getvalue()
        output.close()

        # BOM 추가로 엑셀 호환성 확보
        response = make_response('\ufeff' + response_data)
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        response.headers['Content-Disposition'] = f'attachment; filename=market_table_{market}_{ts}.csv'
        return response

    except Exception as e:
        logging.error(f"테이블 CSV 다운로드 중 오류: {e}")
        flash(f'다운로드 중 오류 발생: {str(e)}', 'error')
        return redirect(url_for('admin.home'))

@admin_bp.route('/force_data_download', methods=['POST'])
@login_required
@admin_required
def force_data_download():
    """강제 데이터 다운로드 - 어드민 전용 (개선된 시간대별 전략 적용)"""
    try:
        # 현재 시간 정보 가져오기
        from services.market.market_status_service import MarketStatusService
        from services.market.data_reading_service import DataReadingService
        market_status_service = MarketStatusService()
        data_reading_service = DataReadingService()
        time_info = market_status_service.get_current_time_info()
        
        # 활성화된 모든 주식의 티커 수집
        kospi_stocks = Stock.query.filter_by(market_type='KOSPI', is_active=True).all()
        kosdaq_stocks = Stock.query.filter_by(market_type='KOSDAQ', is_active=True).all()
        us_stocks = Stock.query.filter_by(market_type='US', is_active=True).all()
        
        kospi_tickers = [stock.ticker for stock in kospi_stocks]
        kosdaq_tickers = [stock.ticker for stock in kosdaq_stocks]
        us_tickers = [stock.ticker for stock in us_stocks]
        
        logging.info(f"[ADMIN] === 강제 데이터 다운로드 시작 ===")
        logging.info(f"[ADMIN] 실행자: {current_user.username}")
        
        # time_info가 비어있거나 키가 없는 경우 처리
        if not time_info:
            logging.error("[ADMIN] 시간 정보를 가져올 수 없음")
            return jsonify({'success': False, 'message': '시간 정보를 가져올 수 없습니다.'})
        
        # 한국 시장용 시간 정보
        kst_time_str = time_info.get('kst_str', time_info.get('kst_time', 'N/A'))
        logging.info(f"[ADMIN] 현재 KST: {kst_time_str}")
        
        # 미국 시장용 시간 정보  
        est_time_str = time_info.get('est_str', time_info.get('est_time', 'N/A'))
        logging.info(f"[ADMIN] 현재 EST: {est_time_str}")
        
        logging.info(f"[ADMIN] KOSPI 종목 수: {len(kospi_tickers)}")
        logging.info(f"[ADMIN] KOSDAQ 종목 수: {len(kosdaq_tickers)}")
        logging.info(f"[ADMIN] US 종목 수: {len(us_tickers)}")
        
        # 시장 상태 확인
        kospi_market_status = market_status_service.get_market_status_info_improved('KOSPI')
        kosdaq_market_status = market_status_service.get_market_status_info_improved('KOSDAQ')
        us_market_status = market_status_service.get_market_status_info_improved('US')
        
        logging.info(f"[ADMIN] KOSPI 상태: {kospi_market_status['market_name']} - {kospi_market_status['status']}")
        logging.info(f"[ADMIN] KOSDAQ 상태: {kosdaq_market_status['market_name']} - {kosdaq_market_status['status']}")
        logging.info(f"[ADMIN] 미국장 상태: {us_market_status['market_name']} - {us_market_status['status']}")
        
        results = {}
        total_processed = 0
        
        # KOSPI 주식 다운로드
        if kospi_tickers:
            logging.info(f"[ADMIN] === KOSPI 주식 데이터 다운로드 시작 ===")
            logging.info(f"[ADMIN] KOSPI 주식 티커 (처음 10개): {kospi_tickers[:10]}")
            from services import get_latest_ohlcv as download_ohlcv
            kospi_results = download_ohlcv(kospi_tickers, 'KOSPI', caller='admin.force_data_download')
            results['KOSPI'] = kospi_results
            total_processed += len(kospi_tickers)
            
            # 결과 요약 로깅
            kospi_success = sum(1 for data in kospi_results.values() if data.get('close') is not None)
            kospi_fail = len(kospi_tickers) - kospi_success
            logging.info(f"[ADMIN] KOSPI 주식 다운로드 완료: 성공 {kospi_success}, 실패 {kospi_fail}")
            
            # 샘플 데이터 로깅
            if kospi_results:
                sample_ticker = list(kospi_results.keys())[0]
                sample_data = kospi_results[sample_ticker]
                if sample_data.get('close') is not None:
                    logging.info(f"[ADMIN] KOSPI 주식 샘플 데이터 ({sample_ticker}): 종가={sample_data.get('close')}, 최신날짜={sample_data.get('latest_date')}, 전략={sample_data.get('strategy_reason')}")
        
        # KOSDAQ 주식 다운로드
        if kosdaq_tickers:
            logging.info(f"[ADMIN] === KOSDAQ 주식 데이터 다운로드 시작 ===")
            logging.info(f"[ADMIN] KOSDAQ 주식 티커 (처음 10개): {kosdaq_tickers[:10]}")
            kosdaq_results = download_ohlcv(kosdaq_tickers, 'KOSDAQ', caller='admin.force_data_download')
            results['KOSDAQ'] = kosdaq_results
            total_processed += len(kosdaq_tickers)
            
            # 결과 요약 로깅
            kosdaq_success = sum(1 for data in kosdaq_results.values() if data.get('close') is not None)
            kosdaq_fail = len(kosdaq_tickers) - kosdaq_success
            logging.info(f"[ADMIN] KOSDAQ 주식 다운로드 완료: 성공 {kosdaq_success}, 실패 {kosdaq_fail}")
            
            # 샘플 데이터 로깅
            if kosdaq_results:
                sample_ticker = list(kosdaq_results.keys())[0]
                sample_data = kosdaq_results[sample_ticker]
                if sample_data.get('close') is not None:
                    logging.info(f"[ADMIN] KOSDAQ 주식 샘플 데이터 ({sample_ticker}): 종가={sample_data.get('close')}, 최신날짜={sample_data.get('latest_date')}, 전략={sample_data.get('strategy_reason')}")
        
        # 미국 주식 다운로드  
        if us_tickers:
            logging.info(f"[ADMIN] === 미국 주식 데이터 다운로드 시작 ===")
            logging.info(f"[ADMIN] 미국 주식 티커 (처음 10개): {us_tickers[:10]}")
            us_results = download_ohlcv(us_tickers, 'US', caller='admin.force_data_download')
            results['US'] = us_results
            total_processed += len(us_tickers)
            
            # 결과 요약 로깅
            us_success = sum(1 for data in us_results.values() if data.get('close') is not None)
            us_fail = len(us_tickers) - us_success
            logging.info(f"[ADMIN] 미국 주식 다운로드 완료: 성공 {us_success}, 실패 {us_fail}")
            
            # 샘플 데이터 로깅
            if us_results:
                sample_ticker = list(us_results.keys())[0]
                sample_data = us_results[sample_ticker]
                if sample_data.get('close') is not None:
                    logging.info(f"[ADMIN] 미국 주식 샘플 데이터 ({sample_ticker}): 종가={sample_data.get('close')}, 최신날짜={sample_data.get('latest_date')}, 전략={sample_data.get('strategy_reason')}")
        
        # 전체 성공/실패 카운트
        success_count = 0
        fail_count = 0
        
        for market_results in results.values():
            for ticker_data in market_results.values():
                if ticker_data.get('close') is not None:
                    success_count += 1
                else:
                    fail_count += 1
        
        logging.info(f"[ADMIN] === 강제 데이터 다운로드 완료 ===")
        logging.info(f"[ADMIN] 전체 처리: {total_processed}, 성공: {success_count}, 실패: {fail_count}")
        
        return jsonify({
            'success': True, 
            'message': f'강제 데이터 다운로드 완료. 성공: {success_count}, 실패: {fail_count}',
            'results': {
                'total_processed': total_processed,
                'success_count': success_count,
                'fail_count': fail_count,
                'time_info': {
                    'kst_time': kst_time_str,
                    'est_time': est_time_str,
                    'kospi_market_status': kospi_market_status['status'],
                    'kosdaq_market_status': kosdaq_market_status['status'],
                    'us_market_status': us_market_status['status']
                }
            }
        })
        
    except Exception as e:
        logging.error(f"[ADMIN] 강제 데이터 다운로드 오류: {e}")
        import traceback
        logging.error(f"[ADMIN] 스택 트레이스: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'오류 발생: {str(e)}'})


# === 이메일 테스트 발송 엔드포인트 ===
@admin_bp.route('/email/test_send', methods=['POST'])
@login_required
@admin_required
def email_test_send():
    try:
        data = request.get_json(force=True)
        to_email = data.get('to_email')
        subject = data.get('subject')
        html = data.get('html')
        if not to_email or not subject or not html:
            return jsonify({'success': False, 'message': '필수 필드(to_email, subject, html)가 누락되었습니다.'})

        email_service = EmailService()
        result = email_service.send_html_email(to_email=to_email, subject=subject, html=html, categories=['admin_test'])

        status = result.get('status_code')
        if status in (200, 202):
            # EmailLog에 기록 (EmailMessage 생성은 EmailService 내부에서 수행됨)
            try:
                from models import EmailLog
                log = EmailLog(user_id=current_user.id, email_type='newsletter', subject=subject, status='sent')
                db.session.add(log)
                db.session.commit()
            except Exception as e:
                logging.warning(f"EmailLog 기록 실패: {e}")
            return jsonify({'success': True, 'message': f'발송 성공 (status={status})'})
        else:
            err = result.get('error')
            try:
                from models import EmailLog
                log = EmailLog(user_id=current_user.id, email_type='newsletter', subject=subject, status='failed', error_message=str(err))
                db.session.add(log)
                db.session.commit()
            except Exception as e:
                logging.warning(f"EmailLog 기록 실패: {e}")
            return jsonify({'success': False, 'message': f'발송 실패 (status={status}) - {err}'})
    except Exception as e:
        logging.error(f"이메일 테스트 발송 오류: {e}")
        return jsonify({'success': False, 'message': str(e)})


# === 이메일 벌크 발송(동기 배치, 지수 백오프 재시도) ===
@admin_bp.route('/email/bulk_send', methods=['POST'])
@login_required
@admin_required
def email_bulk_send():
    try:
        data = request.get_json(force=True)
        recipients = data.get('recipients', [])  # [{email: ...}]
        subject = data.get('subject')
        html = data.get('html')
        if not recipients or not subject or not html:
            return jsonify({'success': False, 'message': 'recipients/subject/html 필요'}), 400

        email_service = EmailService()
        summary = email_service.send_bulk_html(recipients, subject, html)
        return jsonify({'success': True, 'summary': summary})
    except Exception as e:
        logging.error(f"이메일 벌크 발송 오류: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# === 뉴스레터: 저장된 콘텐츠 시험 발송 ===
@admin_bp.route('/newsletter/test_send', methods=['POST'])
@login_required
@admin_required
def newsletter_test_send():
    try:
        from models import db, NewsletterContent, EmailLog, EmailMessage, NewsletterSubscription
        data = request.get_json(force=True)
        newsletter_id = data.get('newsletter_id')
        to_email = data.get('to_email')
        subject = data.get('subject')
        recipient_name = data.get('recipient_name') or current_user.get_full_name()
        if not (newsletter_id and to_email and subject):
            return jsonify({'success': False, 'message': 'newsletter_id/to_email/subject 필요'}), 400

        content = NewsletterContent.query.filter_by(id=newsletter_id).first()
        if not content:
            return jsonify({'success': False, 'message': '뉴스레터 콘텐츠를 찾을 수 없습니다.'}), 404

        # 구독자 토큰으로 개인화된 unsubscribe 링크 시도
        unsubscribe_url = '#'
        try:
            # 수신자 이메일로 구독 레코드 탐색(있는 경우)
            sub = NewsletterSubscription.query.join('user').filter_by(email=to_email).first()
            if sub and sub.unsubscribe_token:
                from flask import url_for
                unsubscribe_url = url_for('newsletter.unsubscribe', token=sub.unsubscribe_token, _external=True)
        except Exception:
            pass

        # 시험발송도 실제 발송과 동일 포맷 사용: 최신 생성 로직으로 email_html 우선 사용
        try:
            from services.newsletter_generation_service import NewsletterGenerationService
            svc = NewsletterGenerationService()
            generated = None
            mkt = (content.market_type or '').upper()
            ntype = (content.newsletter_type or '').lower()
            tf = content.timeframe or 'd'
            if mkt == 'COMBINED' or ntype == 'combined':
                generated = svc.generate_combined_newsletter(timeframe=tf, primary_market=(content.primary_market or 'kospi'))
            elif mkt == 'KOSPI' or ntype == 'korean':
                generated = svc.generate_kospi_newsletter(timeframe=tf)
            elif mkt == 'KOSDAQ':
                generated = svc.generate_kosdaq_newsletter(timeframe=tf)
            elif mkt == 'US' or ntype == 'us':
                generated = svc.generate_us_newsletter(timeframe=tf)
            body_html_effective = (generated or {}).get('email_html') or (generated or {}).get('html') or content.html_content
        except Exception:
            body_html_effective = content.html_content

        email_service = EmailService()
        html_wrapped = email_service.render_newsletter_html(
            title=subject,
            recipient_name=recipient_name,
            body_html=body_html_effective,
            unsubscribe_url=unsubscribe_url,
            inline_css=True
        )

        res = email_service.send_html_email(
            to_email=to_email,
            subject=subject,
            html=html_wrapped,
            categories=['newsletter_test']
        )

        status = res.get('status_code')
        # EmailLog 기록
        try:
            log = EmailLog(user_id=current_user.id, email_type='newsletter', subject=subject, status='sent' if status in (200, 202) else 'failed')
            db.session.add(log)
            # EmailMessage 보강(뉴스레터 참조)
            msg_id = res.get('message_id')
            if msg_id:
                msg = EmailMessage.query.filter_by(sendgrid_message_id=msg_id).first()
                if msg:
                    msg.newsletter_id = content.id
                    msg.edition_date = content.generated_at
            db.session.commit()
        except Exception:
            db.session.rollback()
            pass

        if status in (200, 202):
            return jsonify({'success': True, 'status': status})
        return jsonify({'success': False, 'status': status, 'error': res.get('error')}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# === 뉴스레터: 구독자 벌크 발송(개인화 unsubscribe) ===
@admin_bp.route('/newsletter/bulk_send', methods=['POST'])
@login_required
@admin_required
def newsletter_bulk_send():
    try:
        from models import NewsletterContent, NewsletterSubscription, User
        data = request.get_json(force=True)
        newsletter_id = data.get('newsletter_id')
        subject = data.get('subject')
        segment = data.get('segment')  # 확장용(미사용)
        if not (newsletter_id and subject):
            return jsonify({'success': False, 'message': 'newsletter_id/subject 필요'}), 400

        content = NewsletterContent.query.filter_by(id=newsletter_id).first()
        if not content:
            return jsonify({'success': False, 'message': '뉴스레터 콘텐츠를 찾을 수 없습니다.'}), 404

        # 활성 구독자 목록 수집
        subs = NewsletterSubscription.query.filter_by(is_active=True).all()
        recipients = []
        from flask import url_for
        for s in subs:
            try:
                to_email = s.email or (s.user.email if s.user else None)
                if not to_email:
                    continue
                name = (s.user.get_full_name() if s.user else None) or to_email.split('@')[0]
                unsubscribe_url = url_for('newsletter.unsubscribe', token=s.unsubscribe_token, _external=True) if s.unsubscribe_token else '#'
                recipients.append({'email': to_email, 'name': name, 'unsubscribe_url': unsubscribe_url})
            except Exception:
                continue

        # 벌크 발송도 실제 포맷(email_html) 사용
        try:
            from services.newsletter_generation_service import NewsletterGenerationService
            svc = NewsletterGenerationService()
            generated = None
            mkt = (content.market_type or '').upper()
            ntype = (content.newsletter_type or '').lower()
            tf = content.timeframe or 'd'
            if mkt == 'COMBINED' or ntype == 'combined':
                generated = svc.generate_combined_newsletter(timeframe=tf, primary_market=(content.primary_market or 'kospi'))
            elif mkt == 'KOSPI' or ntype == 'korean':
                generated = svc.generate_kospi_newsletter(timeframe=tf)
            elif mkt == 'KOSDAQ':
                generated = svc.generate_kosdaq_newsletter(timeframe=tf)
            elif mkt == 'US' or ntype == 'us':
                generated = svc.generate_us_newsletter(timeframe=tf)
            body_html_effective = (generated or {}).get('email_html') or (generated or {}).get('html') or content.html_content
        except Exception:
            body_html_effective = content.html_content

        email_service = EmailService()
        summary = email_service.send_bulk_newsletter(
            recipients,
            subject,
            body_html_effective,
            newsletter_id=content.id,
            edition_date=content.generated_at,
            inline_css=True
        )
        return jsonify({'success': True, 'summary': summary})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# === 구독자 관리 화면 ===
@admin_bp.route('/subscribers')
@login_required
@admin_required
def subscribers_list():
    try:
        from models import NewsletterSubscription, User
        limit = request.args.get('limit', 100, type=int)
        # 사용자 연결이 없어도 목록이 떠야 하므로 외부조인 대신 단일 테이블 쿼리 사용
        q = NewsletterSubscription.query.order_by(NewsletterSubscription.created_at.desc())
        items = q.limit(limit).all()
        return render_template('admin/subscribers_list.html', items=items, limit=limit)
    except Exception as e:
        logging.error(f"구독자 목록 조회 실패: {e}")
        return render_template('error.html', error='구독자 목록 조회 중 오류가 발생했습니다.')


# === 구독자 생성 ===
@admin_bp.route('/subscribers', methods=['POST'])
@login_required
@admin_required
def subscribers_create():
    try:
        from models import db, NewsletterSubscription, User
        data = request.get_json(force=True)
        email = data.get('email')
        frequency = data.get('frequency', 'daily')
        send_time = data.get('send_time', '09:00:00')
        include_charts = bool(data.get('include_charts', True))
        include_summary = bool(data.get('include_summary', True))
        include_ta = bool(data.get('include_technical_analysis', True))
        if not email:
            return jsonify({'success': False, 'message': 'email 필요'}), 400
        # 이메일 기준으로 구독자 조회
        sub = NewsletterSubscription.query.filter_by(email=email).first()
        import uuid
        token = uuid.uuid4().hex
        if not sub:
            # 생성
            from datetime import datetime
            from datetime import time as dt_time
            try:
                hh, mm, ss = send_time.split(':')
                send_time_obj = dt_time(int(hh), int(mm), int(ss))
            except Exception:
                send_time_obj = None
            sub = NewsletterSubscription(
                email=email,
                is_active=True,
                frequency=frequency,
                send_time=send_time_obj,
                include_charts=include_charts,
                include_summary=include_summary,
                include_technical_analysis=include_ta,
                unsubscribe_token=token
            )
            db.session.add(sub)
        else:
            # 업데이트
            sub.is_active = True
            sub.frequency = frequency
            try:
                from datetime import time as dt_time
                hh, mm, ss = send_time.split(':')
                sub.send_time = dt_time(int(hh), int(mm), int(ss))
            except Exception:
                pass
            sub.include_charts = include_charts
            sub.include_summary = include_summary
            sub.include_technical_analysis = include_ta
            if not sub.unsubscribe_token:
                sub.unsubscribe_token = token
        db.session.commit()
        return jsonify({'success': True, 'id': sub.id})
    except Exception as e:
        logging.error(f"구독자 생성 실패: {e}")
        from models import db
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# === 구독자 활성/비활성 토글 ===
@admin_bp.route('/subscribers/<int:sub_id>/toggle', methods=['POST'])
@login_required
@admin_required
def subscribers_toggle(sub_id: int):
    try:
        from models import db, NewsletterSubscription
        sub = NewsletterSubscription.query.get(sub_id)
        if not sub:
            return jsonify({'success': False, 'message': '구독 정보를 찾을 수 없습니다.'}), 404
        sub.is_active = not bool(sub.is_active)
        db.session.commit()
        return jsonify({'success': True, 'is_active': sub.is_active})
    except Exception as e:
        logging.error(f"구독 토글 실패: {e}")
        from models import db
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# === 구독자 정보 업데이트 ===
@admin_bp.route('/subscribers/<int:sub_id>/update', methods=['POST'])
@login_required
@admin_required
def subscribers_update(sub_id: int):
    try:
        from models import db, NewsletterSubscription
        data = request.get_json(force=True)
        sub = NewsletterSubscription.query.get(sub_id)
        if not sub:
            return jsonify({'success': False, 'message': '구독 정보를 찾을 수 없습니다.'}), 404
        # 업데이트 가능한 필드
        if 'frequency' in data:
            sub.frequency = data['frequency']
        if 'send_time' in data:
            try:
                from datetime import time as dt_time
                hh, mm, ss = str(data['send_time']).split(':')
                sub.send_time = dt_time(int(hh), int(mm), int(ss))
            except Exception:
                pass
        if 'include_charts' in data:
            sub.include_charts = bool(data['include_charts'])
        if 'include_summary' in data:
            sub.include_summary = bool(data['include_summary'])
        if 'include_technical_analysis' in data:
            sub.include_technical_analysis = bool(data['include_technical_analysis'])
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"구독 업데이트 실패: {e}")
        from models import db
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# === 구독 해지 토큰 재발급 ===
@admin_bp.route('/subscribers/<int:sub_id>/regenerate_token', methods=['POST'])
@login_required
@admin_required
def subscribers_regenerate_token(sub_id: int):
    try:
        from models import db, NewsletterSubscription
        import uuid
        sub = NewsletterSubscription.query.get(sub_id)
        if not sub:
            return jsonify({'success': False, 'message': '구독 정보를 찾을 수 없습니다.'}), 404
        sub.unsubscribe_token = uuid.uuid4().hex
        db.session.commit()
        return jsonify({'success': True, 'token': sub.unsubscribe_token})
    except Exception as e:
        logging.error(f"토큰 재발급 실패: {e}")
        from models import db
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

def get_market_summary_data(market: str, timeframe: str = 'd') -> Dict:
    """단순화된 시장 요약 데이터 가져오기"""
    try:
        unified_service = UnifiedMarketAnalysisService()
        return unified_service.analyze_market_comprehensive(market, timeframe)
    except Exception as e:
        logging.error(f"시장 요약 데이터 생성 오류: {e}")
        return {}

@admin_bp.route('/api/market_summary/<market>')
@login_required
@admin_required
def get_market_summary(market):
    """시장별 요약 정보 API - 새로운 MarketSummaryService 사용"""
    try:
        from services.core.market_summary_service import MarketSummaryService
        
        # UnifiedMarketAnalysisService로 분석 수행
        unified_service = UnifiedMarketAnalysisService()
        analysis_result = unified_service.analyze_market_comprehensive(market, 'd')
        
        # 분류 결과 추출
        classification_results = analysis_result.get('classification_results', {})
        
        # 새로운 MarketSummaryService로 시장 요약 생성
        market_summary = MarketSummaryService.create_market_summary(classification_results, market)
        
        return jsonify({
            'success': True,
            'summary': market_summary
        })

    except Exception as e:
        logging.error(f"시장 요약 정보 생성 중 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        })