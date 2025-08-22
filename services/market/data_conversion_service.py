"""
데이터 변환 서비스
데이터 변환 및 시간프레임 변환 기능을 담당
"""

import os
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List

class DataConversionService:
    """데이터 변환 전담 서비스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def convert_daily_to_weekly_monthly(self, ticker: str, market_type: str = 'KOSPI') -> Dict:
        """일봉을 주봉/월봉으로 변환"""
        try:
            # 일봉 데이터 읽기
            from .data_reading_service import DataReadingService
            reading_service = DataReadingService()
            
            # 인자 순서 교정: (ticker, market_type, timeframe)
            daily_df = reading_service.read_ohlcv_csv(ticker, market_type, 'd')
            if daily_df.empty:
                self.logger.warning(f"[{ticker}] 일봉 데이터 없음")
                return {}
            
            results = {}
            
            # 주봉 변환
            weekly_df = self.convert_dataframe_timeframe(daily_df, 'w')
            if not weekly_df.empty:
                results['weekly'] = weekly_df
                self.logger.info(f"[{ticker}] 주봉 변환 완료: {len(weekly_df)}개")
            
            # 월봉 변환
            monthly_df = self.convert_dataframe_timeframe(daily_df, 'm')
            if not monthly_df.empty:
                results['monthly'] = monthly_df
                self.logger.info(f"[{ticker}] 월봉 변환 완료: {len(monthly_df)}개")
            
            return results
            
        except Exception as e:
            self.logger.error(f"[{ticker}] 시간프레임 변환 실패: {e}")
            return {}
    
    def convert_all_timeframes(self, tickers: List[str], market_type: str = 'KOSPI') -> Dict:
        """모든 종목의 시간프레임 변환"""
        results = {}
        
        for ticker in tickers:
            try:
                ticker_results = self.convert_daily_to_weekly_monthly(ticker, market_type)
                if ticker_results:
                    results[ticker] = ticker_results
            except Exception as e:
                self.logger.error(f"[{ticker}] 시간프레임 변환 실패: {e}")
        
        return results
    
    def convert_dataframe_timeframe(self, df: pd.DataFrame, target_timeframe: str) -> pd.DataFrame:
        """DataFrame의 시간프레임 변환"""
        try:
            if df.empty:
                return pd.DataFrame()
            
            # 리샘플링 규칙 설정
            if target_timeframe == 'w':
                rule = 'W'
            elif target_timeframe == 'm':
                rule = 'M'
            else:
                self.logger.warning(f"지원하지 않는 시간프레임: {target_timeframe}")
                return pd.DataFrame()
            
            # OHLCV 리샘플링
            resampled_df = self.resample_ohlcv_data(df, rule)
            
            return resampled_df
            
        except Exception as e:
            self.logger.error(f"DataFrame 시간프레임 변환 실패: {e}")
            return pd.DataFrame()
    
    def resample_ohlcv_data(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """OHLCV 데이터 리샘플링"""
        try:
            if df.empty:
                return pd.DataFrame()
            
            # OHLCV 컬럼 확인
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in df.columns for col in required_columns):
                self.logger.error("필수 OHLCV 컬럼이 없습니다")
                return pd.DataFrame()
            
            # 리샘플링 규칙 설정
            agg_rules = {
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }
            
            # Adj Close가 있으면 추가
            if 'Adj Close' in df.columns:
                agg_rules['Adj Close'] = 'last'
            
            # 리샘플링 수행
            resampled = df.resample(timeframe).agg(agg_rules)
            
            # NaN 값 제거
            resampled = resampled.dropna()
            
            return resampled
            
        except Exception as e:
            self.logger.error(f"OHLCV 리샘플링 실패: {e}")
            return pd.DataFrame() 