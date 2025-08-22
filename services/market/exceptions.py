"""
커스텀 예외 클래스들
시장 데이터 서비스에서 사용하는 예외 클래스들
"""

class RateLimitError(Exception):
    """Rate limit 오류를 위한 커스텀 예외"""
    pass

class YahooFinanceError(Exception):
    """Yahoo Finance 특정 오류를 위한 커스텀 예외"""
    pass

class DataDownloadError(Exception):
    """데이터 다운로드 오류"""
    pass

class DataValidationError(Exception):
    """데이터 검증 오류"""
    pass

class FileNotFoundError(Exception):
    """파일을 찾을 수 없음"""
    pass

class MarketDataError(Exception):
    """시장 데이터 관련 오류"""
    pass

class DataConversionError(Exception):
    """데이터 변환 오류"""
    pass

class MarketStatusError(Exception):
    """시장 상태 관련 오류"""
    pass 