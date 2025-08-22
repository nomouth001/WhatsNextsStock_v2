"""
크로스오버 표시 정보 생성 서비스 (구 구현)
⚠️ 비활성/통합 안내: 본 파일 기능은 `services/analysis/crossover/unified_detector.py`로 통합되었습니다. (2025-08-02)
사용 지침:
- 이 모듈을 직접 import/호출하지 마세요. 새 코드에서는 `SimplifiedCrossoverDetector`의 분석 결과를 사용하세요.
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

# class CrossoverDisplay:
#     """크로스오버 표시 정보 생성 서비스"""
    
#     def __init__(self):
#         self.logger = logging.getLogger(__name__)
    
#     def create_display_info(self, crossover_data: Dict) -> Optional[Dict]:
#         """크로스오버 표시 정보 생성"""
#         try:
#             if not crossover_data:
#                 return None
            
#             crossover_type = crossover_data.get('type', '')
#             days_ago = crossover_data.get('days_ago', 0)
#             days_text = crossover_data.get('days_text', f"{days_ago}일전")
            
#             # 크로스오버 타입별 의미 해석
#             meaning = self.get_crossover_meaning(crossover_type)
            
#             # 표시용 텍스트 생성
#             display_text = f"{meaning} ({days_text})"
            
#             # 색상 정보 추가
#             color_info = self._get_color_info(crossover_type)
            
#             return {
#                 'type': crossover_type,
#                 'meaning': meaning,
#                 'display_text': display_text,
#                 'days_ago': days_ago,
#                 'days_text': days_text,
#                 'color': color_info['color'],
#                 'bg_color': color_info['bg_color'],
#                 'html': f'<span class="badge bg-{color_info["bg_color"]}">{display_text}</span>'
#             }
            
#         except Exception as e:
#             self.logger.error(f"Error in create_display_info: {str(e)}")
#             return None
    
#     def create_status_display(self, analysis_data: Dict) -> Dict:
#         """상태 표시 정보 생성"""
#         try:
#             # EMA 상태 표시 정보
#             ema_status = analysis_data.get('ema_status', {})
#             ema_display = self._create_status_display_item(ema_status, 'EMA')
            
#             # MACD 상태 표시 정보
#             macd_status = analysis_data.get('macd_status', {})
#             macd_display = self._create_status_display_item(macd_status, 'MACD')
            
#             return {
#                 'ema_display': ema_display,
#                 'macd_display': macd_display,
#                 'overall_status': self._determine_overall_status(ema_status, macd_status)
#             }
            
#         except Exception as e:
#             self.logger.error(f"Error in create_status_display: {str(e)}")
#             return {}
    
#     def get_crossover_meaning(self, crossover_type: str) -> str:
#         """크로스오버 타입별 의미 반환"""
#         meanings = {
#             'golden_cross': '골드크로스',
#             'death_cross': '데드크로스',
#             'dead_cross': '데드크로스',
#             'proximity': '근접성',
#             'unknown': '알 수 없음'
#         }
#         return meanings.get(crossover_type, '크로스오버')
    
#     def _create_status_display_item(self, status_data: Dict, indicator_type: str) -> Dict:
#         """상태 표시 아이템 생성"""
#         try:
#             status = status_data.get('status', 'neutral')
#             message = status_data.get('message', f'{indicator_type} 중립')
#             direction = status_data.get('direction', 'neutral')
#             strength = status_data.get('strength', 0)
            
#             # 색상 정보
#             color_info = self._get_status_color_info(status, direction)
            
#             return {
#                 'status': status,
#                 'message': message,
#                 'direction': direction,
#                 'strength': strength,
#                 'color': color_info['color'],
#                 'bg_color': color_info['bg_color'],
#                 'html': f'<span class="badge bg-{color_info["bg_color"]}">{message}</span>'
#             }
            
#         except Exception as e:
#             self.logger.error(f"Error in _create_status_display_item: {str(e)}")
#             return {
#                 'status': 'error',
#                 'message': f'{indicator_type} 오류',
#                 'direction': 'neutral',
#                 'strength': 0,
#                 'color': 'danger',
#                 'bg_color': 'danger',
#                 'html': f'<span class="badge bg-danger">{indicator_type} 오류</span>'
#             }
    
#     def _determine_overall_status(self, ema_status: Dict, macd_status: Dict) -> str:
#         """전체 상태 결정"""
#         try:
#             # 우선순위: 오류 > 근접성 > 크로스오버 > 중립
#             if ema_status.get('status') == 'error' or macd_status.get('status') == 'error':
#                 return 'error'
#             elif ema_status.get('status') == 'proximity' or macd_status.get('status') == 'proximity':
#                 return 'proximity'
#             elif ema_status.get('status') in ['golden_cross', 'death_cross'] or macd_status.get('status') in ['golden_cross', 'death_cross']:
#                 return 'crossover'
#             else:
#                 return 'neutral'
                
#         except Exception as e:
#             self.logger.error(f"Error in _determine_overall_status: {str(e)}")
#             return 'error'
    
#     def _get_color_info(self, crossover_type: str) -> Dict:
#         """크로스오버 타입별 색상 정보"""
#         color_map = {
#             'golden_cross': {'color': 'success', 'bg_color': 'success'},
#             'death_cross': {'color': 'danger', 'bg_color': 'danger'},
#             'dead_cross': {'color': 'danger', 'bg_color': 'danger'},
#             'proximity': {'color': 'warning', 'bg_color': 'warning'},
#             'unknown': {'color': 'secondary', 'bg_color': 'secondary'}
#         }
#         return color_map.get(crossover_type, {'color': 'secondary', 'bg_color': 'secondary'})
    
#     def _get_status_color_info(self, status: str, direction: str) -> Dict:
#         """상태별 색상 정보"""
#         if status == 'error':
#             return {'color': 'danger', 'bg_color': 'danger'}
#         elif status == 'proximity':
#             return {'color': 'warning', 'bg_color': 'warning'}
#         elif status == 'golden_cross':
#             return {'color': 'success', 'bg_color': 'success'}
#         elif status == 'death_cross':
#             return {'color': 'danger', 'bg_color': 'danger'}
#         else:
#             return {'color': 'secondary', 'bg_color': 'secondary'} 