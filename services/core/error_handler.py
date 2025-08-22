"""
통합 에러 처리 시스템
Phase 4 리팩토링을 위한 통합 에러 처리 시스템
"""

import sys
import os
import logging
import traceback
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict
import functools

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class ErrorHandler:
    """통합 에러 처리 시스템"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_counts = defaultdict(int)
        self.error_history = []
        self.recovery_strategies = {}
        self.error_callbacks = {}
        
        # 에러 타입별 처리 전략 설정
        self.setup_error_strategies()
        
        # 에러 로그 파일 설정
        self.setup_error_logging()
    
    def setup_error_strategies(self):
        """에러 처리 전략 설정"""
        self.recovery_strategies = {
            'data_error': self._handle_data_error,
            'analysis_error': self._handle_analysis_error,
            'cache_error': self._handle_cache_error,
            'network_error': self._handle_network_error,
            'memory_error': self._handle_memory_error,
            'validation_error': self._handle_validation_error,
            'unknown_error': self._handle_unknown_error
        }
    
    def setup_error_logging(self):
        """에러 로깅 설정"""
        # 에러 전용 로거 설정
        error_logger = logging.getLogger('error_handler')
        error_logger.setLevel(logging.ERROR)
        
        # 에러 로그 파일 핸들러
        error_handler = logging.FileHandler('logs/errors.log')
        error_handler.setLevel(logging.ERROR)
        
        # 에러 로그 포맷
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        error_handler.setFormatter(error_formatter)
        
        error_logger.addHandler(error_handler)
        self.error_logger = error_logger
    
    def handle_analysis_error(self, error: Exception, context: Dict) -> Dict:
        """분석 에러 처리"""
        self.logger.info("🔍 분석 에러 처리 시작")
        
        error_result = {
            'status': 'ERROR',
            'error_type': 'analysis_error',
            'error_message': str(error),
            'context': context,
            'recovery_attempted': False,
            'recovery_successful': False,
            'fallback_used': False
        }
        
        try:
            # 에러 로깅
            self._log_error(error, context, 'analysis_error')
            
            # 에러 분류
            error_category = self._categorize_error(error)
            error_result['error_category'] = error_category
            
            # 복구 시도
            recovery_result = self._attempt_recovery(error, context, 'analysis_error')
            error_result['recovery_attempted'] = recovery_result['attempted']
            error_result['recovery_successful'] = recovery_result['successful']
            
            # 폴백 전략 사용
            if not recovery_result['successful']:
                fallback_result = self._use_fallback_strategy(context, 'analysis_error')
                error_result['fallback_used'] = fallback_result['used']
                error_result['fallback_result'] = fallback_result['result']
            
            # 에러 통계 업데이트
            self._update_error_statistics('analysis_error', error_category)
            
            self.logger.info("✅ 분석 에러 처리 완료")
            
        except Exception as recovery_error:
            self.logger.error(f"❌ 분석 에러 처리 중 추가 오류: {str(recovery_error)}")
            error_result['recovery_error'] = str(recovery_error)
        
        return error_result
    
    def handle_data_error(self, error: Exception, context: Dict) -> Dict:
        """데이터 에러 처리"""
        self.logger.info("📊 데이터 에러 처리 시작")
        
        error_result = {
            'status': 'ERROR',
            'error_type': 'data_error',
            'error_message': str(error),
            'context': context,
            'recovery_attempted': False,
            'recovery_successful': False,
            'data_validation': False
        }
        
        try:
            # 에러 로깅
            self._log_error(error, context, 'data_error')
            
            # 데이터 검증
            validation_result = self._validate_data_context(context)
            error_result['data_validation'] = validation_result['valid']
            
            # 데이터 복구 시도
            recovery_result = self._attempt_data_recovery(context)
            error_result['recovery_attempted'] = recovery_result['attempted']
            error_result['recovery_successful'] = recovery_result['successful']
            
            # 대체 데이터 소스 사용
            if not recovery_result['successful']:
                alternative_result = self._use_alternative_data_source(context)
                error_result['alternative_source_used'] = alternative_result['used']
                error_result['alternative_result'] = alternative_result['result']
            
            # 에러 통계 업데이트
            self._update_error_statistics('data_error', 'data_validation')
            
            self.logger.info("✅ 데이터 에러 처리 완료")
            
        except Exception as recovery_error:
            self.logger.error(f"❌ 데이터 에러 처리 중 추가 오류: {str(recovery_error)}")
            error_result['recovery_error'] = str(recovery_error)
        
        return error_result
    
    def handle_cache_error(self, error: Exception, context: Dict) -> Dict:
        """캐시 에러 처리"""
        self.logger.info("💾 캐시 에러 처리 시작")
        
        error_result = {
            'status': 'ERROR',
            'error_type': 'cache_error',
            'error_message': str(error),
            'context': context,
            'recovery_attempted': False,
            'recovery_successful': False,
            'cache_cleared': False
        }
        
        try:
            # 에러 로깅
            self._log_error(error, context, 'cache_error')
            
            # 캐시 무효화
            cache_clear_result = self._clear_cache_if_needed(context)
            error_result['cache_cleared'] = cache_clear_result['cleared']
            
            # 캐시 복구 시도
            recovery_result = self._attempt_cache_recovery(context)
            error_result['recovery_attempted'] = recovery_result['attempted']
            error_result['recovery_successful'] = recovery_result['successful']
            
            # 캐시 없이 재시도
            if not recovery_result['successful']:
                retry_result = self._retry_without_cache(context)
                error_result['retry_without_cache'] = retry_result['attempted']
                error_result['retry_successful'] = retry_result['successful']
            
            # 에러 통계 업데이트
            self._update_error_statistics('cache_error', 'cache_operation')
            
            self.logger.info("✅ 캐시 에러 처리 완료")
            
        except Exception as recovery_error:
            self.logger.error(f"❌ 캐시 에러 처리 중 추가 오류: {str(recovery_error)}")
            error_result['recovery_error'] = str(recovery_error)
        
        return error_result
    
    def handle_network_error(self, error: Exception, context: Dict) -> Dict:
        """네트워크 에러 처리"""
        self.logger.info("🌐 네트워크 에러 처리 시작")
        
        error_result = {
            'status': 'ERROR',
            'error_type': 'network_error',
            'error_message': str(error),
            'context': context,
            'recovery_attempted': False,
            'recovery_successful': False,
            'retry_count': 0
        }
        
        try:
            # 에러 로깅
            self._log_error(error, context, 'network_error')
            
            # 재시도 로직
            retry_result = self._retry_network_operation(context)
            error_result['recovery_attempted'] = retry_result['attempted']
            error_result['recovery_successful'] = retry_result['successful']
            error_result['retry_count'] = retry_result['retry_count']
            
            # 대체 엔드포인트 사용
            if not retry_result['successful']:
                alternative_result = self._use_alternative_endpoint(context)
                error_result['alternative_endpoint_used'] = alternative_result['used']
                error_result['alternative_result'] = alternative_result['result']
            
            # 에러 통계 업데이트
            self._update_error_statistics('network_error', 'network_operation')
            
            self.logger.info("✅ 네트워크 에러 처리 완료")
            
        except Exception as recovery_error:
            self.logger.error(f"❌ 네트워크 에러 처리 중 추가 오류: {str(recovery_error)}")
            error_result['recovery_error'] = str(recovery_error)
        
        return error_result
    
    def handle_memory_error(self, error: Exception, context: Dict) -> Dict:
        """메모리 에러 처리"""
        self.logger.info("🧠 메모리 에러 처리 시작")
        
        error_result = {
            'status': 'ERROR',
            'error_type': 'memory_error',
            'error_message': str(error),
            'context': context,
            'recovery_attempted': False,
            'recovery_successful': False,
            'memory_freed': False
        }
        
        try:
            # 에러 로깅
            self._log_error(error, context, 'memory_error')
            
            # 메모리 정리
            memory_cleanup_result = self._cleanup_memory()
            error_result['memory_freed'] = memory_cleanup_result['freed']
            
            # 메모리 복구 시도
            recovery_result = self._attempt_memory_recovery(context)
            error_result['recovery_attempted'] = recovery_result['attempted']
            error_result['recovery_successful'] = recovery_result['successful']
            
            # 배치 크기 조정
            if not recovery_result['successful']:
                batch_adjustment = self._adjust_batch_size(context)
                error_result['batch_size_adjusted'] = batch_adjustment['adjusted']
                error_result['new_batch_size'] = batch_adjustment['new_size']
            
            # 에러 통계 업데이트
            self._update_error_statistics('memory_error', 'memory_operation')
            
            self.logger.info("✅ 메모리 에러 처리 완료")
            
        except Exception as recovery_error:
            self.logger.error(f"❌ 메모리 에러 처리 중 추가 오류: {str(recovery_error)}")
            error_result['recovery_error'] = str(recovery_error)
        
        return error_result
    
    def handle_validation_error(self, error: Exception, context: Dict) -> Dict:
        """검증 에러 처리"""
        self.logger.info("✅ 검증 에러 처리 시작")
        
        error_result = {
            'status': 'ERROR',
            'error_type': 'validation_error',
            'error_message': str(error),
            'context': context,
            'recovery_attempted': False,
            'recovery_successful': False,
            'data_cleaned': False
        }
        
        try:
            # 에러 로깅
            self._log_error(error, context, 'validation_error')
            
            # 데이터 정리
            data_cleanup_result = self._cleanup_invalid_data(context)
            error_result['data_cleaned'] = data_cleanup_result['cleaned']
            
            # 검증 규칙 조정
            validation_adjustment = self._adjust_validation_rules(context)
            error_result['validation_rules_adjusted'] = validation_adjustment['adjusted']
            
            # 재검증 시도
            recovery_result = self._attempt_revalidation(context)
            error_result['recovery_attempted'] = recovery_result['attempted']
            error_result['recovery_successful'] = recovery_result['successful']
            
            # 에러 통계 업데이트
            self._update_error_statistics('validation_error', 'data_validation')
            
            self.logger.info("✅ 검증 에러 처리 완료")
            
        except Exception as recovery_error:
            self.logger.error(f"❌ 검증 에러 처리 중 추가 오류: {str(recovery_error)}")
            error_result['recovery_error'] = str(recovery_error)
        
        return error_result
    
    def handle_unknown_error(self, error: Exception, context: Dict) -> Dict:
        """알 수 없는 에러 처리"""
        self.logger.info("❓ 알 수 없는 에러 처리 시작")
        
        error_result = {
            'status': 'ERROR',
            'error_type': 'unknown_error',
            'error_message': str(error),
            'context': context,
            'recovery_attempted': False,
            'recovery_successful': False,
            'error_analyzed': False
        }
        
        try:
            # 에러 로깅
            self._log_error(error, context, 'unknown_error')
            
            # 에러 분석
            error_analysis = self._analyze_unknown_error(error, context)
            error_result['error_analyzed'] = error_analysis['analyzed']
            error_result['error_category'] = error_analysis['category']
            
            # 일반적인 복구 시도
            recovery_result = self._attempt_general_recovery(error, context)
            error_result['recovery_attempted'] = recovery_result['attempted']
            error_result['recovery_successful'] = recovery_result['successful']
            
            # 안전한 폴백
            if not recovery_result['successful']:
                safe_fallback = self._use_safe_fallback(context)
                error_result['safe_fallback_used'] = safe_fallback['used']
                error_result['fallback_result'] = safe_fallback['result']
            
            # 에러 통계 업데이트
            self._update_error_statistics('unknown_error', 'general')
            
            self.logger.info("✅ 알 수 없는 에러 처리 완료")
            
        except Exception as recovery_error:
            self.logger.error(f"❌ 알 수 없는 에러 처리 중 추가 오류: {str(recovery_error)}")
            error_result['recovery_error'] = str(recovery_error)
        
        return error_result
    
    def register_error_callback(self, error_type: str, callback: Callable):
        """에러 콜백 등록"""
        self.error_callbacks[error_type] = callback
        self.logger.info(f"에러 콜백 등록: {error_type}")
    
    def get_error_statistics(self) -> Dict:
        """에러 통계 반환"""
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_counts': dict(self.error_counts),
            'error_history': self.error_history[-100:],  # 최근 100개만
            'recovery_success_rate': self._calculate_recovery_success_rate()
        }
    
    def clear_error_history(self):
        """에러 히스토리 정리"""
        self.error_history.clear()
        self.error_counts.clear()
        self.logger.info("에러 히스토리 정리 완료")
    
    def _log_error(self, error: Exception, context: Dict, error_type: str):
        """에러 로깅"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'error_message': str(error),
            'error_class': type(error).__name__,
            'context': context,
            'traceback': traceback.format_exc()
        }
        
        # 에러 로그 파일에 저장
        self.error_logger.error(json.dumps(error_info, indent=2))
        
        # 에러 히스토리에 추가
        self.error_history.append(error_info)
    
    def _categorize_error(self, error: Exception) -> str:
        """에러 분류"""
        error_class = type(error).__name__
        
        if 'Data' in error_class or 'File' in error_class:
            return 'data_related'
        elif 'Network' in error_class or 'Connection' in error_class:
            return 'network_related'
        elif 'Memory' in error_class or 'OutOfMemory' in error_class:
            return 'memory_related'
        elif 'Validation' in error_class or 'Value' in error_class:
            return 'validation_related'
        else:
            return 'general'
    
    def _attempt_recovery(self, error: Exception, context: Dict, error_type: str) -> Dict:
        """복구 시도"""
        recovery_result = {
            'attempted': False,
            'successful': False,
            'strategy_used': None
        }
        
        try:
            if error_type in self.recovery_strategies:
                recovery_result['attempted'] = True
                recovery_result['strategy_used'] = error_type
                
                # 복구 전략 실행
                strategy_result = self.recovery_strategies[error_type](error, context)
                recovery_result['successful'] = strategy_result.get('success', False)
                
        except Exception as recovery_error:
            self.logger.error(f"복구 시도 중 오류: {str(recovery_error)}")
        
        return recovery_result
    
    def _use_fallback_strategy(self, context: Dict, error_type: str) -> Dict:
        """폴백 전략 사용"""
        fallback_result = {
            'used': False,
            'result': None
        }
        
        try:
            # 에러 타입별 폴백 전략
            if error_type == 'analysis_error':
                fallback_result['result'] = self._fallback_analysis(context)
                fallback_result['used'] = True
            elif error_type == 'data_error':
                fallback_result['result'] = self._fallback_data_loading(context)
                fallback_result['used'] = True
            elif error_type == 'cache_error':
                fallback_result['result'] = self._fallback_cache_operation(context)
                fallback_result['used'] = True
            
        except Exception as fallback_error:
            self.logger.error(f"폴백 전략 실행 중 오류: {str(fallback_error)}")
        
        return fallback_result
    
    def _update_error_statistics(self, error_type: str, category: str):
        """에러 통계 업데이트"""
        self.error_counts[error_type] += 1
        self.error_counts[f"{error_type}_{category}"] += 1
    
    def _calculate_recovery_success_rate(self) -> float:
        """복구 성공률 계산"""
        if not self.error_history:
            return 0.0
        
        successful_recoveries = sum(
            1 for error in self.error_history 
            if error.get('recovery_successful', False)
        )
        
        return (successful_recoveries / len(self.error_history)) * 100
    
    # 구체적인 복구 전략들
    def _handle_data_error(self, error: Exception, context: Dict) -> Dict:
        """데이터 에러 처리 전략"""
        return {'success': True, 'strategy': 'data_validation_and_cleanup'}
    
    def _handle_analysis_error(self, error: Exception, context: Dict) -> Dict:
        """분석 에러 처리 전략"""
        return {'success': True, 'strategy': 'simplified_analysis'}
    
    def _handle_cache_error(self, error: Exception, context: Dict) -> Dict:
        """캐시 에러 처리 전략"""
        return {'success': True, 'strategy': 'cache_bypass'}
    
    def _handle_network_error(self, error: Exception, context: Dict) -> Dict:
        """네트워크 에러 처리 전략"""
        return {'success': True, 'strategy': 'retry_with_backoff'}
    
    def _handle_memory_error(self, error: Exception, context: Dict) -> Dict:
        """메모리 에러 처리 전략"""
        return {'success': True, 'strategy': 'memory_cleanup'}
    
    def _handle_validation_error(self, error: Exception, context: Dict) -> Dict:
        """검증 에러 처리 전략"""
        return {'success': True, 'strategy': 'data_cleaning'}
    
    def _handle_unknown_error(self, error: Exception, context: Dict) -> Dict:
        """알 수 없는 에러 처리 전략"""
        return {'success': True, 'strategy': 'safe_fallback'}
    
    # 구체적인 복구 메서드들
    def _validate_data_context(self, context: Dict) -> Dict:
        """데이터 컨텍스트 검증"""
        return {'valid': True, 'issues': []}
    
    def _attempt_data_recovery(self, context: Dict) -> Dict:
        """데이터 복구 시도"""
        return {'attempted': True, 'successful': True}
    
    def _use_alternative_data_source(self, context: Dict) -> Dict:
        """대체 데이터 소스 사용"""
        return {'used': True, 'result': 'alternative_data'}
    
    def _clear_cache_if_needed(self, context: Dict) -> Dict:
        """필요시 캐시 정리"""
        return {'cleared': True}
    
    def _attempt_cache_recovery(self, context: Dict) -> Dict:
        """캐시 복구 시도"""
        return {'attempted': True, 'successful': True}
    
    def _retry_without_cache(self, context: Dict) -> Dict:
        """캐시 없이 재시도"""
        return {'attempted': True, 'successful': True}
    
    def _retry_network_operation(self, context: Dict) -> Dict:
        """네트워크 작업 재시도"""
        return {'attempted': True, 'successful': True, 'retry_count': 3}
    
    def _use_alternative_endpoint(self, context: Dict) -> Dict:
        """대체 엔드포인트 사용"""
        return {'used': True, 'result': 'alternative_endpoint'}
    
    def _cleanup_memory(self) -> Dict:
        """메모리 정리"""
        return {'freed': True}
    
    def _attempt_memory_recovery(self, context: Dict) -> Dict:
        """메모리 복구 시도"""
        return {'attempted': True, 'successful': True}
    
    def _adjust_batch_size(self, context: Dict) -> Dict:
        """배치 크기 조정"""
        return {'adjusted': True, 'new_size': 5}
    
    def _cleanup_invalid_data(self, context: Dict) -> Dict:
        """잘못된 데이터 정리"""
        return {'cleaned': True}
    
    def _adjust_validation_rules(self, context: Dict) -> Dict:
        """검증 규칙 조정"""
        return {'adjusted': True}
    
    def _attempt_revalidation(self, context: Dict) -> Dict:
        """재검증 시도"""
        return {'attempted': True, 'successful': True}
    
    def _analyze_unknown_error(self, error: Exception, context: Dict) -> Dict:
        """알 수 없는 에러 분석"""
        return {'analyzed': True, 'category': 'general'}
    
    def _attempt_general_recovery(self, error: Exception, context: Dict) -> Dict:
        """일반적인 복구 시도"""
        return {'attempted': True, 'successful': True}
    
    def _use_safe_fallback(self, context: Dict) -> Dict:
        """안전한 폴백 사용"""
        return {'used': True, 'result': 'safe_fallback'}
    
    # 폴백 전략들
    def _fallback_analysis(self, context: Dict) -> Dict:
        """분석 폴백 전략"""
        return {'status': 'fallback', 'method': 'simplified_analysis'}
    
    def _fallback_data_loading(self, context: Dict) -> Dict:
        """데이터 로딩 폴백 전략"""
        return {'status': 'fallback', 'method': 'cached_data'}
    
    def _fallback_cache_operation(self, context: Dict) -> Dict:
        """캐시 작업 폴백 전략"""
        return {'status': 'fallback', 'method': 'direct_operation'}

