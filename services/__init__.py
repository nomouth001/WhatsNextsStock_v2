# services 패키지 초기화
from .market.market_data_orchestrator import MarketDataOrchestrator
from .market.data_reading_service import DataReadingService
from .market.market_status_service import MarketStatusService
from .market.file_management_service import FileManagementService
from .technical_indicators_service import TechnicalIndicatorsService, technical_indicators_service

def orchestrate_and_get_latest_ohlcv(tickers, market_type, **kwargs):
    """
    오케스트레이터를 포함하여 최신 OHLCV 데이터를 확보하고 반환합니다.
    - 역할: 필요 시 다운로드·저장까지 수행한 뒤 최신 데이터를 읽어 반환
    - 내부 의존: MarketStatusService, FileManagementService, MarketDataOrchestrator,
      DataReadingService, TechnicalIndicatorsService
    - 주의: 파일 기반 읽기 전용이 아님(다운로드 트리거 가능)
    """
    # 1. 시장 상태 확인
    status_service = MarketStatusService()
    market_status = status_service.get_market_status_info_improved(market_type)

    # 2. 서비스 초기화
    file_service = FileManagementService()
    reading_service = DataReadingService()
    orchestrator = MarketDataOrchestrator()
    indicators_service = TechnicalIndicatorsService()

    results = {}

    for ticker in tickers:
        # 3. 데이터 전략 결정
        strategy = file_service.determine_data_strategy(ticker, market_type)

        if strategy == "download_fresh":
            # 4. 새 데이터 다운로드 및 저장
            result = orchestrator.process_stock_data_complete(ticker, market_type)
            if result.success:
                # 5. 등락률은 indicators CSV에서 읽기
                change_percent = indicators_service.get_latest_change_percent(ticker, 'd', market_type)
                latest_ohlcv = reading_service.read_ohlcv_csv(ticker, market_type, 'd').iloc[-1]

                results[ticker] = {
                    'close': latest_ohlcv['Close'],
                    'change_percent': change_percent,
                    'csv_path': result.daily_path,
                    'from_existing': False
                }
        else:
            # 6. 기존 파일 사용 (파일 관리 서비스의 단일화된 최신 파일 탐색 사용)
            ohlcv_df = reading_service.read_ohlcv_csv(ticker, market_type, 'd')

            if not ohlcv_df.empty:
                change_percent = indicators_service.get_latest_change_percent(ticker, 'd', market_type)
                latest_ohlcv = ohlcv_df.iloc[-1]

                # Deprecated: DataReadingService.find_latest_csv_file → FileManagementService.get_latest_file
                csv_path = file_service.get_latest_file(ticker, 'ohlcv', market_type, 'd')

                results[ticker] = {
                    'close': latest_ohlcv['Close'],
                    'change_percent': change_percent,
                    'csv_path': csv_path,
                    'from_existing': True
                }

    return results

# 하위 호환성을 위한 래퍼 함수
def get_latest_ohlcv(tickers, market_type, **kwargs):
    """
    하위 호환 래퍼: orchestrate_and_get_latest_ohlcv를 호출합니다.
    주의: 이 함수는 다운로드·저장을 포함할 수 있습니다(읽기 전용 아님).
    """
    try:
        import logging
        logging.getLogger(__name__).warning(
            "get_latest_ohlcv는 오케스트레이션을 포함합니다. 파일 읽기 전용은 DataReadingService.get_latest_ohlcv를 사용하세요.")
    except Exception:
        pass
    return orchestrate_and_get_latest_ohlcv(tickers, market_type)

def read_ohlcv_csv(ticker, market_type='US', timeframe='d'):
    """하위 호환성을 위한 래퍼 함수"""
    reader = DataReadingService()
    return reader.read_ohlcv_csv(ticker, market_type, timeframe)