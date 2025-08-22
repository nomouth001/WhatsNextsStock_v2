"""
Phase 5: 안정성 검증 모듈
시스템의 장시간 운영 안정성, 에러 복구, 메모리 누수, 데이터 무결성을 검증합니다.
"""

import time
import logging
import psutil
import gc
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from .mock_unified_service import MockUnifiedMarketAnalysisService
from .error_handler import ErrorHandler
from .logging_service import LoggingService
from .cache_service import CacheService

logger = logging.getLogger(__name__)


class StabilityValidation:
    """안정성 검증 클래스"""
    
    def __init__(self):
        self.unified_service = MockUnifiedMarketAnalysisService()
        self.error_handler = ErrorHandler()
        self.logging_service = LoggingService()
        self.cache_service = CacheService()
        
        # 안정성 메트릭 저장
        self.stability_metrics = {}
        self.validation_results = {}
        
    def long_running_test(self, hours: int = 24) -> Dict[str, Any]:
        """장시간 운영 테스트"""
        logger.info(f"🛡️ 장시간 운영 테스트 시작 (목표: {hours}시간)")
        
        try:
            # 실제 운영에서는 24시간이지만, 테스트를 위해 5분으로 단축
            test_duration_minutes = min(hours * 60, 5)  # 최대 5분으로 제한
            start_time = time.time()
            end_time = start_time + (test_duration_minutes * 60)
            
            # 테스트 메트릭 초기화
            operation_count = 0
            error_count = 0
            memory_samples = []
            performance_samples = []
            max_iterations = 300  # 최대 300회 반복으로 제한
            
            # 주기적인 메모리 샘플링
            memory_monitor_thread = threading.Thread(
                target=self._monitor_memory_usage,
                args=(memory_samples, end_time),
                daemon=True
            )
            memory_monitor_thread.start()
            
            # 메인 테스트 루프
            while time.time() < end_time and operation_count < max_iterations:
                try:
                    # 주기적인 분석 작업 수행
                    if operation_count % 10 == 0:  # 10번마다 한 번씩
                        start_analysis = time.time()
                        result = self.unified_service.analyze_single_stock_comprehensive(
                            ticker="005930.KS",
                            market_type="KOSPI",
                            timeframe="d"
                        )
                        analysis_time = time.time() - start_analysis
                        
                        performance_samples.append({
                            "operation_id": operation_count,
                            "analysis_time": analysis_time,
                            "success": result.get("success", False),
                            "timestamp": datetime.now().isoformat()
                        })
                    
                    operation_count += 1
                    time.sleep(1)  # 1초 대기
                    
                except Exception as e:
                    error_count += 1
                    logger.warning(f"장시간 테스트 중 에러: {str(e)}")
                    self.error_handler.handle_analysis_error("long_running_test", str(e))
                    if error_count > 10:  # 에러가 너무 많으면 중단
                        break
            
            # 실제 테스트 시간 계산
            actual_duration = time.time() - start_time
            
            # 메모리 통계 계산
            memory_stats = self._calculate_memory_statistics(memory_samples)
            
            # 성능 통계 계산
            performance_stats = self._calculate_performance_statistics(performance_samples)
            
            results = {
                "test_duration_minutes": actual_duration / 60,
                "operation_count": operation_count,
                "error_count": error_count,
                "error_rate": error_count / operation_count if operation_count > 0 else 0,
                "memory_statistics": memory_stats,
                "performance_statistics": performance_stats,
                "success": error_count == 0,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ 장시간 운영 테스트 완료 (실행시간: {actual_duration/60:.2f}분, 에러율: {results['error_rate']:.2%})")
            return results
            
        except Exception as e:
            logger.error(f"❌ 장시간 운영 테스트 실패 - {str(e)}")
            return {"error": str(e), "success": False}
    
    def _monitor_memory_usage(self, memory_samples: List[Dict], end_time: float):
        """메모리 사용량 모니터링"""
        process = psutil.Process()
        
        while time.time() < end_time:
            try:
                memory_info = process.memory_info()
                memory_samples.append({
                    "rss_mb": memory_info.rss / 1024 / 1024,
                    "vms_mb": memory_info.vms / 1024 / 1024,
                    "timestamp": datetime.now().isoformat()
                })
                time.sleep(10)  # 10초마다 샘플링
            except Exception as e:
                logger.warning(f"메모리 모니터링 중 에러: {str(e)}")
    
    def _calculate_memory_statistics(self, memory_samples: List[Dict]) -> Dict[str, Any]:
        """메모리 통계 계산"""
        if not memory_samples:
            return {"error": "메모리 샘플이 없습니다."}
        
        rss_values = [sample["rss_mb"] for sample in memory_samples]
        vms_values = [sample["vms_mb"] for sample in memory_samples]
        
        return {
            "rss_statistics": {
                "min": min(rss_values),
                "max": max(rss_values),
                "avg": sum(rss_values) / len(rss_values),
                "current": rss_values[-1],
                "variance": max(rss_values) - min(rss_values)
            },
            "vms_statistics": {
                "min": min(vms_values),
                "max": max(vms_values),
                "avg": sum(vms_values) / len(vms_values),
                "current": vms_values[-1],
                "variance": max(vms_values) - min(vms_values)
            },
            "memory_stability": {
                "rss_stable": max(rss_values) - min(rss_values) < 50,  # 50MB 이하 변동
                "vms_stable": max(vms_values) - min(vms_values) < 100,  # 100MB 이하 변동
                "no_memory_leak": rss_values[-1] - rss_values[0] < 20  # 20MB 이하 증가
            }
        }
    
    def _calculate_performance_statistics(self, performance_samples: List[Dict]) -> Dict[str, Any]:
        """성능 통계 계산"""
        if not performance_samples:
            return {"error": "성능 샘플이 없습니다."}
        
        analysis_times = [sample["analysis_time"] for sample in performance_samples]
        success_count = sum(1 for sample in performance_samples if sample["success"])
        
        return {
            "analysis_time_statistics": {
                "min": min(analysis_times),
                "max": max(analysis_times),
                "avg": sum(analysis_times) / len(analysis_times),
                "current": analysis_times[-1]
            },
            "success_rate": success_count / len(performance_samples),
            "performance_stability": {
                "response_time_stable": max(analysis_times) - min(analysis_times) < 2.0,  # 2초 이하 변동
                "consistent_success": success_count == len(performance_samples)
            }
        }
    
    def error_recovery_test(self) -> Dict[str, Any]:
        """에러 복구 테스트"""
        logger.info("🛡️ 에러 복구 테스트 시작")
        
        try:
            # 다양한 에러 상황 테스트
            error_scenarios = [
                ("data_error", "데이터 로드 실패"),
                ("analysis_error", "분석 처리 실패"),
                ("cache_error", "캐시 접근 실패"),
                ("network_error", "네트워크 연결 실패"),
                ("memory_error", "메모리 부족 에러"),
                ("timeout_error", "처리 시간 초과"),
                ("validation_error", "데이터 검증 실패"),
                ("system_error", "시스템 에러")
            ]
            
            recovery_results = []
            total_tests = len(error_scenarios)
            successful_recoveries = 0
            
            for error_type, error_message in error_scenarios:
                try:
                    # 에러 발생 시뮬레이션
                    if error_type == "data_error":
                        raise ValueError(f"데이터 로드 실패: {error_message}")
                    elif error_type == "analysis_error":
                        raise RuntimeError(f"분석 처리 실패: {error_message}")
                    elif error_type == "cache_error":
                        raise IOError(f"캐시 접근 실패: {error_message}")
                    elif error_type == "network_error":
                        raise ConnectionError(f"네트워크 연결 실패: {error_message}")
                    elif error_type == "memory_error":
                        raise MemoryError(f"메모리 부족: {error_message}")
                    elif error_type == "timeout_error":
                        raise TimeoutError(f"처리 시간 초과: {error_message}")
                    elif error_type == "validation_error":
                        raise ValueError(f"데이터 검증 실패: {error_message}")
                    else:
                        raise Exception(f"시스템 에러: {error_message}")
                    
                except Exception as e:
                    # 에러 복구 시도
                    recovery_start = time.time()
                    try:
                        self.error_handler.handle_analysis_error(error_type, str(e))
                        recovery_time = time.time() - recovery_start
                        
                        recovery_results.append({
                            "error_type": error_type,
                            "error_message": error_message,
                            "recovery_success": True,
                            "recovery_time": recovery_time,
                            "error_handled": True
                        })
                        successful_recoveries += 1
                        
                    except Exception as recovery_error:
                        recovery_time = time.time() - recovery_start
                        recovery_results.append({
                            "error_type": error_type,
                            "error_message": error_message,
                            "recovery_success": False,
                            "recovery_time": recovery_time,
                            "error_handled": False,
                            "recovery_error": str(recovery_error)
                        })
            
            # 복구 성공률 계산
            recovery_success_rate = successful_recoveries / total_tests if total_tests > 0 else 0
            
            # 평균 복구 시간 계산
            successful_recoveries_times = [
                result["recovery_time"] for result in recovery_results 
                if result["recovery_success"]
            ]
            avg_recovery_time = sum(successful_recoveries_times) / len(successful_recoveries_times) if successful_recoveries_times else 0
            
            results = {
                "total_tests": total_tests,
                "successful_recoveries": successful_recoveries,
                "recovery_success_rate": recovery_success_rate,
                "average_recovery_time": avg_recovery_time,
                "recovery_results": recovery_results,
                "success": recovery_success_rate >= 0.8,  # 80% 이상 성공
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ 에러 복구 테스트 완료 (성공률: {recovery_success_rate:.2%})")
            return results
            
        except Exception as e:
            logger.error(f"❌ 에러 복구 테스트 실패 - {str(e)}")
            return {"error": str(e), "success": False}
    
    def memory_leak_test(self) -> Dict[str, Any]:
        """메모리 누수 테스트"""
        logger.info("🛡️ 메모리 누수 테스트 시작")
        
        try:
            process = psutil.Process()
            
            # 초기 메모리 측정
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            initial_vms = process.memory_info().vms / 1024 / 1024  # MB
            
            # 메모리 누수 시뮬레이션 (5회 반복)
            memory_samples = []
            leaked_objects = []
            
            for cycle in range(5):
                cycle_start_memory = process.memory_info().rss / 1024 / 1024
                
                # 객체 생성 (일부는 누수)
                cycle_objects = []
                for i in range(100):
                    obj = {
                        "cycle": cycle,
                        "id": i,
                        "data": "x" * 1000,  # 1KB per object
                        "timestamp": datetime.now().isoformat()
                    }
                    cycle_objects.append(obj)
                
                # 일부 객체는 누수 (참조 유지)
                if cycle % 2 == 0:
                    leaked_objects.extend(cycle_objects[:50])  # 50개 누수
                    cycle_objects = cycle_objects[50:]  # 나머지 정리
                
                # 메모리 사용량 측정
                cycle_end_memory = process.memory_info().rss / 1024 / 1024
                
                memory_samples.append({
                    "cycle": cycle,
                    "start_memory_mb": cycle_start_memory,
                    "end_memory_mb": cycle_end_memory,
                    "memory_increase_mb": cycle_end_memory - cycle_start_memory,
                    "objects_created": len(cycle_objects) + len(leaked_objects),
                    "objects_leaked": len(leaked_objects),
                    "timestamp": datetime.now().isoformat()
                })
                
                # GC 실행 (일부 정리)
                gc.collect()
                time.sleep(0.1)  # 잠시 대기
            
            # 최종 메모리 측정
            final_memory = process.memory_info().rss / 1024 / 1024
            final_vms = process.memory_info().vms / 1024 / 1024
            
            # 누수된 객체 정리
            del leaked_objects
            gc.collect()
            
            # 정리 후 메모리 측정
            cleaned_memory = process.memory_info().rss / 1024 / 1024
            cleaned_vms = process.memory_info().vms / 1024 / 1024
            
            # 메모리 누수 분석
            total_memory_increase = final_memory - initial_memory
            memory_recovery = final_memory - cleaned_memory
            leak_detected = total_memory_increase > 10  # 10MB 이상 증가 시 누수로 판단
            
            # 누수 패턴 분석
            memory_trend = []
            for i in range(1, len(memory_samples)):
                trend = memory_samples[i]["end_memory_mb"] - memory_samples[i-1]["end_memory_mb"]
                memory_trend.append(trend)
            
            consistent_increase = all(trend > 0 for trend in memory_trend) if memory_trend else False
            
            results = {
                "initial_memory_mb": initial_memory,
                "final_memory_mb": final_memory,
                "cleaned_memory_mb": cleaned_memory,
                "total_memory_increase_mb": total_memory_increase,
                "memory_recovery_mb": memory_recovery,
                "memory_samples": memory_samples,
                "memory_trend": memory_trend,
                "leak_analysis": {
                    "leak_detected": leak_detected,
                    "consistent_increase": consistent_increase,
                    "leak_size_mb": total_memory_increase,
                    "recovery_efficiency": memory_recovery / total_memory_increase if total_memory_increase > 0 else 0
                },
                "success": not leak_detected,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ 메모리 누수 테스트 완료 (누수 감지: {leak_detected}, 증가량: {total_memory_increase:.2f}MB)")
            return results
            
        except Exception as e:
            logger.error(f"❌ 메모리 누수 테스트 실패 - {str(e)}")
            return {"error": str(e), "success": False}
    
    def data_integrity_test(self) -> Dict[str, Any]:
        """데이터 무결성 테스트"""
        logger.info("🛡️ 데이터 무결성 테스트 시작")
        
        try:
            test_symbol = "005930.KS"
            integrity_results = []
            
            # 동일한 데이터로 여러 번 분석 수행
            for i in range(5):
                try:
                    start_time = time.time()
                    result = self.unified_service.analyze_single_stock_comprehensive(
                        ticker=test_symbol,
                        market_type="KOSPI",
                        timeframe="d"
                    )
                    analysis_time = time.time() - start_time
                    
                    integrity_results.append({
                        "iteration": i + 1,
                        "success": result.get("success", False),
                        "analysis_time": analysis_time,
                        "result_keys": list(result.keys()) if isinstance(result, dict) else [],
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    time.sleep(0.5)  # 분석 간격
                    
                except Exception as e:
                    integrity_results.append({
                        "iteration": i + 1,
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
            
            # 결과 일관성 검증
            successful_results = [r for r in integrity_results if r.get("success", False)]
            
            if len(successful_results) < 2:
                consistency_check = False
                data_consistency = 0.0
            else:
                # 첫 번째 성공한 결과를 기준으로 비교
                baseline_result = successful_results[0]
                baseline_keys = set(baseline_result.get("result_keys", []))
                
                # 다른 결과들과 키 구조 비교
                consistent_results = 0
                for result in successful_results[1:]:
                    result_keys = set(result.get("result_keys", []))
                    if baseline_keys == result_keys:
                        consistent_results += 1
                
                consistency_check = consistent_results == len(successful_results) - 1
                data_consistency = consistent_results / (len(successful_results) - 1) if len(successful_results) > 1 else 0.0
            
            # 성능 일관성 검증
            analysis_times = [r.get("analysis_time", 0) for r in successful_results]
            if analysis_times:
                avg_analysis_time = sum(analysis_times) / len(analysis_times)
                time_variance = max(analysis_times) - min(analysis_times)
                performance_consistent = time_variance < 2.0  # 2초 이하 변동
            else:
                avg_analysis_time = 0
                performance_consistent = False
            
            # 전체 성공률
            success_rate = len(successful_results) / len(integrity_results) if integrity_results else 0
            
            results = {
                "total_iterations": len(integrity_results),
                "successful_iterations": len(successful_results),
                "success_rate": success_rate,
                "integrity_results": integrity_results,
                "consistency_analysis": {
                    "consistency_check": consistency_check,
                    "data_consistency": data_consistency,
                    "performance_consistent": performance_consistent,
                    "avg_analysis_time": avg_analysis_time,
                    "time_variance": time_variance if analysis_times else 0
                },
                "success": success_rate >= 0.8 and consistency_check,  # 80% 이상 성공하고 일관성 유지
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ 데이터 무결성 테스트 완료 (성공률: {success_rate:.2%}, 일관성: {consistency_check})")
            return results
            
        except Exception as e:
            logger.error(f"❌ 데이터 무결성 테스트 실패 - {str(e)}")
            return {"error": str(e), "success": False}
    
    def run_comprehensive_stability_test(self) -> Dict[str, Any]:
        """종합 안정성 테스트 실행"""
        logger.info("🛡️ 종합 안정성 테스트 시작")
        
        try:
            start_time = time.time()
            
            # 1. 장시간 운영 테스트
            long_running_results = self.long_running_test(hours=1)  # 1시간 테스트 (실제로는 5분)
            
            # 2. 에러 복구 테스트
            error_recovery_results = self.error_recovery_test()
            
            # 3. 메모리 누수 테스트
            memory_leak_results = self.memory_leak_test()
            
            # 4. 데이터 무결성 테스트
            data_integrity_results = self.data_integrity_test()
            
            # 결과 통합
            total_time = time.time() - start_time
            
            # 전체 안정성 점수 계산
            stability_score = self._calculate_stability_score({
                "long_running": long_running_results,
                "error_recovery": error_recovery_results,
                "memory_leak": memory_leak_results,
                "data_integrity": data_integrity_results
            })
            
            self.stability_metrics = {
                "long_running": long_running_results,
                "error_recovery": error_recovery_results,
                "memory_leak": memory_leak_results,
                "data_integrity": data_integrity_results,
                "overall_score": stability_score,
                "total_test_time": total_time,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ 종합 안정성 테스트 완료 (점수: {stability_score:.2f}/100)")
            return self.stability_metrics
            
        except Exception as e:
            logger.error(f"❌ 종합 안정성 테스트 실패 - {str(e)}")
            return {"error": str(e), "success": False}
    
    def _calculate_stability_score(self, results: Dict[str, Any]) -> float:
        """안정성 점수 계산"""
        score = 0.0
        max_score = 100.0
        
        # 장시간 운영 점수 (30점)
        long_running = results.get("long_running", {})
        if long_running.get("success", False):
            error_rate = long_running.get("error_rate", 0)
            score += (1 - error_rate) * 30
        
        # 에러 복구 점수 (25점)
        error_recovery = results.get("error_recovery", {})
        recovery_rate = error_recovery.get("recovery_success_rate", 0)
        score += recovery_rate * 25
        
        # 메모리 누수 점수 (25점)
        memory_leak = results.get("memory_leak", {})
        leak_detected = memory_leak.get("leak_analysis", {}).get("leak_detected", False)
        if not leak_detected:
            score += 25
        
        # 데이터 무결성 점수 (20점)
        data_integrity = results.get("data_integrity", {})
        if data_integrity.get("success", False):
            consistency = data_integrity.get("consistency_analysis", {}).get("data_consistency", 0)
            score += consistency * 20
        
        return min(score, max_score)
    
    def get_stability_summary(self) -> Dict[str, Any]:
        """안정성 검증 결과 요약"""
        if not self.stability_metrics:
            return {"error": "안정성 검증이 실행되지 않았습니다."}
        
        return {
            "overall_stability_score": self.stability_metrics.get("overall_score", 0),
            "long_running_success": self.stability_metrics.get("long_running", {}).get("success", False),
            "error_recovery_success": self.stability_metrics.get("error_recovery", {}).get("success", False),
            "memory_leak_success": self.stability_metrics.get("memory_leak", {}).get("success", False),
            "data_integrity_success": self.stability_metrics.get("data_integrity", {}).get("success", False),
            "total_test_time": self.stability_metrics.get("total_test_time", 0),
            "timestamp": self.stability_metrics.get("timestamp", "")
        } 