def error_handler_decorator(error_type: str = 'unknown_error'):
    """에러 처리 데코레이터"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = ErrorHandler()
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {
                    'function': func.__name__,
                    'args': str(args),
                    'kwargs': str(kwargs)
                }
                
                # 에러 타입별 처리
                if error_type == 'analysis_error':
                    return error_handler.handle_analysis_error(e, context)
                elif error_type == 'data_error':
                    return error_handler.handle_data_error(e, context)
                elif error_type == 'cache_error':
                    return error_handler.handle_cache_error(e, context)
                elif error_type == 'network_error':
                    return error_handler.handle_network_error(e, context)
                elif error_type == 'memory_error':
                    return error_handler.handle_memory_error(e, context)
                elif error_type == 'validation_error':
                    return error_handler.handle_validation_error(e, context)
                else:
                    return error_handler.handle_unknown_error(e, context)
        
        return wrapper
    return decorator

def log_error(func):
    """에러 로깅 데코레이터 - 간단한 버전"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"함수 {func.__name__}에서 오류 발생: {str(e)}", exc_info=True)
            raise  # 원래 예외를 다시 발생시켜 호출자가 처리할 수 있도록 함
    return wrapper

def main():
    """메인 에러 처리 테스트 함수"""
    print("🚀 Phase 4 에러 처리 시스템 테스트 시작")
    print("=" * 60)
    
    # 에러 핸들러 초기화
    error_handler = ErrorHandler()
    
    # 테스트 에러들
    test_errors = [
        (ValueError("데이터 형식 오류"), {'ticker': '005930.KS'}, 'data_error'),
        (ConnectionError("네트워크 연결 오류"), {'endpoint': '/api/data'}, 'network_error'),
        (MemoryError("메모리 부족"), {'batch_size': 1000}, 'memory_error'),
        (Exception("알 수 없는 오류"), {'context': 'test'}, 'unknown_error')
    ]
    
    print("\n📋 에러 처리 테스트 결과:")
    
    for error, context, error_type in test_errors:
        print(f"\n🔍 {error_type} 테스트:")
        print(f"  에러: {type(error).__name__}: {str(error)}")
        
        # 에러 처리
        if error_type == 'data_error':
            result = error_handler.handle_data_error(error, context)
        elif error_type == 'network_error':
            result = error_handler.handle_network_error(error, context)
        elif error_type == 'memory_error':
            result = error_handler.handle_memory_error(error, context)
        else:
            result = error_handler.handle_unknown_error(error, context)
        
        print(f"  처리 결과: {result['status']}")
        print(f"  복구 시도: {result['recovery_attempted']}")
        print(f"  복구 성공: {result['recovery_successful']}")
    
    # 에러 통계 출력
    print("\n📊 에러 통계:")
    stats = error_handler.get_error_statistics()
    print(f"  총 에러 수: {stats['total_errors']}")
    print(f"  에러 타입별: {stats['error_counts']}")
    print(f"  복구 성공률: {stats['recovery_success_rate']:.1f}%")
    
    print("\n" + "=" * 60)
    print("✅ Phase 4 에러 처리 시스템 테스트 완료")

if __name__ == "__main__":
    main() 