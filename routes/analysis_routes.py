import os
import logging
import pandas as pd
import base64
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import mplfinance as mpf
import glob

# 한글 폰트 설정
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'Malgun Gothic', 'NanumGothic', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for
from flask_login import login_required
import google.generativeai as genai
import requests
import json
import ta

# Services
from services.market.data_download_service import DataDownloadService
from services.technical_indicators_service import technical_indicators_service
from services.analysis.ai_analysis_service import AIAnalysisService
from services.analysis.chart_service import ChartService
from services.market.data_reading_service import DataReadingService
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from services.core.unified_market_analysis_service import UnifiedMarketAnalysisService
from services.core.cache_service import CacheService
from services.technical_indicators_service import TechnicalIndicatorsService
from services.analysis.crossover.detection import CrossoverDetector
from models import Stock

# Config
from config import DevelopmentConfig

# Blueprint 생성
analysis_bp = Blueprint('analysis', __name__, url_prefix='/analysis')

def _get_market_timezone(market: str) -> ZoneInfo:
    try:
        m = (market or '').upper()
        if m in ['KOSPI', 'KOSDAQ']:
            return ZoneInfo('Asia/Seoul')
        return ZoneInfo('America/New_York')
    except Exception:
        return ZoneInfo('Asia/Seoul')

def _get_market_hours(market: str) -> tuple:
    """Return (start_h, start_m, close_h, close_m) in local market time."""
    m = (market or '').upper()
    if m in ['KOSPI', 'KOSDAQ']:
        return (9, 0, 15, 30)  # 09:00-15:30 KST
    return (9, 30, 16, 0)     # 09:30-16:00 EST

def _prev_business_day(dt_local: datetime) -> datetime:
    d = dt_local.date()
    while True:
        d = d - timedelta(days=1)
        if d.weekday() < 5:
            return datetime(d.year, d.month, d.day, tzinfo=dt_local.tzinfo)

def _find_latest_cached_analysis_file(ticker: str, market: str) -> str | None:
    try:
        analysis_dir = os.path.join("static", "analysis")
        pattern = os.path.join(analysis_dir, f"{ticker}_AI_Analysis_{market}_*.html")
        files = glob.glob(pattern)
        if not files:
            return None
        files.sort(key=lambda p: os.path.getmtime(p))
        return files[-1]
    except Exception:
        return None

def _detect_canonical_market_by_files(ticker: str, preferred_market: str) -> str:
    try:
        candidates = [preferred_market] + [m for m in ['US', 'KOSPI', 'KOSDAQ'] if m != preferred_market]
        for cand in candidates:
            try:
                data_dir = os.path.join("static", "data", cand)
                if glob.glob(os.path.join(data_dir, f"{ticker}_indicators_d_*.csv")) or \
                   glob.glob(os.path.join(data_dir, f"{ticker}_ohlcv_d_*.csv")):
                    return cand
            except Exception:
                continue
        return preferred_market
    except Exception:
        return preferred_market

def _get_file_created_dt_in_tz(path: str, tz: ZoneInfo) -> datetime | None:
    try:
        mtime = os.path.getmtime(path)
        return datetime.fromtimestamp(mtime, tz)
    except Exception:
        return None

def _determine_market_phase(now_local: datetime, market: str) -> str:
    sh, sm, ch, cm = _get_market_hours(market)
    start_dt = now_local.replace(hour=sh, minute=sm, second=0, microsecond=0)
    close_dt = now_local.replace(hour=ch, minute=cm, second=0, microsecond=0)
    if now_local < start_dt:
        return 'pre'
    if now_local <= close_dt:
        return 'open'
    return 'post'

def _get_prev_close_and_today_close(now_local: datetime, market: str) -> tuple[datetime, datetime]:
    sh, sm, ch, cm = _get_market_hours(market)
    today_close = now_local.replace(hour=ch, minute=cm, second=0, microsecond=0)
    prev_biz = _prev_business_day(now_local)
    prev_close = prev_biz.replace(hour=ch, minute=cm, second=0, microsecond=0)
    return prev_close, today_close

def _try_return_cached_analysis_html(ticker: str, market: str) -> str | None:
    try:
        tz = _get_market_timezone(market)
        now_local = datetime.now(tz)
        latest_path = _find_latest_cached_analysis_file(ticker, market)
        prev_close_dt, today_close_dt = _get_prev_close_and_today_close(now_local, market)
        phase = _determine_market_phase(now_local, market)

        logging.info(f"[CACHE] {ticker}/{market} phase={phase} now={now_local} prev_close={prev_close_dt} today_close={today_close_dt} latest_path={latest_path}")

        if not latest_path:
            logging.info(f"[CACHE] No cached file found for {ticker}/{market}")
            return None

        created_dt = _get_file_created_dt_in_tz(latest_path, tz)
        if created_dt is None:
            return None

        if phase in ('pre', 'open'):
            is_fresh = created_dt >= prev_close_dt
        else:  # post
            is_fresh = created_dt > today_close_dt

        logging.info(f"[CACHE] created={created_dt} fresh={is_fresh}")

        if not is_fresh:
            logging.info(f"[CACHE] Not fresh: created={created_dt} phase={phase} prev_close={prev_close_dt} today_close={today_close_dt}")
            return None

        try:
            with open(latest_path, 'r', encoding='utf-8') as f:
                html = f.read()
            logging.info(f"[CACHE] Using cached analysis HTML: {latest_path}")
            return html
        except Exception as read_err:
            logging.warning(f"[CACHE] Failed to read cached file: {read_err}")
            return None
    except Exception as e:
        logging.warning(f"[CACHE] Unexpected error: {e}")
        return None

def generate_charts(ticker, market_type='KOSPI'):
    """일봉, 주봉, 월봉 차트를 생성합니다."""
    try:
        # 새로운 차트 서비스 사용
        from services.analysis.chart_service import ChartService
        chart_service = ChartService()
        
        # 차트 생성
        charts, error = chart_service.generate_charts(ticker, market_type)
        
        return charts, error
        
    except Exception as e:
        error_msg = f"차트 생성 중 오류 발생: {e}"
        logging.error(error_msg)
        return None, error_msg
        
        # 이 함수는 이제 ChartService로 이동되었습니다.
        # 기존 코드는 제거하고 새로운 서비스를 사용합니다.

def create_chart_image(df, title, timeframe, ticker, market_type='US'):
    """차트 이미지를 생성하고 base64로 인코딩합니다."""
    try:
        # ✅ 새로운 차트 서비스 사용 (중복 계산 제거됨)
        from services.analysis.chart_service import ChartService
        chart_service = ChartService()
        
        # 차트 이미지 생성
        chart_image = chart_service.create_chart_image(df, title, timeframe, ticker, market_type)
        
        return chart_image
        
    except Exception as e:
        error_msg = f"차트 이미지 생성 중 오류 발생: {e}"
        logging.error(error_msg)
        return None

# 🚫 오래된 차트 생성 코드 완전 제거됨 - ChartService를 사용하세요

def load_saved_indicators(df, ticker, timeframe, market_type='US'):
    """
    indicators CSV에서 지표 로드
    계산 로직 제거, 순수 읽기만
    """
    try:
        # 시간대 매핑
        timeframe_map = {
            '일봉': 'd',
            '주봉': 'w', 
            '월봉': 'm'
        }
        tf = timeframe_map.get(timeframe, 'd')
        
        # ✅ 새로운: CSV 읽기만
        indicators_df = get_indicators_data(ticker, tf, market_type)
        
        if indicators_df.empty:
            logging.error(f"지표 데이터 없음: {ticker}")
            return df
        
        # OHLCV 데이터와 지표 데이터 결합
        combined_df = df.join(indicators_df, how='left')
        return combined_df
        
    except Exception as e:
        logging.error(f"지표 로드 실패: {e}")
        return df

def get_indicators_data(ticker, timeframe, market_type='US'):
    """indicators CSV에서 지표 데이터 가져오기"""
    try:
        from services.technical_indicators_service import TechnicalIndicatorsService
        indicators_service = TechnicalIndicatorsService()
        
        # 지표 CSV 확인 및 자동 생성
        if not indicators_service.ensure_indicators_exist(ticker, timeframe, market_type):
            logging.error(f"[{ticker}] 지표 CSV 생성 실패")
            return pd.DataFrame()
        
        return indicators_service.read_indicators_csv(ticker, market_type, timeframe)
    except Exception as e:
        logging.error(f"지표 데이터 가져오기 실패: {e}")
        return pd.DataFrame()

