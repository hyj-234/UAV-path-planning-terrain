'use strict';
// Offline bundles use local copies. The source-only GitHub site uses pinned official distributions.
function loadScript(src){return new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=src;s.onload=resolve;s.onerror=reject;document.head.appendChild(s);});}
Promise.all([
 loadScript('vendor/plotly-2.35.2.min.js').catch(()=>loadScript('https://cdn.plot.ly/plotly-2.35.2.min.js')),
 loadScript('vendor/geotiff-2.1.3.js').catch(()=>loadScript('https://cdn.jsdelivr.net/npm/geotiff@2.1.3/dist-browser/geotiff.js'))
]).then(()=>loadScript('app.js')).catch(()=>{document.getElementById('error').textContent='绘图库未加载。离线使用请运行 tools/download_vendor.py 下载两个固定版本的绘图库，然后重新打开页面。';});
