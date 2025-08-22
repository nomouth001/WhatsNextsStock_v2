"""
뉴스레터용 종목 분류 서비스
- 크로스오버 근접/발생/1일전/2일전/3일전 분류
- EMA 배열 기반 6단계 상태 분류
- 뉴스레터 테이블 생성
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from services.technical_indicators_service import TechnicalIndicatorsService
from services.market.data_reading_service import DataReadingService
from services.analysis.pattern.ema_analyzer import EMAAnalyzer
from services.analysis.pattern.classification import StockClassifier
from services.analysis.scoring.importance_calculator import ImportanceCalculator


class NewsletterClassificationService:
    def __init__(self):
        self.indicators_service = TechnicalIndicatorsService()
        from services.analysis.crossover.simplified_detector import SimplifiedCrossoverDetector
        self.crossover_service = SimplifiedCrossoverDetector()
        self.data_reading_service = DataReadingService()
        self.ema_analyzer = EMAAnalyzer()
        self.stock_classifier = StockClassifier()
        self.importance_calculator = ImportanceCalculator()
        self.indicators_dir = "static/data"
        # MEMO(2025-08-20): 구조 정리 - 통합 분석 결과(UMAS)만 사용
        # - 아래 계산 메서드들은 더 이상 외부에서 사용하지 않음
        #   classify_all_stocks_for_newsletter, _classify_single_stock,
        #   _classify_single_stock_from_cache, _determine_classification_improved,
        #   _determine_classification_improved_from_cache
        # - 보존 목적: 삭제하지 않고 남겨두며, 호출 경로는 제거됨
    
    def classify_all_stocks_for_newsletter(self, market_type: str = 'kospi', timeframe: str = 'd') -> Dict[str, List[Dict]]:
        """RETIRED(2025-08-20): 통합 서비스(UMAS) 사용. 빈 결과 반환."""
        logging.warning("[RETIRED] classify_all_stocks_for_newsletter는 더 이상 사용되지 않습니다. UMAS 결과를 사용하세요.")
        return {}

    def _classify_single_stock(self, ticker: str, market_type: str, timeframe: str) -> Optional[Dict]:
        """RETIRED: 통합 서비스 사용으로 비활성화되었습니다."""
        logging.warning(f"[RETIRED] _classify_single_stock({ticker})는 더 이상 사용되지 않습니다.")
        return None

    def _classify_single_stock_from_cache(self, ticker: str, cached_data: Dict, market_type: str = 'KOSPI', timeframe: str = 'd') -> Optional[Dict]:
        """RETIRED: 통합 서비스 사용으로 비활성화되었습니다."""
        logging.warning(f"[RETIRED] _classify_single_stock_from_cache({ticker})는 더 이상 사용되지 않습니다.")
        return None
    
    def _determine_classification_improved(self, ticker: str, latest_data: pd.Series, 
                                         crossover_info: Dict, proximity_info: Dict, 
                                         current_date: datetime, market_type: str = 'KOSPI', timeframe: str = 'd') -> Dict:
        """
        새로운 분석 모듈들을 사용하여 분류 결정
        """
        # 기본 정보 - 지표 데이터에는 Close가 없으므로 OHLCV 데이터에서 가져옴
        ohlcv_df = self.data_reading_service.read_ohlcv_csv(ticker, market_type, timeframe)
        current_price = 0
        if not ohlcv_df.empty:
            current_price = ohlcv_df.iloc[-1]['Close']
        
        classification = {
            'ticker': ticker,
            'current_price': current_price,
            'ema5': latest_data.get('EMA5', 0),
            'ema20': latest_data.get('EMA20', 0),
            'ema40': latest_data.get('EMA40', 0),
            'current_date': current_date,
            'category': 'no_crossover',
            'importance_score': 0,
            'crossover_type': None,
            'crossover_date': None,
            'days_since_crossover': None,
            'proximity_info': None,
            'ema_array_pattern': None
        }
        
        # 새로운 모듈들을 사용하여 분석
        # 1. EMA 배열 패턴 분석
        ema_array_pattern = self.ema_analyzer.analyze_ema_array(latest_data)
        classification['ema_array_pattern'] = ema_array_pattern
        
        # 2. 크로스오버 정보 분석
        crossover_type = crossover_info.get('ema_crossover', 'none')
        if crossover_type != 'none':
            days_since = crossover_info.get('ema_days_since', 0)
            classification.update({
                'crossover_type': crossover_type,
                'crossover_date': crossover_info.get('ema_crossover_date'),
                'days_since_crossover': days_since
            })
            
            # 3. 분류 결정 (새로운 StockClassifier 사용)
            category = self.stock_classifier.determine_advanced_classification(
                ticker, latest_data, crossover_info, proximity_info, market_type
            )
            classification['category'] = category
            
            # 4. 중요도 점수 계산 (새로운 ImportanceCalculator 사용)
            importance_score = self.importance_calculator.calculate_advanced_score(
                crossover_type, days_since, proximity_info
            )
            classification['importance_score'] = importance_score
        
        # 5. 근접성 정보 추가
        if proximity_info and proximity_info.get('ema_proximity') != 'none':
            classification['proximity_info'] = proximity_info
        
        return classification
    
    def _determine_classification_improved_from_cache(self, ticker: str, latest_data: pd.Series, 
                                         crossover_info: Dict, proximity_info: Dict, 
                                         current_date: datetime, ohlcv_df: pd.DataFrame,
                                         market_type: str = 'KOSPI', timeframe: str = 'd') -> Dict:
        """
        캐시된 데이터를 사용하여 새로운 분석 모듈들로 분류 결정
        """
        # 기본 정보 - 지표 데이터에는 Close가 없으므로 OHLCV 데이터에서 가져옴
        current_price = 0
        if not ohlcv_df.empty:
            current_price = ohlcv_df.iloc[-1]['Close']
        
        classification = {
            'ticker': ticker,
            'current_price': current_price,
            'ema5': latest_data.get('EMA5', 0),
            'ema20': latest_data.get('EMA20', 0),
            'ema40': latest_data.get('EMA40', 0),
            'current_date': current_date,
            'category': 'no_crossover',
            'importance_score': 0,
            'crossover_type': None,
            'crossover_date': None,
            'days_since_crossover': None,
            'proximity_info': None,
            'ema_array_pattern': None
        }
        
        # 새로운 모듈들을 사용하여 분석
        # 1. EMA 배열 패턴 분석
        ema_array_pattern = self.ema_analyzer.analyze_ema_array(latest_data)
        classification['ema_array_pattern'] = ema_array_pattern
        
        # 2. 크로스오버 정보 분석
        crossover_type = crossover_info.get('ema_crossover', 'none')
        if crossover_type != 'none':
            days_since = crossover_info.get('ema_days_since', 0)
            classification.update({
                'crossover_type': crossover_type,
                'crossover_date': crossover_info.get('ema_crossover_date'),
                'days_since_crossover': days_since
            })
            
            # 3. 분류 결정 (새로운 StockClassifier 사용)
            category = self.stock_classifier.determine_advanced_classification(
                ticker, latest_data, crossover_info, proximity_info, market_type
            )
            classification['category'] = category
            
            # 4. 중요도 점수 계산 (새로운 ImportanceCalculator 사용)
            importance_score = self.importance_calculator.calculate_advanced_score(
                crossover_type, days_since, proximity_info
            )
            classification['importance_score'] = importance_score
        
        # 5. 근접성 정보 추가
        if proximity_info and proximity_info.get('ema_proximity') != 'none':
            classification['proximity_info'] = proximity_info
        
        return classification
    
    def _get_stock_list_from_db(self, market_type: str) -> List[Dict]:
        """
        데이터베이스에서 주식 리스트 가져오기
        """
        try:
            from models import Stock
            from app import db
            
            # 시장 타입에 따라 필터링
            if market_type.lower() == 'kospi':
                stocks = Stock.query.filter_by(market_type='KOSPI', is_active=True).all()
            elif market_type.lower() == 'kosdaq':
                stocks = Stock.query.filter_by(market_type='KOSDAQ', is_active=True).all()
            elif market_type.lower() == 'us':
                stocks = Stock.query.filter_by(market_type='US', is_active=True).all()
            else:
                stocks = Stock.query.filter_by(is_active=True).all()
            
            # 일부 모델에는 name 필드가 없고 company_name만 존재할 수 있으므로 안전하게 처리
            return [
                {
                    'ticker': getattr(stock, 'ticker', None),
                    'name': (getattr(stock, 'company_name', None) or getattr(stock, 'name', None) or getattr(stock, 'ticker', ''))
                }
                for stock in stocks
                if getattr(stock, 'ticker', None)
            ]
            
        except Exception as e:
            logging.error(f"데이터베이스에서 주식 리스트 가져오기 실패: {e}")
            return []
    
    def _get_stock_list(self, market_type: str) -> List[str]:
        """
        종목 리스트를 동적으로 생성 (기존 호환성을 위해 ticker만 반환)
        """
        try:
            # DB에서 종목 리스트 가져오기
            stock_dicts = self._get_stock_list_from_db(market_type)
            
            # ticker만 추출하여 반환 (기존 호환성)
            stock_list = [stock['ticker'] for stock in stock_dicts]
            
            return stock_list
            
        except Exception as e:
            logging.error(f"종목 리스트 생성 실패 ({market_type}): {e}")
            return []
    
    def generate_newsletter_tables(self, classification_results: Dict, market_type: str = 'KOSPI') -> Dict[str, str]:
        """
        뉴스레터용 HTML 테이블 생성
        """
        tables = {}
        
        for category, stocks in classification_results.items():
            if not stocks:
                continue
            
            table_html = self._create_category_table(category, stocks, market_type)
            tables[category] = table_html
        
        return tables
    
    def _get_market_subtype_for_ticker(self, ticker: str) -> str:
        """티커에 따른 시장 하위 타입 반환 (KOSPI/KOSDAQ/US)"""
        try:
            # .KQ로 끝나는 주식은 KOSDAQ
            if ticker.endswith('.KQ'):
                return 'KOSDAQ'
            # .KS로 끝나는 주식은 KOSPI
            elif ticker.endswith('.KS'):
                return 'KOSPI'
            # 6자리 숫자로만 구성된 한국 주식은 기본적으로 KOSPI
            elif ticker.isdigit() and len(ticker) == 6:
                return 'KOSPI'
            # 미국 주식 (알파벳으로 구성)
            elif ticker.isalpha():
                return 'US'
            else:
                return 'KOSPI'  # 기본값
        except Exception as e:
            logging.warning(f"시장 하위 타입 감지 실패 ({ticker}): {e}")
            return 'KOSPI'  # 기본값

    def _get_analysis_url_market(self, ticker: str, market_type: str) -> str:
        """상세분석 URL용 시장 타입 반환"""
        if market_type == 'US':
            return 'US'
        else:
            # 한국 주식의 경우 KOSPI/KOSDAQ 구분
            subtype = self._get_market_subtype_for_ticker(ticker)
            if subtype == 'KOSDAQ':
                return 'kosdaq'
            else:
                return 'kospi'

    def _create_category_table(self, category: str, stocks: List[Dict], market_type: str = 'KOSPI') -> str:
        """
        카테고리별 HTML 테이블 생성
        """
        category_titles = {
            # 골드크로스 관련
            'golden_cross_today': '🚀 오늘 골드크로스 발생 종목',
            'golden_cross_1days_ago': '📈 1일전 골드크로스 종목',
            'golden_cross_2days_ago': '📊 2일전 골드크로스 종목',
            'golden_cross_3days_ago': '📋 3일전 골드크로스 종목',
            'golden_cross_4days_ago': '📋 4일전 골드크로스 종목',
            'golden_cross_5days_ago': '📋 5일전 골드크로스 종목',
            'golden_cross_proximity': '🎯 골드크로스 근접 종목',
            
            # 데드크로스 관련
            'dead_cross_today': '⚠️ 오늘 데드크로스 발생 종목',
            'dead_cross_1days_ago': '📉 1일전 데드크로스 종목',
            'dead_cross_2days_ago': '📊 2일전 데드크로스 종목',
            'dead_cross_3days_ago': '📋 3일전 데드크로스 종목',
            'dead_cross_4days_ago': '📋 4일전 데드크로스 종목',
            'dead_cross_5days_ago': '📋 5일전 데드크로스 종목',
            'dead_cross_proximity': '🎯 데드크로스 근접 종목',
            
            # 일반 크로스오버 (기존 호환성)
            'crossover_today': '🚀 오늘 크로스오버 발생 종목',
            'crossover_1days_ago': '📈 1일전 크로스오버 종목',
            'crossover_2days_ago': '📊 2일전 크로스오버 종목',
            'crossover_3days_ago': '📋 3일전 크로스오버 종목',
            'crossover_4days_ago': '📋 4일전 크로스오버 종목',
            'crossover_5days_ago': '📋 5일전 크로스오버 종목',
            'crossover_proximity': '🎯 크로스오버 근접 종목',
            
            # 이평선 배열 패턴
            'ema_array_EMA5-EMA20-EMA40': '📈 완벽한 상승 배열 (EMA5>EMA20>EMA40)',
            'ema_array_EMA5-EMA40-EMA20': '📈 EMA5 최고점 배열',
            'ema_array_EMA20-EMA5-EMA40': '📈 EMA20 최고점 배열',
            'ema_array_EMA20-EMA40-EMA5': '📉 EMA20 최고점 배열',
            'ema_array_EMA40-EMA5-EMA20': '📉 EMA40 최고점 배열',
            'ema_array_EMA40-EMA20-EMA5': '📉 완벽한 하락 배열 (EMA40>EMA20>EMA5)',
            
            # 신규 26개 카테고리 타이틀
            'S_M_L_ema_golden3_today': 'EMA5>EMA20>EMA40 (정배열) · EMA 골드3 오늘',
            'S_M_L_ema_golden3_within_3d': 'EMA5>EMA20>EMA40 (정배열) · EMA 골드3 ≤3일',
            'S_M_L_macd_dead_within_3d': 'EMA5>EMA20>EMA40 (정배열) · MACD 데드 ≤3일',
            'S_M_L_ema_dead1_proximity': 'EMA5>EMA20>EMA40 (정배열) · EMA 데드1 근접',
            'S_M_L_other': 'EMA5>EMA20>EMA40 (정배열) · 그 외',
            'M_S_L_ema_dead1_today': 'EMA20>EMA5>EMA40 · EMA 데드1 오늘',
            'M_S_L_ema_dead1_within_3d': 'EMA20>EMA5>EMA40 · EMA 데드1 ≤3일',
            'M_S_L_ema_dead2_proximity': 'EMA20>EMA5>EMA40 · EMA 데드2 근접',
            'M_S_L_other': 'EMA20>EMA5>EMA40 · 그 외',
            'M_L_S_ema_dead2_today': 'EMA20>EMA40>EMA5 · EMA 데드2 오늘',
            'M_L_S_ema_dead2_within_3d': 'EMA20>EMA40>EMA5 · EMA 데드2 ≤3일',
            'M_L_S_ema_dead3_proximity': 'EMA20>EMA40>EMA5 · EMA 데드3 근접',
            'M_L_S_other': 'EMA20>EMA40>EMA5 · 그 외',
            'L_M_S_ema_dead3_today': 'EMA40>EMA20>EMA5 (역배열) · EMA 데드3 오늘',
            'L_M_S_ema_dead3_within_3d': 'EMA40>EMA20>EMA5 (역배열) · EMA 데드3 ≤3일',
            'L_M_S_macd_golden_within_3d': 'EMA40>EMA20>EMA5 (역배열) · MACD 골드 ≤3일',
            'L_M_S_ema_golden1_proximity': 'EMA40>EMA20>EMA5 (역배열) · EMA 골드1 근접',
            'L_M_S_other': 'EMA40>EMA20>EMA5 (역배열) · 그 외',
            'L_S_M_ema_golden1_today': 'EMA40>EMA5>EMA20 · EMA 골드1 오늘',
            'L_S_M_ema_golden1_within_3d': 'EMA40>EMA5>EMA20 · EMA 골드1 ≤3일',
            'L_S_M_ema_golden2_proximity': 'EMA40>EMA5>EMA20 · EMA 골드2 근접',
            'L_S_M_other': 'EMA40>EMA5>EMA20 · 그 외',
            'S_L_M_ema_golden2_today': 'EMA5>EMA40>EMA20 · EMA 골드2 오늘',
            'S_L_M_ema_golden2_within_3d': 'EMA5>EMA40>EMA20 · EMA 골드2 ≤3일',
            'S_L_M_ema_golden3_proximity': 'EMA5>EMA40>EMA20 · EMA 골드3 근접',
            'S_L_M_other': 'EMA5>EMA40>EMA20 · 그 외',
            # 기타
            'no_crossover': '📊 크로스오버 없음 종목'
        }
        
        # 카테고리 이름이 예상과 다를 경우 처리
        if category not in category_titles:
            # 숫자일전 패턴 확인
            import re
            days_match = re.search(r'(\d+)days_ago', category)
            if days_match:
                days = days_match.group(1)
                if 'golden_cross' in category:
                    title = f"📈 {days}일전 골드크로스 종목"
                elif 'dead_cross' in category:
                    title = f"📉 {days}일전 데드크로스 종목"
                else:
                    title = f"📋 {category} ({len(stocks)}종목)"
            else:
                title = f"📋 {category} ({len(stocks)}종목)"
        else:
            title = category_titles.get(category, f"📋 {category} ({len(stocks)}종목)")
        
        # 한국장과 미국장에 따른 컬럼 헤더 설정 (대소문자 보정)
        market_upper = (market_type or '').upper()
        if market_upper in ['KOSPI', 'KOSDAQ']:
            # MEMO(2025-08-20): 사용자 요청으로 한국장 테이블에서 "시장구분" 컬럼 제거
            header_html = """
                <thead>
                    <tr>
                        <th>종목코드</th>
                        <th>종목명</th>
                        <th style=\"width:120px\">현재가</th>
                        <th style=\"width:140px\">상세분석</th>
                    </tr>
                </thead>
            """
        else:  # US
            header_html = """
                <thead>
                    <tr>
                        <th>종목코드</th>
                        <th>종목명</th>
                        <th style="width:120px">현재가</th>
                        <th style="width:140px">상세분석</th>
                    </tr>
                </thead>
            """
        
        html = f"""
        <div class="newsletter-category" id="{category}" style="margin-top: 18px; margin-bottom: 10px;">
            <h6 style="margin-bottom: 8px;">{title} ({len(stocks)}종목)</h6>
            <table class="newsletter-table" style="table-layout: fixed; width: 100%;">
                {header_html}
                <tbody>
        """
        
        for stock in stocks:
            ticker = stock.get('ticker') or ''
            stock_name = stock.get('name') or self._get_stock_display_name(ticker)

            # current_price 안전하게 처리 (UMAS latest_data 지원)
            resolved_price = stock.get('current_price')
            if resolved_price is None:
                try:
                    latest_data = stock.get('latest_data') or {}
                    resolved_price = latest_data.get('Close')
                except Exception:
                    resolved_price = None
            try:
                if isinstance(resolved_price, (int, float)):
                    current_price = f"{resolved_price:,.0f}"
                else:
                    current_price = str(resolved_price) if resolved_price is not None else 'N/A'
            except (ValueError, TypeError):
                current_price = 'N/A'
            
            # 시장 타입에 따른 URL 생성 (KOSPI/KOSDAQ/US 구분)
            market_url = self._get_analysis_url_market(ticker, market_type)
            
            if (market_type or '').upper() in ['KOSPI', 'KOSDAQ']:
                # 한국장: 사용자 요청으로 시장구분 배지 제거
                # market_subtype = self._get_market_subtype_for_ticker(ticker)
                # market_badge = self._get_market_badge(market_subtype)
                html += f"""
                    <tr>
                        <td><strong>{ticker}</strong></td>
                        <td>{stock_name}</td>
                        <td>{current_price}</td>
                        <td>
                            <a href="/analysis/ai_analysis/{ticker}/{market_url}" class="btn btn-sm btn-outline-primary" target="_blank">
                                <i class="fas fa-chart-line"></i> 상세분석
                            </a>
                        </td>
                    </tr>
                """
            else:
                # 미국장: 시장구분 컬럼 없음
                html += f"""
                    <tr>
                        <td><strong>{ticker}</strong></td>
                        <td>{stock_name}</td>
                        <td>{current_price}</td>
                        <td>
                            <a href="/analysis/ai_analysis/{ticker}/{market_url}" class="btn btn-sm btn-outline-primary" target="_blank">
                                <i class="fas fa-chart-line"></i> 상세분석
                            </a>
                        </td>
                    </tr>
                """
        
        html += """
                </tbody>
            </table>
        </div>
        """
        
        return html
    
    def _get_importance_badge(self, importance_score: float) -> str:
        """중요도 점수에 따른 배지 색상 반환"""
        if importance_score >= 80:
            return 'danger'  # 빨간색 (매우 중요)
        elif importance_score >= 60:
            return 'warning'  # 노란색 (중요)
        elif importance_score >= 40:
            return 'info'  # 파란색 (보통)
        else:
            return 'secondary'  # 회색 (낮음)
    
    def _get_market_badge(self, market_subtype: str) -> str:
        """시장 구분에 따른 배지 생성"""
        if market_subtype == 'KOSPI':
            return '<span class="badge bg-primary">📈 KOSPI</span>'
        elif market_subtype == 'KOSDAQ':
            return '<span class="badge bg-success">📊 KOSDAQ</span>'
        elif market_subtype == 'US':
            return '<span class="badge bg-info">🇺🇸 US</span>'
        else:
            return '<span class="badge bg-secondary">📋 기타</span>'
    
    # _get_indicator_type: 불필요 컬럼 제거로 미사용
    
    def _get_stock_display_name(self, ticker: str) -> str:
        """
        티커에 대응하는 종목 표시명 반환. DB 조회 실패 시 티커 반환
        """
        try:
            from models import Stock
            stock = Stock.query.filter_by(ticker=ticker).first()
            if stock:
                return getattr(stock, 'company_name', None) or getattr(stock, 'name', None) or ticker
        except Exception:
            pass
        return ticker

    def get_multi_condition_stock_lists(self, timeframe: str = 'd', market: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        다중 조건 필터: 모든 시장(KOSPI/KOSDAQ/US), 일봉(d) 전용
        반환: 조건별 [{ 'ticker': str, 'name': str }] 목록

        조건 목록:
        - uptrend_macd_dead_cross_within_3d
        - uptrend_ema_dead1_proximity
        - uptrend_ema_dead1_today
        - uptrend_ema_dead1_within_3d
        - downtrend_macd_golden_cross_within_3d
        - downtrend_ema_golden1_proximity
        - downtrend_ema_golden1_today
        - downtrend_ema_golden_within_3d
        """
        try:
            # 일봉만 적용
            timeframe = 'd'

            results: Dict[str, List[Dict]] = {
                'uptrend_macd_dead_cross_within_3d': [],
                'uptrend_ema_dead1_proximity': [],
                'uptrend_ema_dead1_today': [],
                'uptrend_ema_dead1_within_3d': [],
                'downtrend_macd_golden_cross_within_3d': [],
                'downtrend_ema_golden1_proximity': [],
                'downtrend_ema_golden1_today': [],
                'downtrend_ema_golden_within_3d': []
            }

            # 중복 방지용 집합
            seen: Dict[str, set] = {key: set() for key in results.keys()}

            # 스캔 대상 시장 결정: 특정 시장 지정 시 해당 시장만, 없으면 전시장(하위호환)
            valid_markets = {'us', 'kospi', 'kosdaq'}
            if market and isinstance(market, str) and market.lower() in valid_markets:
                markets = [market.lower()]
            else:
                markets = ['kospi', 'kosdaq', 'us']

            for market in markets:
                logging.info(f"[MULTI_COND] 시장 처리 시작: {market}")
                stock_list = self._get_stock_list(market)
                if not stock_list:
                    logging.info(f"[MULTI_COND][{market.upper()}] 대상 종목 없음")
                    continue
                logging.info(f"[MULTI_COND][{market.upper()}] 대상 종목 수: {len(stock_list)}")

                for ticker in stock_list:
                    try:
                        indicators_df = self.indicators_service.read_indicators_csv(
                            ticker, market=market, timeframe=timeframe
                        )

                        # 데이터 유효성 검사
                        if not isinstance(indicators_df, pd.DataFrame) or indicators_df.empty:
                            logging.debug(f"[MULTI_COND][{market}:{ticker}] 지표 DF 비어있음/유효하지 않음")
                            continue

                        all_signals = self.crossover_service.detect_all_signals(indicators_df)
                        if not all_signals:
                            logging.debug(f"[MULTI_COND][{market}:{ticker}] 신호 감지 실패")
                            continue

                        ema_analysis = all_signals.get('ema_analysis', {})
                        macd_analysis = all_signals.get('macd_analysis', {})

                        ema_order = ema_analysis.get('ema_array_order')  # 예: 'EMA5>EMA20>EMA40'
                        ema_cross = ema_analysis.get('latest_crossover_type')  # 예: 'golden_cross1', 'dead_cross1'
                        ema_days = ema_analysis.get('days_since_crossover')
                        ema_prox = ema_analysis.get('current_proximity')  # 예: 'dead_cross1_proximity'

                        macd_cross = macd_analysis.get('latest_crossover_type')  # 'golden_cross' | 'dead_cross'
                        macd_days = macd_analysis.get('days_since_crossover')

                        # 표시명 준비
                        name = self._get_stock_display_name(ticker)
                        item = {'ticker': ticker, 'name': name}

                        # 정배열 조건군 (EMA5>EMA20>EMA40)
                        if ema_order == 'EMA5>EMA20>EMA40':
                            # 1) MACD dead cross 3일 이내
                            if macd_cross == 'dead_cross' and macd_days is not None and macd_days <= 3:
                                key = 'uptrend_macd_dead_cross_within_3d'
                                if ticker not in seen[key]:
                                    results[key].append(item)
                                    seen[key].add(ticker)

                            # 2) EMA dead-cross1 근접
                            if ema_prox == 'dead_cross1_proximity':
                                key = 'uptrend_ema_dead1_proximity'
                                if ticker not in seen[key]:
                                    results[key].append(item)
                                    seen[key].add(ticker)

                            # 3) EMA dead-cross1 오늘 발생
                            if ema_cross == 'dead_cross1' and ema_days == 0:
                                key = 'uptrend_ema_dead1_today'
                                if ticker not in seen[key]:
                                    results[key].append(item)
                                    seen[key].add(ticker)

                            # 4) EMA dead-cross1 3일 이내
                            if ema_cross == 'dead_cross1' and (ema_days is not None) and (0 <= ema_days <= 3):
                                key = 'uptrend_ema_dead1_within_3d'
                                if ticker not in seen[key]:
                                    results[key].append(item)
                                    seen[key].add(ticker)

                        # 역배열 조건군 (EMA40>EMA20>EMA5)
                        elif ema_order == 'EMA40>EMA20>EMA5':
                            # 5) MACD golden cross 3일 이내
                            if macd_cross == 'golden_cross' and macd_days is not None and macd_days <= 3:
                                key = 'downtrend_macd_golden_cross_within_3d'
                                if ticker not in seen[key]:
                                    results[key].append(item)
                                    seen[key].add(ticker)

                            # 6) EMA golden-cross1 근접
                            if ema_prox == 'golden_cross1_proximity':
                                key = 'downtrend_ema_golden1_proximity'
                                if ticker not in seen[key]:
                                    results[key].append(item)
                                    seen[key].add(ticker)

                            # 7) EMA golden-cross1 오늘 발생
                            if ema_cross == 'golden_cross1' and ema_days == 0:
                                key = 'downtrend_ema_golden1_today'
                                if ticker not in seen[key]:
                                    results[key].append(item)
                                    seen[key].add(ticker)

                            # 8) EMA golden-cross (any) 3일 이내
                            if (isinstance(ema_cross, str) and ema_cross.startswith('golden_cross') and
                                (ema_days is not None) and (0 <= ema_days <= 3)):
                                key = 'downtrend_ema_golden_within_3d'
                                if ticker not in seen[key]:
                                    results[key].append(item)
                                    seen[key].add(ticker)

                    except Exception as e:
                        logging.warning(f"다중 조건 평가 실패 [{market}:{ticker}]: {e}")
                        continue

            # 최종 카운트 로깅
            try:
                summary_counts = {k: len(v) for k, v in results.items()}
                logging.info(f"[MULTI_COND] 최종 카운트: {summary_counts}")
            except Exception:
                pass
            return results

        except Exception as e:
            logging.error(f"get_multi_condition_stock_lists 오류: {e}")
            return {
                'uptrend_macd_dead_cross_within_3d': [],
                'uptrend_ema_dead1_proximity': [],
                'uptrend_ema_dead1_today': [],
                'uptrend_ema_dead1_within_3d': [],
                'downtrend_macd_golden_cross_within_3d': [],
                'downtrend_ema_golden1_proximity': [],
                'downtrend_ema_golden1_today': [],
                'downtrend_ema_golden_within_3d': []
            }

    # get_newsletter_summary 함수 제거됨 - MarketSummaryService 사용 