# 🚫 중복 계산 함수 제거됨 - TechnicalIndicatorsService를 사용하세요
# def calculate_technical_indicators(df): # 이 함수는 중복을 제거하기 위해 삭제되었습니다

def get_ohlcv_data_for_ai(ticker, market_type='KOSPI'):
    """AI 분석용 OHLCV 데이터를 가져옵니다."""
    try:
        ticker = ticker.upper()
        
        # 디버그: 데이터 로딩 과정 로그 저장
        debug_log_path = os.path.join("logs", f"data_loading_debug_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        os.makedirs("logs", exist_ok=True)
        
        with open(debug_log_path, 'w', encoding='utf-8') as f:
            f.write(f"=== AI 분석용 데이터 로딩 디버그 로그 ===\n")
            f.write(f"티커: {ticker}\n")
            f.write(f"시장타입: {market_type}\n")
            f.write(f"로딩 시간: {datetime.now()}\n")
        
        # market_type을 실제 폴더명으로 변환
        if market_type.upper() in ['KOSPI', 'KOSDAQ']:
            actual_market_type = market_type.upper()
        elif market_type.upper() == 'US':
            actual_market_type = 'US'
        else:
            # 기본값은 KOSPI
            actual_market_type = 'KOSPI'
        
        with open(debug_log_path, 'a', encoding='utf-8') as f:
            f.write(f"실제 시장타입: {actual_market_type}\n")
        
        # 저장된 데이터 파일 찾기
        data_dir = os.path.join("static/data", actual_market_type)
        if not os.path.exists(data_dir):
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(f"데이터 디렉토리가 존재하지 않음: {data_dir}\n")
            return None, None, None
        
        with open(debug_log_path, 'a', encoding='utf-8') as f:
            f.write(f"데이터 디렉토리: {data_dir}\n")
        
        # 최신 파일 찾기
        ohlcv_files = []
        for filename in os.listdir(data_dir):
            if filename.startswith(f"{ticker}_") and filename.endswith("_ohlcv_d.csv"):
                ohlcv_files.append(filename)
        
        with open(debug_log_path, 'a', encoding='utf-8') as f:
            f.write(f"발견된 일봉 파일들: {ohlcv_files}\n")
        
        if not ohlcv_files:
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write("일봉 파일을 찾을 수 없음\n")
            return None, None, None
        
        # 가장 최신 파일 선택
        latest_file = max(ohlcv_files)
        ohlcv_path = os.path.join(data_dir, latest_file)
        
        with open(debug_log_path, 'a', encoding='utf-8') as f:
            f.write(f"선택된 일봉 파일: {latest_file}\n")
            f.write(f"일봉 파일 경로: {ohlcv_path}\n")
        
        # OHLCV 데이터 로드
        # [메모] 2025-08-19: CSV 직접 파싱을 중단하고 DataReadingService를 사용합니다.
        # 기존 코드: df = pd.read_csv(ohlcv_path, index_col=0)
        try:
            from services.market.data_reading_service import DataReadingService
            _drs_tmp = DataReadingService()
            # market_type을 알 수 없으므로 폴더명 추출 시도, 실패 시 'US'
            import os
            market_guess = 'US'
            try:
                parts = os.path.normpath(ohlcv_path).split(os.sep)
                if len(parts) >= 2:
                    market_guess = parts[-2].upper()
            except Exception:
                pass
            df = _drs_tmp.read_ohlcv_csv(ticker, market_guess, 'd')
        except Exception as _:
            df = pd.DataFrame()
        
        with open(debug_log_path, 'a', encoding='utf-8') as f:
            f.write(f"로드된 일봉 데이터 행 수: {len(df)}\n")
            f.write(f"일봉 데이터 컬럼: {df.columns.tolist()}\n")
            f.write(f"일봉 데이터 인덱스 (처음 5개): {df.index[:5].tolist()}\n")
            f.write(f"일봉 데이터 인덱스 (마지막 5개): {df.index[-5:].tolist()}\n")
        
        if df.empty:
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write("일봉 데이터가 비어있음\n")
            return None, None, None
        
        # 인덱스를 DatetimeIndex로 변환
        try:
            df.index = pd.to_datetime(df.index, utc=True)
            # UTC 시간대 제거 (로컬 시간으로 변환)
            df.index = df.index.tz_localize(None)
            
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(f"시간대 변환 후 인덱스 (처음 5개): {df.index[:5].tolist()}\n")
                f.write(f"시간대 변환 후 인덱스 (마지막 5개): {df.index[-5:].tolist()}\n")
        except Exception as e:
            logging.error(f"Failed to convert index to datetime: {e}")
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(f"인덱스 변환 실패: {e}\n")
            return None, None, None
        
        # OHLCV 컬럼 정규화
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # 필요한 컬럼만 선택
        required_columns = ["Open", "High", "Low", "Close", "Volume"]
        if not all(col in df.columns for col in required_columns):
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(f"필요한 컬럼이 없음. 현재 컬럼: {df.columns.tolist()}\n")
            return None, None, None
        
        df = df[required_columns].dropna()
        
        with open(debug_log_path, 'a', encoding='utf-8') as f:
            f.write(f"정규화 후 데이터 행 수: {len(df)}\n")
            f.write(f"정규화 후 컬럼: {df.columns.tolist()}\n")
        
        # 일봉 데이터
        daily_data = format_ohlcv_data(df, "일봉")
        
        with open(debug_log_path, 'a', encoding='utf-8') as f:
            f.write(f"포맷팅된 일봉 데이터 개수: {len(daily_data)}\n")
            if daily_data:
                f.write(f"일봉 데이터 샘플 (최근 5개):\n")
                for i, item in enumerate(daily_data[-5:]):
                    f.write(f"  {i+1}. {item}\n")
        
        # 주봉 데이터 - 저장된 주봉 데이터 사용
        weekly_files = []
        for filename in os.listdir(data_dir):
            if filename.startswith(f"{ticker}_") and filename.endswith("_ohlcv_w.csv"):
                weekly_files.append(filename)
        
        with open(debug_log_path, 'a', encoding='utf-8') as f:
            f.write(f"발견된 주봉 파일들: {weekly_files}\n")
        
        if weekly_files:
            latest_weekly_file = max(weekly_files)
            weekly_path = os.path.join(data_dir, latest_weekly_file)
            # [메모] 2025-08-19: 주봉도 서비스 호출로 대체
            # 기존 코드: weekly_df = pd.read_csv(weekly_path, index_col=0)
            try:
                weekly_df = _drs_tmp.read_ohlcv_csv(ticker, market_guess, 'w')
            except Exception:
                weekly_df = pd.DataFrame()
            
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(f"선택된 주봉 파일: {latest_weekly_file}\n")
                f.write(f"로드된 주봉 데이터 행 수: {len(weekly_df)}\n")
            
            try:
                weekly_df.index = pd.to_datetime(weekly_df.index, utc=True)
                weekly_df.index = weekly_df.index.tz_localize(None)
            except Exception as e:
                logging.error(f"Failed to convert weekly index to datetime: {e}")
                weekly_df = pd.DataFrame()
            
            if isinstance(weekly_df.columns, pd.MultiIndex):
                weekly_df.columns = weekly_df.columns.get_level_values(0)
            
            if not weekly_df.empty and all(col in weekly_df.columns for col in required_columns):
                weekly_df = weekly_df[required_columns].dropna()
                weekly_data = format_ohlcv_data(weekly_df, "주봉")
                
                with open(debug_log_path, 'a', encoding='utf-8') as f:
                    f.write(f"포맷팅된 주봉 데이터 개수: {len(weekly_data)}\n")
                    if weekly_data:
                        f.write(f"주봉 데이터 샘플 (최근 5개):\n")
                        for i, item in enumerate(weekly_data[-5:]):
                            f.write(f"  {i+1}. {item}\n")
            else:
                weekly_data = None
                with open(debug_log_path, 'a', encoding='utf-8') as f:
                    f.write("주봉 데이터 처리 실패\n")
        else:
            weekly_data = None
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write("주봉 파일을 찾을 수 없음\n")
        
        # 월봉 데이터 - 저장된 월봉 데이터 사용
        monthly_files = []
        for filename in os.listdir(data_dir):
            if filename.startswith(f"{ticker}_") and filename.endswith("_ohlcv_m.csv"):
                monthly_files.append(filename)
        
        with open(debug_log_path, 'a', encoding='utf-8') as f:
            f.write(f"발견된 월봉 파일들: {monthly_files}\n")
        
        if monthly_files:
            latest_monthly_file = max(monthly_files)
            monthly_path = os.path.join(data_dir, latest_monthly_file)
            # [메모] 2025-08-19: 월봉도 서비스 호출로 대체
            # 기존 코드: monthly_df = pd.read_csv(monthly_path, index_col=0)
            try:
                monthly_df = _drs_tmp.read_ohlcv_csv(ticker, market_guess, 'm')
            except Exception:
                monthly_df = pd.DataFrame()
            
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(f"선택된 월봉 파일: {latest_monthly_file}\n")
                f.write(f"로드된 월봉 데이터 행 수: {len(monthly_df)}\n")
            
            try:
                monthly_df.index = pd.to_datetime(monthly_df.index, utc=True)
                monthly_df.index = monthly_df.index.tz_localize(None)
            except Exception as e:
                logging.error(f"Failed to convert monthly index to datetime: {e}")
                monthly_df = pd.DataFrame()
            
            if isinstance(monthly_df.columns, pd.MultiIndex):
                monthly_df.columns = monthly_df.columns.get_level_values(0)
            
            if not monthly_df.empty and all(col in monthly_df.columns for col in required_columns):
                monthly_df = monthly_df[required_columns].dropna()
                monthly_data = format_ohlcv_data(monthly_df, "월봉")
                
                with open(debug_log_path, 'a', encoding='utf-8') as f:
                    f.write(f"포맷팅된 월봉 데이터 개수: {len(monthly_data)}\n")
                    if monthly_data:
                        f.write(f"월봉 데이터 샘플 (최근 5개):\n")
                        for i, item in enumerate(monthly_data[-5:]):
                            f.write(f"  {i+1}. {item}\n")
            else:
                monthly_data = None
                with open(debug_log_path, 'a', encoding='utf-8') as f:
                    f.write("월봉 데이터 처리 실패\n")
        else:
            monthly_data = None
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write("월봉 파일을 찾을 수 없음\n")
        
        logging.info(f"데이터 로딩 디버그 로그 저장됨: {debug_log_path}")
        
        return daily_data, weekly_data, monthly_data
        
    except Exception as e:
        logging.error(f"Error in get_ohlcv_data_for_ai for {ticker}: {e}")
        return None, None, None

def format_ohlcv_data(df, timeframe):
    """OHLCV 데이터를 AI 분석용으로 포맷팅합니다."""
    try:
        formatted_data = []
        for date, row in df.iterrows():
            formatted_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': round(row['Open'], 2),
                'high': round(row['High'], 2),
                'low': round(row['Low'], 2),
                'close': round(row['Close'], 2),
                'volume': int(row['Volume'])
            })
        
        return formatted_data
        
    except Exception as e:
        logging.error(f"Error formatting OHLCV data: {e}")
        return []

