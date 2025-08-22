"""
Phase 5 리팩토링 실행 테스트 스크립트
전체 시스템 최종 검증, 성능 최적화 검증, 안정성 테스트를 실행합니다.
"""

import sys
import os
import time
import logging
from datetime import datetime
from typing import Dict, Any

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.core.final_system_validation import FinalSystemValidation
from services.core.performance_validation import PerformanceValidation
from services.core.stability_validation import StabilityValidation

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/phase5_execution.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def run_phase5_execution():
    """Phase 5 리팩토링 실행"""
    logger.info("🚀 Phase 5 리팩토링 실행 시작")
    
    start_time = time.time()
    results = {}
    
    try:
        # Step 1: 전체 시스템 최종 검증
        logger.info("=" * 60)
        logger.info("📋 Step 1: 전체 시스템 최종 검증")
        logger.info("=" * 60)
        
        final_validation = FinalSystemValidation()
        validation_results = final_validation.run_comprehensive_validation()
        results["final_validation"] = validation_results
        
        # 검증 결과 요약
        validation_summary = final_validation.get_validation_summary()
        logger.info(f"✅ 전체 시스템 검증 완료")
        logger.info(f"   - 통합 성공률: {validation_summary.get('integration_success_rate', 0):.2%}")
        logger.info(f"   - 프로덕션 준비도: {validation_summary.get('production_ready', False)}")
        logger.info(f"   - 평균 처리 시간: {validation_summary.get('average_processing_time', 0):.2f}초")
        
        # Step 2: 성능 최적화 검증
        logger.info("=" * 60)
        logger.info("⚡ Step 2: 성능 최적화 검증")
        logger.info("=" * 60)
        
        performance_validation = PerformanceValidation()
        
        # 캐시 최적화 검증
        logger.info("🔍 캐시 최적화 검증 실행 중...")
        cache_results = performance_validation.validate_cache_optimization()
        results["cache_optimization"] = cache_results
        
        # 배치 처리 검증
        logger.info("🔍 배치 처리 검증 실행 중...")
        batch_results = performance_validation.validate_batch_processing()
        results["batch_processing"] = batch_results
        
        # 메모리 최적화 검증
        logger.info("🔍 메모리 최적화 검증 실행 중...")
        memory_results = performance_validation.validate_memory_optimization()
        results["memory_optimization"] = memory_results
        
        # 전체 성능 검증
        logger.info("🔍 전체 성능 검증 실행 중...")
        overall_results = performance_validation.validate_overall_performance()
        results["overall_performance"] = overall_results
        
        # 성능 검증 결과 요약
        performance_summary = performance_validation.get_performance_summary()
        logger.info(f"✅ 성능 최적화 검증 완료")
        logger.info(f"   - 캐시 최적화 점수: {performance_summary.get('cache_optimization_score', 0):.2f}/100")
        logger.info(f"   - 배치 처리 점수: {performance_summary.get('batch_processing_score', 0):.2f}/100")
        logger.info(f"   - 메모리 최적화 점수: {performance_summary.get('memory_optimization_score', 0):.2f}/100")
        logger.info(f"   - 전체 성능 점수: {performance_summary.get('overall_performance_score', 0):.2f}/100")
        
        # Step 3: 안정성 검증
        logger.info("=" * 60)
        logger.info("🛡️ Step 3: 안정성 검증")
        logger.info("=" * 60)
        
        stability_validation = StabilityValidation()
        stability_results = stability_validation.run_comprehensive_stability_test()
        results["stability_validation"] = stability_results
        
        # 안정성 검증 결과 요약
        stability_summary = stability_validation.get_stability_summary()
        logger.info(f"✅ 안정성 검증 완료")
        logger.info(f"   - 전체 안정성 점수: {stability_summary.get('overall_stability_score', 0):.2f}/100")
        logger.info(f"   - 장시간 운영 성공: {stability_summary.get('long_running_success', False)}")
        logger.info(f"   - 에러 복구 성공: {stability_summary.get('error_recovery_success', False)}")
        logger.info(f"   - 메모리 누수 없음: {stability_summary.get('memory_leak_success', False)}")
        logger.info(f"   - 데이터 무결성 성공: {stability_summary.get('data_integrity_success', False)}")
        
        # Step 4: 최종 결과 통합
        logger.info("=" * 60)
        logger.info("📊 Step 4: 최종 결과 통합")
        logger.info("=" * 60)
        
        total_time = time.time() - start_time
        
        # 전체 점수 계산
        overall_score = calculate_overall_phase5_score(results)
        
        # 최종 결과 요약
        final_summary = {
            "phase5_execution": {
                "overall_score": overall_score,
                "total_execution_time": total_time,
                "timestamp": datetime.now().isoformat(),
                "validation_success": validation_summary.get("overall_success", False),
                "performance_ready": performance_summary.get("overall_performance_score", 0) >= 70,
                "stability_ready": stability_summary.get("overall_stability_score", 0) >= 70,
                "production_ready": (
                    validation_summary.get("production_ready", False) and
                    performance_summary.get("overall_performance_score", 0) >= 70 and
                    stability_summary.get("overall_stability_score", 0) >= 70
                )
            },
            "detailed_results": results
        }
        
        # 최종 결과 출력
        logger.info("🎉 Phase 5 리팩토링 실행 완료!")
        logger.info(f"   - 전체 점수: {overall_score:.2f}/100")
        logger.info(f"   - 총 실행 시간: {total_time/60:.2f}분")
        logger.info(f"   - 프로덕션 준비도: {final_summary['phase5_execution']['production_ready']}")
        
        # 결과 저장
        save_phase5_results(final_summary)
        
        return final_summary
        
    except Exception as e:
        logger.error(f"❌ Phase 5 리팩토링 실행 실패 - {str(e)}")
        return {"error": str(e), "success": False}


