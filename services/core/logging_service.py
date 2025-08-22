"""
체계적인 로깅 시스템
Phase 4 리팩토링을 위한 체계적인 로깅 시스템
"""

import sys
import os
import logging
import json
import time
from datetime import datetime, timedelta
import uuid
from typing import Dict, List, Optional, Any
from pathlib import Path
import threading
from collections import defaultdict

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class LoggingService:
    """체계적인 로깅 시스템"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 실행 고유 식별자 (타임스탬프 + 짧은 UUID)
        self.run_id = datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + uuid.uuid4().hex[:6]
        self.performance_metrics = defaultdict(list)
        self.operation_history = []
        self.log_levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        # 로그 디렉토리 생성
        self.setup_log_directories()
        
        # 주의: 전역 로깅 초기화의 단일 진입점은 app.py(dictConfig)입니다.
        # 이 클래스는 별도 파일 핸들러/헬퍼를 제공하는 보조 역할로 사용하세요.
        # Deprecated: 아래 전역 로깅 초기화 호출은 더 이상 수행하지 않습니다.
        # self.setup_logging()
        
        # 성능 모니터링 설정
        self.setup_performance_monitoring()
    
    def setup_log_directories(self):
        """로그 디렉토리 설정"""
        log_dirs = ['logs', 'logs/analysis', 'logs/performance', 'logs/errors']
        
        for log_dir in log_dirs:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    def setup_logging(self):
        """Deprecated: 전역 로깅 초기화는 app.py에서 수행합니다."""
        # 기본 로거 설정
        run_app_log = f"logs/app_{self.run_id}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(run_app_log, encoding='utf-8', mode='w'),
                logging.StreamHandler()
            ]
        )
        
        # 분석 전용 로거
        self.analysis_logger = self._create_logger(
            'analysis_logger',
            f"logs/analysis/analysis_{self.run_id}.log",
            logging.INFO
        )
        
        # 성능 전용 로거
        self.performance_logger = self._create_logger(
            'performance_logger',
            f"logs/performance/performance_{self.run_id}.log",
            logging.INFO
        )
        
        # 에러 전용 로거
        self.error_logger = self._create_logger(
            'error_logger',
            'logs/errors/errors.log',
            logging.ERROR
        )
        
        # 시스템 전용 로거
        self.system_logger = self._create_logger(
            'system_logger',
            f"logs/system_{self.run_id}.log",
            logging.INFO
        )
    
    def setup_performance_monitoring(self):
        """성능 모니터링 설정"""
        self.performance_start_times = {}
        self.performance_metrics = defaultdict(list)
    
    def _create_logger(self, name: str, log_file: str, level: int) -> logging.Logger:
        """로거 생성"""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # 파일 핸들러
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        
        # 포맷터
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        
        return logger
    
    def log_analysis_start(self, ticker: str, market_type: str, operation: str = 'analysis'):
        """분석 시작 로깅"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'ticker': ticker,
            'market_type': market_type,
            'status': 'started',
            'thread_id': threading.get_ident()
        }
        
        self.analysis_logger.info(f"분석 시작: {json.dumps(log_data, ensure_ascii=False)}")
        
        # 성능 모니터링 시작
        self.performance_start_times[f"{ticker}_{operation}"] = time.time()
    
    def log_analysis_complete(self, ticker: str, result: Dict, operation: str = 'analysis'):
        """분석 완료 로깅"""
        # 성능 측정
        start_time = self.performance_start_times.get(f"{ticker}_{operation}")
        execution_time = time.time() - start_time if start_time else 0
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'ticker': ticker,
            'status': 'completed',
            'execution_time': execution_time,
            'result_size': len(str(result)),
            'thread_id': threading.get_ident()
        }
        
        self.analysis_logger.info(f"분석 완료: {json.dumps(log_data, ensure_ascii=False)}")
        
        # 성능 메트릭 저장
        self.performance_metrics[f"{ticker}_{operation}"].append({
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat(),
            'result_size': len(str(result))
        })
        
        # 성능 로그
        self.performance_logger.info(f"성능 메트릭: {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_analysis_error(self, ticker: str, error: Exception, operation: str = 'analysis'):
        """분석 에러 로깅"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'ticker': ticker,
            'status': 'error',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'thread_id': threading.get_ident()
        }
        
        self.analysis_logger.error(f"분석 에러: {json.dumps(log_data, ensure_ascii=False)}")
        self.error_logger.error(f"분석 에러: {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_performance(self, operation: str, duration: float, details: Dict = None):
        """성능 로깅"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'duration': duration,
            'details': details or {},
            'thread_id': threading.get_ident()
        }
        
        self.performance_logger.info(f"성능 로그: {json.dumps(log_data, ensure_ascii=False)}")
        
        # 성능 메트릭 저장
        self.performance_metrics[operation].append({
            'duration': duration,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        })
    
    def log_error(self, error: Exception, context: Dict = None, level: str = 'ERROR'):
        """에러 로깅"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {},
            'thread_id': threading.get_ident()
        }
        
        log_message = f"에러 로그: {json.dumps(log_data, ensure_ascii=False)}"
        
        if level.upper() in self.log_levels:
            log_level = self.log_levels[level.upper()]
            self.error_logger.log(log_level, log_message)
        else:
            self.error_logger.error(log_message)
    
    def log_system_event(self, event: str, details: Dict = None):
        """시스템 이벤트 로깅"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'event': event,
            'details': details or {},
            'thread_id': threading.get_ident()
        }
        
        self.system_logger.info(f"시스템 이벤트: {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_cache_operation(self, operation: str, key: str, success: bool, details: Dict = None):
        """캐시 작업 로깅"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'key': key,
            'success': success,
            'details': details or {},
            'thread_id': threading.get_ident()
        }
        
        self.system_logger.info(f"캐시 작업: {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_data_operation(self, operation: str, ticker: str, market_type: str, 
                          success: bool, details: Dict = None):
        """데이터 작업 로깅"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'ticker': ticker,
            'market_type': market_type,
            'success': success,
            'details': details or {},
            'thread_id': threading.get_ident()
        }
        
        self.analysis_logger.info(f"데이터 작업: {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_batch_operation(self, operation: str, batch_size: int, success_count: int, 
                           error_count: int, details: Dict = None):
        """배치 작업 로깅"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'batch_size': batch_size,
            'success_count': success_count,
            'error_count': error_count,
            'success_rate': (success_count / batch_size * 100) if batch_size > 0 else 0,
            'details': details or {},
            'thread_id': threading.get_ident()
        }
        
        self.system_logger.info(f"배치 작업: {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_memory_usage(self, memory_info: Dict):
        """메모리 사용량 로깅"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'memory_usage': memory_info,
            'thread_id': threading.get_ident()
        }
        
        self.performance_logger.info(f"메모리 사용량: {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_api_call(self, endpoint: str, method: str, status_code: int, 
                     response_time: float, details: Dict = None):
        """API 호출 로깅"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'response_time': response_time,
            'details': details or {},
            'thread_id': threading.get_ident()
        }
        
        self.system_logger.info(f"API 호출: {json.dumps(log_data, ensure_ascii=False)}")
    
    def get_performance_statistics(self, operation: str = None, 
                                 time_range: timedelta = None) -> Dict:
        """성능 통계 반환"""
        if operation:
            metrics = self.performance_metrics.get(operation, [])
        else:
            metrics = []
            for op_metrics in self.performance_metrics.values():
                metrics.extend(op_metrics)
        
        if time_range:
            cutoff_time = datetime.now() - time_range
            metrics = [
                m for m in metrics 
                if datetime.fromisoformat(m['timestamp']) > cutoff_time
            ]
        
        if not metrics:
            return {
                'total_operations': 0,
                'average_duration': 0,
                'min_duration': 0,
                'max_duration': 0,
                'total_duration': 0
            }
        
        durations = [m.get('duration', 0) for m in metrics]
        
        return {
            'total_operations': len(metrics),
            'average_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'total_duration': sum(durations)
        }
    
    def get_error_statistics(self, time_range: timedelta = None) -> Dict:
        """에러 통계 반환"""
        # 실제 구현에서는 에러 로그 파일을 분석하여 통계 생성
        return {
            'total_errors': 0,
            'error_types': {},
            'recent_errors': []
        }
    
    def get_system_health_report(self) -> Dict:
        """시스템 건강 상태 리포트"""
        return {
            'timestamp': datetime.now().isoformat(),
            'performance_stats': self.get_performance_statistics(),
            'error_stats': self.get_error_statistics(),
            'memory_usage': self._get_memory_usage(),
            'log_file_sizes': self._get_log_file_sizes()
        }
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """오래된 로그 정리"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        log_dirs = ['logs', 'logs/analysis', 'logs/performance', 'logs/errors']
        
        for log_dir in log_dirs:
            if os.path.exists(log_dir):
                for file in os.listdir(log_dir):
                    file_path = os.path.join(log_dir, file)
                    if os.path.isfile(file_path):
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if file_time < cutoff_date:
                            try:
                                os.remove(file_path)
                                self.system_logger.info(f"오래된 로그 파일 삭제: {file_path}")
                            except Exception as e:
                                self.error_logger.error(f"로그 파일 삭제 실패: {file_path}, {str(e)}")
    
    def export_logs(self, export_path: str, log_types: List[str] = None):
        """로그 내보내기"""
        if log_types is None:
            log_types = ['analysis', 'performance', 'errors', 'system']
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'log_types': log_types,
            'logs': {}
        }
        
        for log_type in log_types:
            log_file = f'logs/{log_type}.log'
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        export_data['logs'][log_type] = f.readlines()
                except Exception as e:
                    self.error_logger.error(f"로그 내보내기 실패: {log_type}, {str(e)}")
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.system_logger.info(f"로그 내보내기 완료: {export_path}")
        except Exception as e:
            self.error_logger.error(f"로그 내보내기 실패: {export_path}, {str(e)}")
    
    def _get_memory_usage(self) -> Dict:
        """메모리 사용량 반환"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return {
                'total_mb': memory.total / (1024 * 1024),
                'available_mb': memory.available / (1024 * 1024),
                'used_mb': memory.used / (1024 * 1024),
                'percent': memory.percent
            }
        except ImportError:
            return {'error': 'psutil not available'}
    
    def _get_log_file_sizes(self) -> Dict:
        """로그 파일 크기 반환"""
        log_files = {
            'analysis': 'logs/analysis/analysis.log',
            'performance': 'logs/performance/performance.log',
            'errors': 'logs/errors/errors.log',
            'system': 'logs/system.log',
            'app': 'logs/app.log'
        }
        
        sizes = {}
        for name, file_path in log_files.items():
            if os.path.exists(file_path):
                try:
                    size = os.path.getsize(file_path)
                    sizes[name] = size
                except Exception:
                    sizes[name] = 0
            else:
                sizes[name] = 0
        
        return sizes

def logging_decorator(operation: str = 'unknown'):
    """로깅 데코레이터"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logging_service = LoggingService()
            
            # 함수 정보 추출
            func_name = func.__name__
            ticker = kwargs.get('ticker', args[0] if args else 'unknown')
            market_type = kwargs.get('market_type', 'unknown')
            
            # 시작 로깅
            logging_service.log_analysis_start(ticker, market_type, operation)
            
            try:
                # 함수 실행
                result = func(*args, **kwargs)
                
                # 완료 로깅
                logging_service.log_analysis_complete(ticker, result, operation)
                
                return result
                
            except Exception as e:
                # 에러 로깅
                logging_service.log_analysis_error(ticker, e, operation)
                raise
            
        return wrapper
    return decorator