def perform_ai_analysis(ticker, daily_data, weekly_data, monthly_data, market_type='KOSPI', company_name=None):
    """AI 분석을 수행합니다."""
    try:
        # 새로운 AI 분석 서비스 사용
        from services.analysis.ai_analysis_service import AIAnalysisService
        ai_service = AIAnalysisService()
        
        # AI 분석 수행
        analysis_result, error = ai_service.analyze_stock(ticker, market_type, company_name)
        
        return analysis_result, error
        
    except Exception as e:
        error_msg = f"AI 분석 중 오류 발생: {e}"
        logging.error(error_msg)
        return None, error_msg

def perform_ai_analysis_with_data(ticker, daily_data, weekly_data, monthly_data, market_type='KOSPI', company_name=None):
    """[2025-08-09 추가] 지표 포함 데이터로 AI 분석을 수행합니다."""
    try:
        from services.analysis.ai_analysis_service import AIAnalysisService
        ai_service = AIAnalysisService()
        
        # 이미 로딩된 지표 포함 데이터를 AI 서비스에 직접 전달
        analysis_result, error = ai_service.analyze_stock_with_data(
            ticker, daily_data, weekly_data, monthly_data, market_type, company_name
        )
        
        logging.info(f"[{ticker}] AI 분석 완료 - 지표 포함 데이터 사용")
        return analysis_result, error
        
    except Exception as e:
        error_msg = f"AI 분석 중 오류 발생: {e}"
        logging.error(error_msg)
        return None, error_msg

