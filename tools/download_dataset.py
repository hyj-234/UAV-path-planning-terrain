"""Download complete native products and verify recorded SHA256: fine|global OUTPUT_DIRECTORY."""
from pathlib import Path
import argparse,json,hashlib,urllib.request

p=argparse.ArgumentParser(description=__doc__);p.add_argument('subset',choices=['fine','global']);p.add_argument('output',type=Path);a=p.parse_args()
root=Path(__file__).resolve().parents[1];manifest=json.loads((root/'dataset'/(a.subset+'_source_manifest.json')).read_text('utf-8'))
a.output.mkdir(parents=True,exist_ok=True)
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
for row in manifest['rows']:
 path=a.output/row['local_raster'];path.parent.mkdir(parents=True,exist_ok=True)
 if not path.exists():
  url=row['source']['asset']['href'] if a.subset=='fine' else row['url']
  part=path.with_suffix('.part')
  with urllib.request.urlopen(url,timeout=90) as response,part.open('wb') as f:
   for block in iter(lambda:response.read(1048576),b''):f.write(block)
  if digest(part)!=row['sha256']:raise ValueError('SHA256 mismatch: '+str(part))
  part.replace(path)
 if digest(path)!=row['sha256']:raise ValueError('Existing file changed: '+str(path))
 print(row['id'],'verified',flush=True)
(a.output/'dataset_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),'utf-8')
