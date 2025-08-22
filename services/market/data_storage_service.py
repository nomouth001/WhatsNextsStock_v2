"""
데이터 저장 서비스
OHLCV 데이터를 CSV 파일로 저장하는 기능을 담당
"""

import os
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

class DataStorageService:
    """데이터 저장 전담 서비스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def _add_date_time_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Date_Index와 Time_Index 컬럼 추가"""
        # DEBUG_STEP_1: _add_date_time_columns 시작 - 나중에 제거 가능
        # self.logger.debug(f"[DEBUG_STEP_1] _add_date_time_columns 시작: df.shape={df.shape}, index_type={type(df.index)}")
        
        df_with_datetime = df.copy()
        
        # DEBUG_STEP_2: strftime 호출 전 인덱스 상태 확인 - 나중에 제거 가능  
        # if len(df_with_datetime) > 0:
        #     first_idx = df_with_datetime.index[0]
        #     self.logger.debug(f"[DEBUG_STEP_2] 첫 번째 인덱스 값: {first_idx} (type: {type(first_idx)}, has_strftime: {hasattr(first_idx, 'strftime')})")
        
        try:
            # DEBUG_STEP_3: strftime 호출 직전 - 나중에 제거 가능
            # self.logger.debug(f"[DEBUG_STEP_3] strftime 호출 시작")
            df_with_datetime['Date_Index'] = df_with_datetime.index.strftime('%Y-%m-%d')
            df_with_datetime['Time_Index'] = df_with_datetime.index.strftime('%H:%M:%S')
            # DEBUG_STEP_4: strftime 호출 성공 - 나중에 제거 가능
            # self.logger.debug(f"[DEBUG_STEP_4] strftime 호출 성공")
        except Exception as e:
            # DEBUG_ERROR_1: strftime 에러 상세 정보 - 나중에 제거 가능
            # self.logger.error(f"[DEBUG_ERROR_1] strftime 에러 상세: {e}, index_type={type(df_with_datetime.index)}")
            raise
        
        return df_with_datetime
    
    def save_ohlcv_to_csv(self, ticker: str, df: pd.DataFrame, market_type: str = 'US', timeframe: str = 'd') -> str:
        """
        OHLCV 데이터를 CSV 파일로 저장 (새로운 파일명 형식)
        timeframe='d'인 경우에만 주봉/월봉을 자동 생성
        
        Args:
            ticker (str): 주식 티커
            df (pd.DataFrame): OHLCV 데이터
            market_type (str): 시장 타입 ('KOSPI', 'KOSDAQ', 'US')
        
        Returns:
            str: 저장된 CSV 파일 경로
        """
        try:
            # DEBUG_STEP_5: save_ohlcv_to_csv 시작 - 나중에 제거 가능
            # self.logger.debug(f"[DEBUG_STEP_5] save_ohlcv_to_csv 시작: ticker={ticker}, df.shape={df.shape}, market_type={market_type}")
            
            # market_type을 실제 폴더명으로 변환
            if market_type.upper() in ['KOSPI', 'KOSDAQ', 'US']:
                actual_market_type = market_type.upper()
            else:
                actual_market_type = market_type.upper()
            
            # CSV 저장 디렉토리 생성
            csv_dir = os.path.join('static/data', actual_market_type)
            os.makedirs(csv_dir, exist_ok=True)
            
            # DEBUG_STEP_6: latest_datetime 추출 전 - 나중에 제거 가능
            # self.logger.debug(f"[DEBUG_STEP_6] latest_datetime 추출 전: df.index.dtype={df.index.dtype}, df.index[-1] 타입 확인 중...")
            
            # 데이터의 최신 날짜와 시간 정보를 파일명에 포함
            latest_datetime = df.index[-1]
            
            # DEBUG_STEP_7: latest_datetime 추출 후 - 나중에 제거 가능
            # self.logger.debug(f"[DEBUG_STEP_7] latest_datetime: {latest_datetime} (type: {type(latest_datetime)}, has_strftime: {hasattr(latest_datetime, 'strftime')})")
            
            try:
                # DEBUG_STEP_8: strftime 호출 직전 - 나중에 제거 가능
                # self.logger.debug(f"[DEBUG_STEP_8] latest_datetime.strftime 호출 시작")
                latest_datetime_str = latest_datetime.strftime('%Y%m%d_%H%M%S')
                # DEBUG_STEP_9: strftime 호출 성공 - 나중에 제거 가능
                # self.logger.debug(f"[DEBUG_STEP_9] latest_datetime.strftime 성공: {latest_datetime_str}")
            except Exception as e:
                # DEBUG_ERROR_2: latest_datetime strftime 에러 - 나중에 제거 가능
                # self.logger.error(f"[DEBUG_ERROR_2] latest_datetime strftime 에러: {e}, latest_datetime={latest_datetime}, type={type(latest_datetime)}")
                raise
            
            # 시장별 시간대 정보
            if market_type in ['KOSPI', 'KOSDAQ']:
                timezone_suffix = 'KST'
            else:
                timezone_suffix = 'EST'
            
            # 파일명 형식: {ticker}_ohlcv_{timeframe}_YYYYMMDD_HHMMSS_{timezone}.csv
            tf = timeframe.lower()
            if tf not in ('d', 'w', 'm'):
                tf = 'd'
            csv_filename = f"{ticker}_ohlcv_{tf}_{latest_datetime_str}_{timezone_suffix}.csv"
            csv_path = os.path.join(csv_dir, csv_filename)
            
            # Date_Index와 Time_Index 컬럼 추가
            df_with_datetime = self._add_date_time_columns(df)
            
            # 메타데이터 정보 추가
            # 메타데이터 타임프레임 라벨 매핑
            tf_label = 'daily' if tf == 'd' else ('weekly' if tf == 'w' else 'monthly')
            metadata_info = self._create_metadata_info(ticker, df_with_datetime, market_type, latest_datetime, tf_label)
            
            # CSV 저장 (메타데이터 포함)
            self._save_csv_with_metadata(df_with_datetime, csv_path, metadata_info)
            
            self.logger.info(f"[{ticker}] {tf_label} OHLCV 데이터 저장 완료: {csv_path} (최신 데이터: {latest_datetime})")
            
            # 자동으로 주봉, 월봉 데이터 생성 및 저장
            try:
                if tf == 'd' and (not df.empty and len(df) >= 7):  # 일봉 저장 시에만 주봉 자동 생성
                    # 주봉 데이터 생성 (일요일 마감 기준)
                    weekly_df = df.resample('W').agg({
                        "Open": "first", 
                        "High": "max", 
                        "Low": "min", 
                        "Close": "last", 
                        "Volume": "sum"
                    }).dropna()
                    
                    if not weekly_df.empty:
                        weekly_csv_filename = f"{ticker}_ohlcv_w_{latest_datetime_str}_{timezone_suffix}.csv"
                        weekly_csv_path = os.path.join(csv_dir, weekly_csv_filename)
                        weekly_df_with_datetime = self._add_date_time_columns(weekly_df)
                        weekly_metadata = self._create_metadata_info(ticker, weekly_df_with_datetime, market_type, latest_datetime, 'weekly')
                        self._save_csv_with_metadata(weekly_df_with_datetime, weekly_csv_path, weekly_metadata)
                        self.logger.info(f"[{ticker}] 주봉 OHLCV 자동 생성: {weekly_csv_path} ({len(weekly_df)}개 행)")
                    else:
                        self.logger.warning(f"[{ticker}] 주봉 데이터 생성 실패 - 빈 결과")
                
                if tf == 'd' and (not df.empty and len(df) >= 30):  # 일봉 저장 시에만 월봉 자동 생성
                    # 월봉 데이터 생성 (월말 기준)
                    # NOTE: 'ME'는 잘못된 오프셋이므로 'M'을 사용
                    monthly_df = df.resample('M').agg({
                        "Open": "first", 
                        "High": "max", 
                        "Low": "min", 
                        "Close": "last", 
                        "Volume": "sum"
                    }).dropna()
                    
                    if not monthly_df.empty:
                        monthly_csv_filename = f"{ticker}_ohlcv_m_{latest_datetime_str}_{timezone_suffix}.csv"
                        monthly_csv_path = os.path.join(csv_dir, monthly_csv_filename)
                        monthly_df_with_datetime = self._add_date_time_columns(monthly_df)
                        monthly_metadata = self._create_metadata_info(ticker, monthly_df_with_datetime, market_type, latest_datetime, 'monthly')
                        self._save_csv_with_metadata(monthly_df_with_datetime, monthly_csv_path, monthly_metadata)
                        self.logger.info(f"[{ticker}] 월봉 OHLCV 자동 생성: {monthly_csv_path} ({len(monthly_df)}개 행)")
                    else:
                        self.logger.warning(f"[{ticker}] 월봉 데이터 생성 실패 - 빈 결과")
                
                # 기술적 지표 자동 계산 비활성화: 오케스트레이터에서 일원화하여 수행
                # self.logger.info(f"[{ticker}] 기술적 지표 자동 계산 시작...")
                # try:
                #     from services.technical_indicators_service import TechnicalIndicatorsService
                #     indicators_service = TechnicalIndicatorsService()
                #     indicators_result = indicators_service.calculate_all_indicators(ticker, market_type, ['d', 'w', 'm'])
                #     success_count = sum(1 for tf_result in indicators_result.values() if tf_result and tf_result.get('success'))
                #     total_count = len(indicators_result)
                #     self.logger.info(f"[{ticker}] 기술적 지표 자동 계산 완료: {success_count}/{total_count} 성공")
                # except Exception as e:
                #     self.logger.error(f"[{ticker}] 기술적 지표 계산 실패: {e}")
                
            except Exception as e:
                self.logger.error(f"[{ticker}] 주봉/월봉 데이터 생성 중 오류: {e}")
            
            return csv_path
            
        except Exception as e:
            self.logger.error(f"[{ticker}] CSV 저장 실패: {e}")
            raise
    
    def _create_metadata_info(self, ticker: str, df: pd.DataFrame, market_type: str, latest_datetime, timeframe: str = 'daily') -> dict:
        """메타데이터 정보 생성"""
        from datetime import datetime
        
        # 현재 시간 정보 가져오기
        time_info = self._get_current_time_info()
        
        # DEBUG_STEP_13: 메타데이터 생성 시작 - 나중에 제거 가능
        # self.logger.debug(f"[DEBUG_STEP_13] 메타데이터 생성 시작")
        # self.logger.debug(f"[DEBUG_STEP_13] df.index[0]: {df.index[0]} (type: {type(df.index[0])})")
        # self.logger.debug(f"[DEBUG_STEP_13] df.index[-1]: {df.index[-1]} (type: {type(df.index[-1])})")
        # self.logger.debug(f"[DEBUG_STEP_13] latest_datetime: {latest_datetime} (type: {type(latest_datetime)})")
        
        try:
            # DEBUG_STEP_14: 각 strftime 호출별 확인 - 나중에 제거 가능
            # self.logger.debug(f"[DEBUG_STEP_14] df.index[0].strftime 호출 시작")
            data_start_date = df.index[0].strftime('%Y-%m-%d %H:%M:%S')
            
            # self.logger.debug(f"[DEBUG_STEP_14] df.index[-1].strftime 호출 시작")
            data_end_date = df.index[-1].strftime('%Y-%m-%d %H:%M:%S')
            
            # self.logger.debug(f"[DEBUG_STEP_14] latest_datetime.strftime 호출 시작")
            latest_data_datetime = latest_datetime.strftime('%Y-%m-%d %H:%M:%S')
            
            # self.logger.debug(f"[DEBUG_STEP_14] 모든 strftime 호출 성공")
            
            metadata = {
                'ticker': ticker,
                'market_type': market_type,
                'timeframe': timeframe,
                'data_start_date': data_start_date,
                'data_end_date': data_end_date,
                'latest_data_datetime': latest_data_datetime,
                'total_rows': len(df),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'timezone': 'KST' if market_type in ['KOSPI', 'KOSDAQ'] else 'EST'
            }
        except Exception as e:
            # DEBUG_ERROR_3: 메타데이터 strftime 에러 - 나중에 제거 가능
            # self.logger.error(f"[DEBUG_ERROR_3] 메타데이터 strftime 에러: {e}")
            raise
        
        # 현재 시간 정보 추가
        try:
            # DEBUG_STEP_15: current_time 생성 - 나중에 제거 가능
            # self.logger.debug(f"[DEBUG_STEP_15] current_time 생성 시작, market_type: {market_type}")
            # self.logger.debug(f"[DEBUG_STEP_15] time_info: {time_info}")
            
            if market_type in ['KOSPI', 'KOSDAQ']:
                kst_time = time_info.get('kst_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                # self.logger.debug(f"[DEBUG_STEP_15] kst_time: {kst_time} (type: {type(kst_time)})")
                # time_info가 이미 문자열을 반환하므로 strftime() 불필요
                metadata['current_time'] = kst_time if isinstance(kst_time, str) else kst_time.strftime('%Y-%m-%d %H:%M:%S')
            else:
                est_time = time_info.get('est_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                # self.logger.debug(f"[DEBUG_STEP_15] est_time: {est_time} (type: {type(est_time)})")
                # time_info가 이미 문자열을 반환하므로 strftime() 불필요
                metadata['current_time'] = est_time if isinstance(est_time, str) else est_time.strftime('%Y-%m-%d %H:%M:%S')
                
            # self.logger.debug(f"[DEBUG_STEP_15] current_time 생성 성공")
        except Exception as e:
            # DEBUG_ERROR_4: current_time strftime 에러 - 나중에 제거 가능
            # self.logger.error(f"[DEBUG_ERROR_4] current_time strftime 에러: {e}")
            raise
        
        return metadata
    
    def _save_csv_with_metadata(self, df: pd.DataFrame, csv_path: str, metadata: dict):
        """메타데이터와 함께 CSV 파일 저장"""
        try:
            with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
                # 메타데이터 헤더 작성
                f.write("# OHLCV Data Metadata\n")
                for key, value in metadata.items():
                    f.write(f"# {key}: {value}\n")
                f.write("# End Metadata\n")
                f.write("\n")
                
                # 데이터 저장
                df.to_csv(f, encoding='utf-8-sig')
                
        except Exception as e:
            self.logger.error(f"Error saving CSV with metadata: {e}")
            # 메타데이터 없이 기본 저장
            df.to_csv(csv_path, encoding='utf-8-sig')
    
    def _get_current_time_info(self):
        """현재 시간 정보 가져오기"""
        from .market_status_service import MarketStatusService
        status_service = MarketStatusService()
        return status_service.get_current_time_info()
    
    def ensure_market_directory(self, market_type: str) -> str:
        """시장별 디렉토리 생성 및 확인"""
        if market_type.upper() in ['KOSPI', 'KOSDAQ']:
            actual_market_type = market_type.upper()
        else:
            actual_market_type = 'US'
        
        csv_dir = os.path.join('static/data', actual_market_type)
        os.makedirs(csv_dir, exist_ok=True)
        
        return csv_dir
    
    def generate_filename(self, ticker: str, data_type: str, timestamp: datetime) -> str:
        """파일명 생성 (새로운 형식)"""
        timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
        return f"{ticker}_{data_type}_{timestamp_str}.csv"
    
    def save_indicators_to_csv(self, ticker: str, indicators_df: pd.DataFrame, 
                              timeframe: str, market_type: str) -> str:
        """지표 데이터 CSV 파일 저장"""
        try:
            # market_type을 실제 폴더명으로 변환
            if market_type.upper() in ['KOSPI', 'KOSDAQ', 'US']:
                actual_market_type = market_type.upper()
            else:
                actual_market_type = market_type.upper()
            
            # CSV 저장 디렉토리 생성
            csv_dir = os.path.join('static/data', actual_market_type)
            os.makedirs(csv_dir, exist_ok=True)
            
            # 데이터의 최신 날짜와 시간 정보를 파일명에 포함
            latest_datetime = indicators_df.index[-1]
            latest_datetime_str = latest_datetime.strftime('%Y%m%d_%H%M%S')
            
            # 시장별 시간대 정보
            if market_type in ['KOSPI', 'KOSDAQ']:
                timezone_suffix = 'KST'
            else:
                timezone_suffix = 'EST'
            
            # 지표 파일명 생성
            indicators_csv_filename = f"{ticker}_indicators_{timeframe}_{latest_datetime_str}_{timezone_suffix}.csv"
            indicators_csv_path = os.path.join(csv_dir, indicators_csv_filename)
            
            # Date_Index와 Time_Index 컬럼 추가
            indicators_df_with_datetime = self._add_date_time_columns(indicators_df)
            
            # 메타데이터 정보 추가
            metadata_info = self._create_metadata_info(ticker, indicators_df_with_datetime, market_type, latest_datetime, f'indicators_{timeframe}')
            
            # CSV 저장 (메타데이터 포함)
            self._save_csv_with_metadata(indicators_df_with_datetime, indicators_csv_path, metadata_info)
            
            self.logger.info(f"[{ticker}] 지표 데이터 저장 완료: {indicators_csv_path} (최신 데이터: {latest_datetime})")
            
            return indicators_csv_path
            
        except Exception as e:
            self.logger.error(f"[{ticker}] 지표 데이터 저장 실패: {e}")
            return None 