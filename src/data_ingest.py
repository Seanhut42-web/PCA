# data_ingest.py

import io
import pandas as pd

# ---------------------------
# Constants & simple helpers
# ---------------------------

DATE_NAMES = {'date', 'dates', 'month', 'asof', 'as_of'}
RET_NAME_ALIASES = {
    'HY'   : ['EMBI GD HY','EMBI_HY','HY','EMBIGD HY','EMBI HY'],
    'IG'   : ['EMBI GD IG','EMBI_IG','IG','EMBIGD IG','EMBI IG'],
    'EMBI' : ['EMBI','EMBI GD','EMBI Global Diversified','EMBIGD','EMBI GD Total']
}

def _detect_date_col(df: pd.DataFrame) -> str:
    """Return the column name that looks like date."""
    for c in df.columns:
        if str(c).strip().lower() in DATE_NAMES:
            return c
    return df.columns[0]

def _month_end_collapse(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """
    Set index to month-end and collapse duplicates within a month by 'last'.
    This is robust to daily/irregular dates while preserving monthly cadence.
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col])
    df = df.set_index(date_col).sort_index()
    # Normalize to month-end
    df.index = df.index.to_period('M').to_timestamp('M')
    return df.groupby(df.index).last()

def _coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce all columns to numeric (safe for already numeric)."""
    out = df.copy()
    for c in out.columns:
        out[c] = pd.to_numeric(out[c], errors='coerce')
    return out

def read_excel_bytes(xls_bytes: bytes) -> pd.ExcelFile:
    """Turn Streamlit's uploaded BytesIO into a pandas.ExcelFile."""
    return pd.ExcelFile(io.BytesIO(xls_bytes), engine='openpyxl')

def detect_sheets(xf: pd.ExcelFile):
    """Identify likely sheet names using flexible matching."""
    names = [str(s) for s in xf.sheet_names]
    lower_map = {str(s).strip().lower(): s for s in names}

    def find(cands):
        for key, val in lower_map.items():
            if key in cands:
                return val
        return None

    return {
        # Common variants for “raw variables”
        'raw': find({'inputs','raw','factors','variables','variables input','variables_input'}),
        # Z-Score tabs (include X-Scores alias)
        'x'  : find({'x-scores','x_scores','xscores'}),
        'z'  : find({'z-scores','z_scores','z','standardized'}),
        # Returns tab
        'ret': find({'returns','return','embi'})
    }

# ---------------------------
# Robust Z-Scores loader
# ---------------------------

def _find_header_row(xf: pd.ExcelFile, sheet: str, max_scan: int = 12) -> int:
    """
    Scan the first `max_scan` rows to locate a header row by looking
    for a row that contains 'Date'. Fallback to row 0 if none found.
    """
    peek = pd.read_excel(xf, sheet_name=sheet, header=None, nrows=max_scan, engine='openpyxl')
    for r in range(min(max_scan, len(peek))):
        vals = [str(v).strip().lower() for v in peek.iloc[r].tolist()]
        if 'date' in vals:
            return r
    return 0

def _load_z_or_x_scores(xf: pd.ExcelFile, drop_leading_zero_row: bool = True) -> pd.DataFrame:
    """
    Prefer X-Scores then Z-Scores. Auto-detect header row, normalize columns,
    coerce numerics, month-end index, and optionally drop a leading all-zero row.
    """
    sheets = detect_sheets(xf)
    sheet = sheets.get('x') or sheets.get('z')
    if not sheet:
        raise ValueError(
            "Could not find a sheet named 'X-Scores' or 'Z-Scores'. "
            f"Available: {list(xf.sheet_names)}"
        )

    header_row = _find_header_row(xf, sheet)
    df = pd.read_excel(xf, sheet_name=sheet, header=header_row, engine='openpyxl')

    # Normalize headers
    df.columns = [str(c).strip() for c in df.columns]

    # Identify/normalize date column
    date_col = _detect_date_col(df)

    # Remove completely empty columns and anything before first valid date
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col])

    # Keep non-empty columns only
    keep_cols = [date_col] + [c for c in df.columns if c != date_col and df[c].notna().any()]
    df = df[keep_cols]

    # Coerce non-date columns to numeric
    for c in df.columns:
        if c != date_col:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    # Collapse to month-end and sort
    df = _month_end_collapse(df, date_col)

    # Optionally drop a leading all-zero row (common on Z-score tabs)
    if drop_leading_zero_row and len(df):
        # Sum absolute values across factors (ignore NaNs)
        if df.iloc[0].fillna(0).abs().sum() == 0:
            df = df.iloc[1:].copy()

    return df

