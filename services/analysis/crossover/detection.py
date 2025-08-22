"""
크로스오버 감지 전용 서비스 (구 구현)
⚠️ 비활성/통합 안내: 본 파일 기능은 `services/analysis/crossover/simplified_detector.py`로 통합되었습니다. (2025-08-02)
사용 지침:
- 이 모듈을 직접 사용하지 마세요. 새 코드에서는 반드시 `SimplifiedCrossoverDetector`를 사용하세요.
- 호환성 유지 목적의 alias만 제공합니다.

권장 사용 예시:
    from services.analysis.crossover.simplified_detector import SimplifiedCrossoverDetector as CrossoverDetector

참고: 본 파일의 과거 구현은 주석으로 보존되며, 런타임 로직은 제공하지 않습니다.
"""

# 호환성을 위한 import
from .simplified_detector import SimplifiedCrossoverDetector

# 기존 코드와의 호환성을 위한 alias
CrossoverDetector = SimplifiedCrossoverDetector

# ⚠️ 파일 통합으로 인한 비활성화 - SimplifiedCrossoverDetector로 통합됨 (2025-08-02)
# 이 파일의 기능은 services/analysis/crossover/simplified_detector.py로 통합되었습니다.
# 기존 코드와의 호환성을 위해 주석처리하여 보존합니다.

# import logging
# import pandas as pd
# from datetime import datetime, timedelta
# import numpy as np
# from typing import Dict, Optional, List, Tuple

# class CrossoverDetector:
#     """크로스오버 감지 전용 서비스"""
    
#     def __init__(self):
#         self.logger = logging.getLogger(__name__)
    
#     def detect_all_crossovers(self, indicators_df: pd.DataFrame) -> Dict:
#         """통합 크로스오버 감지 - EMA와 MACD 모두 감지"""
#         try:
#             if indicators_df.empty:
#                 return {}
            
#             # 최근 60일 데이터 추출
#             recent_data = indicators_df.tail(60)
            
#             # EMA 크로스오버 감지
#             ema_crossover = self.detect_ema_crossover(recent_data)
            
#             # MACD 크로스오버 감지
#             macd_crossover = self.detect_macd_crossover(recent_data)
            
#             return {
#                 'ema_crossover': ema_crossover,
#                 'macd_crossover': macd_crossover
#             }
            
#         except Exception as e:
#             self.logger.error(f"Error in detect_all_crossovers: {str(e)}")
#             return {}
    
#     def detect_ema_crossover(self, data: pd.DataFrame) -> Optional[Dict]:
#         """EMA 크로스오버 감지"""
#         try:
#             # EMA 컬럼들 확인
#             ema_columns = [col for col in data.columns if col.startswith('EMA')]
#             if len(ema_columns) < 2:
#                 return None
            
#             # EMA5-EMA20 크로스오버 감지
#             ema5_ema20_crossover = self._detect_single_ema_crossover(data, 'EMA5', 'EMA20')
            
#             # EMA5-EMA40 크로스오버 감지
#             ema5_ema40_crossover = self._detect_single_ema_crossover(data, 'EMA5', 'EMA40')
            
#             # EMA20-EMA40 크로스오버 감지
#             ema20_ema40_crossover = self._detect_single_ema_crossover(data, 'EMA20', 'EMA40')
            
#             return {
#                 'ema5_ema20': ema5_ema20_crossover,
#                 'ema5_ema40': ema5_ema40_crossover,
#                 'ema20_ema40': ema20_ema40_crossover
#             }
            
#         except Exception as e:
#             self.logger.error(f"Error in detect_ema_crossover: {str(e)}")
#             return None
    
#     def detect_macd_crossover(self, data: pd.DataFrame) -> Optional[Dict]:
#         """MACD 크로스오버 감지"""
#         try:
#             if 'MACD' not in data.columns or 'MACD_Signal' not in data.columns:
#                 return None
            
#             # 최근 20일 데이터에서 MACD 크로스오버 감지
#             recent_data = data.tail(20)
            
#             crossover_info = None
#             crossover_date = None
#             crossover_type = None
            
