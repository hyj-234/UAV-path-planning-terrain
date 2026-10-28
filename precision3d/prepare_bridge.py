"""标准库 + numpy 读取 binary PCD，不依赖 Open3D，不将 VIEWPOINT 默认值作真实扫描站。"""
import collections, json, pathlib
import numpy as np
from acquire import ROOT,write_json

def read(path):
    h={}
    with path.open('rb') as f:
        while True:
            row=f.readline().decode('ascii').strip().split()
            if row and not row[0].startswith('#'):h[row[0]]=row[1:]
            if row and row[0]=='DATA':offset=f.tell();break
    assert h['DATA']==['binary']
    dtype=[]
    for name,size,kind,count in zip(h['FIELDS'],h['SIZE'],h['TYPE'],h['COUNT']):
        typ={'F':'f','U':'u','I':'i'}[kind]+size
        dtype.append((name,typ,int(count)) if int(count)>1 else (name,typ))
    n=int(h['POINTS'][0]);dt=np.dtype(dtype)
    assert offset+n*dt.itemsize==path.stat().st_size
    data=np.memmap(path,dtype=dt,mode='r',offset=offset,shape=(n,))
    low=np.full(3,np.inf);high=-low;bad=0;labels=collections.Counter()
    for start in range(0,n,1_000_000):
        a=data[start:start+1_000_000];xyz=np.column_stack((a['x'],a['y'],a['z']));good=np.isfinite(xyz).all(axis=1)
        bad+=int((~good).sum());low=np.minimum(low,xyz[good].min(axis=0));high=np.maximum(high,xyz[good].max(axis=0))
        if 'Constant' in dt.names:
            values,counts=np.unique(a['Constant'],return_counts=True)
            labels.update({str(float(v)):int(c) for v,c in zip(values,counts)})
    a=data[::max(1,int(np.ceil(n/80000)))];xyz=np.column_stack((a['x'],a['y'],a['z']));good=np.isfinite(xyz).all(axis=1)
    center=(low+high)/2;xyz=xyz[good]-center
    rgb=np.ascontiguousarray(a['rgb'][good]).view(np.uint32)
    colors=['rgb(%s,%s,%s)'%((int(v)>>16)&255,(int(v)>>8)&255,int(v)&255) for v in rgb]
    preview=dict(name=path.stem,center=center.tolist(),xyz=np.round(xyz,4).tolist(),colors=colors,
        warning='Real TLS geometry; source units, axis frame, scanner stations and underpass free-space coverage not certified')
    out=ROOT/'viewer'/(path.stem+'.js');out.write_text('window.bridgeData='+json.dumps(preview,separators=(',',':'))+';',encoding='utf-8')
    return dict(file=path.name,points=n,nonfinite=bad,header=h,min=low.tolist(),max=high.tolist(),
        raw_label_histogram=dict(labels),label_semantics='NOT_DOCUMENTED_IN_DATASET_METADATA',
        coordinate_unit='NOT_DECLARED_IN_PCD_HEADER_OR_RETRIEVED_METADATA',
        source_station_poses='NOT_PROVIDED; VIEWPOINT 0 0 0 1 0 0 0 is not validated as a scanner station',
        underbridge_free_space='UNKNOWN; missing rays/coverage evidence',
        planning_qualification='REAL_GEOMETRY_RESEARCH_ONLY_UNTIL_SCALE_REGISTRATION_AND_FREE_SPACE_VALIDATION')

if __name__=='__main__':
    audits=[read(p) for p in sorted((ROOT/'raw').glob('*.pcd'))]
    write_json(ROOT/'bridge_geometry_audit.json',audits)
    print(json.dumps([{k:r[k] for k in ('file','points','nonfinite','min','max','raw_label_histogram')} for r in audits]),flush=True)
