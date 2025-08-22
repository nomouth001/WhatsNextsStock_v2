"""
Backtrader vs TA 라이브러리 지표 계산 비교 스크립트
기존 ta 라이브러리와 backtrader 라이브러리의 지표 계산 결과를 비교하여 CSV로 export

[경고] 분석/비교용 스크립트입니다. 프로덕션 코드에서 import/호출하지 마세요.
- 본 스크립트는 `TechnicalIndicatorsService`를 대체하지 않으며, 결과는 연구/검증 목적에 한정됩니다.
"""

import sys
import os
import pandas as pd
import numpy as np
import logging
from datetime import datetime
import glob

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 기존 ta 라이브러리 import
import ta

# backtrader 라이브러리 import (선택적)
try:
    import backtrader as bt
    BACKTRADER_AVAILABLE = True
    print("✅ backtrader 라이브러리 사용 가능")
except ImportError as e:
    BACKTRADER_AVAILABLE = False
    print(f"❌ backtrader 라이브러리가 설치되지 않았습니다. pip install backtrader로 설치하세요. 오류: {e}")
    sys.exit(1)
except Exception as e:
    BACKTRADER_AVAILABLE = False
    print(f"❌ backtrader 라이브러리 import 중 오류 발생: {e}")
    sys.exit(1)

