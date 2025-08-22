#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import pandas as pd
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.market.data_storage_service import DataStorageService
from services.market_data_service import get_current_time_info

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_save_ohlcv():
    """DataStorageService의 save_ohlcv_to_csv 함수를 테스트합니다."""
    
    # 테스트용 데이터 생성
    dates = pd.date_range('2025-01-01', periods=10, freq='D')
    test_data = pd.DataFrame({
        'Open': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
        'High': [102, 103, 104, 105, 106, 107, 108, 109, 110, 111],
        'Low': [99, 100, 101, 102, 103, 104, 105, 106, 107, 108],
        'Close': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
        'Volume': [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900]
    }, index=dates)
    
    print("=== 테스트 데이터 ===")
    print(test_data.head())
    print(f"데이터 타입: {type(test_data)}")
    print(f"인덱스 타입: {type(test_data.index)}")
    
    # 시간 정보 테스트
    print("\n=== 시간 정보 테스트 ===")
    time_info = get_current_time_info()
    print(f"Time info keys: {list(time_info.keys())}")
    print(f"est_time: {time_info['est_time']}")
    print(f"est_time type: {type(time_info['est_time'])}")
    
    # 미국 주식 시장 타입으로 테스트
    print("\n=== 미국 주식 저장 테스트 ===")
    try:
        storage_service = DataStorageService()
        storage_service.save_ohlcv_to_csv('TEST', test_data, market_type='US')
        print("✅ 미국 주식 저장 성공")
    except Exception as e:
        print(f"❌ 미국 주식 저장 실패: {e}")
        import traceback
        traceback.print_exc()
    
    # 한국 주식 시장 타입으로 테스트
    print("\n=== 한국 주식 저장 테스트 ===")
    try:
        storage_service = DataStorageService()
        storage_service.save_ohlcv_to_csv('005930', test_data, market_type='KR')
        print("✅ 한국 주식 저장 성공")
    except Exception as e:
        print(f"❌ 한국 주식 저장 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_save_ohlcv() 