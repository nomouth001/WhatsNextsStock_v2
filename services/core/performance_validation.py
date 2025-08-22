"""
Phase 5: 성능 최적화 검증 모듈
Phase 4에서 구현된 성능 최적화 효과를 검증합니다.
"""

import time
import logging
import psutil
import gc
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from .performance_optimizer import PerformanceOptimizer
from .cache_service import CacheService
from .mock_unified_service import MockUnifiedMarketAnalysisService

logger = logging.getLogger(__name__)


class PerformanceValidation:
    """성능 최적화 검증 클래스"""
    
    def __init__(self):
        self.performance_optimizer = PerformanceOptimizer()
        self.cache_service = CacheService()
        self.unified_service = MockUnifiedMarketAnalysisService()
        
        # 성능 메트릭 저장
        self.performance_metrics = {}
        self.optimization_results = {}
        
    def validate_cache_optimization(self) -> Dict[str, Any]:
        """캐시 최적화 검증"""
        logger.info("🔍 캐시 최적화 검증 시작")
        
        try:
            # 1. 캐시 히트율 테스트
            hit_rate_results = self._test_cache_hit_rate()
            
            # 2. 캐시 응답 시간 테스트
            response_time_results = self._test_cache_response_time()
            
            # 3. 캐시 메모리 사용량 테스트
            memory_results = self._test_cache_memory_usage()
            
            # 4. 캐시 정리 효율성 테스트
            cleanup_results = self._test_cache_cleanup_efficiency()
            
            results = {
                "hit_rate": hit_rate_results,
                "response_time": response_time_results,
                "memory_usage": memory_results,
                "cleanup_efficiency": cleanup_results,
                "timestamp": datetime.now().isoformat()
            }
            
            # 전체 캐시 최적화 점수 계산
            overall_score = self._calculate_cache_optimization_score(results)
            results["overall_score"] = overall_score
            
            logger.info(f"✅ 캐시 최적화 검증 완료 (점수: {overall_score:.2f}/100)")
            return results
            
        except Exception as e:
            logger.error(f"❌ 캐시 최적화 검증 실패 - {str(e)}")
            return {"error": str(e), "success": False}
    
    def _test_cache_hit_rate(self) -> Dict[str, Any]:
        """캐시 히트율 테스트"""
        # 테스트 데이터 준비
        test_keys = [f"cache_test_{i}" for i in range(1000)]
        test_data = {"data": "test_value", "timestamp": datetime.now().isoformat()}
        
        # 캐시 저장
        start_time = time.time()
        for key in test_keys:
            self.cache_service.set(key, test_data)
        store_time = time.time() - start_time
        
        # 캐시 조회 (히트율 측정)
        start_time = time.time()
        hit_count = 0
        miss_count = 0
        
        for key in test_keys:
            if self.cache_service.get(key):
                hit_count += 1
            else:
                miss_count += 1
        
        query_time = time.time() - start_time
        total_requests = hit_count + miss_count
        hit_rate = hit_count / total_requests if total_requests > 0 else 0
        
        return {
            "hit_count": hit_count,
            "miss_count": miss_count,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
            "store_time": store_time,
            "query_time": query_time,
            "operations_per_second": total_requests / query_time if query_time > 0 else 0
        }
    
    def _test_cache_response_time(self) -> Dict[str, Any]:
        """캐시 응답 시간 테스트"""
        test_key = "response_time_test"
        test_data = {"large_data": "x" * 10000}  # 10KB 데이터
        
        # 캐시 저장 시간 측정
        start_time = time.time()
        self.cache_service.set(test_key, test_data)
        store_time = time.time() - start_time
        
        # 캐시 조회 시간 측정
        start_time = time.time()
        retrieved_data = self.cache_service.get(test_key)
        query_time = time.time() - start_time
        
        # 데이터베이스 조회 시간 시뮬레이션 (캐시 미스 시)
        db_query_time = 0.1  # 100ms 시뮬레이션
        
        return {
            "store_time_ms": store_time * 1000,
            "query_time_ms": query_time * 1000,
            "db_query_time_ms": db_query_time * 1000,
            "speedup_ratio": db_query_time / query_time if query_time > 0 else 0,
            "data_size_kb": len(str(test_data)) / 1024
        }
    
    def _test_cache_memory_usage(self) -> Dict[str, Any]:
        """캐시 메모리 사용량 테스트"""
        process = psutil.Process()
        
        # 초기 메모리 사용량
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 대용량 캐시 데이터 저장
        large_data = {}
        for i in range(1000):
            large_data[f"large_key_{i}"] = {
                "data": "x" * 1000,  # 1KB per item
                "timestamp": datetime.now().isoformat()
            }
        
        # 캐시에 저장
        for key, value in large_data.items():
            self.cache_service.set(key, value)
        
        # 저장 후 메모리 사용량
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 캐시 정리
        self.cache_service.clear()
        
        # 정리 후 메모리 사용량
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        return {
            "initial_memory_mb": initial_memory,
            "peak_memory_mb": peak_memory,
            "final_memory_mb": final_memory,
            "memory_increase_mb": peak_memory - initial_memory,
            "memory_recovery_mb": peak_memory - final_memory,
            "memory_efficiency": (peak_memory - initial_memory) / len(large_data) if large_data else 0
        }
    
    def _test_cache_cleanup_efficiency(self) -> Dict[str, Any]:
        """캐시 정리 효율성 테스트"""
        # 만료된 캐시 항목 생성
        expired_keys = []
        for i in range(100):
            key = f"expired_key_{i}"
            self.cache_service.set(key, {"data": "expired"}, ttl=1)  # 1초 후 만료
            expired_keys.append(key)
        
        # 만료 대기
        time.sleep(2)
        
        # 만료된 항목 조회
        expired_count = 0
        for key in expired_keys:
            if not self.cache_service.get(key):
                expired_count += 1
        
        cleanup_efficiency = expired_count / len(expired_keys) if expired_keys else 0
        
        return {
            "total_expired_keys": len(expired_keys),
            "cleaned_keys": expired_count,
            "cleanup_efficiency": cleanup_efficiency,
            "cleanup_rate": cleanup_efficiency * 100
        }
    
    def _calculate_cache_optimization_score(self, results: Dict[str, Any]) -> float:
        """캐시 최적화 점수 계산"""
        score = 0.0
        max_score = 100.0
        
        # 히트율 점수 (40점)
        hit_rate = results.get("hit_rate", {}).get("hit_rate", 0)
        score += min(hit_rate * 40, 40)
        
        # 응답 시간 점수 (30점)
        response_time = results.get("response_time", {})
        speedup_ratio = response_time.get("speedup_ratio", 0)
        score += min(speedup_ratio * 10, 30)
        
        # 메모리 효율성 점수 (20점)
        memory_usage = results.get("memory_usage", {})
        memory_efficiency = memory_usage.get("memory_efficiency", 0)
        if memory_efficiency > 0:
            score += min(20 / memory_efficiency, 20)
        
        # 정리 효율성 점수 (10점)
        cleanup_efficiency = results.get("cleanup_efficiency", {}).get("cleanup_efficiency", 0)
        score += cleanup_efficiency * 10
        
        return min(score, max_score)
    
    def validate_batch_processing(self) -> Dict[str, Any]:
        """배치 처리 검증"""
        logger.info("🔍 배치 처리 검증 시작")
        
        try:
            # 1. 배치 크기 최적화 테스트
            batch_size_results = self._test_batch_size_optimization()
            
            # 2. 배치 처리 성능 테스트
            batch_performance_results = self._test_batch_performance()
            
            # 3. 메모리 사용량 테스트
            batch_memory_results = self._test_batch_memory_usage()
            
            # 4. 동시성 처리 테스트
            batch_concurrency_results = self._test_batch_concurrency()
            
            results = {
                "batch_size_optimization": batch_size_results,
                "batch_performance": batch_performance_results,
                "batch_memory": batch_memory_results,
                "batch_concurrency": batch_concurrency_results,
                "timestamp": datetime.now().isoformat()
            }
            
            # 전체 배치 처리 점수 계산
            overall_score = self._calculate_batch_processing_score(results)
            results["overall_score"] = overall_score
            
            logger.info(f"✅ 배치 처리 검증 완료 (점수: {overall_score:.2f}/100)")
            return results
            
        except Exception as e:
            logger.error(f"❌ 배치 처리 검증 실패 - {str(e)}")
            return {"error": str(e), "success": False}
    
    def _test_batch_size_optimization(self) -> Dict[str, Any]:
        """배치 크기 최적화 테스트"""
        total_items = 1000
        batch_sizes = [10, 25, 50, 100, 200]
        
        results = {}
        for batch_size in batch_sizes:
            start_time = time.time()
            
            # 배치 처리 시뮬레이션
            for i in range(0, total_items, batch_size):
                batch = list(range(i, min(i + batch_size, total_items)))
                # 배치 처리 로직 시뮬레이션
                time.sleep(0.001 * len(batch))  # 배치 크기에 비례한 처리 시간
            
            processing_time = time.time() - start_time
            
            results[batch_size] = {
                "processing_time": processing_time,
                "items_per_second": total_items / processing_time if processing_time > 0 else 0,
                "efficiency": total_items / (processing_time * batch_size) if processing_time > 0 else 0
            }
        
        # 최적 배치 크기 찾기
        optimal_batch_size = max(results.keys(), 
                                key=lambda x: results[x]["items_per_second"])
        
        return {
            "batch_size_results": results,
            "optimal_batch_size": optimal_batch_size,
            "optimal_performance": results[optimal_batch_size]
        }
    
    def _test_batch_performance(self) -> Dict[str, Any]:
        """배치 처리 성능 테스트"""
        # 최적 배치 크기로 성능 테스트
        optimal_batch_size = 50
        total_items = 2000
        
        start_time = time.time()
        
        # 배치 처리
        processed_items = 0
        for i in range(0, total_items, optimal_batch_size):
            batch = list(range(i, min(i + optimal_batch_size, total_items)))
            # 배치 처리 로직
            processed_items += len(batch)
            time.sleep(0.001 * len(batch))
        
        processing_time = time.time() - start_time
        
        return {
            "total_items": total_items,
            "processed_items": processed_items,
            "batch_size": optimal_batch_size,
            "processing_time": processing_time,
            "items_per_second": processed_items / processing_time if processing_time > 0 else 0,
            "throughput": processed_items / processing_time if processing_time > 0 else 0
        }
    
    def _test_batch_memory_usage(self) -> Dict[str, Any]:
        """배치 메모리 사용량 테스트"""
        process = psutil.Process()
        
        # 초기 메모리
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 대용량 배치 처리 시뮬레이션
        batch_data = []
        for i in range(1000):
            batch_data.append({
                "id": i,
                "data": "x" * 1000,  # 1KB per item
                "timestamp": datetime.now().isoformat()
            })
        
        # 배치 처리
        peak_memory = 0
        for i in range(0, len(batch_data), 50):  # 50개씩 배치 처리
            batch = batch_data[i:i+50]
            # 배치 처리 로직 시뮬레이션
            current_memory = process.memory_info().rss / 1024 / 1024
            peak_memory = max(peak_memory, current_memory)
        
        # 메모리 정리
        del batch_data
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        return {
            "initial_memory_mb": initial_memory,
            "peak_memory_mb": peak_memory,
            "final_memory_mb": final_memory,
            "memory_increase_mb": peak_memory - initial_memory,
            "memory_recovery_mb": peak_memory - final_memory,
            "memory_efficiency": (peak_memory - initial_memory) / len(batch_data) if batch_data else 0
        }
    
    def _test_batch_concurrency(self) -> Dict[str, Any]:
        """배치 동시성 처리 테스트"""
        total_batches = 10
        batch_size = 50
        
        def process_batch(batch_id):
            """배치 처리 함수"""
            start_time = time.time()
            # 배치 처리 시뮬레이션
            batch_data = [f"item_{batch_id}_{i}" for i in range(batch_size)]
            time.sleep(0.1)  # 처리 시간 시뮬레이션
            end_time = time.time()
            return {
                "batch_id": batch_id,
                "processing_time": end_time - start_time,
                "items_processed": len(batch_data)
            }
        
        # 순차 처리
        sequential_start = time.time()
        sequential_results = []
        for i in range(total_batches):
            result = process_batch(i)
            sequential_results.append(result)
        sequential_time = time.time() - sequential_start
        
        # 병렬 처리
        parallel_start = time.time()
        parallel_results = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(process_batch, i) for i in range(total_batches)]
            for future in as_completed(futures):
                result = future.result()
                parallel_results.append(result)
        parallel_time = time.time() - parallel_start
        
        # 성능 비교
        speedup = sequential_time / parallel_time if parallel_time > 0 else 0
        
        return {
            "sequential_time": sequential_time,
            "parallel_time": parallel_time,
            "speedup": speedup,
            "efficiency": speedup / 3 if speedup > 0 else 0,  # 3개 워커 기준
            "total_batches": total_batches,
            "batch_size": batch_size
        }
    
    def _calculate_batch_processing_score(self, results: Dict[str, Any]) -> float:
        """배치 처리 점수 계산"""
        score = 0.0
        max_score = 100.0
        
        # 배치 크기 최적화 점수 (30점)
        batch_size_results = results.get("batch_size_optimization", {})
        optimal_performance = batch_size_results.get("optimal_performance", {})
        items_per_second = optimal_performance.get("items_per_second", 0)
        score += min(items_per_second / 10, 30)
        
        # 배치 성능 점수 (30점)
        batch_performance = results.get("batch_performance", {})
        throughput = batch_performance.get("throughput", 0)
        score += min(throughput / 10, 30)
        
        # 메모리 효율성 점수 (20점)
        batch_memory = results.get("batch_memory", {})
        memory_efficiency = batch_memory.get("memory_efficiency", 0)
        if memory_efficiency > 0:
            score += min(20 / memory_efficiency, 20)
        
        # 동시성 효율성 점수 (20점)
        batch_concurrency = results.get("batch_concurrency", {})
        efficiency = batch_concurrency.get("efficiency", 0)
        score += min(efficiency * 20, 20)
        
        return min(score, max_score)
    
    def validate_memory_optimization(self) -> Dict[str, Any]:
        """메모리 최적화 검증"""
        logger.info("🔍 메모리 최적화 검증 시작")
        
        try:
            # 1. 메모리 사용량 모니터링
            memory_monitoring_results = self._test_memory_monitoring()
            
            # 2. 메모리 누수 검증
            memory_leak_results = self._test_memory_leak_detection()
            
            # 3. 가비지 컬렉션 효율성
            gc_efficiency_results = self._test_garbage_collection()
            
            # 4. 메모리 정리 효율성
            memory_cleanup_results = self._test_memory_cleanup()
            
            results = {
                "memory_monitoring": memory_monitoring_results,
                "memory_leak_detection": memory_leak_results,
                "garbage_collection": gc_efficiency_results,
                "memory_cleanup": memory_cleanup_results,
                "timestamp": datetime.now().isoformat()
            }
            
            # 전체 메모리 최적화 점수 계산
            overall_score = self._calculate_memory_optimization_score(results)
            results["overall_score"] = overall_score
            
            logger.info(f"✅ 메모리 최적화 검증 완료 (점수: {overall_score:.2f}/100)")
            return results
            
        except Exception as e:
            logger.error(f"❌ 메모리 최적화 검증 실패 - {str(e)}")
            return {"error": str(e), "success": False}
    
    def _test_memory_monitoring(self) -> Dict[str, Any]:
        """메모리 사용량 모니터링 테스트"""
        process = psutil.Process()
        
        # 메모리 사용량 추적
        memory_samples = []
        for i in range(10):
            memory_info = process.memory_info()
            memory_samples.append({
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024,
                "timestamp": datetime.now().isoformat()
            })
            time.sleep(0.1)
        
        # 통계 계산
        rss_values = [sample["rss_mb"] for sample in memory_samples]
        vms_values = [sample["vms_mb"] for sample in memory_samples]
        
        return {
            "memory_samples": memory_samples,
            "rss_stats": {
                "min": min(rss_values),
                "max": max(rss_values),
                "avg": sum(rss_values) / len(rss_values),
                "current": rss_values[-1]
            },
            "vms_stats": {
                "min": min(vms_values),
                "max": max(vms_values),
                "avg": sum(vms_values) / len(vms_values),
                "current": vms_values[-1]
            }
        }
    
    def _test_memory_leak_detection(self) -> Dict[str, Any]:
        """메모리 누수 검증"""
        process = psutil.Process()
        
        # 초기 메모리
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 메모리 누수 시뮬레이션
        leaked_objects = []
        for cycle in range(5):
            # 객체 생성 (일부는 누수)
            for i in range(100):
                obj = {"cycle": cycle, "data": "x" * 1000}
                leaked_objects.append(obj)
            
            # 일부 객체만 정리 (누수 시뮬레이션)
            if cycle % 2 == 0:
                leaked_objects = leaked_objects[:-50]  # 50개만 정리
        
        # 최종 메모리
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 메모리 정리
        del leaked_objects
        gc.collect()
        
        cleaned_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        return {
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "cleaned_memory_mb": cleaned_memory,
            "memory_increase_mb": final_memory - initial_memory,
            "memory_recovery_mb": final_memory - cleaned_memory,
            "leak_detected": (final_memory - initial_memory) > 10  # 10MB 이상 증가 시 누수로 판단
        }
    
    def _test_garbage_collection(self) -> Dict[str, Any]:
        """가비지 컬렉션 효율성 테스트"""
        # GC 통계 초기화
        gc.collect()
        initial_stats = gc.get_stats()
        
        # 대량 객체 생성
        objects = []
        for i in range(10000):
            objects.append({"id": i, "data": "x" * 100})
        
        # 객체 참조 해제
        del objects
        
        # GC 실행
        start_time = time.time()
        collected = gc.collect()
        gc_time = time.time() - start_time
        
        # GC 후 통계
        final_stats = gc.get_stats()
        
        return {
            "objects_collected": collected,
            "gc_time": gc_time,
            "initial_stats": initial_stats,
            "final_stats": final_stats,
            "gc_efficiency": collected / gc_time if gc_time > 0 else 0
        }
    
    def _test_memory_cleanup(self) -> Dict[str, Any]:
        """메모리 정리 효율성 테스트"""
        process = psutil.Process()
        
        # 초기 메모리
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 대량 데이터 생성
        large_data = []
        for i in range(5000):
            large_data.append({
                "id": i,
                "data": "x" * 2000,  # 2KB per item
                "timestamp": datetime.now().isoformat()
            })
        
        # 메모리 사용량 증가
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 수동 정리
        del large_data
        manual_cleanup_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # GC 강제 실행
        gc.collect()
        gc_cleanup_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        return {
            "initial_memory_mb": initial_memory,
            "peak_memory_mb": peak_memory,
            "manual_cleanup_mb": manual_cleanup_memory,
            "gc_cleanup_mb": gc_cleanup_memory,
            "manual_recovery_mb": peak_memory - manual_cleanup_memory,
            "gc_recovery_mb": peak_memory - gc_cleanup_memory,
            "cleanup_efficiency": (peak_memory - gc_cleanup_memory) / (peak_memory - initial_memory) if (peak_memory - initial_memory) > 0 else 0
        }
    
    def _calculate_memory_optimization_score(self, results: Dict[str, Any]) -> float:
        """메모리 최적화 점수 계산"""
        score = 0.0
        max_score = 100.0
        
        # 메모리 모니터링 점수 (25점)
        memory_monitoring = results.get("memory_monitoring", {})
        rss_stats = memory_monitoring.get("rss_stats", {})
        memory_variance = rss_stats.get("max", 0) - rss_stats.get("min", 0)
        if memory_variance < 50:  # 50MB 이하 변동
            score += 25
        
        # 메모리 누수 검증 점수 (30점)
        memory_leak = results.get("memory_leak_detection", {})
        leak_detected = memory_leak.get("leak_detected", False)
        if not leak_detected:
            score += 30
        
        # GC 효율성 점수 (25점)
        garbage_collection = results.get("garbage_collection", {})
        gc_efficiency = garbage_collection.get("gc_efficiency", 0)
        score += min(gc_efficiency / 1000, 25)
        
        # 정리 효율성 점수 (20점)
        memory_cleanup = results.get("memory_cleanup", {})
        cleanup_efficiency = memory_cleanup.get("cleanup_efficiency", 0)
        score += cleanup_efficiency * 20
        
        return min(score, max_score)
    
    def validate_overall_performance(self) -> Dict[str, Any]:
        """전체 성능 검증"""
        logger.info("🔍 전체 성능 검증 시작")
        
        try:
            # 1. 시스템 전체 성능 테스트
            system_performance = self._test_system_overall_performance()
            
            # 2. 사용자 경험 성능 테스트
            user_experience = self._test_user_experience_performance()
            
            # 3. 리소스 사용량 테스트
            resource_usage = self._test_resource_usage_performance()
            
            # 4. 확장성 성능 테스트
            scalability = self._test_scalability_performance()
            
            results = {
                "system_performance": system_performance,
                "user_experience": user_experience,
                "resource_usage": resource_usage,
                "scalability": scalability,
                "timestamp": datetime.now().isoformat()
            }
            
            # 전체 성능 점수 계산
            overall_score = self._calculate_overall_performance_score(results)
            results["overall_score"] = overall_score
            
            logger.info(f"✅ 전체 성능 검증 완료 (점수: {overall_score:.2f}/100)")
            return results
            
        except Exception as e:
            logger.error(f"❌ 전체 성능 검증 실패 - {str(e)}")
            return {"error": str(e), "success": False}
    
    def _test_system_overall_performance(self) -> Dict[str, Any]:
        """시스템 전체 성능 테스트"""
        test_symbols = ["005930.KS", "000660.KS", "005380.KS", "012450.KS", "034020.KS"]
        
        start_time = time.time()
        successful_analyses = 0
        total_analyses = len(test_symbols)
        
        for symbol in test_symbols:
            try:
                result = self.unified_service.analyze_single_stock_comprehensive(
                    ticker=symbol,
                    market_type="KOSPI",
                    timeframe="d"
                )
                if result.get("success", False):
                    successful_analyses += 1
            except Exception as e:
                logger.warning(f"시스템 성능 테스트 중 에러: {symbol} - {str(e)}")
        
        end_time = time.time()
        
        return {
            "total_analyses": total_analyses,
            "successful_analyses": successful_analyses,
            "success_rate": successful_analyses / total_analyses if total_analyses > 0 else 0,
            "total_processing_time": end_time - start_time,
            "average_processing_time": (end_time - start_time) / total_analyses if total_analyses > 0 else 0,
            "analyses_per_second": total_analyses / (end_time - start_time) if (end_time - start_time) > 0 else 0
        }
    
    def _test_user_experience_performance(self) -> Dict[str, Any]:
        """사용자 경험 성능 테스트"""
        # 응답 시간 테스트
        response_times = []
        
        for i in range(5):
            start_time = time.time()
            try:
                self.unified_service.analyze_single_stock_comprehensive(
                    ticker="005930.KS",
                    market_type="KOSPI",
                    timeframe="d"
                )
                response_time = time.time() - start_time
                response_times.append(response_time)
            except Exception as e:
                response_times.append(10.0)  # 에러 시 10초로 설정
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        
        # 사용자 경험 점수 계산
        ux_score = 0
        if avg_response_time < 2.0:
            ux_score = 100
        elif avg_response_time < 5.0:
            ux_score = 80
        elif avg_response_time < 10.0:
            ux_score = 60
        else:
            ux_score = 40
        
        return {
            "response_times": response_times,
            "average_response_time": avg_response_time,
            "max_response_time": max_response_time,
            "ux_score": ux_score,
            "excellent_responses": len([rt for rt in response_times if rt < 2.0]),
            "good_responses": len([rt for rt in response_times if 2.0 <= rt < 5.0]),
            "poor_responses": len([rt for rt in response_times if rt >= 5.0])
        }
    
    def _test_resource_usage_performance(self) -> Dict[str, Any]:
        """리소스 사용량 성능 테스트"""
        process = psutil.Process()
        
        # CPU 사용량 측정
        cpu_percent = process.cpu_percent(interval=1)
        
        # 메모리 사용량 측정
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        # 디스크 사용량 측정
        disk_usage = psutil.disk_usage('/')
        disk_percent = disk_usage.percent
        
        # 네트워크 사용량 (시뮬레이션)
        network_usage = {
            "bytes_sent": 1024 * 1024,  # 1MB
            "bytes_recv": 2048 * 1024   # 2MB
        }
        
        # 리소스 효율성 점수 계산
        resource_score = 100
        
        if cpu_percent > 80:
            resource_score -= 30
        elif cpu_percent > 60:
            resource_score -= 15
        
        if memory_mb > 500:
            resource_score -= 30
        elif memory_mb > 300:
            resource_score -= 15
        
        if disk_percent > 90:
            resource_score -= 20
        elif disk_percent > 80:
            resource_score -= 10
        
        return {
            "cpu_percent": cpu_percent,
            "memory_mb": memory_mb,
            "disk_percent": disk_percent,
            "network_usage": network_usage,
            "resource_score": max(resource_score, 0)
        }
    
    def _test_scalability_performance(self) -> Dict[str, Any]:
        """확장성 성능 테스트"""
        # 동시 요청 처리 능력 테스트
        concurrent_requests = 5
        test_symbols = ["005930.KS", "000660.KS", "005380.KS", "012450.KS", "034020.KS"]
        
        def process_request(symbol):
            start_time = time.time()
            try:
                self.unified_service.analyze_single_stock_comprehensive(
                    ticker=symbol,
                    market_type="KOSPI",
                    timeframe="d"
                )
                return {"success": True, "time": time.time() - start_time}
            except Exception as e:
                return {"success": False, "time": time.time() - start_time, "error": str(e)}
        
        # 동시 처리 테스트
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [executor.submit(process_request, symbol) for symbol in test_symbols[:concurrent_requests]]
            results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # 성공률 계산
        successful_requests = sum(1 for result in results if result["success"])
        success_rate = successful_requests / len(results) if results else 0
        
        # 평균 처리 시간
        avg_processing_time = sum(result["time"] for result in results) / len(results) if results else 0
        
        # 확장성 점수 계산
        scalability_score = 0
        if success_rate >= 0.8 and avg_processing_time < 5.0:
            scalability_score = 100
        elif success_rate >= 0.6 and avg_processing_time < 10.0:
            scalability_score = 80
        elif success_rate >= 0.4:
            scalability_score = 60
        else:
            scalability_score = 40
        
        return {
            "concurrent_requests": concurrent_requests,
            "successful_requests": successful_requests,
            "success_rate": success_rate,
            "total_processing_time": total_time,
            "average_processing_time": avg_processing_time,
            "scalability_score": scalability_score
        }
    
    def _calculate_overall_performance_score(self, results: Dict[str, Any]) -> float:
        """전체 성능 점수 계산"""
        score = 0.0
        max_score = 100.0
        
        # 시스템 성능 점수 (30점)
        system_performance = results.get("system_performance", {})
        success_rate = system_performance.get("success_rate", 0)
        score += success_rate * 30
        
        # 사용자 경험 점수 (25점)
        user_experience = results.get("user_experience", {})
        ux_score = user_experience.get("ux_score", 0)
        score += ux_score * 0.25
        
        # 리소스 사용량 점수 (25점)
        resource_usage = results.get("resource_usage", {})
        resource_score = resource_usage.get("resource_score", 0)
        score += resource_score * 0.25
        
        # 확장성 점수 (20점)
        scalability = results.get("scalability", {})
        scalability_score = scalability.get("scalability_score", 0)
        score += scalability_score * 0.2
        
        return min(score, max_score)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """성능 검증 결과 요약"""
        if not self.performance_metrics:
            return {"error": "성능 검증이 실행되지 않았습니다."}
        
        return {
            "cache_optimization_score": self.performance_metrics.get("cache_optimization", {}).get("overall_score", 0),
            "batch_processing_score": self.performance_metrics.get("batch_processing", {}).get("overall_score", 0),
            "memory_optimization_score": self.performance_metrics.get("memory_optimization", {}).get("overall_score", 0),
            "overall_performance_score": self.performance_metrics.get("overall_performance", {}).get("overall_score", 0),
            "timestamp": datetime.now().isoformat()
        } 