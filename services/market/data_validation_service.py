"""
데이터 검증 서비스
데이터 품질 검증 및 정리 기능을 담당
"""

import os
import logging
import pandas as pd
import numpy as np
from typing import Dict, List

class DataValidationError(Exception):
    """데이터 검증 오류"""
    pass

class DataValidationService:
    """데이터 검증 전담 서비스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_ohlcv_data(self, df: pd.DataFrame, ticker: str, min_rows: int = 10) -> bool:
        """OHLCV 데이터 품질 검증"""
        try:
            if df.empty:
                self.logger.warning(f"[{ticker}] 데이터가 비어있음")
                return False
            
            # 최소 행 수 확인
            if len(df) < min_rows:
                self.logger.warning(f"[{ticker}] 데이터가 너무 적음: {len(df)}개 (최소 {min_rows}개 필요)")
                return False
            
            # 필수 컬럼 확인
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.error(f"[{ticker}] 필수 컬럼 누락: {missing_columns}")
                return False
            
            # 데이터 타입 확인
            for col in required_columns:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    self.logger.error(f"[{ticker}] {col} 컬럼이 숫자형이 아님")
                    return False
            
            # 음수 값 확인
            for col in ['Open', 'High', 'Low', 'Close']:
                if (df[col] < 0).any():
                    self.logger.error(f"[{ticker}] {col} 컬럼에 음수 값 존재")
                    return False
            
            # High >= Low 확인
            if (df['High'] < df['Low']).any():
                self.logger.error(f"[{ticker}] High가 Low보다 작은 값 존재")
                return False
            
            # Volume >= 0 확인
            if (df['Volume'] < 0).any():
                self.logger.error(f"[{ticker}] Volume에 음수 값 존재")
                return False
            
            # 중복 인덱스 확인
            if df.index.duplicated().any():
                self.logger.warning(f"[{ticker}] 중복 인덱스 존재")
                return False
            
            self.logger.info(f"[{ticker}] 데이터 검증 통과")
            return True
            
        except Exception as e:
            self.logger.error(f"[{ticker}] 데이터 검증 중 오류: {e}")
            return False
    
    def clean_ohlcv_data(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """OHLCV 데이터 정리"""
        try:
            if df.empty:
                return df
            
            # 복사본 생성
            cleaned_df = df.copy()
            
            # 중복 인덱스 제거
            if cleaned_df.index.duplicated().any():
                self.logger.info(f"[{ticker}] 중복 인덱스 제거")
                cleaned_df = cleaned_df[~cleaned_df.index.duplicated()]
            
            # 정렬
            cleaned_df = cleaned_df.sort_index()
            
            # 음수 값 처리
            for col in ['Open', 'High', 'Low', 'Close']:
                cleaned_df[col] = cleaned_df[col].abs()
            
            # Volume 음수 값 처리
            cleaned_df['Volume'] = cleaned_df['Volume'].abs()
            
            # High < Low인 경우 수정
            invalid_mask = cleaned_df['High'] < cleaned_df['Low']
            if invalid_mask.any():
                self.logger.warning(f"[{ticker}] High < Low인 {invalid_mask.sum()}개 행 수정")
                # High와 Low를 교환
                temp = cleaned_df.loc[invalid_mask, 'High'].copy()
                cleaned_df.loc[invalid_mask, 'High'] = cleaned_df.loc[invalid_mask, 'Low']
                cleaned_df.loc[invalid_mask, 'Low'] = temp
            
            # NaN 값 처리
            cleaned_df = cleaned_df.dropna()
            
            self.logger.info(f"[{ticker}] 데이터 정리 완료: {len(cleaned_df)}개 행")
            return cleaned_df
            
        except Exception as e:
            self.logger.error(f"[{ticker}] 데이터 정리 중 오류: {e}")
            return df
    
    def log_data_quality_report(self, df: pd.DataFrame, ticker: str, source: str = "Unknown") -> None:
        """데이터 품질 리포트 로깅"""
        try:
            if df.empty:
                self.logger.warning(f"[{ticker}] 데이터 품질 리포트: 빈 데이터")
                return
            
            report = {
                'ticker': ticker,
                'source': source,
                'total_rows': len(df),
                'date_range': f"{df.index.min()} ~ {df.index.max()}",
                'columns': list(df.columns),
                'missing_values': df.isnull().sum().to_dict(),
                'data_types': df.dtypes.to_dict()
            }
            
            # 수치형 컬럼 통계
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            if len(numeric_columns) > 0:
                report['numeric_stats'] = df[numeric_columns].describe().to_dict()
            
            self.logger.info(f"[{ticker}] 데이터 품질 리포트: {report}")
            
        except Exception as e:
            self.logger.error(f"[{ticker}] 데이터 품질 리포트 생성 중 오류: {e}")
    
    def check_data_completeness(self, df: pd.DataFrame, ticker: str) -> Dict:
        """데이터 완성도 검사"""
        try:
            if df.empty:
                return {'completeness': 0.0, 'issues': ['빈 데이터']}
            
            issues = []
            completeness_score = 100.0
            
            # 필수 컬럼 확인
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                issues.append(f"필수 컬럼 누락: {missing_columns}")
                completeness_score -= 20.0
            
            # NaN 값 비율 확인
            nan_ratio = df.isnull().sum().sum() / (len(df) * len(df.columns))
            if nan_ratio > 0.1:  # 10% 이상
                issues.append(f"NaN 값 비율 높음: {nan_ratio:.2%}")
                completeness_score -= 15.0
            
            # 중복 인덱스 확인
            if df.index.duplicated().any():
                issues.append("중복 인덱스 존재")
                completeness_score -= 10.0
            
            # 데이터 범위 확인
            if len(df) < 10:
                issues.append("데이터가 너무 적음")
                completeness_score -= 20.0
            
            return {
                'completeness': max(0.0, completeness_score),
                'issues': issues,
                'total_rows': len(df),
                'nan_ratio': nan_ratio
            }
            
        except Exception as e:
            self.logger.error(f"[{ticker}] 데이터 완성도 검사 중 오류: {e}")
            return {'completeness': 0.0, 'issues': [f'검사 오류: {str(e)}']}
    
    def detect_anomalies(self, df: pd.DataFrame, ticker: str) -> List[Dict]:
        """이상치 감지"""
        try:
            anomalies = []
            
            if df.empty:
                return anomalies
            
            # 가격 이상치 감지 (이동평균 대비 큰 편차)
            if 'Close' in df.columns:
                ma_20 = df['Close'].rolling(window=20).mean()
                price_deviation = abs(df['Close'] - ma_20) / ma_20
                extreme_prices = price_deviation > 0.3  # 30% 이상 편차
                
                if extreme_prices.any():
                    extreme_dates = df.index[extreme_prices]
                    anomalies.append({
                        'type': 'extreme_price',
                        'dates': extreme_dates.strftime('%Y-%m-%d').tolist(),
                        'description': '이동평균 대비 30% 이상 편차'
                    })
            
            # 거래량 이상치 감지
            if 'Volume' in df.columns:
                volume_ma = df['Volume'].rolling(window=20).mean()
                volume_deviation = df['Volume'] / volume_ma
                extreme_volume = volume_deviation > 5  # 평균 대비 5배 이상
                
                if extreme_volume.any():
                    extreme_dates = df.index[extreme_volume]
                    anomalies.append({
                        'type': 'extreme_volume',
                        'dates': extreme_dates.strftime('%Y-%m-%d').tolist(),
                        'description': '평균 거래량 대비 5배 이상'
                    })
            
            # 가격 범위 이상치 감지
            if all(col in df.columns for col in ['High', 'Low', 'Close']):
                price_range = (df['High'] - df['Low']) / df['Close']
                extreme_range = price_range > 0.2  # 20% 이상 변동
                
                if extreme_range.any():
                    extreme_dates = df.index[extreme_range]
                    anomalies.append({
                        'type': 'extreme_range',
                        'dates': extreme_dates.strftime('%Y-%m-%d').tolist(),
                        'description': '일일 변동폭 20% 이상'
                    })
            
            if anomalies:
                self.logger.warning(f"[{ticker}] 이상치 감지: {len(anomalies)}개 유형")
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"[{ticker}] 이상치 감지 중 오류: {e}")
            return [] 