def get_ohlcv_with_indicators(ticker, timeframe, market_type='KOSPI'):
    """OHLCV 데이터와 지표 데이터를 함께 가져옵니다."""
    try:
        import glob
        import pandas as pd
        
        logging.info(f"get_ohlcv_with_indicators: 시작 - 티커: {ticker}, 타임프레임: {timeframe}, 시장: {market_type}")
        
        # market_type을 실제 폴더명으로 변환
        if market_type.upper() in ['KOSPI', 'KOSDAQ']:
            actual_market_type = market_type.upper()
        elif market_type.upper() == 'US':
            actual_market_type = 'US'
        else:
            # 기본값은 KOSPI
            actual_market_type = 'KOSPI'
        
        logging.info(f"get_ohlcv_with_indicators: 실제 폴더명: {actual_market_type}")
        # 디버그: 최신 파일 경로 확인 (OHLCV / Indicators)
        try:
            from services.market.file_management_service import FileManagementService
            fms = FileManagementService()
            latest_ohlcv_path = fms.get_latest_file(ticker, 'ohlcv', actual_market_type, timeframe)
            latest_ind_path = fms.get_latest_file(ticker, 'indicators', actual_market_type, timeframe)
            logging.info(f"get_ohlcv_with_indicators: 최신 경로 확인 - OHLCV={latest_ohlcv_path}, IND={latest_ind_path}")
        except Exception as path_err:
            logging.warning(f"get_ohlcv_with_indicators: 최신 경로 확인 실패: {path_err}")
        
        # [2025-08-09 수정 전 코드 - 주석 처리]
        # 지표 파일 패턴 (자체 검색 방식 - 문제 있음)
        # data_dir = os.path.join("static/data", actual_market_type)
        # indicator_pattern = os.path.join(data_dir, f"{ticker}_indicators_{timeframe}_*.csv")
        # logging.info(f"get_ohlcv_with_indicators: 지표 파일 패턴: {indicator_pattern}")
        # indicator_files = glob.glob(indicator_pattern)
        
        # [2025-08-09 수정] admin_home과 동일한 방식으로 지표 데이터 로드
        try:
            from services.technical_indicators_service import TechnicalIndicatorsService
            technical_service = TechnicalIndicatorsService()
            
            # 지표 데이터 로드 (인자 순서 교정, caller 제거)
            indicators_df = technical_service.read_indicators_csv(ticker, actual_market_type, timeframe)
            
            # None 체크 및 DataFrame 검증 강화
            if indicators_df is None:
                logging.warning(f"get_ohlcv_with_indicators: [{ticker}] {timeframe} TechnicalIndicatorsService에서 None 반환")
                indicators_df = pd.DataFrame()  # 빈 DataFrame으로 초기화
            elif not isinstance(indicators_df, pd.DataFrame):
                logging.warning(f"get_ohlcv_with_indicators: [{ticker}] {timeframe} TechnicalIndicatorsService에서 DataFrame이 아닌 타입 반환: {type(indicators_df)}")
                indicators_df = pd.DataFrame()  # 빈 DataFrame으로 초기화
            
            if indicators_df.empty:
                logging.warning(f"get_ohlcv_with_indicators: [{ticker}] {timeframe}에 대한 지표 데이터가 비어있음 (admin_home 방식)")
                # 기본 OHLCV 데이터 반환
                daily_data, weekly_data, monthly_data = get_ohlcv_data_for_ai(ticker, market_type)
                
                if timeframe == 'd':
                    return daily_data
                elif timeframe == 'w':
                    return weekly_data
                elif timeframe == 'm':
                    return monthly_data
                else:
                    return daily_data
            
            logging.info(f"get_ohlcv_with_indicators: [{ticker}] 지표 데이터 로딩 성공 (admin_home 방식) - 형태: {indicators_df.shape}")
            
        except Exception as e:
            logging.error(f"get_ohlcv_with_indicators: [{ticker}] 지표 로딩 실패 (admin_home 방식): {e}")
            # Fallback: 서비스 함수를 그대로 사용 (직접 CSV 파싱 제거, 메타데이터 문제 방지)
            try:
                indicators_df = technical_service.read_indicators_csv(ticker, actual_market_type, timeframe)
                try:
                    shape_info = getattr(indicators_df, 'shape', None)
                    cols_preview = list(indicators_df.columns)[:12] if hasattr(indicators_df, 'columns') else []
                    logging.info(f"get_ohlcv_with_indicators: [{ticker}] indicators_df 로딩 완료 - shape={shape_info}, cols_preview={cols_preview}")
                except Exception as info_err:
                    logging.warning(f"get_ohlcv_with_indicators: indicators_df 정보 로깅 실패: {info_err}")
            except Exception as e2:
                logging.error(f"get_ohlcv_with_indicators: [{ticker}] 지표 로딩 재시도 실패: {e2}")
                indicators_df = pd.DataFrame()
        
        logging.info(f"get_ohlcv_with_indicators: [{ticker}] 지표 데이터 형태: {indicators_df.shape}")
        logging.info(f"get_ohlcv_with_indicators: [{ticker}] 지표 데이터 컬럼들: {list(indicators_df.columns)}")
        
        if indicators_df.empty:
            logging.warning(f"get_ohlcv_with_indicators: [{ticker}] {timeframe}에 대한 지표 데이터가 비어있음")
            # get_ohlcv_data_for_ai는 튜플을 반환하므로 timeframe에 따라 적절한 데이터 반환
            daily_data, weekly_data, monthly_data = get_ohlcv_data_for_ai(ticker, market_type)
            
            if timeframe == 'd':
                logging.info(f"get_ohlcv_with_indicators: [{ticker}] 일봉 데이터 반환 (개수: {len(daily_data) if daily_data else 0})")
                return daily_data
            elif timeframe == 'w':
                logging.info(f"get_ohlcv_with_indicators: [{ticker}] 주봉 데이터 반환 (개수: {len(weekly_data) if weekly_data else 0})")
                return weekly_data
            elif timeframe == 'm':
                logging.info(f"get_ohlcv_with_indicators: [{ticker}] 월봉 데이터 반환 (개수: {len(monthly_data) if monthly_data else 0})")
                return monthly_data
            else:
                logging.warning(f"get_ohlcv_with_indicators: [{ticker}] 알 수 없는 timeframe: {timeframe}, 일봉 데이터 반환")
                return daily_data
        
        # OHLCV + 지표 + CrossInfo 병합
        try:
            from services.market.data_reading_service import DataReadingService
            drs = DataReadingService()
            ohlcv_df = drs.read_ohlcv_csv(ticker, actual_market_type, timeframe)
            if ohlcv_df is None or ohlcv_df.empty:
                logging.warning(f"get_ohlcv_with_indicators: [{ticker}] OHLCV 데이터 없음 ({timeframe})")
            else:
                # 2025-08-16: 병합 충돌 방지 - indicators_df의 OHLCV/메타 컬럼 전체 제거 후 병합
                try:
                    drop_candidates = {'open','high','low','close','volume','adj close','date','date_index','time_index'}
                    cols_to_drop = [col for col in indicators_df.columns if str(col).strip().lower() in drop_candidates]
                    if cols_to_drop:
                        logging.info(f"get_ohlcv_with_indicators: [{ticker}] 지표 DF 충돌 컬럼 제거: {cols_to_drop}")
                        indicators_df = indicators_df.drop(columns=cols_to_drop, errors='ignore')
                except Exception as drop_err:
                    logging.warning(f"get_ohlcv_with_indicators: [{ticker}] 충돌 컬럼 제거 중 경고: {drop_err}")

                # 인덱스 시간대 정규화(양쪽 tz-naive)
                try:
                    if isinstance(ohlcv_df.index, pd.DatetimeIndex) and ohlcv_df.index.tz is not None:
                        ohlcv_df.index = ohlcv_df.index.tz_localize(None)
                    if isinstance(indicators_df.index, pd.DatetimeIndex) and indicators_df.index.tz is not None:
                        indicators_df.index = indicators_df.index.tz_localize(None)
                except Exception:
                    pass

                indicators_df = ohlcv_df.join(indicators_df, how='left')
                logging.info(f"get_ohlcv_with_indicators: [{ticker}] OHLCV+지표 병합 완료: {indicators_df.shape}")
            # CrossInfo 병합 (갭/EMA 배열 정보) - 컬럼 자동 매핑 포함
            try:
                cross_df = drs.read_crossinfo_csv(ticker, actual_market_type)
                if cross_df is not None and not cross_df.empty:
                    # 날짜 컬럼 정규화
                    if 'Date' in cross_df.columns:
                        cross_df['Date'] = pd.to_datetime(cross_df['Date'])
                        cross_df.set_index('Date', inplace=True)
                    # 자동 매핑: 다양한 컬럼명 변형을 표준 키로 정규화
                    import re
                    def _norm(s: str) -> str:
                        return re.sub(r"[^a-z0-9]", "", s.lower())

                    target_to_aliases = {
                        'Close_Gap_EMA20': ['Close_Gap_EMA20','CloseGapEMA20','close_gap_ema20','Close-EMA20-Gap','Gap_EMA20','GapEMA20','Close_EMA20_Gap'],
                        'Close_Gap_EMA40': ['Close_Gap_EMA40','CloseGapEMA40','close_gap_ema40','Close-EMA40-Gap','Gap_EMA40','GapEMA40','Close_EMA40_Gap'],
                        'EMA_Array_Order': ['EMA_Array_Order','EMAArrayOrder','ema_array_order','EMA_Order','EMA Array Order','EmaArrayOrder']
                    }
                    normalized_aliases = {t: {_norm(a) for a in aliases} for t, aliases in target_to_aliases.items()}
                    resolved_cols = {}  # {target: original_col}
                    for original_col in list(cross_df.columns):
                        ncol = _norm(original_col)
                        for target, nset in normalized_aliases.items():
                            if ncol in nset and target not in resolved_cols:
                                resolved_cols[target] = original_col
                                break
                    if resolved_cols:
                        sub_df = cross_df[list(resolved_cols.values())].rename(columns={v: k for k, v in resolved_cols.items()})
                        indicators_df = indicators_df.join(sub_df, how='left')
                        logging.info(f"get_ohlcv_with_indicators: [{ticker}] CrossInfo 자동매핑 병합 완료: targets={list(resolved_cols.keys())}")
            except Exception as cx_err:
                logging.warning(f"get_ohlcv_with_indicators: [{ticker}] CrossInfo 병합 실패: {cx_err}")
        except Exception as merge_err:
            logging.warning(f"get_ohlcv_with_indicators: [{ticker}] 병합 준비 실패: {merge_err}")

        # 병합 후 최근 31개 데이터 선택 (지표 계산을 위해 31개 필요)
        core_cols = ['Open','High','Low','Close','Volume']
        missing_core = [c for c in core_cols if c not in indicators_df.columns]
        if missing_core:
            logging.warning(f"get_ohlcv_with_indicators: [{ticker}] 핵심 OHLCV 컬럼 누락: {missing_core} (병합 실패 가능)")
        recent_data = indicators_df.tail(31)
        logging.info(f"get_ohlcv_with_indicators: [{ticker}] 최근 31개 데이터 선택됨 (post-merge)")

        # 데이터를 딕셔너리 리스트로 변환
        data_list = []
        for i, (date, row) in enumerate(recent_data.iterrows()):
            try:
                # 안전 접근: 컬럼 부재/대소문자 차이/NaN 대응
                def gv(r, k, default=None):
                    return r[k] if (k in r and pd.notna(r[k])) else default
                data_point = {
                    'date': date.strftime('%Y-%m-%d'),
                    'open': round(gv(row, 'Open', 0), 2),
                    'high': round(gv(row, 'High', 0), 2),
                    'low': round(gv(row, 'Low', 0), 2),
                    'close': round(gv(row, 'Close', 0), 2),
                    'volume': int(gv(row, 'Volume', 0) or 0),
                    'ema5': round(gv(row, 'EMA5'), 2) if gv(row, 'EMA5') is not None else None,
                    'ema20': round(gv(row, 'EMA20'), 2) if gv(row, 'EMA20') is not None else None,
                    'ema40': round(gv(row, 'EMA40'), 2) if gv(row, 'EMA40') is not None else None,
                    'macd': round(gv(row, 'MACD'), 4) if gv(row, 'MACD') is not None else None,
                    'macd_signal': round(gv(row, 'MACD_Signal'), 4) if gv(row, 'MACD_Signal') is not None else None,
                    'macd_histogram': round(gv(row, 'MACD_Histogram'), 4) if gv(row, 'MACD_Histogram') is not None else None,
                    'bb_upper': round(gv(row, 'BB_Upper'), 2) if gv(row, 'BB_Upper') is not None else None,
                    'bb_middle': round(gv(row, 'BB_Middle'), 2) if gv(row, 'BB_Middle') is not None else None,
                    'bb_lower': round(gv(row, 'BB_Lower'), 2) if gv(row, 'BB_Lower') is not None else None,
                    'rsi': round(gv(row, 'RSI'), 2) if gv(row, 'RSI') is not None else None,
                    'stoch_k': round(gv(row, 'Stoch_K'), 2) if gv(row, 'Stoch_K') is not None else None,
                    'stoch_d': round(gv(row, 'Stoch_D'), 2) if gv(row, 'Stoch_D') is not None else None,
                    'ichimoku_tenkan': round(gv(row, 'Ichimoku_Tenkan'), 2) if gv(row, 'Ichimoku_Tenkan') is not None else None,
                    'ichimoku_kijun': round(gv(row, 'Ichimoku_Kijun'), 2) if gv(row, 'Ichimoku_Kijun') is not None else None,
                    'ichimoku_senkou_a': round(gv(row, 'Ichimoku_Senkou_A'), 2) if gv(row, 'Ichimoku_Senkou_A') is not None else None,
                    'ichimoku_senkou_b': round(gv(row, 'Ichimoku_Senkou_B'), 2) if gv(row, 'Ichimoku_Senkou_B') is not None else None,
                    'volume_ratio_5d': round(gv(row, 'Volume_Ratio_5d'), 2) if gv(row, 'Volume_Ratio_5d') is not None else None,
                    'volume_ratio_20d': round(gv(row, 'Volume_Ratio_20d'), 2) if gv(row, 'Volume_Ratio_20d') is not None else None,
                    'volume_ratio_40d': round(gv(row, 'Volume_Ratio_40d'), 2) if gv(row, 'Volume_Ratio_40d') is not None else None,
                    'close_gap_ema20': round(gv(row, 'Close_Gap_EMA20'), 2) if gv(row, 'Close_Gap_EMA20') is not None else None,
                    'close_gap_ema40': round(gv(row, 'Close_Gap_EMA40'), 2) if gv(row, 'Close_Gap_EMA40') is not None else None,
                }
                data_list.append(data_point)
                
                # EMA 배열 문자열 보강: (가능 시)
                try:
                    if 'EMA_Array_Order' in row and pd.notna(row['EMA_Array_Order']):
                        data_point['ema_array'] = {'full_array': str(row['EMA_Array_Order'])}
                except Exception:
                    pass

                # 첫 번째 항목의 키들을 로깅
                if i == 0:
                    # logging.info(f"get_ohlcv_with_indicators: [{ticker}] 첫 번째 데이터 포인트 키들: {list(data_point.keys())}")
                    # logging.info(f"get_ohlcv_with_indicators: [{ticker}] 첫 번째 데이터 포인트 샘플: {data_point}")
                    pass
                
            except Exception as row_error:
                logging.error(f"get_ohlcv_with_indicators: [{ticker}] 행 {i} 처리 오류: {row_error}")
                logging.error(f"get_ohlcv_with_indicators: [{ticker}] 문제 행 데이터: {row}")
                continue
        
        logging.info(f"get_ohlcv_with_indicators: [{ticker}] 성공적으로 {len(data_list)}개 데이터 포인트 로드됨 ({timeframe})")
        
        # 지표 데이터가 포함되었는지 확인
        if data_list and len(data_list) > 0:
            first_item = data_list[0]
            if 'ema5' in first_item:
                logging.info(f"get_ohlcv_with_indicators: [{ticker}] 지표 데이터가 포함된 데이터 반환")
            else:
                logging.warning(f"get_ohlcv_with_indicators: [{ticker}] 지표 데이터가 포함되지 않은 데이터 반환")
        
        return data_list
        
    except Exception as e:
        logging.error(f"get_ohlcv_with_indicators: [{ticker}] 지표와 함께 OHLCV 가져오기 오류: {e}")
        # 에러 발생 시 timeframe별 기본 OHLCV 데이터 반환 (튜플 반환 금지)
        daily_data, weekly_data, monthly_data = get_ohlcv_data_for_ai(ticker, market_type)
        if timeframe == 'd':
            return daily_data
        if timeframe == 'w':
            return weekly_data
        if timeframe == 'm':
            return monthly_data
        return daily_data

