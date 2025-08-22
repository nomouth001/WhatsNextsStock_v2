import sys
import time
from datetime import datetime, timedelta

import pandas as pd

try:
    import FinanceDataReader as fdr
except Exception as e:
    print(f"ERR: FinanceDataReader import failed: {e}")
    sys.exit(1)

try:
    import yfinance as yf
except Exception as e:
    print(f"ERR: yfinance import failed: {e}")
    sys.exit(1)


def get_kosdaq_codes(limit: int = 10) -> pd.Series:
    """Fetch KOSDAQ listing and return a series of 6-digit codes."""
    df = fdr.StockListing('KOSDAQ')
    cols = [c.lower() for c in df.columns]
    # Prefer 'Code' then 'Symbol'
    code_col = None
    for cand in ('code', 'symbol'):  # common FDR columns
        if cand in cols:
            code_col = df.columns[cols.index(cand)]
            break
    if code_col is None:
        raise RuntimeError(f"Cannot find code column in KOSDAQ listing. Columns={list(df.columns)}")
    codes = df[code_col].astype(str)
    # keep 6-digit numeric codes only
    codes = codes[codes.str.fullmatch(r"\d{6}") == True]
    return codes.head(limit)


def try_fdr(code: str, days: int = 365) -> int:
    start = datetime.now() - timedelta(days=days)
    end = datetime.now()
    try:
        df = fdr.DataReader(code, start, end)
        return int(len(df))
    except Exception:
        return -1


def try_yf(symbol: str, period: str = '1y') -> int:
    try:
        df = yf.Ticker(symbol).history(period=period)
        # yfinance sometimes returns an empty df with tz-aware index; just count rows
        return int(len(df))
    except Exception:
        return -1


def main():
    codes = get_kosdaq_codes(limit=12)
    rows = []
    for code in codes:
        # Test matrix
        r_fdr = try_fdr(code)
        # yfinance variants
        r_yf_no = try_yf(code)
        r_yf_kq = try_yf(f"{code}.KQ")
        r_yf_ks = try_yf(f"{code}.KS")

        rows.append({
            'code': code,
            'fdr_rows': r_fdr,
            'yf_no_suffix_rows': r_yf_no,
            'yf_KQ_rows': r_yf_kq,
            'yf_KS_rows': r_yf_ks,
        })
        # be gentle to avoid rate limiting
        time.sleep(0.2)

    out = pd.DataFrame(rows)
    # Success flags
    out['fdr_ok'] = out['fdr_rows'] > 0
    out['yf_no_ok'] = out['yf_no_suffix_rows'] > 0
    out['yf_KQ_ok'] = out['yf_KQ_rows'] > 0
    out['yf_KS_ok'] = out['yf_KS_rows'] > 0

    # Print detailed table
    print("=== Per-code results (rows count; -1 means error) ===")
    print(out.to_string(index=False))

    # Summary
    summary = {
        'sample_size': len(out),
        'fdr_success': int(out['fdr_ok'].sum()),
        'yf_no_suffix_success': int(out['yf_no_ok'].sum()),
        'yf_KQ_success': int(out['yf_KQ_ok'].sum()),
        'yf_KS_success': int(out['yf_KS_ok'].sum()),
    }
    print("\n=== Summary (success counts) ===")
    for k, v in summary.items():
        print(f"{k}: {v}")

    # Recommendation based on success rates
    # Prefer variant with higher success for KOSDAQ
    prefer = 'KQ' if summary['yf_KQ_success'] >= summary['yf_KS_success'] else 'KS'
    print(f"\nRecommendation: Prefer .{prefer} suffix first for KOSDAQ in yfinance.")


if __name__ == '__main__':
    main()


