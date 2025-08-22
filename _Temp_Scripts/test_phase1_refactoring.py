"""
Phase 1 리팩토링 테스트 스크립트
새로 구현된 모듈들이 제대로 작동하는지 테스트
"""

import sys
import os
import logging
import pandas as pd
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_crossover_modules():
    """크로스오버 모듈들 테스트 (통합된 UnifiedCrossoverDetector 사용)"""
    logger.info("=== 크로스오버 모듈 테스트 시작 (통합 버전) ===")
    
    try:
        # 1. UnifiedCrossoverDetector 테스트 (통합된 모듈)
        from services.analysis.crossover.unified_detector import UnifiedCrossoverDetector
        unified_detector = UnifiedCrossoverDetector()
        logger.info("✓ UnifiedCrossoverDetector 임포트 성공")
        
        # 2. 샘플 데이터로 테스트
        sample_data = create_sample_data()
        
        # 3. 통합 신호 감지 테스트
        all_signals = unified_detector.detect_all_signals(sample_data)
        logger.info(f"✓ 통합 신호 감지 테스트 완료: {len(all_signals)}")
        
        # 4. 크로스오버만 감지 테스트
        crossover_only = unified_detector.detect_crossovers_only(sample_data)
        logger.info(f"✓ 크로스오버만 감지 테스트 완료: {len(crossover_only)}")
        
        # 5. 근접성만 감지 테스트
        proximity_only = unified_detector.detect_proximity_only(sample_data)
        logger.info(f"✓ 근접성만 감지 테스트 완료: {len(proximity_only)}")
        
        logger.info("=== 크로스오버 모듈 테스트 완료 (통합 버전) ===")
        return True
        
    except Exception as e:
        logger.error(f"크로스오버 모듈 테스트 실패: {e}")
        return False

def test_cache_service():
    """캐시 서비스 테스트"""
    logger.info("=== 캐시 서비스 테스트 시작 ===")
    
    try:
        from services.core.cache_service import FileBasedCacheService
        # [경고/메모] 2025-08-19: 프로덕션 표준은 CacheService 사용입니다. 테스트 스크립트에서는 참고만 하세요.
        # 기존 코드: cache_service = FileBasedCacheService()
        from services.core.cache_service import CacheService
        cache_service = CacheService()
        logger.info("✓ FileBasedCacheService 임포트 성공")
        
        # 캐시 저장/조회 테스트
        test_data = {'test': 'data', 'timestamp': datetime.now().isoformat()}
        cache_service.set_cache('test_key', test_data, expire=60)
        logger.info("✓ 캐시 저장 테스트 완료")
        
        retrieved_data = cache_service.get_cache('test_key')
        if retrieved_data and retrieved_data.get('test') == 'data':
            logger.info("✓ 캐시 조회 테스트 완료")
        else:
            logger.error("✗ 캐시 조회 테스트 실패")
            return False
        
        # 캐시 통계 테스트
        stats = cache_service.get_cache_stats()
        logger.info(f"✓ 캐시 통계 테스트 완료: {stats}")
        
        # 캐시 정리 테스트
        cache_service.clear_cache('test_key')
        logger.info("✓ 캐시 정리 테스트 완료")
        
        logger.info("=== 캐시 서비스 테스트 완료 ===")
        return True
        
    except Exception as e:
        logger.error(f"캐시 서비스 테스트 실패: {e}")
        return False

def test_chart_service():
    """차트 서비스 테스트"""
    logger.info("=== 차트 서비스 테스트 시작 ===")
    
    try:
        from services.analysis.chart_service import ChartService
        chart_service = ChartService()
        logger.info("✓ ChartService 임포트 성공")
        
        # 차트 서비스 초기화 테스트
        if hasattr(chart_service, 'logger'):
            logger.info("✓ ChartService 초기화 완료")
        else:
            logger.error("✗ ChartService 초기화 실패")
            return False
        
        logger.info("=== 차트 서비스 테스트 완료 ===")
        return True
        
    except Exception as e:
        logger.error(f"차트 서비스 테스트 실패: {e}")
        return False

def test_unified_service():
    """통합 서비스 테스트"""
    logger.info("=== 통합 서비스 테스트 시작 ===")
    
    try:
        from services.core.unified_market_analysis_service import UnifiedMarketAnalysisService
        unified_service = UnifiedMarketAnalysisService()
        logger.info("✓ UnifiedMarketAnalysisService 임포트 성공")
        
        # 새로운 모듈들이 제대로 주입되었는지 확인
        if hasattr(unified_service, 'unified_detector'):
            logger.info("✓ UnifiedCrossoverDetector 주입 확인")
        else:
            logger.error("✗ UnifiedCrossoverDetector 주입 실패")
            return False
        
        if hasattr(unified_service, 'cache_service'):
            logger.info("✓ FileBasedCacheService 주입 확인")
        else:
            logger.error("✗ FileBasedCacheService 주입 실패")
            return False
        
        logger.info("=== 통합 서비스 테스트 완료 ===")
        return True
        
    except Exception as e:
        logger.error(f"통합 서비스 테스트 실패: {e}")
        return False

def create_sample_data():
    """테스트용 샘플 데이터 생성"""
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    
    # 가격 데이터 생성
    import numpy as np
    np.random.seed(42)
    
    close_prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
    open_prices = close_prices + np.random.randn(100) * 0.2
    high_prices = np.maximum(open_prices, close_prices) + np.random.rand(100) * 0.3
    low_prices = np.minimum(open_prices, close_prices) - np.random.rand(100) * 0.3
    volumes = np.random.randint(1000, 10000, 100)
    
    # DataFrame 생성
    df = pd.DataFrame({
        'Open': open_prices,
        'High': high_prices,
        'Low': low_prices,
        'Close': close_prices,
        'Volume': volumes
    }, index=dates)
    
    # 기술적 지표 추가
    df['EMA5'] = df['Close'].ewm(span=5).mean()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA40'] = df['Close'].ewm(span=40).mean()
    
    # MACD 계산
    exp1 = df['Close'].ewm(span=12).mean()
    exp2 = df['Close'].ewm(span=26).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
    
    return df

def main():
    """메인 테스트 함수"""
    logger.info("Phase 1 리팩토링 테스트 시작")
    
    test_results = []
    
    # 각 모듈별 테스트 실행
    test_results.append(("크로스오버 모듈", test_crossover_modules()))
    test_results.append(("캐시 서비스", test_cache_service()))
    test_results.append(("차트 서비스", test_chart_service()))
    test_results.append(("통합 서비스", test_unified_service()))
    
    # 결과 요약
    logger.info("\n=== 테스트 결과 요약 ===")
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ 통과" if result else "✗ 실패"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n전체 테스트: {passed}/{total} 통과")
    
    if passed == total:
        logger.info("🎉 Phase 1 리팩토링 테스트 모두 통과!")
        return True
    else:
        logger.error("❌ 일부 테스트 실패")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 