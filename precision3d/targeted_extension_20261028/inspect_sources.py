"""按规划问题核验来源；先下载元数据，不把来源目录数量计为规划场景数量。"""
import hashlib,json,pathlib,sqlite3,urllib.request

ROOT=pathlib.Path(__file__).resolve().parent

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=60)

def save(name,d):
    p=ROOT/'source_evidence'/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    for name,url in [
        ('semantic_card.txt','https://huggingface.co/datasets/maxim0815/SemanticBridge/raw/main/README.md'),
        ('semantic_repository_license.txt','https://raw.githubusercontent.com/mvg-inatech/3d_bridge_segmentation/main/LICENSE'),
        ('fractal_card.txt','https://huggingface.co/datasets/IGNF/FRACTAL/raw/main/README.md')]:
        data=get(url).read();p=ROOT/'source_evidence'/name;p.parent.mkdir(exist_ok=True);p.write_bytes(data)
    meta=json.load(get('https://huggingface.co/api/datasets/IGNF/FRACTAL'))
    sha=meta['sha'];save('fractal_repository.json',dict(id=meta['id'],sha=sha,cardData=meta.get('cardData')))
    entries=json.load(get('https://huggingface.co/api/datasets/IGNF/FRACTAL/tree/'+sha+'?recursive=false&expand=false'))
    save('fractal_root_tree.json',entries);asset=next(e for e in entries if e['path']=='fractal.gpkg')
    url='https://huggingface.co/datasets/IGNF/FRACTAL/resolve/'+sha+'/fractal.gpkg'
    p=ROOT/'metadata'/'fractal.gpkg';p.parent.mkdir(exist_ok=True)
    if not p.exists():
        part=p.with_suffix('.gpkg.part')
        with get(url) as r,part.open('wb') as f:
            while b:=r.read(2**20):f.write(b)
        part.replace(p)
    actual=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();assert actual==asset['lfs']['oid'] and p.stat().st_size==asset['size']
    save('fractal_metadata_receipt.json',dict(url=url,repository_commit=sha,sha256=actual,official_lfs_sha256_verified=True,bytes=p.stat().st_size,kind='METADATA_ONLY_NOT_POINT_CLOUD_ACQUISITION'))
    db=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True)
    tables=db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
    for (name,) in tables:
        if name.startswith(('gpkg','rtree')):continue
        quoted='"'+name.replace('"','""')+'"'
        print('table',name,'columns',db.execute('pragma table_info('+quoted+')').fetchall(),flush=True)
        rows=db.execute('SELECT * FROM '+quoted+" WHERE split='train' LIMIT 1").fetchall()
        print('sample',[[str(v)[:180] if not isinstance(v,bytes) else '<geometry blob>' for v in row] for row in rows],flush=True)
    print('metadata hash PASS',actual,flush=True)

if __name__=='__main__':main()
