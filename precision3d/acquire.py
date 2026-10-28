"""完整官方生产瓦片：保存 STAC 原证据，并按官方 multihash 校验；不裁剪原件。"""
import concurrent.futures, hashlib, json, pathlib, time, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
BASE = 'https://data.geo.admin.ch/api/stac/v1/collections/'
SOURCES = [
    ('ch.swisstopo.swisssurface3d', 'swisssurface3d_2024_2681-1248', '.copc.laz'),
    ('ch.swisstopo.swisssurface3d', 'swisssurface3d_2024_2681-1249', '.copc.laz'),
    ('ch.swisstopo.swissbuildings3d_3_0', 'swissbuildings3d_3_0_2019_1091-23', '.citygml.zip'),
]

def write_json(p, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')

def fetch(source):
    col, item, suffix = source
    url = BASE + col + '/items/' + item
    d = json.load(urllib.request.urlopen(url, timeout=60))
    write_json(ROOT / 'source_evidence' / (item + '.json'), d)
    name, a = next((n, a) for n, a in d['assets'].items() if n.endswith(suffix))
    expected = a.get('checksum:multihash', a.get('file:checksum', ''))
    if not expected:
        # STAC 的扩展字段以实际返回为准；不把本地散列冒充官方散列。
        expected = next((str(v) for k, v in a.items() if 'checksum' in k), '')
    p = ROOT / 'raw' / name
    p.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    if not p.exists():
        part = p.with_suffix(p.suffix + '.part')
        with urllib.request.urlopen(a['href'], timeout=120) as r, part.open('wb') as f:
            while block := r.read(2**20): f.write(block)
        part.replace(p)
    sha = hashlib.file_digest(p.open('rb'), 'sha256').hexdigest()
    if expected:
        assert expected.lower() == '1220' + sha, (name, expected, sha)
    row = dict(item=item, collection=col, asset_url=a['href'], stac_url=url,
        path=str(p), bytes=p.stat().st_size, sha256=sha, official_multihash=expected,
        official_hash_verified=bool(expected), elapsed_s=time.perf_counter()-t0,
        nominal_datetime=d['properties'].get('datetime'), crs='EPSG:2056 + EPSG:5728',
        license='swisstopo OGD terms; attribution required; not relicensed as CC BY',
        attribution='Source: Federal Office of Topography swisstopo',
        qualification='SOURCE_VERIFIED_GEOMETRY_QA_PENDING')
    write_json(ROOT / 'receipts' / (item + '.json'), row)
    print(json.dumps(row), flush=True)
    return row

if __name__ == '__main__':
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for f in concurrent.futures.as_completed([pool.submit(fetch, s) for s in SOURCES]):
            try: results.append(f.result())
            except Exception as e: results.append({'error':repr(e)})
    write_json(ROOT / 'source_manifest.json', results)
    if any('error' in r for r in results): raise SystemExit(1)