from services.market.data_reading_service import DataReadingService

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BacktraderVsTAComparison:
    """Backtrader와 TA 라이브러리 지표 계산 비교 클래스"""
    
    def __init__(self):
        self.data_reading_service = DataReadingService()
        self.results_dir = "static/data/comparison_results"
        os.makedirs(self.results_dir, exist_ok=True)
        
    def calculate_ta_indicators(self, df):
        """TA 라이브러리로 지표 계산"""
        indicators_df = pd.DataFrame(index=df.index)
        
        try:
            # EMA 계산
            indicators_df['TA_EMA5'] = ta.trend.ema_indicator(df['Close'], window=5)
            indicators_df['TA_EMA20'] = ta.trend.ema_indicator(df['Close'], window=20)
            indicators_df['TA_EMA40'] = ta.trend.ema_indicator(df['Close'], window=40)
            
            # MACD 계산
            macd = ta.trend.MACD(df['Close'])
            indicators_df['TA_MACD'] = macd.macd()
            indicators_df['TA_MACD_Signal'] = macd.macd_signal()
            indicators_df['TA_MACD_Histogram'] = macd.macd_diff()
            
            # RSI 계산
            indicators_df['TA_RSI'] = ta.momentum.rsi(df['Close'], window=14)
            
            # Stochastic 계산
            stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'])
            indicators_df['TA_Stoch_K'] = stoch.stoch()
            indicators_df['TA_Stoch_D'] = stoch.stoch_signal()
            
            # Bollinger Bands 계산
            bb = ta.volatility.BollingerBands(df['Close'])
            indicators_df['TA_BB_Upper'] = bb.bollinger_hband()
            indicators_df['TA_BB_Lower'] = bb.bollinger_lband()
            indicators_df['TA_BB_Middle'] = bb.bollinger_mavg()
            
            print("✅ TA 라이브러리 지표 계산 완료")
            
        except Exception as e:
            print(f"❌ TA 라이브러리 지표 계산 실패: {e}")
            
        return indicators_df
    
    def calculate_backtrader_indicators(self, df):
        """Backtrader 라이브러리로 지표 계산"""
        indicators_df = pd.DataFrame(index=df.index)
        
        try:
            # backtrader용 데이터 준비
            # backtrader는 특정 컬럼명을 요구합니다
            bt_df = df.copy()
            bt_df.columns = [col.title() for col in bt_df.columns]  # 첫 글자 대문자로
            
            # backtrader 데이터 피드 생성
            data = bt.feeds.PandasData(
                dataname=bt_df,
                datetime=None,  # 인덱스가 날짜
                open='Open',
                high='High', 
                low='Low',
                close='Close',
                volume='Volume',
                openinterest=-1
            )
            
            # backtrader 전략 클래스 정의
            class IndicatorStrategy(bt.Strategy):
                def __init__(self):
                    # EMA 계산
                    self.ema5 = bt.indicators.EMA(self.data.close, period=5)
                    self.ema20 = bt.indicators.EMA(self.data.close, period=20)
                    self.ema40 = bt.indicators.EMA(self.data.close, period=40)
                    
                    # MACD 계산
                    self.macd = bt.indicators.MACD(self.data.close)
                    
                    # RSI 계산
                    self.rsi = bt.indicators.RSI(self.data.close, period=14)
                    
                    # Stochastic 계산
                    self.stoch = bt.indicators.Stochastic(self.data)
                    
                    # Bollinger Bands 계산
                    self.bbands = bt.indicators.BollingerBands(self.data.close, period=20, devfactor=2)
                    
                    # 결과 저장용 리스트
                    self.ema5_values = []
                    self.ema20_values = []
                    self.ema40_values = []
                    self.macd_values = []
                    self.macd_signal_values = []
                    self.macd_histogram_values = []
                    self.rsi_values = []
                    self.stoch_k_values = []
                    self.stoch_d_values = []
                    self.bb_upper_values = []
                    self.bb_lower_values = []
                    self.bb_middle_values = []
                
                def next(self):
                    # 각 지표 값 저장
                    self.ema5_values.append(self.ema5[0] if len(self.ema5) > 0 else np.nan)
                    self.ema20_values.append(self.ema20[0] if len(self.ema20) > 0 else np.nan)
                    self.ema40_values.append(self.ema40[0] if len(self.ema40) > 0 else np.nan)
                    
                    self.macd_values.append(self.macd.macd[0] if len(self.macd.macd) > 0 else np.nan)
                    self.macd_signal_values.append(self.macd.signal[0] if len(self.macd.signal) > 0 else np.nan)
                    self.macd_histogram_values.append(self.macd.macd[0] - self.macd.signal[0] if len(self.macd.macd) > 0 and len(self.macd.signal) > 0 else np.nan)
                    
                    self.rsi_values.append(self.rsi[0] if len(self.rsi) > 0 else np.nan)
                    
                    self.stoch_k_values.append(self.stoch.lines.percK[0] if len(self.stoch.lines.percK) > 0 else np.nan)
                    self.stoch_d_values.append(self.stoch.lines.percD[0] if len(self.stoch.lines.percD) > 0 else np.nan)
                    
                    self.bb_upper_values.append(self.bbands.lines.top[0] if len(self.bbands.lines.top) > 0 else np.nan)
                    self.bb_lower_values.append(self.bbands.lines.bot[0] if len(self.bbands.lines.bot) > 0 else np.nan)
                    self.bb_middle_values.append(self.bbands.lines.mid[0] if len(self.bbands.lines.mid) > 0 else np.nan)
            
            # backtrader 엔진 생성 및 실행
            cerebro = bt.Cerebro()
            cerebro.adddata(data)
            cerebro.addstrategy(IndicatorStrategy)
            
            # 결과 저장용 변수
            strategy = None
            
            # 전략 실행
            results = cerebro.run()
            if results:
                strategy = results[0]
                
                # 결과를 DataFrame에 저장 (데이터 길이 맞춤)
                if strategy.ema5_values and len(strategy.ema5_values) == len(indicators_df):
                    indicators_df['BACKTRADER_EMA5'] = strategy.ema5_values
                if strategy.ema20_values and len(strategy.ema20_values) == len(indicators_df):
                    indicators_df['BACKTRADER_EMA20'] = strategy.ema20_values
                if strategy.ema40_values and len(strategy.ema40_values) == len(indicators_df):
                    indicators_df['BACKTRADER_EMA40'] = strategy.ema40_values
                
                if strategy.macd_values and len(strategy.macd_values) == len(indicators_df):
                    indicators_df['BACKTRADER_MACD'] = strategy.macd_values
                if strategy.macd_signal_values and len(strategy.macd_signal_values) == len(indicators_df):
                    indicators_df['BACKTRADER_MACD_Signal'] = strategy.macd_signal_values
                if strategy.macd_histogram_values and len(strategy.macd_histogram_values) == len(indicators_df):
                    indicators_df['BACKTRADER_MACD_Histogram'] = strategy.macd_histogram_values
                
                if strategy.rsi_values and len(strategy.rsi_values) == len(indicators_df):
                    indicators_df['BACKTRADER_RSI'] = strategy.rsi_values
                
                if strategy.stoch_k_values and len(strategy.stoch_k_values) == len(indicators_df):
                    indicators_df['BACKTRADER_Stoch_K'] = strategy.stoch_k_values
                if strategy.stoch_d_values and len(strategy.stoch_d_values) == len(indicators_df):
                    indicators_df['BACKTRADER_Stoch_D'] = strategy.stoch_d_values
                
                if strategy.bb_upper_values and len(strategy.bb_upper_values) == len(indicators_df):
                    indicators_df['BACKTRADER_BB_Upper'] = strategy.bb_upper_values
                if strategy.bb_lower_values and len(strategy.bb_lower_values) == len(indicators_df):
                    indicators_df['BACKTRADER_BB_Lower'] = strategy.bb_lower_values
                if strategy.bb_middle_values and len(strategy.bb_middle_values) == len(indicators_df):
                    indicators_df['BACKTRADER_BB_Middle'] = strategy.bb_middle_values
            
            print("✅ Backtrader 라이브러리 지표 계산 완료")
            
        except Exception as e:
            print(f"❌ Backtrader 라이브러리 지표 계산 실패: {e}")
            
        return indicators_df
    
    def compare_indicators(self, ta_df, backtrader_df):
        """두 라이브러리의 지표 결과를 비교"""
        comparison_df = pd.DataFrame(index=ta_df.index)
        
        # 공통 컬럼들 찾기
        ta_columns = [col for col in ta_df.columns if col.startswith('TA_')]
        backtrader_columns = [col for col in backtrader_df.columns if col.startswith('BACKTRADER_')]
        
        for ta_col in ta_columns:
            # 대응하는 backtrader 컬럼 찾기
            backtrader_col = ta_col.replace('TA_', 'BACKTRADER_')
            
            if backtrader_col in backtrader_df.columns:
                # 두 지표 모두 존재하는 경우
                comparison_df[f'{ta_col}_vs_{backtrader_col}'] = ta_df[ta_col] - backtrader_df[backtrader_col]
                comparison_df[f'{ta_col}_vs_{backtrader_col}_pct'] = (
                    (ta_df[ta_col] - backtrader_df[backtrader_col]) / backtrader_df[backtrader_col] * 100
                ).fillna(0)
                
                # 상관관계 계산
                correlation = ta_df[ta_col].corr(backtrader_df[backtrader_col])
                comparison_df[f'{ta_col}_vs_{backtrader_col}_corr'] = correlation
                
                print(f"📊 {ta_col} vs {backtrader_col} - 상관관계: {correlation:.4f}")
        
        return comparison_df
    
    def export_comparison_results(self, ticker, timeframe, market_type, ta_df, backtrader_df, comparison_df):
        """비교 결과를 CSV로 export"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 결과 디렉토리 생성
        result_dir = os.path.join(self.results_dir, f"{ticker}_{timeframe}_{market_type}_{timestamp}")
        os.makedirs(result_dir, exist_ok=True)
        
        # 각 라이브러리별 결과 저장
        ta_file = os.path.join(result_dir, f"{ticker}_TA_indicators_{timeframe}.csv")
        ta_df.to_csv(ta_file)
        print(f"💾 TA 라이브러리 결과 저장: {ta_file}")
        
        backtrader_file = os.path.join(result_dir, f"{ticker}_BACKTRADER_indicators_{timeframe}.csv")
        backtrader_df.to_csv(backtrader_file)
        print(f"💾 Backtrader 라이브러리 결과 저장: {backtrader_file}")
        
        # 비교 결과 저장
        comparison_file = os.path.join(result_dir, f"{ticker}_comparison_{timeframe}.csv")
        comparison_df.to_csv(comparison_file)
        print(f"💾 비교 결과 저장: {comparison_file}")
        
        # 요약 리포트 생성
        summary_file = os.path.join(result_dir, f"{ticker}_summary_{timeframe}.txt")
        self._create_summary_report(summary_file, ticker, timeframe, market_type, comparison_df)
        print(f"📄 요약 리포트 생성: {summary_file}")
        
        return result_dir
    
    def _create_summary_report(self, summary_file, ticker, timeframe, market_type, comparison_df):
        """요약 리포트 생성"""
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"=== Backtrader vs TA 라이브러리 비교 리포트 ===\n")
            f.write(f"티커: {ticker}\n")
            f.write(f"시간프레임: {timeframe}\n")
            f.write(f"시장타입: {market_type}\n")
            f.write(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"데이터 행수: {len(comparison_df)}\n\n")
            
            # 상관관계 요약
            correlation_cols = [col for col in comparison_df.columns if 'corr' in col]
            f.write("=== 상관관계 요약 ===\n")
            for col in correlation_cols:
                corr_value = comparison_df[col].iloc[0] if not comparison_df[col].isna().all() else 0
                f.write(f"{col}: {corr_value:.4f}\n")
            
            # 차이값 요약
            diff_cols = [col for col in comparison_df.columns if 'vs' in col and 'corr' not in col and 'pct' not in col]
            f.write("\n=== 평균 차이값 요약 ===\n")
            for col in diff_cols:
                mean_diff = comparison_df[col].mean()
                std_diff = comparison_df[col].std()
                f.write(f"{col}: 평균={mean_diff:.6f}, 표준편차={std_diff:.6f}\n")
    
    def run_comparison(self, ticker, market_type='KOSPI', timeframe='d'):
        """메인 비교 실행 함수"""
        print(f"\n=== {ticker} Backtrader vs TA 라이브러리 비교 시작 ===")
        
        try:
            # 1. OHLCV 데이터 읽기
            print(f"1. {ticker} OHLCV 데이터 읽기 중...")
            df = self.data_reading_service.read_ohlcv_csv(ticker, timeframe, market_type)
            
            if df.empty:
                print(f"❌ {ticker} 데이터가 없습니다.")
                return None
            
            print(f"✅ {ticker} 데이터 로드 완료: {len(df)}행")
            
            # 2. TA 라이브러리로 지표 계산
            print(f"2. TA 라이브러리로 지표 계산 중...")
            ta_indicators = self.calculate_ta_indicators(df)
            
            # 3. Backtrader 라이브러리로 지표 계산
            print(f"3. Backtrader 라이브러리로 지표 계산 중...")
            backtrader_indicators = self.calculate_backtrader_indicators(df)
            
            # 4. 지표 비교
            print(f"4. 지표 비교 중...")
            comparison_results = self.compare_indicators(ta_indicators, backtrader_indicators)
            
            # 5. 결과 export
            print(f"5. 결과 export 중...")
            result_dir = self.export_comparison_results(
                ticker, timeframe, market_type, 
                ta_indicators, backtrader_indicators, comparison_results
            )
            
            print(f"✅ {ticker} 비교 완료! 결과 저장 위치: {result_dir}")
            return result_dir
            
        except Exception as e:
            print(f"❌ {ticker} 비교 중 오류 발생: {e}")
            return None

def test_backtrader_vs_ta_comparison():
    """Backtrader vs TA 라이브러리 비교 테스트"""
    
    # 테스트할 종목들 (KOSPI 데이터 사용)
    test_tickers = ['000270.KS', '000660.KS']  # 기아, SK하이닉스
    market_type = 'KOSPI'
    timeframe = 'd'
    
    # 비교 서비스 초기화
    comparison_service = BacktraderVsTAComparison()
    
    print("=== Backtrader vs TA 라이브러리 비교 테스트 시작 ===")
    
    for ticker in test_tickers:
        print(f"\n--- {ticker} 테스트 ---")
        result_dir = comparison_service.run_comparison(ticker, market_type, timeframe)
        
        if result_dir:
            print(f"✅ {ticker} 테스트 완료: {result_dir}")
        else:
            print(f"❌ {ticker} 테스트 실패")
    
    print("\n=== 테스트 완료 ===")

if __name__ == "__main__":
    test_backtrader_vs_ta_comparison() 