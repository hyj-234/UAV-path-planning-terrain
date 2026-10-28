"""Conditional single-UAV static 2.5D planning audit, not a real-flight safety certificate."""
from pathlib import Path
from collections import Counter
import hashlib,heapq,json,math,time,sys
import numpy as np
import rasterio
from scipy.ndimage import maximum_filter,minimum_filter

if len(sys.argv)!=3:raise SystemExit('Usage: audit_planning.py FINE_DATASET_ROOT OUTPUT_ROOT')
OLD=Path(sys.argv[1]).resolve()
ROOT=Path(sys.argv[2]).resolve()
ROOT.mkdir(parents=True,exist_ok=True)
CONFIG=dict(clearance_m=10.,max_AGL_m=120.,horizontal_grid_m=8.,vertical_grid_m=5.,vehicle_radius_m=2.,vmax_mps=10.,vertical_vmax_mps=2.,amax_mps2=2.,sample_dt_s=.2,max_expansions=50000,
 model='Point mass with rest-to-rest trapezoidal segments; no wind, tracking controller, attitude, jerk, moving traffic, team conflicts or overhangs',intended_use='Conditional static simulation reference feasibility only')

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def envelopes(a,res):
 factor=max(1,math.ceil(CONFIG['horizontal_grid_m']/res));radius=math.ceil(CONFIG['vehicle_radius_m']/res);n=2*radius+1
 hi=maximum_filter(np.where(np.isfinite(a),a,np.inf),size=n,mode='constant',cval=np.inf)
 lo=minimum_filter(np.where(np.isfinite(a),a,-np.inf),size=n,mode='constant',cval=-np.inf)
 nr,nc=math.ceil(a.shape[0]/factor),math.ceil(a.shape[1]/factor)
 ph=np.full((nr*factor,nc*factor),np.inf);pl=np.full_like(ph,-np.inf);ph[:a.shape[0],:a.shape[1]]=hi;pl[:a.shape[0],:a.shape[1]]=lo
 hi=ph.reshape(nr,factor,nc,factor).max(axis=(1,3));lo=pl.reshape(nr,factor,nc,factor).min(axis=(1,3))
 return hi,lo,factor*res,factor

def search(hi,lo,spacing,startxy,goalxy):
 valid=np.isfinite(hi)&np.isfinite(lo)
 if not valid.any():return None,'NO_VALID_SPACE',0,None
 z0=math.floor(float(np.min(lo[valid]))/5)*5
 low=np.full(hi.shape,1,dtype=int);high=np.zeros_like(low)
 low[valid]=np.ceil((hi[valid]+10-z0)/5).astype(int);high[valid]=np.floor((lo[valid]+120-z0)/5).astype(int)
 start=(*startxy,int(low[startxy])+1);goal=(*goalxy,int(low[goalxy])+1)
 def allowed(q):r,c,k=q;return 0<=r<hi.shape[0] and 0<=c<hi.shape[1] and low[r,c]<=k<=high[r,c]
 if not allowed(start) or not allowed(goal):return None,'ENDPOINT_NODATA_OR_ALTITUDE_LIMIT',0,z0
 def heuristic(q):return (abs(q[0]-goal[0])+abs(q[1]-goal[1]))*spacing/10+abs(q[2]-goal[2])*5/2
 queue=[(heuristic(start),0.,start)];cost={start:0.};parent={};expanded=0
 while queue and expanded<CONFIG['max_expansions']:
  _,g,q=heapq.heappop(queue)
  if g!=cost.get(q):continue
  if q==goal:
   path=[q]
   while q!=start:q=parent[q];path.append(q)
   return path[::-1],'REFERENCE_FOUND',expanded,z0
  expanded+=1
  for dr,dc,dk in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
   v=q[0]+dr,q[1]+dc,q[2]+dk
   if not allowed(v):continue
   ng=g+(5/2 if dk else spacing/10)
   if ng<cost.get(v,math.inf):cost[v]=ng;parent[v]=q;heapq.heappush(queue,(ng+heuristic(v),ng,v))
 return None,'SEARCH_RESOURCE_LIMIT' if queue else 'NO_PATH_IN_DECLARED_LATTICE',expanded,z0

