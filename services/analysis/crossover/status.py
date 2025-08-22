"""
상태 결정 전용 서비스 (구 구현)
⚠️ 비활성/통합 안내: 본 파일 기능은 `services/analysis/crossover/unified_detector.py`로 통합되었습니다. (2025-08-02)
사용 지침:
- 이 모듈을 직접 import/호출하지 마세요. 새 코드에서는 `SimplifiedCrossoverDetector`에서 제공하는 상태/신호를 사용하세요.
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
# from typing import Dict, Optional

# class StatusDeterminer:
#     """상태 결정 전용 서비스"""
    
#     def __init__(self):
#         self.logger = logging.getLogger(__name__)
    
#     def get_final_status(self, crossover_info: Dict, proximity_info: Dict) -> Dict:
#         """최종 상태 결정 - EMA와 MACD 상태를 모두 결정"""
#         try:
#             # EMA 상태 결정
#             ema_status = self.get_ema_status(
#                 crossover_info.get('ema_crossover'),
#                 proximity_info.get('ema_proximity')
#             )
            
#             # MACD 상태 결정
#             macd_status = self.get_macd_status(
#                 crossover_info.get('macd_crossover'),
#                 proximity_info.get('macd_proximity')
#             )
            
#             return {
#                 'ema_status': ema_status,
#                 'macd_status': macd_status
#             }
            
#         except Exception as e:
#             self.logger.error(f"Error in get_final_status: {str(e)}")
#             return {}
    
#     def get_ema_status(self, ema_crossover: Optional[Dict], 
#                        ema_proximity: Optional[Dict]) -> Dict:
#         """EMA 상태 결정"""
#         try:
#             # 근접성 우선 확인
#             if ema_proximity:
#                 return {
#                     'status': 'proximity',
#                     'message': f"EMA 근접성 감지 ({ema_proximity.get('proximity_ratio', 0):.2%})",
#                     'type': 'proximity',
#                     'direction': ema_proximity.get('direction', 'neutral'),
#                     'strength': ema_proximity.get('strength', 0)
#                 }
            
#             # 최근 크로스오버 확인 (9일 이내)
#             if ema_crossover:
#                 days_ago = ema_crossover.get('days_ago', 999)
#                 if days_ago <= 9:
#                     crossover_type = ema_crossover.get('type', 'unknown')
#                     days_text = ema_crossover.get('days_text', f"{days_ago}일전")
#                     
#                     if crossover_type == 'golden_cross':
#                         return {
#                             'status': 'golden_cross',
#                             'message': f"EMA 골드크로스 ({days_text})",
#                             'type': 'crossover',
#                             'direction': 'bullish',
#                             'strength': ema_crossover.get('strength', 0)
#                         }
#                     elif crossover_type == 'death_cross':
#                         return {
#                             'status': 'death_cross',
#                             'message': f"EMA 데드크로스 ({days_text})",
#                             'type': 'crossover',
#                             'direction': 'bearish',
#                             'strength': ema_crossover.get('strength', 0)
#                         }
            
#             # 기본 상태 반환
#             return {
#                 'status': 'neutral',
#                 'message': 'EMA 중립',
#                 'type': 'neutral',
#                 'direction': 'neutral',
#                 'strength': 0
#             }
            
#         except Exception as e:
#             self.logger.error(f"Error in get_ema_status: {str(e)}")
#             return {
#                 'status': 'error',
#                 'message': 'EMA 상태 결정 오류',
#                 'type': 'error',
#                 'direction': 'neutral',
#                 'strength': 0
#             }
    
#     def get_macd_status(self, macd_crossover: Optional[Dict], 
#                         macd_proximity: Optional[Dict]) -> Dict:
#         """MACD 상태 결정"""
#         try:
#             # 근접성 우선 확인
#             if macd_proximity:
#                 return {
#                     'status': 'proximity',
#                     'message': f"MACD 근접성 감지 ({macd_proximity.get('proximity_ratio', 0):.2%})",
#                     'type': 'proximity',
#                     'direction': macd_proximity.get('direction', 'neutral'),
#                     'strength': macd_proximity.get('strength', 0)
#                 }
            
#             # 최근 크로스오버 확인 (9일 이내)
#             if macd_crossover:
#                 days_ago = macd_crossover.get('days_ago', 999)
#                 if days_ago <= 9:
#                     crossover_type = macd_crossover.get('type', 'unknown')
#                     days_text = macd_crossover.get('days_text', f"{days_ago}일전")
#                     
#                     if crossover_type == 'golden_cross':
#                         return {
#                             'status': 'golden_cross',
#                             'message': f"MACD 골드크로스 ({days_text})",
#                             'type': 'crossover',
#                             'direction': 'bullish',
#                             'strength': macd_crossover.get('strength', 0)
#                         }
#                     elif crossover_type == 'death_cross':
#                         return {
#                             'status': 'death_cross',
#                             'message': f"MACD 데드크로스 ({days_text})",
#                             'type': 'crossover',
#                             'direction': 'bearish',
#                             'strength': macd_crossover.get('strength', 0)
#                         }
            
#             # 기본 상태 반환
#             return {
#                 'status': 'neutral',
#                 'message': 'MACD 중립',
#                 'type': 'neutral',
#                 'direction': 'neutral',
#                 'strength': 0
#             }
            
#         except Exception as e:
#             self.logger.error(f"Error in get_macd_status: {str(e)}")
#             return {
#                 'status': 'error',
#                 'message': 'MACD 상태 결정 오류',
#                 'type': 'error',
#                 'direction': 'neutral',
#                 'strength': 0
#             }
    
#     def _calculate_days_ago(self, date: datetime) -> int:
#         """날짜 차이 계산"""
#         try:
#             return (datetime.now() - date).days
#         except:
#             return 999
    
#     def _get_days_text(self, days_ago: int) -> str:
#         """일수 텍스트 변환"""
#         if days_ago == 0:
#             return "오늘"
#         elif days_ago == 1:
#             return "1일전"
#         else:
#             return f"{days_ago}일전" 