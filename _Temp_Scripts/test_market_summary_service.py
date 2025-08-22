"""
MarketSummaryService 테스트 스크립트

새로운 통합 시장 요약 서비스의 기능을 테스트합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.core.market_summary_service import MarketSummaryService
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_market_summary_service():
    """MarketSummaryService 테스트"""
    
    print("=" * 60)
    print("MarketSummaryService 테스트 시작")
    print("=" * 60)
    
    # 테스트용 분류 결과 데이터 생성
    test_classification_results = {
        'golden_cross_today': [
            {'ticker': 'AAPL', 'importance_score': 85},
            {'ticker': 'MSFT', 'importance_score': 78}
        ],
        'golden_cross_1days_ago': [
            {'ticker': 'GOOGL', 'importance_score': 72}
        ],
        'dead_cross_today': [
            {'ticker': 'TSLA', 'importance_score': 65}
        ],
        'dead_cross_1days_ago': [
            {'ticker': 'NVDA', 'importance_score': 58}
        ],
        'golden_cross_proximity': [
            {'ticker': 'AMZN', 'importance_score': 45}
        ],
        'dead_cross_proximity': [
            {'ticker': 'META', 'importance_score': 42}
        ],
        'ema_array_EMA5-EMA20-EMA40': [
            {'ticker': 'NFLX', 'importance_score': 88}
        ],
        'ema_array_EMA40-EMA20-EMA5': [
            {'ticker': 'AMD', 'importance_score': 35}
        ],
        'strong_buy': [
            {'ticker': 'INTC', 'importance_score': 92}
        ],
        'strong_sell': [
            {'ticker': 'ORCL', 'importance_score': 28}
        ],
        'buy_signal': [
            {'ticker': 'CRM', 'importance_score': 75}
        ],
        'sell_signal': [
            {'ticker': 'ADBE', 'importance_score': 38}
        ],
        'watch_up': [
            {'ticker': 'PYPL', 'importance_score': 55}
        ],
        'watch_down': [
            {'ticker': 'UBER', 'importance_score': 48}
        ],
        'no_crossover': [
            {'ticker': 'SHOP', 'importance_score': 25}
        ]
    }
    
    try:
        # 1. 단일 시장 요약 테스트
        print("\n1. 단일 시장 요약 테스트 (US)")
        us_summary = MarketSummaryService.create_market_summary(test_classification_results, 'us')
        
        print("US 시장 요약:")
        for key, value in us_summary.items():
            print(f"  {key}: {value}")
        
        # 2. KOSPI 시장 요약 테스트
        print("\n2. KOSPI 시장 요약 테스트")
        kospi_summary = MarketSummaryService.create_market_summary(test_classification_results, 'kospi')
        
        print("KOSPI 시장 요약:")
        for key, value in kospi_summary.items():
            print(f"  {key}: {value}")
        
        # 3. KOSDAQ 시장 요약 테스트
        print("\n3. KOSDAQ 시장 요약 테스트")
        kosdaq_summary = MarketSummaryService.create_market_summary(test_classification_results, 'kosdaq')
        
        print("KOSDAQ 시장 요약:")
        for key, value in kosdaq_summary.items():
            print(f"  {key}: {value}")
        
        # 4. 통합 시장 요약 테스트
        print("\n4. 통합 시장 요약 테스트")
        combined_summary = MarketSummaryService.create_combined_market_summary(
            test_classification_results,  # KOSPI
            test_classification_results,  # KOSDAQ
            test_classification_results   # US
        )
        
        print("통합 시장 요약:")
        for key, value in combined_summary.items():
            if key in ['kospi', 'kosdaq', 'us']:
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")
        
        # 5. 데이터 유효성 검증 테스트
        print("\n5. 데이터 유효성 검증 테스트")
        is_valid = MarketSummaryService.validate_classification_results(test_classification_results)
        print(f"분류 결과 유효성: {is_valid}")
        
        # 6. 빈 데이터 테스트
        print("\n6. 빈 데이터 테스트")
        empty_summary = MarketSummaryService.create_market_summary({}, 'test')
        print("빈 데이터 요약:")
        for key, value in empty_summary.items():
            print(f"  {key}: {value}")
        
        # 7. 에러 처리 테스트
        print("\n7. 에러 처리 테스트")
        error_summary = MarketSummaryService.create_market_summary(None, 'test')
        print("에러 데이터 요약:")
        for key, value in error_summary.items():
            print(f"  {key}: {value}")
        
        print("\n" + "=" * 60)
        print("모든 테스트 완료!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {str(e)}")
        import traceback
        logger.error(f"스택 트레이스: {traceback.format_exc()}")
        return False

def test_integration_with_existing_services():
    """기존 서비스와의 통합 테스트"""
    
    print("\n" + "=" * 60)
    print("기존 서비스와의 통합 테스트")
    print("=" * 60)
    
    try:
        # UnifiedMarketAnalysisService 테스트
        print("\n1. UnifiedMarketAnalysisService 통합 테스트")
        from services.core.unified_market_analysis_service import UnifiedMarketAnalysisService
        
        unified_service = UnifiedMarketAnalysisService()
        print("✓ UnifiedMarketAnalysisService import 성공")
        
        # SimplifiedCrossoverDetector 테스트
        print("\n2. SimplifiedCrossoverDetector 통합 테스트")
        from services.analysis.crossover.simplified_detector import SimplifiedCrossoverDetector
        
        detector = SimplifiedCrossoverDetector()
        print("✓ SimplifiedCrossoverDetector import 성공")
        
        # NewsletterClassificationService 테스트
        print("\n3. NewsletterClassificationService 통합 테스트")
        from services.newsletter_classification_service import NewsletterClassificationService
        
        newsletter_service = NewsletterClassificationService()
        print("✓ NewsletterClassificationService import 성공")
        
        print("\n✓ 모든 기존 서비스와의 통합 성공!")
        return True
        
    except Exception as e:
        logger.error(f"통합 테스트 중 오류 발생: {str(e)}")
        import traceback
        logger.error(f"스택 트레이스: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("MarketSummaryService 테스트 시작...")
    
    # 기본 기능 테스트
    basic_test_success = test_market_summary_service()
    
    # 통합 테스트
    integration_test_success = test_integration_with_existing_services()
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    print(f"기본 기능 테스트: {'성공' if basic_test_success else '실패'}")
    print(f"통합 테스트: {'성공' if integration_test_success else '실패'}")
    
    if basic_test_success and integration_test_success:
        print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
    else:
        print("\n❌ 일부 테스트가 실패했습니다. 로그를 확인해주세요.")
