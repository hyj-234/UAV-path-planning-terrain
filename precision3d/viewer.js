/* 显示层不参与科学碰撞检查，不构造桥下可飞空域。 */
const colors={1:'#98a5b3',2:'#ba9b7c',3:'#5cbd7a',6:'#e5b14d',9:'#529edf',14:'#f66aaf',15:'#a88bff',17:'#fa7149',26:'#e8cd8b',27:'#ffead2'};
const labels={1:'未分类',2:'裸地',3:'植被',6:'建筑屋顶',9:'水面',14:'电力线',15:'杆塔',17:'桥面',26:'建筑立面',27:'桥墩 / 拉索'};
let version=0, traces=[], current='geometry';
const status=document.getElementById('status');
function pointTrace(xyz,name,color){return {type:'scatter3d',mode:'markers',name,x:xyz.map(p=>p[0]),y:xyz.map(p=>p[1]),z:xyz.map(p=>p[2]),marker:{size:1.4,color,opacity:.85},hovertemplate:name+'<br>X %{x}<br>Y %{y}<br>Z %{z}<extra></extra>'};}
async function load(){const turn=++version;current=document.getElementById('scene').value;status.textContent='正在读取三维预览…';
try{if(window.plotlyReady)await window.plotlyReady;await new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=current+'.js';s.onload=resolve;s.onerror=reject;document.body.appendChild(s)});if(turn!==version)return;
const bytes=Uint8Array.from(atob(window.geometryPayload),c=>c.charCodeAt(0));const obj=JSON.parse(await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).text());if(turn!==version)return;if(current==='geometry')window.geometryData=obj;else window.bridgeData=obj;
let units='米（源坐标减去固定原点）';
if(current==='geometry'){
const d=window.geometryData;traces=d.clouds.map(c=>pointTrace(c.xyz,labels[c.class_id]||c.label,colors[c.class_id]||'#aaa'));
const x=[],y=[],z=[];for(const b of d.buildings)for(const polygon of b.polygons)for(const ring of polygon){for(const p of ring){x.push(p[0]);y.push(p[1]);z.push(p[2])}x.push(null);y.push(null);z.push(null)}
traces.push({type:'scatter3d',mode:'lines',name:'实际建筑面轮廓 · 抽样',x,y,z,line:{width:2,color:'#80d3ed'}});
status.textContent='Source: Federal Office of Topography swisstopo · 完整原件52,936,486点；建筑原件9,214个有坐标对象，936个与点云范围相交。图中为抽样。';
document.getElementById('notice').textContent='LV95 / LN02。建筑名义年份2019，点云2024；两者有时间差。未见点的空间仍为未知，桥下通行尚未认证。';
}else{const d=window.bridgeData;traces=[pointTrace(d.xyz,'实测 TLS · 作者版本',d.colors)];units='源坐标单位（米制与轴向尚待独立核验）';status.textContent='Source: Fang et al. (2025), DOI 10.17632/znxxsgn2ky.2 · CC BY 4.0 · 本图显示 '+d.xyz.length.toLocaleString()+' 个抽样点';document.getElementById('notice').innerHTML='真实桥梁扫描，不是生成的桥模型。原始文件未给出可核验的扫描站与自由空间证据，不能将桥下空洞视为已认证航线。<a href="https://data.mendeley.com/datasets/znxxsgn2ky/2" target="_blank" rel="noopener">查看原始来源与署名</a>';}
await Plotly.newPlot('plot',traces,{paper_bgcolor:'#0c1420',plot_bgcolor:'#0c1420',font:{color:'#dbe8f3'},margin:{l:0,r:0,t:0,b:0},legend:{x:0,y:1,bgcolor:'#152337cc'},scene:{aspectmode:'data',xaxis:{title:'X · '+units},yaxis:{title:'Y'},zaxis:{title:'Z'},camera:{eye:{x:1.6,y:-1.6,z:.9}}}},{responsive:true,scrollZoom:true,displaylogo:false});
}catch(e){if(turn===version)status.textContent='预览加载失败：'+String(e)}}
document.getElementById('scene').onchange=load;
document.getElementById('reset').onclick=()=>Plotly.relayout('plot',{'scene.camera':{eye:{x:1.6,y:-1.6,z:.9}},'scene.xaxis.autorange':true,'scene.yaxis.autorange':true,'scene.zaxis.autorange':true});
document.getElementById('bridge').onclick=()=>{if(current!=='geometry')return;Plotly.restyle('plot',{visible:traces.map(t=>t.name==='桥面'||t.name==='桥墩 / 拉索'?true:'legendonly')});};
load();
