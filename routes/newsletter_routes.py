from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from services.newsletter_generation_service import NewsletterGenerationService
from services.newsletter_storage_service import NewsletterStorageService
from datetime import datetime
import os
import logging

newsletter_bp = Blueprint('newsletter', __name__)
logger = logging.getLogger(__name__)

storage_service = NewsletterStorageService()

@newsletter_bp.route('/kospi')
@login_required
def kospi_newsletter():
    """KOSPI 뉴스레터 페이지 - 단순화된 버전"""
    try:
        timeframe = request.args.get('timeframe', 'd')
        service = NewsletterGenerationService()
        # 생성 서비스 경로 사용: category_summary_html 포함
        newsletter_data = service.generate_kospi_newsletter(timeframe, current_user.id)

        html_content = render_template('newsletter/kospi_newsletter.html', 
                                       newsletter=newsletter_data,
                                       timeframe=timeframe)
        storage_service.save_html_file(html_content, kind="kospi")
        return html_content
    except Exception as e:
        logger.error(f"KOSPI 뉴스레터 생성 중 오류: {str(e)}")
        return render_template('error.html', error="뉴스레터 생성 중 오류가 발생했습니다.")

@newsletter_bp.route('/kosdaq')
@login_required
def kosdaq_newsletter():
    """KOSDAQ 뉴스레터 페이지"""
    try:
        timeframe = request.args.get('timeframe', 'd')
        service = NewsletterGenerationService()
        
        # KOSDAQ 뉴스레터 생성 (사용자 ID 전달하여 저장)
        newsletter_data = service.generate_kosdaq_newsletter(timeframe, current_user.id)
        
        html_content = render_template('newsletter/kosdaq_newsletter.html', 
                                       newsletter=newsletter_data,
                                       timeframe=timeframe)
        storage_service.save_html_file(html_content, kind="kosdaq")
        return html_content
    except Exception as e:
        logger.error(f"KOSDAQ 뉴스레터 생성 중 오류: {str(e)}")
        return render_template('error.html', error="뉴스레터 생성 중 오류가 발생했습니다.")

@newsletter_bp.route('/us')
@login_required
def us_newsletter():
    """미국장 뉴스레터 페이지"""
    try:
        timeframe = request.args.get('timeframe', 'd')
        service = NewsletterGenerationService()
        
        # 미국장 뉴스레터 생성 (사용자 ID 전달하여 저장)
        newsletter_data = service.generate_us_newsletter(timeframe, current_user.id)
        
        html_content = render_template('newsletter/us_newsletter.html', 
                                       newsletter=newsletter_data,
                                       timeframe=timeframe)
        storage_service.save_html_file(html_content, kind="us")
        return html_content
    except Exception as e:
        logger.error(f"미국장 뉴스레터 생성 중 오류: {str(e)}")
        return render_template('error.html', error="뉴스레터 생성 중 오류가 발생했습니다.")

@newsletter_bp.route('/combined')
@login_required
def combined_newsletter():
    """통합 뉴스레터 페이지"""
    try:
        timeframe = request.args.get('timeframe', 'd')
        primary_market = request.args.get('primary', 'kospi')  # kospi, kosdaq, US
        service = NewsletterGenerationService()
        
        # 통합 뉴스레터 생성 (사용자 ID 전달하여 저장)
        newsletter_data = service.generate_combined_newsletter(timeframe, primary_market, current_user.id)
        
        # 각 시장별 종목 수만 계산 (이미 분류는 완료됨)
        from models import Stock
        
        # KOSPI 데이터
        kospi_stocks = Stock.query.filter_by(market_type='KOSPI', is_active=True).count()
        
        # KOSDAQ 데이터
        kosdaq_stocks = Stock.query.filter_by(market_type='KOSDAQ', is_active=True).count()
        
        # US Market 데이터
        us_stocks = Stock.query.filter_by(market_type='US', is_active=True).count()
        
        # 크로스오버 수는 newsletter_data의 summary에서 추출
        kospi_crossover = newsletter_data.get('summary', {}).get('kospi', {}).get('crossover_proximity_count', 0) + \
                          newsletter_data.get('summary', {}).get('kospi', {}).get('crossover_occurred_count', 0)
        kosdaq_crossover = newsletter_data.get('summary', {}).get('kosdaq', {}).get('crossover_proximity_count', 0) + \
                          newsletter_data.get('summary', {}).get('kosdaq', {}).get('crossover_occurred_count', 0)
        us_crossover = newsletter_data.get('summary', {}).get('us', {}).get('crossover_proximity_count', 0) + \
                      newsletter_data.get('summary', {}).get('us', {}).get('crossover_occurred_count', 0)
        
        html_content = render_template('newsletter/combined_newsletter.html', 
                                       newsletter=newsletter_data,
                                       timeframe=timeframe,
                                       primary_market=primary_market,
                                       kospi_count=kospi_stocks,
                                       kospi_crossover=kospi_crossover,
                                       kosdaq_count=kosdaq_stocks,
                                       kosdaq_crossover=kosdaq_crossover,
                                       us_count=us_stocks,
                                       us_crossover=us_crossover)
        storage_service.save_html_file(html_content, kind="combined", primary=primary_market)
        return html_content
    except Exception as e:
        logger.error(f"통합 뉴스레터 생성 중 오류: {str(e)}")
        return render_template('error.html', error="뉴스레터 생성 중 오류가 발생했습니다.")

