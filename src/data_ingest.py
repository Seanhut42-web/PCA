# data_ingest.py
import io
import pandas as pd

# ---------------------------
# Constants & simple helpers
# ---------------------------
DATE_NAMES = {'date', 'dates', 'month', 'asof', 'as_of'}

def _detect_date_col(df: pd.DataFrame) -> str:
    """Return the column name that looks like date."""
    for c in df.columns:
        if str(c).strip().lower() in DATE_NAMES:
            return c
    return df.columns[0]

def _month_end_collapse(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """
    Set index to month-end and collapse duplicates within a month by 'last'.
    Robust to daily/irregular dates while preserving monthly cadence.
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col])
    df = df.set_index(date_col).sort_index()
    # Normalize to month-end stamps
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
        'x' : find({'x-scores','x_scores','xscores'}),
        'z' : find({'z-scores','z_scores','z','standardized'}),
        # Returns tab
        'ret': find({'returns','return','embi'})
    }

# ---------------------------
# Z / X scores loader
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
        # Coerce numerics and remove incomplete rows so expanding stats behave well
        RAW = _coerce_numeric(RAW).dropna(how='all', axis=1)
        RAW = RAW.dropna(how='any')

        mu = RAW.expanding(min_periods=minp_z).mean()
        sd = RAW.expanding(min_periods=minp_z).std(ddof=0)
        Z = (RAW - mu) / sd
        Z = Z.dropna(how='any')
        return Z

    # 3) Nothing suitable found
    raise ValueError(
        "Workbook must contain 'X-Scores'/'Z-Scores' or a raw 'Variables/Inputs' sheet."
    )

def load_returns(xf: pd.ExcelFile) -> pd.DataFrame:
    """
    Load HY/IG/EMBI *monthly returns* from the 'Returns' sheet.
    **Prefers the .1 columns**: 'EMBI GD HY.1', 'EMBI GD IG.1', 'EMBI GD.1'.
    Falls back to endswith('.1') detection, then to fixed positions (H/J/K ~ 7/9/11).
    """
    sheets = detect_sheets(xf)
    if sheets['ret'] is None:
        raise ValueError('Returns sheet not found.')

    R = pd.read_excel(xf, sheet_name=sheets['ret'], engine='openpyxl')
    R.columns = [str(c).strip() for c in R.columns]

    # Use the first/leftmost Date-like column as the master date
    dc = _detect_date_col(R)
    R = _month_end_collapse(R, dc)

    # Drop columns that are entirely NaN (duplicate Date columns become NaN after coercion)
    drop_cols = [c for c in R.columns if R[c].isna().all()]
    if drop_cols:
        R = R.drop(columns=drop_cols)

    # 1) Prefer explicit monthly return columns with '.1' suffix
    preferred = {
        'EMBI GD HY.1': 'EMBI GD HY',
        'EMBI GD IG.1': 'EMBI GD IG',
        'EMBI GD.1'  : 'EMBI GD',
    }
    have_pref = [k for k in preferred if k in R.columns]
    if len(have_pref) == 3:
        out = R[have_pref].rename(columns=preferred)
    else:
        # 2) Generic endswith('.1') detection for the three series
        base_map = {}
        for c in R.columns:
            if c.endswith('.1'):
                base = c[:-2]
                if base in ['EMBI GD HY', 'EMBI GD IG', 'EMBI GD']:
                    base_map[base] = c
        if len(base_map) == 3:
            out = R[[base_map['EMBI GD HY'], base_map['EMBI GD IG'], base_map['EMBI GD']]].copy()
            out.columns = ['EMBI GD HY','EMBI GD IG','EMBI GD']
        else:
            # 3) Final positional fallback: columns H, J, K ≈ indices 7, 9, 11 (0-based)
            idxs = [7, 9, 11]
            cols = [R.columns[i] for i in idxs if i < len(R.columns)]
            if len(cols) != 3:
                raise ValueError(
                    f"Could not robustly locate monthly return columns. Columns: {list(R.columns)}"
                )
            out = R[cols].copy()
            out.columns = ['EMBI GD HY','EMBI GD IG','EMBI GD']

    # Coerce to numeric returns
    for c in out.columns:
        out[c] = pd.to_numeric(out[c], errors='coerce')

    # Basic magnitude sanity-check (monthly returns should be small)
    if (out.abs() > 2).any().any():
        raise ValueError(
            "Monthly return magnitudes look wrong—likely read levels instead of returns."
        )

    return out