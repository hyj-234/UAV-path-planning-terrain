"""独立、连续时间的多机轨迹检查器；单位 m、s，模型为有限分段常加速度球体。

每段 p(t)=p0+v0*t+a*t²/2。机间最近距离检查四次距离平方的全部实驻点；
障碍使用保守 AABB 膨胀。未知空间默认拒绝。此检查不等于六自由度飞行认证。
"""
import argparse, itertools, json, math, pathlib, time
import numpy as np

EPS=1e-7

def roots(coeff, duration):
    """系数按升幂；仅返回区间内实根。"""
    c=np.trim_zeros(np.asarray(coeff,dtype=float),'b')
    if len(c)<=1:return []
    out=[]
    for x in np.polynomial.polynomial.polyroots(c):
        if abs(x.imag)<1e-6 and -EPS<=x.real<=duration+EPS:out.append(float(np.clip(x.real,0,duration)))
    return out

def position(s,t):return s['p']+s['v']*t+0.5*s['a']*t*t

def box_intervals(s,lo,hi):
    """精确分解二次曲线处在闭 AABB 内的时间区间，包含相切时刻。"""
    cuts=[0.,s['dt']]
    for k in range(3):
        for edge in (lo[k],hi[k]):cuts+=roots([s['p'][k]-edge,s['v'][k],0.5*s['a'][k]],s['dt'])
    cuts=sorted(set(cuts));out=[]
    def inside(t):
        q=position(s,t);return bool(np.all(q>=lo-EPS) and np.all(q<=hi+EPS))
    for t in cuts:
        if inside(t):out.append((t,t))
    for a,b in zip(cuts,cuts[1:]):
        if inside((a+b)/2):out.append((a,b))
    return out

def covered(intervals,duration):
    end=0.
    for a,b in sorted(intervals):
        if a>end+EPS:return False
        end=max(end,b)
    return end>=duration-EPS

def normalize(task,submission):
    agents=task['agents'];paths=submission['trajectories'];out={}
    if set(paths)!=set(a['id'] for a in agents):raise ValueError('agent IDs must match exactly; missing agents remain failures')
    for agent in agents:
        ident=agent['id'];segments=[];t=0.
        if not paths[ident]:raise ValueError('empty trajectory '+ident)
        for raw in paths[ident]:
            s={k:np.asarray(raw[k],float) for k in ('p','v','a')};s['dt']=float(raw['dt']);s['t']=t
            if any(s[k].shape!=(3,) or not np.isfinite(s[k]).all() for k in ('p','v','a')):raise ValueError('invalid vectors')
            if not math.isfinite(s['dt']) or s['dt']<=0:raise ValueError('nonpositive or nonfinite duration')
            if segments:
                prev=segments[-1]
                if np.linalg.norm(position(prev,prev['dt'])-s['p'])>1e-5:raise ValueError('position discontinuity')
                if np.linalg.norm(prev['v']+prev['a']*prev['dt']-s['v'])>1e-5:raise ValueError('velocity discontinuity')
            segments.append(s);t+=s['dt']
        out[ident]=segments
    return out

