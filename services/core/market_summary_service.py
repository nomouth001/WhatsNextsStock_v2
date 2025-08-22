"""
통합 시장 요약 서비스

SimplifiedCrossoverDetector와 UnifiedMarketAnalysisService의 
모든 정보를 통합하여 완전한 시장 요약을 제공합니다.
크로스 갯수 계산은 SimplifiedCrossoverDetector의 시간별 누적 방식을 채택합니다.
"""

from typing import Dict, List, Optional
from datetime import datetime


class MarketSummaryService:
    """통합 시장 요약 서비스"""
    
    @staticmethod
    def create_market_summary(classification_results: Dict, market_type: str) -> Dict:
        """
        시장 요약 정보 생성
        
        Args:
            classification_results: 분류 결과 딕셔너리
                - 최소 요구 키 예시(하나 이상 존재):
                  ['golden_cross_today','dead_cross_today','golden_cross_1days_ago','dead_cross_1days_ago',
                   'golden_cross','death_cross','strong_buy','strong_sell','buy_signal','sell_signal',
                   'watch_up','watch_down','no_crossover']
                - 각 값은 [{'ticker': '005930.KS', ...}, ...] 형식의 리스트 권장
            market_type: 시장 타입 (kospi, kosdaq, us)
            
        Returns:
            Dict: 통합된 시장 요약 정보
        """
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            logger.info(f"🔍 [MARKET_SUMMARY] 입력 받음: classification_results 타입={type(classification_results)}, market_type={market_type}")
            logger.info(f"🔍 [MARKET_SUMMARY] classification_results 키들: {list(classification_results.keys()) if classification_results else 'Empty'}")
            
            # 기본 정보 - 고유한 종목 수만 카운트
            all_tickers = set()
            for category, stocks in classification_results.items():
                if isinstance(stocks, list):
                    logger.info(f"🔍 [MARKET_SUMMARY] 카테고리 {category}: {len(stocks)}개 종목")
                    for stock in stocks:
                        if isinstance(stock, dict) and 'ticker' in stock:
                            all_tickers.add(stock['ticker'])
            total_stocks = len(all_tickers)
            logger.info(f"🔍 [MARKET_SUMMARY] 고유 종목 수: {total_stocks}개")
            
            # SimplifiedCrossoverDetector 방식 (크로스 갯수 계산 - 시간별 누적)
            golden_cross_count = (
                len(classification_results.get('golden_cross_today', [])) +
                len(classification_results.get('golden_cross_1days_ago', []))
            )
            
            dead_cross_count = (
                len(classification_results.get('dead_cross_today', [])) +
                len(classification_results.get('dead_cross_1days_ago', []))
            )
            
            # 크로스오버 근접 종목 수
            crossover_proximity_count = (
                len(classification_results.get('golden_cross_proximity', [])) +
                len(classification_results.get('dead_cross_proximity', []))
            )
            
            # 오늘만 크로스오버 발생 종목 수 (중복 제거)
            crossover_occurred_count = (
                len(classification_results.get('golden_cross_today', [])) +
                len(classification_results.get('dead_cross_today', []))
            )
            
            # 최근 크로스오버 종목 수 (1-3일 전, 중복 제거)
            recent_crossover_count = (
                len(classification_results.get('golden_cross_1days_ago', [])) +
                len(classification_results.get('dead_cross_1days_ago', [])) +
                len(classification_results.get('golden_cross_2days_ago', [])) +
                len(classification_results.get('dead_cross_2days_ago', [])) +
                len(classification_results.get('golden_cross_3days_ago', [])) +
                len(classification_results.get('dead_cross_3days_ago', []))
            )
            
            # EMA 배열 패턴 통계
            ema_array_perfect_rise = len(classification_results.get('ema_array_EMA5-EMA20-EMA40', []))
            ema_array_perfect_fall = len(classification_results.get('ema_array_EMA40-EMA20-EMA5', []))
            
            # UnifiedMarketAnalysisService 방식 (현재 상태 기반)
            strong_buy_count = len(classification_results.get('strong_buy', []))
            strong_sell_count = len(classification_results.get('strong_sell', []))
            
            # 크로스오버 없음 종목 수
            no_crossover_count = len(classification_results.get('no_crossover', []))
            
            # 🔍 카운팅 검증 로직 (2025-01-11 리팩토링 완료 기념)
            MarketSummaryService._validate_counting_logic(
                total_stocks, crossover_occurred_count, no_crossover_count, 
                classification_results, market_type
            )
            buy_signal_count = len(classification_results.get('buy_signal', []))
            sell_signal_count = len(classification_results.get('sell_signal', []))
            watch_up_count = len(classification_results.get('watch_up', []))
            watch_down_count = len(classification_results.get('watch_down', []))
            
            # 크로스오버 없음 종목 수
            no_crossover_count = len(classification_results.get('no_crossover', []))
            
            # 카테고리별 개수 집계 (신규 26개 카테고리 포함, 존재하는 키만 카운트)
            category_counts = {}
            try:
                for k, v in (classification_results or {}).items():
                    if isinstance(v, list):
                        category_counts[k] = len(v)
            except Exception:
                category_counts = {}

            # 통합된 시장 요약 정보 생성
            market_summary = {
                'market_type': market_type,
                'total_stocks': total_stocks,
                
                # SimplifiedCrossoverDetector 방식 (크로스 갯수 계산)
                'crossover_proximity_count': crossover_proximity_count,
                'crossover_occurred_count': crossover_occurred_count,
                'recent_crossover_count': recent_crossover_count,
                'golden_cross_count': golden_cross_count,
                'dead_cross_count': dead_cross_count,
                'ema_array_perfect_rise': ema_array_perfect_rise,
                'ema_array_perfect_fall': ema_array_perfect_fall,
                
                # UnifiedMarketAnalysisService 방식 (현재 상태 기반)
                'strong_buy_count': strong_buy_count,
                'strong_sell_count': strong_sell_count,
                'buy_signal_count': buy_signal_count,
                'sell_signal_count': sell_signal_count,
                'watch_up_count': watch_up_count,
                'watch_down_count': watch_down_count,
                'no_crossover_count': no_crossover_count,
                
                # 통일된 날짜 형식
                'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                # 신규: 카테고리별 개수
                'category_counts': category_counts
            }
            
            return market_summary
            
        except Exception as e:
            # 에러 발생 시 기본값 반환
            return MarketSummaryService._create_fallback_summary(market_type, str(e))
    
    @staticmethod
    def create_combined_market_summary(kospi_results: Dict, kosdaq_results: Dict, us_results: Dict) -> Dict:
        """
        통합 시장 요약 정보 생성 (KOSPI, KOSDAQ, US 전체)
        
        Args:
            kospi_results: KOSPI 분류 결과
            kosdaq_results: KOSDAQ 분류 결과  
            us_results: US 분류 결과
            
        Returns:
            Dict: 통합된 전체 시장 요약 정보
        """
        try:
            # 각 시장별 요약 생성
            kospi_summary = MarketSummaryService.create_market_summary(kospi_results, 'kospi')
            kosdaq_summary = MarketSummaryService.create_market_summary(kosdaq_results, 'kosdaq')
            us_summary = MarketSummaryService.create_market_summary(us_results, 'us')
            
            # 전체 통계 집계
            combined_summary = {
                'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_markets': 3,
                'kospi': kospi_summary,
                'kosdaq': kosdaq_summary,
                'us': us_summary,
                
                # 전체 시장 통합 통계
                'total_stocks_all_markets': (
                    kospi_summary.get('total_stocks', 0) +
                    kosdaq_summary.get('total_stocks', 0) +
                    us_summary.get('total_stocks', 0)
                ),
                'total_golden_cross_all_markets': (
                    kospi_summary.get('golden_cross_count', 0) +
                    kosdaq_summary.get('golden_cross_count', 0) +
                    us_summary.get('golden_cross_count', 0)
                ),
                'total_dead_cross_all_markets': (
                    kospi_summary.get('dead_cross_count', 0) +
                    kosdaq_summary.get('dead_cross_count', 0) +
                    us_summary.get('dead_cross_count', 0)
                ),
                'total_crossover_proximity_all_markets': (
                    kospi_summary.get('crossover_proximity_count', 0) +
                    kosdaq_summary.get('crossover_proximity_count', 0) +
                    us_summary.get('crossover_proximity_count', 0)
                )
            }
            
            return combined_summary
            
        except Exception as e:
            # 에러 발생 시 기본값 반환
            return MarketSummaryService._create_fallback_summary('combined', str(e))
    
    @staticmethod
    def _create_fallback_summary(market_type: str, error_message: str) -> Dict:
        """
        에러 발생 시 기본 시장 요약 정보 생성
        
        Args:
            market_type: 시장 타입
            error_message: 에러 메시지
            
        Returns:
            Dict: 기본 시장 요약 정보
        """
        return {
            'market_type': market_type,
            'total_stocks': 0,
            'crossover_proximity_count': 0,
            'crossover_occurred_count': 0,
            'recent_crossover_count': 0,
            'golden_cross_count': 0,
            'dead_cross_count': 0,
            'ema_array_perfect_rise': 0,
            'ema_array_perfect_fall': 0,
            'strong_buy_count': 0,
            'strong_sell_count': 0,
            'buy_signal_count': 0,
            'sell_signal_count': 0,
            'watch_up_count': 0,
            'watch_down_count': 0,
            'no_crossover_count': 0,
            'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'error_message': error_message,
            'is_fallback': True
        }
    
    @staticmethod
    def validate_classification_results(classification_results: Dict) -> bool:
        """
        분류 결과 데이터 유효성 검증
        
        Args:
            classification_results: 분류 결과 딕셔너리
            
        Returns:
            bool: 유효성 여부
        """
        if not isinstance(classification_results, dict):
            return False
        
        # 최소한 하나의 분류 카테고리가 있어야 함
        valid_categories = [
            'golden_cross_today', 'dead_cross_today',
            'golden_cross_1days_ago', 'dead_cross_1days_ago',
            'golden_cross', 'death_cross',
            'strong_buy', 'strong_sell',
            'buy_signal', 'sell_signal',
            'watch_up', 'watch_down',
            'no_crossover'
        ]
        
        return any(category in classification_results for category in valid_categories)
    
    @staticmethod
    def _validate_counting_logic(total_stocks: int, crossover_occurred_count: int, 
                               no_crossover_count: int, classification_results: Dict, 
                               market_type: str) -> bool:
        """
        카운팅 로직 검증 - 2025-01-11 리팩토링 완료 기념
        
        수학적 검증:
        - 전체 종목 수 = 크로스오버 발생 종목 + 크로스오버 없음 종목
        - 중복 카운팅 방지 검증
        
        Args:
            total_stocks: 전체 종목 수
            crossover_occurred_count: 오늘 크로스오버 발생 종목 수
            no_crossover_count: 크로스오버 없음 종목 수
            classification_results: 분류 결과
            market_type: 시장 타입
        
        Returns:
            bool: 검증 통과 여부
        """
        try:
            # 1. 기본 수학적 검증
            calculated_total = crossover_occurred_count + no_crossover_count
            
            if calculated_total != total_stocks:
                import logging
                logging.warning(
                    f"🚨 [{market_type}] 카운팅 불일치 발견! "
                    f"전체: {total_stocks}, "
                    f"크로스오버: {crossover_occurred_count}, "
                    f"크로스오버없음: {no_crossover_count}, "
                    f"계산합계: {calculated_total}"
                )
                # 검증 실패해도 시스템은 계속 동작 (경고만)
                return False
            
            # 2. 중복 종목 검증
            all_tickers_in_categories = set()
            duplicate_tickers = set()
            
            for category, stocks in classification_results.items():
                if isinstance(stocks, list):
                    for stock in stocks:
                        if isinstance(stock, dict) and 'ticker' in stock:
                            ticker = stock['ticker']
                            if ticker in all_tickers_in_categories:
                                duplicate_tickers.add(ticker)
                            all_tickers_in_categories.add(ticker)
            
            if duplicate_tickers:
                import logging
                logging.warning(
                    f"🚨 [{market_type}] 중복 종목 발견: {list(duplicate_tickers)[:5]}..."
                )
                return False
            
            # 3. 검증 통과
            import logging
            logging.info(
                f"✅ [{market_type}] 카운팅 검증 통과! "
                f"전체: {total_stocks} = 크로스오버: {crossover_occurred_count} + 없음: {no_crossover_count}"
            )
            return True
            
        except Exception as e:
            import logging
            logging.error(f"카운팅 검증 중 오류: {e}")
            return False
