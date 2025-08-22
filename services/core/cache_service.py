"""
임시파일 기반 캐시 서비스
메모리 기반 캐시를 대체하여 디스크에 임시파일로 캐시를 저장
"""

import os
import json
import pickle
import logging
import tempfile
import gzip
import hashlib
import time
from datetime import datetime
from typing import Any, Optional, Dict
from pathlib import Path

class CacheService:
    """통합 캐시 서비스 (검증 모듈용)"""
    
    def __init__(self):
        self.file_cache = FileBasedCacheService()
        self.logger = logging.getLogger(__name__)
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """캐시에 데이터 저장"""
        try:
            self.file_cache.set_cache(key, value, ttl)
            return True
        except Exception as e:
            self.logger.error(f"캐시 저장 실패: {e}")
            return False
    
    def get(self, key: str) -> Any:
        """캐시에서 데이터 가져오기"""
        try:
            return self.file_cache.get_cache(key)
        except Exception as e:
            self.logger.error(f"캐시 조회 실패: {e}")
            return None
    
    def clear(self) -> bool:
        """캐시 정리"""
        try:
            self.file_cache.clear_cache()
            return True
        except Exception as e:
            self.logger.error(f"캐시 정리 실패: {e}")
            return False

    def delete(self, key: str) -> bool:
        """특정 키의 캐시 삭제"""
        try:
            self.file_cache.delete_cache(key)
            return True
        except Exception as e:
            self.logger.error(f"캐시 삭제 실패 ({key}): {e}")
            return False

