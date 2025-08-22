# 주식 뉴스레터 관리 시스템

Flask 기반의 주식 뉴스레터 관리 시스템입니다. KOSPI/KOSDAQ(한국)과 US(미국) 주식 데이터를 관리하고 CSV 파일 업로드를 통해 주식 리스트를 쉽게 관리할 수 있습니다.

## 주요 기능

### 인증 시스템
- 사용자 로그인/회원가입
- 관리자 권한 관리
- 세션 관리

### 관리자 기능
- **대시보드**: 전체 통계 및 현황 보기
- **주식 리스트 관리**: KOSPI/KOSDAQ/US 주식 리스트 토글 및 관리
- **CSV 업로드**: 주식 데이터 일괄 업로드
- **자동 회사명 추출**: 야후 파이낸스 API를 통한 회사명 자동 추출

### 주식 데이터 관리
- KOSPI/KOSDAQ(한국) / US(미국) 시장 구분
- 티커 기반 주식 관리
- CSV 파일을 통한 일괄 데이터 업로드
- 중복 데이터 자동 처리

## 설치 및 실행

### 1. 가상환경 생성 및 활성화

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 가상환경 활성화 (macOS/Linux)
source venv/bin/activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 초기 관리자 계정 생성

```bash
python init_admin.py
```

기본 관리자 계정:
- 사용자명: `admin`
- 비밀번호: `admin123`
- 이메일: `admin@example.com`

### 4. 애플리케이션 실행

```bash
python app.py
```

애플리케이션이 `http://localhost:5000`에서 실행됩니다.

## 사용법

### 1. 로그인
- 브라우저에서 `http://localhost:5000` 접속
- 초기 관리자 계정으로 로그인

### 2. 주식 리스트 관리
- 관리자 홈에서 KOSPI/KOSDAQ/US 토글 스위치로 시장 선택
- CSV 업로드 버튼으로 주식 데이터 일괄 업로드

### 3. CSV 파일 형식
CSV 파일은 다음 형식을 지원합니다:

**필수 컬럼:**
- `ticker` 또는 `symbol` 또는 `code`: 주식 티커 심볼

**선택 컬럼:**
- `name` 또는 `company_name` 또는 `company`: 회사명 (없으면 야후 파이낸스에서 자동 추출)

**예시 CSV:**
```csv
ticker,company_name
AAPL,Apple Inc.
MSFT,Microsoft Corporation
005930,삼성전자
```

또는 티커만:
```csv
ticker
AAPL
MSFT
GOOGL
```

## 프로젝트 구조

```
├── app.py                 # 메인 애플리케이션
├── config.py              # 설정 파일
├── models.py              # 데이터베이스 모델
├── forms.py               # WTForms 폼 정의
├── init_admin.py          # 관리자 계정 생성 스크립트
├── requirements.txt       # 의존성 목록
├── routes/                # 라우트 모듈
│   ├── auth_routes.py     # 인증 관련 라우트
│   ├── admin_routes.py    # 관리자 라우트
│   ├── stock_routes.py    # 주식 관련 라우트
│   └── user_routes.py     # 사용자 라우트
├── templates/             # HTML 템플릿
│   ├── base.html          # 기본 템플릿
│   ├── auth/              # 인증 템플릿
│   ├── admin/             # 관리자 템플릿
│   └── user/              # 사용자 템플릿
├── static/                # 정적 파일
├── uploads/               # 업로드 파일 임시 저장
├── stock_lists/           # 주식 리스트 파일
└── logs/                  # 로그 파일
```

## 기술 스택

- **Backend**: Flask, SQLAlchemy
- **Frontend**: Bootstrap 5, JavaScript
- **Database**: SQLite (기본), 다른 DB로 변경 가능
- **Data Processing**: Pandas, yfinance
- **Authentication**: Flask-Login

## 환경 변수

`.env` 파일을 생성하여 다음 환경 변수를 설정할 수 있습니다:

```
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///stock_newsletter.db
FLASK_ENV=development
```

## 주의사항

1. **보안**: 운영 환경에서는 반드시 기본 관리자 비밀번호를 변경하세요.
2. **API 제한**: 야후 파이낸스 API는 요청 제한이 있을 수 있습니다.
3. **한국 주식**: 한국 주식의 경우 `.KS` (코스피) 또는 `.KQ` (코스닥) 접미사가 자동으로 추가됩니다.

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 