def main():
    """메인 로깅 시스템 테스트 함수"""
    print("🚀 Phase 4 로깅 시스템 테스트 시작")
    print("=" * 60)
    
    # 로깅 서비스 초기화
    logging_service = LoggingService()
    
    # 테스트 로깅
    print("\n📋 로깅 테스트:")
    
    # 1. 분석 시작/완료 로깅
    print("  1. 분석 로깅 테스트")
    logging_service.log_analysis_start('005930.KS', 'KOSPI', 'stock_analysis')
    time.sleep(0.1)  # 시뮬레이션된 처리 시간
    logging_service.log_analysis_complete('005930.KS', {'status': 'success'}, 'stock_analysis')
    
    # 2. 성능 로깅
    print("  2. 성능 로깅 테스트")
    logging_service.log_performance('data_loading', 1.5, {'rows': 1000})
    logging_service.log_performance('analysis', 2.3, {'indicators': 5})
    
    # 3. 에러 로깅
    print("  3. 에러 로깅 테스트")
    try:
        raise ValueError("테스트 에러")
    except Exception as e:
        logging_service.log_error(e, {'context': 'test'})
    
    # 4. 시스템 이벤트 로깅
    print("  4. 시스템 이벤트 로깅 테스트")
    logging_service.log_system_event('cache_cleanup', {'files_removed': 5})
    logging_service.log_system_event('batch_processing', {'batch_size': 100})
    
    # 5. 캐시 작업 로깅
    print("  5. 캐시 작업 로깅 테스트")
    logging_service.log_cache_operation('get', 'test_key', True, {'hit': True})
    logging_service.log_cache_operation('set', 'test_key', True, {'expire': 3600})
    
    # 6. 데이터 작업 로깅
    print("  6. 데이터 작업 로깅 테스트")
    logging_service.log_data_operation('load', '005930.KS', 'KOSPI', True, {'rows': 1000})
    logging_service.log_data_operation('save', '005930.KS', 'KOSPI', True, {'format': 'csv'})
    
    # 7. 배치 작업 로깅
    print("  7. 배치 작업 로깅 테스트")
    logging_service.log_batch_operation('analysis', 10, 8, 2, {'market_type': 'KOSPI'})
    
    # 8. 메모리 사용량 로깅
    print("  8. 메모리 사용량 로깅 테스트")
    memory_info = logging_service._get_memory_usage()
    logging_service.log_memory_usage(memory_info)
    
    # 9. API 호출 로깅
    print("  9. API 호출 로깅 테스트")
    logging_service.log_api_call('/api/stock/005930.KS', 'GET', 200, 0.5, {'cache': True})
    
    # 통계 출력
    print("\n📊 로깅 통계:")
    performance_stats = logging_service.get_performance_statistics()
    print(f"  성능 통계: {performance_stats}")
    
    system_health = logging_service.get_system_health_report()
    print(f"  시스템 건강 상태: {system_health}")
    
    print("\n" + "=" * 60)
    print("✅ Phase 4 로깅 시스템 테스트 완료")

if __name__ == "__main__":
    main() 