"""
파일 관리 서비스
파일 관리 및 전략 결정 기능을 담당
"""

import os
import logging
import glob
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

class FileManagementService:
    """파일 관리 전담 서비스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def find_csv_files(self, ticker: str, market_type: str, data_type: str = 'ohlcv', timeframe: str = 'd') -> List[str]:
        """특정 조건에 맞는 CSV 파일들 찾기"""
        try:
            # 시장 타입에 따른 디렉토리 결정
            if market_type.upper() in ['KOSPI', 'KOSDAQ']:
                actual_market_type = market_type.upper()
            else:
                actual_market_type = 'US'
            
            # CSV 파일 경로 패턴 (새로운 형식 지원)
            csv_dir = os.path.join('static/data', actual_market_type)
            # 새로운 형식: {ticker}_{data_type}_{timeframe}_*.csv
            # KOSPI/KOSDAQ의 경우, 저장 시 접미사(.KS/.KQ) 유무가 혼재할 수 있으므로 후보 티커를 모두 시도
            def _ticker_candidates(t: str, m: str) -> List[str]:
                if m.upper() not in ['KOSPI', 'KOSDAQ']:
                    return [t]
                candidates: List[str] = [t]
                try:
                    # 6자리 숫자 코드 추출
                    m6 = re.search(r"(\d{6})", t)
                    if m6:
                        base = m6.group(1)
                        if base not in candidates:
                            candidates.append(base)
                        # 접미사 재부여 후보 (디스크 저장명이 접미사 포함일 수도 있음)
                        suffix = '.KS' if m.upper() == 'KOSPI' else '.KQ'
                        suffixed = f"{base}{suffix}"
                        if suffixed not in candidates:
                            candidates.append(suffixed)
                except Exception:
                    pass
                # 중복 제거 순서 유지
                return list(dict.fromkeys(candidates))

            candidates = _ticker_candidates(ticker, actual_market_type)

            # 파일 찾기 (후보별 글롭 후 합치기)
            files: List[str] = []
            for cand in candidates:
                # CrossInfo 파일명의 대소문자 혼재를 지원 (Ubuntu에서 대소문자 구분)
                if data_type.lower() == 'crossinfo':
                    patterns = [
                        os.path.join(csv_dir, f"{cand}_crossinfo_{timeframe}_*.csv"),
                        os.path.join(csv_dir, f"{cand}_CrossInfo_{timeframe}_*.csv"),
                        os.path.join(csv_dir, f"{cand}_CROSSINFO_{timeframe}_*.csv"),
                    ]
                    for pattern in patterns:
                        files.extend(glob.glob(pattern))
                    # 추가 폴백: 디렉토리 나열 후 소문자 비교로 수동 필터링
                    try:
                        for fname in os.listdir(csv_dir):
                            name_l = fname.lower()
                            # '{cand}_crossinfo_{timeframe}_' 접두 + 임의의 접미 + .csv
                            if name_l.startswith(f"{cand.lower()}_crossinfo_{timeframe}_") and name_l.endswith('.csv'):
                                files.append(os.path.join(csv_dir, fname))
                    except Exception:
                        pass
                else:
                    pattern = os.path.join(csv_dir, f"{cand}_{data_type}_{timeframe}_*.csv")
                    files.extend(glob.glob(pattern))
            
            if not files:
                self.logger.debug(f"[{ticker}] {data_type}_{timeframe} CSV 파일을 찾을 수 없음 (candidates={candidates})")
                return []
            
            # 파일들을 '파일명에 포함된 타임스탬프(epoch: float)' 기준으로 정렬 (실패 시 ctime 사용)
            def _sort_key(p):
                try:
                    info = self.parse_filename_time_info(os.path.basename(p), market_type)
                    if info and 'epoch' in info:
                        return info['epoch']  # float
                    return os.path.getctime(p)  # float
                except Exception:
                    return os.path.getctime(p)
            files.sort(key=_sort_key, reverse=True)
            
            self.logger.debug(f"[{ticker}] {data_type}_{timeframe} CSV 파일 {len(files)}개 발견")
            return files
            
        except Exception as e:
            self.logger.error(f"[{ticker}] CSV 파일 검색 실패: {e}")
            return []

    def get_latest_file(self, ticker: str, data_type: str, market_type: str, timeframe: str = 'd') -> str:
        """
        최신 CSV 파일 경로 반환
        - 최신 파일 탐색의 단일 진입점 (다른 서비스들은 이 메서드만 사용)
        - 기존 임시 구현(글롭/ctime)은 모두 이 메서드로 위임/대체
        """
        try:
            self.logger.info(f"get_latest_file: ticker={ticker}, data_type={data_type}, market={market_type}, tf={timeframe}")
            files = self.find_csv_files(ticker, market_type, data_type, timeframe)
            if files:
                latest_file = files[0]  # find_csv_files가 이미 시간순 정렬됨
                self.logger.info(f"[{ticker}] 최신 {data_type} 파일 선택: {latest_file}")
                return latest_file
            return ""
        except Exception as e:
            self.logger.error(f"[{ticker}] 최신 {data_type} 파일 찾기 실패: {e}")
            return ""
    
    def check_existing_csv_file(self, ticker: str, market_type: str) -> Tuple[str, bool]:
        """기존 CSV 파일 확인"""
        try:
            # 시장 타입에 따른 디렉토리 결정
            if market_type.upper() in ['KOSPI', 'KOSDAQ']:
                actual_market_type = market_type.upper()
            else:
                actual_market_type = 'US'
            
            # CSV 파일 경로 패턴 (새로운 형식 지원)
            csv_dir = os.path.join('static/data', actual_market_type)
            # 새로운 형식: {ticker}_ohlcv_* (tf 무관)
            # KOSPI/KOSDAQ의 티커 후보를 모두 시도
            def _ticker_candidates(t: str, m: str) -> List[str]:
                if m.upper() not in ['KOSPI', 'KOSDAQ']:
                    return [t]
                candidates: List[str] = [t]
                try:
                    m6 = re.search(r"(\d{6})", t)
                    if m6:
                        base = m6.group(1)
                        if base not in candidates:
                            candidates.append(base)
                        suffix = '.KS' if m.upper() == 'KOSPI' else '.KQ'
                        suffixed = f"{base}{suffix}"
                        if suffixed not in candidates:
                            candidates.append(suffixed)
                except Exception:
                    pass
                return list(dict.fromkeys(candidates))

            candidates = _ticker_candidates(ticker, actual_market_type)

            # 파일 찾기 (후보별 합치기)
            files: List[str] = []
            for cand in candidates:
                pattern = os.path.join(csv_dir, f"{cand}_ohlcv_*.csv")
                files.extend(glob.glob(pattern))
            
            if not files:
                return "", False
            
            # 가장 최신 파일 선택 (파일명 타임스탬프 우선, float으로 통일)
            def _sort_key(p):
                try:
                    info = self.parse_filename_time_info(os.path.basename(p), market_type)
                    if info and 'epoch' in info:
                        return info['epoch']
                    return os.path.getctime(p)
                except Exception:
                    return os.path.getctime(p)
            latest_file = max(files, key=_sort_key)
            
            return latest_file, True
            
        except Exception as e:
            self.logger.error(f"[{ticker}] 기존 CSV 파일 확인 실패: {e}")
            return "", False
    
    def determine_data_strategy(self, ticker: str, market_type: str = 'US') -> str:
        """데이터 전략 결정 (보수적 다운로드 방지)"""
        try:
            # 기존 파일 확인
            existing_file, exists = self.check_existing_csv_file(ticker, market_type)

            if not exists or not existing_file:
                return "download_fresh"

            # 파일 시간 파악: 파일명 파싱 우선, 실패 시 파일 mtime 사용
            file_info = self.parse_filename_time_info(os.path.basename(existing_file), market_type)
            if file_info and 'epoch' in file_info:
                file_ts = datetime.fromtimestamp(file_info['epoch'])
            else:
                try:
                    file_ts = datetime.fromtimestamp(os.path.getctime(existing_file))
                except Exception:
                    # 파일 시간 확인 실패 시, 불필요 다운로드 방지 위해 기존 사용
                    return "use_existing"

            # 시장 상태 확인
            from .market_status_service import MarketStatusService
            market_service = MarketStatusService()
            market_status = market_service.get_market_status_info_improved(market_type)

            file_age_hours = (datetime.now() - file_ts).total_seconds() / 3600

            # 정책: 장이 열려 있고, 파일이 충분히 오래됐을 때만 갱신
            if market_status.get('is_open', False):
                if file_age_hours > 1.0:
                    return "download_fresh"
                return "use_existing"

            # 장이 닫혀 있으면 기존 사용(야간 반복 다운로드 방지)
            return "use_existing"

        except Exception as e:
            self.logger.error(f"[{ticker}] 데이터 전략 결정 실패: {e}")
            # 실패 시에도 보수적으로 기존 사용
            return "use_existing"
    
    def should_download_fresh_data_improved(self, ticker: str, market_type: str = 'US') -> bool:
        """새 데이터 다운로드 필요 여부 (개선된 버전)"""
        strategy = self.determine_data_strategy(ticker, market_type)
        return strategy == "download_fresh"
    
    def should_download_fresh_data(self, ticker: str, market_type: str = 'US') -> bool:
        """새 데이터 다운로드 필요 여부 (기존 버전)"""
        return self.should_download_fresh_data_improved(ticker, market_type)
    
    def parse_filename_time_info(self, filename: str, market_type: str = 'KOSPI') -> Optional[Dict]:
        """파일명에서 시간 정보 파싱 (티커의 '.'/'-' 허용, d/w/m 지원)"""
        try:
            # 파일명 패턴: ticker_ohlcv_{tf}_{YYYYMMDD}_{HHMMSS}_{TZ}.csv
            # 예: 000250.KS_ohlcv_d_20250812_000000_KST.csv
            pattern = r"(.+?)_ohlcv_(d|w|m)_(\d{8})_(\d{6})_(KST|EST)\.csv"
            match = re.match(pattern, filename)

            if not match:
                return None

            ticker, tf, date_str, time_str, tz = match.groups()

            # 날짜와 시간 파싱
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            time_obj = datetime.strptime(time_str, '%H%M%S')

            # 전체 타임스탬프 생성
            timestamp = datetime.combine(date_obj.date(), time_obj.time())
            epoch = timestamp.timestamp()

            # 파일명에 포함된 시간대 사용
            timezone = tz if tz else ('KST' if market_type.upper() in ['KOSPI', 'KOSDAQ'] else 'EST')

            return {
                'ticker': ticker,
                'timeframe': tf,
                'timestamp': timestamp,  # backward compatibility
                'epoch': epoch,
                'date': date_str,
                'time': time_str,
                'timezone': timezone
            }

        except Exception as e:
            self.logger.error(f"파일명 시간 정보 파싱 실패: {e}")
            return None
    
    def is_file_created_after_market_close(self, filename: str, market_type: str) -> bool:
        """파일이 장마감 후 생성되었는지 확인"""
        try:
            file_info = self.parse_filename_time_info(filename, market_type)
            if not file_info:
                return False
            
            file_timestamp = file_info['timestamp']
            
            # 시장 상태 서비스 사용
            from .market_status_service import MarketStatusService
            market_service = MarketStatusService()
            
            # 파일 생성일의 시장 마감 시간 계산
            if market_type.upper() in ['KOSPI', 'KOSDAQ']:
                # 한국 시장: 15:30 마감
                market_close = file_timestamp.replace(hour=15, minute=30, second=0, microsecond=0)
            else:
                # 미국 시장: 16:00 마감
                market_close = file_timestamp.replace(hour=16, minute=0, second=0, microsecond=0)
            
            return file_timestamp > market_close
            
        except Exception as e:
            self.logger.error(f"파일 생성 시간 확인 실패: {e}")
            return False
    
    def cleanup_old_files(self, directory: str, days: int = 90) -> None:
        """오래된 파일 정리"""
        try:
            if not os.path.exists(directory):
                return
            
            cutoff_date = datetime.now() - timedelta(days=days)
            removed_count = 0
            
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                
                if os.path.isfile(file_path):
                    file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_modified < cutoff_date:
                        os.remove(file_path)
                        removed_count += 1
                        self.logger.info(f"오래된 파일 삭제: {file_path}")
            
            if removed_count > 0:
                self.logger.info(f"총 {removed_count}개 오래된 파일 삭제 완료")
                
        except Exception as e:
            self.logger.error(f"오래된 파일 정리 실패: {e}")
    
    def get_market_data_for_stocks(self, stocks: List, market_type: str, current_date: datetime) -> Dict:
        """주식 리스트의 시장 데이터 가져오기"""
        try:
            results = {}
            
            for stock in stocks:
                ticker = stock.ticker
                
                # 기존 파일 확인
                existing_file, exists = self.check_existing_csv_file(ticker, market_type)
                
                if exists:
                    # 기존 파일에서 데이터 읽기
                    from .data_reading_service import DataReadingService
                    reading_service = DataReadingService()
                    
                    csv_data = reading_service.read_data_from_csv(existing_file)
                    if csv_data:
                        results[ticker] = csv_data
                        continue
                
                # 기존 파일이 없거나 읽기 실패한 경우
                results[ticker] = {
                    'close': 0,
                    'change_percent': 0,
                    'csv_path': '',
                    'data_rows': 0,
                    'from_existing': False
                }
            
            return results
            
        except Exception as e:
            self.logger.error(f"주식 시장 데이터 가져오기 실패: {e}")
            return {} 