import FinanceDataReader as fdr
import yfinance as yf
import pandas as pd
from datetime import datetime

def test_compatible_structure():
    """호환성을 고려한 Date, Date_Index, Time_Index 구조 테스트"""
    print("=== 호환성을 고려한 구조 테스트 ===")
    
    # FinanceDataReader 데이터
    df_fdr = fdr.DataReader('005930', '2024-01-01', '2024-01-10')
    print("원본 FinanceDataReader 데이터:")
    print(df_fdr.head(3))
    print(f"컬럼 목록: {df_fdr.columns.tolist()}")
    print("\n" + "="*50 + "\n")
    
    # 호환성을 고려한 구조로 변환
    df_compatible = df_fdr.copy()
    df_compatible['Date_Index'] = df_compatible.index.strftime('%Y-%m-%d')
    df_compatible['Time_Index'] = df_compatible.index.strftime('%H:%M:%S')
    
    print("호환성을 고려한 구조로 변환 후:")
    print(df_compatible.head(3))
    print(f"컬럼 목록: {df_compatible.columns.tolist()}")
    print("\n" + "="*50 + "\n")
    
    # yfinance 데이터도 테스트
    stock_yf = yf.Ticker('005930.KS')
    df_yf = stock_yf.history(start='2024-01-01', end='2024-01-10', auto_adjust=True)
    
    print("원본 yfinance 데이터:")
    print(df_yf.head(3))
    print(f"컬럼 목록: {df_yf.columns.tolist()}")
    print("\n" + "="*50 + "\n")
    
    # yfinance도 동일한 구조로 변환
    df_yf_compatible = df_yf.copy()
    df_yf_compatible['Date_Index'] = df_yf_compatible.index.strftime('%Y-%m-%d')
    df_yf_compatible['Time_Index'] = df_yf_compatible.index.strftime('%H:%M:%S')
    
    print("yfinance 호환 구조로 변환 후:")
    print(df_yf_compatible.head(3))
    print(f"컬럼 목록: {df_yf_compatible.columns.tolist()}")
    
    return df_compatible, df_yf_compatible

def test_csv_save():
    """CSV 저장 테스트"""
    print("\n=== CSV 저장 테스트 ===")
    
    df_compatible, _ = test_compatible_structure()
    
    # CSV 저장 테스트
    csv_path = "test_compatible_structure.csv"
    df_compatible.to_csv(csv_path, encoding='utf-8-sig')
    
    print(f"CSV 저장 완료: {csv_path}")
    print("저장된 CSV 내용:")
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:10]):  # 처음 10줄만 출력
            print(f"{i+1:2d}: {line.rstrip()}")
    
    # 파일 삭제
    import os
    if os.path.exists(csv_path):
        os.remove(csv_path)
        print(f"\n테스트 파일 삭제: {csv_path}")

if __name__ == "__main__":
    test_compatible_structure()
    test_csv_save() 