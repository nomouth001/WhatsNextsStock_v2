import os
import csv
import pandas as pd
import yfinance as yf
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Stock
from forms import CSVUploadForm
from datetime import datetime
from services.market.market_data_orchestrator import MarketDataOrchestrator

stock_bp = Blueprint('stock_bp', __name__, url_prefix='/stock')

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    """허용된 파일 확장자 확인"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_company_name_from_yahoo(ticker):
    """야후 파이낸스에서 회사명 가져오기"""
    try:
        stock_info = yf.Ticker(ticker)
        company_name = stock_info.info.get('longName', 'Unknown')
        return company_name
    except Exception as e:
        print(f"Error fetching company name for {ticker}: {e}")
        return "Unknown"

def process_csv_file(file_path, market_type):
    """CSV 파일 처리 및 데이터베이스 저장 (비활성 종목 재활성화 포함)"""
    # CSV 로드 및 컬럼 보정
    try:
        df = pd.read_csv(file_path)
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='cp949')

    # 컬럼명 유연화: Ticker/Symbol → ticker
    if 'ticker' not in df.columns:
        for alt in ['Ticker', 'symbol', 'Symbol']:
            if alt in df.columns:
                df = df.rename(columns={alt: 'ticker'})
                break
    if 'ticker' not in df.columns:
        raise ValueError("CSV에 'ticker' 컬럼이 없습니다. (지원: ticker/Ticker/symbol/Symbol)")

    # MEMO(2025-08-20): 회사명 컬럼 허용 범위 확대 → 내부 표준 'company_name'으로 정규화
    company_name_aliases = [
        'company_name', 'Company_Name', 'name', 'Name', 'company', 'Company', 'longName', 'LongName',
        'companyName', 'CompanyName'
    ]
    if 'company_name' not in df.columns:
        for alias in company_name_aliases:
            if alias in df.columns:
                df = df.rename(columns={alias: 'company_name'})
                break

    orchestrator = MarketDataOrchestrator()

    added = 0
    reactivated = 0
    processed = 0

    for _, row in df.iterrows():
        raw = row.get('ticker')
        if raw is None or str(raw).strip() == '':
            continue
        ticker = str(raw).strip().upper()

        # (ticker, market_type) 기준으로 조회
        existing = Stock.query.filter_by(ticker=ticker, market_type=market_type).first()

        # CSV에서 회사명 추출 (있으면 우선 사용)
        csv_company_name = None
        try:
            if 'company_name' in df.columns:
                raw_name = row.get('company_name')
                if raw_name is not None:
                    csv_company_name = str(raw_name).strip()
                    if csv_company_name == '':
                        csv_company_name = None
        except Exception:
            csv_company_name = None
        if existing:
            # 비활성인 경우 재활성화
            if not existing.is_active:
                existing.is_active = True
                reactivated += 1

            # 회사명 채우기: CSV 우선, 없으면 yfinance 보강
            if csv_company_name:
                # CSV 값이 있고 기존과 다르면 갱신
                if (existing.company_name or '').strip() != csv_company_name:
                    existing.company_name = csv_company_name
            else:
                if not existing.company_name:
                    # 기존 로직(메모): 비어있을 때 yfinance로 보강
                    # existing.company_name = get_company_name_from_yahoo(ticker)
                    # MEMO(2025-08-20): 위 한 줄은 회귀 대비 주석 보존. 아래와 동일 동작 수행.
                    existing.company_name = get_company_name_from_yahoo(ticker)
        else:
            # 없으면 신규 추가: CSV 우선, 없으면 yfinance
            if csv_company_name:
                company_name = csv_company_name
            else:
                # 기존 로직(메모): 신규 추가 시 yfinance 조회
                # company_name = get_company_name_from_yahoo(ticker)
                # MEMO(2025-08-20): 위 한 줄은 회귀 대비 주석 보존. 아래와 동일 동작 수행.
                company_name = get_company_name_from_yahoo(ticker)

            new_stock = Stock(
                ticker=ticker,
                company_name=company_name,
                market_type=market_type
            )
            db.session.add(new_stock)
            added += 1

        # 신규/재활성 모두 데이터 확보 시도 (조용히 실패 허용)
        try:
            orchestrator.execute(ticker, market_type)
        except Exception:
            pass

        processed += 1

    db.session.commit()
    return {"processed": processed, "added": added, "reactivated": reactivated}

@stock_bp.route('/upload-csv', methods=['POST'])
def upload_csv():
    # 표준화된 응답 포맷 유지: {success: bool, message: str}
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "파일 필드가 없습니다."}), 400

    file = request.files['file']
    market_type = request.form.get('market_type', 'KOSPI')

    if not file or file.filename == '':
        return jsonify({"success": False, "message": "선택된 파일이 없습니다."}), 400

    if file and allowed_file(file.filename):
        try:
            # 업로드 폴더 보장
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)

            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            try:
                stats = process_csv_file(file_path, market_type)
                return jsonify({
                    "success": True,
                    "message": f"처리 완료: {stats['processed']}건 (신규 {stats['added']}건, 재활성 {stats['reactivated']}건)",
                    "stats": stats
                })
            except Exception as e:
                db.session.rollback()
                return jsonify({"success": False, "message": f"파일 처리 실패: {str(e)}"}), 500
        except Exception as e:
            return jsonify({"success": False, "message": f"업로드 실패: {str(e)}"}), 500

    return jsonify({"success": False, "message": "허용되지 않은 파일 형식입니다."}), 400

@stock_bp.route('/stocks')
@login_required
def list_stocks():
    """종목 목록 조회"""
    try:
        # 시장별 종목 조회
        us_stocks = Stock.query.filter_by(market_type='US', is_active=True).all()
        kospi_stocks = Stock.query.filter_by(market_type='KOSPI', is_active=True).all()
        kosdaq_stocks = Stock.query.filter_by(market_type='KOSDAQ', is_active=True).all()
        
        return render_template('stock/list.html', 
                             us_stocks=us_stocks,
                             kospi_stocks=kospi_stocks,
                             kosdaq_stocks=kosdaq_stocks)
    except Exception as e:
        flash(f'종목 목록 조회 중 오류 발생: {str(e)}', 'error')
        return redirect(url_for('user.home'))

@stock_bp.route('/stocks/<market_type>')
@login_required
def list_stocks_by_market(market_type):
    """시장별 종목 목록 조회"""
    try:
        if market_type not in ['US', 'KOSPI', 'KOSDAQ']:
            flash('잘못된 시장 타입입니다.', 'error')
            return redirect(url_for('stock.list_stocks'))
        
        stocks = Stock.query.filter_by(market_type=market_type, is_active=True).all()
        
        return render_template('stock/list_by_market.html', 
                             stocks=stocks,
                             market_type=market_type)
    except Exception as e:
        flash(f'종목 목록 조회 중 오류 발생: {str(e)}', 'error')
        return redirect(url_for('stock.list_stocks'))

@stock_bp.route('/stock/<ticker>')
@login_required
def view_stock(ticker):
    """개별 종목 상세 조회"""
    try:
        stock = Stock.query.filter_by(ticker=ticker, is_active=True).first()
        if not stock:
            flash('종목을 찾을 수 없습니다.', 'error')
            return redirect(url_for('stock.list_stocks'))
        
        return render_template('stock/detail.html', stock=stock)
    except Exception as e:
        flash(f'종목 조회 중 오류 발생: {str(e)}', 'error')
        return redirect(url_for('stock.list_stocks')) 