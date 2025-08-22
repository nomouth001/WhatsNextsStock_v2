"""
Finta vs TA 라이브러리 지표 계산 비교 스크립트
기존 ta 라이브러리와 finta 라이브러리의 지표 계산 결과를 비교하여 CSV로 export

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

# finta 라이브러리 import (선택적)
try:
    from finta import TA
    FINTA_AVAILABLE = True
    print("✅ finta 라이브러리 사용 가능")
except ImportError as e:
    FINTA_AVAILABLE = False
    print(f"❌ finta 라이브러리가 설치되지 않았습니다. pip install finta로 설치하세요. 오류: {e}")
    sys.exit(1)
except Exception as e:
    FINTA_AVAILABLE = False
    print(f"❌ finta 라이브러리 import 중 오류 발생: {e}")
    sys.exit(1)

from services.market.data_reading_service import DataReadingService

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FintaVsTAComparison:
    """Finta와 TA 라이브러리 지표 계산 비교 클래스"""
    
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
            
            # Ichimoku 계산
            indicators_df['TA_Ichimoku_Tenkan'] = ta.trend.ichimoku_conversion_line(df['High'], df['Low'])
            indicators_df['TA_Ichimoku_Kijun'] = ta.trend.ichimoku_base_line(df['High'], df['Low'])
            indicators_df['TA_Ichimoku_Senkou_A'] = ta.trend.ichimoku_a(df['High'], df['Low'])
            indicators_df['TA_Ichimoku_Senkou_B'] = ta.trend.ichimoku_b(df['High'], df['Low'])
            
            print("✅ TA 라이브러리 지표 계산 완료")
            
        except Exception as e:
            print(f"❌ TA 라이브러리 지표 계산 실패: {e}")
            
        return indicators_df
    
    def calculate_finta_indicators(self, df):
        """Finta 라이브러리로 지표 계산"""
        indicators_df = pd.DataFrame(index=df.index)
        
        try:
            # EMA 계산
            try:
                ema5_result = TA.EMA(df, 5)
                if ema5_result is not None:
                    indicators_df['FINTA_EMA5'] = ema5_result
            except:
                pass
            
            try:
                ema20_result = TA.EMA(df, 20)
                if ema20_result is not None:
                    indicators_df['FINTA_EMA20'] = ema20_result
            except:
                pass
            
            try:
                ema40_result = TA.EMA(df, 40)
                if ema40_result is not None:
                    indicators_df['FINTA_EMA40'] = ema40_result
            except:
                pass
            
            # MACD 계산
            try:
                macd_result = TA.MACD(df, 12, 26, 9)
                if macd_result is not None and isinstance(macd_result, pd.DataFrame):
                    if 'MACD' in macd_result.columns:
                        indicators_df['FINTA_MACD'] = macd_result['MACD']
                    if 'SIGNAL' in macd_result.columns:
                        indicators_df['FINTA_MACD_Signal'] = macd_result['SIGNAL']
            except:
                pass
            
            # RSI 계산
            try:
                rsi_result = TA.RSI(df, 14)
                if rsi_result is not None:
                    indicators_df['FINTA_RSI'] = rsi_result
            except:
                pass
            
            # Bollinger Bands 계산
            try:
                bb_result = TA.BBANDS(df, 20, 2)
                if bb_result is not None and isinstance(bb_result, pd.DataFrame):
                    if 'BB_UPPER' in bb_result.columns:
                        indicators_df['FINTA_BB_Upper'] = bb_result['BB_UPPER']
                    if 'BB_LOWER' in bb_result.columns:
                        indicators_df['FINTA_BB_Lower'] = bb_result['BB_LOWER']
                    if 'BB_MIDDLE' in bb_result.columns:
                        indicators_df['FINTA_BB_Middle'] = bb_result['BB_MIDDLE']
            except:
                pass
            
            print("✅ Finta 라이브러리 지표 계산 완료")
            
        except Exception as e:
            print(f"❌ Finta 라이브러리 지표 계산 실패: {e}")
            
        return indicators_df
    
    def compare_indicators(self, ta_df, finta_df):
        """두 라이브러리의 지표 결과를 비교"""
        comparison_df = pd.DataFrame(index=ta_df.index)
        
        # 공통 컬럼들 찾기
        ta_columns = [col for col in ta_df.columns if col.startswith('TA_')]
        finta_columns = [col for col in finta_df.columns if col.startswith('FINTA_')]
        
        for ta_col in ta_columns:
            # 대응하는 finta 컬럼 찾기
            finta_col = ta_col.replace('TA_', 'FINTA_')
            
            if finta_col in finta_df.columns:
                # 두 지표 모두 존재하는 경우
                comparison_df[f'{ta_col}_vs_{finta_col}'] = ta_df[ta_col] - finta_df[finta_col]
                comparison_df[f'{ta_col}_vs_{finta_col}_pct'] = (
                    (ta_df[ta_col] - finta_df[finta_col]) / finta_df[finta_col] * 100
                ).fillna(0)
                
                # 상관관계 계산
                correlation = ta_df[ta_col].corr(finta_df[finta_col])
                comparison_df[f'{ta_col}_vs_{finta_col}_corr'] = correlation
                
                print(f"📊 {ta_col} vs {finta_col} - 상관관계: {correlation:.4f}")
        
        return comparison_df
    
    def export_comparison_results(self, ticker, timeframe, market_type, ta_df, finta_df, comparison_df):
        """비교 결과를 CSV로 export"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 결과 디렉토리 생성
        result_dir = os.path.join(self.results_dir, f"{ticker}_{timeframe}_{market_type}_{timestamp}")
        os.makedirs(result_dir, exist_ok=True)
        
        # 각 라이브러리별 결과 저장
        ta_file = os.path.join(result_dir, f"{ticker}_TA_indicators_{timeframe}.csv")
        ta_df.to_csv(ta_file)
        print(f"💾 TA 라이브러리 결과 저장: {ta_file}")
        
        finta_file = os.path.join(result_dir, f"{ticker}_FINTA_indicators_{timeframe}.csv")
        finta_df.to_csv(finta_file)
        print(f"💾 Finta 라이브러리 결과 저장: {finta_file}")
        
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
            f.write(f"=== Finta vs TA 라이브러리 비교 리포트 ===\n")
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
        print(f"\n=== {ticker} Finta vs TA 라이브러리 비교 시작 ===")
        
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
            
            # 3. Finta 라이브러리로 지표 계산
            print(f"3. Finta 라이브러리로 지표 계산 중...")
            finta_indicators = self.calculate_finta_indicators(df)
            
            # 4. 지표 비교
            print(f"4. 지표 비교 중...")
            comparison_results = self.compare_indicators(ta_indicators, finta_indicators)
            
            # 5. 결과 export
            print(f"5. 결과 export 중...")
            result_dir = self.export_comparison_results(
                ticker, timeframe, market_type, 
                ta_indicators, finta_indicators, comparison_results
            )
            
            print(f"✅ {ticker} 비교 완료! 결과 저장 위치: {result_dir}")
            return result_dir
            
        except Exception as e:
            print(f"❌ {ticker} 비교 중 오류 발생: {e}")
            return None

def test_finta_vs_ta_comparison():
    """Finta vs TA 라이브러리 비교 테스트"""
    
    # 테스트할 종목들 (KOSPI 데이터 사용)
    test_tickers = ['000270.KS', '000660.KS']  # 기아, SK하이닉스
    market_type = 'KOSPI'
    timeframe = 'd'
    
    # 비교 서비스 초기화
    comparison_service = FintaVsTAComparison()
    
    print("=== Finta vs TA 라이브러리 비교 테스트 시작 ===")
    
    for ticker in test_tickers:
        print(f"\n--- {ticker} 테스트 ---")
        result_dir = comparison_service.run_comparison(ticker, market_type, timeframe)
        
        if result_dir:
            print(f"✅ {ticker} 테스트 완료: {result_dir}")
        else:
            print(f"❌ {ticker} 테스트 실패")
    
    print("\n=== 테스트 완료 ===")

if __name__ == "__main__":
    test_finta_vs_ta_comparison() 