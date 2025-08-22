"""
데이터 다운로드 서비스
다양한 소스에서 주식 데이터를 다운로드하는 기능을 담당
"""

import os
import logging
import json
import time
# import time  # 중복 import 제거
import requests
import pandas as pd
import yfinance as yf
import FinanceDataReader as fdr
from datetime import datetime, timedelta
import pytz
from typing import List, Optional

# 커스텀 예외 클래스
from .exceptions import RateLimitError, YahooFinanceError, DataDownloadError

class DataDownloadService:
    """데이터 다운로드 전담 서비스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 핸들러 중복 방지를 위한 propagate 제어는 전역 로깅 설정에서 수행

    def _log_json(self, payload: dict):
        try:
            self.logger.info(json.dumps(payload, ensure_ascii=False))
        except Exception:
            self.logger.info(str(payload))

    def _normalize_for_provider(self, ticker: str, market_type: str, provider: str) -> str:
        """공급자/시장별 티커 정규화 (현재는 로깅 목적, 동작 변경 없음)"""
        normalized = ticker
        if provider.lower() == 'fdr' and market_type in ('KOSPI', 'KOSDAQ'):
            # 6자리 숫자코드만 추출 (예: 005930.KS -> 005930)
            import re
            m = re.search(r'(\d{6})', ticker)
            if m:
                normalized = m.group(1)
        return normalized
    
    def is_korean_stock(self, ticker: str) -> bool:
        """한국 주식 여부 확인"""
        return ticker.endswith('.KS') or ticker.endswith('.KQ')
    
    def get_ticker_suffix(self, ticker: str, market_type: str) -> List[str]:
        """시장 타입에 맞는 티커 접미사 반환 (야후 파이낸스 형식 기준)
        - MEMO(2025-08-20): KOSDAQ은 .KQ 우선, KOSPI는 .KS 우선으로 변경
        """
        if market_type.upper() in ['KOSPI', 'KOSDAQ']:
            # 이미 접미사가 붙어 있으면 그대로 사용
            if ticker.endswith(('.KS', '.KQ')):
                return [ticker]
            # 6자리 숫자 코드인 경우 시장 컨텍스트 기반으로 우선순위 결정
            if len(ticker) == 6 and ticker.isdigit():
                if market_type.upper() == 'KOSDAQ':
                    return [f"{ticker}.KQ", f"{ticker}.KS"]
                # KOSPI 기본
                return [f"{ticker}.KS", f"{ticker}.KQ"]
            # 기타 형식은 원형 유지
            return [ticker]
        else:  # US 등
            return [ticker]
    
    def download_from_yahoo_finance(self, ticker: str, start_date: datetime, 
                                   end_date: datetime, max_retries: int = 3, delay: int = 5) -> pd.DataFrame:
        """Yahoo Finance에서 데이터 다운로드"""
        self._log_json({"event":"download.call","provider":"yfinance","ticker":ticker,"start":str(start_date),"end":str(end_date)})
        
        for attempt in range(max_retries):
            try:
                # yfinance로 데이터 다운로드
                stock = yf.Ticker(ticker)
                df = stock.history(start=start_date, end=end_date, auto_adjust=True)
                
                if not df.empty:
                    # 시간대 정보 정규화 (tz-naive로 변환)
                    if df.index.tz is not None:
                        df.index = df.index.tz_localize(None)
                    
                    # 컬럼명 정규화
                    if 'Adj Close' not in df.columns and 'Close' in df.columns:
                        df['Adj Close'] = df['Close']
                    
                    self._log_json({"event":"download.result","provider":"yfinance","ticker":ticker,"rows":len(df),"status":"success"})
                    return df
                else:
                    self._log_json({"event":"download.result","provider":"yfinance","ticker":ticker,"rows":0,"status":"empty"})
                    
            except Exception as e:
                self._log_json({"event":"download.retry","provider":"yfinance","ticker":ticker,"attempt":attempt+1,"error":str(e)})
                if attempt < max_retries - 1:
                    time.sleep(delay)
        
        raise YahooFinanceError(f"[{ticker}] Yahoo Finance에서 데이터 다운로드 실패")
    
    def download_from_finance_data_reader(self, ticker: str, start_date: datetime, 
                                         end_date: datetime, max_retries: int = 3) -> pd.DataFrame:
        """FinanceDataReader에서 데이터 다운로드"""
        self._log_json({"event":"download.call","provider":"fdr","ticker":ticker,"start":str(start_date),"end":str(end_date)})
        
        for attempt in range(max_retries):
            try:
                # FinanceDataReader로 데이터 다운로드
                df = fdr.DataReader(ticker, start_date, end_date)
                
                if not df.empty:
                    # 컬럼명 정규화
                    if 'Adj Close' not in df.columns and 'Close' in df.columns:
                        df['Adj Close'] = df['Close']
                    
                    self._log_json({"event":"download.result","provider":"fdr","ticker":ticker,"rows":len(df),"status":"success"})
                    return df
                else:
                    self._log_json({"event":"download.result","provider":"fdr","ticker":ticker,"rows":0,"status":"empty"})
                    
            except Exception as e:
                self._log_json({"event":"download.retry","provider":"fdr","ticker":ticker,"attempt":attempt+1,"error":str(e)})
                if attempt < max_retries - 1:
                    time.sleep(2)
        
        raise DataDownloadError(f"[{ticker}] FinanceDataReader에서 데이터 다운로드 실패")
    
    def download_stock_data_korean_fallback(self, ticker: str, start_date: datetime,
                                           end_date: datetime, market_type: Optional[str] = None) -> pd.DataFrame:
        """한국 주식 폴백 다운로드
        - MEMO(2025-08-20): 시장 컨텍스트 기반 접미사 우선순위 적용(KOSDAQ→.KQ 우선)
        - FDR 호출은 6자리 코드만 사용
        """
        self._log_json({"event": "korean.fallback.begin", "ticker": ticker})

        # 시장 컨텍스트 결정: 인자 우선, 없으면 티커 접미사로 추정
        market_context = (market_type.upper() if isinstance(market_type, str) and market_type
                          else ('KOSDAQ' if ticker.endswith('.KQ') else 'KOSPI'))

        # 1. FinanceDataReader 시도 (정규화된 6자리 코드 사용)
        try:
            norm = self._normalize_for_provider(ticker, market_context, 'fdr')
            self._log_json({
                "event": "korean.fallback.fdr_call",
                "input": ticker,
                "normalized": norm,
                "market_context": market_context
            })
            df = self.download_from_finance_data_reader(norm, start_date, end_date)
            if not df.empty:
                return df
        except Exception as e:
            self._log_json({"event": "korean.fallback.fdr_fail", "ticker": ticker, "error": str(e)})

        # 2. Yahoo Finance 시도 (여러 접미사)
        # MEMO(2025-08-20): 기존 하드코딩 'KOSPI' → market_context 사용으로 변경
        ticker_suffixes = self.get_ticker_suffix(ticker, market_context)

        for suffix in ticker_suffixes:
            try:
                df = self.download_from_yahoo_finance(suffix, start_date, end_date)
                if not df.empty:
                    return df
            except Exception as e:
                self._log_json({
                    "event": "korean.fallback.yf_fail",
                    "ticker": ticker,
                    "suffix": suffix,
                    "market_context": market_context,
                    "error": str(e)
                })

        raise DataDownloadError(f"[{ticker}] 한국 주식 데이터 다운로드 실패")
    
    def download_stock_data_us_fallback(self, ticker: str, start_date: datetime, 
                                       end_date: datetime) -> pd.DataFrame:
        """미국 주식 폴백 다운로드"""
        self._log_json({"event":"us.fallback.begin","ticker":ticker})
        
        # 1. Yahoo Finance 시도
        try:
            df = self.download_from_yahoo_finance(ticker, start_date, end_date)
            if not df.empty:
                return df
        except Exception as e:
            self._log_json({"event":"us.fallback.yf_fail","ticker":ticker,"error":str(e)})
        
        # 2. FinanceDataReader 시도
        try:
            df = self.download_from_finance_data_reader(ticker, start_date, end_date)
            if not df.empty:
                return df
        except Exception as e:
            self._log_json({"event":"us.fallback.fdr_fail","ticker":ticker,"error":str(e)})
        
        raise DataDownloadError(f"[{ticker}] 미국 주식 데이터 다운로드 실패")
    
    def download_stock_data_with_fallback(self, ticker: str, start_date: datetime,
                                         end_date: datetime, market_type: Optional[str] = None) -> pd.DataFrame:
        """폴백 방식으로 데이터 다운로드
        - MEMO(2025-08-20): 시장 컨텍스트 인자를 받아 한국 주식 접미사 우선순위 및 FDR 정규화에 반영
        """
        self._log_json({"event": "download.fallback.begin", "ticker": ticker, "market_type": market_type})

        # 시장 타입 판별
        if (self.is_korean_stock(ticker) or ticker.isdigit() or (market_type and market_type.upper() in ['KOSPI', 'KOSDAQ'])):
            # FDR용 정규화 형태와 yfinance용 형태를 함께 로깅 (컨텍스트 반영)
            ctx = (market_type.upper() if market_type else ('KOSDAQ' if ticker.endswith('.KQ') else 'KOSPI'))
            norm_fdr = self._normalize_for_provider(ticker, ctx, 'fdr')
            self._log_json({
                "event": "download.fallback.route",
                "market": "KR",
                "input": ticker,
                "market_context": ctx,
                "fdr_norm": norm_fdr
            })
            return self.download_stock_data_korean_fallback(ticker, start_date, end_date, market_type=ctx)
        else:
            return self.download_stock_data_us_fallback(ticker, start_date, end_date)