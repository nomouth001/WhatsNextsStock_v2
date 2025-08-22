import os
import logging
import pandas as pd
import google.generativeai as genai
from datetime import datetime, time
from zoneinfo import ZoneInfo
from typing import Dict, List, Optional, Tuple

# Config
from config import DevelopmentConfig

class AIAnalysisService:
    """AI 분석 전용 서비스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.prompt_template = self._load_prompt_template()
    
    def analyze_stock(self, ticker: str, market_type: str = 'KOSPI', 
                     company_name: str = None) -> Tuple[Optional[str], Optional[str]]:
        """주식 AI 분석 수행"""
        try:
            # 데이터 수집 (일봉, 주봉, 월봉)
            daily_data, weekly_data, monthly_data = self._get_ohlcv_data_for_ai(ticker, market_type)
            
            # 지표 데이터 포함
            daily_ohlcv_with_indicators = self._get_ohlcv_with_indicators(ticker, 'd', market_type)
            weekly_ohlcv_with_indicators = self._get_ohlcv_with_indicators(ticker, 'w', market_type)
            monthly_ohlcv_with_indicators = self._get_ohlcv_with_indicators(ticker, 'm', market_type)
            
            # 프롬프트 생성
            prompt = self._create_analysis_prompt(
                ticker, company_name, 
                daily_ohlcv_with_indicators, 
                weekly_ohlcv_with_indicators, 
                monthly_ohlcv_with_indicators,
                market_type=market_type
            )
            
            # AI API 호출
            analysis_result = self._call_ai_api(prompt)
            
            # 분석 로그 저장
            self._save_analysis_log(ticker, prompt, analysis_result)
            
            return analysis_result, None
            
        except Exception as e:
            error_msg = f"AI 분석 중 오류 발생: {e}"
            self.logger.error(error_msg)
            # 예외 시에도 디버그 로그 강제 저장
            try:
                fallback_prompt = self._get_default_prompt_template().format(
                    ticker=ticker,
                    company_name=company_name or ticker,
                    daily_ohlcv_with_indicators_str="데이터 없음",
                    weekly_ohlcv_with_indicators_str="데이터 없음",
                    monthly_ohlcv_with_indicators_str="데이터 없음"
                )
                self._save_analysis_log(ticker, fallback_prompt, error_msg)
            except Exception:
                pass
            return None, error_msg
    
    def analyze_stock_with_data(self, ticker: str, daily_data: List, weekly_data: List, 
                               monthly_data: List, market_type: str = 'KOSPI', 
                               company_name: str = None) -> Tuple[Optional[str], Optional[str]]:
        """[2025-08-09 추가] 이미 로딩된 지표 포함 데이터로 AI 분석 수행"""
        try:
            # 전달받은 데이터 검증: 중단하지 않고 진행하여 로그/프롬프트를 남김
            if not daily_data and not weekly_data and not monthly_data:
                self.logger.warning(f"[{ticker}] 분석할 데이터가 없습니다. 최소 프롬프트로 진행합니다.")
            
            self.logger.info(f"[{ticker}] AI 분석 시작 - 지표 포함 데이터 직접 사용")
            
            # ai_analysis_prompt.txt 템플릿 로드
            template = self._load_prompt_template()
            
            # 데이터 포맷팅 (OHLCV + 지표 통합 형식)
            from routes.analysis_routes import format_data_with_indicators_for_prompt
            # 디버그: 프롬프트 데이터 요약만 남기고 상세 키 출력은 주석 처리(로그 절감)
            try:
                logging.info(f"[{ticker}] Prompt 데이터 요약 - d={len(daily_data) if daily_data else 0}, w={len(weekly_data) if weekly_data else 0}, m={len(monthly_data) if monthly_data else 0}")
                # if daily_data:
                #     logging.info(f"[{ticker}] d 첫 항목 키: {list(daily_data[0].keys())}")
                # if weekly_data:
                #     logging.info(f"[{ticker}] w 첫 항목 키: {list(weekly_data[0].keys())}")
                # if monthly_data:
                #     logging.info(f"[{ticker}] m 첫 항목 키: {list(monthly_data[0].keys())}")
            except Exception as pinfo_err:
                logging.warning(f"[{ticker}] Prompt 데이터 요약 로깅 실패: {pinfo_err}")

            daily_str = format_data_with_indicators_for_prompt(daily_data)
            weekly_str = format_data_with_indicators_for_prompt(weekly_data)
            monthly_str = format_data_with_indicators_for_prompt(monthly_data)
            
            # 프롬프트 생성
            prompt = template.format(
                ticker=ticker,
                company_name=company_name or ticker,
                daily_ohlcv_with_indicators_str=daily_str,
                weekly_ohlcv_with_indicators_str=weekly_str,
                monthly_ohlcv_with_indicators_str=monthly_str
            )
            # 장중이면 간단 프리앰블을 앞에 덧붙임 (시장별 현지시간 HHMM)
            try:
                if (market_type or 'KOSPI').upper() == 'US':
                    tz = ZoneInfo("America/New_York")
                    now_local = datetime.now(tz)
                    is_open = time(9,30) <= now_local.time() <= time(16,0)
                else:
                    tz = ZoneInfo("Asia/Seoul")
                    now_local = datetime.now(tz)
                    is_open = time(9,0) <= now_local.time() <= time(15,30)
                if is_open:
                    preamble = f"지금은 {now_local.strftime('%Y-%m-%d %H%M')}인 것을 거래량 분석에 감안하여라."
                    prompt = preamble + "\n" + prompt
            except Exception:
                pass
            
            self.logger.info(f"[{ticker}] AI 프롬프트 생성 완료 - OHLCV + 지표 데이터 포함 (d_len={len(daily_str)}, w_len={len(weekly_str)}, m_len={len(monthly_str)})")
            
            # AI API 호출
            analysis_result = self._call_ai_api(prompt)
            
            # 분석 로그 저장
            self._save_analysis_log(ticker, prompt, analysis_result)
            
            return analysis_result, None
            
        except Exception as e:
            error_msg = f"AI 분석 수행 실패: {e}"
            self.logger.error(error_msg)
            # 예외 시에도 디버그 로그 강제 저장 (최소 프롬프트)
            try:
                fallback_prompt = self._get_default_prompt_template().format(
                    ticker=ticker,
                    company_name=company_name or ticker,
                    daily_ohlcv_with_indicators_str="데이터 없음",
                    weekly_ohlcv_with_indicators_str="데이터 없음",
                    monthly_ohlcv_with_indicators_str="데이터 없음"
                )
                self._save_analysis_log(ticker, fallback_prompt, error_msg)
            except Exception:
                pass
            return None, error_msg
    
    def _load_prompt_template(self) -> str:
        """프롬프트 템플릿 로드"""
        try:
            # [2025-08-09 수정] ai_analysis_prompt.txt 파일은 프로젝트 루트에 위치
            template_path = "ai_analysis_prompt.txt"  # 프로젝트 루트 경로
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                # 이전 경로로도 시도
                fallback_path = os.path.join("templates", "ai_analysis_prompt.txt") 
                if os.path.exists(fallback_path):
                    with open(fallback_path, 'r', encoding='utf-8') as f:
                        return f.read()
                # 기본 템플릿 반환
                return self._get_default_prompt_template()
        except Exception as e:
            self.logger.error(f"프롬프트 템플릿 로드 실패: {e}")
            return self._get_default_prompt_template()
    
    def _get_default_prompt_template(self) -> str:
        """기본 프롬프트 템플릿"""
        return """밑에 제공되는 {ticker} ({company_name}) 종목의 OHLCV 데이터와 각종 기술적 지표들 (EMA5, EMA20, EMA40, MACD, 볼린저밴드, RSI, 스토캐스틱, 일목균형표, 5일 평균 거래량 대비 당일의 거래량, 20일 평균 거래량 대비 당일의 거래량, 40일 평균 거래량 대비 당일의 거래량)을 기반으로 차트를 분석 후, 스윙 투자자의 매수 및 매도 시점점에 대한 의견을 개진해라. 