def calculate_overall_phase5_score(results: Dict[str, Any]) -> float:
    """Phase 5 전체 점수 계산"""
    score = 0.0
    max_score = 100.0
    
    # 검증 점수 (40점)
    validation_results = results.get("final_validation", {})
    validation_summary = validation_results.get("integration", {})
    validation_score = validation_summary.get("success_rate", 0) * 40
    score += validation_score
    
    # 성능 점수 (35점)
    performance_results = results.get("overall_performance", {})
    performance_score = performance_results.get("overall_score", 0) * 0.35
    score += performance_score
    
    # 안정성 점수 (25점)
    stability_results = results.get("stability_validation", {})
    stability_score = stability_results.get("overall_score", 0) * 0.25
    score += stability_score
    
    return min(score, max_score)


def save_phase5_results(results: Dict[str, Any]):
    """Phase 5 결과 저장"""
    try:
        import json
        from datetime import datetime
        
        # 결과 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"z_archives/phase5_execution_results_{timestamp}.json"
        
        # 결과 저장
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"📁 Phase 5 결과가 저장되었습니다: {filename}")
        
    except Exception as e:
        logger.error(f"❌ 결과 저장 실패 - {str(e)}")


def print_detailed_results(results: Dict[str, Any]):
    """상세 결과 출력"""
    logger.info("=" * 80)
    logger.info("📊 Phase 5 상세 결과")
    logger.info("=" * 80)
    
    # 검증 결과
    validation = results.get("detailed_results", {}).get("final_validation", {})
    if validation:
        logger.info("🔍 검증 결과:")
        logger.info(f"   - 통합 성공률: {validation.get('integration', {}).get('success_rate', 0):.2%}")
        logger.info(f"   - 프로덕션 준비도: {validation.get('production_readiness', {}).get('production_ready', False)}")
    
    # 성능 결과
    performance = results.get("detailed_results", {}).get("overall_performance", {})
    if performance:
        logger.info("⚡ 성능 결과:")
        logger.info(f"   - 전체 성능 점수: {performance.get('overall_score', 0):.2f}/100")
        logger.info(f"   - 시스템 성능: {performance.get('system_performance', {}).get('success_rate', 0):.2%}")
        logger.info(f"   - 사용자 경험 점수: {performance.get('user_experience', {}).get('ux_score', 0)}")
    
    # 안정성 결과
    stability = results.get("detailed_results", {}).get("stability_validation", {})
    if stability:
        logger.info("🛡️ 안정성 결과:")
        logger.info(f"   - 전체 안정성 점수: {stability.get('overall_score', 0):.2f}/100")
        logger.info(f"   - 장시간 운영: {stability.get('long_running', {}).get('success', False)}")
        logger.info(f"   - 에러 복구: {stability.get('error_recovery', {}).get('success', False)}")
        logger.info(f"   - 메모리 누수: {stability.get('memory_leak', {}).get('success', False)}")
        logger.info(f"   - 데이터 무결성: {stability.get('data_integrity', {}).get('success', False)}")


if __name__ == "__main__":
    try:
        # Phase 5 실행
        results = run_phase5_execution()
        
        if results and not results.get("error"):
            # 상세 결과 출력
            print_detailed_results(results)
            
            # 최종 상태 출력
            execution_info = results.get("phase5_execution", {})
            logger.info("=" * 80)
            logger.info("🎯 Phase 5 최종 상태")
            logger.info("=" * 80)
            logger.info(f"✅ 전체 점수: {execution_info.get('overall_score', 0):.2f}/100")
            logger.info(f"✅ 검증 성공: {execution_info.get('validation_success', False)}")
            logger.info(f"✅ 성능 준비: {execution_info.get('performance_ready', False)}")
            logger.info(f"✅ 안정성 준비: {execution_info.get('stability_ready', False)}")
            logger.info(f"🚀 프로덕션 준비: {execution_info.get('production_ready', False)}")
            
            if execution_info.get('production_ready', False):
                logger.info("🎉 Phase 5 리팩토링이 성공적으로 완료되었습니다!")
                logger.info("🚀 시스템이 프로덕션 배포 준비가 완료되었습니다.")
            else:
                logger.warning("⚠️ 일부 검증이 실패했습니다. 추가 검토가 필요합니다.")
        else:
            logger.error("❌ Phase 5 실행 중 오류가 발생했습니다.")
            
    except KeyboardInterrupt:
        logger.info("⏹️ 사용자에 의해 실행이 중단되었습니다.")
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류가 발생했습니다: {str(e)}")
        import traceback
        logger.error(traceback.format_exc()) 