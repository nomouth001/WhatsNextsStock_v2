"""
2025-01-11: user_routes 활성화
admin_routes의 UnifiedMarketAnalysisService + MarketSummaryService 패턴을 user용으로 적용
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, Stock
from services.core.unified_market_analysis_service import UnifiedMarketAnalysisService
from services.technical_indicators_service import technical_indicators_service
from datetime import datetime
import logging
from typing import Dict
import pandas as pd

user_bp = Blueprint('user', __name__)

# 어드민 권한 확인 데코레이터 - 주석처리
# def admin_required(f):
#     """관리자 권한 확인 데코레이터"""
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if not current_user.is_authenticated or not current_user.is_admin:
#             flash('관리자 권한이 필요합니다.', 'error')
#             return redirect(url_for('auth.login'))
#         return f(*args, **kwargs)
#     return decorated_function

@user_bp.route('/home')
@user_bp.route('/home/<market>')
@login_required
def home(market='us'):
    """사용자 홈페이지 - UnifiedMarketAnalysisService 단일 패턴 사용"""
    try:
        # market 파라미터 검증
        if market not in ['us', 'kospi', 'kosdaq']:
            market = 'us'
        
        # 시장별 설정
        market_type = 'US' if market == 'us' else 'KOSPI' if market == 'kospi' else 'KOSDAQ'
        market_name = '미국 주식 (US)' if market == 'us' else 'KOSPI' if market == 'kospi' else 'KOSDAQ'
        
        # 통합 서비스 사용 (admin_routes와 동일한 패턴)
        unified_service = UnifiedMarketAnalysisService()
        analysis_result = unified_service.analyze_market_comprehensive(market, 'd')
        
        # 분석 결과에서 데이터 추출
        classification_results = analysis_result.get('classification_results', {})
        
        # MarketSummaryService로 시장 요약 생성
        from services.core.market_summary_service import MarketSummaryService
        market_summary = MarketSummaryService.create_market_summary(classification_results, market_type)
        
        return render_template('user/user_home.html',
                             title='사용자 홈',
                             current_market=market,
                             current_market_name=market_name,
                             market_summary=market_summary,
                             classification_results=classification_results,
                             analysis_result=analysis_result,
                             display_date=datetime.now().strftime('%Y-%m-%d'))
    except Exception as e:
        logging.error(f"사용자 홈페이지 오류: {e}")
        return render_template('error.html', error="데이터 로딩 중 오류가 발생했습니다.")
# 2025-01-11: NewsletterClassificationService 사용 코드 제거 완료
# UnifiedMarketAnalysisService + MarketSummaryService 패턴으로 통합됨

# 어드민 전용 기능들 - 주석처리
# @user_bp.route('/refresh_market_data', methods=['POST'])
# @login_required
# @admin_required
# def refresh_market_data():
#     try:
#         # 한국/미국 주식 가져오기
#         kospi_stocks = Stock.query.filter_by(market_type='KOSPI', is_active=True).all()
#         kosdaq_stocks = Stock.query.filter_by(market_type='KOSDAQ', is_active=True).all()
#         us_stocks = Stock.query.filter_by(market_type='US', is_active=True).all()
#         
#         # 시장별 데이터 갱신 (타임필터링 완전 제거)
#         # 한국 주식 갱신
#         get_market_data_for_stocks(kospi_stocks, 'KOSPI', datetime.now().date())
#         get_market_data_for_stocks(kosdaq_stocks, 'KOSDAQ', datetime.now().date())
#         
#         # 미국 주식 갱신
#         get_market_data_for_stocks(us_stocks, 'US', datetime.now().date())
#         
#         # 갱신 후 데이터 다시 불러오기
#         kospi_tickers = [stock.ticker for stock in kospi_stocks]
#         kosdaq_tickers = [stock.ticker for stock in kosdaq_stocks]
#         us_tickers = [stock.ticker for stock in us_stocks]
#         
#         # 최신 데이터 확인
#         if kospi_tickers:
#             get_latest_ohlcv(kospi_tickers, 'KOSPI')
#         if kosdaq_tickers:
#             get_latest_ohlcv(kosdaq_tickers, 'KOSDAQ')
#         if us_tickers:
#             get_latest_ohlcv(us_tickers, 'US')
#         
#         return jsonify({'success': True, 'message': '주가 데이터가 성공적으로 갱신되었습니다.'})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)})

# 어드민 전용 기능들 - 주석처리
# @user_bp.route('/users')
# @login_required
# @admin_required
# def users():
#     # 사용자 관리 페이지
#     users = User.query.filter_by(is_withdrawn=False).all()
#     return render_template('admin/users.html', title='사용자 관리', users=users)

# @user_bp.route('/delete-stocks', methods=['POST'])
# @login_required
# @admin_required
# def delete_stocks():
#     # 선택된 주식들 삭제
#     try:
#         stock_ids = request.json.get('stock_ids', [])
#         if not stock_ids:
#             return jsonify({'success': False, 'message': '삭제할 주식을 선택해주세요.'})
#         
#         # 선택된 주식들을 비활성화
#         stocks = Stock.query.filter(Stock.id.in_(stock_ids)).all()
#         deleted_count = 0
#         
#         for stock in stocks:
#             stock.is_active = False
#             deleted_count += 1
#         
#         db.session.commit()
#         
#         return jsonify({
#             'success': True, 
#             'message': f'{deleted_count}개의 주식이 삭제되었습니다.'
#         })
#         
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({'success': False, 'message': f'삭제 중 오류 발생: {str(e)}'})

# @user_bp.route('/download-stocks/<market_type>')
# @login_required
# @admin_required
# def download_stocks(market_type):
#     # 주식 리스트 CSV 다운로드
#     try:
#         from flask import make_response
#         import io
#         import csv
#         
#         if market_type not in ['KOSPI', 'KOSDAQ', 'US']:
#             flash('잘못된 시장 타입입니다.', 'error')
#             return redirect(url_for('user.home'))
#         
#         # 해당 시장의 활성화된 주식들 조회
#         stocks = Stock.query.filter_by(
#             market_type=market_type, 
#             is_active=True
#         ).order_by(Stock.ticker).all()
#         
#         # CSV 생성
#         output = io.StringIO()
#         writer = csv.writer(output)
#         
#         # 헤더 작성
#         writer.writerow(['ticker', 'company_name'])
#         
#         # 데이터 작성
#         for stock in stocks:
#             writer.writerow([stock.ticker, stock.company_name or ''])
#         
#         # 응답 생성
#         response_data = output.getvalue()
#         output.close()
#         
#         response = make_response(response_data)
#         response.headers['Content-Type'] = 'text/csv'
#         response.headers['Content-Disposition'] = f'attachment; filename={market_type}_stocks.csv'
#         
#         return response
#         
#     except Exception as e:
#         flash(f'다운로드 중 오류 발생: {str(e)}', 'error')
#         return redirect(url_for('user.home')) 

# @user_bp.route('/force_data_download', methods=['POST'])
# @login_required
# @admin_required
# def force_data_download():
#     # 강제 데이터 다운로드 - 어드민 전용 (개선된 시간대별 전략 적용)
#     try:
#         # 현재 시간 정보 가져오기
#         from services.market_data_service import get_current_time_info, get_market_status_info_improved
#         time_info = get_current_time_info()
#         
#         # 활성화된 모든 주식의 티커 수집
#         kospi_stocks = Stock.query.filter_by(market_type='KOSPI', is_active=True).all()
#         kosdaq_stocks = Stock.query.filter_by(market_type='KOSDAQ', is_active=True).all()
#         us_stocks = Stock.query.filter_by(market_type='US', is_active=True).all()
#         
#         kospi_tickers = [stock.ticker for stock in kospi_stocks]
#         kosdaq_tickers = [stock.ticker for stock in kosdaq_stocks]
#         us_tickers = [stock.ticker for stock in us_stocks]
#         
#         logging.info(f"[ADMIN] === 강제 데이터 다운로드 시작 ===")
#         logging.info(f"[ADMIN] 실행자: {current_user.username}")
#         logging.info(f"[ADMIN] 현재 KST: {time_info['kst_str']}")
#         logging.info(f"[ADMIN] 현재 EST: {time_info['est_str']}")
#         logging.info(f"[ADMIN] KOSPI 종목 수: {len(kospi_tickers)}")
#         logging.info(f"[ADMIN] KOSDAQ 종목 수: {len(kosdaq_tickers)}")
#         logging.info(f"[ADMIN] US 종목 수: {len(us_tickers)}")
#         
#         # 시장 상태 확인
#         kospi_market_status = get_market_status_info_improved('KOSPI')
#         kosdaq_market_status = get_market_status_info_improved('KOSDAQ')
#         us_market_status = get_market_status_info_improved('US')
#         
#         logging.info(f"[ADMIN] KOSPI 상태: {kospi_market_status['market_name']} - {kospi_market_status['status']}")
#         logging.info(f"[ADMIN] KOSDAQ 상태: {kosdaq_market_status['market_name']} - {kosdaq_market_status['status']}")
#         logging.info(f"[ADMIN] 미국장 상태: {us_market_status['market_name']} - {us_market_status['status']}")
#         
#         results = {}
#         total_processed = 0
#         
#         # KOSPI 주식 다운로드
#         if kospi_tickers:
#             logging.info(f"[ADMIN] === KOSPI 주식 데이터 다운로드 시작 ===")
#             logging.info(f"[ADMIN] KOSPI 주식 티커 (처음 10개): {kospi_tickers[:10]}")
#             kospi_results = get_latest_ohlcv(kospi_tickers, 'KOSPI')
#             results['KOSPI'] = kospi_results
#             total_processed += len(kospi_tickers)
#             
#             # 결과 요약 로깅
#             kospi_success = sum(1 for data in kospi_results.values() if data.get('close') is not None)
#             kospi_fail = len(kospi_tickers) - kospi_success
#             logging.info(f"[ADMIN] KOSPI 주식 다운로드 완료: 성공 {kospi_success}, 실패 {kospi_fail}")
#             
#             # 샘플 데이터 로깅
#             if kospi_results:
#                 sample_ticker = list(kospi_results.keys())[0]
#                 sample_data = kospi_results[sample_ticker]
#                 if sample_data.get('close') is not None:
#                     logging.info(f"[ADMIN] KOSPI 주식 샘플 데이터 ({sample_ticker}): 종가={sample_data.get('close')}, 최신날짜={sample_data.get('latest_date')}, 전략={sample_data.get('strategy_reason')}")
#         
#         # KOSDAQ 주식 다운로드
#         if kosdaq_tickers:
#             logging.info(f"[ADMIN] === KOSDAQ 주식 데이터 다운로드 시작 ===")
#             logging.info(f"[ADMIN] KOSDAQ 주식 티커 (처음 10개): {kosdaq_tickers[:10]}")
#             kosdaq_results = get_latest_ohlcv(kosdaq_tickers, 'KOSDAQ')
#             results['KOSDAQ'] = kosdaq_results
#             total_processed += len(kosdaq_tickers)
#             
#             # 결과 요약 로깅
#             kosdaq_success = sum(1 for data in kosdaq_results.values() if data.get('close') is not None)
#             kosdaq_fail = len(kosdaq_tickers) - kosdaq_success
#             logging.info(f"[ADMIN] KOSDAQ 주식 다운로드 완료: 성공 {kosdaq_success}, 실패 {kosdaq_fail}")
#             
#             # 샘플 데이터 로깅
#             if kosdaq_results:
#                 sample_ticker = list(kosdaq_results.keys())[0]
#                 sample_data = kosdaq_results[sample_ticker]
#                 if sample_data.get('close') is not None:
#                     logging.info(f"[ADMIN] KOSDAQ 주식 샘플 데이터 ({sample_ticker}): 종가={sample_data.get('close')}, 최신날짜={sample_data.get('latest_date')}, 전략={sample_data.get('strategy_reason')}")
#         
#         # 미국 주식 다운로드  
#         if us_tickers:
#             logging.info(f"[ADMIN] === 미국 주식 데이터 다운로드 시작 ===")
#             logging.info(f"[ADMIN] 미국 주식 티커 (처음 10개): {us_tickers[:10]}")
#             us_results = get_latest_ohlcv(us_tickers, 'US')
#             results['US'] = us_results
#             total_processed += len(us_tickers)
#             
#             # 결과 요약 로깅
#             us_success = sum(1 for data in us_results.values() if data.get('close') is not None)
#             us_fail = len(us_tickers) - us_success
#             logging.info(f"[ADMIN] 미국 주식 다운로드 완료: 성공 {us_success}, 실패 {us_fail}")
#             
#             # 샘플 데이터 로깅
#             if us_results:
#                 sample_ticker = list(us_results.keys())[0]
#                 sample_data = us_results[sample_ticker]
#                 if sample_data.get('close') is not None:
#                     logging.info(f"[ADMIN] 미국 주식 샘플 데이터 ({sample_ticker}): 종가={sample_data.get('close')}, 최신날짜={sample_data.get('latest_date')}, 전략={sample_data.get('strategy_reason')}")
#         
#         # 전체 성공/실패 카운트
#         success_count = 0
#         fail_count = 0
#         
#         for market_results in results.values():
#             for ticker_data in market_results.values():
#                 if ticker_data.get('close') is not None:
#                     success_count += 1
#                 else:
#                     fail_count += 1
#         
#         logging.info(f"[ADMIN] === 강제 데이터 다운로드 완료 ===")
#         logging.info(f"[ADMIN] 전체 처리: {total_processed}, 성공: {success_count}, 실패: {fail_count}")
#         
#         return jsonify({
#             'success': True, 
#             'message': f'강제 데이터 다운로드 완료. 성공: {success_count}, 실패: {fail_count}',
#             'results': {
#                 'total_processed': total_processed,
#                 'success_count': success_count,
#                 'fail_count': fail_count,
#                 'time_info': {
#                     'kst_time': time_info['kst_str'],
#                     'est_time': time_info['est_str'],
#                     'kospi_market_status': kospi_market_status['status'],
#                     'kosdaq_market_status': kosdaq_market_status['status'],
#                     'us_market_status': us_market_status['status']
#                 }
#             }
#         })
#         
#     except Exception as e:
#         logging.error(f"[ADMIN] 강제 데이터 다운로드 오류: {e}")
#         import traceback
#         logging.error(f"[ADMIN] 스택 트레이스: {traceback.format_exc()}")
#         return jsonify({'success': False, 'message': f'오류 발생: {str(e)}'})

# 2025-01-11: 중복 API 및 함수 제거 
# admin_routes.py의 통합 API 사용 권장 (UnifiedMarketAnalysisService + MarketSummaryService)

# def get_stock_with_indicators_from_cache(ticker, cached_data, market_type):
#     # 캐시된 데이터를 사용하여 주식의 OHLCV 데이터와 기술적 지표를 함께 가져오기
#     try:
#         ohlcv_df = cached_data['ohlcv']
#         indicators_df = cached_data['indicators']
#         
#         if ohlcv_df.empty:
#             return None
#         
#         # 최신 OHLCV 데이터
#         latest_ohlcv = ohlcv_df.iloc[-1]
#         
#         # 등락률 계산 (TechnicalIndicatorsService 사용)
#         change_percent = technical_indicators_service.get_latest_change_percent(ticker, 'd', market_type)
#         
#         stock_data = {
#             'ticker': ticker,
#             'close': round(latest_ohlcv['Close'], 2 if market_type == 'US' else 0),
#             'change_percent': round(change_percent, 2),
#             'volume': int(latest_ohlcv['Volume']),
#             'indicators': {}
#         }
#         
#         # 지표 데이터가 있으면 최신 값들 추가
#         if not indicators_df.empty:
#             latest_indicators = indicators_df.iloc[-1]
#             
#             # NaN 값을 안전하게 처리하는 헬퍼 함수
#             def safe_get_value(series, key, default=0, decimals=2):
#                 value = series.get(key, default)
#                 if pd.isna(value) or value is None:
#                     return default
#                 return round(float(value), decimals)
#             
#             stock_data['indicators'] = {
#                 # EMA 지표
#                 'ema5': safe_get_value(latest_indicators, 'EMA5', 0, 2 if market_type == 'US' else 0),
#                 'ema20': safe_get_value(latest_indicators, 'EMA20', 0, 2 if market_type == 'US' else 0),
#                 'ema40': safe_get_value(latest_indicators, 'EMA40', 0, 2 if market_type == 'US' else 0),
#                 
#                 # MACD (올바른 컬럼명 사용)
#                 'macd_line': safe_get_value(latest_indicators, 'MACD', 0, 3),
#                 'macd_signal': safe_get_value(latest_indicators, 'MACD_Signal', 0, 3),
#                 'macd_histogram': safe_get_value(latest_indicators, 'MACD_Histogram', 0, 3),
#                 
#                 # RSI (올바른 컬럼명 사용)
#                 'rsi': safe_get_value(latest_indicators, 'RSI', 0, 2),
#                 
#                 # Stochastic
#                 'stoch_k': safe_get_value(latest_indicators, 'Stoch_K', 0, 2),
#                 'stoch_d': safe_get_value(latest_indicators, 'Stoch_D', 0, 2),
#                 
#                 # Ichimoku
#                 'ichimoku_tenkan': safe_get_value(latest_indicators, 'Ichimoku_Tenkan', 0, 2 if market_type == 'US' else 0),
#                 'ichimoku_kijun': safe_get_value(latest_indicators, 'Ichimoku_Kijun', 0, 2 if market_type == 'US' else 0),
#                 
#                 # Volume Ratios
#                 'volume_ratio_5d': safe_get_value(latest_indicators, 'Volume_Ratio_5d', 0, 1),
#                 'volume_ratio_20d': safe_get_value(latest_indicators, 'Volume_Ratio_20d', 0, 1),
#                 'volume_ratio_40d': safe_get_value(latest_indicators, 'Volume_Ratio_40d', 0, 1)
#             }
#             
#             # 추가 분석 데이터 가져오기 - 캐시된 데이터 사용
#             analysis_data = technical_indicators_service.get_stock_analysis_data_from_cache(ticker, cached_data, market_type)
#             if analysis_data:
#                 stock_data['analysis'] = {
#                     'ema_array': analysis_data.get('ema_array'),
#                     'ema_crossover': technical_indicators_service.get_crossover_display_info(analysis_data.get('ema_crossover')),
#                     'macd_crossover': technical_indicators_service.get_crossover_display_info(analysis_data.get('macd_crossover')),
#                     'ema_crossover_status': analysis_data.get('ema_crossover_status'),
#                     'macd_crossover_status': analysis_data.get('macd_crossover_status'),
#                     'gap_ema20': analysis_data.get('gap_ema20'),
#                     'gap_ema40': analysis_data.get('gap_ema40')
#                 }
#         
#         return stock_data
#         
#     except Exception as e:
#         logging.error(f"[{ticker}] Error getting stock with indicators from cache: {e}")
#         return None 

# 임시 Blueprint 생성 (다른 파일에서 import 에러 방지용)
from flask import Blueprint
user_bp = Blueprint('user', __name__)