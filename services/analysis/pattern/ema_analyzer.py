import logging
import pandas as pd
from typing import Dict, List, Optional

class EMAAnalyzer:
    """EMA 배열 분석 전용 서비스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_ema_array(self, latest_data: pd.Series) -> str:
        """기본 EMA 배열 분석"""
        try:
            # EMA5, EMA20, EMA40 값 추출 (대소문자 무시)
            ema5 = self._get_value_ci(latest_data, 'EMA5', default=0)
            ema20 = self._get_value_ci(latest_data, 'EMA20', default=0)
            ema40 = self._get_value_ci(latest_data, 'EMA40', default=0)
            
            # 고정된 6가지 패턴 판별
            if ema5 > ema20 > ema40:
                return "상승추세"
            elif ema5 < ema20 < ema40:
                return "하락추세"
            elif ema5 > ema20 and ema20 < ema40:
                return "반등추세"
            elif ema5 < ema20 and ema20 > ema40:
                return "조정추세"
            elif ema5 > ema20 and ema20 > ema40:
                return "상승추세"
            else:
                return "횡보추세"
                
        except Exception as e:
            self.logger.error(f"EMA 배열 분석 실패: {e}")
            return "분석불가"
    
    def analyze_ema_array_pattern(self, latest_data: pd.Series) -> str:
        """동적 EMA 배열 패턴 분석"""
        try:
            # EMA 컬럼들 동적 검색
            ema_columns = []
            for col in latest_data.index:
                if 'ema' in col.lower():
                    ema_columns.append(col)
            
            if not ema_columns:
                return "EMA 데이터 없음"
            
            # EMA 값들 정렬
            ema_values = []
            for col in ema_columns:
                value = latest_data.get(col, 0)
                ema_values.append((col, value))
            
            # 값 기준으로 정렬
            ema_values.sort(key=lambda x: x[1], reverse=True)
            
            # 패턴 문자열 생성
            pattern_parts = []
            for col, value in ema_values:
                pattern_parts.append(f"{col}={value:.2f}")
            
            return " > ".join(pattern_parts)
            
        except Exception as e:
            self.logger.error(f"동적 EMA 패턴 분석 실패: {e}")
            return "분석불가"
    
    def calculate_ema_gap(self, close: float, ema: float) -> float:
        """EMA와 종가 간격 계산"""
        try:
            if ema == 0:
                return 0
            return (close - ema) / ema * 100
        except Exception as e:
            self.logger.error(f"EMA 간격 계산 실패: {e}")
            return 0
    
    def get_ema_trend_strength(self, latest_data: pd.Series) -> Dict[str, float]:
        """EMA 추세 강도 계산"""
        try:
            # Close, EMA 값 추출 (대소문자 무시)
            close = self._get_value_ci(latest_data, 'Close', default=0)
            ema5 = self._get_value_ci(latest_data, 'EMA5', default=0)
            ema20 = self._get_value_ci(latest_data, 'EMA20', default=0)
            ema40 = self._get_value_ci(latest_data, 'EMA40', default=0)
            
            # 각 EMA와의 간격 계산
            gap_5 = self.calculate_ema_gap(close, ema5)
            gap_20 = self.calculate_ema_gap(close, ema20)
            gap_40 = self.calculate_ema_gap(close, ema40)
            
            # 추세 강도 계산
            short_trend = gap_5 - gap_20  # 단기 추세
            medium_trend = gap_20 - gap_40  # 중기 추세
            long_trend = gap_5 - gap_40  # 장기 추세
            
            return {
                'short_trend': short_trend,
                'medium_trend': medium_trend,
                'long_trend': long_trend,
                'gap_5': gap_5,
                'gap_20': gap_20,
                'gap_40': gap_40
            }
            
        except Exception as e:
            self.logger.error(f"EMA 추세 강도 계산 실패: {e}")
            return {
                'short_trend': 0,
                'medium_trend': 0,
                'long_trend': 0,
                'gap_5': 0,
                'gap_20': 0,
                'gap_40': 0
            } 

    def _get_value_ci(self, latest_data: pd.Series, key: str, default: float = 0) -> float:
        """Series에서 대소문자 무시(case-insensitive)로 값을 조회합니다."""
        try:
            # 1) 정확 매칭 시도
            if key in latest_data.index:
                return latest_data.get(key, default)
            # 2) 대소문자 무시 매칭
            target = key.lower()
            for col in latest_data.index:
                if str(col).lower() == target:
                    return latest_data[col]
        except Exception:
            pass
        return default