"""
Tulipy vs TA 라이브러리 지표 계산 비교 스크립트
기존 ta 라이브러리와 tulipy 라이브러리의 지표 계산 결과를 비교하여 CSV로 export

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

# tulipy 라이브러리 import (선택적)
try:
    import tulipy
    TULIPY_AVAILABLE = True
    print("✅ tulipy 라이브러리 사용 가능")
except ImportError:
    TULIPY_AVAILABLE = False
    print("❌ tulipy 라이브러리가 설치되지 않았습니다. pip install tulipy로 설치하세요.")
    sys.exit(1)

from services.market.data_reading_service import DataReadingService

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TulipyVsTAComparison:
    """Tulipy와 TA 라이브러리 지표 계산 비교 클래스"""
    
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
    
    def calculate_tulipy_indicators(self, df):
        """Tulipy 라이브러리로 지표 계산"""
        indicators_df = pd.DataFrame(index=df.index)
        
        try:
            # 데이터를 numpy 배열로 변환
            close_prices = df['Close'].values
            high_prices = df['High'].values
            low_prices = df['Low'].values
            volume_prices = df['Volume'].values
            
            # EMA 계산 (tulipy는 period를 사용)
            indicators_df['TULIPY_EMA5'] = tulipy.ema(close_prices, period=5)
            indicators_df['TULIPY_EMA20'] = tulipy.ema(close_prices, period=20)
            indicators_df['TULIPY_EMA40'] = tulipy.ema(close_prices, period=40)
            
            # MACD 계산 (tulipy는 fast_period, slow_period, signal_period 사용)
            macd_result = tulipy.macd(close_prices, fast_period=12, slow_period=26, signal_period=9)
            if len(macd_result) == 3:
                indicators_df['TULIPY_MACD'] = macd_result[0]
                indicators_df['TULIPY_MACD_Signal'] = macd_result[1]
                indicators_df['TULIPY_MACD_Histogram'] = macd_result[2]
            
            # RSI 계산
            indicators_df['TULIPY_RSI'] = tulipy.rsi(close_prices, period=14)
            
            # Stochastic 계산
            stoch_result = tulipy.stoch(high_prices, low_prices, close_prices, k_period=14, d_period=3)
            if len(stoch_result) == 2:
                indicators_df['TULIPY_Stoch_K'] = stoch_result[0]
                indicators_df['TULIPY_Stoch_D'] = stoch_result[1]
            
            # Bollinger Bands 계산
            bb_result = tulipy.bbands(close_prices, period=20, stddev=2)
            if len(bb_result) == 3:
                indicators_df['TULIPY_BB_Upper'] = bb_result[0]
                indicators_df['TULIPY_BB_Lower'] = bb_result[1]
                indicators_df['TULIPY_BB_Middle'] = bb_result[2]
            
            print("✅ Tulipy 라이브러리 지표 계산 완료")
            
        except Exception as e:
            print(f"❌ Tulipy 라이브러리 지표 계산 실패: {e}")
            
        return indicators_df
    
    def compare_indicators(self, ta_df, tulipy_df):
        """두 라이브러리의 지표 결과를 비교"""
        comparison_df = pd.DataFrame(index=ta_df.index)
        
        # 공통 컬럼들 찾기
        ta_columns = [col for col in ta_df.columns if col.startswith('TA_')]
        tulipy_columns = [col for col in tulipy_df.columns if col.startswith('TULIPY_')]
        
        for ta_col in ta_columns:
            # 대응하는 tulipy 컬럼 찾기
            tulipy_col = ta_col.replace('TA_', 'TULIPY_')
            
            if tulipy_col in tulipy_df.columns:
                # 두 지표 모두 존재하는 경우
                comparison_df[f'{ta_col}_vs_{tulipy_col}'] = ta_df[ta_col] - tulipy_df[tulipy_col]
                comparison_df[f'{ta_col}_vs_{tulipy_col}_pct'] = (
                    (ta_df[ta_col] - tulipy_df[tulipy_col]) / tulipy_df[tulipy_col] * 100
                ).fillna(0)
                
                # 상관관계 계산
                correlation = ta_df[ta_col].corr(tulipy_df[tulipy_col])
                comparison_df[f'{ta_col}_vs_{tulipy_col}_corr'] = correlation
                
                print(f"📊 {ta_col} vs {tulipy_col} - 상관관계: {correlation:.4f}")
        
        return comparison_df
    
    def export_comparison_results(self, ticker, timeframe, market_type, ta_df, tulipy_df, comparison_df):
        """비교 결과를 CSV로 export"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 결과 디렉토리 생성
        result_dir = os.path.join(self.results_dir, f"{ticker}_{timeframe}_{market_type}_{timestamp}")
        os.makedirs(result_dir, exist_ok=True)
        
        # 각 라이브러리별 결과 저장
        ta_file = os.path.join(result_dir, f"{ticker}_TA_indicators_{timeframe}.csv")
        ta_df.to_csv(ta_file)
        print(f"💾 TA 라이브러리 결과 저장: {ta_file}")
        
        tulipy_file = os.path.join(result_dir, f"{ticker}_TULIPY_indicators_{timeframe}.csv")
        tulipy_df.to_csv(tulipy_file)
        print(f"💾 Tulipy 라이브러리 결과 저장: {tulipy_file}")
        
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
            f.write(f"=== Tulipy vs TA 라이브러리 비교 리포트 ===\n")
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
        print(f"\n=== {ticker} Tulipy vs TA 라이브러리 비교 시작 ===")
        
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
            
            # 3. Tulipy 라이브러리로 지표 계산
            print(f"3. Tulipy 라이브러리로 지표 계산 중...")
            tulipy_indicators = self.calculate_tulipy_indicators(df)
            
            # 4. 지표 비교
            print(f"4. 지표 비교 중...")
            comparison_results = self.compare_indicators(ta_indicators, tulipy_indicators)
            
            # 5. 결과 export
            print(f"5. 결과 export 중...")
            result_dir = self.export_comparison_results(
                ticker, timeframe, market_type, 
                ta_indicators, tulipy_indicators, comparison_results
            )
            
            print(f"✅ {ticker} 비교 완료! 결과 저장 위치: {result_dir}")
            return result_dir
            
        except Exception as e:
            print(f"❌ {ticker} 비교 중 오류 발생: {e}")
            return None

def test_tulipy_vs_ta_comparison():
    """Tulipy vs TA 라이브러리 비교 테스트"""
    
    # 테스트할 종목들
    test_tickers = ['000270.KS', '000660.KS']  # 기아, SK하이닉스
    market_type = 'KOSPI'
    timeframe = 'd'
    
    # 비교 서비스 초기화
    comparison_service = TulipyVsTAComparison()
    
    print("=== Tulipy vs TA 라이브러리 비교 테스트 시작 ===")
    
    for ticker in test_tickers:
        print(f"\n--- {ticker} 테스트 ---")
        result_dir = comparison_service.run_comparison(ticker, market_type, timeframe)
        
        if result_dir:
            print(f"✅ {ticker} 테스트 완료: {result_dir}")
        else:
            print(f"❌ {ticker} 테스트 실패")
    
    print("\n=== 테스트 완료 ===")

if __name__ == "__main__":
    test_tulipy_vs_ta_comparison() 