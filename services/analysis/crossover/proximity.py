"""
근접성 감지 전용 서비스 (구 구현)
⚠️ 비활성/통합 안내: 본 파일 기능은 `services/analysis/crossover/unified_detector.py`로 통합되었습니다. (2025-08-02)
사용 지침:
- 이 모듈을 직접 import/호출하지 마세요. 새 코드에서는 `SimplifiedCrossoverDetector`(또는 통합 감지기)를 사용하세요.
- 본 파일은 과거 구현을 주석으로 보존합니다.

권장 사용 예시:
    from services.analysis.crossover.simplified_detector import SimplifiedCrossoverDetector
"""

# ⚠️ 파일 통합으로 인한 비활성화 - UnifiedCrossoverDetector로 통합됨 (2025-08-02)
# 이 파일의 기능은 services/analysis/crossover/unified_detector.py로 통합되었습니다.
# 기존 코드와의 호환성을 위해 주석처리하여 보존합니다.

# import logging
# import pandas as pd
# from datetime import datetime, timedelta
# import numpy as np
# from typing import Dict, Optional, List, Tuple

# class ProximityDetector:
#     """근접성 감지 전용 서비스"""
    
#     def __init__(self):
#         self.logger = logging.getLogger(__name__)
#         self.proximity_threshold = 0.05  # 5% 임계값
    
#     def detect_proximity_signals(self, indicators_df: pd.DataFrame) -> Dict:
#         """통합 근접성 감지 - EMA와 MACD 근접성 모두 감지"""
#         try:
#             if indicators_df.empty:
#                 return {}
            
#             # 최근 10일 데이터 추출
#             recent_data = indicators_df.tail(10)
            
#             # EMA 근접성 감지
#             ema_proximity = self.detect_ema_proximity(recent_data)
            
#             # MACD 근접성 감지
#             macd_proximity = self.detect_macd_proximity(recent_data)
            
#             return {
#                 'ema_proximity': ema_proximity,
#                 'macd_proximity': macd_proximity
#             }
            
#         except Exception as e:
#             self.logger.error(f"Error in detect_proximity_signals: {str(e)}")
#             return {}
    
#     def detect_ema_proximity(self, data: pd.DataFrame) -> Optional[Dict]:
#         """EMA 근접성 감지"""
#         try:
#             # EMA 컬럼들 확인
#             ema_columns = [col for col in data.columns if col.startswith('EMA')]
#             if len(ema_columns) < 2:
#                 return None
            
#             # EMA5-EMA20 근접성 감지
#             ema5_ema20_proximity = self._detect_single_ema_proximity(data, 'EMA5', 'EMA20')
            
#             # EMA5-EMA40 근접성 감지
#             ema5_ema40_proximity = self._detect_single_ema_proximity(data, 'EMA5', 'EMA40')
            
#             # EMA20-EMA40 근접성 감지
#             ema20_ema40_proximity = self._detect_single_ema_proximity(data, 'EMA20', 'EMA40')
            
#             return {
#                 'ema5_ema20': ema5_ema20_proximity,
#                 'ema5_ema40': ema5_ema40_proximity,
#                 'ema20_ema40': ema20_ema40_proximity
#             }
            
#         except Exception as e:
#             self.logger.error(f"Error in detect_ema_proximity: {str(e)}")
#             return None
    
#     def detect_macd_proximity(self, data: pd.DataFrame) -> Optional[Dict]:
#         """MACD 근접성 감지"""
#         try:
#             if 'MACD' not in data.columns or 'MACD_Signal' not in data.columns:
#                 return None
            
#             # 최근 데이터에서 MACD 근접성 감지
#             latest = data.iloc[-1]
#             prev = data.iloc[-2] if len(data) > 1 else latest
            
#             macd_diff = abs(latest['MACD'] - latest['MACD_Signal'])
#             macd_avg = (latest['MACD'] + latest['MACD_Signal']) / 2
            
#             if macd_avg != 0:
#                 proximity_ratio = macd_diff / abs(macd_avg)
#             else:
#                 proximity_ratio = 1.0
            
#             if proximity_ratio <= self.proximity_threshold:
#                 return {
#                     'type': 'proximity',
#                     'date': data.index[-1],
#                     'macd_value': latest['MACD'],
#                     'signal_value': latest['MACD_Signal'],
#                     'proximity_ratio': proximity_ratio,
#                     'direction': 'bullish' if latest['MACD'] > latest['MACD_Signal'] else 'bearish'
#                 }
            
#             return None
            
#         except Exception as e:
#             self.logger.error(f"Error in detect_macd_proximity: {str(e)}")
#             return None
    
#     def _detect_single_ema_proximity(self, data: pd.DataFrame, ema1: str, ema2: str) -> Optional[Dict]:
#         """단일 EMA 근접성 감지"""
#         try:
#             if ema1 not in data.columns or ema2 not in data.columns:
#                 return None
            
#             # 최근 데이터에서 EMA 근접성 감지
#             latest = data.iloc[-1]
#             prev = data.iloc[-2] if len(data) > 1 else latest
            
#             ema_diff = abs(latest[ema1] - latest[ema2])
#             ema_avg = (latest[ema1] + latest[ema2]) / 2
            
#             if ema_avg != 0:
#                 proximity_ratio = ema_diff / abs(ema_avg)
#             else:
#                 proximity_ratio = 1.0
            
#             if proximity_ratio <= self.proximity_threshold:
#                 return {
#                     'type': 'proximity',
#                     'date': data.index[-1],
#                     'ema1_value': latest[ema1],
#                     'ema2_value': latest[ema2],
#                     'proximity_ratio': proximity_ratio,
#                     'direction': 'bullish' if latest[ema1] > latest[ema2] else 'bearish'
#                 }
            
#             return None
            
#         except Exception as e:
#             self.logger.error(f"Error in _detect_single_ema_proximity: {str(e)}")
#             return None 