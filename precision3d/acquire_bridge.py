"""原始桥梁 TLS 与作者处理版本；同一采集不计为三个独立场景。"""
import concurrent.futures, hashlib, json, time, urllib.request
from acquire import ROOT, write_json

def run(f):
    a=f['content_details'];p=ROOT/'raw'/f['filename'];t=time.perf_counter()
    if not p.exists():
        part=p.with_suffix('.pcd.part')
        req=urllib.request.Request(a['download_url'],headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=120) as r,part.open('wb') as out:
            while b:=r.read(2**20):out.write(b)
        part.replace(p)
    sha=hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
    assert sha==a['sha256_hash'] and p.stat().st_size==a['size']
    row=dict(filename=f['filename'],path=str(p),bytes=p.stat().st_size,sha256=sha,
        official_hash_verified=True,license='CC BY 4.0',doi='10.17632/znxxsgn2ky.2',
        source_url='https://data.mendeley.com/datasets/znxxsgn2ky/2',download_url=a['download_url'],
        attribution='Yunping Fang, Jelena Ninic, Stergios Mitoulis, Daniel Boddice, Jialiang Yu (2025)',
        independent_acquisition_group='birmingham_aqueduct_tls',elapsed_s=time.perf_counter()-t,
        qualification='SOURCE_VERIFIED; COORDINATES_AND_VISIBILITY_QA_PENDING')
    write_json(ROOT/'receipts'/(f['filename']+'.json'),row);print(json.dumps(row),flush=True)
    return row

if __name__=='__main__':
    d=json.loads((ROOT/'source_evidence'/'aqueduct_metadata.json').read_text(encoding='utf-8'))
    assert d['id']=='znxxsgn2ky' and d['version']==2
    print('source license',d['data_licence'],flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:r=list(ex.map(run,d['files']))
    write_json(ROOT/'bridge_source_manifest.json',r)
