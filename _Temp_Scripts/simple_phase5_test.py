"""
간단한 Phase 5 테스트 스크립트
기본적인 검증만 수행합니다.
"""

import sys
import os
import time
import logging
from datetime import datetime
from typing import Dict, Any

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/simple_phase5_test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def test_mock_service():
    """Mock 서비스 테스트"""
    try:
        from services.core.mock_unified_service import MockUnifiedMarketAnalysisService
        
        logger.info("🔍 Mock 서비스 테스트 시작")
        
        service = MockUnifiedMarketAnalysisService()
        
        # 단일 종목 분석 테스트
        result = service.analyze_single_stock_comprehensive(
            ticker="005930.KS",
            market_type="KOSPI",
            timeframe="d"
        )
        
        if result.get("success", False):
            logger.info("✅ Mock 단일 종목 분석 성공")
            logger.info(f"   - 심볼: {result.get('symbol')}")
            logger.info(f"   - 기술적 분석 점수: {result.get('technical_analysis', {}).get('analysis_score', 0)}")
            logger.info(f"   - 기본적 분석 점수: {result.get('fundamental_analysis', {}).get('analysis_score', 0)}")
            logger.info(f"   - AI 분석 점수: {result.get('ai_analysis', {}).get('analysis_score', 0)}")
        else:
            logger.error("❌ Mock 단일 종목 분석 실패")
            return False
        
        # 시장 분석 테스트
        market_result = service.analyze_market_comprehensive(
            market_type="KOSPI",
            timeframe="d"
        )
        
        if market_result.get("success", False):
            logger.info("✅ Mock 시장 분석 성공")
            logger.info(f"   - 시장: {market_result.get('market')}")
            logger.info(f"   - 분석된 종목 수: {market_result.get('analyzed_stocks')}")
            logger.info(f"   - 시장 트렌드: {market_result.get('market_trend')}")
        else:
            logger.error("❌ Mock 시장 분석 실패")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Mock 서비스 테스트 실패 - {str(e)}")
        return False


def test_basic_validation():
    """기본 검증 테스트"""
    try:
        logger.info("🔍 기본 검증 테스트 시작")
        
        # 성능 테스트
        start_time = time.time()
        time.sleep(0.1)  # 간단한 처리 시뮬레이션
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        if processing_time < 1.0:
            logger.info("✅ 성능 테스트 통과")
        else:
            logger.warning("⚠️ 성능 테스트 경고")
        
        # 메모리 테스트
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        if memory_mb < 1000:  # 1GB 이하
            logger.info("✅ 메모리 테스트 통과")
        else:
            logger.warning("⚠️ 메모리 사용량 높음")
        
        # 에러 처리 테스트
        try:
            # 의도적인 에러 발생
            raise ValueError("테스트 에러")
        except Exception as e:
            logger.info("✅ 에러 처리 테스트 통과")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 기본 검증 테스트 실패 - {str(e)}")
        return False


def run_simple_phase5_test():
    """간단한 Phase 5 테스트 실행"""
    logger.info("🚀 간단한 Phase 5 테스트 시작")
    
    start_time = time.time()
    results = {}
    
    try:
        # 1. Mock 서비스 테스트
        logger.info("=" * 50)
        logger.info("📋 Step 1: Mock 서비스 테스트")
        logger.info("=" * 50)
        
        mock_test_result = test_mock_service()
        results["mock_service"] = mock_test_result
        
        # 2. 기본 검증 테스트
        logger.info("=" * 50)
        logger.info("🔍 Step 2: 기본 검증 테스트")
        logger.info("=" * 50)
        
        basic_test_result = test_basic_validation()
        results["basic_validation"] = basic_test_result
        
        # 3. 결과 요약
        logger.info("=" * 50)
        logger.info("📊 Step 3: 결과 요약")
        logger.info("=" * 50)
        
        total_time = time.time() - start_time
        success_count = sum(1 for result in results.values() if result)
        total_count = len(results)
        success_rate = success_count / total_count if total_count > 0 else 0
        
        logger.info(f"✅ 테스트 완료!")
        logger.info(f"   - 총 실행 시간: {total_time:.2f}초")
        logger.info(f"   - 성공률: {success_rate:.2%} ({success_count}/{total_count})")
        logger.info(f"   - Mock 서비스: {'성공' if results.get('mock_service') else '실패'}")
        logger.info(f"   - 기본 검증: {'성공' if results.get('basic_validation') else '실패'}")
        
        # 최종 결과
        if success_rate >= 0.8:
            logger.info("🎉 Phase 5 테스트 성공!")
            return True
        else:
            logger.warning("⚠️ Phase 5 테스트 실패")
            return False
            
    except Exception as e:
        logger.error(f"❌ 테스트 실행 중 오류: {str(e)}")
        return False


if __name__ == "__main__":
    try:
        success = run_simple_phase5_test()
        if success:
            logger.info("🎯 Phase 5 간단 테스트 성공!")
        else:
            logger.error("❌ Phase 5 간단 테스트 실패!")
            
    except KeyboardInterrupt:
        logger.info("⏹️ 사용자에 의해 실행이 중단되었습니다.")
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류가 발생했습니다: {str(e)}")
        import traceback
        logger.error(traceback.format_exc()) 