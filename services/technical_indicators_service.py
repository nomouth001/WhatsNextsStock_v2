"""
기술적 지표 계산 및 저장 서비스
FormerCodes에서 이식된 로직 사용
- EMA5, EMA20, EMA40
- MACD (Line, Signal, Histogram)
- RSI
- Stochastic (%K, %D)
- Ichimoku (Tenkan, Kijun, Senkou A/B)
- Volume Ratios (5일/20일/40일 평균 대비)
- 크로스오버 감지 (MACD, EMA)
"""

import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime, timedelta
import ta
from services.market.data_reading_service import DataReadingService
from services.analysis.pattern.ema_analyzer import EMAAnalyzer


class TechnicalIndicatorsService:
    def __init__(self):
        self.indicators_dir = "static/data"
        # [Deprecated] 로컬 지표 캐시 (전역 캐시 사용 권장: services.core.cache_service.CacheService)
        # - 남겨두되, 신규 코드에서 사용하지 말 것
        self._indicators_cache = {}
        self._cache_ttl = 300  # 5분 캐시
        self.ema_analyzer = EMAAnalyzer()
        
        # DataReadingService 초기화
        self.data_reader = DataReadingService()
        
    
    def calculate_all_indicators(self, ticker, market_type='KOSPI', timeframes=['d', 'w', 'm']):
        """
        특정 티커의 모든 시간프레임에 대해 기술적 지표를 계산하고 저장
        장마감 시간에 따라 목표 날짜까지의 데이터만 사용
        """
        results = {}
        
        # 타임필터링 완전 제거 - 모든 데이터 사용
        logging.info(f"[{ticker}] 모든 데이터를 사용하여 지표 계산")
        
        for timeframe in timeframes:
            logging.info(f"[{ticker}] {timeframe} 타임프레임 지표 계산 시작")
            
            # OHLCV 데이터 읽기 (인자 순서: ticker, market_type, timeframe)
            data_reading_service = DataReadingService()
            df = data_reading_service.read_ohlcv_csv(ticker, market_type, timeframe)
            
            if df.empty:
                logging.warning(f"[{ticker}] {timeframe} 데이터 없음, 지표 계산 건너뜀")
                results[timeframe] = None
                continue
            
            # 타임필터링 완전 제거 - 모든 데이터 사용
            
            # 최소 데이터 요구사항을 동적으로 조정
            min_data_required = self._get_min_data_requirement(timeframe, ticker)
            if len(df) < min_data_required:
                logging.warning(f"[{ticker}] {timeframe} 데이터 부족 ({len(df)} < {min_data_required}), 지표 계산 건너뜀")
                results[timeframe] = None
                continue
            
            try:
                # 데이터 품질 검증 및 수정
                df = self._validate_and_fix_data_quality(df, ticker)
                
                # 모든 데이터로 지표 계산
                indicators_df = self._calculate_indicators(df)
                
                # 새로운 간소화된 크로스오버 감지 및 저장 (일봉만)
                signals_result = None
                if timeframe == 'd':  # 일봉일 때만 CrossInfo 생성
                    from services.analysis.crossover.simplified_detector import SimplifiedCrossoverDetector
                    crossover_service = SimplifiedCrossoverDetector()
                    signals_result = crossover_service.detect_and_save_signals(indicators_df, ticker, timeframe, market_type)
                
                # 기존 지표 CSV 저장 (신호 정보 없이) - 모든 timeframe에 대해 저장
                saved_path = self._save_indicators_to_csv(ticker, indicators_df, timeframe, market_type)
                
                results[timeframe] = {
                    'success': True,
                    'data_rows': len(df),
                    'indicators_rows': len(indicators_df),
                    'indicators_csv_path': saved_path,
                    'signals_result': signals_result
                }
                
                # 최신 날짜 정보 가져오기
                latest_date = df.index[-1].date() if not df.empty else None
                current_date = latest_date.strftime('%Y-%m-%d') if latest_date else 'Unknown'
                
                logging.info(f"[{ticker}] {timeframe} 타임프레임 지표 계산 완료: {saved_path} (최신: {current_date})")
                
            except Exception as e:
                logging.error(f"[{ticker}] {timeframe} 타임프레임 지표 계산 오류: {e}")
                results[timeframe] = {'success': False, 'error': str(e)}
        
        return results
    
    def _get_min_data_requirement(self, timeframe, ticker):
        """시간프레임과 종목에 따른 최소 데이터 요구사항을 동적으로 조정"""
        base_requirements = {
            'd': 50,   # 일봉: 50일
            'w': 20,   # 주봉: 20주
            'm': 12    # 월봉: 12개월
        }
        
        # 기본 요구사항
        base_req = base_requirements.get(timeframe, 50)
        
        # 특정 종목이나 상황에 따른 조정
        if timeframe == 'm':
            # 월봉의 경우 더 관대하게 조정
            return max(6, base_req // 2)  # 최소 6개월, 기본 12개월의 절반
        
        return base_req
    
    def _validate_and_fix_data_quality(self, df, ticker):
        """데이터 품질 검증 및 수정"""
        original_count = len(df)
        fixed_count = 0
        
        # Close > High 또는 Close < Low 문제 수정
        for idx in df.index:
            row = df.loc[idx]
            close = row['Close']
            high = row['High']
            low = row['Low']
            
            if close > high:
                # Close가 High보다 높으면 High를 Close로 조정
                df.loc[idx, 'High'] = close
                fixed_count += 1
                logging.debug(f"[{ticker}] Fixed Close > High at {idx}: Close={close}, High adjusted to {close}")
            
            if close < low:
                # Close가 Low보다 낮으면 Low를 Close로 조정
                df.loc[idx, 'Low'] = close
                fixed_count += 1
                logging.debug(f"[{ticker}] Fixed Close < Low at {idx}: Close={close}, Low adjusted to {close}")
        
        if fixed_count > 0:
            logging.info(f"[{ticker}] Fixed {fixed_count} data quality issues out of {original_count} rows")
        
        return df
    
    def _calculate_indicators(self, df):
        """기술적 지표 계산"""
        indicators_df = pd.DataFrame(index=df.index)
        
        # Close 컬럼 추가 (종가-EMA 갭 계산을 위해 필요)
        indicators_df['Close'] = df['Close']
        
        # 등락률 계산 추가
        indicators_df['Change_Percent'] = self._calculate_change_percent(df)
        
        # EMA 계산
        indicators_df['EMA5'] = ta.trend.ema_indicator(df['Close'], window=5)
        indicators_df['EMA20'] = ta.trend.ema_indicator(df['Close'], window=20)
        indicators_df['EMA40'] = ta.trend.ema_indicator(df['Close'], window=40)
        
        # MACD 계산
        macd = ta.trend.MACD(df['Close'])
        indicators_df['MACD'] = macd.macd()
        indicators_df['MACD_Signal'] = macd.macd_signal()
        indicators_df['MACD_Histogram'] = macd.macd_diff()
        
        # RSI 계산
        indicators_df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
        
        # Stochastic 계산
        stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'])
        indicators_df['Stoch_K'] = stoch.stoch()
        indicators_df['Stoch_D'] = stoch.stoch_signal()
        
        # Bollinger Bands 계산
        bb = ta.volatility.BollingerBands(df['Close'])
        indicators_df['BB_Upper'] = bb.bollinger_hband()
        indicators_df['BB_Lower'] = bb.bollinger_lband()
        indicators_df['BB_Middle'] = bb.bollinger_mavg()
        
        # Ichimoku 계산
        indicators_df['Ichimoku_Tenkan'] = ta.trend.ichimoku_conversion_line(df['High'], df['Low'])
        indicators_df['Ichimoku_Kijun'] = ta.trend.ichimoku_base_line(df['High'], df['Low'])
        indicators_df['Ichimoku_Senkou_A'] = ta.trend.ichimoku_a(df['High'], df['Low'])
        indicators_df['Ichimoku_Senkou_B'] = ta.trend.ichimoku_b(df['High'], df['Low'])
        
        # Volume 관련 지표 계산
        indicators_df['Volume_MA5'] = df['Volume'].rolling(window=5).mean()
        indicators_df['Volume_MA20'] = df['Volume'].rolling(window=20).mean()
        indicators_df['Volume_MA40'] = df['Volume'].rolling(window=40).mean()
        
        # Volume Ratios (%) 계산
        indicators_df['Volume_Ratio_5d'] = (df['Volume'] / indicators_df['Volume_MA5'] * 100).round(2)
        indicators_df['Volume_Ratio_20d'] = (df['Volume'] / indicators_df['Volume_MA20'] * 100).round(2)
        indicators_df['Volume_Ratio_40d'] = (df['Volume'] / indicators_df['Volume_MA40'] * 100).round(2)
        
        return indicators_df
    
    def _calculate_change_percent(self, df):
        """등락률 계산"""
        try:
            if len(df) < 2:
                return pd.Series([0.0] * len(df), index=df.index)
            
            # 이전 종가 대비 등락률 계산
            change_percent = ((df['Close'] - df['Close'].shift(1)) / df['Close'].shift(1)) * 100
            return change_percent.round(2)
        except Exception as e:
            logging.error(f"등락률 계산 실패: {e}")
            return pd.Series([0.0] * len(df), index=df.index)
    
    def _save_indicators_to_csv(self, ticker, indicators_df, timeframe, market_type):
        """
        계산된 지표를 CSV 파일로 저장 (DataStorageService 사용)
        """
        try:
            from services.market.data_storage_service import DataStorageService
            storage_service = DataStorageService()
            
            # DataStorageService를 통한 저장
            saved_path = storage_service.save_indicators_to_csv(ticker, indicators_df, timeframe, market_type)
            
            logging.info(f"[{ticker}] 지표 CSV 저장 완료: {saved_path}")
            return saved_path
            
        except Exception as e:
            logging.error(f"[{ticker}] 지표 CSV 저장 실패: {e}")
            return None
    
    def _get_actual_market_type(self, ticker, market_type):
        """실제 폴더명을 결정하는 함수"""
        # 디버깅 로그 추가
        logging.debug(f"[{ticker}] _get_actual_market_type 호출: market_type='{market_type}'")
        
        # market_type을 대문자로 정규화
        market_type_upper = market_type.upper()
        logging.debug(f"[{ticker}] 정규화된 market_type: '{market_type_upper}'")
        
        # US 주식 처리 - 다양한 입력 형태 지원
        if market_type_upper in ['US', 'U.S.', 'USA']:
            result = 'US'
            logging.debug(f"[{ticker}] US 주식으로 인식: '{result}'")
            return result
        elif market_type_upper in ['KOSPI', 'KOSDAQ']:
            result = market_type_upper
            logging.debug(f"[{ticker}] 한국 주식으로 인식: '{result}'")
            return result

        else:
            # 기본값: 이외의 market_type이 전달된 경우, 'US'로 변환하지만 어떤 값을 받았다는 메시지를 출력
            result = 'US'
            logging.warning(f"[{ticker}] 예상치 못한 market_type '{market_type_upper}'를 받아서 'US'로 변환")
            return result
    
    def read_indicators_csv(self, ticker: str, market: str, timeframe: str = 'd') -> pd.DataFrame:
        """기술적 지표 CSV 파일 읽기"""
        return self.data_reader.read_indicators_csv(ticker, market, timeframe)

    def calculate_and_save_indicators(self, ticker: str, market_type: str, ohlcv_df: pd.DataFrame, timeframe: str = 'd'):
        """모든 타임프레임에 대한 기술적 지표 계산 및 저장"""
        if ohlcv_df.empty:
            self.logger.warning(f"[{ticker}] OHLCV 데이터프레임이 비어 있어 지표를 계산할 수 없습니다 ({timeframe}).")
            return

        indicators_df = self.indicator_calculator.calculate_all_indicators(ohlcv_df)
        self.data_storage.save_data(indicators_df, ticker, market_type, 'indicators', timeframe)
        self.logger.info(f"[{ticker}] 기술적 지표 계산 및 저장 완료 ({timeframe}).")

    def _get_calculator(self):
        """지표 계산기 인스턴스를 반환"""
        return self.indicator_calculator

    def get_latest_indicators(self, ticker: str, timeframe: str = 'd', market_type: str = 'KOSPI') -> dict:
        """
        최신 지표 값들만 딕셔너리로 반환
        차트나 분석에서 간단히 사용할 수 있도록
        """
        try:
            df = self.read_indicators_csv(ticker, market_type, timeframe)
            if df.empty:
                return {}
            
            latest = df.iloc[-1]
            return {
                'EMA5': latest.get('EMA5'),
                'EMA20': latest.get('EMA20'),
                'EMA40': latest.get('EMA40'),
                'MACD': latest.get('MACD'),
                'MACD_Signal': latest.get('MACD_Signal'),
                'RSI': latest.get('RSI'),
                'BB_Upper': latest.get('BB_Upper'),
                'BB_Lower': latest.get('BB_Lower'),
                'BB_Middle': latest.get('BB_Middle'),
                'Stoch_K': latest.get('Stoch_K'),
                'Stoch_D': latest.get('Stoch_D'),
                'Ichimoku_Tenkan': latest.get('Ichimoku_Tenkan'),
                'Ichimoku_Kijun': latest.get('Ichimoku_Kijun'),
                'Volume_Ratio_5d': latest.get('Volume_Ratio_5d'),
                'Volume_Ratio_20d': latest.get('Volume_Ratio_20d'),
                'Volume_Ratio_40d': latest.get('Volume_Ratio_40d')
            }
        except Exception as e:
            logging.error(f"[{ticker}] 최신 지표 값 가져오기 실패: {e}")
            return {}
    
    def ensure_indicators_exist(self, ticker: str, timeframe: str, market_type: str) -> bool:
        """지표 CSV가 없으면 자동 생성"""
        try:
            # 신선도 전략 확인: 장중 구형 데이터면 오케스트레이터 트리거
            try:
                from services.market.file_management_service import FileManagementService
                freshness_service = FileManagementService()
                strategy = freshness_service.determine_data_strategy(ticker, market_type)
                if strategy == "download_fresh":
                    logging.info(f"[{ticker}] 신선도 정책으로 새 데이터 다운로드 필요 → 오케스트레이터 트리거")
                    from services.market.market_data_orchestrator import MarketDataOrchestrator
                    orchestrator = MarketDataOrchestrator()
                    orchestrator_result = orchestrator.process_stock_data_complete(ticker, market_type)
                    if not (orchestrator_result and orchestrator_result.success):
                        logging.warning(f"[{ticker}] 오케스트레이터 실패: stage={getattr(orchestrator_result, 'error_stage', None)} msg={getattr(orchestrator_result, 'error_message', None)}")
                        return False
            except Exception as _:
                pass

            # 1) OHLCV 존재 여부 확인
            from services.market.file_management_service import FileManagementService
            file_service = FileManagementService()
            latest_ohlcv = file_service.get_latest_file(ticker, 'ohlcv', market_type, timeframe)

            # 2) 없으면 오케스트레이터로 다운로드/저장/지표 계산 수행
            if not latest_ohlcv:
                logging.info(f"[{ticker}] {timeframe} OHLCV 파일 없음 → 오케스트레이터 트리거")
                from services.market.market_data_orchestrator import MarketDataOrchestrator
                orchestrator = MarketDataOrchestrator()
                orchestrator_result = orchestrator.process_stock_data_complete(ticker, market_type)
                if not (orchestrator_result and orchestrator_result.success):
                    logging.warning(f"[{ticker}] 오케스트레이터 실패: stage={getattr(orchestrator_result, 'error_stage', None)} msg={getattr(orchestrator_result, 'error_message', None)}")
                    return False

            # 3) 지표 파일 존재 여부 확인
            indicators_df = self.read_indicators_csv(ticker, market_type, timeframe)
            if not indicators_df.empty:
                return True

            # 4) 여전히 없으면 단일 타임프레임 지표 계산 시도 (중복 계산 억제: 오케스트레이터 직후면 보통 스킵됨)
            logging.info(f"[{ticker}] {timeframe} 지표 CSV 없음 → 단일 타임프레임 계산 시도")
            result = self.calculate_all_indicators(ticker, market_type, [timeframe])
            return bool(result.get(timeframe) and result.get(timeframe, {}).get('success'))
        except Exception as e:
            logging.error(f"[{ticker}] 지표 존재 확인/생성 실패: {e}")
            return False

    def get_latest_values(self, ticker, timeframe='d', market_type='US'):
        """최신 지표 값들을 가져오기 - 기존 호환성 유지"""
        try:
            indicators_df = self.read_indicators_csv(ticker, market_type, timeframe)
            
            if indicators_df.empty:
                return {}
            
            latest_data = indicators_df.iloc[-1]
            
            return {
                'ema5': latest_data.get('EMA5', 0),
                'ema20': latest_data.get('EMA20', 0),
                'ema40': latest_data.get('EMA40', 0),
                'macd': latest_data.get('MACD', 0),
                'macd_signal': latest_data.get('MACD_Signal', 0),
                'macd_histogram': latest_data.get('MACD_Histogram', 0),
                'rsi': latest_data.get('RSI', 0),
                'stoch_k': latest_data.get('Stoch_K', 0),
                'stoch_d': latest_data.get('Stoch_D', 0),
                'bb_upper': latest_data.get('BB_Upper', 0),
                'bb_lower': latest_data.get('BB_Lower', 0),
                'bb_middle': latest_data.get('BB_Middle', 0)
            }
            
        except Exception as e:
            logging.error(f"[{ticker}] Error getting latest values: {e}")
            return {}
    
    def get_stock_analysis_data(self, ticker, market_type='US'):
        """주식 분석 데이터 가져오기 - 기존 인터페이스 호환성 유지"""
        try:
            indicators_df = self.read_indicators_csv(ticker, market_type, timeframe='d')
            
            if indicators_df.empty:
                return None
            
            # 새로운 간소화된 크로스오버 감지 서비스 사용
            from services.analysis.crossover.simplified_detector import SimplifiedCrossoverDetector
            crossover_service = SimplifiedCrossoverDetector()
            signals = crossover_service.detect_all_signals(indicators_df)
            
            # EMA 배열 분석
            latest_data = indicators_df.iloc[-1]
            ema_array = self._analyze_ema_array(latest_data)
            
            # 기존 인터페이스와 호환되는 형식으로 반환
            return {
                'ema_array': ema_array,
                'ema_crossover': signals.get('ema_analysis', {}).get('latest_crossover_type'),
                'macd_crossover': signals.get('macd_analysis', {}).get('latest_crossover_type'),
                'ema_crossover_status': signals.get('ema_analysis', {}),
                'macd_crossover_status': signals.get('macd_analysis', {}),
                'proximity_info': {
                    'ema_proximity': signals.get('ema_analysis', {}).get('current_proximity'),
                    'macd_proximity': signals.get('macd_analysis', {}).get('current_proximity')
                },
                'gap_ema20': self._calculate_gap(latest_data.get('Close', 0), latest_data.get('EMA20', 0)),
                'gap_ema40': self._calculate_gap(latest_data.get('Close', 0), latest_data.get('EMA40', 0))
            }
            
        except Exception as e:
            logging.error(f"[{ticker}] Error getting stock analysis data: {e}")
            return None
    
    def get_stock_analysis_data_from_cache(self, ticker, cached_data, market_type='US'):
        """캐시된 데이터를 사용하여 주식 분석 데이터 가져오기"""
        try:
            indicators_df = cached_data['indicators']
            
            if indicators_df.empty:
                return None
            
            # 새로운 간소화된 크로스오버 감지 서비스 사용
            from services.analysis.crossover.simplified_detector import SimplifiedCrossoverDetector
            crossover_service = SimplifiedCrossoverDetector()
            signals = crossover_service.detect_all_signals(indicators_df)
            
            # EMA 배열 분석
            latest_data = indicators_df.iloc[-1]
            ema_array = self._analyze_ema_array(latest_data)
            
            # 기존 인터페이스와 호환되는 형식으로 반환
            return {
                'ema_array': ema_array,
                'ema_crossover': signals.get('ema_analysis', {}).get('latest_crossover_type'),
                'macd_crossover': signals.get('macd_analysis', {}).get('latest_crossover_type'),
                'ema_crossover_status': signals.get('ema_analysis', {}),
                'macd_crossover_status': signals.get('macd_analysis', {}),
                'proximity_info': {
                    'ema_proximity': signals.get('ema_analysis', {}).get('current_proximity'),
                    'macd_proximity': signals.get('macd_analysis', {}).get('current_proximity')
                },
                'gap_ema20': self._calculate_gap(latest_data.get('Close', 0), latest_data.get('EMA20', 0)),
                'gap_ema40': self._calculate_gap(latest_data.get('Close', 0), latest_data.get('EMA40', 0))
            }
            
        except Exception as e:
            logging.error(f"[{ticker}] Error getting stock analysis data from cache: {e}")
            return None
    
    def _analyze_ema_array(self, latest_data):
        """EMA 배열 패턴 분석 - 새로운 EMAAnalyzer 사용"""
        return self.ema_analyzer.analyze_ema_array(latest_data)
    
    def _calculate_gap(self, close, ema):
        """종가와 EMA 간의 갭 계산"""
        # [메모] 2025-08-19: 수식 직접 구현을 중단하고 EMAAnalyzer.calculate_ema_gap로 일원화합니다.
        # 아래 기존 수식은 회귀 대비를 위해 주석으로 보존합니다.
        # if ema == 0:
        #     return 0
        # return ((close - ema) / ema * 100)
        try:
            return self.ema_analyzer.calculate_ema_gap(close, ema)
        except Exception:
            # 예외 시 보수적으로 0 반환
            return 0
    
    def get_latest_change_percent(self, ticker, timeframe='d', market_type='US'):
        """
        최신 등락률 계산 (df.iloc[-2] 방식 사용)
        다른 모든 곳에서 중복 계산을 제거하고 이 함수만 사용
        """
        try:
            # OHLCV 데이터 읽기
            from services.market.data_reading_service import DataReadingService
            data_reading_service = DataReadingService()
            df = data_reading_service.read_ohlcv_csv(ticker, market_type, timeframe)
            
            if df.empty or len(df) < 2:
                logging.warning(f"[{ticker}] 등락률 계산을 위한 충분한 데이터가 없습니다.")
                return 0.0
            
            # 최신 데이터와 이전 데이터
            latest = df.iloc[-1]
            previous = df.iloc[-2]
            
            current_close = latest['Close']
            previous_close = previous['Close']
            
            # 등락률 계산
            change_percent = ((current_close - previous_close) / previous_close) * 100
            
            return round(change_percent, 2)
            
        except Exception as e:
            logging.error(f"[{ticker}] 최신 등락률 계산 실패: {e}")
            return 0.0
    
    # 제거된 함수들:
    # - get_crossover_display_info() → services/analysis/crossover/display.py로 이동
    # - _get_crossover_meaning() → services/analysis/crossover/display.py로 이동
    
    def clear_cache(self):
        """캐시를 완전히 초기화"""
        self._indicators_cache.clear()
        logging.info("Technical indicators cache cleared")
    
    def clear_expired_cache(self):
        """만료된 캐시만 정리"""
        current_time = datetime.now()
        expired_keys = []
        
        for key, (cache_time, _) in self._indicators_cache.items():
            if (current_time - cache_time).seconds >= self._cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._indicators_cache[key]
        
        if expired_keys:
            logging.info(f"Cleared {len(expired_keys)} expired cache entries")
    
    def clear_invalid_cache(self):
        """잘못된 캐시 데이터 정리"""
        invalid_keys = []
        
        for key, (_, cached_data) in self._indicators_cache.items():
            if not isinstance(cached_data, pd.DataFrame):
                invalid_keys.append(key)
        
        for key in invalid_keys:
            del self._indicators_cache[key]
        
        if invalid_keys:
            logging.info(f"Cleared {len(invalid_keys)} invalid cache entries")


# 전역 인스턴스 생성
technical_indicators_service = TechnicalIndicatorsService() 