#!/usr/bin/env python3
"""
최종 구현 테스트 스크립트
Date_Index와 Time_Index 컬럼이 추가된 OHLCV 저장 기능 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import FinanceDataReader as fdr
from services.market.data_storage_service import DataStorageService

def test_final_implementation():
    """최종 구현 테스트"""
    print("=== 최종 구현 테스트 ===")
    
    try:
        # 테스트 데이터 다운로드
        df = fdr.DataReader('005930', '2024-01-01', '2024-01-10')
        print(f"원본 데이터 Shape: {df.shape}")
        print(f"원본 컬럼: {df.columns.tolist()}")
        print("원본 데이터 샘플:")
        print(df.head(3))
        print("\n" + "="*50 + "\n")
        
        # DataStorageService 인스턴스 생성
        storage_service = DataStorageService()
        
        # Date_Index와 Time_Index 컬럼 추가 테스트
        df_with_datetime = storage_service._add_date_time_columns(df)
        print(f"Date_Index, Time_Index 추가 후 Shape: {df_with_datetime.shape}")
        print(f"Date_Index, Time_Index 추가 후 컬럼: {df_with_datetime.columns.tolist()}")
        print("Date_Index, Time_Index 추가 후 데이터 샘플:")
        print(df_with_datetime.head(3))
        print("\n" + "="*50 + "\n")
        
        # CSV 저장 테스트
        csv_path = storage_service.save_ohlcv_to_csv('005930', df, 'KOSPI')
        print(f"CSV 저장 완료: {csv_path}")
        
        # 저장된 CSV 파일 확인
        if csv_path and os.path.exists(csv_path):
            print("\n저장된 CSV 파일 내용:")
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
                for i, line in enumerate(lines[:15]):  # 처음 15줄만 출력
                    print(f"{i+1:2d}: {line.rstrip()}")
        
    except Exception as e:
        print(f"테스트 오류: {e}")

def test_metadata_reading():
    """메타데이터 읽기 테스트"""
    print("\n=== 메타데이터 읽기 테스트 ===")
    
    try:
        from services.market.data_reading_service import DataReadingService
        
        reader = DataReadingService()
        
        # 메타데이터 조회
        metadata = reader.get_ohlcv_metadata('005930', 'd', 'KOSPI')
        print("메타데이터:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
        
        # DataFrame 읽기
        df = reader.read_ohlcv_csv('005930', 'd', 'KOSPI')
        if not df.empty:
            print(f"\nDataFrame Shape: {df.shape}")
            print(f"DataFrame 컬럼: {df.columns.tolist()}")
            print("DataFrame 샘플:")
            print(df.head(3))
            
            # Date_Index, Time_Index 컬럼 확인
            if 'Date_Index' in df.columns and 'Time_Index' in df.columns:
                print("\n✅ Date_Index, Time_Index 컬럼이 성공적으로 추가되었습니다!")
                print(f"Date_Index 샘플: {df['Date_Index'].head(3).tolist()}")
                print(f"Time_Index 샘플: {df['Time_Index'].head(3).tolist()}")
            else:
                print("\n❌ Date_Index, Time_Index 컬럼이 없습니다.")
        
    except Exception as e:
        print(f"메타데이터 읽기 테스트 오류: {e}")

if __name__ == "__main__":
    test_final_implementation()
    test_metadata_reading() 