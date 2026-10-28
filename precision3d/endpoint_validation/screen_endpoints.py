"""真实COPC端点的可复核几何初筛。完整瓦片不变；无回波不被认证为自由。

固定均匀网格先登记，再检查原始点；数值阈值是可修改的开发假设。
仅输出候选或已观测的排除理由，不输出实机起降认证。
"""
import hashlib,json,math,pathlib,time
import numpy as np
from laspy.copc import Bounds,CopcReader

ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT.parent
CONFIG=dict(body_radius_m=.30,map_margin_m=.20,tracking_margin_m=.15,
    pad_radius_m=2.,coverage_cell_m=.5,min_ground_points=80,min_ground_coverage_fraction=.90,
    max_slope_deg=5.,max_plane_rms_m=.10,max_plane_residual_p95_m=.20,
    hover_agl_m=8.,support_to_airborne_agl_m=1.,
    note='Illustrative screening thresholds, not aircraft specifications or real-flight safety limits')

def screen(xyz,classes,xy,cfg):
    r=cfg['body_radius_m']+cfg['map_margin_m']+cfg['tracking_margin_m']
    dxy=xyz[:,:2]-xy;rad=np.linalg.norm(dxy,axis=1)
    finite=np.isfinite(xyz).all(axis=1);ground=xyz[finite&(classes==2)&(rad<=cfg['pad_radius_m'])]
    row=dict(xy_lv95_m=xy.tolist(),queried_points=len(xyz),ground_points=len(ground),
        final_takeoff_status='UNQUALIFIED',final_hover_status='UNQUALIFIED',final_landing_status='UNQUALIFIED',
        missing_evidence=['verified free-space visibility','surface material and bearing capacity','traffic and transient obstacles','current-condition verification','vehicle-specific landing/contact and tracking limits'])
    if len(ground)<cfg['min_ground_points']:
        row.update(geometric_screen='INSUFFICIENT_GROUND_EVIDENCE',exclusion_reasons=['GROUND_POINT_COUNT']);return row
    local=ground[:,:2]-xy;design=np.column_stack((local,np.ones(len(local))))
    coef,_,rank,_=np.linalg.lstsq(design,ground[:,2],rcond=None)
    if rank<3:
        row.update(geometric_screen='INSUFFICIENT_GROUND_EVIDENCE',exclusion_reasons=['DEGENERATE_PLANE']);return row
    residual=ground[:,2]-design@coef;slope=float(np.degrees(np.arctan(np.linalg.norm(coef[:2]))));rms=float(np.sqrt(np.mean(residual**2)));p95=float(np.quantile(np.abs(residual),.95));z=float(coef[2])
    pad=cfg['pad_radius_m'];cell=cfg['coverage_cell_m'];n=round(2*pad/cell)
    expected={(i,j) for i in range(n) for j in range(n) if (-pad+(i+.5)*cell)**2+(-pad+(j+.5)*cell)**2<=pad**2}
    observed=set(map(tuple,np.floor((local+pad)/cell).astype(int)));coverage=len(expected&observed)/len(expected)
    delta_z=xyz[:,2]-(dxy@coef[:2]+z);other=finite&(classes!=2)
    pad_obstacles=int(np.count_nonzero(other&(rad<=pad)&(delta_z>.10)&(delta_z<1.5)))
    water=int(np.count_nonzero(finite&(classes==9)&(rad<=pad)))
    corridor=int(np.count_nonzero(other&(rad<=r)&(xyz[:,2]>=z+cfg['support_to_airborne_agl_m']-r)&(xyz[:,2]<=z+cfg['hover_agl_m']+r)))
    hover=np.array([xy[0],xy[1],z+cfg['hover_agl_m']]);hover_obstacles=int(np.count_nonzero(finite&(np.linalg.norm(xyz-hover,axis=1)<=r)))
    reasons=[]
    for flag,name in [(coverage<cfg['min_ground_coverage_fraction'],'GROUND_COVERAGE'),(slope>cfg['max_slope_deg'],'SLOPE'),(rms>cfg['max_plane_rms_m'],'ROUGHNESS_RMS'),(p95>cfg['max_plane_residual_p95_m'],'ROUGHNESS_P95'),(pad_obstacles>0,'OBSERVED_PAD_OBSTACLE'),(water>0,'WATER_OBSERVATIONS')]:
        if flag:reasons.append(name)
    pad_pass=not reasons;corridor_pass=corridor==0;hover_pass=hover_obstacles==0
    row.update(ground_contact_reference_lv95_ln02_m=[float(xy[0]),float(xy[1]),z],
        airborne_departure_reference_lv95_ln02_m=[float(xy[0]),float(xy[1]),z+cfg['support_to_airborne_agl_m']],
        hover_reference_lv95_ln02_m=hover.tolist(),plane_coefficients_local_xy=coef.tolist(),slope_deg=slope,
        ground_plane_rms_m=rms,ground_plane_abs_residual_p95_m=p95,ground_coverage_fraction=coverage,
        pad_nonground_observations=pad_obstacles,water_observations=water,corridor_obstacle_observations=corridor,
        hover_obstacle_observations=hover_obstacles,pad_geometry_pass=pad_pass,
        departure_arrival_corridor_geometry_pass=corridor_pass,hover_observation_screen_pass=hover_pass,
        geometric_screen='GEOMETRY_CANDIDATE_ONLY' if pad_pass and corridor_pass and hover_pass else 'EXCLUDED_BY_OBSERVATIONS_OR_COVERAGE',
        exclusion_reasons=reasons+([] if corridor_pass else ['OBSERVED_VERTICAL_CORRIDOR_OBSTACLE'])+([] if hover_pass else ['OBSERVED_HOVER_OBSTACLE']),
        caution='No obstacle observation is not proof of free space. Ground contact reference is not airborne vehicle center.')
    return row

