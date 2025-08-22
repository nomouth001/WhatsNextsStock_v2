"""
통합 크로스오버 감지 모듈 테스트 스크립트
새로 구현된 UnifiedCrossoverDetector가 제대로 작동하는지 테스트
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

def test_unified_detector():
    """통합 감지 모듈 테스트"""
    logger.info("=== 통합 크로스오버 감지 모듈 테스트 시작 ===")
    
    try:
        # 1. UnifiedCrossoverDetector 임포트 및 초기화
        from services.analysis.crossover.unified_detector import UnifiedCrossoverDetector
        detector = UnifiedCrossoverDetector()
        logger.info("✓ UnifiedCrossoverDetector 임포트 성공")
        
        # 2. 샘플 데이터 생성
        sample_data = create_sample_data()
        logger.info(f"✓ 샘플 데이터 생성 완료: {len(sample_data)}행")
        
        # 3. 통합 신호 감지 테스트
        all_signals = detector.detect_all_signals(sample_data)
        logger.info(f"✓ 통합 신호 감지 테스트 완료: {len(all_signals)}")
        
        # 4. 크로스오버만 감지 테스트
        crossover_only = detector.detect_crossovers_only(sample_data)
        logger.info(f"✓ 크로스오버만 감지 테스트 완료: {len(crossover_only)}")
        
        # 5. 근접성만 감지 테스트
        proximity_only = detector.detect_proximity_only(sample_data)
        logger.info(f"✓ 근접성만 감지 테스트 완료: {len(proximity_only)}")
        
        # 6. 결과 검증
        logger.info("=== 결과 검증 ===")
        
        # 통합 신호 결과
        if all_signals:
            logger.info(f"  - EMA 신호: {all_signals.get('ema_signals', {}).get('type', 'None')}")
            logger.info(f"  - MACD 신호: {all_signals.get('macd_signals', {}).get('type', 'None')}")
            logger.info(f"  - 전체 상태: {all_signals.get('overall_status', 'None')}")
        else:
            logger.info("  - 통합 신호: 없음")
        
        # 크로스오버 결과
        if crossover_only.get('ema_crossover') or crossover_only.get('macd_crossover'):
            logger.info("  - 크로스오버: 감지됨")
        else:
            logger.info("  - 크로스오버: 없음")
        
        # 근접성 결과
        if proximity_only.get('ema_proximity') or proximity_only.get('macd_proximity'):
            logger.info("  - 근접성: 감지됨")
        else:
            logger.info("  - 근접성: 없음")
        
        logger.info("=== 통합 크로스오버 감지 모듈 테스트 완료 ===")
        return True
        
    except Exception as e:
        logger.error(f"통합 크로스오버 감지 모듈 테스트 실패: {e}")
        return False

def test_backward_compatibility():
    """기존 호환성 테스트"""
    logger.info("=== 기존 호환성 테스트 시작 ===")
    
    try:
        from services.analysis.crossover.unified_detector import UnifiedCrossoverDetector
        detector = UnifiedCrossoverDetector()
        
        sample_data = create_sample_data()
        
        # 기존 메서드들이 제대로 작동하는지 확인
        crossover_result = detector.detect_crossovers_only(sample_data)
        proximity_result = detector.detect_proximity_only(sample_data)
        
        # 결과 구조 확인
        expected_crossover_keys = ['ema_crossover', 'macd_crossover']
        expected_proximity_keys = ['ema_proximity', 'macd_proximity']
        
        crossover_keys_ok = all(key in crossover_result for key in expected_crossover_keys)
        proximity_keys_ok = all(key in proximity_result for key in expected_proximity_keys)
        
        if crossover_keys_ok and proximity_keys_ok:
            logger.info("✓ 기존 호환성 테스트 통과")
            return True
        else:
            logger.error("✗ 기존 호환성 테스트 실패")
            return False
            
    except Exception as e:
        logger.error(f"기존 호환성 테스트 실패: {e}")
        return False

def test_performance():
    """성능 테스트"""
    logger.info("=== 성능 테스트 시작 ===")
    
    try:
        from services.analysis.crossover.unified_detector import UnifiedCrossoverDetector
        import time
        
        detector = UnifiedCrossoverDetector()
        sample_data = create_sample_data()
        
        # 통합 신호 감지 성능 측정
        start_time = time.time()
        for _ in range(10):
            detector.detect_all_signals(sample_data)
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 10
        logger.info(f"✓ 통합 신호 감지 평균 시간: {avg_time:.4f}초")
        
        # 기존 방식과 비교 (시뮬레이션)
        start_time = time.time()
        for _ in range(10):
            detector.detect_crossovers_only(sample_data)
            detector.detect_proximity_only(sample_data)
        end_time = time.time()
        
        avg_time_old = (end_time - start_time) / 10
        logger.info(f"✓ 기존 방식 평균 시간: {avg_time_old:.4f}초")
        
        if avg_time < avg_time_old:
            logger.info(f"✓ 성능 개선: {((avg_time_old - avg_time) / avg_time_old * 100):.1f}% 향상")
        else:
            logger.info(f"⚠ 성능 변화: {((avg_time - avg_time_old) / avg_time_old * 100):.1f}% 변화")
        
        return True
        
    except Exception as e:
        logger.error(f"성능 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    logger.info("통합 크로스오버 감지 모듈 테스트 시작")
    
    test_results = []
    
    # 각 테스트 실행
    test_results.append(("통합 감지 모듈", test_unified_detector()))
    test_results.append(("기존 호환성", test_backward_compatibility()))
    test_results.append(("성능 테스트", test_performance()))
    
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
        logger.info("🎉 통합 크로스오버 감지 모듈 테스트 모두 통과!")
        return True
    else:
        logger.error("❌ 일부 테스트 실패")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 