def format_data_with_indicators_for_prompt(data):
    """지표 데이터를 포함한 데이터를 프롬프트용으로 포맷팅합니다."""
    logging.info(f"format_data_with_indicators_for_prompt: 데이터 개수 {len(data) if data else 0}")
    
    if not data:
        logging.warning("format_data_with_indicators_for_prompt: 데이터가 비어있음")
        return "데이터 없음"
    
    try:
        # 데이터 타입 검증
        if not isinstance(data, list):
            logging.error(f"format_data_with_indicators_for_prompt: 데이터가 리스트가 아님. 타입: {type(data)}")
            return "데이터 형식 오류"
        
        if len(data) == 0:
            logging.warning("format_data_with_indicators_for_prompt: 빈 리스트")
            return "데이터 없음"
        
        # 첫 번째 항목이 딕셔너리인지 확인
        first_item = data[0]
        if not isinstance(first_item, dict):
            logging.error(f"format_data_with_indicators_for_prompt: 첫 번째 항목이 딕셔너리가 아님. 타입: {type(first_item)}")
            return "데이터 형식 오류"
        
        logging.info(f"format_data_with_indicators_for_prompt: 첫 번째 항목 키들: {list(first_item.keys())}")
        # 디버그: 지표 키 미존재 시 원인 추적 로그 강화
        try:
            missing_keys = []
            for key in ['ema5','ema20','ema40','macd','macd_signal','macd_histogram','bb_upper','bb_middle','bb_lower','rsi','stoch_k','stoch_d']:
                if key not in first_item:
                    missing_keys.append(key)
            if missing_keys:
                logging.warning(f"format_data_with_indicators_for_prompt: 지표 키 누락: {missing_keys}")
        except Exception as mk_err:
            logging.warning(f"format_data_with_indicators_for_prompt: 지표 키 점검 실패: {mk_err}")
        
        # 첫 번째 항목 확인 및 디버깅
        if data and len(data) > 0:
            first_item = data[0]
            logging.info(f"format_data_with_indicators_for_prompt: 첫 번째 항목 키들: {list(first_item.keys())}")
            
            # 지표 키들 확인 및 로깅
            indicator_keys = []
            if 'ema5' in first_item:
                indicator_keys = [
                    'ema5', 'ema20', 'ema40', 'macd', 'macd_signal', 'macd_histogram',
                    'rsi', 'bb_upper', 'bb_middle', 'bb_lower', 'stoch_k', 'stoch_d',
                    'ichimoku_tenkan', 'ichimoku_kijun', 'volume_ratio_5d', 'volume_ratio_20d', 'volume_ratio_40d'
                ]
                logging.info(f"format_data_with_indicators_for_prompt: 지표 키들 발견: {indicator_keys}")
            else:
                logging.warning("format_data_with_indicators_for_prompt: ema5 키가 없음 - 지표 데이터가 포함되지 않음")
                # 기본 OHLCV 데이터만 처리
                indicator_keys = []
        
        formatted_lines = []
        
        # 헤더 라인 추가
        if indicator_keys:
            header = "날짜, 시가, 고가, 저가, 종가, 거래량 | 지표: " + ", ".join([key.upper() for key in indicator_keys])
            formatted_lines.append(header)
            logging.info(f"format_data_with_indicators_for_prompt: 헤더 추가: {header}")
        else:
            header = "날짜, 시가, 고가, 저가, 종가, 거래량"
            formatted_lines.append(header)
            logging.info(f"format_data_with_indicators_for_prompt: 기본 헤더 추가: {header}")
        
        # 데이터 라인들 추가
        processed_count = 0
        for i, item in enumerate(data):
            try:
                # 기본 OHLCV 데이터 - 키 이름 대소문자 구분 없이 처리
                open_val = item.get('open') or item.get('Open', 0)
                high_val = item.get('high') or item.get('High', 0)
                low_val = item.get('low') or item.get('Low', 0)
                close_val = item.get('close') or item.get('Close', 0)
                volume_val = item.get('volume') or item.get('Volume', 0)
                date_val = item.get('date') or item.get('Date', '')
                
                # numpy.float64 타입 처리
                if hasattr(open_val, 'item'):
                    open_val = open_val.item()
                if hasattr(high_val, 'item'):
                    high_val = high_val.item()
                if hasattr(low_val, 'item'):
                    low_val = low_val.item()
                if hasattr(close_val, 'item'):
                    close_val = close_val.item()
                if hasattr(volume_val, 'item'):
                    volume_val = volume_val.item()
                
                # float 변환 및 안전한 처리
                try:
                    open_val = float(open_val) if open_val is not None else 0
                    high_val = float(high_val) if high_val is not None else 0
                    low_val = float(low_val) if low_val is not None else 0
                    close_val = float(close_val) if close_val is not None else 0
                    volume_val = int(volume_val) if volume_val is not None else 0
                except (ValueError, TypeError) as conv_error:
                    logging.error(f"format_data_with_indicators_for_prompt: 값 변환 오류 (항목 {i}): {conv_error}")
                    open_val = high_val = low_val = close_val = volume_val = 0
                
                line = f"{date_val}, {open_val:.2f}, {high_val:.2f}, {low_val:.2f}, {close_val:.2f}, {volume_val}"
                
                # 지표 데이터 추가
                if indicator_keys:
                    indicator_values = []
                    for key in indicator_keys:
                        value = item.get(key)
                        if value is not None and not pd.isna(value):
                            # numpy.float64 타입 처리
                            if hasattr(value, 'item'):
                                value = value.item()
                            try:
                                indicator_values.append(f"{float(value):.4f}")
                            except (ValueError, TypeError) as ind_error:
                                logging.error(f"format_data_with_indicators_for_prompt: 지표 값 변환 오류 (키 {key}, 값 {value}): {ind_error}")
                                indicator_values.append("")
                        else:
                            indicator_values.append("")
                    line += " | " + ", ".join(indicator_values)
                
                formatted_lines.append(line)
                processed_count += 1
                
            except Exception as item_error:
                logging.error(f"format_data_with_indicators_for_prompt: 항목 {i} 포맷팅 오류: {item_error}")
                logging.error(f"format_data_with_indicators_for_prompt: 문제 항목 데이터: {item}")
                continue
        
        result = '\n'.join(formatted_lines)
        logging.info(f"format_data_with_indicators_for_prompt: 성공적으로 처리된 항목 수: {processed_count}/{len(data)}")
        logging.info(f"format_data_with_indicators_for_prompt: 결과 길이: {len(result)} 문자")
        
        return result
        
    except Exception as e:
        logging.error(f"format_data_with_indicators_for_prompt: 전체 포맷팅 오류: {e}")
        return "데이터 포맷팅 오류"

