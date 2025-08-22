"""
Market Data Orchestrator Service
/market/ 디렉토리의 모든 서비스들을 유기적으로 연결하는 오케스트레이터
"""

import os
import logging
import pandas as pd
import time
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ProcessingResult:
    """처리 결과 데이터 클래스"""
    success: bool
    ticker: str
    market_type: str
    daily_path: Optional[str] = None
    weekly_path: Optional[str] = None
    monthly_path: Optional[str] = None
    indicators_path: Optional[str] = None
    error_message: Optional[str] = None
    error_stage: Optional[str] = None
    processing_time: Optional[float] = None
    data_rows: Optional[int] = None
    indicators_rows: Optional[int] = None

class MarketDataOrchestrator:
    """Market Data 오케스트레이터 서비스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 의존성 서비스들 초기화
        from .data_download_service import DataDownloadService
        from .data_storage_service import DataStorageService
        from .data_reading_service import DataReadingService
        from .data_conversion_service import DataConversionService
        from .data_validation_service import DataValidationService
        from .market_status_service import MarketStatusService
        from .file_management_service import FileManagementService
        from services.technical_indicators_service import TechnicalIndicatorsService
        
        self.download_service = DataDownloadService()
        self.storage_service = DataStorageService()
        self.reading_service = DataReadingService()
        self.conversion_service = DataConversionService()
        self.validation_service = DataValidationService()
        self.market_status_service = MarketStatusService()
        self.file_management_service = FileManagementService()
        self.indicators_service = TechnicalIndicatorsService()
    
    def process_stock_data_complete(self, ticker: str, market_type: str) -> ProcessingResult:
        """완전한 주식 데이터 처리 워크플로우"""
        start_time = datetime.now()
        trace_id = f"{ticker}-{uuid.uuid4().hex[:8]}"
        
        try:
            # 비활성 종목 가드: 저장/처리 방지
            try:
                from models import Stock
                stock_active = Stock.query.filter_by(ticker=ticker, is_active=True).first()
                if not stock_active:
                    self.logger.info(json.dumps({
                        "event": "orchestrator.skip_inactive",
                        "trace": trace_id,
                        "ticker": ticker,
                        "market": market_type
                    }, ensure_ascii=False))
                    return self._compose_error_result(ticker, market_type, "inactive_stock", "precheck", start_time)
            except Exception:
                # DB 접근 불가 시에는 가드를 건너뛰되, 로깅만 남김
                self.logger.debug(f"[{ticker}] 활성 상태 확인 건너뜀 (DB 접근 불가)")
            # 시작 로그 (구조화)
            self.logger.info(json.dumps({
                "event": "orchestrator.start",
                "trace": trace_id,
                "ticker": ticker,
                "market": market_type,
                "start_ms": int(time.time() * 1000)
            }, ensure_ascii=False))
            
            # 0. 데이터 전략 결정(신선도 우선 적용)
            try:
                strategy = self.file_management_service.determine_data_strategy(ticker, market_type)
            except Exception:
                strategy = "download_fresh"

            # 1. 기존 데이터 확인 (전략이 기존 사용일 때만)
            if strategy != "download_fresh":
                existing_check = self._check_existing_data(ticker, market_type)
                if existing_check['use_existing']:
                    self.logger.info(json.dumps({
                        "event": "orchestrator.use_existing",
                        "trace": trace_id,
                        "ticker": ticker,
                        "market": market_type,
                        "reason": existing_check.get('reason')
                    }, ensure_ascii=False))
                    return self._process_with_existing_data(ticker, market_type, existing_check)
            
            # 2. 새 데이터 다운로드
            self.logger.info(json.dumps({
                "event": "download.begin",
                "trace": trace_id,
                "ticker": ticker,
                "market": market_type
            }, ensure_ascii=False))
            df = self._download_fresh_data(ticker, market_type)
            if df.empty:
                return self._compose_error_result(ticker, market_type, "데이터 다운로드 실패", "download", start_time)
            else:
                self.logger.info(json.dumps({
                    "event": "download.end",
                    "trace": trace_id,
                    "ticker": ticker,
                    "market": market_type,
                    "rows": len(df)
                }, ensure_ascii=False))
            
            # 3. 데이터 검증 (기존 서비스 사용)
            if not self.validation_service.validate_ohlcv_data(df, ticker, min_rows=20):
                return self._compose_error_result(ticker, market_type, "데이터 검증 실패", "validation", start_time)
            
            # 4. 일봉 데이터 저장 (주봉, 월봉, 지표 자동 생성됨)
            self.logger.info(json.dumps({
                "event": "save.daily.begin",
                "trace": trace_id,
                "ticker": ticker,
                "market": market_type
            }, ensure_ascii=False))
            daily_path = self._save_daily_data(ticker, df, market_type)
            if not daily_path:
                return self._compose_error_result(ticker, market_type, "일봉 데이터 저장 실패", "daily_save", start_time)
            else:
                self.logger.info(json.dumps({
                    "event": "save.daily.end",
                    "trace": trace_id,
                    "ticker": ticker,
                    "market": market_type,
                    "daily_path": daily_path
                }, ensure_ascii=False))
            
            # 5-7. 주봉/월봉은 DataStorageService가 일봉 저장 시 자동 생성함
            #    수동 생성 호출 시 일봉 파일이 중복 생성되는 부작용이 있어 호출하지 않음
            weekly_path = daily_path.replace('_ohlcv_d_', '_ohlcv_w_')
            monthly_path = daily_path.replace('_ohlcv_d_', '_ohlcv_m_')

            self.logger.info(json.dumps({
                "event": "indicators.calculate.begin",
                "trace": trace_id,
                "ticker": ticker,
                "market": market_type,
                "timeframes": ["d","w","m"]
            }, ensure_ascii=False))
            indicators_result = self._calculate_technical_indicators(ticker, market_type)
            self.logger.info(json.dumps({
                "event": "indicators.calculate.end",
                "trace": trace_id,
                "ticker": ticker,
                "market": market_type,
                "success": indicators_result.get("success"),
                "success_count": indicators_result.get("success_count"),
                "total_count": indicators_result.get("total_count")
            }, ensure_ascii=False))
            
            # 8. 결과 구성 및 반환
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(json.dumps({
                "event": "orchestrator.done",
                "trace": trace_id,
                "ticker": ticker,
                "market": market_type,
                "processing_time_s": processing_time,
                "weekly_path": weekly_path,
                "monthly_path": monthly_path
            }, ensure_ascii=False))
            return ProcessingResult(
                success=True,
                ticker=ticker,
                market_type=market_type,
                daily_path=daily_path,
                weekly_path=weekly_path,
                monthly_path=monthly_path,
                indicators_path=indicators_result.get('path'),
                processing_time=processing_time,
                data_rows=len(df),
                indicators_rows=indicators_result.get('rows', 0)
            )
            
        except Exception as e:
            self.logger.error(f"[{ticker}] 처리 중 예외 발생: {e}")
            return self._compose_error_result(ticker, market_type, str(e), "exception", start_time)
    
    def _check_existing_data(self, ticker: str, market_type: str) -> Dict:
        """기존 데이터 확인"""
        try:
            # 파일 존재 여부 먼저 확인
            from .file_management_service import FileManagementService
            file_service = FileManagementService()
            
            # 일봉 파일 존재 여부 확인
            daily_files = file_service.find_csv_files(ticker, market_type, 'ohlcv', 'd')
            if not daily_files:
                return {
                    'use_existing': False,
                    'reason': '일봉 데이터 파일 없음'
                }
            
            # 일봉 파일 읽기
            daily_df = self.reading_service.read_ohlcv_csv(ticker, market_type, 'd')
            
            if daily_df.empty:
                return {
                    'use_existing': False,
                    'reason': '일봉 데이터 읽기 실패'
                }
            
            # 데이터 검증
            if not self._validate_data(ticker, market_type):
                return {
                    'use_existing': False,
                    'reason': '기존 데이터 검증 실패'
                }
            
            # 주봉/월봉 파일 확인
            weekly_df = self.reading_service.read_ohlcv_csv(ticker, market_type, 'w')
            monthly_df = self.reading_service.read_ohlcv_csv(ticker, market_type, 'm')
            
            has_weekly = not weekly_df.empty
            has_monthly = not monthly_df.empty
            
            return {
                'use_existing': True,
                'reason': f'기존 데이터 사용 (일봉: 있음, 주봉: {has_weekly}, 월봉: {has_monthly})',
                'daily_df': daily_df,
                'weekly_df': weekly_df,
                'monthly_df': monthly_df,
                'has_weekly': has_weekly,
                'has_monthly': has_monthly
            }
            
        except Exception as e:
            self.logger.error(f"[{ticker}] 기존 데이터 확인 실패: {e}")
            return {
                'use_existing': False,
                'reason': f'기존 데이터 확인 실패: {e}'
            }
    
    def _process_with_existing_data(self, ticker: str, market_type: str, existing_check: Dict) -> ProcessingResult:
        """기존 데이터로 처리"""
        try:
            daily_df = existing_check['daily_df']
            
            # 주봉/월봉이 없으면 생성
            weekly_path = None
            monthly_path = None
            
            if not existing_check['has_weekly']:
                weekly_path = self._generate_weekly_data(ticker, daily_df, market_type)
            
            if not existing_check['has_monthly']:
                monthly_path = self._generate_monthly_data(ticker, daily_df, market_type)
            
            # 기술적 지표 확인 및 계산
            indicators_result = self._calculate_technical_indicators(ticker, market_type)
            
            return ProcessingResult(
                success=True,
                ticker=ticker,
                market_type=market_type,
                daily_path=self.file_management_service.get_latest_file(ticker, 'ohlcv', market_type, 'd'),
                weekly_path=weekly_path,
                monthly_path=monthly_path,
                indicators_path=indicators_result.get('path'),
                processing_time=0.0,
                data_rows=len(daily_df),
                indicators_rows=indicators_result.get('rows', 0)
            )
            
        except Exception as e:
            self.logger.error(f"[{ticker}] 기존 데이터 처리 실패: {e}")
            return self._compose_error_result(ticker, market_type, str(e), "existing_process", datetime.now())
    
    def _download_fresh_data(self, ticker: str, market_type: str) -> pd.DataFrame:
        """새 데이터 다운로드"""
        try:
            self.logger.debug(f"[{ticker}] 새 데이터 다운로드 시작")
            
            # 다운로드 기간 설정 (최근 5년)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=5*365)
            
            # 데이터 다운로드
            # MEMO(2025-08-20): 시장 컨텍스트를 다운로드 서비스에 전달하여 한국 접미사 우선순위가 정확히 적용되도록 함
            df = self.download_service.download_stock_data_with_fallback(ticker, start_date, end_date, market_type)
            
            if df.empty:
                self.logger.error(f"[{ticker}] 다운로드된 데이터가 비어있음")
                return pd.DataFrame()
            
            self.logger.debug(f"[{ticker}] 다운로드 완료: {len(df)}개 행")
            return df
            
        except Exception as e:
            self.logger.error(f"[{ticker}] 데이터 다운로드 실패: {e}")
            return pd.DataFrame()
    

    def _validate_data(self, ticker, market_type):
        """데이터 유효성 검증 (파일에서)
        - 최소 행수 확인
        - 시장 상태에 따른 최신 거래일 포함 여부 확인
        """
        daily_df = self.reading_service.read_ohlcv_csv(ticker, market_type, 'd')
        if daily_df.empty or len(daily_df) < 20:
            logging.warning(f"[{ticker}] 데이터가 너무 적어 처리를 건너뜁니다.")
            return False

        try:
            market_status = self.market_status_service.get_market_status_info_improved(market_type)
            last_date = daily_df.index.max().date()

            # 현재 날짜 문자열(시장 시간대 기준)을 date로 변환
            current_date_str = market_status.get('current_date')
            if current_date_str:
                current_date = datetime.strptime(current_date_str, '%Y-%m-%d').date()
            else:
                current_date = datetime.now().date()

            if market_status.get('is_open'):
                # 장중: 오늘자 데이터가 아직 반영되지 않았으면 신선하지 않음
                if last_date < current_date:
                    logging.info(f"[{ticker}] 장중 신선도 미충족: last_date={last_date}, current_date={current_date}")
                    return False
            else:
                # 장마감: 최소한 현재 날짜(시장기준)까지 반영되어 있어야 함
                if last_date < current_date:
                    logging.info(f"[{ticker}] 장마감 신선도 미충족: last_date={last_date}, current_date={current_date}")
                    return False
        except Exception as e:
            # 신선도 검사 실패 시에는 최소 행수 기준만 통과시키고 계속 진행
            logging.debug(f"[{ticker}] 신선도 검사 중 예외: {e}")

        return True

    def _save_daily_data(self, ticker: str, df: pd.DataFrame, market_type: str) -> Optional[str]:
        """일봉 데이터 저장"""
        try:
            self.logger.info(f"[{ticker}] 일봉 데이터 저장 시작")

            # 데이터 정리 (필수 컬럼만 선택)
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            if 'Adj Close' in df.columns:
                required_columns.append('Adj Close')

            clean_df = df[required_columns].copy()

            # CSV 저장
            csv_path = self.storage_service.save_ohlcv_to_csv(ticker, clean_df, market_type)

            if csv_path and os.path.exists(csv_path):
                self.logger.info(f"[{ticker}] 일봉 데이터 저장 완료: {csv_path}")
                return csv_path
            else:
                self.logger.error(f"[{ticker}] 일봉 데이터 저장 실패")
                return None

        except Exception as e:
            self.logger.error(f"[{ticker}] 일봉 데이터 저장 실패: {e}")
            return None

    def _get_existing_data_status(self, ticker, market_type):
        """기존 데이터 파일 존재 여부 확인"""
        daily_exists = not self.reading_service.read_ohlcv_csv(ticker, market_type, 'd').empty
        weekly_exists = not self.reading_service.read_ohlcv_csv(ticker, market_type, 'w').empty
        monthly_exists = not self.reading_service.read_ohlcv_csv(ticker, market_type, 'm').empty
        return {'d': daily_exists, 'w': weekly_exists, 'm': monthly_exists}


    def _process_timeframe(self, ticker, market_type, timeframe, ohlcv_data=None):
        """
        주어진 시간대(일봉, 주봉, 월봉)의 데이터를 처리하는 내부 메서드.
        데이터가 제공되지 않으면 파일에서 읽어온다.
        """
        # 데이터가 제공되지 않은 경우 파일에서 읽기
        if ohlcv_data is None:
            timeframe_str = {'d': '일봉', 'w': '주봉', 'm': '월봉'}.get(timeframe)
            logging.info(f"[{ticker}] 제공된 {timeframe_str} 데이터가 없어 파일에서 직접 읽습니다.")
            ohlcv_data = self.reading_service.read_ohlcv_csv(ticker, market_type, timeframe)

        if ohlcv_data is None or ohlcv_data.empty:
            logging.warning(f"[{ticker}] {timeframe} 데이터가 없어 처리를 건너뜁니다.")
            return

    def _generate_weekly_data(self, ticker: str, df: pd.DataFrame, market_type: str) -> Optional[str]:
        """주봉 데이터 생성"""
        try:
            if df.empty or len(df) < 7:
                self.logger.warning(f"[{ticker}] 주봉 생성 불가: 데이터 부족 ({len(df)}개)")
                return None
            
            self.logger.info(f"[{ticker}] 주봉 데이터 생성 시작")
            
            # 주봉 변환
            weekly_df = self.conversion_service.convert_dataframe_timeframe(df, 'w')
            
            if weekly_df.empty:
                self.logger.warning(f"[{ticker}] 주봉 변환 결과가 비어있음")
                return None
            
            # 주봉 저장 (save_ohlcv_to_csv_with_timestamp 함수는 제거되었으므로 save_ohlcv_to_csv 사용)
            # 주봉은 명시적으로 timeframe='w'로 저장 (일봉용 자동 로직 방지)
            csv_path = self.storage_service.save_ohlcv_to_csv(ticker, weekly_df, market_type, timeframe='w')
            
            if csv_path and os.path.exists(csv_path):
                self.logger.info(f"[{ticker}] 주봉 데이터 생성 완료: {csv_path}")
                return csv_path
            else:
                self.logger.error(f"[{ticker}] 주봉 데이터 저장 실패")
                return None
                
        except Exception as e:
            self.logger.error(f"[{ticker}] 주봉 데이터 생성 실패: {e}")
            return None
    
    def _generate_monthly_data(self, ticker: str, df: pd.DataFrame, market_type: str) -> Optional[str]:
        """월봉 데이터 생성"""
        try:
            if df.empty or len(df) < 30:
                self.logger.warning(f"[{ticker}] 월봉 생성 불가: 데이터 부족 ({len(df)}개)")
                return None
            
            self.logger.info(f"[{ticker}] 월봉 데이터 생성 시작")
            
            # 월봉 변환
            monthly_df = self.conversion_service.convert_dataframe_timeframe(df, 'm')
            
            if monthly_df.empty:
                self.logger.warning(f"[{ticker}] 월봉 변환 결과가 비어있음")
                return None
            
            # 월봉 저장 (save_ohlcv_to_csv_with_timestamp 함수는 제거되었으므로 save_ohlcv_to_csv 사용)
            # 월봉은 명시적으로 timeframe='m'로 저장 (일봉용 자동 로직 방지)
            csv_path = self.storage_service.save_ohlcv_to_csv(ticker, monthly_df, market_type, timeframe='m')
            
            if csv_path and os.path.exists(csv_path):
                self.logger.info(f"[{ticker}] 월봉 데이터 생성 완료: {csv_path}")
                return csv_path
            else:
                self.logger.error(f"[{ticker}] 월봉 데이터 저장 실패")
                return None
                
        except Exception as e:
            self.logger.error(f"[{ticker}] 월봉 데이터 생성 실패: {e}")
            return None
    
    def _calculate_technical_indicators(self, ticker: str, market_type: str) -> Dict:
        """기술적 지표 계산"""
        try:
            self.logger.info(f"[{ticker}] 기술적 지표 계산 시작")
            
            # 기술적 지표 계산 (일봉, 주봉, 월봉)
            indicators_result = self.indicators_service.calculate_all_indicators(
                ticker, market_type, timeframes=['d', 'w', 'm']
            )
            
            success_count = sum(1 for tf_result in indicators_result.values() 
                              if tf_result and tf_result.get('success'))
            total_count = len(indicators_result)
            
            self.logger.info(f"[{ticker}] 기술적 지표 계산 완료: {success_count}/{total_count}")
            
            return {
                'success': success_count > 0,
                'success_count': success_count,
                'total_count': total_count,
                'results': indicators_result
            }
            
        except Exception as e:
            self.logger.error(f"[{ticker}] 기술적 지표 계산 실패: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _compose_error_result(self, ticker: str, market_type: str, error_message: str, error_stage: str, start_time: datetime) -> ProcessingResult:
        """오류 결과 구성"""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        self.logger.error(f"[{ticker}] {error_stage} 단계에서 실패: {error_message}")
        
        return ProcessingResult(
            success=False,
            ticker=ticker,
            market_type=market_type,
            error_message=error_message,
            error_stage=error_stage,
            processing_time=processing_time
        )
    
    def process_multiple_stocks(self, tickers: List[str], market_type: str) -> Dict[str, ProcessingResult]:
        """여러 종목 처리"""
        results = {}
        
        for ticker in tickers:
            try:
                result = self.process_stock_data_complete(ticker, market_type)
                results[ticker] = result
                
                if result.success:
                    self.logger.info(f"[{ticker}] 처리 완료: 성공")
                else:
                    self.logger.warning(f"[{ticker}] 처리 완료: 실패 ({result.error_stage})")
                    
            except Exception as e:
                self.logger.error(f"[{ticker}] 처리 중 예외: {e}")
                results[ticker] = self._compose_error_result(ticker, market_type, str(e), "exception", datetime.now())
        
        return results 