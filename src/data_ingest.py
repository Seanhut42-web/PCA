import io
import pandas as pd

DATE_NAMES = {'date','dates','month','asof','as_of'}
RET_NAME_ALIASES = {
    'HY': ['EMBI GD HY','EMBI_HY','HY','EMBIGD HY','EMBI HY'],
    'IG': ['EMBI GD IG','EMBI_IG','IG','EMBIGD IG','EMBI IG'],
    'EMBI': ['EMBI','EMBI GD','EMBI Global Diversified','EMBIGD','EMBI GD Total']
}

def _detect_date_col(df: pd.DataFrame) -> str:
    for c in df.columns:
        if str(c).strip().lower() in DATE_NAMES:
            return c
    return df.columns[0]

def _month_end_collapse(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    df = df.copy(); df[date_col] = pd.to_datetime(df[date_col]); df = df.set_index(date_col).sort_index()
    df.index = df.index.to_period('M').to_timestamp('M')
    return df.groupby(df.index).last()

def _coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in out.columns: out[c] = pd.to_numeric(out[c], errors='coerce')
    return out

def read_excel_bytes(xls_bytes: bytes) -> pd.ExcelFile:
    return pd.ExcelFile(io.BytesIO(xls_bytes))

def detect_sheets(xf: pd.ExcelFile):
    names = [str(s) for s in xf.sheet_names]
    def find(cands):
        for s in names:
            if str(s).lower() in cands: return s
        return None
    return {
        'raw': find({'inputs','raw','factors','variables','variables input','variables_input'}),
        'z':   find({'z-scores','z_scores','z','standardized'}),
        'ret': find({'returns','return','embi'})
    }

def load_variables(xf: pd.ExcelFile, prefer_raw=True, minp_z=24) -> pd.DataFrame:
    sheets = detect_sheets(xf)
    if prefer_raw and sheets['raw'] is not None:
        RAW = pd.read_excel(xf, sheet_name=sheets['raw'], engine='openpyxl')
        dc = _detect_date_col(RAW)
        RAW = _month_end_collapse(RAW, dc)
        RAW = _coerce_numeric(RAW).dropna(how='all', axis=1)
        RAW = RAW.dropna(how='any')
        mu = RAW.expanding(min_periods=minp_z).mean(); sd = RAW.expanding(min_periods=minp_z).std(ddof=0)
        Z = (RAW - mu)/sd
        return Z.dropna(how='any')
    elif sheets['z'] is not None:
        Z_raw = pd.read_excel(xf, sheet_name=sheets['z'], engine='openpyxl')
        dc = _detect_date_col(Z_raw)
        Z = _month_end_collapse(Z_raw, dc)
        Z = _coerce_numeric(Z).dropna(how='all', axis=1)
        return Z.dropna(how='any') if Z.isna().any().any() else Z
    else:
        raise ValueError("Workbook must contain an 'Inputs'/'Variables' or a 'Z-Scores' sheet.")

def load_returns(xf: pd.ExcelFile) -> pd.DataFrame:
    sheets = detect_sheets(xf)
    if sheets['ret'] is None: raise ValueError('Returns sheet not found.')
    R = pd.read_excel(xf, sheet_name=sheets['ret'], engine='openpyxl')
    dc = _detect_date_col(R)
    R = _month_end_collapse(R, dc)
    R = _coerce_numeric(R).dropna(how='all', axis=1)
    name_map, up = {}, {str(c).upper(): c for c in R.columns}
    for k, aliases in RET_NAME_ALIASES.items():
        for a in aliases:
            if a.upper() in up: name_map[k] = up[a.upper()]; break
    def col(df, i): return df.columns[i] if i < len(df.columns) else None
    if 'HY' not in name_map: name_map['HY'] = col(R,7)
    if 'IG' not in name_map: name_map['IG'] = col(R,8)
    if 'EMBI' not in name_map: name_map['EMBI'] = col(R,11)
    out = R[[name_map['HY'], name_map['IG'], name_map['EMBI']]].copy(); out.columns=['HY','IG','EMBI']
    return out
