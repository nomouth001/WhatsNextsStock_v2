import logging
from typing import Dict, Optional

class ImportanceCalculator:
    """중요도 점수 계산 서비스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_basic_score(self, analysis_result: Dict) -> float:
        """기본 중요도 점수 계산"""
        try:
            score = 0.0
            
            # 골드크로스/데드크로스 점수
            crossover_type = analysis_result.get('crossover_type', 'none')
            if crossover_type == 'golden_cross':
                score += 10.0
            elif crossover_type == 'dead_cross':
                score += 8.0
            
            # EMA 배열 패턴 점수
            ema_pattern = analysis_result.get('ema_pattern', '')
            if ema_pattern == "상승추세":
                score += 5.0
            elif ema_pattern == "하락추세":
                score += 4.0
            elif ema_pattern == "반등추세":
                score += 6.0
            elif ema_pattern == "조정추세":
                score += 3.0
            
            # 기본 점수 반환
            return min(score, 20.0)  # 최대 20점
            
        except Exception as e:
            self.logger.error(f"기본 점수 계산 실패: {e}")
            return 0.0
    
    def calculate_advanced_score(self, crossover_type: str, days_since: int, 
                               proximity_signal: Optional[Dict]) -> float:
        """고급 중요도 점수 계산"""
        try:
            score = 0.0
            
            # 크로스오버 타입별 점수
            if crossover_type == 'golden_cross':
                score += 15.0
            elif crossover_type == 'dead_cross':
                score += 12.0
            elif crossover_type == 'ema_crossover':
                score += 8.0
            elif crossover_type == 'macd_crossover':
                score += 6.0
            
            # 일수별 가중치 적용
            if days_since <= 1:
                score *= 1.5  # 오늘/어제 발생
            elif days_since <= 3:
                score *= 1.3  # 3일 이내
            elif days_since <= 7:
                score *= 1.1  # 1주 이내
            elif days_since > 14:
                score *= 0.5  # 2주 이상
            
            # 근접성 점수 추가
            if proximity_signal:
                proximity_score = self.calculate_proximity_score(proximity_signal)
                score += proximity_score
            
            # 복합 점수 반환
            return min(score, 30.0)  # 최대 30점
            
        except Exception as e:
            self.logger.error(f"고급 점수 계산 실패: {e}")
            return 0.0
    
    def calculate_proximity_score(self, proximity_signal: Dict) -> float:
        """근접성 점수 계산"""
        try:
            score = 0.0
            
            # 근접성 강도 계산
            proximity_strength = proximity_signal.get('strength', 0)
            if proximity_strength > 0.8:
                score += 8.0
            elif proximity_strength > 0.6:
                score += 6.0
            elif proximity_strength > 0.4:
                score += 4.0
            elif proximity_strength > 0.2:
                score += 2.0
            
            # 방향성 점수 추가
            direction = proximity_signal.get('direction', 'neutral')
            if direction == 'bullish':
                score += 3.0
            elif direction == 'bearish':
                score += 2.0
            
            # 근접성 점수 반환
            return min(score, 10.0)  # 최대 10점
            
        except Exception as e:
            self.logger.error(f"근접성 점수 계산 실패: {e}")
            return 0.0
    
    def calculate_comprehensive_score(self, analysis_data: Dict) -> Dict[str, float]:
        """종합 점수 계산"""
        try:
            # 기본 점수
            basic_score = self.calculate_basic_score(analysis_data)
            
            # 고급 점수
            crossover_type = analysis_data.get('crossover_type', 'none')
            days_since = analysis_data.get('days_since', 0)
            proximity_signal = analysis_data.get('proximity_signal')
            advanced_score = self.calculate_advanced_score(crossover_type, days_since, proximity_signal)
            
            # 근접성 점수
            proximity_score = 0.0
            if proximity_signal:
                proximity_score = self.calculate_proximity_score(proximity_signal)
            
            # 종합 점수
            total_score = basic_score + advanced_score + proximity_score
            
            return {
                'basic_score': basic_score,
                'advanced_score': advanced_score,
                'proximity_score': proximity_score,
                'total_score': total_score
            }
            
        except Exception as e:
            self.logger.error(f"종합 점수 계산 실패: {e}")
            return {
                'basic_score': 0.0,
                'advanced_score': 0.0,
                'proximity_score': 0.0,
                'total_score': 0.0
            }
    
    def get_score_level(self, score: float) -> str:
        """점수 레벨 반환"""
        if score >= 25:
            return "매우높음"
        elif score >= 20:
            return "높음"
        elif score >= 15:
            return "보통"
        elif score >= 10:
            return "낮음"
        else:
            return "매우낮음"
    
    def get_score_color(self, score: float) -> str:
        """점수별 색상 반환"""
        if score >= 25:
            return "danger"
        elif score >= 20:
            return "warning"
        elif score >= 15:
            return "info"
        elif score >= 10:
            return "success"
        else:
            return "secondary" 