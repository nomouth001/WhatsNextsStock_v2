import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import pandas as pd
from services.newsletter_classification_service import NewsletterClassificationService
from models import db, NewsletterContent

class NewsletterGenerationService:
    def __init__(self):
        self.classification_service = NewsletterClassificationService()
        self.logger = logging.getLogger(__name__)
        
    def generate_kospi_newsletter(self, timeframe: str = 'd', user_id: Optional[int] = None) -> Dict:
        """KOSPI 뉴스레터 생성"""
        try:
            # [구조 정리] 통합 서비스 결과만 사용
            from services.core.unified_market_analysis_service import UnifiedMarketAnalysisService
            unified_service = UnifiedMarketAnalysisService()
            analysis_result = unified_service.analyze_market_comprehensive('KOSPI', timeframe)

            classification_results = analysis_result.get('classification_results', {})
            summary = analysis_result.get('summary', {})

            # 뉴스레터 HTML 생성
            newsletter_html = self._create_newsletter_html(classification_results, 'kospi', timeframe)
            category_summary_html = self._create_category_summary_html(classification_results, 'kospi')
            
            newsletter_data = {
                'html': newsletter_html,
                'summary': summary,
                'market': 'kospi',
                'timeframe': timeframe,
                'generated_at': datetime.now().isoformat(),
                'category_summary_html': category_summary_html
            }
            
            # 데이터베이스에 저장 (통합 저장 서비스 사용)
            if user_id:
                try:
                    from services.newsletter_storage_service import NewsletterStorageService
                    NewsletterStorageService().save_to_db(user_id, newsletter_data, 'kospi')
                except Exception:
                    # 기존 경로 폴백
                    self._save_newsletter_content(user_id, newsletter_data, 'kospi')
            
            return newsletter_data
        except Exception as e:
            self.logger.error(f"KOSPI 뉴스레터 생성 중 오류: {str(e)}")
            raise
    
    def generate_kosdaq_newsletter(self, timeframe: str = 'd', user_id: Optional[int] = None) -> Dict:
        """KOSDAQ 뉴스레터 생성"""
        try:
            # [구조 정리] 통합 서비스 결과만 사용
            from services.core.unified_market_analysis_service import UnifiedMarketAnalysisService
            unified_service = UnifiedMarketAnalysisService()
            analysis_result = unified_service.analyze_market_comprehensive('KOSDAQ', timeframe)

            classification_results = analysis_result.get('classification_results', {})
            summary = analysis_result.get('summary', {})

            # 뉴스레터 HTML 생성
            newsletter_html = self._create_newsletter_html(classification_results, 'kosdaq', timeframe)
            category_summary_html = self._create_category_summary_html(classification_results, 'kosdaq')
            
            newsletter_data = {
                'html': newsletter_html,
                'summary': summary,
                'market': 'kosdaq',
                'timeframe': timeframe,
                'generated_at': datetime.now().isoformat(),
                'category_summary_html': category_summary_html
            }
            
            # 데이터베이스에 저장 (통합 저장 서비스 사용)
            if user_id:
                try:
                    from services.newsletter_storage_service import NewsletterStorageService
                    NewsletterStorageService().save_to_db(user_id, newsletter_data, 'kosdaq')
                except Exception:
                    self._save_newsletter_content(user_id, newsletter_data, 'kosdaq')
            
            return newsletter_data
        except Exception as e:
            self.logger.error(f"KOSDAQ 뉴스레터 생성 중 오류: {str(e)}")
            raise
    
    def generate_us_newsletter(self, timeframe: str = 'd', user_id: Optional[int] = None) -> Dict:
        """US 뉴스레터 생성"""
        try:
            # [구조 정리] 통합 서비스 결과만 사용
            from services.core.unified_market_analysis_service import UnifiedMarketAnalysisService
            unified_service = UnifiedMarketAnalysisService()
            analysis_result = unified_service.analyze_market_comprehensive('US', timeframe)

            classification_results = analysis_result.get('classification_results', {})
            summary = analysis_result.get('summary', {})

            # 뉴스레터 HTML 생성
            newsletter_html = self._create_newsletter_html(classification_results, 'us', timeframe)
            category_summary_html = self._create_category_summary_html(classification_results, 'us')
            
            newsletter_data = {
                'html': newsletter_html,
                'summary': summary,
                'market': 'us',
                'timeframe': timeframe,
                'generated_at': datetime.now().isoformat(),
                'category_summary_html': category_summary_html
            }
            
            # 데이터베이스에 저장 (통합 저장 서비스 사용)
            if user_id:
                try:
                    from services.newsletter_storage_service import NewsletterStorageService
                    NewsletterStorageService().save_to_db(user_id, newsletter_data, 'us')
                except Exception:
                    self._save_newsletter_content(user_id, newsletter_data, 'us')
            
            return newsletter_data
        except Exception as e:
            self.logger.error(f"US 뉴스레터 생성 중 오류: {str(e)}")
            raise
    
    def generate_combined_newsletter(self, timeframe: str = 'd', primary_market: str = 'kospi', user_id: Optional[int] = None) -> Dict:
        """통합 뉴스레터 생성 (KOSPI, KOSDAQ, 미국장 모두 포함)"""
        try:
            # [구조 정리] 통합 서비스 결과만 사용
            from services.core.unified_market_analysis_service import UnifiedMarketAnalysisService
            unified_service = UnifiedMarketAnalysisService()

            kospi_analysis = unified_service.analyze_market_comprehensive('KOSPI', timeframe)
            kosdaq_analysis = unified_service.analyze_market_comprehensive('KOSDAQ', timeframe)
            us_analysis = unified_service.analyze_market_comprehensive('US', timeframe)

            kospi_results = kospi_analysis.get('classification_results', {})
            kosdaq_results = kosdaq_analysis.get('classification_results', {})
            us_results = us_analysis.get('classification_results', {})
            
            # 통합 뉴스레터 HTML 생성
            newsletter_html = self._create_combined_newsletter_html(
                kospi_results, kosdaq_results, us_results, primary_market, timeframe
            )
            
            # 통합 요약 정보 생성 (통합 서비스 결과 사용)
            combined_summary = self._create_combined_summary_from_admin(
                kospi_analysis.get('summary', {}), 
                kosdaq_analysis.get('summary', {}), 
                us_analysis.get('summary', {})
            )
            
            newsletter_data = {
                'html': newsletter_html,
                'summary': combined_summary,
                'market': 'COMBINED',
                'primary_market': primary_market,
                'timeframe': timeframe,
                'generated_at': datetime.now().isoformat(),
                # 상단 카테고리 요약(시장별)
                'kospi_category_summary_html': self._create_category_summary_html(kospi_results, 'kospi'),
                'kosdaq_category_summary_html': self._create_category_summary_html(kosdaq_results, 'kosdaq'),
                'us_category_summary_html': self._create_category_summary_html(us_results, 'us'),
                # 이메일 전용: 스크립트 없는 고정형 본문 생성
                'email_html': self._create_email_combined_body_html(
                    kospi_results, kosdaq_results, us_results, combined_summary
                )
            }
            
            # 데이터베이스에 저장 (통합 저장 서비스 사용)
            if user_id:
                try:
                    from services.newsletter_storage_service import NewsletterStorageService
                    NewsletterStorageService().save_to_db(user_id, newsletter_data, 'combined')
                except Exception:
                    self._save_newsletter_content(user_id, newsletter_data, 'combined')
            
            return newsletter_data
        except Exception as e:
            self.logger.error(f"통합 뉴스레터 생성 중 오류: {str(e)}")
            raise

    def _create_email_combined_body_html(
        self,
        kospi_results: Dict,
        kosdaq_results: Dict,
        us_results: Dict,
        combined_summary: Dict,
    ) -> str:
        """이메일 친화적 고정형 본문(자바스크립트 없이) 생성.
        - 상단에 간단한 시장 요약 카드 3개
        - 각 시장 섹션을 모두 세로로 노출
        - 표 내용은 기존 테이블 생성 함수를 재사용
        """
        try:
            # 시장별 테이블 HTML 생성 재사용
            kospi_tables = "".join(self.classification_service.generate_newsletter_tables(kospi_results, 'kospi').values())
            kosdaq_tables = "".join(self.classification_service.generate_newsletter_tables(kosdaq_results, 'kosdaq').values())
            us_tables = "".join(self.classification_service.generate_newsletter_tables(us_results, 'US').values())

            def safe_get(summary: Dict, market_key: str, key: str) -> int:
                try:
                    return int((summary.get(market_key) or {}).get(key, 0))
                except Exception:
                    return 0

            # 간단 요약(전체 종목 수만 우선 표시; 확장 가능)
            kospi_total = safe_get(combined_summary, 'kospi', 'total_stocks')
            kosdaq_total = safe_get(combined_summary, 'kosdaq', 'total_stocks')
            us_total = safe_get(combined_summary, 'us', 'total_stocks')

            html = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, 'Apple SD Gothic Neo', 'Noto Sans KR', '맑은 고딕', sans-serif;">
              <div style="margin:12px 0 16px 0;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="border-collapse:collapse;">
                  <tr>
                    <td style="width:33.33%; padding:6px;">
                      <div style="border:1px solid #e5e7eb; border-radius:6px; padding:10px;">
                        <div style="font-weight:600; margin-bottom:4px;">📈 KOSPI</div>
                        <div style="color:#2563eb; font-size:18px; font-weight:700;">{kospi_total}</div>
                        <div style="color:#6b7280; font-size:12px;">전체 종목</div>
                      </div>
                    </td>
                    <td style="width:33.33%; padding:6px;">
                      <div style="border:1px solid #e5e7eb; border-radius:6px; padding:10px;">
                        <div style="font-weight:600; margin-bottom:4px;">📊 KOSDAQ</div>
                        <div style="color:#2563eb; font-size:18px; font-weight:700;">{kosdaq_total}</div>
                        <div style="color:#6b7280; font-size:12px;">전체 종목</div>
                      </div>
                    </td>
                    <td style="width:33.33%; padding:6px;">
                      <div style="border:1px solid #e5e7eb; border-radius:6px; padding:10px;">
                        <div style="font-weight:600; margin-bottom:4px;">🇺🇸 US Market</div>
                        <div style="color:#2563eb; font-size:18px; font-weight:700;">{us_total}</div>
                        <div style="color:#6b7280; font-size:12px;">전체 종목</div>
                      </div>
                    </td>
                  </tr>
                </table>
              </div>

              <div style="margin-top:8px;">
                <h3 style="margin:14px 0 8px 0;">📈 KOSPI 주식 분류</h3>
                {kospi_tables}
              </div>

              <div style="margin-top:8px;">
                <h3 style="margin:14px 0 8px 0;">📊 KOSDAQ 주식 분류</h3>
                {kosdaq_tables}
              </div>

              <div style="margin-top:8px;">
                <h3 style="margin:14px 0 8px 0;">🇺🇸 US Market 주식 분류</h3>
                {us_tables}
              </div>
            </div>
            """
            return html
        except Exception as e:
            self.logger.error(f"이메일용 본문 생성 실패: {e}")
            return ""

    def create_newsletter_html(self, classification_results: Dict, market: str, timeframe: str) -> str:
        """공개용: 라우트에서 사용하는 HTML 생성 래퍼"""
        return self._create_newsletter_html(classification_results, market, timeframe)
    
    def _create_newsletter_html(self, classification_results: Dict, market: str, timeframe: str) -> str:
        """단일 시장 뉴스레터 HTML 생성 (다른 서비스들의 결과 조합)"""
        try:
            # 분류 서비스에서 테이블 생성
            tables_dict = self.classification_service.generate_newsletter_tables(classification_results, market)

            # 테이블 HTML 조합
            tables_html = ""
            for category, table_html in tables_dict.items():
                tables_html += table_html

            return tables_html
            
        except Exception as e:
            self.logger.error(f"뉴스레터 HTML 생성 중 오류: {str(e)}")
            return f"<div class='alert alert-danger'>뉴스레터 생성 중 오류가 발생했습니다: {str(e)}</div>"

    def _create_category_summary_html(self, classification_results: Dict, market: str) -> str:
        """상단 카드에 표시할 카테고리 요약 버튼 묶음 생성"""
        try:
            if not classification_results or not isinstance(classification_results, dict):
                return ""

            # 26개 카테고리 한글 타이틀 매핑 (뉴스레터 테이블과 동일 매핑)
            titles = {
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
            }

            buttons: List[str] = []
            for key in sorted(classification_results.keys()):
                items = classification_results.get(key, []) or []
                count = len(items)
                if count <= 0:
                    continue
                label = titles.get(key, key)
                buttons.append(
                    f"<a href='#{key}' class='btn btn-sm btn-outline-secondary me-2 mb-2'>{label} <span class='badge bg-primary'>{count}</span></a>"
                )

            if not buttons:
                return ""

            return (
                "<div class='newsletter-summary mb-2'>"
                "<div class='d-flex flex-wrap'>" + "".join(buttons) + "</div>"
                "</div>"
            )
        except Exception:
            return ""
    
    def _create_combined_newsletter_html(self, kospi_results: Dict, kosdaq_results: Dict, us_results: Dict, 
                                       primary_market: str, timeframe: str) -> str:
        """통합 뉴스레터 HTML 생성 (다른 서비스들의 결과 조합)"""
        try:
            # 각 시장별 테이블 생성
            kospi_tables_dict = self.classification_service.generate_newsletter_tables(kospi_results, 'kospi')
            kosdaq_tables_dict = self.classification_service.generate_newsletter_tables(kosdaq_results, 'kosdaq')
            us_tables_dict = self.classification_service.generate_newsletter_tables(us_results, 'US')
            
            # 테이블 HTML 조합
            kospi_tables = ""
            for category, table_html in kospi_tables_dict.items():
                kospi_tables += table_html
                
            kosdaq_tables = ""
            for category, table_html in kosdaq_tables_dict.items():
                kosdaq_tables += table_html
                
            us_tables = ""
            for category, table_html in us_tables_dict.items():
                us_tables += table_html
            
            # 시장별 탭 구조 생성
            html_template = f"""
            <div class="newsletter-container">
            <div class="market-tabs">
                    <button class="market-tab active" onclick="showMarket('kospi')">
                        📈 KOSPI
                    </button>
                    <button class="market-tab" onclick="showMarket('kosdaq')">
                        📊 KOSDAQ
                </button>
                    <button class="market-tab" onclick="showMarket('us')">
                        🇺🇸 US Market
                </button>
            </div>
            
                <div id="market-kospi" class="market-content">
                    <h2>📈 KOSPI 주식 분류</h2>
                    {kospi_tables}
                </div>
                
                <div id="market-kosdaq" class="market-content" style="display: none;">
                    <h2>📊 KOSDAQ 주식 분류</h2>
                    {kosdaq_tables}
            </div>
            
                <div id="market-us" class="market-content" style="display: none;">
                    <h2>🇺🇸 US Market 주식 분류</h2>
                    {us_tables}
                </div>
            </div>
            
            <script>
                function showMarket(market) {{
                    console.log('showMarket called with:', market);
                    
                    // 모든 탭 비활성화
                    document.querySelectorAll('.market-tab').forEach(tab => {{
                        tab.classList.remove('active');
                    }});
                    document.querySelectorAll('.market-content').forEach(content => {{
                        content.style.display = 'none';
                    }});
                    
                    // 선택된 탭 활성화
                    event.target.classList.add('active');
                    const targetContent = document.getElementById('market-' + market);
                    if (targetContent) {{
                        targetContent.style.display = 'block';
                        console.log('Market content shown:', market);
                    }} else {{
                        console.error('Market content not found:', 'market-' + market);
                    }}
                }}
                
                // 페이지 로드 시 기본 탭 설정
                document.addEventListener('DOMContentLoaded', function() {{
                    console.log('DOM loaded, setting default tab');
                    // 기본 탭을 KOSPI로 설정
                    const defaultTab = document.querySelector('.market-tab');
                    if (defaultTab) {{
                        defaultTab.classList.add('active');
                    }}
                    const defaultContent = document.getElementById('market-kospi');
                    if (defaultContent) {{
                        defaultContent.style.display = 'block';
                    }}
                }});
            </script>
        """
            
            return html_template
            
        except Exception as e:
            self.logger.error(f"통합 뉴스레터 HTML 생성 중 오류: {str(e)}")
            return f"<div class='alert alert-danger'>통합 뉴스레터 생성 중 오류가 발생했습니다: {str(e)}</div>"
    
    def _generate_summary_html(self, summary: Dict) -> str:
        """요약 정보 HTML 생성"""
        if not summary:
            return "<p>요약 정보를 불러올 수 없습니다.</p>"
        
        html_parts = []
        
        # 카테고리별 표시명 매핑
        category_names = {
            'golden_cross_proximity_count': '골드크로스 근접',
            'dead_cross_proximity_count': '데드크로스 근접',
            'golden_cross_today_count': '오늘 골드크로스',
            'dead_cross_today_count': '오늘 데드크로스',
            'golden_cross_recent_count': '최근 골드크로스',
            'dead_cross_recent_count': '최근 데드크로스',
            'bullish_array_count': '강세 배열',
            'bearish_array_count': '약세 배열',
            'neutral_array_count': '중립 배열',
            'total_stocks': '전체 종목'
        }
        
        for category, count in summary.items():
            if category in category_names and count > 0:  # 0개인 카테고리는 표시하지 않음
                # 카테고리 ID 생성 (하이퍼링크용)
                category_id = category.replace('_count', '')
                html_parts.append(f"""
                <div class="summary-item">
                    <h3><a href="#{category_id}" class="summary-link">{category_names[category]}</a></h3>
                    <div class="count">{count}</div>
                </div>
                """)
        
        return ''.join(html_parts)
    
    def _create_combined_summary(self, kospi_results: Dict, kosdaq_results: Dict, us_results: Dict) -> Dict:
        """통합 요약 정보 생성 (crossover_detection_service 사용)"""
        try:
            # crossover_detection_service의 통합 요약 기능 사용
            return self.classification_service.crossover_service.get_combined_market_summary(
                kospi_results, kosdaq_results, us_results
            )
        except Exception as e:
            self.logger.error(f"통합 요약 정보 생성 중 오류: {str(e)}")
            return {
                'error': str(e),
                'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def _create_combined_summary_from_admin(self, kospi_summary: Dict, kosdaq_summary: Dict, us_summary: Dict) -> Dict:
        """어드민 홈의 요약 정보들을 통합"""
        try:
            combined_summary = {
                'market_type': 'COMBINED',
                'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'kospi': kospi_summary,
                'kosdaq': kosdaq_summary,
                'us': us_summary,
                'total_stocks': kospi_summary.get('total_stocks', 0) + kosdaq_summary.get('total_stocks', 0) + us_summary.get('total_stocks', 0),
                'total_crossover_proximity': kospi_summary.get('crossover_proximity_count', 0) + kosdaq_summary.get('crossover_proximity_count', 0) + us_summary.get('crossover_proximity_count', 0),
                'total_crossover_occurred': kospi_summary.get('crossover_occurred_count', 0) + kosdaq_summary.get('crossover_occurred_count', 0) + us_summary.get('crossover_occurred_count', 0),
                'total_recent_crossover': kospi_summary.get('recent_crossover_count', 0) + kosdaq_summary.get('recent_crossover_count', 0) + us_summary.get('recent_crossover_count', 0),
                'total_golden_cross': kospi_summary.get('golden_cross_count', 0) + kosdaq_summary.get('golden_cross_count', 0) + us_summary.get('golden_cross_count', 0),
                'total_dead_cross': kospi_summary.get('dead_cross_count', 0) + kosdaq_summary.get('dead_cross_count', 0) + us_summary.get('dead_cross_count', 0),
                'total_ema_array_perfect_rise': kospi_summary.get('ema_array_perfect_rise', 0) + kosdaq_summary.get('ema_array_perfect_rise', 0) + us_summary.get('ema_array_perfect_rise', 0),
                'total_ema_array_perfect_fall': kospi_summary.get('ema_array_perfect_fall', 0) + kosdaq_summary.get('ema_array_perfect_fall', 0) + us_summary.get('ema_array_perfect_fall', 0)
            }
            return combined_summary
        except Exception as e:
            self.logger.error(f"어드민 요약 정보 통합 중 오류: {str(e)}")
            return {
                'market_type': 'COMBINED',
                'total_stocks': 0,
                'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error': str(e)
            }
    
    def _save_newsletter_content(self, user_id: int, newsletter_data: Dict, newsletter_type: str):
        """뉴스레터 내용을 데이터베이스에 저장"""
        try:
            # summary를 JSON 문자열로 변환
            summary_json = json.dumps(newsletter_data['summary'], ensure_ascii=False) if isinstance(newsletter_data['summary'], dict) else str(newsletter_data['summary'])
            
            newsletter_content = NewsletterContent(
                user_id=user_id,
                market_type=newsletter_data['market'],
                primary_market=newsletter_data.get('primary_market'),
                timeframe=newsletter_data['timeframe'],
                newsletter_type=newsletter_type,
                html_content=newsletter_data['html'],
                summary=summary_json,
                generated_at=datetime.now()
            )
            
            db.session.add(newsletter_content)
            db.session.commit()
            
            self.logger.info(f"뉴스레터 내용 저장 완료: 사용자 {user_id}, 타입 {newsletter_type}")
            
        except Exception as e:
            self.logger.error(f"뉴스레터 내용 저장 실패: {str(e)}")
            db.session.rollback()
            raise
    
    def get_newsletter_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """사용자의 뉴스레터 히스토리 조회"""
        try:
            contents = NewsletterContent.query.filter_by(user_id=user_id)\
                .order_by(NewsletterContent.generated_at.desc())\
                .limit(limit).all()
            
            history = []
            for content in contents:
                # summary를 다시 딕셔너리로 변환
                summary_dict = {}
                if content.summary:
                    try:
                        summary_dict = json.loads(content.summary)
                    except (json.JSONDecodeError, TypeError):
                        summary_dict = {'text': str(content.summary)}
                
                history.append({
                    'id': content.id,
                    'market_type': content.market_type,
                    'primary_market': content.primary_market,
                    'timeframe': content.timeframe,
                    'newsletter_type': content.newsletter_type,
                    'summary': summary_dict,
                    'generated_at': content.generated_at.isoformat()
                })
            
            return history
            
        except Exception as e:
            self.logger.error(f"뉴스레터 히스토리 조회 실패: {str(e)}")
            return []
    
    def get_newsletter_by_id(self, newsletter_id: int, user_id: int) -> Optional[Dict]:
        """특정 뉴스레터 내용 조회"""
        try:
            content = NewsletterContent.query.filter_by(
                id=newsletter_id, 
                user_id=user_id
            ).first()
            
            if content:
                # summary를 다시 딕셔너리로 변환
                summary_dict = {}
                if content.summary:
                    try:
                        summary_dict = json.loads(content.summary)
                    except (json.JSONDecodeError, TypeError):
                        summary_dict = {'text': str(content.summary)}
                
                return {
                    'id': content.id,
                    'html': content.html_content,
                    'summary': summary_dict,
                    'market_type': content.market_type,
                    'primary_market': content.primary_market,
                    'timeframe': content.timeframe,
                    'newsletter_type': content.newsletter_type,
                    'generated_at': content.generated_at.isoformat()
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"뉴스레터 조회 실패: {str(e)}")
            return None
    
    def get_newsletter_by_time(self, timeframe: str = 'd', user_id: Optional[int] = None) -> Dict:
        """시간대에 따라 적절한 뉴스레터 생성"""
        now = datetime.now()
        
        # 한국 시간 기준 (UTC+9)
        korea_time = now + timedelta(hours=9)
        hour = korea_time.hour
        
        # 한국장 마감 후 (15:30 + 2시간 = 17:30 이후)
        if 17 <= hour or hour < 9:
            # 한국장이 주요 시장
            return self.generate_combined_newsletter(timeframe, 'kospi', user_id)
        else:
            # 미국장이 주요 시장 (한국 시간 9시~17시는 미국장 시간대)
            return self.generate_combined_newsletter(timeframe, 'US', user_id)