import json
import re
import sys
from typing import Dict


def login_and_get_session(base_url: str):
    try:
        import requests
        s = requests.Session()
        r = s.get(f"{base_url}/auth/login", timeout=15)
        csrf = ""
        try:
            m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r.text)
            csrf = m.group(1) if m else ""
        except Exception:
            csrf = ""
        s.post(
            f"{base_url}/auth/login",
            data={
                "username": "admin",
                "password": "admin123",
                "remember_me": "y",
                "csrf_token": csrf,
            },
            timeout=15,
        )
        return s
    except Exception as e:
        print(json.dumps({"login_error": str(e)}, ensure_ascii=False))
        sys.exit(2)


def check_admin_endpoints(base_url: str, s) -> Dict:
    results: Dict[str, Dict] = {}
    for market in ["us", "kospi", "kosdaq"]:
        try:
            home = s.get(f"{base_url}/admin/home/{market}", timeout=20)
            api = s.get(f"{base_url}/admin/api/market_summary/{market}", timeout=20)
            api_json = {}
            try:
                api_json = api.json()
            except Exception:
                api_json = {}
            results[market] = {
                "home_status": home.status_code,
                "api_status": api.status_code,
                "api_keys": list((api_json.get("summary") or {}).keys()) if api.ok else [],
            }
        except Exception as e:
            results[market] = {"error": str(e)}
    return results


def check_services() -> Dict:
    # 오케스트레이션 래퍼 및 파일 리더 간단 확인
    try:
        from services import orchestrate_and_get_latest_ohlcv
        from services.market.data_reading_service import DataReadingService

        kospi_tickers = ["005930.KS", "000660.KS"]
        orch = orchestrate_and_get_latest_ohlcv(kospi_tickers, "KOSPI") or {}
        reader = DataReadingService()
        read_ok = {}
        for t in kospi_tickers:
            df = reader.read_ohlcv_csv(t, "KOSPI", "d")
            read_ok[t] = (not df.empty)

        # numpy 직렬화 이슈를 피하기 위해 문자열 변환
        safe_orch = {}
        for k, v in orch.items():
            safe = {}
            for kk, vv in (v or {}).items():
                try:
                    safe[kk] = int(vv)
                except Exception:
                    try:
                        safe[kk] = float(vv)
                    except Exception:
                        safe[kk] = str(vv)
            safe_orch[k] = safe

        return {"orchestrate_and_get_latest_ohlcv": safe_orch, "ohlcv_read_nonempty": read_ok}
    except Exception as e:
        return {"services_error": str(e)}


def main():
    base_url = "http://127.0.0.1:5000"
    s = login_and_get_session(base_url)
    endpoints = check_admin_endpoints(base_url, s)
    services_check = check_services()
    output = {"endpoints": endpoints, "services": services_check}
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