def verify_native(path,a,factor,res,z0):
 xyz=np.array([[(c+.5)*factor*res,(r+.5)*factor*res,z0+k*5] for r,c,k in path])
 # Merge only collinear points, preserving the exact 6-connected reference geometry.
 keep=[0]
 for i in range(1,len(xyz)-1):
  if np.linalg.norm(np.cross(xyz[i]-xyz[i-1],xyz[i+1]-xyz[i]))>1e-8:keep.append(i)
 keep.append(len(xyz)-1);xyz=xyz[keep]
 duration=0.;length=0.;samples=0;minimum=math.inf;radius=math.ceil(2/res)
 for p,q in zip(xyz[:-1],xyz[1:]):
  L=float(np.linalg.norm(q-p));direction=(q-p)/L;limit=min(10.,2/max(abs(direction[2]),1e-12));ta=min(limit/2,math.sqrt(L/2));T=2*ta+max(0.,(L-2*ta*ta)/(2*ta))
  t=np.r_[np.arange(0,T,.2),T];distance=np.where(t<ta,t*t,np.where(t>T-ta,L-(T-t)**2,ta*ta+2*ta*(t-ta)));positions=p+distance[:,None]*direction
  velocity=np.minimum(np.minimum(2*t,2*(T-t)),2*ta)[:,None]*direction
  assert np.max(np.linalg.norm(velocity,axis=1))<=10+1e-8 and np.max(np.abs(velocity[:,2]))<=2+1e-8
  # Independent conservative check against every native pixel in the segment's
  # horizontal footprint, including vehicle radius. No preview pixels are used.
  c0=max(0,int(min(p[0],q[0])/res)-radius);c1=min(a.shape[1],int(max(p[0],q[0])/res)+radius+1)
  r0=max(0,int(min(p[1],q[1])/res)-radius);r1=min(a.shape[0],int(max(p[1],q[1])/res)+radius+1)
  native=a[r0:r1,c0:c1]
  if not np.isfinite(native).all():return dict(status='NATIVE_AUDIT_UNKNOWN_NODATA')
  margin=min(p[2],q[2])-float(native.max());minimum=min(minimum,margin)
  if margin<10-1e-7 or max(p[2],q[2])-float(native.min())>120+1e-7:return dict(status='NATIVE_CLEARANCE_OR_CEILING_FAILURE')
  length+=L;duration+=T;samples+=len(t)
 return dict(status='CONDITIONAL_STATIC_REFERENCE_AND_POINT_MASS_PROFILE_PASS',path_length_m=length,duration_s=duration,profile_samples=samples,minimum_native_clearance_m=minimum,waypoints=xyz.tolist(),continuous_native_segment_bounds_checked=True,amax_bound_mps2=2.,real_flight_certified=False)

def self_check():
 a=np.zeros((64,64));hi,lo,spacing,factor=envelopes(a,1.)
 path,status,_,z0=search(hi,lo,spacing,(2,2),(5,5));assert path and verify_native(path,a,factor,1.,z0)['status'].endswith('_PASS')
 a[:,32:40]=500;hi,lo,spacing,factor=envelopes(a,1.);path,status,_,_=search(hi,lo,spacing,(2,2),(5,5));assert path is None
 a[:]=0;a[:,32:40]=np.nan;hi,lo,spacing,factor=envelopes(a,1.);assert search(hi,lo,spacing,(2,2),(5,5))[0] is None
 print('SYNTHETIC_FLAT_CLIFF_NODATA_CHECK_PASS',flush=True)

def main():
 self_check();rows=json.loads((OLD/'dataset_manifest.json').read_text('utf-8'))['rows'];results=[]
 (ROOT/'planning_audit').mkdir(exist_ok=True)
 (ROOT/'planning_audit/protocol.json').write_text(json.dumps(CONFIG,indent=2),'utf-8')
 for row in rows:
  out=ROOT/'planning_audit'/(row['id']+'.json')
  if out.exists():results.extend(json.loads(out.read_text('utf-8')));continue
  file=OLD/row['local_raster'];assert sha(file)==row['sha256']==row['source']['asset']['file:checksum'][4:].lower()
  with rasterio.open(file) as s:a=s.read(1,masked=True).astype('float64').filled(np.nan);res=float(s.res[0])
  hi,lo,spacing,factor=envelopes(a,res);nr,nc=hi.shape;tasks=[]
  for i,(s,g) in enumerate([((.5,.15),(.5,.85)),((.15,.5),(.85,.5)),((.15,.15),(.85,.85))]):
   start=tuple(int(v*n) for v,n in zip(s,(nr,nc)));goal=tuple(int(v*n) for v,n in zip(g,(nr,nc)))
   t=time.perf_counter();path,status,expanded,z0=search(hi,lo,spacing,start,goal)
   result=verify_native(path,a,factor,res,z0) if path else dict(status=status)
   tasks.append(dict(id=row['id'],task=i,scene=row['scene_context'],surface_kind=row['surface_kind'],source_sha256=row['sha256'],expansions=expanded,wall_seconds=time.perf_counter()-t,**result))
  out.write_text(json.dumps(tasks,indent=2),'utf-8');results.extend(tasks);print('AUDIT',row['id'],[r['status'] for r in tasks],flush=True)
 summary=dict(high_resolution_declared_tasks=192,accounted_tasks=len(results),statuses=dict(Counter(r['status'] for r in results)),passed=sum(r['status'].endswith('_PASS') for r in results),task_success_is_not_real_flight_safety=True,scope=CONFIG,regional_low_altitude_detail_qualification='REJECTED: 30/90m DSM cannot resolve precision low-altitude clearances or building gaps',results=results)
 (ROOT/'planning_audit/summary.json').write_text(json.dumps(summary,indent=2),'utf-8');print('PLANNING_SUMMARY',summary['statuses'],flush=True)
if __name__=='__main__':main()