class FileBasedCacheService:
    """임시파일 기반 캐시 서비스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache_dir = tempfile.mkdtemp(prefix='market_analysis_cache_')
        self.logger.info(f"캐시 디렉토리 생성: {self.cache_dir}")
    
    def get_cache(self, key: str) -> Optional[Dict]:
        """
        캐시에서 데이터 가져오기
        Args:
            key: 캐시 키
        Returns:
            저장된 데이터 또는 None
        """
        try:
            cache_file = self._get_cache_file_path(key)
            
            # 캐시 파일 존재 확인
            if not os.path.exists(cache_file):
                return None
            
            # 만료 시간 확인
            if self._is_cache_expired(cache_file):
                self._remove_cache_file(cache_file)
                return None
            
            # 파일에서 데이터 로드
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            # 만료 시간 확인
            if time.time() > cache_data['expire_time']:
                self._remove_cache_file(cache_file)
                return None
            
            self.logger.info(f"캐시에서 데이터 로드: {key}")
            return cache_data['value']
            
        except Exception as e:
            self.logger.error(f"캐시 조회 실패 ({key}): {e}")
            return None
    
    def set_cache(self, key: str, data: Dict, expire: int = 3600) -> None:
        """
        캐시에 데이터 저장
        Args:
            key: 캐시 키
            data: 저장할 데이터
            expire: 만료 시간 (초)
        """
        try:
            # 캐시 데이터 준비
            cache_data = {
                'value': data,
                'created_time': time.time(),
                'expire_time': time.time() + expire,
                'expire_duration': expire
            }
            
            # 임시 파일에 pickle 직렬화 저장
            cache_file = self._get_cache_file_path(key)
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            self.logger.info(f"캐시 저장 완료: {key} (만료: {expire}초)")
            
        except Exception as e:
            self.logger.error(f"캐시 저장 실패 ({key}): {e}")
    
    def clear_cache(self, pattern: str = None) -> None:
        """
        캐시 정리
        Args:
            pattern: 삭제할 파일 패턴 (None이면 모든 캐시 삭제)
        """
        try:
            if pattern:
                # 패턴에 맞는 파일만 삭제
                for filename in os.listdir(self.cache_dir):
                    if pattern in filename:
                        file_path = os.path.join(self.cache_dir, filename)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            self.logger.info(f"캐시 파일 삭제: {filename}")
            else:
                # 모든 캐시 파일 삭제
                for filename in os.listdir(self.cache_dir):
                    file_path = os.path.join(self.cache_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                
                self.logger.info("모든 캐시 파일 삭제 완료")
                
        except Exception as e:
            self.logger.error(f"캐시 정리 실패: {e}")

    def delete_cache(self, key: str) -> None:
        """특정 키에 해당하는 캐시 파일 삭제"""
        try:
            cache_file = self._get_cache_file_path(key)
            self._remove_cache_file(cache_file)
        except Exception as e:
            self.logger.error(f"캐시 단일 삭제 실패 ({key}): {e}")
    
    def get_cache_stats(self) -> Dict:
        """
        캐시 통계 정보 반환
        Returns:
            캐시 통계 정보
        """
        try:
            cache_files = [f for f in os.listdir(self.cache_dir) if os.path.isfile(os.path.join(self.cache_dir, f))]
            
            total_size = 0
            valid_files = 0
            expired_files = 0
            
            for filename in cache_files:
                file_path = os.path.join(self.cache_dir, filename)
                file_size = os.path.getsize(file_path)
                total_size += file_size
                
                if self._is_cache_expired(file_path):
                    expired_files += 1
                else:
                    valid_files += 1
            
            return {
                'total_files': len(cache_files),
                'valid_files': valid_files,
                'expired_files': expired_files,
                'total_size_mb': total_size / (1024 * 1024),
                'cache_dir': self.cache_dir
            }
            
        except Exception as e:
            self.logger.error(f"캐시 통계 조회 실패: {e}")
            return {}
    
    def cleanup_expired_cache(self) -> None:
        """만료된 캐시 정리"""
        try:
            expired_count = 0
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path) and self._is_cache_expired(file_path):
                    os.remove(file_path)
                    expired_count += 1
            
            if expired_count > 0:
                self.logger.info(f"만료된 캐시 {expired_count}개 정리 완료")
                
        except Exception as e:
            self.logger.error(f"만료된 캐시 정리 실패: {e}")
    
    def _get_cache_file_path(self, key: str) -> str:
        """
        캐시 파일 경로 생성
        Args:
            key: 캐시 키
        Returns:
            캐시 파일 경로
        """
        # 키를 해시하여 파일명 생성
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"cache_{key_hash}.pkl")
    
    def _is_cache_expired(self, cache_file: str) -> bool:
        """
        캐시 파일 만료 여부 확인
        Args:
            cache_file: 캐시 파일 경로
        Returns:
            만료 여부
        """
        try:
            # 파일 수정 시간 확인
            file_mtime = os.path.getmtime(cache_file)
            current_time = time.time()
            
            # 기본 만료 시간 (1시간)
            default_expire = 3600
            
            # 파일이 너무 오래된 경우 만료로 간주
            if current_time - file_mtime > default_expire:
                return True
            
            # pickle 파일에서 만료 시간 확인
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            return current_time > cache_data.get('expire_time', 0)
            
        except Exception as e:
            self.logger.error(f"캐시 만료 확인 실패: {e}")
            return True
    
    def _remove_cache_file(self, cache_file: str) -> None:
        """
        캐시 파일 삭제
        Args:
            cache_file: 삭제할 캐시 파일 경로
        """
        try:
            if os.path.exists(cache_file):
                os.remove(cache_file)
                self.logger.info(f"캐시 파일 삭제: {cache_file}")
        except Exception as e:
            self.logger.error(f"캐시 파일 삭제 실패: {e}")
    
    def set_cache_compressed(self, key: str, data: Dict, expire: int = 3600) -> None:
        """
        압축된 캐시에 데이터 저장
        Args:
            key: 캐시 키
            data: 저장할 데이터
            expire: 만료 시간 (초)
        """
        try:
            # 캐시 데이터 준비
            cache_data = {
                'value': data,
                'created_time': time.time(),
                'expire_time': time.time() + expire,
                'expire_duration': expire
            }
            
            # JSON 직렬화 후 gzip 압축
            json_data = json.dumps(cache_data, ensure_ascii=False)
            compressed_data = gzip.compress(json_data.encode('utf-8'))
            
            # 압축된 데이터를 파일에 저장
            cache_file = self._get_cache_file_path(key)
            with open(cache_file, 'wb') as f:
                f.write(compressed_data)
            
            self.logger.info(f"압축 캐시 저장 완료: {key} (만료: {expire}초)")
            
        except Exception as e:
            self.logger.error(f"압축 캐시 저장 실패 ({key}): {e}")
    
    def get_cache_compressed(self, key: str) -> Optional[Dict]:
        """
        압축된 캐시에서 데이터 가져오기
        Args:
            key: 캐시 키
        Returns:
            저장된 데이터 또는 None
        """
        try:
            cache_file = self._get_cache_file_path(key)
            
            # 캐시 파일 존재 확인
            if not os.path.exists(cache_file):
                return None
            
            # 만료 시간 확인
            if self._is_cache_expired(cache_file):
                self._remove_cache_file(cache_file)
                return None
            
            # 압축된 파일에서 데이터 로드
            with open(cache_file, 'rb') as f:
                compressed_data = f.read()
            
            # gzip 압축 해제 후 JSON 역직렬화
            json_data = gzip.decompress(compressed_data).decode('utf-8')
            cache_data = json.loads(json_data)
            
            # 만료 시간 확인
            if time.time() > cache_data['expire_time']:
                self._remove_cache_file(cache_file)
                return None
            
            self.logger.info(f"압축 캐시에서 데이터 로드: {key}")
            return cache_data['value']
            
        except Exception as e:
            self.logger.error(f"압축 캐시 조회 실패 ({key}): {e}")
            return None
    
    def set_cache_json(self, key: str, data: Dict, expire: int = 3600) -> None:
        """
        JSON 형식으로 캐시에 데이터 저장
        Args:
            key: 캐시 키
            data: 저장할 데이터
            expire: 만료 시간 (초)
        """
        try:
            # 캐시 데이터 준비
            cache_data = {
                'value': data,
                'created_time': time.time(),
                'expire_time': time.time() + expire,
                'expire_duration': expire
            }
            
            # JSON 형식으로 파일에 저장
            cache_file = self._get_cache_file_path(key)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"JSON 캐시 저장 완료: {key} (만료: {expire}초)")
            
        except Exception as e:
            self.logger.error(f"JSON 캐시 저장 실패 ({key}): {e}")
    
    def get_cache_json(self, key: str) -> Optional[Dict]:
        """
        JSON 형식 캐시에서 데이터 가져오기
        Args:
            key: 캐시 키
        Returns:
            저장된 데이터 또는 None
        """
        try:
            cache_file = self._get_cache_file_path(key)
            
            # 캐시 파일 존재 확인
            if not os.path.exists(cache_file):
                return None
            
            # 만료 시간 확인
            if self._is_cache_expired(cache_file):
                self._remove_cache_file(cache_file)
                return None
            
            # JSON 파일에서 데이터 로드
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 만료 시간 확인
            if time.time() > cache_data['expire_time']:
                self._remove_cache_file(cache_file)
                return None
            
            self.logger.info(f"JSON 캐시에서 데이터 로드: {key}")
            return cache_data['value']
            
        except Exception as e:
            self.logger.error(f"JSON 캐시 조회 실패 ({key}): {e}")
            return None 