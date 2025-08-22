"""
새로운 SimplifiedCrossoverDetector 테스트 스크립트
"""

import sys
import os
import pandas as pd
import logging
from datetime import datetime
import glob

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.analysis.crossover.simplified_detector import SimplifiedCrossoverDetector
from services.technical_indicators_service import TechnicalIndicatorsService
from services.market.data_reading_service import DataReadingService

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_simplified_crossover_detector():
    """SimplifiedCrossoverDetector 테스트"""
    
    # 테스트할 종목들 (기존 데이터가 있는 종목들)
    test_tickers = ['000270.KS', '000660.KS']  # 기아, SK하이닉스
    market_type = 'KOSPI'
    timeframe = 'd'
    
    # 서비스 초기화
    detector = SimplifiedCrossoverDetector()
    indicators_service = TechnicalIndicatorsService()
    data_reading_service = DataReadingService()
    
    print("=== SimplifiedCrossoverDetector 테스트 시작 ===")
    
    for ticker in test_tickers:
        print(f"\n--- {ticker} 테스트 ---")
        
        try:
            # 1. 지표 데이터 읽기 또는 생성
            print(f"1. {ticker} 지표 데이터 읽기/생성 중...")
            
            # 직접 파일 찾기 (정확한 패턴으로)
            pattern = f"static/data/{market_type.upper()}/{ticker}_indicators_{timeframe}_*.csv"
            files = glob.glob(pattern)
            
            if files:
                # 가장 최신 파일 선택 (로그 용도로만 경로 출력)
                latest_file = max(files, key=os.path.getctime)
                print(f"   📁 파일 발견: {latest_file}")
                # 메타데이터/헤더 구조를 고려하여 서비스 경유로 읽기
                indicators_df = data_reading_service.read_indicators_csv(ticker, market_type, timeframe)
            else:
                print(f"   ⚠️ {ticker} 지표 데이터가 없습니다. 지표 계산을 시도합니다...")
                
                # 지표 계산 시도
                try:
                    results = indicators_service.calculate_all_indicators(ticker, market_type, [timeframe])
                    if results.get(timeframe, {}).get('success'):
                        indicators_df = data_reading_service.read_indicators_csv(ticker, market_type, timeframe)
                        print(f"   ✅ {ticker} 지표 계산 완료")
                    else:
                        print(f"   ❌ {ticker} 지표 계산 실패")
                        continue
                except Exception as e:
                    print(f"   ❌ {ticker} 지표 계산 중 오류: {e}")
                    continue
            
            if indicators_df.empty:
                print(f"   ❌ {ticker} 지표 데이터가 비어있습니다.")
                continue
            
            print(f"   ✅ {ticker} 지표 데이터 로드 완료: {len(indicators_df)}행")
            
            # 2. 신호 감지
            print(f"2. {ticker} 신호 감지 중...")
            signals = detector.detect_all_signals(indicators_df)
            
            if not signals:
                print(f"   ❌ {ticker} 신호 감지 실패")
                continue
            
            print(f"   ✅ {ticker} 신호 감지 완료")
            
            # 3. 결과 출력
            print(f"3. {ticker} 결과:")
            
            # EMA 분석 결과
            ema_analysis = signals.get('ema_analysis', {})
            print(f"   EMA 분석:")
            print(f"     - 최근 크로스오버: {ema_analysis.get('latest_crossover_type', 'None')}")
            print(f"     - 크로스오버 날짜: {ema_analysis.get('latest_crossover_date', 'None')}")
            print(f"     - 경과일수: {ema_analysis.get('days_since_crossover', 'None')}")
            print(f"     - EMA 쌍: {ema_analysis.get('ema_pair', 'None')}")
            print(f"     - 현재 근접성: {ema_analysis.get('current_proximity', 'None')}")
            print(f"     - 근접성 쌍: {ema_analysis.get('proximity_pair', 'None')}")
            print(f"     - 근접성 비율: {ema_analysis.get('proximity_ratio', 'None')}")
            print(f"     - 근접성 방향: {ema_analysis.get('proximity_direction', 'None')}")
            
            # MACD 분석 결과
            macd_analysis = signals.get('macd_analysis', {})
            print(f"   MACD 분석:")
            print(f"     - 최근 크로스오버: {macd_analysis.get('latest_crossover_type', 'None')}")
            print(f"     - 크로스오버 날짜: {macd_analysis.get('latest_crossover_date', 'None')}")
            print(f"     - 경과일수: {macd_analysis.get('days_since_crossover', 'None')}")
            print(f"     - 현재 근접성: {macd_analysis.get('current_proximity', 'None')}")
            
            # 4. CSV 저장 테스트
            print(f"4. {ticker} CSV 저장 테스트...")
            save_result = detector.detect_and_save_signals(indicators_df, ticker, timeframe, market_type)
            
            if save_result.get('success'):
                print(f"   ✅ {ticker} CSV 저장 완료: {save_result.get('signals_csv_path', 'None')}")
            else:
                print(f"   ❌ {ticker} CSV 저장 실패: {save_result.get('error', 'Unknown error')}")
            
        except Exception as e:
            print(f"   ❌ {ticker} 테스트 중 오류 발생: {e}")
            continue
    
    print("\n=== 테스트 완료 ===")

if __name__ == "__main__":
    test_simplified_crossover_detector() 