def main():
    ROOT.mkdir(exist_ok=True);manifest=json.loads((DATA/'source_manifest.json').read_text(encoding='utf-8'))
    sources=sorted([r for r in manifest if r['path'].endswith('.copc.laz')],key=lambda r:r['path'])
    sites=[]
    for source in sources:
        with pathlib.Path(source['path']).open('rb') as f:
            if hashlib.file_digest(f,'sha256').hexdigest()!=source['sha256']:raise ValueError('Source hash mismatch')
        with CopcReader.open(source['path']) as reader:
            low=reader.header.mins;high=reader.header.maxs
            for x in (125,375,625,875):
                for y in (125,375,625,875):sites.append(dict(source=source,xy=[float(low[0]+x),float(low[1]+y)],zrange=[float(low[2]-1),float(high[2]+1)]))
    plan=dict(config=CONFIG,candidates=[dict(source_sha256=s['source']['sha256'],xy=s['xy']) for s in sites],selection='Fixed 4x4 lattice per complete official tile; not selected using flight outcomes')
    (ROOT/'screening_plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    results=[];start=time.perf_counter()
    for source in sources:
        with CopcReader.open(source['path']) as reader:
            for s in [s for s in sites if s['source']==source]:
                xy=np.asarray(s['xy']);q=CONFIG['pad_radius_m']+.5
                b=Bounds(np.array([xy[0]-q,xy[1]-q,s['zrange'][0]]),np.array([xy[0]+q,xy[1]+q,s['zrange'][1]]))
                pts=reader.query(bounds=b) # 不设置resolution/level：读取查询范围的原始层级点。
                xyz=np.column_stack((pts.x,pts.y,pts.z));c=np.asarray(pts.classification)
                row=screen(xyz,c,xy,CONFIG);row.update(id='endpoint_%03d'%len(results),source_file=source['path'],source_sha256=source['sha256'])
                results.append(row)
        print('screened',pathlib.Path(source['path']).name,flush=True)
    summary=dict(preliminary_sites=len(results),geometry_candidates=sum(r['geometric_screen']=='GEOMETRY_CANDIDATE_ONLY' for r in results),
        pad_geometry_pass_count=sum(r.get('pad_geometry_pass',False) for r in results),
        hover_observation_screen_pass_count=sum(r.get('hover_observation_screen_pass',False) for r in results),
        insufficient_ground=sum(r['geometric_screen']=='INSUFFICIENT_GROUND_EVIDENCE' for r in results),
        excluded_by_observations_or_coverage=sum(r['geometric_screen']=='EXCLUDED_BY_OBSERVATIONS_OR_COVERAGE' for r in results),
        certified_takeoff_sites=0,certified_hover_sites=0,certified_landing_sites=0,elapsed_s=time.perf_counter()-start,
        caveat='Raw-point geometric screening only; no scanner-origin free-space evidence or operational landing certification')
    (ROOT/'endpoint_screening.json').write_text(json.dumps(dict(summary=summary,config=CONFIG,sites=results),indent=2),encoding='utf-8')
    marks=[dict(id=r['id'],position=r['hover_reference_lv95_ln02_m'],status='UNQUALIFIED_GEOMETRY_CANDIDATE_ONLY') for r in results if r['geometric_screen']=='GEOMETRY_CANDIDATE_ONLY']
    (ROOT/'endpoint_markers.js').write_text('window.endpointCandidates='+json.dumps(marks)+';',encoding='utf-8')
    print(json.dumps(summary),flush=True)

if __name__=='__main__':main()
