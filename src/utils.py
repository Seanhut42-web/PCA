import hashlib

REGIME_COLORS = {'Goldilocks':'#F4E3B1','Reflation':'#BFE8C6','Recession':'#D8C7E8','Stagflation':'#F3C5D3'}
RISK_COLORS = {True:'#C6EFCE', False:'#FFC7CE'}

def bytes_hash(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]

def file_hash(file) -> str:
    data = file.getvalue() if hasattr(file,'getvalue') else file.read()
    return bytes_hash(data)