# ---------------------------
# Public API
# ---------------------------

def load_variables(xf: pd.ExcelFile, prefer_raw: bool = True, minp_z: int = 24) -> pd.DataFrame:
    """
    Load the factor matrix for PCA/regime modelling.

    Behavior:
      1) If an X-Scores or Z-Scores tab exists, use it (preferred).
      2) Else, if `prefer_raw` is True and a raw 'Variables/Inputs' tab exists,
         compute Z-scores by expanding mean/std (minp_z).
      3) Else, raise a clear error.
    """
    sheets = detect_sheets(xf)

    # 1) Prefer the provided X/Z scores (matches the workbook you shared)
    if sheets.get('x') or sheets.get('z'):
        return _load_z_or_x_scores(xf, drop_leading_zero_row=True)

    # 2) Fall back to computing Z from raw variables if explicitly allowed
    if prefer_raw and sheets['raw'] is not None:
        RAW = pd.read_excel(xf, sheet_name=sheets['raw'], engine='openpyxl')
        dc = _detect_date_col(RAW)
        RAW = _month_end_collapse(RAW, dc)
        RAW = _coerce_numeric(RAW).dropna(how='all', axis=1)
        RAW = RAW.dropna(how='any')  # ensure expanding stats behave well
        mu = RAW.expanding(min_periods=minp_z).mean()
        sd = RAW.expanding(min_periods=minp_z).std(ddof=0)
        Z = (RAW - mu) / sd
        Z = Z.dropna(how='any')
        return Z

    # 3) Nothing suitable found
    raise ValueError(
        "Workbook must contain 'X-Scores'/'Z-Scores' "
        "or a raw 'Variables/Inputs' sheet."
    )

def load_returns(xf: pd.ExcelFile) -> pd.DataFrame:
    """
    Load HY/IG/EMBI returns from the 'Returns' sheet. Keeps original logic but
    ignores empty/unnamed columns and is resilient to duplicated date blocks.
    """
    sheets = detect_sheets(xf)
    if sheets['ret'] is None:
        raise ValueError('Returns sheet not found.')

    R = pd.read_excel(xf, sheet_name=sheets['ret'], engine='openpyxl')

    # Drop obviously empty/unnamed helper columns
    R = R.loc[:, [c for c in R.columns
                  if not (str(c).startswith('Unnamed') and R[c].isna().all())]]

    # Find and normalize date column, collapse to ME
    dc = _detect_date_col(R)
    R = _month_end_collapse(R, dc)

    # Coerce numerics (levels + returns are mixed; NaNs allowed)
    R = _coerce_numeric(R).dropna(how='all', axis=1)

    # Build alias map (prefer columns that actually exist)
    name_map, up = {}, {str(c).upper(): c for c in R.columns}
    for k, aliases in RET_NAME_ALIASES.items():
        for a in aliases:
            if a.upper() in up:
                name_map[k] = up[a.upper()]
                break

    # Fallback to positional indexes if aliases not found (kept from original)
    def col(df, i):
        return df.columns[i] if i < len(df.columns) else None
    if 'HY' not in name_map:   name_map['HY']   = col(R, 7)
    if 'IG' not in name_map:   name_map['IG']   = col(R, 8)
    if 'EMBI' not in name_map: name_map['EMBI'] = col(R, 11)

    out = R[[name_map['HY'], name_map['IG'], name_map['EMBI']]].copy()
    out.columns = ['HY', 'IG', 'EMBI']
    return out