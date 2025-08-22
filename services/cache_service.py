"""
[Deprecated] 캐시 서비스 - 메모리 기반 데이터 캐싱

주의:
- 전역 캐시는 `services.core.cache_service.CacheService`/`FileBasedCacheService`를 사용하세요.
- 이 모듈의 함수들은 향후 제거될 예정이며, 남겨두는 목적은 호환 경고 제공입니다.
"""

import json
import logging
import time
from typing import Any, Optional, Dict
from threading import Lock

# 메모리 캐시 저장소
_cache_store: Dict[str, Dict] = {}
_cache_lock = Lock()

def set_cache(key: str, value: Any, expire: int = 3600) -> bool:
    """
    [Deprecated] 캐시에 데이터 저장 (메모리)
    - 사용 금지: `services.core.cache_service.CacheService().set(...)` 사용
    Args:
        key: 캐시 키
        value: 저장할 데이터
        expire: 만료 시간 (초)
    Returns:
        성공 여부
    """
    try:
        with _cache_lock:
            # 만료 시간 계산
            expire_time = time.time() + expire
            
            # JSON으로 직렬화
            serialized_value = json.dumps(value, ensure_ascii=False, default=str)
            
            _cache_store[key] = {
                'value': serialized_value,
                'expire_time': expire_time
            }
            
            logging.info(f"캐시 저장 완료: {key} (만료: {expire}초)")
            return True
    except Exception as e:
        logging.error(f"캐시 저장 실패 ({key}): {e}")
        return False

def get_cache(key: str) -> Optional[Any]:
    """
    [Deprecated] 캐시에서 데이터 가져오기 (메모리)
    - 사용 금지: `services.core.cache_service.CacheService().get(...)` 사용
    Args:
        key: 캐시 키
    Returns:
        저장된 데이터 또는 None
    """
    try:
        with _cache_lock:
            if key not in _cache_store:
                return None
            
            cache_data = _cache_store[key]
            
            # 만료 시간 확인
            if time.time() > cache_data['expire_time']:
                # 만료된 데이터 삭제
                del _cache_store[key]
                return None
            
            # JSON 역직렬화
            return json.loads(cache_data['value'])
    except Exception as e:
        logging.error(f"캐시 조회 실패 ({key}): {e}")
        return None

def delete_cache(key: str) -> bool:
    """
    [Deprecated] 캐시에서 데이터 삭제 (메모리)
    - 사용 금지: `services.core.cache_service.CacheService().delete(...)` 사용
    Args:
        key: 캐시 키
    Returns:
        성공 여부
    """
    try:
        with _cache_lock:
            if key in _cache_store:
                del _cache_store[key]
                logging.info(f"캐시 삭제 완료: {key}")
            return True
    except Exception as e:
        logging.error(f"캐시 삭제 실패 ({key}): {e}")
        return False

def clear_all_cache() -> bool:
    """
    [Deprecated] 모든 캐시 삭제 (메모리)
    - 사용 금지: `services.core.cache_service.CacheService().clear(...)` 사용
    Returns:
        성공 여부
    """
    try:
        with _cache_lock:
            _cache_store.clear()
            logging.info("전체 캐시 삭제 완료")
        return True
    except Exception as e:
        logging.error(f"전체 캐시 삭제 실패: {e}")
        return False

def cleanup_expired_cache():
    """만료된 캐시 정리"""
    try:
        with _cache_lock:
            current_time = time.time()
            expired_keys = []
            
            for key, cache_data in _cache_store.items():
                if current_time > cache_data['expire_time']:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del _cache_store[key]
            
            if expired_keys:
                logging.info(f"만료된 캐시 {len(expired_keys)}개 정리 완료")
    except Exception as e:
        logging.error(f"캐시 정리 실패: {e}") 