이 분석의 핵심내용을 세 문장으로 요약해 제일 첫머리에 **핵심 요약**의 제목아래 번호를 붙여 제시해라. 상세분석은 일봉-주봉-월봉의 순으로 배열해라.

일봉 데이터 (최근 31일, OHLCV + 지표 포함):
{daily_ohlcv_with_indicators_str}

주봉 데이터 (최근 31주, OHLCV + 지표 포함):
{weekly_ohlcv_with_indicators_str}

월봉 데이터 (최근 31개월, OHLCV + 지표 포함):
{monthly_ohlcv_with_indicators_str}"""
    
    def _get_ohlcv_data_for_ai(self, ticker: str, market_type: str = 'KOSPI') -> Tuple[List, List, List]:
        """AI 분석용 OHLCV 데이터 가져오기"""
        try:
            from services.market.data_reading_service import DataReadingService
            reading_service = DataReadingService()
            
            # 일봉, 주봉, 월봉 데이터 로딩 (인자 순서 교정: ticker, market_type, timeframe)
            daily_data = reading_service.read_ohlcv_csv(ticker, market_type, 'd')
            weekly_data = reading_service.read_ohlcv_csv(ticker, market_type, 'w')
            monthly_data = reading_service.read_ohlcv_csv(ticker, market_type, 'm')
            
            return daily_data, weekly_data, monthly_data
            
        except Exception as e:
            self.logger.error(f"OHLCV 데이터 로딩 실패: {e}")
            return [], [], []
    
    def _get_ohlcv_with_indicators(self, ticker: str, timeframe: str, market_type: str = 'KOSPI') -> List:
        """지표가 포함된 OHLCV 데이터 가져오기"""
        try:
            from services.market.data_reading_service import DataReadingService
            from services.technical_indicators_service import TechnicalIndicatorsService
            
            reading_service = DataReadingService()
            indicators_service = TechnicalIndicatorsService()
            
            # OHLCV 데이터 로딩
            # 인자 순서 교정: (ticker, market_type, timeframe)
            ohlcv_df = reading_service.read_ohlcv_csv(ticker, market_type, timeframe)
            ohlcv_data = []
            if not ohlcv_df.empty:
                for idx, row in ohlcv_df.iterrows():
                    ohlcv_data.append({
                        'date': idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx),
                        'open': row.get('Open', 0),
                        'high': row.get('High', 0),
                        'low': row.get('Low', 0),
                        'close': row.get('Close', 0),
                        'volume': row.get('Volume', 0),
                    })
            
            if not ohlcv_data:
                return []
            
            # 지표 데이터 로딩
            indicators_df = indicators_service.read_indicators_csv(ticker, market_type, timeframe)
            
            # DataFrame 검증 (None 체크 추가)
            if indicators_df is None:
                self.logger.warning(f"[{ticker}] 지표 데이터가 None임")
                return []
            
            if not isinstance(indicators_df, pd.DataFrame):
                self.logger.warning(f"[{ticker}] 지표 데이터가 DataFrame이 아님: {type(indicators_df)}")
                return []
                
            if indicators_df.empty:
                self.logger.warning(f"[{ticker}] 지표 데이터가 비어있음")
                return []
            
            # 지표 DataFrame을 딕셔너리 리스트로 변환
            indicators_list = []
            for idx, row in indicators_df.iterrows():
                indicator_dict = row.to_dict()
                indicator_dict['date'] = idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx)
                indicators_list.append(indicator_dict)
            
            # 데이터 결합
            combined_data = []
            for i, ohlcv_item in enumerate(ohlcv_data):
                combined_item = ohlcv_item.copy()
                
                # 해당 날짜의 지표 데이터 추가
                if i < len(indicators_list):
                    indicator_item = indicators_list[i]
                    for key, value in indicator_item.items():
                        if key not in combined_item and key != 'date':
                            combined_item[key] = value
                
                combined_data.append(combined_item)
            
            return combined_data
            
        except Exception as e:
            self.logger.error(f"지표 포함 데이터 로딩 실패: {e}")
            return []
    
    def _create_analysis_prompt(self, ticker: str, company_name: str, 
                               daily_data: List, weekly_data: List, monthly_data: List,
                               market_type: str = 'KOSPI') -> str:
        """분석 프롬프트 생성"""
        try:
            # 데이터 포맷팅
            daily_str = self._format_data_with_indicators_for_prompt(daily_data)
            weekly_str = self._format_data_with_indicators_for_prompt(weekly_data)
            monthly_str = self._format_data_with_indicators_for_prompt(monthly_data)
            
            # 프롬프트 생성
            prompt = self.prompt_template.format(
                ticker=ticker,
                company_name=company_name if company_name else ticker,
                daily_ohlcv_with_indicators_str=daily_str,
                weekly_ohlcv_with_indicators_str=weekly_str,
                monthly_ohlcv_with_indicators_str=monthly_str
            )
            # 장중이면 간단 프리앰블을 앞에 덧붙임 (시장별 현지시간 HHMM)
            try:
                if (market_type or 'KOSPI').upper() == 'US':
                    tz = ZoneInfo("America/New_York")
                    now_local = datetime.now(tz)
                    is_open = time(9,30) <= now_local.time() <= time(16,0)
                else:
                    tz = ZoneInfo("Asia/Seoul")
                    now_local = datetime.now(tz)
                    is_open = time(9,0) <= now_local.time() <= time(15,30)
                if is_open:
                    preamble = f"지금은 {now_local.strftime('%Y-%m-%d %H%M')}인 것을 거래량을 이용한 분석에 감안하여라."
                    prompt = preamble + "\n" + prompt
            except Exception:
                pass
            
            return prompt
            
        except Exception as e:
            self.logger.error(f"프롬프트 생성 실패: {e}")
            return ""
    
    def _format_data_with_indicators_for_prompt(self, data: List) -> str:
        """지표가 포함된 데이터를 프롬프트 형식으로 변환"""
        if not data:
            return "데이터 없음"
        
        formatted_lines = []
        for item in data:
            if isinstance(item, dict):
                # 기본 OHLCV 데이터
                line = f"{item.get('date', 'N/A')}: O={item.get('open', 0)}, H={item.get('high', 0)}, L={item.get('low', 0)}, C={item.get('close', 0)}, V={item.get('volume', 0)}"
                
                # 지표 데이터 추가
                indicators = []
                for key, value in item.items():
                    if key in ['ema5', 'ema20', 'ema40', 'macd', 'macd_signal', 'rsi', 'stoch_k', 'stoch_d']:
                        if isinstance(value, (int, float)):
                            indicators.append(f"{key}={value:.2f}")
                
                if indicators:
                    line += f" | {', '.join(indicators)}"
                
                formatted_lines.append(line)
        
        return "\n".join(formatted_lines)
    
    def _call_ai_api(self, prompt: str) -> str:
        """AI API 호출"""
        try:
            google_api_key = DevelopmentConfig.GOOGLE_API_KEY
            if not google_api_key:
                return "Google API 키가 설정되지 않았습니다."
            
            genai.configure(api_key=google_api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            response = model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            self.logger.error(f"AI API 호출 실패: {e}")
            return f"AI 분석 중 오류가 발생했습니다: {e}"
    
    def _save_analysis_log(self, ticker: str, prompt: str, result: str) -> None:
        """분석 로그 저장"""
        try:
            debug_log_path = os.path.join("logs", f"ai_analysis_debug_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            os.makedirs("logs", exist_ok=True)
            
            with open(debug_log_path, 'w', encoding='utf-8') as f:
                f.write(f"=== AI 분석 디버그 로그 ===\n")
                f.write(f"티커: {ticker}\n")
                f.write(f"분석 시간: {datetime.now()}\n")
                f.write(f"\n=== AI 분석 프롬프트 ===\n")
                f.write(prompt)
                f.write(f"\n=== AI 분석 결과 ===\n")
                f.write(result)
            
            self.logger.info(f"AI 분석 로그 저장됨: {debug_log_path}")
            
        except Exception as e:
            self.logger.error(f"분석 로그 저장 실패: {e}") 