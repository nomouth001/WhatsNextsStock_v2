import logging
import pandas as pd
from typing import Dict, Optional

class StockClassifier:
    """주식 분류 결정 서비스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def determine_classification(self, ticker: str, latest_data: pd.Series, 
                               crossover_info: Dict, market_type: str) -> str:
        """기본 분류 결정"""
        try:
            # 크로스오버 분류
            crossover_type = crossover_info.get('type', 'none')
            if crossover_type == 'golden_cross':
                return "골드크로스"
            elif crossover_type == 'dead_cross':
                return "데드크로스"
            
            # EMA 배열 패턴 분류
            ema_pattern = self._analyze_ema_pattern(latest_data)
            if ema_pattern == "상승추세":
                return "상승추세"
            elif ema_pattern == "하락추세":
                return "하락추세"
            elif ema_pattern == "반등추세":
                return "반등추세"
            elif ema_pattern == "조정추세":
                return "조정추세"
            
            # 기본 분류 카테고리 반환
            return "횡보추세"
            
        except Exception as e:
            self.logger.error(f"기본 분류 결정 실패: {e}")
            return "분류불가"
    
    def determine_advanced_classification(self, ticker: str, latest_data: pd.Series,
                                        crossover_info: Dict, proximity_info: Dict, 
                                        market_type: str) -> str:
        """고급 분류 결정 (뉴스레터용)"""
        try:
            # 크로스오버 + 근접성 분류
            crossover_type = crossover_info.get('type', 'none')
            proximity_type = proximity_info.get('type', 'none')
            
            # 복합 신호 분석
            if crossover_type == 'golden_cross' and proximity_type == 'bullish':
                return "강력매수"
            elif crossover_type == 'dead_cross' and proximity_type == 'bearish':
                return "강력매도"
            elif crossover_type == 'golden_cross':
                return "매수신호"
            elif crossover_type == 'dead_cross':
                return "매도신호"
            elif proximity_type == 'bullish':
                return "관망상승"
            elif proximity_type == 'bearish':
                return "관망하락"
            
            # EMA 배열 패턴 분류
            ema_pattern = self._analyze_ema_pattern(latest_data)
            if ema_pattern == "상승추세":
                return "상승추세"
            elif ema_pattern == "하락추세":
                return "하락추세"
            elif ema_pattern == "반등추세":
                return "반등추세"
            elif ema_pattern == "조정추세":
                return "조정추세"
            
            # 복합 분류 카테고리 반환
            return "횡보추세"
            
        except Exception as e:
            self.logger.error(f"고급 분류 결정 실패: {e}")
            return "분류불가"
    
    def _analyze_ema_pattern(self, latest_data: pd.Series) -> str:
        """EMA 패턴 분석"""
        try:
            from .ema_analyzer import EMAAnalyzer
            ema_analyzer = EMAAnalyzer()
            return ema_analyzer.analyze_ema_array(latest_data)
        except Exception as e:
            self.logger.error(f"EMA 패턴 분석 실패: {e}")
            return "분석불가"
    
    def get_classification_priority(self, classification: str) -> int:
        """분류 우선순위 반환"""
        priority_map = {
            "강력매수": 1,
            "강력매도": 1,
            "매수신호": 2,
            "매도신호": 2,
            "골드크로스": 3,
            "데드크로스": 3,
            "관망상승": 4,
            "관망하락": 4,
            "상승추세": 5,
            "하락추세": 5,
            "반등추세": 6,
            "조정추세": 6,
            "횡보추세": 7,
            "분류불가": 8
        }
        return priority_map.get(classification, 9)
    
    def get_classification_color(self, classification: str) -> str:
        """분류별 색상 반환"""
        color_map = {
            "강력매수": "success",
            "매수신호": "success",
            "골드크로스": "success",
            "관망상승": "info",
            "상승추세": "info",
            "반등추세": "warning",
            "횡보추세": "secondary",
            "조정추세": "warning",
            "관망하락": "warning",
            "하락추세": "danger",
            "매도신호": "danger",
            "데드크로스": "danger",
            "강력매도": "danger",
            "분류불가": "secondary"
        }
        return color_map.get(classification, "secondary") 