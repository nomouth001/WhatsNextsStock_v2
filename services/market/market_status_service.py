"""
시장 상태 서비스
시장 상태 및 시간 정보 관리 기능을 담당
"""

import os
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict
import pytz

class MarketStatusService:
    """시장 상태 전담 서비스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_current_time_info(self) -> Dict:
        """현재 시간 정보 가져오기"""
        try:
            # 한국 시간대
            kst = pytz.timezone('Asia/Seoul')
            kst_time = datetime.now(kst)
            
            # 미국 시간대
            est = pytz.timezone('US/Eastern')
            est_time = datetime.now(est)
            
            return {
                'kst_time': kst_time.strftime('%Y-%m-%d %H:%M:%S'),
                'est_time': est_time.strftime('%Y-%m-%d %H:%M:%S'),
                'kst_str': kst_time.strftime('%Y-%m-%d %H:%M:%S KST'),
                'est_str': est_time.strftime('%Y-%m-%d %H:%M:%S EST'),
                'kst_date': kst_time.strftime('%Y-%m-%d'),
                'est_date': est_time.strftime('%Y-%m-%d'),
                'kst_weekday': kst_time.strftime('%A'),
                'est_weekday': est_time.strftime('%A')
            }
        except Exception as e:
            self.logger.error(f"현재 시간 정보 가져오기 실패: {e}")
            return {}
    
    def is_market_open_improved(self, market_type: str = 'US') -> bool:
        """시장 개장 여부 확인 (개선된 버전)"""
        try:
            current_info = self.get_current_time_info()
            
            if market_type.upper() in ['KOSPI', 'KOSDAQ']:
                # 한국 시장 (KST 기준)
                kst_time = datetime.strptime(current_info['kst_time'], '%Y-%m-%d %H:%M:%S')
                weekday = kst_time.weekday()
                hour = kst_time.hour
                minute = kst_time.minute
                
                # 주말 제외
                if weekday >= 5:  # 토요일(5), 일요일(6)
                    return False
                
                # 장 시간: 9:00-15:30
                current_minutes = hour * 60 + minute
                market_start = 9 * 60  # 9:00
                market_end = 15 * 60 + 30  # 15:30
                
                return market_start <= current_minutes <= market_end
                
            else:
                # 미국 시장 (EST 기준)
                est_time = datetime.strptime(current_info['est_time'], '%Y-%m-%d %H:%M:%S')
                weekday = est_time.weekday()
                hour = est_time.hour
                minute = est_time.minute
                
                # 주말 제외
                if weekday >= 5:  # 토요일(5), 일요일(6)
                    return False
                
                # 장 시간: 9:30-16:00
                current_minutes = hour * 60 + minute
                market_start = 9 * 60 + 30  # 9:30
                market_end = 16 * 60  # 16:00
                
                return market_start <= current_minutes <= market_end
                
        except Exception as e:
            self.logger.error(f"시장 개장 여부 확인 실패: {e}")
            return False
    
    def get_market_status_info_improved(self, market_type: str = 'US') -> Dict:
        """시장 상태 정보 (개선된 버전)"""
        try:
            current_info = self.get_current_time_info()
            is_open = self.is_market_open_improved(market_type)
            
            if market_type.upper() in ['KOSPI', 'KOSDAQ']:
                market_name = "한국 증시"
                timezone = "KST"
                current_time = current_info['kst_time']
                current_date = current_info['kst_date']
                weekday = current_info['kst_weekday']
            else:
                market_name = "미국 증시"
                timezone = "EST"
                current_time = current_info['est_time']
                current_date = current_info['est_date']
                weekday = current_info['est_weekday']
            
            return {
                'market_name': market_name,
                'is_open': is_open,
                'current_time': current_time,
                'current_date': current_date,
                'weekday': weekday,
                'timezone': timezone,
                'status': '장중' if is_open else '장마감'
            }
            
        except Exception as e:
            self.logger.error(f"시장 상태 정보 가져오기 실패: {e}")
            return {
                'market_name': 'Unknown',
                'is_open': False,
                'current_time': 'Unknown',
                'current_date': 'Unknown',
                'weekday': 'Unknown',
                'timezone': 'Unknown',
                'status': 'Unknown'
            }
    
    def is_market_open(self, market_type: str = 'US') -> bool:
        """시장 개장 여부 확인 (기존 버전)"""
        return self.is_market_open_improved(market_type)
    
    def get_market_status_info(self, market_type: str = 'US') -> Dict:
        """시장 상태 정보 (기존 버전)"""
        return self.get_market_status_info_improved(market_type)
    
    def get_market_hours(self, market_type: str) -> Dict:
        """시장 운영 시간 정보"""
        if market_type.upper() in ['KOSPI', 'KOSDAQ']:
            return {
                'market_name': '한국 증시',
                'timezone': 'KST',
                'trading_hours': '09:00-15:30',
                'break_time': '11:20-13:00',
                'days': '월-금'
            }
        else:
            return {
                'market_name': '미국 증시',
                'timezone': 'EST',
                'trading_hours': '09:30-16:00',
                'break_time': '없음',
                'days': '월-금'
            } 