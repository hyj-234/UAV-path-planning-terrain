'use strict';
const $=id=>document.getElementById(id);
const cfg={responsive:true,scrollZoom:true,displaylogo:false,toImageButtonOptions:{format:'png',scale:2}};
let current=null,localImage=null,loadVersion=0,detailVersion=0,viewBusy=false;
const finite=v=>typeof v==='number'&&Number.isFinite(v)&&Math.abs(v)<1e10;
function validate(d){
 if(!d||!Array.isArray(d.z)||d.z.length<2||!Array.isArray(d.z[0])||d.z[0].length<2)throw Error('需要至少2×2的高程网格');
 if(d.z.some(row=>row.length!==d.x.length)||d.y.length!==d.z.length)throw Error('坐标和高程网格尺寸不一致');
 if(!d.x.every(finite)||!d.y.every(finite)||!d.z.some(row=>row.some(finite)))throw Error('网格没有有效坐标或高程');
 if(d.z.some(row=>row.some(v=>v!==null&&!finite(v))))throw Error('缺测值请使用null');
}
function error(e){$('error').textContent='无法显示：'+String(e.message||e);}
function terrainOptions(){
 const items=window.TERRAIN_CATALOG.filter(t=>t.group===$('group').value);
 $('terrain').replaceChildren(...items.map(t=>new Option(t.title,t.id)));
}
function groupOptions(){
 $('group').replaceChildren(...[...new Set(window.TERRAIN_CATALOG.map(t=>t.group))].map(s=>new Option(s,s)));
 terrainOptions();
}
async function show(d,version){
 validate(d);if(version!==loadVersion)return;current=d;$('error').textContent='';viewBusy=true;
 // 扫描高度范围，避免把大网格展开为函数参数。
 let min=Infinity,max=-Infinity;for(const row of d.z)for(const v of row)if(finite(v)){min=Math.min(min,v);max=Math.max(max,v);}
 const hover='X %{x:.3f}<br>Y %{y:.3f}<br>高程 %{z:.4f}<extra></extra>';
 const layout={margin:{l:70,r:105,t:15,b:55},xaxis:{title:{text:d.xy_unit?'局部东向（'+d.xy_unit+'）':'X（源坐标单位）'},constrain:'domain'},yaxis:{title:{text:d.xy_unit?'局部北向（'+d.xy_unit+'）':'Y（源坐标单位）'},scaleanchor:'x'},dragmode:'zoom'};
 await Plotly.react('flat',[{type:'heatmap',x:d.x,y:d.y,z:d.z,colorscale:'Earth',zmin:min,zmax:max,zsmooth:false,hoverongaps:false,hovertemplate:hover,colorbar:{title:{text:'高程'+(d.z_unit?'（'+d.z_unit+'）':'（源单位）')}}}],layout,cfg);
 const stride=Math.max(1,Math.ceil(Math.max(d.x.length,d.y.length)/220));
 const indices=n=>{let a=[];for(let i=0;i<n;i+=stride)a.push(i);if(a.at(-1)!==n-1)a.push(n-1);return a;};
 const ix=indices(d.x.length),iy=indices(d.y.length);
 const spans={x:Math.abs(d.x.at(-1)-d.x[0]),y:Math.abs(d.y.at(-1)-d.y[0]),z:max-min};
 const extent=Math.max(spans.x,spans.y,spans.z,1e-9);
 const aspect={x:Math.max(spans.x/extent,1e-6),y:Math.max(spans.y/extent,1e-6),z:Math.max(spans.z/extent,1e-6)};
 await Plotly.react('surface',[{type:'surface',x:ix.map(i=>d.x[i]),y:iy.map(i=>d.y[i]),z:iy.map(j=>ix.map(i=>d.z[j][i])),connectgaps:false,colorscale:'Earth',cmin:min,cmax:max,hovertemplate:hover,colorbar:{title:{text:'高程'+(d.z_unit?'（'+d.z_unit+'）':'（源单位）')}}}],{margin:{l:0,r:85,t:15,b:15},scene:{aspectmode:'manual',aspectratio:aspect,xaxis:{title:{text:'X'}},yaxis:{title:{text:'Y'}},zaxis:{title:{text:'高程'}},camera:{eye:{x:1.9,y:-2,z:1.5}}}},cfg);
 if(version!==loadVersion){viewBusy=false;return;}
 $('scope').textContent=d.scope||'源文件全范围预览';$('provenance').textContent='来源：'+(d.source||'用户本地文件');
 $('metadata').textContent=JSON.stringify(d.metadata||{},null,2);
 $('status').textContent=d.title+' · 全范围 '+d.z[0].length+'×'+d.z.length+' 显示网格 · 高程 '+min.toFixed(3)+' 至 '+max.toFixed(3)+(d.z_unit?' '+d.z_unit:'（源单位）');viewBusy=false;
}
window.registerTerrain=async function(id,d){
 if(id!==$('terrain').value)return;
 try{await show(d,loadVersion);}catch(e){viewBusy=false;error(e);}
};
function loadSelected(){
 ++loadVersion;++detailVersion;localImage=null;$('error').textContent='';$('status').textContent='加载完整范围…';
 const t=window.TERRAIN_CATALOG.find(t=>t.id===$('terrain').value);if(!t)return;
 if(t.url){const version=loadVersion;GeoTIFF.fromUrl(t.url).then(tiff=>openDataset(tiff,t.title,version,t)).catch(e=>{if(version===loadVersion)error(e);});return;}
 const script=document.createElement('script');script.src=t.file;
 script.onerror=()=>error(Error('找不到地图文件，请保留整个文件夹'));
 document.head.appendChild(script);
}
function cleanRasters(rasters,width,height,nodata){
 const a=rasters[0],z=[];for(let j=0;j<height;j++){let row=[];for(let i=0;i<width;i++){const v=Number(a[j*width+i]);row.push(finite(v)&&v!==nodata?v:null);}z.push(row);}return z;
}
async function openTiff(file,version){
 return openDataset(await GeoTIFF.fromBlob(file),file.name,version,null);
}
async function openDataset(tiff,name,version,entry){
 const image=await tiff.getImage();
 const bbox=image.getBoundingBox();if(bbox.length!==4||!bbox.every(finite))throw Error('文件没有可识别的地理范围');
 const width=image.getWidth(),height=image.getHeight(),scale=Math.min(1,600/Math.max(width,height));
 const w=Math.max(2,Math.round(width*scale)),h=Math.max(2,Math.round(height*scale));
 const raw=await image.readRasters({samples:[0],width:w,height:h,resampleMethod:'nearest'});
 const nodata=image.getGDALNoData(),dx=(bbox[2]-bbox[0])/w,dy=(bbox[3]-bbox[1])/h;
 const d={title:name,source:entry?entry.source:'浏览器本地读取；没有上传文件',x:Array.from({length:w},(_,i)=>bbox[0]+(i+.5)*dx),y:Array.from({length:h},(_,j)=>bbox[3]-(j+.5)*dy),z:cleanRasters(raw,w,h,nodata),scope:'源GeoTIFF完整范围。二维放大时重新读取源像元；三维显示全幅概览。'+(entry?' © swisstopo；场景为地点语境标签，尚未逐像元独立审核。':''),metadata:{...(entry?entry.metadata:{}),native_width:width,native_height:height,bounds:bbox,geokeys:image.getGeoKeys(),nodata}};
 await show(d,version);if(version===loadVersion)localImage={image,bbox,nodata,width,height};
}
async function zoomDetail(event){
 if(!localImage||viewBusy)return;
 const layout=$('flat').layout;
 if(!(event['xaxis.range[0]']!==undefined||event['yaxis.range[0]']!==undefined||event['xaxis.range']||event['yaxis.range']||event['xaxis.autorange']))return;
 const {image,bbox,nodata,width,height}=localImage,version=++detailVersion;
 const xr=layout.xaxis.range,yr=layout.yaxis.range;
 const col=v=>(v-bbox[0])/(bbox[2]-bbox[0])*width,row=v=>(bbox[3]-v)/(bbox[3]-bbox[1])*height;
 const clamp=(v,n)=>Math.max(0,Math.min(n,v));
 const x0=clamp(Math.floor(col(Math.min(...xr))),width-1),x1=clamp(Math.ceil(col(Math.max(...xr))),width);
 const y0=clamp(Math.floor(row(Math.max(...yr))),height-1),y1=clamp(Math.ceil(row(Math.min(...yr))),height);
 if(x1<=x0||y1<=y0)return;
 try{
 const w=Math.min(800,x1-x0),h=Math.min(800,y1-y0),r=await image.readRasters({window:[x0,y0,x1,y1],width:w,height:h,samples:[0],resampleMethod:'nearest'});
 if(version!==detailVersion||!localImage||localImage.image!==image)return;
 const dx=(bbox[2]-bbox[0])/width,dy=(bbox[3]-bbox[1])/height;
 await Plotly.restyle('flat',{x:[Array.from({length:w},(_,i)=>bbox[0]+(x0+(i+.5)*(x1-x0)/w)*dx)],y:[Array.from({length:h},(_,j)=>bbox[3]-(y0+(j+.5)*(y1-y0)/h)*dy)],z:[cleanRasters(r,w,h,nodata)]},[0]);
 }catch(e){error(e);}
}
$('group').addEventListener('change',()=>{terrainOptions();loadSelected();});$('terrain').addEventListener('change',loadSelected);
$('file').addEventListener('change',async()=>{
 const file=$('file').files[0];if(!file)return;const version=++loadVersion;++detailVersion;localImage=null;
 $('status').textContent='正在读取本地完整地形…';
 try{if(/\.json$/i.test(file.name))await show(JSON.parse(await file.text()),version);else await openTiff(file,version);}catch(e){viewBusy=false;error(e);}
});
$('reset').addEventListener('click',async()=>{if(!current)return;++detailVersion;if(localImage){await show(current,loadVersion);}else await Plotly.relayout('flat',{'xaxis.autorange':true,'yaxis.autorange':true});await Plotly.relayout('surface',{'scene.camera':{eye:{x:1.9,y:-2,z:1.5}}});});
groupOptions();loadSelected();
let hooked=false;const timer=setInterval(()=>{if(!hooked&&typeof $('flat').on==='function'){hooked=true;$('flat').on('plotly_relayout',zoomDetail);clearInterval(timer);}},100);
