"""
통합 시장 분석 서비스
한 번의 데이터 로드로 모든 분석을 완료하는 통합 서비스
"""

import os
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

class UnifiedMarketAnalysisService:
    """통합 시장 분석 서비스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 의존성 서비스들 초기화
        from services.analysis.crossover.simplified_detector import SimplifiedCrossoverDetector
        from services.analysis.pattern.ema_analyzer import EMAAnalyzer
        from services.analysis.pattern.classification import StockClassifier
        from services.analysis.scoring.importance_calculator import ImportanceCalculator
        # [메모] 2025-08-19: 캐시 사용 경로 단일화
        # 기존 직접 FileBasedCacheService 사용은 주석 보존하고, CacheService 래퍼를 사용합니다.
        # from services.core.cache_service import FileBasedCacheService
        from services.core.cache_service import CacheService
        from services.market.data_reading_service import DataReadingService
        from services.technical_indicators_service import TechnicalIndicatorsService
        
        self.data_reading_service = DataReadingService()
        self.technical_indicators_service = TechnicalIndicatorsService()
        self.unified_detector = SimplifiedCrossoverDetector()
        # 기존 코드: self.cache_service = FileBasedCacheService()
        self.cache_service = CacheService()
        
        # TODO: NewsletterClassificationService - 현재 정의되지 않음, 나중에 정리 필요
        # from services.newsletter_classification_service import NewsletterClassificationService
        # self.classification_service = NewsletterClassificationService()
        
        # TODO: MarketStatusService - 현재 정의되지 않음, 나중에 정리 필요  
        # from services.market.market_status_service import MarketStatusService
        # self.market_status_service = MarketStatusService()
        
        self.ema_analyzer = EMAAnalyzer()
        self.stock_classifier = StockClassifier()
        self.importance_calculator = ImportanceCalculator()
    
    def analyze_market_comprehensive(self, market_type: str, timeframe: str = 'd') -> Dict:
        """
        한 번의 데이터 로드로 모든 분석 완료
        Returns:
            {
                'classification_results': {...},
                'summary': {...},
                'market_type': 'kospi',
                'timeframe': 'd',
                'generated_at': '2024-01-01T00:00:00'
            }
        """
        try:
            # 1. 시장 타입 정규화
            normalized_market = self._normalize_market_type(market_type)
            
            # 2. 캐시 확인
            cache_key = f"market_analysis:{normalized_market}:{timeframe}"
            # [메모] CacheService 래퍼 사용으로 메서드명(get_cache→get) 변경
            cached_result = self.cache_service.get(cache_key)
            if cached_result:
                self.logger.info(f"캐시에서 {normalized_market} 시장 분석 결과 재사용")
                return cached_result
            
            # 3. 종목 리스트 가져오기
            stock_list = self._get_stock_list(normalized_market)
            
            # 4. 배치로 데이터 로딩
            stock_data_cache = self._load_stock_data_batch(stock_list, normalized_market, timeframe)
            
            # 5. 배치로 분석 처리
            analysis_results = self._process_stock_batch(stock_data_cache, normalized_market)
            
            # 6. 분류 결과 생성
            self.logger.info(f"🔍 [UNIFIED] Step 6: _create_classification_results 호출 (analysis_results 개수={len(analysis_results)})")
            classification_results = self._create_classification_results(analysis_results)
            self.logger.info(f"🔍 [UNIFIED] Step 6-1: classification_results 생성 완료, 키들={list(classification_results.keys()) if classification_results else 'Empty'}")
            
            # 7. 시장 요약 생성 (MarketSummaryService 사용)
            from services.core.market_summary_service import MarketSummaryService
            self.logger.info(f"🔍 [UNIFIED] Step 7: MarketSummaryService.create_market_summary 호출")
            market_summary = MarketSummaryService.create_market_summary(classification_results, normalized_market)
            self.logger.info(f"🔍 [UNIFIED] Step 7-1: market_summary 생성 완료: {market_summary}")
            
            # 8. 결과 구성
            result = {
                'classification_results': classification_results,
                'summary': market_summary,
                'market_type': normalized_market,
                'timeframe': timeframe,
                'generated_at': datetime.now().isoformat()
            }
            
            # 9. 캐시 저장
            # [메모] CacheService 래퍼 사용으로 메서드명(set_cache→set) 및 인자명(expire→ttl) 변경
            self.cache_service.set(cache_key, result, ttl=3600)
            
            return result
            
        except Exception as e:
            self.logger.error(f"시장 분석 중 오류: {str(e)}")
            return {}
    
    def analyze_single_stock_comprehensive(self, ticker: str, market_type: str, timeframe: str) -> Dict:
        """단일 종목의 모든 분석을 한 번에 수행"""
        try:
            # 1. 데이터 로딩
            stock_data = self._load_single_stock_data(ticker, market_type, timeframe)
            
            # 2. 분석 처리
            analysis_result = self._analyze_single_stock(ticker, stock_data, market_type)
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"단일 종목 분석 중 오류: {str(e)}")
            return {}
    
    def _normalize_market_type(self, market_type: str) -> str:
        """시장 타입 정규화"""
        market_type = market_type.upper()
        if market_type in ['KOSPI', 'KOSDAQ', 'US']:
            return market_type
        return 'KOSPI'  # 기본값
    
    def _get_stock_list(self, market_type: str) -> List[str]:
        """시장 타입에 따른 종목 리스트 가져오기"""
        try:
            from models import Stock
            
            # 시장 타입에 따라 필터링
            if market_type == 'KOSPI':
                stocks = Stock.query.filter_by(market_type='KOSPI', is_active=True).all()
            elif market_type == 'KOSDAQ':
                stocks = Stock.query.filter_by(market_type='KOSDAQ', is_active=True).all()
            elif market_type == 'US':
                stocks = Stock.query.filter_by(market_type='US', is_active=True).all()
            else:
                stocks = Stock.query.filter_by(is_active=True).all()
            
            ticker_list = [stock.ticker for stock in stocks]
            self.logger.info(f"종목 리스트 조회 성공: {market_type} {len(ticker_list)}개")
            return ticker_list
            
        except Exception as e:
            self.logger.error(f"종목 리스트 가져오기 실패: {e}")
            import traceback
            self.logger.error(f"상세 오류: {traceback.format_exc()}")
            return []
    
    def _load_stock_data_batch(self, tickers: List[str], market_type: str, timeframe: str) -> Dict:
        """배치로 주식 데이터 로딩"""
        stock_data_cache = {}
        
        for ticker in tickers:
            try:
                stock_data = self._load_single_stock_data(ticker, market_type, timeframe)
                if stock_data:
                    stock_data_cache[ticker] = stock_data
            except Exception as e:
                self.logger.error(f"[{ticker}] 단일 주식 데이터 로딩 중 오류: {str(e)}")
                continue
        
        return stock_data_cache
    
    def _load_single_stock_data(self, ticker: str, market_type: str, timeframe: str) -> Dict:
        """단일 주식 데이터 로딩"""
        try:
            # OHLCV 데이터 로딩
            ohlcv_df = self.data_reading_service.read_ohlcv_csv(ticker, market_type, timeframe)
            
            # 지표 데이터 로딩
            indicators_df = self.technical_indicators_service.read_indicators_csv(ticker, market_type, timeframe)
            
            if ohlcv_df.empty or indicators_df.empty:
                return {}
            
            return {
                'ohlcv': ohlcv_df,
                'indicators': indicators_df
            }
            
        except Exception as e:
            self.logger.error(f"[{ticker}] 단일 주식 데이터 로딩 중 오류: {str(e)}")
            return {}
    
    def _process_stock_batch(self, stock_data_cache: Dict, market_type: str) -> Dict:
        """주식 배치 처리"""
        all_results = {}
        
        for ticker, stock_data in stock_data_cache.items():
            try:
                result = self._analyze_single_stock(ticker, stock_data, market_type)
                if result:
                    all_results[ticker] = result
            except Exception as e:
                self.logger.error(f"[{ticker}] 배치 처리 중 오류: {str(e)}")
                continue
        
        return all_results
    
    def _analyze_single_stock(self, ticker: str, stock_data: Dict, market_type: str) -> Dict:
        """단일 주식 분석"""
        try:
            ohlcv_df = stock_data['ohlcv']
            indicators_df = stock_data['indicators']
            
            # 데이터 검증
            if ohlcv_df.empty or indicators_df.empty:
                return None
            
            # 크로스오버 및 패턴 감지 (새로운 SimplifiedCrossoverDetector 사용)
            crossover_info = self.unified_detector.detect_all_signals(indicators_df)
            
            # 최신 데이터 추출
            latest_data = indicators_df.iloc[-1]
            
            # 분류 결정 (새로운 StockClassifier 사용)
            classification = self.stock_classifier.determine_advanced_classification(
                ticker, latest_data, crossover_info.get('ema_analysis', {}), 
                crossover_info.get('macd_analysis', {}), market_type
            )
            
            # 중요도 점수 계산 (새로운 ImportanceCalculator 사용)
            importance_score = self.importance_calculator.calculate_advanced_score(
                crossover_info.get('ema_analysis', {}).get('latest_crossover_type', 'none'),
                crossover_info.get('ema_analysis', {}).get('days_since_crossover', 0),
                {
                    'ema_proximity': crossover_info.get('ema_analysis', {}).get('current_proximity'),
                    'macd_proximity': crossover_info.get('macd_analysis', {}).get('current_proximity')
                }
            )
            
            return {
                'ticker': ticker,
                'classification': classification,
                'crossover_info': crossover_info.get('ema_analysis', {}),
                'proximity_info': {
                    'ema_proximity': crossover_info.get('ema_analysis', {}).get('current_proximity'),
                    'macd_proximity': crossover_info.get('macd_analysis', {}).get('current_proximity')
                },
                # 테이블 표시에 필요한 MACD 최신 크로스오버 정보 포함
                'macd_analysis': crossover_info.get('macd_analysis', {}),
                'importance_score': importance_score,
                'latest_data': latest_data.to_dict()
            }
            
        except Exception as e:
            self.logger.error(f"[{ticker}] 단일 주식 분석 중 오류: {str(e)}")
            return None
    
    def _create_classification_results(self, all_results: Dict) -> Dict:
        """분류 결과 생성 - 26개 세분화 카테고리(S_M_L 코드)"""
        self.logger.info(f"🔍 [CLASSIFICATION] all_results 타입={type(all_results)}, 키 개수={len(all_results)}")
        self.logger.info(f"🔍 [CLASSIFICATION] all_results 키들: {list(all_results.keys())}")

        # 26개 카테고리 초기화
        categories = [
            # S_M_L (EMA5>EMA20>EMA40, 정배열)
            'S_M_L_ema_golden3_today', 'S_M_L_ema_golden3_within_3d', 'S_M_L_macd_dead_within_3d', 'S_M_L_ema_dead1_proximity', 'S_M_L_other',
            # M_S_L
            'M_S_L_ema_dead1_today', 'M_S_L_ema_dead1_within_3d', 'M_S_L_ema_dead2_proximity', 'M_S_L_other',
            # M_L_S
            'M_L_S_ema_dead2_today', 'M_L_S_ema_dead2_within_3d', 'M_L_S_ema_dead3_proximity', 'M_L_S_other',
            # L_M_S (역배열)
            'L_M_S_ema_dead3_today', 'L_M_S_ema_dead3_within_3d', 'L_M_S_macd_golden_within_3d', 'L_M_S_ema_golden1_proximity', 'L_M_S_other',
            # L_S_M
            'L_S_M_ema_golden1_today', 'L_S_M_ema_golden1_within_3d', 'L_S_M_ema_golden2_proximity', 'L_S_M_other',
            # S_L_M
            'S_L_M_ema_golden2_today', 'S_L_M_ema_golden2_within_3d', 'S_L_M_ema_golden3_proximity', 'S_L_M_other',
        ]
        classification_results: Dict[str, List[Dict]] = {k: [] for k in categories}

        def pick_category(ema_order: str, ema_latest: str, ema_days: int, ema_prox: str, macd_latest: str, macd_days: int) -> str:
            # None 가드
            ema_order = ema_order or ''
            ema_latest = ema_latest or ''
            ema_days = 999 if ema_days is None else ema_days
            ema_prox = ema_prox or ''
            macd_latest = macd_latest or ''
            macd_days = 999 if macd_days is None else macd_days

            if ema_order == 'EMA5>EMA20>EMA40':  # S_M_L
                if ema_latest == 'golden_cross3' and ema_days == 0:
                    return 'S_M_L_ema_golden3_today'
                if ema_latest == 'golden_cross3' and 0 <= ema_days <= 3:
                    return 'S_M_L_ema_golden3_within_3d'
                if macd_latest == 'dead_cross' and 0 <= macd_days <= 3:
                    return 'S_M_L_macd_dead_within_3d'
                if ema_prox == 'dead_cross1_proximity':
                    return 'S_M_L_ema_dead1_proximity'
                return 'S_M_L_other'

            if ema_order == 'EMA20>EMA5>EMA40':  # M_S_L
                if ema_latest == 'dead_cross1' and ema_days == 0:
                    return 'M_S_L_ema_dead1_today'
                if ema_latest == 'dead_cross1' and 0 <= ema_days <= 3:
                    return 'M_S_L_ema_dead1_within_3d'
                if ema_prox == 'dead_cross2_proximity':
                    return 'M_S_L_ema_dead2_proximity'
                return 'M_S_L_other'

            if ema_order == 'EMA20>EMA40>EMA5':  # M_L_S
                if ema_latest == 'dead_cross2' and ema_days == 0:
                    return 'M_L_S_ema_dead2_today'
                if ema_latest == 'dead_cross2' and 0 <= ema_days <= 3:
                    return 'M_L_S_ema_dead2_within_3d'
                if ema_prox == 'dead_cross3_proximity':
                    return 'M_L_S_ema_dead3_proximity'
                return 'M_L_S_other'

            if ema_order == 'EMA40>EMA20>EMA5':  # L_M_S (역배열)
                if ema_latest == 'dead_cross3' and ema_days == 0:
                    return 'L_M_S_ema_dead3_today'
                if ema_latest == 'dead_cross3' and 0 <= ema_days <= 3:
                    return 'L_M_S_ema_dead3_within_3d'
                if macd_latest == 'golden_cross' and 0 <= macd_days <= 3:
                    return 'L_M_S_macd_golden_within_3d'
                if ema_prox == 'golden_cross1_proximity':
                    return 'L_M_S_ema_golden1_proximity'
                return 'L_M_S_other'

            if ema_order == 'EMA40>EMA5>EMA20':  # L_S_M
                if ema_latest == 'golden_cross1' and ema_days == 0:
                    return 'L_S_M_ema_golden1_today'
                if ema_latest == 'golden_cross1' and 0 <= ema_days <= 3:
                    return 'L_S_M_ema_golden1_within_3d'
                if ema_prox == 'golden_cross2_proximity':
                    return 'L_S_M_ema_golden2_proximity'
                return 'L_S_M_other'

            if ema_order == 'EMA5>EMA40>EMA20':  # S_L_M
                if ema_latest == 'golden_cross2' and ema_days == 0:
                    return 'S_L_M_ema_golden2_today'
                if ema_latest == 'golden_cross2' and 0 <= ema_days <= 3:
                    return 'S_L_M_ema_golden2_within_3d'
                if ema_prox == 'golden_cross3_proximity':
                    return 'S_L_M_ema_golden3_proximity'
                return 'S_L_M_other'

            # 알 수 없는 배열 → 가장 가까운 범주 없음: 임시로 L_M_S_other로 수용
            return 'L_M_S_other'

        for ticker, result in all_results.items():
            try:
                ema = (result.get('crossover_info') or {})
                macd = (result.get('macd_analysis') or {})
                prox = (result.get('proximity_info') or {})

                ema_order = ema.get('ema_array_order')
                ema_latest = ema.get('latest_crossover_type')
                ema_days = ema.get('days_since_crossover')
                ema_prox = prox.get('ema_proximity')
                macd_latest = macd.get('latest_crossover_type')
                macd_days = macd.get('days_since_crossover')

                key = pick_category(ema_order, ema_latest, ema_days, ema_prox, macd_latest, macd_days)
                item = {
                    'ticker': ticker,
                    'importance_score': result.get('importance_score', 0),
                    'crossover_info': ema,
                    'proximity_info': prox,
                    'macd_analysis': macd,
                    'latest_data': result.get('latest_data', {})
                }
                classification_results[key].append(item)
            except Exception as e:
                self.logger.warning(f"[CLASSIFICATION] {ticker} 분류 실패: {e}")

        # 최종 결과 로깅
        for category, stocks in classification_results.items():
            self.logger.info(f"🔍 [CLASSIFICATION] 최종 결과 - {category}: {len(stocks)}개 종목")

        return classification_results
    
    # _create_market_summary 함수 제거됨 - MarketSummaryService 사용 