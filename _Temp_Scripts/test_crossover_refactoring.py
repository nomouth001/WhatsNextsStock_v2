#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
크로스오버 판정로직 리팩토링 테스트
새로운 UnifiedCrossoverDetector를 테스트하는 스크립트
"""

import sys
import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.analysis.crossover.unified_detector import UnifiedCrossoverDetector
from services.technical_indicators_service import TechnicalIndicatorsService

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_test_data():
    """
    테스트용 지표 데이터 생성
    """
    # 날짜 범위 생성 (최근 100일)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=100)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # 기본 가격 데이터 생성
    np.random.seed(42)  # 재현 가능한 결과를 위해
    base_price = 10000
    price_changes = np.random.normal(0, 0.02, len(dates))  # 2% 표준편차
    prices = [base_price]
    
    for change in price_changes[1:]:
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    
    # OHLCV 데이터 생성
    df = pd.DataFrame({
        'Open': prices,
        'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'Close': prices,
        'Volume': np.random.randint(1000000, 5000000, len(dates))
    }, index=dates)
    
    # 기술적 지표 계산
    indicators_service = TechnicalIndicatorsService()
    indicators_df = indicators_service._calculate_indicators(df)
    
    return indicators_df

def test_crossover_detection():
    """
    크로스오버 감지 시스템 테스트
    """
    print("=== 크로스오버 감지 시스템 테스트 시작 ===")
    
    # 테스트 데이터 생성
    print("1. 테스트 데이터 생성 중...")
    indicators_df = create_test_data()
    print(f"   생성된 데이터: {len(indicators_df)} 행")
    print(f"   데이터 범위: {indicators_df.index[0]} ~ {indicators_df.index[-1]}")
    
    # 새로운 크로스오버 감지 서비스 초기화
    print("\n2. 새로운 크로스오버 감지 서비스 초기화...")
    crossover_service = UnifiedCrossoverDetector()
    
    # 통합 분석 실행
    print("\n3. 통합 크로스오버 분석 실행...")
    analysis_result = crossover_service.detect_all_signals(indicators_df)
    
    if analysis_result is None:
        print("   ❌ 분석 결과가 None입니다.")
        return
    
    print("   ✅ 분석 완료")
    
    # 결과 출력
    print("\n4. 분석 결과:")
    print("   --- 크로스오버 정보 ---")
    crossover_info = analysis_result.get('crossover_info', {})
    
    if crossover_info.get('ema_crossover'):
        ema_cross = crossover_info['ema_crossover']
        print(f"   EMA 크로스오버: {ema_cross['type']} (날짜: {ema_cross['date']})")
    else:
        print("   EMA 크로스오버: 없음")
    
    if crossover_info.get('macd_crossover'):
        macd_cross = crossover_info['macd_crossover']
        print(f"   MACD 크로스오버: {macd_cross['type']} (날짜: {macd_cross['date']})")
    else:
        print("   MACD 크로스오버: 없음")
    
    # 근접성 정보 출력
    print("\n   --- 근접성 정보 ---")
    proximity_info = analysis_result.get('proximity_info', {})
    
    if proximity_info.get('ema_proximity'):
        ema_prox = proximity_info['ema_proximity']
        print(f"   EMA 근접성: {ema_prox['type']} (강도: {ema_prox['strength']})")
    else:
        print("   EMA 근접성: 없음")
    
    if proximity_info.get('macd_proximity'):
        macd_prox = proximity_info['macd_proximity']
        print(f"   MACD 근접성: {macd_prox['type']} (강도: {macd_prox['strength']})")
    else:
        print("   MACD 근접성: 없음")
    
    # 전체 상태 정보 출력
    print("\n   --- 전체 상태 정보 ---")
    overall_status = analysis_result.get('overall_status', '정상')
    print(f"   전체 상태: {overall_status}")
    
    return analysis_result

def test_individual_functions():
    """
    개별 함수 테스트
    """
    print("=== 개별 함수 테스트 ===")
    
    # 테스트 데이터 생성
    indicators_df = create_test_data()
    crossover_service = UnifiedCrossoverDetector()
    
    # 1. EMA 크로스오버 감지 테스트
    print("1. EMA 크로스오버 감지 테스트...")
    ema_signals = crossover_service.detect_crossovers_only(indicators_df)
    if ema_signals.get('ema_crossover'):
        print(f"   ✅ EMA 크로스오버 감지: {ema_signals['ema_crossover']['type']}")
    else:
        print("   ⚠️ EMA 크로스오버 없음")
    
    # 2. MACD 크로스오버 감지 테스트
    print("2. MACD 크로스오버 감지 테스트...")
    macd_signals = crossover_service.detect_crossovers_only(indicators_df)
    if macd_signals.get('macd_crossover'):
        print(f"   ✅ MACD 크로스오버 감지: {macd_signals['macd_crossover']['type']}")
    else:
        print("   ⚠️ MACD 크로스오버 없음")
    
    # 3. 근접성 감지 테스트
    print("3. 근접성 감지 테스트...")
    proximity_signals = crossover_service.detect_proximity_only(indicators_df)
    if proximity_signals.get('ema_proximity'):
        print(f"   ✅ EMA 근접성 감지: {proximity_signals['ema_proximity']['type']}")
    else:
        print("   ⚠️ EMA 근접성 없음")
    
    if proximity_signals.get('macd_proximity'):
        print(f"   ✅ MACD 근접성 감지: {proximity_signals['macd_proximity']['type']}")
    else:
        print("   ⚠️ MACD 근접성 없음")
    
    print("✅ 개별 함수 테스트 완료")

def test_with_real_data():
    """
    실제 데이터로 테스트
    """
    print("\n=== 실제 데이터 테스트 ===")
    
    try:
        # 실제 데이터 로드
        from services.technical_indicators_service import technical_indicators_service
        
        # KOSPI 종목 중 하나 선택
        ticker = '005930.KS'  # 삼성전자
        df = technical_indicators_service.read_indicators_csv(ticker, 'KOSPI', 'd')
        
        if df.empty:
            print(f"   ❌ {ticker} 데이터를 읽을 수 없습니다.")
            return
        
        print(f"   ✅ {ticker} 데이터 로드 완료: {len(df)} 행")
        
        # 크로스오버 분석
        crossover_service = UnifiedCrossoverDetector()
        analysis_result = crossover_service.detect_all_signals(df)
        
        print(f"   분석 결과: {analysis_result}")
        
    except Exception as e:
        print(f"   ❌ 실제 데이터 테스트 중 오류: {e}")

def main():
    """
    메인 테스트 함수
    """
    print("🚀 크로스오버 리팩토링 테스트 시작")
    print("=" * 50)
    
    # 1. 기본 크로스오버 감지 테스트
    test_crossover_detection()
    
    # 2. 개별 함수 테스트
    test_individual_functions()
    
    # 3. 실제 데이터 테스트
    test_with_real_data()
    
    print("\n" + "=" * 50)
    print("✅ 크로스오버 리팩토링 테스트 완료")

if __name__ == "__main__":
    main() 