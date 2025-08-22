#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_crossinfo_new_columns():
    """새로운 CrossInfo CSV 컬럼들 테스트"""
    try:
        from services.technical_indicators_service import technical_indicators_service
        from services.market.data_reading_service import DataReadingService
        
        # 테스트할 종목
        test_ticker = '000270.KS'  # 기아
        market_type = 'KOSPI'
        timeframe = 'd'
        
        print(f"=== {test_ticker} 새로운 CrossInfo 컬럼들 테스트 ===")
        
        # 1. 지표 데이터 로드
        print("1. 지표 데이터 로드 중...")
        
        # 디버깅: 실제 파일 경로 확인
        import glob
        csv_dir = os.path.join('static', 'data', 'KOSPI')
        pattern = os.path.join(csv_dir, f"{test_ticker}_indicators_{timeframe}_*.csv")
        print(f"검색 패턴: {pattern}")
        
        files = glob.glob(pattern)
        print(f"찾은 파일들: {files}")
        
        if files:
            latest_file = max(files, key=os.path.getctime)
            print(f"최신 파일: {latest_file}")
        
        indicators_df = technical_indicators_service.read_indicators_csv(test_ticker, market_type, timeframe)
        
        if indicators_df.empty:
            print("❌ 지표 데이터를 읽을 수 없습니다.")
            return
        
        print(f"✅ 지표 데이터 로드 완료: {len(indicators_df)}행")
        
        # 2. 새로운 크로스오버 감지 및 CrossInfo CSV 생성
        print("2. 크로스오버 감지 및 CrossInfo CSV 생성 중...")
        from services.analysis.crossover.simplified_detector import SimplifiedCrossoverDetector
        crossover_service = SimplifiedCrossoverDetector()
        
        # 신호 감지 및 저장
        signals_result = crossover_service.detect_and_save_signals(indicators_df, test_ticker, timeframe, market_type)
        
        if not signals_result.get('success'):
            print(f"❌ 크로스오버 감지 실패: {signals_result.get('error')}")
            return
        
        print(f"✅ CrossInfo CSV 생성 완료: {signals_result.get('signals_csv_path')}")
        
        # 3. 새로운 CrossInfo CSV 읽기
        print("3. 새로운 CrossInfo CSV 읽기 중...")
        data_reading_service = DataReadingService()
        crossinfo_df = data_reading_service.read_crossinfo_csv(test_ticker, market_type)
        
        if crossinfo_df.empty:
            print("❌ CrossInfo CSV를 읽을 수 없습니다.")
            return
        
        print(f"✅ CrossInfo 데이터 로드 완료: {len(crossinfo_df)}행")
        
        # 4. 새로운 컬럼들 확인
        print("4. 새로운 컬럼들 확인...")
        expected_columns = [
            'EMA_Array_Pattern',
            'EMA_Array_Order', 
            'Close_Gap_EMA20',
            'Close_Gap_EMA40'
        ]
        
        print("기존 컬럼들:")
        for col in crossinfo_df.columns:
            if col not in expected_columns:
                print(f"  - {col}")
        
        print("\n새로운 컬럼들:")
        for col in expected_columns:
            if col in crossinfo_df.columns:
                value = crossinfo_df[col].iloc[0] if not crossinfo_df.empty else "N/A"
                print(f"  ✅ {col}: {value}")
            else:
                print(f"  ❌ {col}: 누락됨")
        
        # 5. 데이터 검증
        print("\n5. 데이터 검증...")
        if not crossinfo_df.empty:
            latest_row = crossinfo_df.iloc[-1]
            
            # EMA 배열 패턴 검증
            ema_pattern = latest_row.get('EMA_Array_Pattern', 'N/A')
            print(f"  - EMA 배열 패턴: {ema_pattern}")
            
            # EMA 배열 순서 검증
            ema_order = latest_row.get('EMA_Array_Order', 'N/A')
            print(f"  - EMA 배열 순서: {ema_order}")
            
            # 종가-EMA 갭 검증
            gap_ema20 = latest_row.get('Close_Gap_EMA20', 0.0)
            gap_ema40 = latest_row.get('Close_Gap_EMA40', 0.0)
            print(f"  - 종가-EMA20 갭: {gap_ema20:.2f}%")
            print(f"  - 종가-EMA40 갭: {gap_ema40:.2f}%")
        
        print("\n=== 테스트 완료 ===")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_crossinfo_new_columns()
