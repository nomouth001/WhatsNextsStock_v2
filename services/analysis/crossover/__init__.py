"""
Crossover Analysis Package
크로스오버 분석 관련 서비스들을 모아놓은 패키지
⚠️ 파일 통합으로 인한 변경 - SimplifiedCrossoverDetector로 통합됨 (2025-08-07)
기존 개별 모듈들은 주석처리되었으며, SimplifiedCrossoverDetector만 사용 가능합니다.
"""

# ⚠️ 파일 통합으로 인한 변경 - SimplifiedCrossoverDetector로 통합됨 (2025-08-07)
# 기존 개별 모듈들은 주석처리되었으며, SimplifiedCrossoverDetector만 사용 가능합니다.

# from .detection import CrossoverDetector
# from .proximity import ProximityDetector
# from .status import StatusDeterminer
# from .display import CrossoverDisplay
# from .unified_detector import UnifiedCrossoverDetector
from .simplified_detector import SimplifiedCrossoverDetector

__all__ = [
    # 'CrossoverDetector',      # 주석처리됨 - SimplifiedCrossoverDetector로 통합
    # 'ProximityDetector',      # 주석처리됨 - SimplifiedCrossoverDetector로 통합
    # 'StatusDeterminer',       # 주석처리됨 - SimplifiedCrossoverDetector로 통합
    # 'CrossoverDisplay',       # 주석처리됨 - SimplifiedCrossoverDetector로 통합
    # 'UnifiedCrossoverDetector',  # 주석처리됨 - SimplifiedCrossoverDetector로 통합
    'SimplifiedCrossoverDetector'  # 통합된 크로스오버 감지기
]

__version__ = "3.0.0" 