#             for i in range(1, len(recent_data)):
#                 prev_macd = recent_data.iloc[i-1]['MACD']
#                 prev_signal = recent_data.iloc[i-1]['MACD_Signal']
#                 curr_macd = recent_data.iloc[i]['MACD']
#                 curr_signal = recent_data.iloc[i]['MACD_Signal']
                
#                 # 골드크로스 (MACD가 Signal을 상향 돌파)
#                 if prev_macd <= prev_signal and curr_macd > curr_signal:
#                     crossover_info = {
#                         'type': 'golden_cross',
#                         'date': recent_data.index[i],
#                         'macd_value': curr_macd,
#                         'signal_value': curr_signal,
#                         'strength': abs(curr_macd - curr_signal)
#                     }
#                     crossover_date = recent_data.index[i]
#                     crossover_type = 'golden_cross'
#                     break
                
#                 # 데드크로스 (MACD가 Signal을 하향 돌파)
#                 elif prev_macd >= prev_signal and curr_macd < curr_signal:
#                     crossover_info = {
#                         'type': 'death_cross',
#                         'date': recent_data.index[i],
#                         'macd_value': curr_macd,
#                         'signal_value': curr_signal,
#                         'strength': abs(curr_macd - curr_signal)
#                     }
#                     crossover_date = recent_data.index[i]
#                     crossover_type = 'death_cross'
#                     break
            
#             if crossover_info:
#                 days_ago = (datetime.now() - crossover_date).days
#                 crossover_info['days_ago'] = days_ago
#                 crossover_info['days_text'] = self._get_days_text(days_ago)
            
#             return crossover_info
            
#         except Exception as e:
#             self.logger.error(f"Error in detect_macd_crossover: {str(e)}")
#             return None
    
#     def _detect_single_ema_crossover(self, data: pd.DataFrame, ema1: str, ema2: str) -> Optional[Dict]:
#         """단일 EMA 크로스오버 감지"""
#         try:
#             if ema1 not in data.columns or ema2 not in data.columns:
#                 return None
            
#             crossover_info = None
#             crossover_date = None
#             crossover_type = None
            
#             for i in range(1, len(data)):
#                 prev_ema1 = data.iloc[i-1][ema1]
#                 prev_ema2 = data.iloc[i-1][ema2]
#                 curr_ema1 = data.iloc[i][ema1]
#                 curr_ema2 = data.iloc[i][ema2]
                
#                 # 골드크로스 (EMA1이 EMA2를 상향 돌파)
#                 if prev_ema1 <= prev_ema2 and curr_ema1 > curr_ema2:
#                     crossover_info = {
#                         'type': 'golden_cross',
#                         'date': data.index[i],
#                         'ema1_value': curr_ema1,
#                         'ema2_value': curr_ema2,
#                         'strength': abs(curr_ema1 - curr_ema2)
#                     }
#                     crossover_date = data.index[i]
#                     crossover_type = 'golden_cross'
#                     break
                
#                 # 데드크로스 (EMA1이 EMA2를 하향 돌파)
#                 elif prev_ema1 >= prev_ema2 and curr_ema1 < curr_ema2:
#                     crossover_info = {
#                         'type': 'death_cross',
#                         'date': data.index[i],
#                         'ema1_value': curr_ema1,
#                         'ema2_value': curr_ema2,
#                         'strength': abs(curr_ema1 - curr_ema2)
#                     }
#                     crossover_date = data.index[i]
#                     crossover_type = 'death_cross'
#                     break
            
#             if crossover_info:
#                 days_ago = (datetime.now() - crossover_date).days
#                 crossover_info['days_ago'] = days_ago
#                 crossover_info['days_text'] = self._get_days_text(days_ago)
            
#             return crossover_info
            
#         except Exception as e:
#             self.logger.error(f"Error in _detect_single_ema_crossover: {str(e)}")
#             return None
    
#     def _get_days_text(self, days_ago: int) -> str:
#         """일수 텍스트 변환"""
#         if days_ago == 0:
#             return "오늘"
#         elif days_ago == 1:
#             return "1일전"
#         else:
#             return f"{days_ago}일전" 