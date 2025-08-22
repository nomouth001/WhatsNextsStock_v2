"""
Finta 라이브러리 API 테스트 스크립트
"""

import pandas as pd
import numpy as np
from finta import TA

# 샘플 데이터 생성
dates = pd.date_range('2023-01-01', periods=100, freq='D')
np.random.seed(42)
data = {
    'Open': np.random.randn(100).cumsum() + 100,
    'High': np.random.randn(100).cumsum() + 102,
    'Low': np.random.randn(100).cumsum() + 98,
    'Close': np.random.randn(100).cumsum() + 100,
    'Volume': np.random.randint(1000, 10000, 100)
}
df = pd.DataFrame(data, index=dates)

print("=== Finta 라이브러리 API 테스트 ===")
print(f"데이터 형태: {df.shape}")
print(f"컬럼: {list(df.columns)}")
print(f"처음 5행:\n{df.head()}")

# EMA 계산 테스트
try:
    print("\n1. EMA 계산 테스트...")
    ema5 = TA.EMA(df, 5)
    print(f"✅ EMA(5) 계산 성공: {type(ema5)}")
    if isinstance(ema5, pd.Series):
        print(f"   결과 형태: {ema5.shape}, 처음 5개 값: {ema5.head().values}")
except Exception as e:
    print(f"❌ EMA 계산 실패: {e}")

# MACD 계산 테스트
try:
    print("\n2. MACD 계산 테스트...")
    macd = TA.MACD(df, 12, 26, 9)
    print(f"✅ MACD 계산 성공: {type(macd)}")
    if isinstance(macd, pd.DataFrame):
        print(f"   결과 형태: {macd.shape}, 컬럼: {list(macd.columns)}")
        print(f"   처음 5행:\n{macd.head()}")
except Exception as e:
    print(f"❌ MACD 계산 실패: {e}")

# RSI 계산 테스트
try:
    print("\n3. RSI 계산 테스트...")
    rsi = TA.RSI(df, 14)
    print(f"✅ RSI 계산 성공: {type(rsi)}")
    if isinstance(rsi, pd.Series):
        print(f"   결과 형태: {rsi.shape}, 처음 5개 값: {rsi.head().values}")
except Exception as e:
    print(f"❌ RSI 계산 실패: {e}")

# Bollinger Bands 계산 테스트
try:
    print("\n4. Bollinger Bands 계산 테스트...")
    bb = TA.BBANDS(df, 20, 2)
    print(f"✅ Bollinger Bands 계산 성공: {type(bb)}")
    if isinstance(bb, pd.DataFrame):
        print(f"   결과 형태: {bb.shape}, 컬럼: {list(bb.columns)}")
        print(f"   처음 5행:\n{bb.head()}")
except Exception as e:
    print(f"❌ Bollinger Bands 계산 실패: {e}")

# Stochastic 계산 테스트
try:
    print("\n5. Stochastic 계산 테스트...")
    stoch = TA.STOCH(df, 14, 3)
    print(f"✅ Stochastic 계산 성공: {type(stoch)}")
    if isinstance(stoch, pd.DataFrame):
        print(f"   결과 형태: {stoch.shape}, 컬럼: {list(stoch.columns)}")
        print(f"   처음 5행:\n{stoch.head()}")
except Exception as e:
    print(f"❌ Stochastic 계산 실패: {e}")

print("\n=== 테스트 완료 ===") 