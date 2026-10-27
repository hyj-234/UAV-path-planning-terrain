"""Optional full-footprint JSON export: pip install numpy rasterio. No source window is selected."""
from argparse import ArgumentParser
from pathlib import Path
import json
import numpy as np
import rasterio
from rasterio.enums import Resampling

p=ArgumentParser(description=__doc__)
p.add_argument('source');p.add_argument('output',type=Path);p.add_argument('--max-side',type=int,default=600)
a=p.parse_args()
if not 2<=a.max_side<=2000:p.error('--max-side must be between 2 and 2000')
with rasterio.open(a.source) as s:
    scale=min(1,a.max_side/max(s.width,s.height));w=max(2,round(s.width*scale));h=max(2,round(s.height*scale))
    z=s.read(1,out_shape=(h,w),masked=True,resampling=Resampling.nearest).astype('float64').filled(np.nan)
    b=s.bounds;dx=(b.right-b.left)/w;dy=(b.top-b.bottom)/h
    d=dict(title=Path(a.source).name,source=a.source,scope='Source-file full footprint; display downsampling only.',x=[b.left+(i+.5)*dx for i in range(w)],y=[b.top-(j+.5)*dy for j in range(h)],z=[[float(v) if np.isfinite(v) and abs(v)<1e10 else None for v in row] for row in z],metadata=dict(native_shape=[s.height,s.width],bounds=list(b),crs=str(s.crs),window_crop=False))
a.output.parent.mkdir(parents=True,exist_ok=True)
with a.output.open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,allow_nan=False,separators=(',',':'))
print(a.output)
