"""Download the two pinned browser libraries once for offline use; no pip dependencies."""
from pathlib import Path
import hashlib
import urllib.request

DEST=Path(__file__).resolve().parents[1]/'vendor'
FILES={
 'plotly-2.35.2.min.js':'https://cdn.plot.ly/plotly-2.35.2.min.js',
 'geotiff-2.1.3.js':'https://cdn.jsdelivr.net/npm/geotiff@2.1.3/dist-browser/geotiff.js',
}
DEST.mkdir(exist_ok=True)
for name,url in FILES.items():
    with urllib.request.urlopen(url,timeout=60) as response:data=response.read()
    (DEST/name).write_bytes(data)
    print(name,len(data),'bytes',hashlib.sha256(data).hexdigest())
