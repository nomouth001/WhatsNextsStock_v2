#!/usr/bin/env python3
"""
자동 의존성 업데이트 스크립트 (교차 플랫폼: Windows / Ubuntu 공용)

동작 개요:
- 허용 목록(allowlist) 패키지만 업그레이드(yfinance, finance-datareader, pandas)
- 스모크 테스트(간단 데이터 호출) 수행
- 실패 시 핀 버전으로 즉시 롤백
- 결과를 logs/auto_update_deps.log에 기록

스케줄러 등록 방법(주석 안내):

1) Windows (작업 스케줄러)
   - 프로그램: <가상환경 또는 파이썬 경로>\python.exe
   - 인수:     C:\_PythonWorkspace\_NewsLetter_WorkingFolder\scripts\auto_update_deps.py
   - 시작 위치: C:\_PythonWorkspace\_NewsLetter_WorkingFolder
   - 예시 명령:
       schtasks /Create /SC WEEKLY /D SUN /TN AutoUpdateDeps ^
         /TR "C:\\_PythonWorkspace\\_NewsLetter_WorkingFolder\\.venv\\Scripts\\python.exe C:\\_PythonWorkspace\\_NewsLetter_WorkingFolder\\scripts\\auto_update_deps.py" ^
         /ST 02:30

2) Ubuntu (cron, Lightsail 포함)
   - 가상환경 파이썬을 사용해 실행
   - crontab -e 후 아래 예시 추가(매주 일요일 02:30):
       30 2 * * 0 /home/ubuntu/app/.venv/bin/python /home/ubuntu/app/scripts/auto_update_deps.py >> /home/ubuntu/app/logs/auto_update_deps.log 2>&1

주의:
- 먼저 수동으로 한 번 실행해 정상 동작을 확인하세요.
- 네트워크/방화벽이 pip 및 데이터 소스(yahoo/FDR)에 접근 가능해야 합니다.
"""

from __future__ import annotations

import sys
import subprocess
import datetime as dt
import os
from pathlib import Path
from typing import List, Dict


# ===== 설정 =====
# 허용 목록(업그레이드 대상)
ALLOW_PACKAGES: List[str] = [
    "yfinance",
    "finance-datareader",
    "pandas",
]

# 롤백(핀) 버전: 필요 시 환경에 맞게 조정
PINS: Dict[str, str] = {
    "yfinance": "0.2.65",
    "finance-datareader": "0.9.96",
    "pandas": "2.2.3",
}


def resolve_app_paths() -> tuple[Path, Path]:
    """앱 루트와 로그 파일 경로를 결정한다.

    - 스크립트 기준으로 상위 디렉토리를 앱 루트로 가정
    - logs/auto_update_deps.log 파일 경로 반환
    """
    app_dir = Path(__file__).resolve().parents[1]
    log_dir = app_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "auto_update_deps.log"
    return app_dir, log_file


APP_DIR, LOG_FILE = resolve_app_paths()


def log(message: str) -> None:
    timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}\n"
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        # 로그 파일 기록 실패 시에도 표준출력은 보장
        pass
    print(line, end="")


def run(cmd: List[str], allow_fail: bool = False) -> int:
    """서브프로세스 실행 헬퍼. 표준출력/에러를 로그에 적재.

    Args:
        cmd: 실행할 명령(리스트 형태)
        allow_fail: True면 비정상 종료를 예외로 승격하지 않음
    Returns:
        프로세스 반환 코드(int)
    Raises:
        RuntimeError: allow_fail=False이고 반환 코드가 0이 아닐 때
    """
    log(f"$ {' '.join(cmd)}")
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.stdout:
            log(res.stdout.strip())
        if res.stderr:
            log(res.stderr.strip())
        if res.returncode != 0 and not allow_fail:
            raise RuntimeError(
                f"Command failed: {' '.join(cmd)} (code={res.returncode})"
            )
        return res.returncode
    except Exception as e:
        log(f"ERROR: {e}")
        if allow_fail:
            return 1
        raise


def pip_exec() -> List[str]:
    """현재 파이썬 해석기의 pip를 사용하도록 명령을 구성.

    - 가상환경을 활성화한 상태라면 해당 venv의 pip가 사용됨
    - 그렇지 않더라도 sys.executable -m pip로 안전하게 호출
    """
    return [sys.executable, "-m", "pip"]


def list_outdated() -> None:
    run(pip_exec() + ["list", "--outdated"], allow_fail=True)


def upgrade_allowlist() -> None:
    run(pip_exec() + ["install", "-U", *ALLOW_PACKAGES])


def smoke_test() -> bool:
    """간단 스모크 테스트 수행.

    - yfinance: AAPL 1개월 히스토리 조회
    - FinanceDataReader: AAPL 2024-01 범위 조회
    """
    try:
        import yfinance as yf  # type: ignore
        import FinanceDataReader as fdr  # type: ignore
    except Exception as e:
        log(f"import error: {e}")
        return False

    ok = True
    try:
        df1 = yf.Ticker("AAPL").history(period="1mo")
        ok &= (not df1.empty)
    except Exception as e:
        log(f"yfinance error: {e}")
        ok = False

    try:
        df2 = fdr.DataReader("AAPL", dt.date(2024, 1, 1), dt.date(2024, 2, 1))
        ok &= (not df2.empty)
    except Exception as e:
        log(f"FDR error: {e}")
        ok = False

    log("SMOKE_OK" if ok else "SMOKE_FAIL")
    return ok


def rollback_pins() -> None:
    pkgs = [f"{name}=={ver}" for name, ver in PINS.items()]
    run(pip_exec() + ["install", *pkgs])


def main() -> None:
    log("=== Auto Update Deps: START ===")
    list_outdated()
    try:
        upgrade_allowlist()
        if not smoke_test():
            log("Smoke failed → rollback to pinned versions")
            rollback_pins()
            log("Rolled back to pinned versions")
            log("=== Auto Update Deps: END (ROLLBACK) ===")
            sys.exit(1)
        log("=== Auto Update Deps: END (OK) ===")
    except Exception as e:
        log(f"FATAL: {e}")
        # 마지막 방어선: 롤백 시도
        try:
            rollback_pins()
            log("Rolled back to pinned versions after fatal error")
        except Exception as e2:
            log(f"Rollback failed: {e2}")
        sys.exit(2)


if __name__ == "__main__":
    main()


