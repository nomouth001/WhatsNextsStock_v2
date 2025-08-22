"""
간소화된 크로스오버 및 근접성 감지 서비스
90일 데이터를 사용하여 EMA5-EMA20, EMA5-EMA40, EMA20-EMA40, MACD-MACD_Signal 쌍의 
크로스오버와 근접성을 감지하고 별도 CSV 파일로 저장
"""

import logging
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple

class SimplifiedCrossoverDetector:
    """간소화된 크로스오버 및 근접성 감지 서비스"""
    
    # 동일 실행(run) 내 중복 저장 방지용 (티커-타임프레임-거래일 키)
    _created_today_keys = set()

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_period = 90  # 90일 데이터
        self.proximity_threshold = 0.03  # 3% 임계값
        self.recent_days_threshold = 5  # 최근 5일 이내 크로스오버만 의미있음
    
    def detect_all_signals(self, indicators_df: pd.DataFrame) -> Dict:
        """
        모든 신호를 한 번에 감지 (크로스오버 + 근접성)
        Args:
            indicators_df: 지표 데이터가 포함된 DataFrame
        Returns:
            통합 신호 정보 딕셔너리
        """
        try:
            if not self._validate_data(indicators_df):
                return {}
            
            # 90일 데이터 추출
            recent_data = self._prepare_data(indicators_df)
            
            # EMA 쌍별 분석
            ema_results = {}
            ema_pairs = [('EMA5', 'EMA20'), ('EMA5', 'EMA40'), ('EMA20', 'EMA40')]
            
            for ema1, ema2 in ema_pairs:
                ema_results[f"{ema1}_{ema2}"] = self._analyze_ema_pair(recent_data, ema1, ema2)
            
            # MACD 분석
            macd_results = self._analyze_macd_pair(recent_data)
            
            # EMA 통합 분석
            ema_integrated = self._integrate_ema_analysis(ema_results)
            
            # EMA 배열 분석 및 종가-EMA 갭 계산 추가
            ema_array_info = self._analyze_ema_array_and_gaps(recent_data)
            ema_integrated.update(ema_array_info)
            
            return {
                'ema_analysis': ema_integrated,
                'macd_analysis': macd_results,
                'ema_details': ema_results
            }
            
        except Exception as e:
            self.logger.error(f"Error in detect_all_signals: {str(e)}")
            return {}
    
    def detect_and_save_signals(self, indicators_df: pd.DataFrame, ticker: str, timeframe: str, market_type: str) -> Dict:
        """
        신호를 감지하고 별도 CSV 파일에 저장하는 통합 함수
        Args:
            indicators_df: 지표 데이터
            ticker: 종목 코드
            timeframe: 시간프레임 (d/w/m)
            market_type: 시장 타입 (KOSPI/KOSDAQ/US)
        Returns:
            저장 결과 딕셔너리
        """
        try:
            # 1. 신호 감지
            signals = self.detect_all_signals(indicators_df)
            
            if not signals:
                return {
                    'success': False,
                    'error': '신호 감지 실패'
                }
            
            # 2. 신호 정보를 별도 DataFrame으로 생성
            signals_df = self._create_signals_dataframe(signals, ticker, timeframe)
            
            # 2-1. 저장 파일의 거래일(데이터 기준 날짜) 결정: 지표 DF의 마지막 인덱스 사용
            try:
                last_idx = indicators_df.index[-1]
                trade_date_str = last_idx.strftime('%Y%m%d') if hasattr(last_idx, 'strftime') else str(last_idx)[:10].replace('-', '')
            except Exception:
                # 폴백: 시스템 현재 날짜
                trade_date_str = datetime.now().strftime('%Y%m%d')

            # 3. 동일 실행(run) 내 중복 저장 방지: 이미 오늘 생성한 경우 저장 스킵
            timezone = 'KST' if market_type.upper() in ['KOSPI', 'KOSDAQ'] else 'EST'
            created_key = f"{ticker}:{timeframe}:{trade_date_str}:{timezone}"

            if created_key in SimplifiedCrossoverDetector._created_today_keys:
                # 이미 동일 실행에서 생성됨 → 스킵
                market_folder = market_type.upper()
                save_dir = os.path.join("static", "data", market_folder)
                filename = f"{ticker}_CrossInfo_{timeframe}_{trade_date_str}_{timezone}.csv"
                saved_path = os.path.join(save_dir, filename)
                self.logger.info(f"[{ticker}] 동일 실행 내 CrossInfo 재생성 스킵: {saved_path}")
            else:
                # 최초 생성 또는 다른 실행 → 저장 수행 후 키 기록
                saved_path = self._save_signals_to_csv(signals_df, ticker, timeframe, market_type, trade_date_str=trade_date_str)
                SimplifiedCrossoverDetector._created_today_keys.add(created_key)
            
            return {
                'success': True,
                'signals': signals,
                'signals_csv_path': saved_path,
                'signals_data': signals_df.to_dict('records')[0] if not signals_df.empty else {},
                'analysis_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"[{ticker}] 신호 감지 및 저장 실패: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_data(self, data: pd.DataFrame) -> bool:
        """데이터 유효성 검증"""
        if data is None or data.empty:
            return False
        
        required_columns = ['EMA5', 'EMA20', 'EMA40', 'MACD', 'MACD_Signal']
        for col in required_columns:
            if col not in data.columns:
                self.logger.warning(f"Required column {col} not found")
                return False
        
        return True
    
    def _prepare_data(self, indicators_df: pd.DataFrame) -> pd.DataFrame:
        """90일 데이터 추출 및 검증"""
        if len(indicators_df) < self.data_period:
            self.logger.warning(f"Data length ({len(indicators_df)}) is less than required period ({self.data_period})")
            return indicators_df
        
        return indicators_df.tail(self.data_period)
    
    def _analyze_ema_pair(self, data: pd.DataFrame, ema1: str, ema2: str) -> Dict:
        """단일 EMA 쌍 분석"""
        try:
            # 크로스오버 감지
            crossover = self._detect_crossover(data, ema1, ema2)
            
            # 근접성 감지
            proximity = self._detect_proximity(data, ema1, ema2)
            
            return {
                'latest_crossover_type': crossover.get('type') if crossover else None,
                'latest_crossover_date': crossover.get('date') if crossover else None,
                'days_since_crossover': crossover.get('days_since') if crossover else None,
                'current_proximity': proximity.get('type') if isinstance(proximity, dict) else proximity,
                'proximity_pair': proximity.get('pair') if isinstance(proximity, dict) else f"{ema1}-{ema2}",
                'proximity_ratio': proximity.get('proximity_ratio') if isinstance(proximity, dict) else None,
                'proximity_direction': proximity.get('direction') if isinstance(proximity, dict) else None
            }
            
        except Exception as e:
            self.logger.error(f"Error in _analyze_ema_pair for {ema1}-{ema2}: {str(e)}")
            return {}
    
    def _analyze_macd_pair(self, data: pd.DataFrame) -> Dict:
        """MACD 쌍 분석"""
        try:
            # 크로스오버 감지
            crossover = self._detect_crossover(data, 'MACD', 'MACD_Signal')
            
            # 근접성 감지
            proximity = self._detect_proximity(data, 'MACD', 'MACD_Signal')
            
            return {
                'latest_crossover_type': crossover.get('type') if crossover else None,
                'latest_crossover_date': crossover.get('date') if crossover else None,
                'days_since_crossover': crossover.get('days_since') if crossover else None,
                'current_proximity': proximity.get('type', 'no_proximity') if isinstance(proximity, dict) else proximity
            }
            
        except Exception as e:
            self.logger.error(f"Error in _analyze_macd_pair: {str(e)}")
            return {}
    
    def _detect_crossover(self, data: pd.DataFrame, col1: str, col2: str) -> Optional[Dict]:
        """크로스오버 감지"""
        try:
            if len(data) < 2:
                return None
            
            # 최근 데이터에서 크로스오버 감지
            for i in range(len(data) - 1, 0, -1):
                current = data.iloc[i]
                previous = data.iloc[i-1]
                
                # col1이 col2를 상향 돌파 (골드크로스)
                if (previous[col1] <= previous[col2] and 
                    current[col1] > current[col2]):
                    days_since = self._calculate_days_ago(current.name)
                    return {
                        'type': 'golden_cross',
                        'date': current.name,
                        'col1': col1,
                        'col2': col2,
                        'col1_value': current[col1],
                        'col2_value': current[col2],
                        'strength': abs(current[col1] - current[col2]),
                        'days_since': days_since
                    }
                
                # col1이 col2를 하향 돌파 (데드크로스)
                elif (previous[col1] >= previous[col2] and 
                      current[col1] < current[col2]):
                    days_since = self._calculate_days_ago(current.name)
                    return {
                        'type': 'dead_cross',
                        'date': current.name,
                        'col1': col1,
                        'col2': col2,
                        'col1_value': current[col1],
                        'col2_value': current[col2],
                        'strength': abs(current[col1] - current[col2]),
                        'days_since': days_since
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in _detect_crossover for {col1}-{col2}: {str(e)}")
            return None
    
    def _detect_proximity(self, data: pd.DataFrame, col1: str, col2: str) -> Dict:
        """근접성 감지 - 어떤 EMA 쌍의 근접성인지 정보 포함"""
        try:
            if len(data) < 2:
                return {'type': 'no_proximity', 'pair': f"{col1}-{col2}"}
            
            latest = data.iloc[-1]
            prev = data.iloc[-2]
            
            # 두 지표의 차이 계산
            diff = abs(latest[col1] - latest[col2])
            avg = (latest[col1] + latest[col2]) / 2
            
            # 근접성 비율 계산
            proximity_ratio = diff / avg if avg != 0 else float('inf')
            
            # 5% 임계값을 초과하면 근접하지 않음
            if proximity_ratio > self.proximity_threshold:
                return {'type': 'no_proximity', 'pair': f"{col1}-{col2}"}
            
            # 기울기 계산
            col1_slope = self._calculate_slope(data, col1)
            col2_slope = self._calculate_slope(data, col2)
            
            # EMA 쌍에 따라 근접성 타입 결정
            pair_name = f"{col1}-{col2}"
            
            # MACD 쌍에 대한 근접성 타입 결정
            if pair_name == 'MACD-MACD_Signal':
                if (latest[col1] < latest[col2] and 
                    col1_slope > 0 and 
                    col1_slope > col2_slope):
                    proximity_type = 'golden_cross_proximity'
                elif (latest[col1] > latest[col2] and 
                      col1_slope < 0 and 
                      col1_slope < col2_slope):
                    proximity_type = 'dead_cross_proximity'
                else:
                    proximity_type = 'no_proximity'
                
                return {
                    'type': proximity_type,
                    'pair': pair_name,
                    'proximity_ratio': proximity_ratio,
                    'direction': 'bullish' if proximity_type == 'golden_cross_proximity' else 'bearish' if proximity_type == 'dead_cross_proximity' else 'neutral'
                }
            
            # 골드크로스 근접 판단
            if (latest[col1] < latest[col2] and 
                col1_slope > 0 and 
                col1_slope > col2_slope):
                
                if pair_name == 'EMA5-EMA20':
                    proximity_type = 'golden_cross1_proximity'
                elif pair_name == 'EMA5-EMA40':
                    proximity_type = 'golden_cross2_proximity'
                elif pair_name == 'EMA20-EMA40':
                    proximity_type = 'golden_cross3_proximity'
                else:
                    proximity_type = 'golden_cross_proximity'
                
                return {
                    'type': proximity_type,
                    'pair': pair_name,
                    'proximity_ratio': proximity_ratio,
                    'direction': 'bullish'
                }
            
            # 데드크로스 근접 판단
            elif (latest[col1] > latest[col2] and 
                  col1_slope < 0 and 
                  col1_slope < col2_slope):
                
                if pair_name == 'EMA5-EMA20':
                    proximity_type = 'dead_cross1_proximity'
                elif pair_name == 'EMA5-EMA40':
                    proximity_type = 'dead_cross2_proximity'
                elif pair_name == 'EMA20-EMA40':
                    proximity_type = 'dead_cross3_proximity'
                else:
                    proximity_type = 'dead_cross_proximity'
                
                return {
                    'type': proximity_type,
                    'pair': pair_name,
                    'proximity_ratio': proximity_ratio,
                    'direction': 'bearish'
                }
            
            return {'type': 'no_proximity', 'pair': pair_name}
            
        except Exception as e:
            self.logger.error(f"Error in _detect_proximity for {col1}-{col2}: {str(e)}")
            return {'type': 'no_proximity', 'pair': f"{col1}-{col2}"}
    
    def _calculate_slope(self, data: pd.DataFrame, column: str) -> float:
        """기울기 계산 (변화량)"""
        try:
            if len(data) < 2:
                return 0.0
            
            latest = data.iloc[-1][column]
            previous = data.iloc[-2][column]
            
            return latest - previous
            
        except Exception as e:
            self.logger.error(f"Error in _calculate_slope for {column}: {str(e)}")
            return 0.0
    
    def _integrate_ema_analysis(self, ema_results: Dict) -> Dict:
        """EMA 결과 통합 - 가장 최근의 크로스오버 선택 및 근접성 정보 포함"""
        try:
            latest_crossover = None
            latest_date = None
            
            # 가장 최근의 크로스오버 찾기
            for pair_name, result in ema_results.items():
                if result.get('latest_crossover_date'):
                    crossover_date = result['latest_crossover_date']
                    if latest_date is None or crossover_date > latest_date:
                        latest_date = crossover_date
                        
                        # EMA 쌍에 따라 크로스오버 타입 결정
                        crossover_type = result['latest_crossover_type']
                        if crossover_type:
                            if pair_name == 'EMA5_EMA20':
                                # EMA5-EMA20: 골드크로스1 또는 데드크로스1
                                if crossover_type == 'golden_cross':
                                    crossover_type = 'golden_cross1'
                                elif crossover_type == 'dead_cross':
                                    crossover_type = 'dead_cross1'
                            elif pair_name == 'EMA5_EMA40':
                                # EMA5-EMA40: 골드크로스2 또는 데드크로스2
                                if crossover_type == 'golden_cross':
                                    crossover_type = 'golden_cross2'
                                elif crossover_type == 'dead_cross':
                                    crossover_type = 'dead_cross2'
                            elif pair_name == 'EMA20_EMA40':
                                # EMA20-EMA40: 골드크로스3 또는 데드크로스3
                                if crossover_type == 'golden_cross':
                                    crossover_type = 'golden_cross3'
                                elif crossover_type == 'dead_cross':
                                    crossover_type = 'dead_cross3'
                        
                        latest_crossover = {
                            'type': crossover_type,
                            'date': result['latest_crossover_date'],
                            'days_since': result['days_since_crossover'],
                            'pair': pair_name.replace('_', '-')
                        }
            
            # 근접성 정보 통합
            proximity_info = self._determine_ema_proximity(ema_results)
            
            return {
                'latest_crossover_type': latest_crossover['type'] if latest_crossover else None,
                'latest_crossover_date': latest_crossover['date'] if latest_crossover else None,
                'days_since_crossover': latest_crossover['days_since'] if latest_crossover else None,
                'ema_pair': latest_crossover['pair'] if latest_crossover else None,
                'current_proximity': proximity_info.get('type') if isinstance(proximity_info, dict) else proximity_info,
                'proximity_pair': proximity_info.get('pair') if isinstance(proximity_info, dict) else None,
                'proximity_ratio': proximity_info.get('proximity_ratio') if isinstance(proximity_info, dict) else None,
                'proximity_direction': proximity_info.get('direction') if isinstance(proximity_info, dict) else None
            }
            
        except Exception as e:
            self.logger.error(f"Error in _integrate_ema_analysis: {str(e)}")
            return {}
    
    def _determine_ema_proximity(self, ema_results: Dict) -> Dict:
        """EMA 근접성 상태 결정 - 가장 중요한 근접성 정보 반환"""
        try:
            # 우선순위: EMA5-EMA20 > EMA5-EMA40 > EMA20-EMA40
            priority_pairs = ['EMA5_EMA20', 'EMA5_EMA40', 'EMA20_EMA40']
            
            for pair_name in priority_pairs:
                if pair_name in ema_results:
                    result = ema_results[pair_name]
                    proximity = result.get('current_proximity', 'no_proximity')
                    
                    if proximity != 'no_proximity':
                        return {
                            'type': proximity,
                            'pair': result.get('proximity_pair', pair_name.replace('_', '-')),
                            'proximity_ratio': result.get('proximity_ratio'),
                            'direction': result.get('proximity_direction')
                        }
            
            # 근접성이 없는 경우
            return {
                'type': 'no_proximity',
                'pair': None,
                'proximity_ratio': None,
                'direction': None
            }
            
        except Exception as e:
            self.logger.error(f"Error in _determine_ema_proximity: {str(e)}")
            return {
                'type': 'no_proximity',
                'pair': None,
                'proximity_ratio': None,
                'direction': None
            }
    
    def _analyze_ema_array_and_gaps(self, data: pd.DataFrame) -> Dict:
        """EMA 배열 패턴 분석 및 종가-EMA 갭 계산"""
        try:
            if data.empty:
                return {
                    'ema_array_pattern': '분석불가',
                    'ema_array_order': '분석불가',
                    'close_gap_ema20': 0.0,
                    'close_gap_ema40': 0.0
                }
            
            # 최신 데이터 추출
            latest_data = data.iloc[-1]
            
            # EMA 값들 추출 (대소문자 구분 없이)
            ema5 = None
            ema20 = None
            ema40 = None
            close = None
            
            # 종가 컬럼 찾기 (대소문자 구분 없이)
            for col in latest_data.index:
                col_lower = col.lower()
                if col_lower == 'close':
                    close = latest_data[col]
                    break
            
            # EMA 컬럼명 찾기 (대소문자 구분 없이)
            for col in latest_data.index:
                col_lower = col.lower()
                if 'ema5' in col_lower or 'ema_5' in col_lower:
                    ema5 = latest_data[col]
                elif 'ema20' in col_lower or 'ema_20' in col_lower:
                    ema20 = latest_data[col]
                elif 'ema40' in col_lower or 'ema_40' in col_lower:
                    ema40 = latest_data[col]
            
            # EMA 값이 없는 경우 기본값 처리
            if ema5 is None or ema20 is None or ema40 is None:
                return {
                    'ema_array_pattern': '분석불가',
                    'ema_array_order': '분석불가',
                    'close_gap_ema20': 0.0,
                    'close_gap_ema40': 0.0
                }
            
            # 종가가 없는 경우 기본값 처리
            if close is None or close == 0:
                return {
                    'ema_array_pattern': '분석불가',
                    'ema_array_order': '분석불가',
                    'close_gap_ema20': 0.0,
                    'close_gap_ema40': 0.0
                }
            
            # EMA 배열 순서 생성 (예: EMA5>EMA20>EMA40)
            ema_values = [
                ('EMA5', ema5),
                ('EMA20', ema20),
                ('EMA40', ema40)
            ]
            ema_values.sort(key=lambda x: x[1], reverse=True)
            ema_array_order = '>'.join([name for name, value in ema_values])
            
            # EMA 배열 패턴 판별
            ema_array_pattern = self._determine_ema_array_pattern(ema5, ema20, ema40)
            
            # 종가-EMA 갭 계산
            close_gap_ema20 = self._calculate_gap(close, ema20)
            close_gap_ema40 = self._calculate_gap(close, ema40)
            
            return {
                'ema_array_pattern': ema_array_pattern,
                'ema_array_order': ema_array_order,
                'close_gap_ema20': close_gap_ema20,
                'close_gap_ema40': close_gap_ema40
            }
            
        except Exception as e:
            self.logger.error(f"Error in _analyze_ema_array_and_gaps: {str(e)}")
            return {
                'ema_array_pattern': '분석불가',
                'ema_array_order': '분석불가',
                'close_gap_ema20': 0.0,
                'close_gap_ema40': 0.0
            }
    
    def _determine_ema_array_pattern(self, ema5: float, ema20: float, ema40: float) -> str:
        """EMA 배열 패턴 판별"""
        try:
            if ema5 > ema20 > ema40:
                return "상승추세"
            elif ema5 < ema20 < ema40:
                return "하락추세"
            elif ema5 > ema20 and ema20 < ema40:
                return "반등추세"
            elif ema5 < ema20 and ema20 > ema40:
                return "조정추세"
            elif ema5 > ema20 and ema20 > ema40:
                return "상승추세"
            else:
                return "횡보추세"
        except Exception as e:
            self.logger.error(f"Error in _determine_ema_array_pattern: {str(e)}")
            return "분석불가"
    
    def _calculate_gap(self, close: float, ema: float) -> float:
        """종가와 EMA 간의 갭 계산 (%)"""
        # [메모] 2025-08-19: 수식 직접 구현을 중단하고 EMAAnalyzer.calculate_ema_gap로 일원화합니다.
        # 아래 기존 수식은 회귀 대비를 위해 주석으로 보존합니다.
        # try:
        #     if ema == 0:
        #         return 0.0
        #     return ((close - ema) / ema * 100)
        # except Exception as e:
        #     self.logger.error(f"Error in _calculate_gap: {str(e)}")
        #     return 0.0
        try:
            from services.analysis.pattern.ema_analyzer import EMAAnalyzer
            return EMAAnalyzer().calculate_ema_gap(close, ema)
        except Exception as e:
            self.logger.error(f"Error in _calculate_gap via EMAAnalyzer: {str(e)}")
            return 0.0
    
    def _create_signals_dataframe(self, signals: Dict, ticker: str, timeframe: str) -> pd.DataFrame:
        """신호 정보를 별도 DataFrame으로 생성"""
        try:
            current_date = datetime.now()
            
            # EMA 분석 정보
            ema_analysis = signals.get('ema_analysis', {})
            
            # MACD 분석 정보
            macd_analysis = signals.get('macd_analysis', {})
            
            # MACD 근접성 정보 처리 - 딕셔너리인 경우 type 값만 추출
            macd_proximity = macd_analysis.get('current_proximity', 'no_proximity')
            if isinstance(macd_proximity, dict):
                macd_proximity_type = macd_proximity.get('type', 'no_proximity')
            else:
                macd_proximity_type = macd_proximity
            
            # 신호 데이터 구성
            signal_data = {
                'Date': [current_date],
                'Ticker': [ticker],
                'Timeframe': [timeframe],
                'EMA_Latest_Crossover_Type': [ema_analysis.get('latest_crossover_type')],
                'EMA_Latest_Crossover_Date': [ema_analysis.get('latest_crossover_date')],
                'EMA_Days_Since_Crossover': [ema_analysis.get('days_since_crossover')],
                'EMA_Crossover_Pair': [ema_analysis.get('ema_pair')],
                'EMA_Current_Proximity': [ema_analysis.get('current_proximity', 'no_proximity')],
                'EMA_Proximity_Pair': [ema_analysis.get('proximity_pair')],
                'EMA_Proximity_Ratio': [ema_analysis.get('proximity_ratio')],
                'EMA_Proximity_Direction': [ema_analysis.get('proximity_direction')],
                'MACD_Latest_Crossover_Type': [macd_analysis.get('latest_crossover_type')],
                'MACD_Latest_Crossover_Date': [macd_analysis.get('latest_crossover_date')],
                'MACD_Days_Since_Crossover': [macd_analysis.get('days_since_crossover')],
                'MACD_Current_Proximity': [macd_proximity_type],
                'Overall_Signal_Status': [self._determine_overall_status(signals)],
                'Signal_Strength': [self._calculate_signal_strength(signals)],
                'Analysis_Date': [current_date],
                # 새로운 컬럼들 추가
                'EMA_Array_Pattern': [ema_analysis.get('ema_array_pattern', '분석불가')],
                'EMA_Array_Order': [ema_analysis.get('ema_array_order', '분석불가')],
                'Close_Gap_EMA20': [ema_analysis.get('close_gap_ema20', 0.0)],
                'Close_Gap_EMA40': [ema_analysis.get('close_gap_ema40', 0.0)]
            }
            
            return pd.DataFrame(signal_data)
            
        except Exception as e:
            self.logger.error(f"Error in _create_signals_dataframe: {str(e)}")
            return pd.DataFrame()
    
    def _save_signals_to_csv(self, signals_df: pd.DataFrame, ticker: str, timeframe: str, market_type: str, trade_date_str: Optional[str] = None) -> str:
        """신호 정보를 별도 CSV 파일로 저장"""
        try:
            # 파일명 생성: {ticker}_CrossInfo_{timeframe}_YYYYMMDD_EST/KST.csv (거래일 기준)
            if not trade_date_str:
                trade_date_str = datetime.now().strftime('%Y%m%d')
            
            # 시간대 결정 (market_type에 따라)
            if market_type.upper() in ['KOSPI', 'KOSDAQ']:
                timezone = 'KST'
            else:
                timezone = 'EST'
            
            filename = f"{ticker}_CrossInfo_{timeframe}_{trade_date_str}_{timezone}.csv"
            
            # 저장 경로 결정
            market_folder = market_type.upper()
            save_dir = os.path.join("static", "data", market_folder)
            os.makedirs(save_dir, exist_ok=True)
            
            filepath = os.path.join(save_dir, filename)
            
            # CSV 저장
            signals_df.to_csv(filepath, index=False, encoding='utf-8')
            
            self.logger.info(f"[{ticker}] 신호 정보 CSV 저장 완료: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"[{ticker}] 신호 정보 CSV 저장 실패: {e}")
            return None
    
    def _determine_overall_status(self, signals: Dict) -> str:
        """전체 상태 결정"""
        try:
            # EMA 근접성 확인
            ema_proximity = signals.get('ema_analysis', {}).get('current_proximity', 'no_proximity')
            if ema_proximity != 'no_proximity':
                return '근접성 감지'
            
            # MACD 근접성 확인
            macd_proximity = signals.get('macd_analysis', {}).get('current_proximity', 'no_proximity')
            if macd_proximity != 'no_proximity':
                return '근접성 감지'
            
            # 최근 크로스오버 확인
            ema_days = signals.get('ema_analysis', {}).get('days_since_crossover')
            macd_days = signals.get('macd_analysis', {}).get('days_since_crossover')
            
            if (ema_days is not None and ema_days <= self.recent_days_threshold) or \
               (macd_days is not None and macd_days <= self.recent_days_threshold):
                return '최근 크로스오버'
            
            return '정상'
            
        except Exception as e:
            self.logger.error(f"Error in _determine_overall_status: {str(e)}")
            return '정상'
    
    def _calculate_signal_strength(self, signals: Dict) -> float:
        """신호 강도 계산"""
        try:
            strength = 0.0
            
            # 근접성 가중치 (높음)
            ema_proximity = signals.get('ema_analysis', {}).get('current_proximity', 'no_proximity')
            macd_proximity = signals.get('macd_analysis', {}).get('current_proximity', 'no_proximity')
            
            if ema_proximity != 'no_proximity' or macd_proximity != 'no_proximity':
                strength += 0.8
            
            # 최근 크로스오버 가중치 (중간)
            ema_days = signals.get('ema_analysis', {}).get('days_since_crossover')
            macd_days = signals.get('macd_analysis', {}).get('days_since_crossover')
            
            if ema_days is not None and ema_days <= self.recent_days_threshold:
                strength += 0.6 * (1 - ema_days / self.recent_days_threshold)
            
            if macd_days is not None and macd_days <= self.recent_days_threshold:
                strength += 0.6 * (1 - macd_days / self.recent_days_threshold)
            
            return min(strength, 1.0)
            
        except Exception as e:
            self.logger.error(f"Error in _calculate_signal_strength: {str(e)}")
            return 0.0
    
    def _calculate_days_ago(self, date: datetime) -> int:
        """날짜 차이 계산"""
        try:
            today = datetime.now().date()
            if isinstance(date, datetime):
                date = date.date()
            elif isinstance(date, str):
                date = datetime.strptime(date, '%Y-%m-%d').date()
            
            return (today - date).days
        except Exception as e:
            self.logger.error(f"Error in _calculate_days_ago: {str(e)}")
            return 999  # 오류 시 큰 값 반환
    
    # 기존 호환성 유지 메서드들
    def detect_crossovers_only(self, indicators_df: pd.DataFrame) -> Dict:
        """크로스오버만 감지 (기존 호환성 유지)"""
        signals = self.detect_all_signals(indicators_df)
        return {
            'ema_crossover': signals.get('ema_analysis', {}),
            'macd_crossover': signals.get('macd_analysis', {})
        }
    
    def detect_proximity_only(self, indicators_df: pd.DataFrame) -> Dict:
        """근접성만 감지 (기존 호환성 유지)"""
        signals = self.detect_all_signals(indicators_df)
        return {
            'ema_proximity': signals.get('ema_analysis', {}).get('current_proximity'),
            'macd_proximity': signals.get('macd_analysis', {}).get('current_proximity')
        }
    
    # get_market_summary 함수 제거됨 - MarketSummaryService 사용 