def load_ai_prompt_template():
    """AI 분석 프롬프트 템플릿을 로드합니다."""
    try:
        # 루트 디렉토리의 ai_analysis_prompt.txt 파일을 사용
        prompt_path = os.path.join(os.path.dirname(__file__), '..', 'ai_analysis_prompt.txt')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logging.error(f"Error loading prompt template: {e}")
        # 기본 프롬프트 반환
        return """밑에 제공되는 {ticker} 종목의 OHLCV 데이터를 기반으로 EMA, MACD, 볼린저밴드, 일목균형표, RSI, 스토캐스틱 오실레이션 등 가용한 기술적 지표들을 계산하여 차트를 분석 후, 스윙 투자자의 매수 및 매도 타이밍에 대한 의견을 개진해라. 이 분석의 핵심내용을 세 문장으로 요약해 제일 첫머리에 **핵심 요약**의 제목아래 번호를 붙여 제시해라.상세분석은 일봉-주봉-월봉의 순으로 배열해라.

일봉 데이터 (최근 30일):
날짜, 시가, 고가, 저가, 종가, 거래량
{daily_ohlcv_data}

주봉 데이터 (최근 30주):
{weekly_ohlcv_data}

월봉 데이터 (최근 30개월):
{monthly_ohlcv_data}"""

def format_data_for_prompt(data):
    """데이터를 프롬프트용으로 포맷팅합니다."""
    if not data:
        return "데이터 없음"
    
    # 최근 데이터만 선택 (일봉: 30일, 주봉: 30주, 월봉: 30개월)
    if len(data) > 30:
        data = data[-30:]  # 최근 30개만 선택
    
    formatted = "날짜, 시가, 고가, 저가, 종가, 거래량\n"
    for item in data:
        formatted += f"{item['date']}, {item['open']}, {item['high']}, {item['low']}, {item['close']}, {item['volume']}\n"
    
    return formatted



@analysis_bp.route('/<ticker>')
@login_required
def analysis_page(ticker):
    """개별 종목 분석 페이지"""
    stock = Stock.query.filter_by(ticker=ticker).first_or_404()
    
    cache_service = CacheService()
    unified_service = UnifiedMarketAnalysisService(cache_service)
    
    # 종합 분석 데이터 가져오기
    analysis_data = unified_service.analyze_stock_comprehensive(stock.ticker, stock.market_type)
    
    return render_template('analysis/analysis_page.html', stock=stock, analysis_data=analysis_data)

@analysis_bp.route('/analysis/<ticker>')
@login_required
def analyze_ticker(ticker):
    """상세분석 버튼을 위한 라우트 - 시장 타입을 자동으로 감지하여 AI 분석 페이지로 리다이렉트"""
    try:
        ticker = ticker.upper()
        
        # 시장 타입 감지 (파일 존재 여부로 판단)
        kospi_data_dir = os.path.join("static/data", "KOSPI")
        kosdaq_data_dir = os.path.join("static/data", "KOSDAQ")
        us_data_dir = os.path.join("static/data", "US")
        
        market_type = 'KOSPI'  # 기본값
        
        # KOSPI, KOSDAQ, US 디렉토리에서 해당 티커의 데이터 파일 확인
        if os.path.exists(kospi_data_dir):
            kospi_files = [f for f in os.listdir(kospi_data_dir) if f.startswith(f"{ticker}_")]
            if kospi_files:
                market_type = 'KOSPI'
            else:
                # KOSDAQ 디렉토리 확인
                if os.path.exists(kosdaq_data_dir):
                    kosdaq_files = [f for f in os.listdir(kosdaq_data_dir) if f.startswith(f"{ticker}_")]
                    if kosdaq_files:
                        market_type = 'KOSDAQ'
                    else:
                        # US 디렉토리 확인
                        if os.path.exists(us_data_dir):
                            us_files = [f for f in os.listdir(us_data_dir) if f.startswith(f"{ticker}_")]
                            if us_files:
                                market_type = 'US'
        
        # AI 분석 페이지로 리다이렉트
        return redirect(url_for('analysis.ai_analysis', ticker=ticker, market=market_type))
        
    except Exception as e:
        logging.error(f"Analyze ticker error for {ticker}: {e}")
        return f"분석 오류: {str(e)}", 500

