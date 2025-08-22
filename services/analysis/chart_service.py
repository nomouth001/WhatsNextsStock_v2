"""
차트 생성 전용 서비스
일봉, 주봉, 월봉 차트를 생성하는 기능을 담당
"""

import os
import logging
import pandas as pd
import base64
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import mplfinance as mpf
import glob
from datetime import datetime
from typing import Dict, Optional, Tuple
from services.technical_indicators_service import technical_indicators_service

# 한글 폰트 설정
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'Malgun Gothic', 'NanumGothic', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

class ChartService:
    """차트 생성 전용 서비스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_charts(self, ticker: str, market_type: str = 'KOSPI') -> Tuple[Dict, Optional[str]]:
        """
        일봉, 주봉, 월봉 차트를 생성합니다.
        Args:
            ticker: 종목 코드
            market_type: 시장 타입
        Returns:
            (차트 데이터 딕셔너리, 오류 메시지)
        """
        try:
            ticker = ticker.upper()
            
            # 디버그 로그 시작
            debug_log_path = os.path.join("logs", f"chart_generation_debug_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            os.makedirs("logs", exist_ok=True)
            
            with open(debug_log_path, 'w', encoding='utf-8') as f:
                f.write(f"=== 차트 생성 디버그 로그 ===\n")
                f.write(f"티커: {ticker}\n")
                f.write(f"시장타입: {market_type}\n")
                f.write(f"시작 시간: {datetime.now()}\n")
            
            # market_type을 실제 폴더명으로 변환
            if market_type.upper() in ['KOSPI', 'KOSDAQ']:
                actual_market_type = market_type.upper()
            elif market_type.upper() == 'US':
                actual_market_type = 'US'
            else:
                actual_market_type = 'KOSPI'
            
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(f"실제 시장타입: {actual_market_type}\n")
            
            # 저장된 데이터 파일 찾기
            data_dir = os.path.join("static/data", actual_market_type)
            if not os.path.exists(data_dir):
                error_msg = f"데이터 디렉토리를 찾을 수 없습니다: {data_dir}"
                with open(debug_log_path, 'a', encoding='utf-8') as f:
                    f.write(f"오류: {error_msg}\n")
                return {}, error_msg
            
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(f"데이터 디렉토리: {data_dir}\n")
            
            # glob 패턴을 사용한 파일 검색
            ohlcv_pattern = os.path.join(data_dir, f"{ticker}_ohlcv_d_*.csv")
            ohlcv_files = glob.glob(ohlcv_pattern)
            
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(f"파일 검색 패턴: {ohlcv_pattern}\n")
                f.write(f"찾은 일봉 파일들: {ohlcv_files}\n")
            
            if not ohlcv_files:
                error_msg = f"{ticker}의 저장된 데이터를 찾을 수 없습니다."
                with open(debug_log_path, 'a', encoding='utf-8') as f:
                    f.write(f"오류: {error_msg}\n")
                return {}, error_msg
            
            # 가장 최신 파일 선택 (glob로 이미 전체 경로 반환)
            ohlcv_path = max(ohlcv_files)
            
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(f"선택된 일봉 파일: {os.path.basename(ohlcv_path)}\n")
                f.write(f"파일 경로: {ohlcv_path}\n")
            
            # OHLCV 데이터 로드
            try:
                # [메모] 2025-08-19: CSV 직접 파싱을 중단하고 DataReadingService 단일 진입점 사용
                # 기존 직접 파싱 로직은 회귀 대비를 위해 아래에 주석 보존합니다.
                # 기존 코드 블록 (메타데이터 스캔 및 pd.read_csv):
                # with open(ohlcv_path, 'r', encoding='utf-8-sig') as f:
                #     lines = f.readlines()
                # ... data_start_line 계산 ...
                # if data_start_line > 0:
                #     df = pd.read_csv(ohlcv_path, skiprows=data_start_line, index_col=0, parse_dates=True)
                # else:
                #     df = pd.read_csv(ohlcv_path, index_col=0, parse_dates=True)
                from services.market.data_reading_service import DataReadingService
                _drs_tmp = DataReadingService()
                df = _drs_tmp.read_ohlcv_csv(ticker, actual_market_type, 'd')
                if df is None or df.empty:
                    raise ValueError('DataReadingService에서 빈 데이터 반환')
                with open(debug_log_path, 'a', encoding='utf-8') as f:
                    f.write(f"데이터 로드 성공(서비스). 행 수: {len(df)}, 컬럼: {list(df.columns)}\n")
            except Exception as e:
                error_msg = f"OHLCV 로드 실패: {e}"
                with open(debug_log_path, 'a', encoding='utf-8') as f:
                    f.write(f"오류: {error_msg}\n")
                return {}, error_msg
            
            if df.empty:
                error_msg = "저장된 데이터가 비어있습니다."
                with open(debug_log_path, 'a', encoding='utf-8') as f:
                    f.write(f"오류: {error_msg}\n")
                return {}, error_msg
            
            # 인덱스를 DatetimeIndex로 변환
            try:
                df.index = pd.to_datetime(df.index, utc=True)
                # UTC 시간대 제거 (로컬 시간으로 변환)
                df.index = df.index.tz_localize(None)
                with open(debug_log_path, 'a', encoding='utf-8') as f:
                    f.write(f"인덱스 변환 성공. 인덱스 범위: {df.index.min()} ~ {df.index.max()}\n")
            except Exception as e:
                error_msg = f"날짜 인덱스 변환에 실패했습니다: {e}"
                with open(debug_log_path, 'a', encoding='utf-8') as f:
                    f.write(f"오류: {error_msg}\n")
                return {}, error_msg
            
            # OHLCV 컬럼 정규화
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                with open(debug_log_path, 'a', encoding='utf-8') as f:
                    f.write(f"MultiIndex 컬럼 정규화 완료. 컬럼: {list(df.columns)}\n")
            
            # 필요한 컬럼만 선택
            required_columns = ["Open", "High", "Low", "Close", "Volume"]
            if not all(col in df.columns for col in required_columns):
                error_msg = f"필요한 OHLCV 컬럼이 없습니다. 현재 컬럼: {list(df.columns)}"
                with open(debug_log_path, 'a', encoding='utf-8') as f:
                    f.write(f"오류: {error_msg}\n")
                return {}, error_msg
            
            df = df[required_columns].dropna()
            
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(f"데이터 전처리 완료. 최종 행 수: {len(df)}\n")
                f.write(f"최근 5개 데이터:\n{df.tail()}\n")
            
            # 차트 생성
            charts = {}
            
            # 일봉 차트
            daily_chart = self.create_chart_image(df, f"{ticker} 일봉 차트", "d", ticker, market_type)
            if daily_chart:
                # 2025-08-09: 템플릿 구조에 맞게 딕셔너리로 변경 (templates/analysis/ai_analysis.html에서 charts.daily.base64 기대)
                charts['daily'] = {
                    'base64': daily_chart,
                    'filename': f"{ticker}_daily_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                }
                # # 기존 코드 (롤백용) - 템플릿 구조 불일치로 인해 base64 데이터가 빈 상태로 전달됨
                # charts['daily'] = daily_chart
            
            # 주봉 차트 (주봉 데이터가 있는 경우)
            try:
                from services.market.data_reading_service import DataReadingService
                _drs_tmp = DataReadingService()
                weekly_df = _drs_tmp.read_ohlcv_csv(ticker, actual_market_type, 'w')
                if weekly_df is not None and not weekly_df.empty:
                    weekly_df = weekly_df[required_columns].dropna()
                    weekly_chart = self.create_chart_image(weekly_df, f"{ticker} 주봉 차트", "w", ticker, market_type)
                    if weekly_chart:
                        charts['weekly'] = {
                            'base64': weekly_chart,
                            'filename': f"{ticker}_weekly_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        }
            except Exception as e:
                self.logger.warning(f"주봉 차트 생성 실패: {e}")
            
            # 월봉 차트 (월봉 데이터가 있는 경우)
            try:
                from services.market.data_reading_service import DataReadingService
                _drs_tmp = DataReadingService()
                monthly_df = _drs_tmp.read_ohlcv_csv(ticker, actual_market_type, 'm')
                if monthly_df is not None and not monthly_df.empty:
                    monthly_df = monthly_df[required_columns].dropna()
                    monthly_chart = self.create_chart_image(monthly_df, f"{ticker} 월봉 차트", "m", ticker, market_type)
                    if monthly_chart:
                        charts['monthly'] = {
                            'base64': monthly_chart,
                            'filename': f"{ticker}_monthly_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        }
            except Exception as e:
                self.logger.warning(f"월봉 차트 생성 실패: {e}")
            
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(f"차트 생성 완료. 생성된 차트: {list(charts.keys())}\n")
            
            return charts, None
            
        except Exception as e:
            error_msg = f"차트 생성 중 오류 발생: {e}"
            self.logger.error(error_msg)
            return {}, error_msg
    
    def create_chart_image(self, df: pd.DataFrame, title: str, timeframe: str, 
                          ticker: str, market_type: str = 'US') -> Optional[str]:
        """
        차트 이미지를 생성하고 base64로 인코딩합니다 (기존 방식 복원)
        Args:
            df: OHLCV 데이터
            title: 차트 제목 (사용되지 않음, 내부에서 생성)
            timeframe: 시간프레임
            ticker: 종목 코드
            market_type: 시장 타입
        Returns:
            base64 인코딩된 이미지 또는 None
        """
        # # 기존 코드 (롤백용) - 간소화된 차트 생성 방식
        # try:
        #     self.logger.info(f"[{ticker}] 차트 생성 시작: {title}")
        #     
        #     # 데이터 전처리
        #     df = df.copy()
        #     df = df.dropna()
        #     
        #     if df.empty:
        #         self.logger.warning(f"[{ticker}] 빈 DataFrame으로 차트 생성 불가")
        #         return None
        #     
        #     # 기본 OHLCV 컬럼 확인
        #     required_cols = ['Open', 'High', 'Low', 'Close']
        #     if not all(col in df.columns for col in required_cols):
        #         self.logger.error(f"[{ticker}] 필수 OHLCV 컬럼 누락: {list(df.columns)}")
        #         return None
        #     
        #     # 지표 로딩 시도 (실패해도 계속 진행)
        #     try:
        #         df = self._load_saved_indicators(df, ticker, timeframe, market_type)
        #         self.logger.info(f"[{ticker}] 지표 데이터 로드 성공")
        #     except Exception as e:
        #         self.logger.warning(f"[{ticker}] 지표 로딩 실패, 기본 차트로 진행: {e}")
        #     
        #     # 기술적 지표 계산 시도 (실패해도 계속 진행)
        #     try:
        #         df = self._calculate_technical_indicators(df)
        #         add_plots = self._add_technical_indicators(df)
        #         self.logger.info(f"[{ticker}] 기술적 지표 계산 성공")
        #     except Exception as e:
        #         self.logger.warning(f"[{ticker}] 지표 계산 실패, 기본 차트로 진행: {e}")
        #         add_plots = []
        #     
        #     # 차트 스타일 설정
        #     try:
        #         style = self._setup_chart_style(market_type)
        #     except:
        #         style = 'yahoo'  # 기본 스타일
        #     
        #     # 차트 생성 (단계별 fallback)
        #     chart_created = False
        #     fig = None
        #     
        #     # 1단계: 모든 기능 포함 차트 시도
        #     try:
        #         fig, axes = mpf.plot(
        #             df[required_cols],
        #             type='candle',
        #             title=title,
        #             style=style,
        #             addplot=add_plots if add_plots else None,
        #             volume=True if 'Volume' in df.columns else False,
        #             figsize=(12, 8),
        #             returnfig=True
        #         )
        #         chart_created = True
        #         self.logger.info(f"[{ticker}] 전체 기능 차트 생성 성공")
        #         
        #     except Exception as e:
        #         self.logger.warning(f"[{ticker}] 전체 기능 차트 실패: {e}")
        #         
        #         # 2단계: 기본 캔들차트만 시도
        #         try:
        #             fig, axes = mpf.plot(
        #                 df[required_cols],
        #                 type='candle',
        #                 title=title,
        #                 volume=False,
        #                 figsize=(12, 6),
        #                 returnfig=True
        #             )
        #             chart_created = True
        #             self.logger.info(f"[{ticker}] 기본 캔들차트 생성 성공")
        #             
        #         except Exception as e2:
        #             self.logger.error(f"[{ticker}] 기본 차트 생성도 실패: {e2}")
        #             return None
        #     
        #     if not chart_created or fig is None:
        #         return None
        #     
        #     # base64 인코딩
        #     try:
        #         img_buffer = io.BytesIO()
        #         fig.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
        #         img_buffer.seek(0)
        #         img_str = base64.b64encode(img_buffer.getvalue()).decode()
        #         
        #         plt.close(fig)
        #         
        #         self.logger.info(f"[{ticker}] 차트 생성 완료: {title}")
        #         return img_str
        #         
        #     except Exception as e:
        #         self.logger.error(f"[{ticker}] 이미지 인코딩 실패: {e}")
        #         if fig:
        #             plt.close(fig)
        #         return None
        #     
        # except Exception as e:
        #     self.logger.error(f"[{ticker}] 차트 이미지 생성 실패: {e}")
        #     return None
        
        # 새로운 코드 - 기존 아카이브 방식 복원
        try:
            self.logger.info(f"[{ticker}] 기존 방식 차트 생성 시작")
            
            # 데이터 전처리
            df = df.copy()
            df = df.dropna()
            
            if df.empty:
                self.logger.warning(f"[{ticker}] 빈 DataFrame으로 차트 생성 불가")
                return None
            
            # 데이터 포인트 수 제한 (사용자 요구사항)
            data_limit_map = {
                '일봉': 41, 'Daily': 41, 'd': 41,
                '주봉': 41, 'Weekly': 41, 'w': 41,
                '월봉': 37, 'Monthly': 37, 'm': 37
            }
            
            # timeframe에 따른 데이터 포인트 수 결정
            data_limit = data_limit_map.get(timeframe, 41)  # 기본값 41
            
            # 최신 데이터만 유지
            if len(df) > data_limit:
                df = df.tail(data_limit)
                self.logger.info(f"[{ticker}] 데이터 포인트 제한: {len(df)}개 (timeframe: {timeframe}, limit: {data_limit})")
            else:
                self.logger.info(f"[{ticker}] 전체 데이터 사용: {len(df)}개 (timeframe: {timeframe})")
            
            # 기본 OHLCV 컬럼 확인
            required_cols = ['Open', 'High', 'Low', 'Close']
            if not all(col in df.columns for col in required_cols):
                self.logger.error(f"[{ticker}] 필수 OHLCV 컬럼 누락: {list(df.columns)}")
                return None
            
            # 지표 로딩
            try:
                # ❌ 기존: df = self._calculate_technical_indicators(df)
                # ✅ 새로운: 
                indicators_df = self._load_indicators_from_csv(ticker, timeframe, market_type)
                
                if not indicators_df.empty:
                    # Close 컬럼 중복 방지: indicators_df에서 Close 컬럼 제거
                    indicators_df_clean = indicators_df.drop(columns=['Close'], errors='ignore')
                    # OHLCV 데이터와 지표 데이터 결합
                    df = df.join(indicators_df_clean, how='left')
                    self.logger.info(f"[{ticker}] 지표 데이터 준비 완료 (컬럼 수: {len(indicators_df_clean.columns)})")
                else:
                    self.logger.warning(f"[{ticker}] 지표 데이터가 비어있음, 기본 차트로 진행")
            except Exception as e:
                self.logger.warning(f"[{ticker}] 지표 로딩 실패, 기본 차트로 진행: {e}")
            
            # 복합 제목 생성 (아카이브 방식)
            if len(df) > 0:
                latest = df.iloc[-1]
                close = latest['Close']
                
                # 등락률 계산 (TechnicalIndicatorsService 사용)
                change_percent = technical_indicators_service.get_latest_change_percent(ticker, timeframe, market_type)
                
                # 최신 데이터 날짜
                data_date = df.index[-1].strftime('%Y-%m-%d')
                
                # timeframe 영어 변환
                timeframe_map = {'일봉': 'Daily', '주봉': 'Weekly', '월봉': 'Monthly'}
                if timeframe in timeframe_map:
                    timeframe_en = timeframe_map[timeframe]
                elif timeframe == 'd':
                    timeframe_en = 'Daily'
                elif timeframe == 'w':
                    timeframe_en = 'Weekly'
                elif timeframe == 'm':
                    timeframe_en = 'Monthly'
                else:
                    timeframe_en = timeframe
                
                # EMA 값들 추출 (기본값 사용)
                ema5 = latest.get('EMA5', close)
                ema20 = latest.get('EMA20', close)
                ema40 = latest.get('EMA40', close)
                
                # Gap 계산
                gap_ema20 = ((close - ema20) / ema20 * 100) if ema20 != 0 else 0.0
                gap_ema40 = ((close - ema40) / ema40 * 100) if ema40 != 0 else 0.0
                
                # 볼린저 밴드 값들
                bb_upper = latest.get('BB_Upper', close)
                bb_lower = latest.get('BB_Lower', close)
                bb_ma = latest.get('BB_Middle', close)
                if pd.isna(bb_ma):
                    bb_ma = latest.get('BB_MA', close)
                
                # 복합 제목 생성 (BB 정보 제거)
                complex_title = (
                    f"{ticker} - {timeframe_en} Chart (as of {data_date})\n"
                    f"Close: {close:.2f} ({change_percent:+.2f}%), "
                    f"EMA5: {ema5:.2f}, EMA20: {ema20:.2f}, EMA40: {ema40:.2f}\n"
                    f"Gap EMA20: {gap_ema20:.2f}%, EMA40: {gap_ema40:.2f}%"
                )
            else:
                complex_title = f"{ticker} - {timeframe} Chart"
            
            # 완전한 addplot 구성 (아카이브 방식)
            apds = []
            
            # 볼린저 밴드 (개별 라인으로 단순화)
            if 'BB_Upper' in df.columns:
                apds.append(mpf.make_addplot(df['BB_Upper'], color='grey', width=0.5, alpha=0.7))
            if 'BB_Lower' in df.columns:
                apds.append(mpf.make_addplot(df['BB_Lower'], color='grey', width=0.5, alpha=0.7))
            
            # 볼린저 밴드 중앙선
            bb_middle_col = 'BB_Middle' if 'BB_Middle' in df.columns else ('BB_MA' if 'BB_MA' in df.columns else None)
            if bb_middle_col:
                apds.append(mpf.make_addplot(df[bb_middle_col], color='black', width=1.2))
            
            # EMA 라인들
            if 'EMA5' in df.columns:
                apds.append(mpf.make_addplot(df["EMA5"], color="red", width=1.0))
            if 'EMA20' in df.columns:
                apds.append(mpf.make_addplot(df["EMA20"], color="orange", width=1.2))
            if 'EMA40' in df.columns:
                apds.append(mpf.make_addplot(df["EMA40"], color="green", width=1.5))
            
            # MACD 패널 (panel=2) - Volume이 panel=1을 사용하므로 MACD는 panel=2 사용
            macd_col = 'MACD' if 'MACD' in df.columns else None
            macd_signal_col = 'MACD_Signal' if 'MACD_Signal' in df.columns else None
            macd_hist_col = 'MACD_Histogram' if 'MACD_Histogram' in df.columns else ('MACD_Hist' if 'MACD_Hist' in df.columns else None)
            
            if macd_col:
                apds.append(mpf.make_addplot(df[macd_col], panel=2, color="purple", ylabel=f"MACD_{timeframe_en}"))
            if macd_signal_col:
                apds.append(mpf.make_addplot(df[macd_signal_col], panel=2, color="red"))
            if macd_hist_col:
                apds.append(mpf.make_addplot(df[macd_hist_col], type='bar', panel=2, color='gray', alpha=0.5))
            
            # MACD 제로 라인
            if macd_col:
                apds.append(mpf.make_addplot([0]*len(df), panel=2, color='black', linestyle='--'))
            
            self.logger.info(f"[{ticker}] addplot 구성 완료: {len(apds)}개 요소")
            
            # 차트 생성 (아카이브 방식)
            try:
                # Volume 컬럼 존재 여부 확인
                has_volume = 'Volume' in df.columns
                self.logger.info(f"[{ticker}] Volume 컬럼 존재: {has_volume}, 사용 가능한 컬럼: {list(df.columns)}")
                
                # 패널 비율 결정 (MACD panel=1, Volume panel=2)
                has_macd_panel = any('panel' in str(plot) for plot in apds)
                has_volume = 'Volume' in df.columns
                
                if has_volume and has_macd_panel:
                    panel_ratios = (4, 1, 1)  # 메인, 볼륨, MACD
                elif has_volume:
                    panel_ratios = (4, 1)  # 메인, 볼륨
                elif has_macd_panel:
                    panel_ratios = (3, 1)  # 메인, MACD
                else:
                    panel_ratios = None  # 기본값
                
                # Volume addplot 추가 (panel=1 사용, MACD는 panel=2)
                if has_volume:
                    # Volume을 panel=1에 추가
                    volume_plot = mpf.make_addplot(df['Volume'], panel=1, type='bar', color='lightblue', alpha=0.7, ylabel='Volume')
                    apds.insert(0, volume_plot)  # 맨 앞에 추가
                
                self.logger.info(f"[{ticker}] 최종 addplot 구성: {len(apds)}개 요소, volume: {has_volume}, macd: {has_macd_panel}")
                
                # 차트 생성 (Volume과 addplot 함께 사용)
                fig, axes = mpf.plot(
                    df[required_cols],
                    type="candle",
                    style="charles",  # 전문적인 스타일
                    volume=False,  # addplot으로 Volume 처리하므로 비활성화
                    title=complex_title,
                    ylabel="Price",
                    addplot=apds if apds else None,
                    panel_ratios=panel_ratios,
                    figsize=(15, 10),  # 높이 약간 증가 (볼륨 패널 고려)
                    warn_too_much_data=100,  # 경고 제거
                    returnfig=True
                )
                
                # 차트 후처리: 제목 폰트 크기 조정, 여백 조정 및 범례 추가
                try:
                    # 제목 폰트 크기 2배로 증가
                    if fig._suptitle:
                        current_fontsize = fig._suptitle.get_fontsize()
                        fig._suptitle.set_fontsize(current_fontsize * 2)
                        self.logger.info(f"[{ticker}] 제목 폰트 크기 조정: {current_fontsize} -> {current_fontsize * 2}")
                    
                    # 타이틀과 차트 간 여백 조정
                    fig.subplots_adjust(top=0.85)  # 상단 여백 확보
                    self.logger.info(f"[{ticker}] 타이틀 여백 조정 완료")
                    
                    # 범례 추가 (자동 위치 설정)
                    main_ax = axes[0] if isinstance(axes, list) else axes
                    legend_elements = []
                    
                    # EMA 라인들 범례
                    if 'EMA5' in df.columns:
                        legend_elements.append(plt.Line2D([0], [0], color='red', linewidth=2, label='EMA5'))
                    if 'EMA20' in df.columns:
                        legend_elements.append(plt.Line2D([0], [0], color='orange', linewidth=2, label='EMA20'))
                    if 'EMA40' in df.columns:
                        legend_elements.append(plt.Line2D([0], [0], color='green', linewidth=2, label='EMA40'))
                    
                    # 볼린저 밴드 범례
                    if 'BB_Upper' in df.columns and 'BB_Lower' in df.columns:
                        legend_elements.append(plt.Line2D([0], [0], color='grey', linewidth=1, label='Bollinger Bands'))
                    
                    bb_middle_col = 'BB_Middle' if 'BB_Middle' in df.columns else ('BB_MA' if 'BB_MA' in df.columns else None)
                    if bb_middle_col:
                        legend_elements.append(plt.Line2D([0], [0], color='black', linewidth=2, label='BB Middle'))
                    
                    # 메인 차트 범례 표시 (자동 위치, 폰트 크기 증가)
                    if legend_elements:
                        main_ax.legend(handles=legend_elements, loc='best', fontsize=14, framealpha=0.9)
                        self.logger.info(f"[{ticker}] 메인 차트 범례 추가 완료: {len(legend_elements)}개 항목")
                    
                    # MACD 범례 추가 (별도 패널)
                    if len(axes) > 2:  # MACD 패널이 존재하는 경우 (panel=2)
                        macd_ax = axes[2]
                        macd_legend_elements = []
                        
                        # MACD 지표들 범례
                        if macd_col:
                            macd_legend_elements.append(plt.Line2D([0], [0], color='purple', linewidth=2, label='MACD'))
                        if macd_signal_col:
                            macd_legend_elements.append(plt.Line2D([0], [0], color='red', linewidth=2, label='MACD Signal'))
                        if macd_hist_col:
                            macd_legend_elements.append(plt.Rectangle((0, 0), 1, 1, facecolor='gray', alpha=0.5, label='MACD Histogram'))
                        
                        # MACD 패널 범례 표시 (왼쪽 위 고정, 폰트 크기 증가)
                        if macd_legend_elements:
                            macd_ax.legend(handles=macd_legend_elements, loc='upper left', fontsize=14, framealpha=0.9)
                            self.logger.info(f"[{ticker}] MACD 범례 추가 완료 (왼쪽 위 고정): {len(macd_legend_elements)}개 항목")
                    
                except Exception as e:
                    self.logger.warning(f"[{ticker}] 차트 후처리 실패: {e}")
                
                # base64 인코딩
                img_buffer = io.BytesIO()
                fig.savefig(img_buffer, format='png', dpi=120, bbox_inches='tight')
                img_buffer.seek(0)
                img_str = base64.b64encode(img_buffer.getvalue()).decode()
                
                plt.close(fig)
                
                self.logger.info(f"[{ticker}] 기존 방식 차트 생성 완료")
                return img_str
                
            except Exception as e:
                self.logger.error(f"[{ticker}] 기존 방식 차트 생성 실패: {e}")
                
                # Fallback: 간단한 차트
                try:
                    has_volume_fallback = 'Volume' in df.columns
                    fig, axes = mpf.plot(
                        df[required_cols],
                        type='candle',
                        title=complex_title,
                        volume=has_volume_fallback,
                        figsize=(12, 8),
                        warn_too_much_data=100,  # 경고 제거
                        returnfig=True
                    )
                    
                    # Fallback 차트 후처리: 제목 폰트 크기 조정 및 여백 조정
                    try:
                        if fig._suptitle:
                            current_fontsize = fig._suptitle.get_fontsize()
                            fig._suptitle.set_fontsize(current_fontsize * 2)
                            self.logger.info(f"[{ticker}] Fallback 제목 폰트 크기 조정: {current_fontsize} -> {current_fontsize * 2}")
                        
                        # Fallback 차트도 타이틀 여백 조정
                        fig.subplots_adjust(top=0.85)
                        self.logger.info(f"[{ticker}] Fallback 타이틀 여백 조정 완료")
                    except Exception as e:
                        self.logger.warning(f"[{ticker}] Fallback 차트 후처리 실패: {e}")
                    
                    img_buffer = io.BytesIO()
                    fig.savefig(img_buffer, format='png', dpi=120, bbox_inches='tight')
                    img_buffer.seek(0)
                    img_str = base64.b64encode(img_buffer.getvalue()).decode()
                    
                    plt.close(fig)
                    
                    self.logger.info(f"[{ticker}] Fallback 차트 생성 완료")
                    return img_str
                    
                except Exception as e2:
                    self.logger.error(f"[{ticker}] Fallback 차트도 실패: {e2}")
                    return None
            
        except Exception as e:
            self.logger.error(f"[{ticker}] 차트 이미지 생성 실패: {e}")
            return None
    
    def _load_saved_indicators(self, df: pd.DataFrame, ticker: str, timeframe: str, 
                              market_type: str = 'US') -> pd.DataFrame:
        """
        저장된 지표 데이터를 로드합니다.
        Args:
            df: OHLCV 데이터
            ticker: 종목 코드
            timeframe: 시간프레임
            market_type: 시장 타입
        Returns:
            지표가 추가된 DataFrame
        """
        try:
            # 지표 파일 경로
            data_dir = os.path.join("static/data", market_type)
            indicator_files = glob.glob(os.path.join(data_dir, f"{ticker}_*_indicators_{timeframe[0]}_*.csv"))
            
            if indicator_files:
                # 기존 직접 파일 로딩 방식은 주석으로 보존하고, 서비스 호출로 대체합니다.
                # 기존 코드:
                # latest_indicator_file = max(indicator_files)
                # indicators_df = pd.read_csv(latest_indicator_file, index_col=0)
                # indicators_df.index = pd.to_datetime(indicators_df.index, utc=True).tz_localize(None)
                try:
                    from services.technical_indicators_service import TechnicalIndicatorsService
                    _tis_tmp = TechnicalIndicatorsService()
                    indicators_df = _tis_tmp.read_indicators_csv(ticker, market_type, timeframe)
                    
                    if indicators_df is not None and not indicators_df.empty:
                        # 공통 인덱스만 사용
                        common_index = df.index.intersection(indicators_df.index)
                        if len(common_index) > 0:
                            df = df.loc[common_index]
                            indicators_df = indicators_df.loc[common_index]
                            
                            # 지표 컬럼들을 원본 데이터에 추가
                            for col in indicators_df.columns:
                                if col not in df.columns:
                                    df[col] = indicators_df[col]
                except Exception as e:
                    self.logger.warning(f"지표 데이터 로드 실패(서비스): {e}")
            
            return df
            
        except Exception as e:
            self.logger.error(f"지표 데이터 로드 중 오류: {e}")
            return df
    
    def _load_indicators_from_csv(self, ticker: str, timeframe: str, market_type: str) -> pd.DataFrame:
        """저장된 indicators CSV에서 지표 데이터 로드"""
        try:
            from services.technical_indicators_service import TechnicalIndicatorsService
            indicators_service = TechnicalIndicatorsService()
            
            # 지표 CSV 확인 및 자동 생성
            if not indicators_service.ensure_indicators_exist(ticker, timeframe, market_type):
                self.logger.error(f"[{ticker}] 지표 CSV 생성 실패")
                return pd.DataFrame()
            
            # 인자 순서: read_indicators_csv(ticker, market_type, timeframe)
            return indicators_service.read_indicators_csv(ticker, market_type, timeframe)
        except Exception as e:
            self.logger.error(f"지표 CSV 읽기 실패: {e}")
            return pd.DataFrame()

    # 🚫 중복 계산 함수 제거됨 - TechnicalIndicatorsService를 사용하세요
    # def _calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame: # 중복 제거를 위해 삭제됨
    
    def _setup_chart_style(self, market_type: str):
        """
        차트 스타일을 설정합니다.
        Args:
            market_type: 시장 타입
        Returns:
            차트 스타일
        """
        if market_type.upper() in ['KOSPI', 'KOSDAQ']:
            # 한국식 색상 (빨간색 상승, 파란색 하락)
            return mpf.make_mpf_style(
                base_mpf_style='charles',
                marketcolors=mpf.make_marketcolors(
                    up='red',
                    down='blue',
                    edge='inherit',
                    wick='inherit',
                    volume='in',
                    ohlc='inherit'
                ),
                gridstyle='',
                y_on_right=False
            )
        else:
            # 미국식 색상 (초록색 상승, 빨간색 하락)
            return mpf.make_mpf_style(
                base_mpf_style='charles',
                marketcolors=mpf.make_marketcolors(
                    up='green',
                    down='red',
                    edge='inherit',
                    wick='inherit',
                    volume='in',
                    ohlc='inherit'
                ),
                gridstyle='',
                y_on_right=False
            )
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> list:
        """
        차트에 기술적 지표를 추가합니다.
        Args:
            df: OHLCV + 지표 데이터
        Returns:
            추가할 플롯 리스트
        """
        add_plots = []
        
        try:
            # EMA 추가
            if 'EMA5' in df.columns:
                add_plots.append(mpf.make_addplot(df['EMA5'], color='orange', width=0.7))
            if 'EMA20' in df.columns:
                add_plots.append(mpf.make_addplot(df['EMA20'], color='blue', width=0.7))
            if 'EMA40' in df.columns:
                add_plots.append(mpf.make_addplot(df['EMA40'], color='red', width=0.7))
            
            # 볼린저 밴드 추가
            if 'BB_Upper' in df.columns and 'BB_Lower' in df.columns:
                add_plots.append(mpf.make_addplot(df['BB_Upper'], color='gray', width=0.5, alpha=0.7))
                add_plots.append(mpf.make_addplot(df['BB_Lower'], color='gray', width=0.5, alpha=0.7))
            
            return add_plots
            
        except Exception as e:
            self.logger.error(f"기술적 지표 추가 중 오류: {e}")
            return add_plots
    
    def _save_chart_debug_log(self, ticker: str, timeframe: str, df: pd.DataFrame) -> str:
        """
        차트 생성 디버그 로그를 저장합니다.
        Args:
            ticker: 종목 코드
            timeframe: 시간프레임
            df: 데이터
        Returns:
            로그 파일 경로
        """
        try:
            debug_log_path = os.path.join("logs", f"chart_debug_{ticker}_{timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            os.makedirs("logs", exist_ok=True)
            
            with open(debug_log_path, 'w', encoding='utf-8') as f:
                f.write(f"=== 차트 디버그 로그 ===\n")
                f.write(f"티커: {ticker}\n")
                f.write(f"시간프레임: {timeframe}\n")
                f.write(f"데이터 형태: {df.shape}\n")
                f.write(f"컬럼: {list(df.columns)}\n")
                f.write(f"최근 5개 데이터:\n{df.tail()}\n")
            
            return debug_log_path
            
        except Exception as e:
            self.logger.error(f"디버그 로그 저장 실패: {e}")
            return "" 