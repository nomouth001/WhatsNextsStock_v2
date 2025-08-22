"""
데이터 읽기 서비스
저장된 CSV 파일에서 데이터를 읽어오는 기능을 담당
"""

import os
import logging
import pandas as pd
import glob
from typing import Dict, List, Optional
from .file_management_service import FileManagementService
from ..core.error_handler import log_error

class DataReadingService:
    """데이터 읽기 전담 서비스"""
    
    def __init__(self, cache_service=None):
        """데이터 읽기 서비스 초기화"""
        self.cache_service = cache_service
        self.file_manager = FileManagementService()
        self.logger = logging.getLogger(__name__)
    
    @log_error
    def read_ohlcv_csv(self, ticker: str, market: str, timeframe: str = 'd') -> pd.DataFrame:
        """
        OHLCV CSV 파일 읽기
        - 파일 기반 읽기 전용(다운로드/저장 수행하지 않음)
        - 최신 파일 탐색은 FileManagementService.get_latest_file 단일 진입점을 사용
        """
        try:
            latest_file = self.file_manager.get_latest_file(ticker, 'ohlcv', market, timeframe)
            logging.info(f"read_ohlcv_csv: latest_file={latest_file} (ticker={ticker}, market={market}, tf={timeframe})")
            if not latest_file:
                logging.info(f"[{ticker}] OHLCV 데이터 파일 없음 ({timeframe})")
                return pd.DataFrame()
            
            # 메타데이터 건너뛰기
            skiprows = 0
            with open(latest_file, 'r', encoding='utf-8-sig') as f:
                for i, line in enumerate(f):
                    if line.strip() == '# End Metadata':
                        skiprows = i + 1
                        break
            
            logging.info(f"read_ohlcv_csv: skiprows={skiprows}")
            df = pd.read_csv(latest_file, skiprows=skiprows, parse_dates=['Date'])
            df.set_index('Date', inplace=True)
            try:
                preview_cols = list(df.columns)[:12]
                logging.info(f"read_ohlcv_csv: cols_preview={preview_cols}, rows={len(df)}")
            except Exception:
                pass
            
            self.logger.info(f"[{ticker}] OHLCV 데이터 로드 완료: {latest_file} ({timeframe}, {len(df)}개 행)")
            return df
        except FileNotFoundError:
            self.logger.warning(f"[{ticker}] OHLCV 파일 없음: {latest_file}")
            return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"[{ticker}] OHLCV 파일 읽기 실패: {e}")
            return pd.DataFrame()

    @log_error
    def read_indicators_csv(self, ticker: str, market: str, timeframe: str = 'd') -> pd.DataFrame:
        """기술적 지표 CSV 파일 읽기"""
        try:
            latest_file = self.file_manager.get_latest_file(ticker, 'indicators', market, timeframe)
            logging.info(f"read_indicators_csv: latest_file={latest_file} (ticker={ticker}, market={market}, tf={timeframe})")
            if not latest_file:
                logging.info(f"[{ticker}] 기술적 지표 파일 없음 ({timeframe})")
                return pd.DataFrame()

            # 메타데이터/헤더 자동 감지: '# End Metadata' 우선, 없으면 'Date' 헤더 라인 탐지
            skiprows = 0
            header_found = False
            header_idx = 0
            after_meta = False
            with open(latest_file, 'r', encoding='utf-8-sig') as f:
                for i, line in enumerate(f):
                    stripped = line.strip()
                    if stripped == '# End Metadata':
                        # 메타데이터 끝을 만났으니 이후부터 헤더 라인을 찾는다
                        after_meta = True
                        continue
                    # 메타데이터 이후 첫 번째 'Date,...' 라인을 헤더로 사용
                    if after_meta and stripped and stripped.startswith('Date') and ',' in stripped:
                        header_idx = i
                        header_found = True
                        break
                    # 메타데이터가 없는 파일의 경우, 파일 어디서든 'Date,...'를 헤더로 인정
                    if not after_meta and stripped.startswith('Date') and ',' in stripped:
                        header_idx = i
                        header_found = True
                        break
            if not header_found:
                # 최악의 경우: 메타데이터가 없고 헤더도 감지 못함 → 파일 첫 줄을 헤더로 간주
                header_idx = 0
            
            logging.info(f"read_indicators_csv: header_idx={header_idx}")
            try:
                # 주의: header_idx는 원본 파일 기준 라인 인덱스이므로 skiprows로 건너뛰고 header=0으로 지정
                df = pd.read_csv(
                    latest_file,
                    skiprows=header_idx,
                    header=0,
                    sep=',',
                    engine='python',
                    on_bad_lines='skip'
                )
            except Exception as e:
                # 토크나이즈 오류 등 발생 시 문제있는 라인 스킵 시도
                logging.warning(f"read_indicators_csv: tokenizing 오류 발생, 폴백 적용: {e}")
                df = pd.read_csv(
                    latest_file,
                    skiprows=header_idx,
                    header=0,
                    sep=',',
                    engine='python',
                    on_bad_lines='skip'
                )

            # Date 컬럼 파싱 및 인덱스 설정
            if 'Date' not in df.columns and df.columns.size > 0:
                # 첫 컬럼이 날짜일 가능성 높음
                first_col = df.columns[0]
                try:
                    df['Date'] = pd.to_datetime(df[first_col], errors='coerce')
                except Exception:
                    df['Date'] = pd.NaT
            else:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df[df['Date'].notna()]
            df.set_index('Date', inplace=True)
            try:
                preview_cols = list(df.columns)[:12]
                logging.info(f"read_indicators_csv: cols_preview={preview_cols}, rows={len(df)}")
            except Exception:
                pass
            
            self.logger.info(f"[{ticker}] 기술적 지표 데이터 로드 완료: {latest_file} ({timeframe}, {len(df)}개 행)")
            return df
        except FileNotFoundError:
            self.logger.warning(f"[{ticker}] 기술적 지표 파일 없음: {latest_file}")
            return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"[{ticker}] 기술적 지표 파일 읽기 실패: {e}")
            return pd.DataFrame()

    @log_error
    def read_crossinfo_csv(self, ticker: str, market: str) -> pd.DataFrame:
        """CrossInfo CSV 파일 읽기 (일봉 기준)"""
        try:
            latest_file = self.file_manager.get_latest_file(ticker, 'crossinfo', market, 'd') # CrossInfo는 일봉 기준
            logging.info(f"read_crossinfo_csv: latest_file={latest_file} (ticker={ticker}, market={market})")
            if not latest_file:
                logging.info(f"[{ticker}] CrossInfo 데이터 파일 없음")
                return pd.DataFrame()

            # 메타데이터 건너뛰기
            skiprows = 0
            with open(latest_file, 'r', encoding='utf-8-sig') as f:
                for i, line in enumerate(f):
                    if line.strip() == '# End Metadata':
                        skiprows = i + 1
                        break
            
            logging.info(f"read_crossinfo_csv: skiprows={skiprows}")
            df = pd.read_csv(latest_file, skiprows=skiprows, parse_dates=['Date'])
            try:
                preview_cols = list(df.columns)[:12]
                logging.info(f"read_crossinfo_csv: cols_preview={preview_cols}, rows={len(df)}")
            except Exception:
                pass
            
            self.logger.info(f"[{ticker}] 일봉 CrossInfo 데이터 로드 완료: {latest_file} ({len(df)}개 행)")
            return df
        except FileNotFoundError:
            self.logger.warning(f"[{ticker}] CrossInfo 파일 없음: {latest_file}")
            return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"[{ticker}] CrossInfo 파일 읽기 실패: {e}")
            return pd.DataFrame()

    def get_latest_ohlcv_deprecated(self, tickers: list, market: str, caller: str = None) -> dict:
        """
        여러 티커에 대해 최신 OHLCV 데이터를 가져옵니다.
        (이 함수는 파일을 직접 읽는 것이 아니라, 다른 함수를 통해 데이터를 가져옵니다.)
        """
        # ... (이 함수는 직접 파일을 읽지 않으므로, 호출하는 다른 함수에서 caller를 전달해야 합니다.)
        # 이 예시에서는 직접적인 파일 읽기가 없으므로 로깅을 수정할 필요가 없습니다.
        # 만약 이 함수 내부에서 read_ohlcv_csv 등을 호출한다면, caller를 전달해야 합니다.
        results = {}
        for ticker in tickers:
            df = self.read_ohlcv_csv(ticker, market, 'd')
            if not df.empty:
                latest_data = df.iloc[-1]
                results[ticker] = {
                    'close': latest_data.get('Close'),
                    'latest_date': df.index[-1].strftime('%Y-%m-%d')
                }
        return results
    
    def read_data_from_csv(self, csv_path: str) -> Dict:
        """기존 CSV 파일에서 최신 종가/등락률 읽기"""
        try:
            # 메타데이터 건너뛰기
            skiprows = 0
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                for i, line in enumerate(f):
                    if line.strip() == '# End Metadata':
                        skiprows = i + 1
                        break
            
            df = pd.read_csv(csv_path, skiprows=skiprows, index_col=0, parse_dates=True)
            
            if not df.empty and len(df) >= 2:
                # 최신 2일 데이터
                latest = df.iloc[-1]
                previous = df.iloc[-2]
                close_price = latest.get('Close')

                # [메모] 2025-08-19: 등락률 계산 단일화
                # 기존 직접 계산 코드는 주석 보존합니다. (회귀 대비)
                # 기존 코드:
                # change_percent = ((close_price - previous['Close']) / previous['Close']) * 100
                # return {
                #     'close': close_price,
                #     'change_percent': round(change_percent, 2),
                #     'csv_path': csv_path,
                #     'data_rows': len(df),
                #     'from_existing': True
                # }

                # 새로운 표준 경로: TechnicalIndicatorsService.get_latest_change_percent 호출
                change_percent_value = None
                try:
                    from services.technical_indicators_service import TechnicalIndicatorsService
                    tis = TechnicalIndicatorsService()
                    # csv_path에서 market_type, ticker, timeframe 추출 시도
                    market_type = ''
                    ticker = ''
                    timeframe = 'd'
                    try:
                        import os
                        norm = os.path.normpath(csv_path)
                        parts = norm.split(os.sep)
                        # 예상 경로: .../static/data/<MARKET>/<FILENAME>
                        if len(parts) >= 2:
                            market_type = parts[-2].upper()
                        filename = os.path.basename(csv_path)
                        # 티커는 첫 '_' 이전까지
                        if '_' in filename:
                            ticker = filename.split('_', 1)[0]
                        # timeframe 패턴 파싱
                        import re
                        m = re.search(r"_ohlcv_([dwm])_", filename)
                        if m:
                            timeframe = m.group(1)
                    except Exception:
                        pass
                    # 표준 함수 호출 (실패 시 아래 폴백 사용)
                    if ticker and market_type:
                        change_percent_value = tis.get_latest_change_percent(ticker, timeframe=timeframe, market_type=market_type)
                except Exception:
                    change_percent_value = None

                # 폴백: 동일 파일 내 직접 계산 (주석 보존된 기존 로직과 동일 수식)
                if change_percent_value is None:
                    try:
                        prev_close = previous.get('Close')
                        if close_price is not None and prev_close not in (None, 0):
                            change_percent_value = ((close_price - prev_close) / prev_close) * 100
                            change_percent_value = round(change_percent_value, 2)
                        else:
                            change_percent_value = 0.0
                    except Exception:
                        change_percent_value = 0.0

                return {
                    'close': close_price,
                    'change_percent': change_percent_value,
                    'csv_path': csv_path,
                    'data_rows': len(df),
                    'from_existing': True
                }
        except Exception as e:
            self.logger.error(f"CSV 파일 읽기 오류 {csv_path}: {e}")
        
        return None
    
    def get_latest_ohlcv(self, tickers: List[str], market_type: str, **kwargs) -> Dict:
        """
        여러 종목의 최신 OHLCV 데이터 조회 (파일 읽기 전용)
        - 다운로드/저장 트리거 없이 로컬 최신 파일에서만 읽습니다.
        """
        results = {}
        
        for ticker in tickers:
            try:
                df = self.read_ohlcv_csv(ticker, market_type, 'd')
                if not df.empty:
                    latest_data = df.iloc[-1]
                    results[ticker] = {
                        'close': latest_data['Close'],
                        'volume': latest_data['Volume'],
                        'date': latest_data.name.strftime('%Y-%m-%d')
                    }
            except Exception as e:
                self.logger.error(f"[{ticker}] 최신 OHLCV 조회 실패: {e}")
        
        return results
    
    def find_latest_csv_file(self, ticker: str, market_type: str, data_type: str = 'ohlcv') -> str:
        """
        [Deprecated] 최신 CSV 파일 경로 찾기
        - 이 함수는 FileManagementService.get_latest_file로 위임됩니다.
        - 호출부는 get_latest_file 사용으로 교체하세요.
        """
        try:
            # 단일 진입점 위임
            return self.file_manager.get_latest_file(ticker, data_type, market_type, 'd')
        except Exception as e:
            self.logger.error(f"[{ticker}] 최신 CSV 파일 찾기 실패: {e}")
            return "" 
    
    def get_csv_metadata(self, csv_path: str) -> dict:
        """CSV 파일의 메타데이터 조회"""
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
            
            metadata = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('# End Metadata'):
                    break
                elif line.startswith('# ') and ':' in line:
                    key_value = line[2:].split(':', 1)
                    if len(key_value) == 2:
                        key = key_value[0].strip()
                        value = key_value[1].strip()
                        metadata[key] = value
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"메타데이터 조회 실패 {csv_path}: {e}")
            return {}
    
    def get_ohlcv_metadata(self, ticker: str, timeframe: str = 'd', market_type: str = 'KOSPI') -> dict:
        """OHLCV 파일의 메타데이터 조회"""
        try:
            # 시장 타입에 따른 디렉토리 결정
            if market_type.upper() in ['KOSPI', 'KOSDAQ']:
                actual_market_type = market_type.upper()
            else:
                actual_market_type = 'US'
            
            # CSV 파일 경로 패턴
            csv_dir = os.path.join('static/data', actual_market_type)
            pattern = os.path.join(csv_dir, f"{ticker}_ohlcv_{timeframe}_*.csv")
            
            # 파일 찾기
            files = glob.glob(pattern)
            
            if not files:
                return {}
            
            # 가장 최신 파일 선택
            latest_file = max(files, key=os.path.getctime)
            
            return self.get_csv_metadata(latest_file)
            
        except Exception as e:
            self.logger.error(f"[{ticker}] OHLCV 메타데이터 조회 실패: {e}")
            return {} 