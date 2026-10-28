"""流式读取完整三维原件。显示抽样与科学原件分开；不凭点云空洞推断自由空间。"""
import collections, json, math, pathlib, zipfile, xml.etree.ElementTree as ET
import laspy
import numpy as np
from acquire import ROOT, write_json

LABELS={1:'unclassified',2:'ground',3:'vegetation',6:'building_roof',9:'water',
        14:'powerline',15:'mast',17:'bridge_deck',26:'building_facade',27:'bridge_pier_or_stay_cable'}
ORIGIN=np.array([2681000.,1248000.,390.])
GML='{http://www.opengis.net/gml}'
CORE='{http://www.opengis.net/citygml/2.0}'
BLDG='{http://www.opengis.net/citygml/building/2.0}'

def clouds():
    audits=[]; samples=collections.defaultdict(list)
    for path in sorted((ROOT/'raw').glob('*.copc.laz')):
        counts=collections.Counter(); bad=0; withheld=0; processed=0
        with laspy.open(path) as src:
            hdr=src.header
            for pts in src.chunk_iterator(1_000_000):
                xyz=np.column_stack((pts.x,pts.y,pts.z)); c=np.asarray(pts.classification)
                good=np.isfinite(xyz).all(axis=1); bad+=int((~good).sum())
                withheld+=int(np.asarray(pts.withheld).sum()); processed+=len(pts)
                for value,n in zip(*np.unique(c,return_counts=True)): counts[int(value)]+=int(n)
                for value in np.unique(c):
                    sel=xyz[(c==value)&good&(np.asarray(pts.withheld)==0)]-ORIGIN
                    step=max(1,math.ceil(len(sel)/300))
                    samples[int(value)].append(np.round(sel[::step],3))
            audits.append(dict(file=path.name,points=processed,nonfinite=bad,withheld_points=withheld,
                classes=dict(sorted(counts.items())),min=hdr.mins.tolist(),max=hdr.maxs.tolist(),
                sensor_origins_available=False,free_space_status='UNKNOWN_NO_RAY_ORIGIN_EVIDENCE',
                synthetic_points_used_as_free_space=False))
        print('point cloud processed',path.name,processed,flush=True)
    preview=[]
    for c,parts in sorted(samples.items()):
        xyz=np.concatenate(parts); step=max(1,math.ceil(len(xyz)/12000)); xyz=xyz[::step]
        preview.append(dict(class_id=c,label=LABELS.get(c,'other'),xyz=xyz.tolist()))
    return audits,preview

def buildings():
    archive=next((ROOT/'raw').glob('*.citygml.zip'))
    records=[]; surfaces=[]; total=0; total_surfaces=0; rings_bad=0
    with zipfile.ZipFile(archive) as z:
        name=next(n for n in z.namelist() if n.endswith('.gml'))
        with z.open(name) as stream:
            events=ET.iterparse(stream,events=('start','end')); _,root=next(events)
            for event,obj in events:
                if event!='end' or obj.tag!=CORE+'cityObjectMember': continue
                total+=1
                polygons=[]; points=[]; edges=collections.Counter(); seen=set()
                for poly in obj.iter(GML+'Polygon'):
                    rings=[]
                    for ring in poly.iter(GML+'LinearRing'):
                        pos=ring.find(GML+'posList')
                        if pos is None or not pos.text: continue
                        a=np.fromstring(pos.text,sep=' ')
                        if len(a)%3: rings_bad+=1; continue
                        a=np.round(a.reshape(-1,3)-ORIGIN,4)
                        if not np.isfinite(a).all() or len(a)<4 or not np.allclose(a[0],a[-1],atol=0.0002,rtol=0):
                            rings_bad+=1;continue
                        rings.append(a.tolist());points.append(a)
                    # XLink 的重复面仅计一次，不将“每边两面”误认为完整流形认证。
                    if rings:
                        key=tuple(sorted(tuple(v) for v in rings[0]))
                        if key in seen: continue
                        seen.add(key);polygons.append(rings)
                        for r in rings:
                            for a,b in zip(r,r[1:]): edges[tuple(sorted((tuple(a),tuple(b))))]+=1
                if points:
                    xyz=np.concatenate(points); lo=xyz.min(axis=0); hi=xyz.max(axis=0)
                    b=next(iter(obj),None); ident=b.get(GML+'id',str(total)) if b is not None else str(total)
                    overlap=bool(hi[0]>=0 and lo[0]<=1000 and hi[1]>=0 and lo[1]<=2000)
                    row=dict(id=ident,lo=lo.tolist(),hi=hi.tolist(),polygon_count=len(polygons),
                        edge_incidence_two=all(v==2 for v in edges.values()) and bool(edges),
                        certification='NOT_CERTIFIED_SELF_INTERSECTIONS_OR_ORIENTATION',overlaps_lidar=overlap)
                    records.append(row);total_surfaces+=len(polygons)
                    if overlap: surfaces.append(dict(id=ident,polygons=polygons,lo=row['lo'],hi=row['hi']))
                obj.clear();root.clear()
    write_json(ROOT/'geometry'/'building_catalog.json',records)
    write_json(ROOT/'geometry'/'building_surfaces_overlap.json',surfaces)
    return dict(source_members=total,objects_with_coordinates=len(records),unique_polygons=total_surfaces,
        overlapping_lidar_objects=len(surfaces),invalid_rings=rings_bad,
        two_incidence_objects=sum(r['edge_incidence_two'] for r in records),
        epoch_mismatch='Building source nominal 2019, lidar nominal 2024; no co-temporal ground-truth claim',
        warning='Source CityGML retains full original; derived overlap is explicitly a subset; no synthetic height extrusion'),surfaces

if __name__=='__main__':
    a,p=clouds(); b,s=buildings()
    audit=dict(crs='EPSG:2056 + EPSG:5728',local_origin=ORIGIN.tolist(),point_clouds=a,buildings=b,
        underbridge_status='REAL_DECK_AND_PIER_OBSERVATIONS_AVAILABLE; FREE_SPACE_UNQUALIFIED',
        fully_qualified_real_underbridge_routes=0)
    write_json(ROOT/'geometry_audit.json',audit)
    display=[dict(id=o['id'],polygons=o['polygons'][::max(1,math.ceil(len(o['polygons'])/8))],lo=o['lo'],hi=o['hi']) for o in s]
    payload=dict(origin=ORIGIN.tolist(),clouds=p,buildings=display,warning=audit['underbridge_status'],building_display='At most eight polygon outlines per object; full polygons in geometry/building_surfaces_overlap.json')
    out=ROOT/'viewer'/'geometry.js';out.parent.mkdir(exist_ok=True)
    out.write_text('window.geometryData='+json.dumps(payload,separators=(',',':'))+';',encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=False),flush=True)
