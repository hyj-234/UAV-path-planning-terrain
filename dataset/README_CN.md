# 多场景真实地形数据集 v2

100个登记地点、20个国家、200份完整分发栅格，约2.89GB原始文件。高分辨率32地点/64产品来自swisstopo；区域级68地点各有Copernicus GLO30/GLO90，共136产品。两种分辨率同源，不能算作独立观测或额外地点。场景包括城市、山地、农村、森林、湖泊河流、荒漠、海岸、冰雪。

## 真实性与许可

- 64个swisstopo文件逐一匹配官方STAC SHA256。许可是swisstopo OGD，保留 Source: Federal Office of Topography swisstopo，不是MIT/CC BY。
- 136个Copernicus文件来自文档指明的AWS COG分发，核对官方瓦片清单、HTTPS、内容长度、投影、锚点范围和本地SHA256。上游未提供SHA256，不能声称已验证官方校验和。它们是基于真实观测的编辑DSM，并非未经处理的裸地真值。
- Copernicus署名：© DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved。分发方对边界重复行列和COG概览做过处理；本项目保留其完整分发文件。
- WorldCover 2021为辅助地类模型，CC BY 4.0。署名：© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium。
- 三种数据许可分别适用，不受查看器MIT代码许可覆盖。

## 标签复核

100地点均检查了锚点附近约1公里WorldCover地类比例。76个达到预先固定的25%相关类别支持阈值，24个是混合或需复核标签，未删除或强行改成通过。海岸、山地等地貌语境不能只由地表覆盖类别证明；该检查不是人工地面真值，也不代表整幅1度区域主类别。不得把100地点称为100个独立统计样本；相邻地理区域应分组隔离。

## 是否适合无人机规划

高分辨率：执行192个固定任务，169个通过保守原始像元净空核查和点质量运动剖面检查，23个达到50,000状态搜索上限；不是证明23个任务无解。64份精细栅格各至少有1条通过的参考。配置：半径2m、净空10m、相对表面高度上限120m、速度10m/s、垂直速度2m/s、加速度2m/s²。搜索在保守最大/最小高度包络上进行，独立检查回到原始像元，未使用网页降采样像素作碰撞证据。

区域级：GLO30执行204条固定区域直线参考诊断。143条满足所表示表面的60m净空及1000m相对表面高度上限，61条超过所声明的高度上限；需要绕行或不同任务，不能按原约束算通过。GLO90是相关的低分辨率背景，没有另做独立运动试验。区域距离为局部近似，不是可上传飞控的导航坐标。

这些仅为静态、单机、简化点质量或解析剖面的参考可行性检查，不含跟踪误差、风、真实飞控、动力/续航、空域法规、动态障碍或多机冲突。DTM缺少建筑树冠，DSM是2.5D表面且不能表达桥下/悬挑。30/90m栅格不合格于精密低空与建筑间隙避障。所有类别均未获得真实飞行安全认证。

## 复现与现有实验

原始下载链接、SHA256、尺寸和用途见catalog.json；完整原始源清单见fine_source_manifest.json与global_source_manifest.json。下载工具：python tools/download_dataset.py fine|global OUTPUT_DIRECTORY。校验工具依赖numpy/rasterio/scipy，位于tools/validation。输出路径应独立保存。

原有变化地形10来源组继续单独保留，尚未重新完成许可/配准精度资格，不混入本批200静态产品。原论文冻结任务、模型和五地域留出没有修改；尚未创建新的正式训练/验证/测试划分。

官方文档：
- https://www.swisstopo.admin.ch/en/faq-free-geodata
- https://www.swisstopo.admin.ch/en/height-model-swisssurface3d-raster
- https://copernicus-dem-30m.s3.amazonaws.com/readme.html
- https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM
- https://esa-worldcover.org/en/data-access

## 网页概览与坐标

部分Copernicus分发地址没有浏览器跨域许可。因此网站提供96行、覆盖完整分发瓦片的重采样概览，并保留每个原始文件下载入口与SHA256。浏览概览不能用于碰撞校验或替代原始分辨率。经纬度数据只在视图中使用局部米制近似；原始坐标不改写，该显示转换不是导航坐标或严密正射投影。

各来源垂直基准、获取时段和处理方式可能不同，尚未统一；禁止直接无缝拼接或把不同来源高度相减解释为真实变化。完整源文件范围并不代表整个城市或国家都被精细测量。

## Copernicus概览衍生物署名

produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved

produced using Copernicus WorldDEM-90 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved
