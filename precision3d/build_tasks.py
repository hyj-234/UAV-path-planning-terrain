"""协议校准任务与三种可运行启发式；合成桥仅用于检查协议，不冒充真实桥。"""
import copy,json,math,time
import numpy as np
from acquire import ROOT,write_json
from evaluate import evaluate

def rest_to_rest(start,goal,speed,acc,wait=0):
    p=np.array(start,float);goal=np.array(goal,float);d=goal-p;length=float(np.linalg.norm(d));u=d/length
    ta=min(speed/acc,math.sqrt(length/acc));peak=acc*ta;tc=max(0.,(length-peak*ta)/peak)
    out=[];v=np.zeros(3)
    for dt,a in [(wait,np.zeros(3)),(ta,acc*u),(tc,np.zeros(3)),(ta,-acc*u)]:
        if dt<1e-9:continue
        out.append(dict(p=p.tolist(),v=v.tolist(),a=a.tolist(),dt=dt));p=p+v*dt+.5*a*dt*dt;v=v+a*dt
    return out

def task(n,r,width):
    ys=np.linspace(-9.35,9.35,n) if n>1 else [0.]
    agents=[dict(id='uav_%02d'%i,radius_m=r,start=[3.,float(y),4.],goal=[37.,-float(y),4.],initial_velocity=[0.,0.,0.],final_velocity=[0.,0.,0.]) for i,y in enumerate(ys)]
    ident='calibration_n%d_r%s_w%d'%(n,str(r).replace('.','p'),width)
    return dict(schema_version='uav3d-0.1',id=ident,world_id='synthetic_bridge_w%d'%width,source_kind='SYNTHETIC_PROTOCOL_CALIBRATION_ONLY',
        agents=agents,map_margin_m=.15,tracking_margin_m=.10,separation_margin_m=.30,
        limits=dict(runtime_budget_s=10.,mission_deadline_s=600.,speed_mps=5.,acceleration_mps2=2.,endpoint_tolerance_m=.02),
        difficulty=dict(fleet_size=n,body_radius_m=r,bridge_half_width_m=width,crossing='symmetric center convergence',endpoint_height_m=4.))

def world(width):
    return dict(schema_version='uav3d-0.1',id='synthetic_bridge_w%d'%width,unknown_policy='blocked',bounds=[[0,-15,0],[40,15,16]],
        evidence_scope='SYNTHETIC_GEOMETRY_EXACT_BY_CONSTRUCTION_NOT_REAL_WORLD',
        free_boxes=[dict(lo=[0,-15,0],hi=[40,15,16],evidence_ref='synthetic construction; occupied boxes take precedence')],
        occupied_boxes=[dict(lo=[0,-15,0],hi=[40,15,1],semantic='ground'),dict(lo=[0,-width,8],hi=[40,width,9],semantic='bridge_deck')]+
            [dict(lo=[x-1,y-1,1],hi=[x+1,y+1,8],semantic='bridge_pier') for x in (12,28) for y in (-width+1,width-1)])

def baseline(t,mode):
    start=time.perf_counter();paths={};durations=[]
    for a in t['agents']:
        s=rest_to_rest(a['start'],a['goal'],5,2);durations.append(sum(x['dt'] for x in s))
    for i,a in enumerate(t['agents']):
        wait=0 if mode=='independent' else i*2 if mode=='staggered_2s' else i*(max(durations)+2)
        paths[a['id']]=rest_to_rest(a['start'],a['goal'],5,2,wait)
    return dict(task_id=t['id'],trajectories=paths,runtime_wall_s=time.perf_counter()-start,algorithm=mode)

def main():
    results=[];tasks=[]
    for width in (12,14):
        w=world(width);write_json(ROOT/'worlds'/(w['id']+'.json'),w)
        for n in (1,2,4,6,12):
            for r in (.25,.4,.6):
                t=task(n,r,width);tasks.append(t);write_json(ROOT/'tasks'/(t['id']+'.json'),t)
                for mode in ('independent','staggered_2s','serialized'):
                    s=baseline(t,mode);result=evaluate(t,w,s);result['algorithm']=mode
                    result['runtime_trust']='MEASURED_BY_LOCAL_REFERENCE_HARNESS_SAME_PROCESS_NO_SENSOR_OR_TRAINING_TIME'
                    results.append(result)
                    write_json(ROOT/'reference_runs'/mode/(t['id']+'.json'),dict(submission=s,evaluation=result))
    write_json(ROOT/'task_manifest.json',dict(kind='SYNTHETIC_CALIBRATION',count=len(tasks),tasks=[t['id'] for t in tasks]))
    write_json(ROOT/'reference_results.json',results)
    summary=[]
    for mode in ('independent','staggered_2s','serialized'):
        rows=[r for r in results if r['algorithm']==mode];passed=[r for r in rows if r['team_success']]
        summary.append(dict(algorithm=mode,total=len(rows),team_success=sum(r['team_success'] for r in rows),
            completed_agents=sum(r['completed_agents'] for r in rows),total_agents=sum(r['total_agents'] for r in rows),
            runtime_mean_s=float(np.mean([r['runtime_wall_s'] for r in rows])),
            total_path_length_success_mean_m=float(np.mean([r['total_path_length_m'] for r in passed])) if passed else None,
            makespan_success_mean_s=float(np.mean([r['makespan_s'] for r in passed])) if passed else None,
            scope='Synthetic protocol calibration; not an external algorithm comparison or paper result'))
    write_json(ROOT/'reference_summary.json',summary);print(json.dumps(summary,indent=2),flush=True)
    # 真实区域候选保留 UNKNOWN；不以建筑盒或稀疏点云构造假的自由空间。
    if not (ROOT/'geometry'/'building_catalog.json').exists():
        print('Real candidate tasks require prepare_geometry.py first; calibration is complete.',flush=True)
        return
    catalog=json.loads((ROOT/'geometry'/'building_catalog.json').read_text(encoding='utf-8'))
    rw=dict(schema_version='uav3d-0.1',id='zurich_real_observation_only',unknown_policy='blocked',bounds=[[0,0,0],[1000,2000,200]],
        evidence_scope='PARTIAL_CONSERVATIVE_BUILDING_AABB_OBSERVATIONS; LIDAR_AVAILABLE_AS_NATIVE_COPC; NO_FREE_SPACE_CERTIFICATE',
        free_boxes=[],occupied_boxes=[dict(lo=b['lo'],hi=b['hi'],semantic='building_conservative_bbox',source_id=b['id']) for b in catalog if b['overlaps_lidar']])
    write_json(ROOT/'worlds'/(rw['id']+'.json'),rw)
    candidates=[]
    for n in (1,2,4,6,12):
        t=task(n,.25,14);t.update(id='zurich_candidate_n%d'%n,world_id=rw['id'],source_kind='REAL_GEOMETRY_CANDIDATE_NOT_QUALIFIED')
        for i,a in enumerate(t['agents']):a.update(start=[100.,100.+i*3,50.],goal=[900.,1900.-i*3,50.])
        t['qualification']='DO_NOT_RANK; ENDPOINTS_AND_FULL_FREE_SPACE_NOT_VERIFIED'
        write_json(ROOT/'candidate_tasks'/(t['id']+'.json'),t);candidates.append(t['id'])
    write_json(ROOT/'candidate_task_manifest.json',dict(count=len(candidates),ids=candidates,status='UNQUALIFIED',qualified_underbridge_routes=0))

if __name__=='__main__':main()
