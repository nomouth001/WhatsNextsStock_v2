"""
Mock UnifiedMarketAnalysisService
테스트용 Mock 서비스
"""

import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


class MockUnifiedMarketAnalysisService:
    """Mock 통합 시장 분석 서비스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_single_stock_comprehensive(self, ticker: str, market_type: str, timeframe: str) -> Dict[str, Any]:
        """Mock 단일 종목 종합 분석"""
        try:
            # Mock 분석 결과 생성
            result = {
                "success": True,
                "symbol": ticker,
                "market_type": market_type,
                "timeframe": timeframe,
                "analysis_date": datetime.now().isoformat(),
                "technical_analysis": {
                    "trend": "BULLISH",
                    "strength": 0.75,
                    "support_levels": [50000, 48000],
                    "resistance_levels": [52000, 54000],
                    "analysis_score": 85.5
                },
                "fundamental_analysis": {
                    "pe_ratio": 15.2,
                    "pb_ratio": 1.8,
                    "dividend_yield": 2.5,
                    "analysis_score": 78.3
                },
                "ai_analysis": {
                    "sentiment": "POSITIVE",
                    "confidence": 0.82,
                    "recommendation": "BUY",
                    "analysis_score": 88.7
                },
                "recommendations": [
                    "기술적 지표가 강세를 보임",
                    "기본적 분석 결과 양호",
                    "AI 분석 결과 매수 추천"
                ],
                "risk_level": "MEDIUM",
                "confidence_score": 0.85
            }
            
            self.logger.info(f"Mock 분석 완료: {ticker}")
            return result
            
        except Exception as e:
            self.logger.error(f"Mock 분석 중 에러: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "symbol": ticker,
                "market_type": market_type,
                "timeframe": timeframe
            }
    
    def analyze_market_comprehensive(self, market_type: str, timeframe: str = 'd') -> Dict[str, Any]:
        """Mock 시장 종합 분석"""
        try:
            result = {
                "success": True,
                "market": market_type,
                "analysis_date": datetime.now().isoformat(),
                "total_stocks": 100,
                "analyzed_stocks": 95,
                "market_summary": {
                    "trend": "BULLISH",
                    "strength": 0.7,
                    "volume": "HIGH"
                },
                "top_performers": [
                    {"symbol": "005930.KS", "performance": 0.15},
                    {"symbol": "000660.KS", "performance": 0.12}
                ],
                "bottom_performers": [
                    {"symbol": "012450.KS", "performance": -0.05},
                    {"symbol": "034020.KS", "performance": -0.03}
                ],
                "market_trend": "BULLISH",
                "recommendations": [
                    "시장 전반적으로 강세",
                    "기술주 중심 매수 추천"
                ]
            }
            
            self.logger.info(f"Mock 시장 분석 완료: {market_type}")
            return result
            
        except Exception as e:
            self.logger.error(f"Mock 시장 분석 중 에러: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "market": market_type,
                "timeframe": timeframe
            } 