@analysis_bp.route('/ai_analysis/<ticker>/<market>')
@login_required
def ai_analysis(ticker, market):
    """AI 분석 페이지를 렌더링합니다."""
    try:
        ticker = ticker.upper()
        market = market.upper()  # 대문자로 변환 추가
        logging.info(f"AI 분석 시작: {ticker} ({market})")

        # 0) 시장 canonicalization (파일 존재 기반) 및 URL 정합성 확보
        canonical_market = _detect_canonical_market_by_files(ticker, market)
        if canonical_market != market:
            logging.info(f"[CANON] Redirecting to canonical market: {ticker} {market} → {canonical_market}")
            return redirect(url_for('analysis.ai_analysis', ticker=ticker, market=canonical_market))

        # 1) 캐시 신선도 판정 후 즉시 반환 시도 (차트 생성 전에 수행)
        try:
            cached_html = _try_return_cached_analysis_html(ticker, market)
        except Exception:
            cached_html = None
        if cached_html:
            return cached_html

        # 0-LEGACY) 기존 차트 기반 시장 자동 교정 로직 (성능 문제로 비활성화) — 보존용 주석
        # resolved_market = market
        # charts, chart_error = generate_charts(ticker, resolved_market)
        # if chart_error:
        #     logging.info(f"[AUTO-MARKET] Primary market failed for {ticker}/{resolved_market}: {chart_error}")
        #     market_candidates = ['US', 'KOSPI', 'KOSDAQ']
        #     if resolved_market in market_candidates:
        #         market_candidates.remove(resolved_market)
        #         market_candidates.insert(0, resolved_market)
        #     for cand in market_candidates:
        #         try:
        #             data_dir = os.path.join("static", "data", cand)
        #             pattern = os.path.join(data_dir, f"{ticker}_ohlcv_d_*.csv")
        #             if glob.glob(pattern):
        #                 resolved_market = cand
        #                 break
        #         except Exception:
        #             continue
        #     if resolved_market != market:
        #         logging.info(f"[AUTO-MARKET] Resolved market for {ticker}: {resolved_market} (was {market})")
        #         market = resolved_market
        #         charts, chart_error = generate_charts(ticker, market)

        # 2) 여기서부터만 차트 생성 등 비용 작업 수행
        charts, chart_error = generate_charts(ticker, market)

        # 종목명 가져오기
        from models import Stock
        stock = Stock.query.filter_by(ticker=ticker).first()
        company_name = stock.company_name if stock and stock.company_name else ticker
        
        # [2025-08-09 수정 전 코드 - 주석 처리]
        # OHLCV만 로딩 (지표 없음) - AI 프롬프트 데이터 누락의 원인
        # daily_data, weekly_data, monthly_data = get_ohlcv_data_for_ai(ticker, market)
        
        # [2025-08-09 수정] OHLCV + 지표 통합 데이터 로딩 (AI 프롬프트용)
        daily_data = get_ohlcv_with_indicators(ticker, 'd', market)
        weekly_data = get_ohlcv_with_indicators(ticker, 'w', market)
        monthly_data = get_ohlcv_with_indicators(ticker, 'm', market)

        # 데이터 실패 시 한 번 더 시장 교정 재시도
        if (not daily_data) and (not weekly_data) and (not monthly_data):
            logging.info(f"[AUTO-MARKET] Indicator data empty for {ticker}/{market} → probing other markets")
            for cand in ['US', 'KOSPI', 'KOSDAQ']:
                if cand == market:
                    continue
                try:
                    data_dir = os.path.join("static", "data", cand)
                    if glob.glob(os.path.join(data_dir, f"{ticker}_indicators_d_*.csv")) or \
                       glob.glob(os.path.join(data_dir, f"{ticker}_ohlcv_d_*.csv")):
                        market = cand
                        logging.info(f"[AUTO-MARKET] Resolved by indicators/ohlcv presence: {ticker} → {market}")
                        # 재로드
                        charts, chart_error = generate_charts(ticker, market)
                        daily_data = get_ohlcv_with_indicators(ticker, 'd', market)
                        weekly_data = get_ohlcv_with_indicators(ticker, 'w', market)
                        monthly_data = get_ohlcv_with_indicators(ticker, 'm', market)
                        break
                except Exception:
                    continue
        
        # 데이터 부재 시 자동 다운로드/보장은 실행하지 않음
        # 사용자 안내 메시지로 대체: 어드민 홈 새로고침 유도
        analysis_result = None
        analysis_error = None
        if (not daily_data) and (not weekly_data) and (not monthly_data):
            analysis_error = "지표 파일은 존재하지만 읽기 실패로 보입니다. 관리자 홈을 새로고침해 데이터를 재생성한 뒤 다시 시도해 주세요."
        
        # 지표 데이터 가져오기 - get_stock_with_indicators 함수 사용 (어드민 홈과 동일한 구조)
        # [2025-08-09 수정 전 코드 - 주석 처리]
        # stock_data = get_stock_with_indicators(ticker, market)
        # indicators_data = None
        # if stock_data:
        #     indicators_data = {ticker: stock_data}
        # 임시로 빈 데이터 사용 - 이 부분이 페이지 표시 실패의 원인이었음
        # indicators_data = None
        
        # [2025-08-09 수정] admin_home과 동일한 방식으로 지표 데이터 로딩
        try:
            from services.technical_indicators_service import TechnicalIndicatorsService
            
            technical_service = TechnicalIndicatorsService()
            indicators_df = technical_service.read_indicators_csv(ticker, market, 'd')
            
            # None 체크 및 DataFrame 검증 강화
            if indicators_df is None:
                indicators_data = None
                logging.warning(f"[{ticker}] 페이지용 지표 데이터 로딩 실패 - None 반환됨")
            elif not isinstance(indicators_df, pd.DataFrame):
                indicators_data = None
                logging.warning(f"[{ticker}] 페이지용 지표 데이터 로딩 실패 - DataFrame이 아님: {type(indicators_df)}")
            elif indicators_df.empty:
                indicators_data = None
                logging.warning(f"[{ticker}] 페이지용 지표 데이터 로딩 실패 - DataFrame이 비어있음")
            else:
                latest_indicators = indicators_df.iloc[-1]
                
                # [메모] 2025-08-19: 등락률 최신치 조회 경로 단일화
                # 기존 CSV 컬럼 직접 참조는 보존하되, 표준 함수 호출 결과를 우선 사용합니다.
                try:
                    change_pct_value = technical_service.get_latest_change_percent(ticker, 'd', market)
                except Exception:
                    change_pct_value = latest_indicators.get('Change_Percent', 0)

                indicators_data = {ticker: {
                    'indicators': {
                        'ema5': latest_indicators.get('EMA5', 0),
                        'ema20': latest_indicators.get('EMA20', 0),
                        'ema40': latest_indicators.get('EMA40', 0),
                        'macd_line': latest_indicators.get('MACD', 0),
                        'macd_signal': latest_indicators.get('MACD_Signal', 0),
                        'macd_histogram': latest_indicators.get('MACD_Histogram', 0),
                        'rsi': latest_indicators.get('RSI', 0),
                        'stoch_k': latest_indicators.get('Stoch_K', 0),
                        'stoch_d': latest_indicators.get('Stoch_D', 0),
                        'volume_ratio_5d': latest_indicators.get('Volume_Ratio_5d', 0),
                        'volume_ratio_20d': latest_indicators.get('Volume_Ratio_20d', 0),
                        'volume_ratio_40d': latest_indicators.get('Volume_Ratio_40d', 0),
                        'change_percent': change_pct_value
                    },
                    'analysis': {
                        'macd_signals': {},  # 크로스오버는 나중에 처리
                        'ema_signals': {},   # 크로스오버는 나중에 처리
                        'gap_ema20': 0,
                        'gap_ema40': 0,
                        'ema_array': {'full_array': ''}
                    }
                }}
                
                # CrossInfo CSV 읽기 및 새로운 컬럼들 추가 (admin_home과 동일한 방식)
                try:
                    from services.market.data_reading_service import DataReadingService
                    data_reading_service = DataReadingService()
                    # CrossInfo 호출 인자 정리 (caller 인자 제거)
                    crossinfo_df = data_reading_service.read_crossinfo_csv(ticker, market)
                    
                    if not crossinfo_df.empty:
                        latest_crossinfo = crossinfo_df.iloc[-1]

                    # CrossInfo 컬럼명 자동 매핑(표준화)
                    import re
                    def _norm(s: str) -> str:
                        return re.sub(r"[^a-z0-9]", "", str(s).lower())
                    aliases = {
                        'Close_Gap_EMA20': ['Close_Gap_EMA20','CloseGapEMA20','close_gap_ema20','Close-EMA20-Gap','Gap_EMA20','GapEMA20','Close_EMA20_Gap'],
                        'Close_Gap_EMA40': ['Close_Gap_EMA40','CloseGapEMA40','close_gap_ema40','Close-EMA40-Gap','Gap_EMA40','GapEMA40','Close_EMA40_Gap'],
                        'EMA_Array_Order': ['EMA_Array_Order','EMAArrayOrder','ema_array_order','EMA_Order','EMA Array Order','EmaArrayOrder']
                    }
                    norm_map = {k: {_norm(a) for a in v} for k, v in aliases.items()}
                    resolved = {}
                    for col in list(crossinfo_df.columns):
                        n = _norm(col)
                        for tgt, aset in norm_map.items():
                            if n in aset and tgt not in resolved:
                                resolved[tgt] = col
                                break
                        
                        # MACD 근접성 정보 파싱 함수
                        def parse_macd_proximity(proximity_value):
                            """MACD 근접성 정보를 파싱하여 type 값만 반환"""
                            if not proximity_value or proximity_value == 'no_proximity':
                                return 'no_proximity'
                            
                            # 딕셔너리 문자열인 경우 파싱
                            if isinstance(proximity_value, str) and proximity_value.startswith('{'):
                                try:
                                    import ast
                                    proximity_dict = ast.literal_eval(proximity_value)
                                    if isinstance(proximity_dict, dict):
                                        return proximity_dict.get('type', 'no_proximity')
                                except:
                                    pass
                            
                            # 이미 문자열인 경우 그대로 반환
                            return str(proximity_value)
                        
                        # 새로운 컬럼들 추가 (admin_home과 동일)
                        # 표준 키 추출
                        gap20_val = latest_crossinfo.get(resolved.get('Close_Gap_EMA20', 'Close_Gap_EMA20'), 0.0)
                        gap40_val = latest_crossinfo.get(resolved.get('Close_Gap_EMA40', 'Close_Gap_EMA40'), 0.0)
                        order_val = latest_crossinfo.get(resolved.get('EMA_Array_Order', 'EMA_Array_Order'), '')

                        indicators_data[ticker]['analysis'].update({
                            'ema_array_pattern': latest_crossinfo.get('EMA_Array_Pattern', '분석불가'),
                            'ema_array_order': order_val if order_val != '' else '분석불가',
                            'close_gap_ema20': gap20_val,
                            'close_gap_ema40': gap40_val,
                            
                            # MACD 크로스오버 정보
                            'macd_signals': {
                                'type': 'crossover' if latest_crossinfo.get('MACD_Latest_Crossover_Type') else 'normal',
                                'status': latest_crossinfo.get('MACD_Latest_Crossover_Type', '정상'),
                                'latest_crossover_type': latest_crossinfo.get('MACD_Latest_Crossover_Type'),
                                'latest_crossover_date': latest_crossinfo.get('MACD_Latest_Crossover_Date'),
                                'days_since_crossover': latest_crossinfo.get('MACD_Days_Since_Crossover'),
                                'proximity_type': parse_macd_proximity(latest_crossinfo.get('MACD_Current_Proximity'))
                            },
                            
                            # EMA 크로스오버 정보
                            'ema_signals': {
                                'type': 'crossover' if latest_crossinfo.get('EMA_Latest_Crossover_Type') else 'normal',
                                'status': latest_crossinfo.get('EMA_Latest_Crossover_Type', '정상'),
                                'latest_crossover_type': latest_crossinfo.get('EMA_Latest_Crossover_Type'),
                                'latest_crossover_date': latest_crossinfo.get('EMA_Latest_Crossover_Date'),
                                'days_since_crossover': latest_crossinfo.get('EMA_Days_Since_Crossover'),
                                'crossover_pair': latest_crossinfo.get('EMA_Crossover_Pair'),
                                'proximity_type': latest_crossinfo.get('EMA_Current_Proximity', 'no_proximity')
                            }
                        })
                        # 템플릿 호환: ema_array.full_array 채우기
                        try:
                            indicators_data[ticker]['analysis']['ema_array'] = {'full_array': str(order_val) if order_val != '' else ''}
                        except Exception:
                            pass
                        logging.debug(f"[{ticker}] CrossInfo CSV 읽기 성공 - EMA 배열(Order): {order_val}")
                except Exception as e:
                    logging.warning(f"[{ticker}] CrossInfo CSV 읽기 실패: {e}")
                
                logging.info(f"[{ticker}] 페이지용 지표 데이터 로딩 성공 (admin_home과 완전히 동일한 방식)")
                
        except Exception as e:
            logging.error(f"[{ticker}] 지표 데이터 로딩 오류: {e}")
            indicators_data = None
        
        logging.info(f"ai_analysis: 지표 데이터 결과 - {indicators_data}")
        
        # [2025-08-09 수정 전 코드 - 주석 처리]
        # AI 분석 수행 (전달받은 데이터 무시되고 내부에서 다시 로딩하는 문제)
        # analysis_result, analysis_error = perform_ai_analysis(ticker, daily_data, weekly_data, monthly_data, market, company_name)
        
        # [2025-08-09 수정] 지표 포함 데이터로 AI 분석 수행 (데이터 없는 경우 스킵하고 안내 메시지 표시)
        if analysis_error is None:
            analysis_result, analysis_error = perform_ai_analysis_with_data(
                ticker, daily_data, weekly_data, monthly_data, market, company_name
            )
        
        # HTML 렌더링
        html_content = render_template('analysis/ai_analysis.html',
                             ticker=ticker,
                             company_name=company_name,
                             market=market,
                             charts=charts,
                             chart_error=chart_error,
                             analysis_result=analysis_result,
                             analysis_error=analysis_error,
                             indicators_data=indicators_data,
                             daily_data=daily_data,
                             weekly_data=weekly_data,
                             monthly_data=monthly_data)
        
        # static/analysis 폴더에 HTML 파일 자동 저장
        try:
            analysis_dir = os.path.join("static", "analysis")
            os.makedirs(analysis_dir, exist_ok=True)
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{ticker}_AI_Analysis_{market}_{timestamp}.html"
            filepath = os.path.join(analysis_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logging.info(f"AI analysis HTML saved: {filepath}")
        except Exception as save_error:
            logging.error(f"Failed to save HTML file: {save_error}")
        
        return html_content
        
    except Exception as e:
        logging.error(f"AI analysis page error: {e}")
        return render_template('analysis/ai_analysis.html',
                             ticker=ticker,
                             market=market,
                             error=str(e))

@analysis_bp.route('/view_chart/<ticker>')
@login_required
def view_chart(ticker):
    """차트 보기 - 저장된 indicator 데이터를 사용하여 차트를 생성합니다."""
    try:
        ticker = ticker.upper()
        
        # 시장 타입 감지
        kospi_data_dir = os.path.join("static/data", "KOSPI")
        kosdaq_data_dir = os.path.join("static/data", "KOSDAQ")
        us_data_dir = os.path.join("static/data", "US")
        
        market_type = 'KOSPI'  # 기본값
        
        # KOSPI, KOSDAQ, US 디렉토리에서 해당 티커의 데이터 파일 확인
        if os.path.exists(kospi_data_dir):
            kospi_files = [f for f in os.listdir(kospi_data_dir) if f.startswith(f"{ticker}_")]
            if kospi_files:
                market_type = 'KOSPI'
            else:
                # KOSDAQ 디렉토리 확인
                if os.path.exists(kosdaq_data_dir):
                    kosdaq_files = [f for f in os.listdir(kosdaq_data_dir) if f.startswith(f"{ticker}_")]
                    if kosdaq_files:
                        market_type = 'KOSDAQ'
                    else:
                        # US 디렉토리 확인
                        if os.path.exists(us_data_dir):
                            us_files = [f for f in os.listdir(us_data_dir) if f.startswith(f"{ticker}_")]
                            if us_files:
                                market_type = 'US'
        
        # 차트 생성
        charts, chart_error = generate_charts(ticker, market_type)
        
        if chart_error:
            return f"차트 생성 실패: {chart_error}", 500
        
        return render_template('analysis/chart_view.html',
                             ticker=ticker,
                             charts=charts)
        
    except Exception as e:
        logging.error(f"Chart view error for {ticker}: {e}")
        return f"차트 보기 오류: {str(e)}", 500 

@analysis_bp.route('/api/indicators/<ticker>/<market_type>/<timeframe>')
def get_indicators_api(ticker, market_type, timeframe):
    """특정 종목의 지표 데이터를 JSON으로 반환"""
    try:
        technical_service = TechnicalIndicatorsService()
        indicators_df = technical_service.read_indicators_csv(ticker, timeframe, market_type)
        
        if indicators_df.empty:
            return jsonify({'error': '지표 데이터를 찾을 수 없습니다.'}), 404
            
        return jsonify(indicators_df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/api/crossinfo/<ticker>/<market_type>')
def get_crossinfo_api(ticker, market_type):
    """특정 종목의 CrossInfo 데이터를 JSON으로 반환"""
    try:
        data_reading_service = DataReadingService()
        crossinfo_df = data_reading_service.read_crossinfo_csv(ticker, market_type)

        if crossinfo_df.empty:
            return jsonify({'error': 'CrossInfo 데이터를 찾을 수 없습니다.'}), 404

        return jsonify(crossinfo_df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500 