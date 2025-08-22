#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.market.data_storage_service import DataStorageService
from services.market_data_service import get_current_time_info
import pandas as pd
import datetime as dt

def test_save_function():
    print("=== 파일 저장 기능 테스트 ===")
    
    # 현재 시간 정보 확인
    time_info = get_current_time_info()
    print(f"현재 KST: {time_info['kst_str']}")
    print(f"현재 EST: {time_info['est_str']}")
    
    # 테스트 데이터 생성
    test_data = pd.DataFrame({
        'Open': [100, 101, 102],
        'High': [110, 111, 112],
        'Low': [90, 91, 92],
        'Close': [105, 106, 107],
        'Volume': [1000, 1100, 1200]
    }, index=[
        dt.datetime.now() - dt.timedelta(days=2),
        dt.datetime.now() - dt.timedelta(days=1),
        dt.datetime.now()
    ])
    
    print(f"테스트 데이터:\n{test_data}")
    
    # 미국 주식 테스트
    print("\n=== 미국 주식 저장 테스트 ===")
    try:
        storage_service = DataStorageService()
        result_us = storage_service.save_ohlcv_to_csv('TEST_US', test_data, 'US')
        print(f"미국 주식 저장 결과: {result_us}")
    except Exception as e:
        print(f"미국 주식 저장 오류: {e}")
    
    # 한국 주식 테스트
    print("\n=== 한국 주식 저장 테스트 ===")
    try:
        storage_service = DataStorageService()
        result_kr = storage_service.save_ohlcv_to_csv('TEST_KR', test_data, 'KR')
        print(f"한국 주식 저장 결과: {result_kr}")
    except Exception as e:
        print(f"한국 주식 저장 오류: {e}")

if __name__ == "__main__":
    test_save_function() 