@newsletter_bp.route('/auto')
@login_required
def auto_newsletter():
    """시간대에 따른 자동 뉴스레터 페이지"""
    try:
        timeframe = request.args.get('timeframe', 'd')
        service = NewsletterGenerationService()
        
        # 시간대에 따른 뉴스레터 생성 (통합 뉴스레터 재사용)
        newsletter_data = service.get_newsletter_by_time(timeframe, current_user.id)
        
        html_content = render_template('newsletter/combined_newsletter.html', 
                                       newsletter=newsletter_data,
                                       timeframe=timeframe)
        storage_service.save_html_file(html_content, kind="auto")
        return html_content
    except Exception as e:
        logger.error(f"자동 뉴스레터 생성 중 오류: {str(e)}")
        return render_template('error.html', error="뉴스레터 생성 중 오류가 발생했습니다.")

@newsletter_bp.route('/history')
@login_required
def newsletter_history():
    """뉴스레터 히스토리 페이지"""
    try:
        service = NewsletterGenerationService()
        history = service.get_newsletter_history(current_user.id, limit=20)
        
        return render_template('newsletter/history.html', 
                             history=history)
    except Exception as e:
        logger.error(f"뉴스레터 히스토리 조회 중 오류: {str(e)}")
        return render_template('error.html', error="뉴스레터 히스토리 조회 중 오류가 발생했습니다.")

@newsletter_bp.route('/view/<int:newsletter_id>')
@login_required
def view_newsletter(newsletter_id):
    """저장된 뉴스레터 조회"""
    try:
        service = NewsletterGenerationService()
        newsletter_data = service.get_newsletter_by_id(newsletter_id, current_user.id)
        
        if not newsletter_data:
            return render_template('error.html', error="뉴스레터를 찾을 수 없습니다.")
        
        return render_template('newsletter/view_saved.html', 
                             newsletter=newsletter_data)
    except Exception as e:
        logger.error(f"뉴스레터 조회 중 오류: {str(e)}")
        return render_template('error.html', error="뉴스레터 조회 중 오류가 발생했습니다.")


# === 구독 해지 ===
@newsletter_bp.route('/unsubscribe/<token>')
def unsubscribe(token):
    try:
        from models import db, NewsletterSubscription
        sub = NewsletterSubscription.query.filter_by(unsubscribe_token=token).first()
        if not sub:
            return render_template('error.html', error="구독 정보를 찾을 수 없습니다.")
        sub.is_active = False
        db.session.commit()
        return render_template('email/unsubscribed.html')
    except Exception as e:
        logger.error(f"구독 해지 처리 중 오류: {e}")
        return render_template('error.html', error="구독 해지 처리 중 오류가 발생했습니다.")

# API 엔드포인트들
@newsletter_bp.route('/api/kospi')
@login_required
def api_kospi_newsletter():
    """KOSPI 뉴스레터 API"""
    try:
        timeframe = request.args.get('timeframe', 'd')
        service = NewsletterGenerationService()
        
        newsletter_data = service.generate_kospi_newsletter(timeframe, current_user.id)
        
        return jsonify({
            'success': True,
            'data': newsletter_data
        })
    except Exception as e:
        logger.error(f"KOSPI 뉴스레터 API 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@newsletter_bp.route('/api/kosdaq')
@login_required
def api_kosdaq_newsletter():
    """KOSDAQ 뉴스레터 API"""
    try:
        timeframe = request.args.get('timeframe', 'd')
        service = NewsletterGenerationService()
        
        newsletter_data = service.generate_kosdaq_newsletter(timeframe, current_user.id)
        
        return jsonify({
            'success': True,
            'data': newsletter_data
        })
    except Exception as e:
        logger.error(f"KOSDAQ 뉴스레터 API 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@newsletter_bp.route('/api/us')
@login_required
def api_us_newsletter():
    """미국장 뉴스레터 API"""
    try:
        timeframe = request.args.get('timeframe', 'd')
        service = NewsletterGenerationService()
        
        newsletter_data = service.generate_us_newsletter(timeframe, current_user.id)
        
        return jsonify({
            'success': True,
            'data': newsletter_data
        })
    except Exception as e:
        logger.error(f"미국장 뉴스레터 API 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@newsletter_bp.route('/api/combined')
@login_required
def api_combined_newsletter():
    """통합 뉴스레터 API"""
    try:
        timeframe = request.args.get('timeframe', 'd')
        primary_market = request.args.get('primary', 'kospi')
        service = NewsletterGenerationService()
        
        newsletter_data = service.generate_combined_newsletter(timeframe, primary_market, current_user.id)
        
        return jsonify({
            'success': True,
            'data': newsletter_data
        })
    except Exception as e:
        logger.error(f"통합 뉴스레터 API 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@newsletter_bp.route('/api/history')
@login_required
def api_newsletter_history():
    """뉴스레터 히스토리 API"""
    try:
        limit = request.args.get('limit', 10, type=int)
        service = NewsletterGenerationService()
        
        history = service.get_newsletter_history(current_user.id, limit)
        
        return jsonify({
            'success': True,
            'data': history
        })
    except Exception as e:
        logger.error(f"뉴스레터 히스토리 API 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 