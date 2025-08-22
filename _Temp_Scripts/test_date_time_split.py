import FinanceDataReader as fdr
import yfinance as yf
import pandas as pd
from datetime import datetime

def test_date_time_split():
    """Date와 Time 컬럼 분리 테스트"""
    print("=== Date와 Time 컬럼 분리 테스트 ===")
    
    # FinanceDataReader 데이터
    df_fdr = fdr.DataReader('005930', '2024-01-01', '2024-01-10')
    print("원본 FinanceDataReader 데이터:")
    print(df_fdr.head(3))
    print(f"인덱스 타입: {type(df_fdr.index[0])}")
    print(f"첫 번째 인덱스: {df_fdr.index[0]}")
    print("\n" + "="*50 + "\n")
    
    # 방법 1: Date와 Time 컬럼 추가 (인덱스 유지)
    df_with_datetime = df_fdr.copy()
    df_with_datetime['Date'] = df_with_datetime.index.date
    df_with_datetime['Time'] = df_with_datetime.index.time
    df_with_datetime['DateTime'] = df_with_datetime.index
    
    print("Date, Time 컬럼 추가 후 (인덱스 유지):")
    print(df_with_datetime.head(3))
    print(f"컬럼 목록: {df_with_datetime.columns.tolist()}")
    print("\n" + "="*50 + "\n")
    
    # 방법 2: 인덱스를 리셋하고 Date, Time을 별도 컬럼으로
    df_reset = df_fdr.reset_index()
    df_reset['Date_Str'] = df_reset['Date'].dt.strftime('%Y-%m-%d')
    df_reset['Time_Str'] = df_reset['Date'].dt.strftime('%H:%M:%S')
    df_reset['DateTime_Str'] = df_reset['Date'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    print("인덱스 리셋 후 Date, Time 분리:")
    print(df_reset.head(3))
    print(f"컬럼 목록: {df_reset.columns.tolist()}")
    print("\n" + "="*50 + "\n")
    
    # 방법 3: 문자열로 Date, Time 분리 (인덱스 유지)
    df_string = df_fdr.copy()
    df_string['Date'] = df_string.index.strftime('%Y-%m-%d')
    df_string['Time'] = df_string.index.strftime('%H:%M:%S')
    df_string['DateTime'] = df_string.index.strftime('%Y-%m-%d %H:%M:%S')
    
    print("문자열로 Date, Time 분리 (인덱스 유지):")
    print(df_string.head(3))
    print(f"컬럼 목록: {df_string.columns.tolist()}")
    
    return df_string

def test_yfinance_split():
    """yfinance 데이터도 테스트"""
    print("\n=== yfinance Date, Time 분리 테스트 ===")
    
    stock_yf = yf.Ticker('005930.KS')
    df_yf = stock_yf.history(start='2024-01-01', end='2024-01-10', auto_adjust=True)
    
    print("원본 yfinance 데이터:")
    print(df_yf.head(3))
    print(f"인덱스 타입: {type(df_yf.index[0])}")
    print(f"첫 번째 인덱스: {df_yf.index[0]}")
    print("\n" + "="*50 + "\n")
    
    # yfinance 데이터도 동일하게 분리
    df_yf_split = df_yf.copy()
    df_yf_split['Date'] = df_yf_split.index.strftime('%Y-%m-%d')
    df_yf_split['Time'] = df_yf_split.index.strftime('%H:%M:%S')
    df_yf_split['DateTime'] = df_yf_split.index.strftime('%Y-%m-%d %H:%M:%S')
    
    print("yfinance Date, Time 분리 후:")
    print(df_yf_split.head(3))
    print(f"컬럼 목록: {df_yf_split.columns.tolist()}")

if __name__ == "__main__":
    test_date_time_split()
    test_yfinance_split() 