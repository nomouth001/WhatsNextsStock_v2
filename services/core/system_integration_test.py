"""
전체 시스템 통합 테스트
Phase 4 리팩토링을 위한 시스템 통합 테스트
"""

import sys
import os
import logging
import time
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import tempfile
import shutil

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.core.unified_market_analysis_service import UnifiedMarketAnalysisService
from services.analysis.crossover.simplified_detector import SimplifiedCrossoverDetector
from services.analysis.pattern.ema_analyzer import EMAAnalyzer
from services.analysis.pattern.classification import StockClassifier
from services.analysis.scoring.importance_calculator import ImportanceCalculator
from services.core.cache_service import CacheService
from services.market.data_reading_service import DataReadingService
from services.technical_indicators_service import TechnicalIndicatorsService

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class SystemIntegrationTest:
    """전체 시스템 통합 테스트"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_results = {}
        self.performance_metrics = {}
        
        # 서비스들 초기화
        self.unified_service = UnifiedMarketAnalysisService()
        self.crossover_detector = SimplifiedCrossoverDetector()
        self.ema_analyzer = EMAAnalyzer()
        self.stock_classifier = StockClassifier()
        self.importance_calculator = ImportanceCalculator()
        # [메모] 2025-08-19: 캐시 사용 경로 단일화
        # 기존 코드: self.cache_service = FileBasedCacheService()
        self.cache_service = CacheService()
        self.data_reading_service = DataReadingService()
        self.technical_indicators_service = TechnicalIndicatorsService()
    
    def run_complete_integration_test(self) -> Dict:
        """완전한 시스템 통합 테스트 실행"""
        self.logger.info("🚀 전체 시스템 통합 테스트 시작")
        
        test_results = {
            'start_time': datetime.now().isoformat(),
            'tests': {},
            'performance': {},
            'errors': []
        }
        
        try:
            # 1. 데이터 로딩 테스트
            test_results['tests']['data_loading'] = self.test_data_loading()
            
            # 2. 분석 플로우 테스트
            test_results['tests']['analysis_flow'] = self.test_complete_analysis_flow()
            
            # 3. 캐시 시스템 테스트
            test_results['tests']['cache_system'] = self.test_cache_system()
            
            # 4. 에러 복구 테스트
            test_results['tests']['error_recovery'] = self.test_error_recovery()
            
            # 5. 성능 벤치마크 테스트
            test_results['tests']['performance_benchmark'] = self.test_performance_benchmark()
            
            # 6. 모듈 간 통합 테스트
            test_results['tests']['module_integration'] = self.test_module_integration()
            
            test_results['end_time'] = datetime.now().isoformat()
            test_results['overall_status'] = 'PASS' if not test_results['errors'] else 'FAIL'
            
            self.logger.info(f"✅ 전체 시스템 통합 테스트 완료: {test_results['overall_status']}")
            
        except Exception as e:
            self.logger.error(f"❌ 시스템 통합 테스트 중 오류 발생: {str(e)}")
            test_results['errors'].append(str(e))
            test_results['overall_status'] = 'ERROR'
        
        return test_results
    
    def test_data_loading(self) -> Dict:
        """데이터 로딩 테스트"""
        self.logger.info("📊 데이터 로딩 테스트 시작")
        
        test_result = {
            'status': 'PASS',
            'details': {},
            'errors': []
        }
        
        try:
            # 테스트용 종목 리스트
            test_tickers = ['005930.KS', '000660.KS', '005380.KS']  # 삼성전자, SK하이닉스, 현대차
            
            for ticker in test_tickers:
                try:
                    # OHLCV 데이터 로딩 테스트
                    ohlcv_df = self.data_reading_service.read_ohlcv_csv(ticker, 'd', 'KOSPI')
                    if ohlcv_df.empty:
                        test_result['errors'].append(f"{ticker}: OHLCV 데이터 로딩 실패")
                        continue
                    
                    # 지표 데이터 로딩 테스트
                    indicators_df = self.technical_indicators_service.read_indicators_csv(ticker, 'KOSPI', 'd')
                    if indicators_df.empty:
                        test_result['errors'].append(f"{ticker}: 지표 데이터 로딩 실패")
                        continue
                    
                    test_result['details'][ticker] = {
                        'ohlcv_rows': len(ohlcv_df),
                        'indicators_rows': len(indicators_df),
                        'ohlcv_columns': list(ohlcv_df.columns),
                        'indicators_columns': list(indicators_df.columns)
                    }
                    
                except Exception as e:
                    test_result['errors'].append(f"{ticker}: {str(e)}")
            
            if test_result['errors']:
                test_result['status'] = 'FAIL'
            
            self.logger.info(f"📊 데이터 로딩 테스트 완료: {test_result['status']}")
            
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['errors'].append(f"데이터 로딩 테스트 중 오류: {str(e)}")
            self.logger.error(f"❌ 데이터 로딩 테스트 중 오류: {str(e)}")
        
        return test_result
    
    def test_complete_analysis_flow(self) -> Dict:
        """완전한 분석 플로우 테스트"""
        self.logger.info("🔄 완전한 분석 플로우 테스트 시작")
        
        test_result = {
            'status': 'PASS',
            'details': {},
            'errors': []
        }
        
        try:
            # 테스트용 종목
            test_ticker = '005930.KS'  # 삼성전자
            
            # 1. 데이터 로딩
            ohlcv_df = self.data_reading_service.read_ohlcv_csv(test_ticker, 'd', 'KOSPI')
            indicators_df = self.technical_indicators_service.read_indicators_csv(test_ticker, 'KOSPI', 'd')
            
            if ohlcv_df.empty or indicators_df.empty:
                test_result['status'] = 'FAIL'
                test_result['errors'].append("테스트 데이터 로딩 실패")
                return test_result
            
            # 2. 크로스오버 감지
            crossover_result = self.crossover_detector.detect_all_signals(indicators_df)
            test_result['details']['crossover_detection'] = {
                'status': 'PASS' if crossover_result else 'FAIL',
                'result': crossover_result
            }
            
            # 3. EMA 배열 분석
            latest_data = indicators_df.iloc[-1]
            ema_pattern = self.ema_analyzer.analyze_ema_array(latest_data)
            test_result['details']['ema_analysis'] = {
                'status': 'PASS' if ema_pattern else 'FAIL',
                'pattern': ema_pattern
            }
            
            # 4. 분류 결정
            crossover_info = crossover_result.get('crossover_info', {}) if crossover_result else {}
            proximity_info = crossover_result.get('proximity_info', {}) if crossover_result else {}
            
            classification = self.stock_classifier.determine_advanced_classification(
                test_ticker, latest_data, crossover_info, proximity_info, 'KOSPI'
            )
            test_result['details']['classification'] = {
                'status': 'PASS' if classification else 'FAIL',
                'classification': classification
            }
            
            # 5. 중요도 점수 계산
            crossover_type = crossover_info.get('type', 'none')
            days_since = crossover_info.get('days_since', 0)
            
            importance_score = self.importance_calculator.calculate_advanced_score(
                crossover_type, days_since, proximity_info
            )
            test_result['details']['importance_score'] = {
                'status': 'PASS' if importance_score is not None else 'FAIL',
                'score': importance_score
            }
            
            # 6. 통합 서비스 테스트
            unified_result = self.unified_service.analyze_single_stock_comprehensive(
                test_ticker, 'KOSPI', 'd'
            )
            test_result['details']['unified_service'] = {
                'status': 'PASS' if unified_result else 'FAIL',
                'result': unified_result
            }
            
            # 전체 결과 검증
            if any(detail['status'] == 'FAIL' for detail in test_result['details'].values()):
                test_result['status'] = 'FAIL'
            
            self.logger.info(f"🔄 완전한 분석 플로우 테스트 완료: {test_result['status']}")
            
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['errors'].append(f"분석 플로우 테스트 중 오류: {str(e)}")
            self.logger.error(f"❌ 분석 플로우 테스트 중 오류: {str(e)}")
        
        return test_result
    
    def test_cache_system(self) -> Dict:
        """캐시 시스템 테스트"""
        self.logger.info("💾 캐시 시스템 테스트 시작")
        
        test_result = {
            'status': 'PASS',
            'details': {},
            'errors': []
        }
        
        try:
            # 테스트 데이터
            test_data = {
                'test_key': 'test_value',
                'timestamp': datetime.now().isoformat(),
                'data': {'sample': 'data'}
            }
            
            # 1. 캐시 저장 테스트
            self.cache_service.set_cache('test_key', test_data, expire=60)
            test_result['details']['cache_set'] = {'status': 'PASS'}
            
            # 2. 캐시 읽기 테스트
            cached_data = self.cache_service.get_cache('test_key')
            if cached_data and cached_data.get('test_key') == 'test_value':
                test_result['details']['cache_get'] = {'status': 'PASS'}
            else:
                test_result['details']['cache_get'] = {'status': 'FAIL'}
                test_result['errors'].append("캐시 읽기 실패")
            
            # 3. 캐시 만료 테스트
            self.cache_service.set_cache('expire_test', test_data, expire=1)
            time.sleep(2)  # 1초 후 만료
            expired_data = self.cache_service.get_cache('expire_test')
            if expired_data is None:
                test_result['details']['cache_expire'] = {'status': 'PASS'}
            else:
                test_result['details']['cache_expire'] = {'status': 'FAIL'}
                test_result['errors'].append("캐시 만료 실패")
            
            # 4. 캐시 통계 테스트
            cache_stats = self.cache_service.get_cache_stats()
            test_result['details']['cache_stats'] = {
                'status': 'PASS',
                'stats': cache_stats
            }
            
            # 5. 캐시 정리 테스트
            self.cache_service.clear_cache()
            test_result['details']['cache_clear'] = {'status': 'PASS'}
            
            if test_result['errors']:
                test_result['status'] = 'FAIL'
            
            self.logger.info(f"💾 캐시 시스템 테스트 완료: {test_result['status']}")
            
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['errors'].append(f"캐시 시스템 테스트 중 오류: {str(e)}")
            self.logger.error(f"❌ 캐시 시스템 테스트 중 오류: {str(e)}")
        
        return test_result
    
    def test_error_recovery(self) -> Dict:
        """에러 복구 테스트"""
        self.logger.info("🛠️ 에러 복구 테스트 시작")
        
        test_result = {
            'status': 'PASS',
            'details': {},
            'errors': []
        }
        
        try:
            # 1. 잘못된 종목 코드 테스트
            invalid_ticker = 'INVALID.TICKER'
            try:
                result = self.unified_service.analyze_single_stock_comprehensive(
                    invalid_ticker, 'KOSPI', 'd'
                )
                if result is None or not result:
                    test_result['details']['invalid_ticker'] = {'status': 'PASS'}
                else:
                    test_result['details']['invalid_ticker'] = {'status': 'FAIL'}
                    test_result['errors'].append("잘못된 종목 코드 처리 실패")
            except Exception as e:
                test_result['details']['invalid_ticker'] = {'status': 'PASS', 'error': str(e)}
            
            # 2. 빈 데이터 테스트
            empty_df = pd.DataFrame()
            try:
                crossover_result = self.crossover_detector.detect_all_signals(empty_df)
                if crossover_result is None or not crossover_result:
                    test_result['details']['empty_data'] = {'status': 'PASS'}
                else:
                    test_result['details']['empty_data'] = {'status': 'FAIL'}
                    test_result['errors'].append("빈 데이터 처리 실패")
            except Exception as e:
                test_result['details']['empty_data'] = {'status': 'PASS', 'error': str(e)}
            
            # 3. 잘못된 시장 타입 테스트
            try:
                result = self.unified_service.analyze_market_comprehensive('INVALID_MARKET', 'd')
                if result is None or not result:
                    test_result['details']['invalid_market'] = {'status': 'PASS'}
                else:
                    test_result['details']['invalid_market'] = {'status': 'FAIL'}
                    test_result['errors'].append("잘못된 시장 타입 처리 실패")
            except Exception as e:
                test_result['details']['invalid_market'] = {'status': 'PASS', 'error': str(e)}
            
            if test_result['errors']:
                test_result['status'] = 'FAIL'
            
            self.logger.info(f"🛠️ 에러 복구 테스트 완료: {test_result['status']}")
            
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['errors'].append(f"에러 복구 테스트 중 오류: {str(e)}")
            self.logger.error(f"❌ 에러 복구 테스트 중 오류: {str(e)}")
        
        return test_result
    
    def test_performance_benchmark(self) -> Dict:
        """성능 벤치마크 테스트"""
        self.logger.info("⚡ 성능 벤치마크 테스트 시작")
        
        test_result = {
            'status': 'PASS',
            'details': {},
            'errors': []
        }
        
        try:
            # 테스트용 종목 리스트
            test_tickers = ['005930.KS', '000660.KS', '005380.KS']
            
            # 1. 단일 종목 분석 성능 테스트
            performance_metrics = {}
            
            for ticker in test_tickers:
                start_time = time.time()
                try:
                    result = self.unified_service.analyze_single_stock_comprehensive(
                        ticker, 'KOSPI', 'd'
                    )
                    end_time = time.time()
                    
                    performance_metrics[ticker] = {
                        'execution_time': end_time - start_time,
                        'success': result is not None and result != {},
                        'result_size': len(str(result)) if result else 0
                    }
                    
                except Exception as e:
                    performance_metrics[ticker] = {
                        'execution_time': 0,
                        'success': False,
                        'error': str(e)
                    }
            
            # 2. 배치 처리 성능 테스트
            batch_start_time = time.time()
            try:
                batch_result = self.unified_service.analyze_market_comprehensive('KOSPI', 'd')
                batch_end_time = time.time()
                
                performance_metrics['batch_processing'] = {
                    'execution_time': batch_end_time - batch_start_time,
                    'success': batch_result is not None and batch_result != {},
                    'result_size': len(str(batch_result)) if batch_result else 0
                }
                
            except Exception as e:
                performance_metrics['batch_processing'] = {
                    'execution_time': 0,
                    'success': False,
                    'error': str(e)
                }
            
            # 3. 성능 기준 검증
            max_single_time = 5.0  # 단일 종목 분석 최대 5초
            max_batch_time = 30.0  # 배치 처리 최대 30초
            
            for ticker, metrics in performance_metrics.items():
                if ticker != 'batch_processing':
                    if metrics['execution_time'] > max_single_time:
                        test_result['errors'].append(f"{ticker}: 실행 시간 초과 ({metrics['execution_time']:.2f}s)")
                    if not metrics['success']:
                        test_result['errors'].append(f"{ticker}: 분석 실패")
            
            if performance_metrics.get('batch_processing', {}).get('execution_time', 0) > max_batch_time:
                test_result['errors'].append(f"배치 처리: 실행 시간 초과 ({performance_metrics['batch_processing']['execution_time']:.2f}s)")
            
            test_result['details']['performance_metrics'] = performance_metrics
            
            if test_result['errors']:
                test_result['status'] = 'FAIL'
            
            self.logger.info(f"⚡ 성능 벤치마크 테스트 완료: {test_result['status']}")
            
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['errors'].append(f"성능 벤치마크 테스트 중 오류: {str(e)}")
            self.logger.error(f"❌ 성능 벤치마크 테스트 중 오류: {str(e)}")
        
        return test_result
    
    def test_module_integration(self) -> Dict:
        """모듈 간 통합 테스트"""
        self.logger.info("🔗 모듈 간 통합 테스트 시작")
        
        test_result = {
            'status': 'PASS',
            'details': {},
            'errors': []
        }
        
        try:
            # 테스트용 데이터
            test_ticker = '005930.KS'
            ohlcv_df = self.data_reading_service.read_ohlcv_csv(test_ticker, 'd', 'KOSPI')
            indicators_df = self.technical_indicators_service.read_indicators_csv(test_ticker, 'KOSPI', 'd')
            
            if ohlcv_df.empty or indicators_df.empty:
                test_result['status'] = 'FAIL'
                test_result['errors'].append("테스트 데이터 로딩 실패")
                return test_result
            
            latest_data = indicators_df.iloc[-1]
            
            # 1. 크로스오버 감지 + EMA 분석 통합 테스트
            crossover_result = self.crossover_detector.detect_all_signals(indicators_df)
            ema_pattern = self.ema_analyzer.analyze_ema_array(latest_data)
            
            if crossover_result and ema_pattern:
                test_result['details']['crossover_ema_integration'] = {'status': 'PASS'}
            else:
                test_result['details']['crossover_ema_integration'] = {'status': 'FAIL'}
                test_result['errors'].append("크로스오버-EMA 통합 실패")
            
            # 2. 분류 + 점수 계산 통합 테스트
            crossover_info = crossover_result.get('crossover_info', {}) if crossover_result else {}
            proximity_info = crossover_result.get('proximity_info', {}) if crossover_result else {}
            
            classification = self.stock_classifier.determine_advanced_classification(
                test_ticker, latest_data, crossover_info, proximity_info, 'KOSPI'
            )
            
            crossover_type = crossover_info.get('type', 'none')
            days_since = crossover_info.get('days_since', 0)
            
            importance_score = self.importance_calculator.calculate_advanced_score(
                crossover_type, days_since, proximity_info
            )
            
            if classification and importance_score is not None:
                test_result['details']['classification_score_integration'] = {'status': 'PASS'}
            else:
                test_result['details']['classification_score_integration'] = {'status': 'FAIL'}
                test_result['errors'].append("분류-점수 통합 실패")
            
            # 3. 캐시 + 분석 통합 테스트
            cache_key = f"integration_test:{test_ticker}"
            test_data = {
                'classification': classification,
                'importance_score': importance_score,
                'ema_pattern': ema_pattern,
                'crossover_info': crossover_info
            }
            
            self.cache_service.set_cache(cache_key, test_data, expire=300)
            cached_data = self.cache_service.get_cache(cache_key)
            
            if cached_data and cached_data.get('classification') == classification:
                test_result['details']['cache_analysis_integration'] = {'status': 'PASS'}
            else:
                test_result['details']['cache_analysis_integration'] = {'status': 'FAIL'}
                test_result['errors'].append("캐시-분석 통합 실패")
            
            if test_result['errors']:
                test_result['status'] = 'FAIL'
            
            self.logger.info(f"🔗 모듈 간 통합 테스트 완료: {test_result['status']}")
            
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['errors'].append(f"모듈 간 통합 테스트 중 오류: {str(e)}")
            self.logger.error(f"❌ 모듈 간 통합 테스트 중 오류: {str(e)}")
        
        return test_result

def main():
    """메인 테스트 실행 함수"""
    print("🚀 Phase 4 시스템 통합 테스트 시작")
    print("=" * 60)
    
    # 테스트 실행
    integration_test = SystemIntegrationTest()
    results = integration_test.run_complete_integration_test()
    
    # 결과 출력
    print("\n📊 테스트 결과 요약:")
    print(f"전체 상태: {results['overall_status']}")
    print(f"시작 시간: {results['start_time']}")
    print(f"종료 시간: {results['end_time']}")
    
    if results['errors']:
        print(f"\n❌ 오류 목록:")
        for error in results['errors']:
            print(f"  - {error}")
    
    print("\n📋 세부 테스트 결과:")
    for test_name, test_result in results['tests'].items():
        status_icon = "✅" if test_result['status'] == 'PASS' else "❌"
        print(f"  {status_icon} {test_name}: {test_result['status']}")
        
        if test_result.get('errors'):
            for error in test_result['errors']:
                print(f"    - {error}")
    
    print("\n" + "=" * 60)
    print("✅ Phase 4 시스템 통합 테스트 완료")

if __name__ == "__main__":
    main() 