def evaluate(task,world,submission):
    started=time.perf_counter();fail=[];metrics={};done=0
    try:
        if task['schema_version']!='uav3d-0.1' or world['schema_version']!='uav3d-0.1':raise ValueError('schema version')
        if task['world_id']!=world['id'] or submission['task_id']!=task['id']:raise ValueError('task/world mismatch')
        if world['unknown_policy'] not in ('blocked','model_closed_world'):raise ValueError('unknown policy')
        paths=normalize(task,submission)
        if not task['agents']:raise ValueError('empty fleet')
        if len({a['id'] for a in task['agents']})!=len(task['agents']):raise ValueError('duplicate task agent IDs')
        for agent in task['agents']:
            for key in ('start','goal','initial_velocity','final_velocity'):
                vector=np.asarray(agent[key],float)
                if vector.shape!=(3,) or not np.isfinite(vector).all():raise ValueError('invalid task vector')
            if np.linalg.norm(agent['final_velocity'])>EPS:raise ValueError('this version requires rest at goal')
        if not isinstance(submission['runtime_wall_s'],(int,float)) or not math.isfinite(submission['runtime_wall_s']) or submission['runtime_wall_s']<0:raise ValueError('invalid measured runtime')
        limit=task['limits'];bounds=np.asarray(world['bounds'],float)
        for key in ('runtime_budget_s','endpoint_tolerance_m','speed_mps','acceleration_mps2','mission_deadline_s'):
            if not math.isfinite(limit[key]) or limit[key]<=0:raise ValueError('invalid positive limit '+key)
        if not math.isfinite(task['separation_margin_m']) or task['separation_margin_m']<0:raise ValueError('invalid separation margin')
        if bounds.shape!=(2,3) or not np.isfinite(bounds).all() or np.any(bounds[1]<=bounds[0]):raise ValueError('invalid bounds')
        for collection in ('occupied_boxes','free_boxes'):
            for b in world.get(collection,[]):
                box=np.array([b['lo'],b['hi']],float)
                if box.shape!=(2,3) or not np.isfinite(box).all() or np.any(box[1]<box[0]):raise ValueError('invalid box')
                if collection=='free_boxes' and not b.get('evidence_ref'):raise ValueError('free box lacks evidence')
        if submission['runtime_wall_s']>limit['runtime_budget_s']:fail.append('RUNTIME_BUDGET')
        for a in task['agents']:
            ident=a['id'];segs=paths[ident];r=float(a['radius_m'])+float(task['map_margin_m'])+float(task['tracking_margin_m'])
            if not math.isfinite(r) or a['radius_m']<=0 or min(task['map_margin_m'],task['tracking_margin_m'])<0:raise ValueError('invalid margin or radius')
            reasons=[];length=0.;vmax=0.;amax=0.
            if np.linalg.norm(segs[0]['p']-a['start'])>limit['endpoint_tolerance_m']:reasons.append('START')
            if np.linalg.norm(segs[0]['v']-a['initial_velocity'])>1e-5:reasons.append('START_VELOCITY')
            for s in segs:
                vmax=max(vmax,float(np.linalg.norm(s['v'])),float(np.linalg.norm(s['v']+s['a']*s['dt'])))
                amax=max(amax,float(np.linalg.norm(s['a'])))
                if not covered(box_intervals(s,bounds[0]+r,bounds[1]-r),s['dt']):reasons.append('OUT_OF_BOUNDS')
                for b in world.get('occupied_boxes',[]):
                    if box_intervals(s,np.array(b['lo'])-r,np.array(b['hi'])+r):reasons.append('STATIC_COLLISION');break
                if world['unknown_policy']=='blocked':
                    intervals=[]
                    for b in world.get('free_boxes',[]):
                        lo=np.array(b['lo'])+r;hi=np.array(b['hi'])-r
                        if np.all(hi>=lo):intervals+=box_intervals(s,lo,hi)
                    if not covered(intervals,s['dt']):reasons.append('UNKNOWN_SPACE')
                # 路长用固定 24 点 Gauss-Legendre 积分；碰撞检查不依赖该离散积分。
                q,w=np.polynomial.legendre.leggauss(24);ts=(q+1)*s['dt']/2
                length+=float(np.dot(w,np.linalg.norm(s['v'][None,:]+ts[:,None]*s['a'][None,:],axis=1))*s['dt']/2)
            last=segs[-1];end=position(last,last['dt']);endv=last['v']+last['a']*last['dt']
            if np.linalg.norm(end-a['goal'])>limit['endpoint_tolerance_m']:reasons.append('GOAL')
            if np.linalg.norm(endv-a['final_velocity'])>1e-5:reasons.append('GOAL_VELOCITY')
            if vmax>limit['speed_mps']+EPS:reasons.append('SPEED')
            if amax>limit['acceleration_mps2']+EPS:reasons.append('ACCELERATION')
            arrival=last['t']+last['dt']
            if arrival>limit['mission_deadline_s']:reasons.append('DEADLINE')
            fail += [ident+':'+x for x in sorted(set(reasons))]
            if not reasons:done+=1
            metrics[ident]=dict(path_length_m=length,arrival_s=arrival,max_speed_mps=vmax,max_acceleration_mps2=amax)
        horizon=max(v[-1]['t']+v[-1]['dt'] for v in paths.values())
        # 到达后原地占位；轨迹时间从共同 t=0 开始，延迟必须显式给出悬停段。
        for ident,segs in paths.items():
            last=segs[-1];endtime=last['t']+last['dt']
            if endtime<horizon-EPS:
                segs.append(dict(p=position(last,last['dt']),v=np.zeros(3),a=np.zeros(3),dt=horizon-endtime,t=endtime))
        minsep=math.inf;conflicted=set()
        amap={a['id']:a for a in task['agents']}
        for i,j in itertools.combinations(paths,2):
            threshold=amap[i]['radius_m']+amap[j]['radius_m']+task['separation_margin_m']
            pairmin=math.inf
            for s in paths[i]:
                for z in paths[j]:
                    begin=max(s['t'],z['t']);end=min(s['t']+s['dt'],z['t']+z['dt'])
                    if end<begin:continue
                    p=position(s,begin-s['t'])-position(z,begin-z['t'])
                    v=s['v']+s['a']*(begin-s['t'])-z['v']-z['a']*(begin-z['t']);a=(s['a']-z['a'])/2
                    coeff=np.zeros(5)
                    for k in range(3):
                        term=np.polynomial.polynomial.polymul([p[k],v[k],a[k]],[p[k],v[k],a[k]])
                        coeff[:len(term)]+=term
                    candidates=[0,end-begin]+roots(np.arange(1,5)*coeff[1:],end-begin)
                    distance=math.sqrt(max(0,min(float(np.polynomial.polynomial.polyval(t,coeff)) for t in candidates)))
                    pairmin=min(pairmin,distance)
            minsep=min(minsep,pairmin)
            if pairmin<=threshold+EPS:fail.append('PAIR_COLLISION:'+i+':'+j);conflicted.update((i,j))
        for ident in conflicted:
            if not any(x.startswith(ident+':') for x in fail):done-=1
        if 'RUNTIME_BUDGET' in fail:done=0
        result=dict(task_id=task['id'],status=('PASS_MODEL_CONDITIONAL' if world['unknown_policy']=='model_closed_world' else 'PASS') if not fail else 'FAIL',
            failure_reasons=fail,completed_agents=done,total_agents=len(task['agents']),task_completion_fraction=done/len(task['agents']),
            team_success=not fail,metrics=metrics,minimum_pair_distance_m=None if minsep==math.inf else minsep,
            runtime_wall_s=submission['runtime_wall_s'],runtime_trust='SUBMITTER_REPORTED_REQUIRE_EXTERNAL_HARNESS_FOR_RANKING',
            total_path_length_m=sum(m['path_length_m'] for m in metrics.values()),makespan_s=horizon,
            evidence_scope=world.get('evidence_scope','UNSPECIFIED'))
    except (KeyError,ValueError,TypeError,OverflowError) as e:
        result=dict(task_id=task.get('id'),status='INVALID',failure_reasons=[str(e)],completed_agents=0,total_agents=len(task.get('agents',[])),team_success=False)
    result['evaluator_wall_s']=time.perf_counter()-started
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('task');p.add_argument('world');p.add_argument('submission');p.add_argument('--output');args=p.parse_args()
    load=lambda f:json.loads(pathlib.Path(f).read_text(encoding='utf-8'))
    result=evaluate(load(args.task),load(args.world),load(args.submission))
    text=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output:pathlib.Path(args.output).write_text(text,encoding='utf-8')
    print(text)
