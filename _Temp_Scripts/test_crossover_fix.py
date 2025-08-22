#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_crossover_fix():
    """크로스오버 판정 수정 테스트"""
    try:
        from services.technical_indicators_service import technical_indicators_service
        
        # 267260.KS 데이터 읽기
        df = technical_indicators_service.read_indicators_csv('267260.KS', 'KR', 'd')
        if df.empty:
            print("데이터를 읽을 수 없습니다.")
            return
        
        print("=== 267260.KS 크로스오버 판정 테스트 ===")
        
        # 크로스오버 정보 가져오기
        # 새로운 통합 크로스오버 감지 시스템 사용
        from services.analysis.crossover.unified_detector import UnifiedCrossoverDetector
        crossover_service = UnifiedCrossoverDetector()
        all_signals = crossover_service.detect_all_signals(df)
        crossover_info = all_signals.get('crossover_info', {})
        proximity_info = all_signals.get('proximity_info', {})
        
        print(f"EMA Crossover: {crossover_info.get('ema_crossover')}")
        print(f"MACD Crossover: {crossover_info.get('macd_crossover')}")
        
        # 근접성 정보 확인
        if proximity_info:
            print("\n=== 근접성 정보 ===")
            
            # EMA 근접성
            ema_proximity = proximity_info.get('ema_proximity')
            if ema_proximity:
                print(f"EMA Proximity: {ema_proximity}")
            else:
                print("EMA 근접성: 없음")
            
            # MACD 근접성
            macd_proximity = proximity_info.get('macd_proximity')
            if macd_proximity:
                print(f"MACD Proximity: {macd_proximity}")
            else:
                print("MACD 근접성: 없음")
        
        # 수정된 판정 결과 - 새로운 시스템 사용
        print("\n=== 수정된 판정 결과 ===")
        
        final_status = crossover_service.get_final_status(crossover_info, proximity_info)
        ema_status = final_status.get('ema_status', {})
        macd_status = final_status.get('macd_status', {})
        
        print(f"EMA Status: {ema_status}")
        print(f"MACD Status: {macd_status}")
        
        # 전체 분석 데이터 테스트
        print("\n=== 전체 분석 데이터 ===")
        analysis_data = technical_indicators_service.get_stock_analysis_data('267260.KS', 'KR')
        if analysis_data:
            print(f"EMA Crossover Status: {analysis_data.get('ema_crossover_status')}")
            print(f"MACD Crossover Status: {analysis_data.get('macd_crossover_status')}")
        
    except Exception as e:
        print(f"테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_crossover_fix() 