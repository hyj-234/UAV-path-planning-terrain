"""先固定目标障碍，再按来源元数据筛选；只用官方train分区，不按算法成绩选场景。"""
import hashlib,json,math,pathlib,sqlite3,struct

ROOT=pathlib.Path(__file__).resolve().parent
STRATA={
 'layered_bridge':"numpts_bridge >= 100",
 'pylon_structure':"PERMSTRUCT_PYLON=1 AND numpts_permanentstructures >= 50",
 'antenna_structure':"PERMSTRUCT_ANTENNA=1 AND numpts_permanentstructures >= 50",
 'urban_building_vegetation':"URBAN=1 AND numpts_buildings>=1000 AND numpts_high_vegetation>=1000",
}

def center(blob):
    endian='<' if blob[3]&1 else '>';envelope=(blob[3]>>1)&7
    if envelope:
        x0,x1,y0,y1=struct.unpack(endian+'4d',blob[8:40]);return [(x0+x1)/2,(y0+y1)/2]
    raise ValueError('No GPKG envelope: explicit WKB parsing required, never infer source coords from patch name')

def main():
    path=ROOT/'metadata'/'fractal.gpkg';db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    selected=[];counts={};quota=8;seed='low-altitude-targeted-v1'
    for label,where in STRATA.items():
        rows=[dict(r) for r in db.execute("SELECT * FROM fractal_for_huggingface WHERE split='train' AND "+where)]
        counts[label]=len(rows);rows.sort(key=lambda r:hashlib.sha256((seed+r['patch_id']).encode()).hexdigest())
        accepted=[]
        for row in rows:
            xy=center(row.pop('geom'))
            if any(math.dist(xy,r['center_epsg2154_m'])<1000 for r in selected):continue
            row.update(target_problem=label,center_epsg2154_m=xy,status='METADATA_CANDIDATE_ONLY_NOT_DOWNLOADED_OR_ROUTE_QUALIFIED',
                claim_boundary='Bridge tag does not certify underpass; pylon/antenna tag does not certify wires or submeter obstacle completeness')
            accepted.append(row);selected.append(row)
            if len(accepted)==quota:break
        assert len(accepted)==quota,(label,len(accepted))
    assert all(r['split']=='train' for r in selected)
    assert len({r['patch_id'] for r in selected})==len(selected)
    receipt=json.loads((ROOT/'source_evidence'/'fractal_metadata_receipt.json').read_text(encoding='utf-8'))
    result=dict(source='IGNF/FRACTAL',metadata_sha256=receipt['sha256'],repository_commit=receipt['repository_commit'],
        source_split='train',pool_counts=counts,selected_count=len(selected),quota_per_target=quota,
        declared_seed=seed,minimum_pairwise_center_distance_m=1000,spatial_separation_is_not_independence_proof=True,
        point_cloud_files_downloaded=0,qualified_planning_scenes=0,candidates=selected)
    (ROOT/'fractal_target_candidates.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='candidates'},ensure_ascii=True,indent=2))

if __name__=='__main__':main()
