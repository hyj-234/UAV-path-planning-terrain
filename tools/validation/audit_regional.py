"""Straight regional reference checks on native GLO30 pixels; not precision navigation."""
from pathlib import Path
from collections import Counter
import json,math,sys
import numpy as np
import rasterio
from rasterio.windows import Window
if len(sys.argv)!=2:raise SystemExit('Usage: audit_regional.py GLOBAL_DATASET_ROOT')
ROOT=Path(sys.argv[1]).resolve()
def duration(L,v,a):
 if L==0:return 0.
 ta=min(v/a,math.sqrt(L/a));return 2*ta+max(0.,(L-a*ta*ta)/(a*ta))
def main():
 assert duration(0,5,1)==0 and abs(duration(100,10,2)-15)<1e-10
 rows=json.loads((ROOT/'dataset_manifest.json').read_text())['rows'];out=[]
 for row in rows:
  if row['resolution']!=30:continue
  with rasterio.open(ROOT/row['local_raster']) as s:
   c0=int(s.width*.2);c1=int(s.width*.8)
   for task,fraction in enumerate([.25,.5,.75]):
    r=int(s.height*fraction);a=s.read(1,window=Window(c0-1,r-1,c1-c0+3,3),masked=True).astype('float64').filled(np.nan)
    result=dict(site_id=row['site_id'],task=task,source_sha256=row['sha256'],representation_only=True,real_flight_certified=False)
    if not np.isfinite(a).all():result['status']='UNKNOWN_NODATA'
    else:
     peak=float(a.max());low=float(a.min());z=peak+60.;aglmax=z-low
     if aglmax>1000:result.update(status='STRAIGHT_REFERENCE_EXCEEDS_DECLARED_AGL_CEILING',maximum_AGL_m=aglmax)
     else:
      lat=s.transform.f+(r+.5)*s.transform.e;length=(c1-c0)*s.res[0]*111320*math.cos(math.radians(lat));h1=peak-float(a[1,1]);h2=peak-float(a[1,-2])
      result.update(status='REGIONAL_REPRESENTED_SURFACE_REFERENCE_PASS',reference_length_m=length+h1+h2,analytic_profile_duration_s=duration(length,30,2)+duration(h1,5,1)+duration(h2,5,1),minimum_native_clearance_m=60.,maximum_AGL_m=aglmax,assumptions='Rest-to-rest vertical climb, straight level transit, vertical descent. Surface-based 60m margin, 1000m AGL ceiling, no traffic/wind/airspace or tracking error. Horizontal distances use latitude-local approximation, not navigation coordinates.')
    out.append(result)
 j=dict(declared_tasks=204,accounted_tasks=len(out),statuses=dict(Counter(r['status'] for r in out)),resolution_role='Regional representation diagnostics only; GLO90 is related lower-resolution context and is not independently flight-tested',results=out)
 (ROOT/'planning_audit').mkdir(exist_ok=True)
 (ROOT/'planning_audit/regional_summary.json').write_text(json.dumps(j,indent=2),'utf-8');print(j['statuses'])
if __name__=='__main__':main()
