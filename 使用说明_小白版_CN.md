# UAV path planning terrain：小白使用说明与讲解稿

更新日期：2026-10-28。适用仓库：[hyj-234/UAV-path-planning-terrain](https://github.com/hyj-234/UAV-path-planning-terrain)。
给小白的一句话介绍

> 这是一个无人机规划研究用的地图资料库，带地图查看器、参考任务和检查工具。先看懂地图，再选择任务，最后检查算法给出的轨迹是否符合设定条件。

它不是完整无人机飞控软件，不会直接控制真实无人机，也没有收录原论文全部算法训练代码、模型和实验。网页能显示地图，不代表这张地图中所有位置都能安全飞行。

可以把三层文件理解为：

- **地图/场景**：告诉你哪里有地面、建筑、植被或桥梁。
- **任务**：告诉你几架飞机，从哪里到哪里，采用什么条件。
- **轨迹与评测**：算法给出怎么走；检查器判断是否达到该任务条件。

##  第一次打开：只看地图，不安装编程环境

两个入口：

1. [普通地形查看器](https://hyj-234.github.io/UAV-path-planning-terrain/)：看高程图和地形起伏。
2. [真实三维障碍查看器](https://hyj-234.github.io/UAV-path-planning-terrain/precision3d/index.html)：看建筑、桥面、桥墩和实测桥梁点云。

普通地图操作：

1. 选择“来源组”，再选择“数据产品”。
2. 左侧二维图用滚轮或拖框放大，工具栏手形用来平移；右侧三维图拖动旋转、滚轮缩放、右键平移。
3. 查看底部“范围、分辨率与数据来源”，先确认数据种类和适用范围。
4. 需要原始高程文件时，点击“下载官方原始GeoTIFF”。
5. 已有本地`.tif/.tiff`时，在网页中点击“打开本地GeoTIFF / JSON”选择文件；直接双击TIF可能打开系统图片程序，不是本查看器。

三维点云操作：选择苏黎世或伯明翰场景，拖动旋转、滚轮缩放。点击图例可隐藏/显示某一层，双击图例可单独查看。苏黎世可用按钮只看桥面、桥墩/拉索。

网页显示的是抽样或重采样预览，覆盖范围保持完整。放大网页不会自动增加原始测量精度。普通高程页不支持直接导入任意LAZ、PCD或CityGML；三维页目前显示仓库准备好的预览。

##  GitHub页面怎么看、怎么下载代码

打开仓库后，页面上方是文件夹和文件列表，下方展示`README.md`，相当于项目首页说明。点击文件名可以读文件；点击文件夹名进入下一层；浏览器返回键回到上一层。

下载一份到电脑：

1. 点击绿色`Code`按钮，选择`Download ZIP`。
2. 下载完成后先解压；不要只从压缩包里拖出一个`index.html`。
3. 完整保留文件夹结构，双击根目录`index.html`看普通地形，双击`precision3d/index.html`看三维障碍。
4. 如绘图库或部分在线原始文件暂时无法加载，可先使用在线入口，或按第8节准备离线依赖和原件。

下载ZIP得到代码、目录、预览和记录，**不会同时得到约2.89GB栅格原件及约1.82GB新增三维原件**。这些完整文件需要从官方源另外获取。网页预览已经随仓库提供的部分，可以先看，不必先下载全部原件。

## 根目录：每个部分是什么

|路径|人话解释|初学者什么时候需要|
|---|---|---|
|`README.md`|项目首页说明|第一个读|
|`使用说明_小白版_CN.md`|本说明和课堂讲解稿|按步骤讲解时读|
|`index.html`|普通地形网页的入口与页面结构|双击打开；想改按钮/布局时读|
|`style.css`|网页的颜色、字体和排版|想改外观时读|
|`catalog.js`|供网页使用的地图菜单与来源配置|想知道下拉框地图从哪里来时读|
|`app.js`|读取高程、组织数据、画二维/三维图、响应缩放|理解地图查看功能的主要代码|
|`load-libraries.js`|加载绘图和GeoTIFF读取库|排查绘图库加载问题时读|
|`data/demo.js`|明确标为合成的演示地形|理解显示数据结构；不要当实测|
|`data/regional/`|区域地图的压缩显示概览|用于网页预览；不要用作原始碰撞地图|
|`dataset/`|100地点、200份栅格的目录、来源、许可和检查汇总|查真实数据是什么、从哪里下载|
|`precision3d/`|真实三维增强、参考任务、检查器和端点初筛|研究低空建筑/桥梁与多机任务|
|`tools/`|下载、格式导出和栅格验证工具|需要原始文件或复跑检查时使用|
|`vendor/`|绘图/读取库和它们的许可证|一般不用改；完整离线时需要相应库|
|`tests/`|查看器开发测试及合成测试文件|开发者检查网页，不是无人机飞行实验|
|`LICENSE`|本仓库代码的MIT许可|复制代码前了解；不替代每种真实数据许可|
|`.gitignore`、`.nojekyll`|Git跟踪规则和Pages静态网站设置|初学者一般不用修改|

如果你在本机看见`.git/`、`test-results/`或`.venv/`，它们分别可能是Git历史、测试输出和Python环境，通常不是要讲解的地图原件。

## 数据说明文件怎么看

先读`dataset/README_CN.md`，再按目的打开下面文件：

|文件|内容|
|---|---|
|`dataset/catalog.json`|地点、产品和用途的总目录；区别于给网页菜单使用的根目录`catalog.js`|
|`dataset/fine_source_manifest.json`|64份精细原件的官方URL、散列、坐标、分辨率和范围|
|`dataset/global_source_manifest.json`|136份区域原件的分发地址与完整性记录|
|`dataset/planning_audit.json`|192次精细栅格参考诊断的通过、资源上限和指标|
|`dataset/regional_audit.json`|204次GLO30区域参考诊断；不是精密低空任务清单|
|`dataset/landcover_audit.json`|地类标签的辅助核对；不是人工地面真值|
|`dataset/source_anchor_corrections.json`|少数来源锚点的修正记录|

文件后缀可以这样理解：`.md`是说明书，`.html`是网页，`.css`是样式，`.js`是网页程序或数据，`.py`是Python程序，`.json`是按字段组织的配置/记录。后缀不能代替内容判断：`geometry.js`主要装显示数据，`evaluate.py`才是评测程序。

常见术语：

- **DTM**：裸地高程，一般不含建筑和树冠；城市避障不能只靠它。
- **DSM**：地物表面的高度，例如屋顶、树冠；每个水平位置只有一个高度，无法完整描述桥下。
- **点云**：大量三维测量点；没测到点的位置仍可能有障碍。
- **CityGML**：建筑等对象的三维模型格式；本批保留来源模型及其局限。
- **GeoTIFF/COG**：包含地理定位信息的栅格文件；COG适合按需读取。
- **SHA-256**：文件指纹，用来检查文件是否与记录一致；不能证明所有测量或标签都正确。

## precision3d：任务与代码怎么看

|路径|作用|
|---|---|
|`precision3d/index.html`、`viewer.js`、`load-plotly.js`|三维预览入口、绘制逻辑、绘图库加载|
|`geometry.js`、`Aqueduct_*.js`|真实几何的压缩/抽样显示数据；不建议新手直接修改|
|`source_manifest.json`、`bridge_source_manifest.json`、`source_evidence/`|真实原件来源、散列和原始来源元数据|
|`geometry_audit.json`、`bridge_geometry_audit.json`|真实几何的解析结果、分类计数和证据缺口|
|`worlds/`|场景模型：边界、障碍盒、自由空间证据和未知处理规则|
|`tasks/`|30个合成校准任务：飞机、起终点和约束|
|`example_submission.json`|一份已经准备好的双机轨迹提交|
|`evaluate.py`|检查提交轨迹，输出条件下的成功/失败与指标；不是规划算法|
|`build_tasks.py`|生成校准任务并运行三种简单参考启发式；不是论文完整外部算法集合|
|`reference_results.json`、`reference_summary.json`|90条校准参考结果及汇总；不等于真实数据性能排名|
|`candidate_tasks/`|五种机队规模的真实任务格式候选，标记未通过资格；不可直接当正式测试集|
|`endpoint_validation/`|32个真实位置的几何初筛程序、参数和全部结果；6个综合推荐候选|
|`targeted_extension_20261028/`|FRACTAL元数据定向筛选；32候选不等于32个已下载点云场景|
|`acquire.py`、`acquire_bridge.py`|下载并校验真实三维原件|
|`prepare_geometry.py`、`prepare_bridge.py`|解析真实原件，生成几何审计和显示数据|
|`protocol.json`及中文规范文档|任务约定、适用范围、可选参考参数和研究边界|
|`test_evaluate.py`、`evaluator_acceptance.json`|检查器的必要测试与结果；与真实任务资格分开|

读代码的推荐顺序：先读一个`tasks/*.json`知道题目，再读对应`worlds/*.json`知道环境，接着读`example_submission.json`知道答案格式，最后读`evaluate.py`知道怎样判分。

### 一个任务文件里的字段

以`tasks/calibration_n2_r0p25_w14.json`为例：

|字段|人话解释|
|---|---|
|`id`、`world_id`|题目编号和配套场景编号|
|`source_kind`|这里明确写合成校准，不能介绍成真实桥梁任务|
|`agents`|飞机列表；这个例子有两架|
|`radius_m`|机身球体半径，单位米|
|`start`、`goal`|三维起点和终点`[x,y,z]`|
|`initial_velocity`、`final_velocity`|起终点速度；本例均为零|
|`map_margin_m`、`tracking_margin_m`|地图误差和跟踪误差余量|
|`separation_margin_m`|两机半径之外的附加间距|
|`runtime_budget_s`|规划计算允许的时间，不是飞行时间|
|`mission_deadline_s`|任务执行截止时间|
|`speed_mps`、`acceleration_mps2`|速度、加速度上限|

本例两个起终点：

|飞机|起点(m)|终点(m)|
|---|---|---|
|uav_00|[3,-9.35,4]|[37,9.35,4]|
|uav_01|[3,9.35,4]|[37,-9.35,4]|

这是合成场景的局部坐标，不能搬到真实地图。`z=4`是该场景坐标高度；该合成地面顶面为z=1，所以离地3m。真实地图的z也应确认高程基准，不能自动当作离地高度。

提交文件中的每架飞机由若干段组成：`p`为段初位置、`v`为段初速度、`a`为加速度、`dt`为持续时间。检查器按这些信息重建运动。修改任务后必须生成对应轨迹，不能只改任务文件再拿旧答案判分。

## 8. 安装与使用：按需要选择

### A. 只浏览地图

打开第3节两个在线入口即可，不需要Python、Node.js、ROS、MATLAB或GPU。三维点云预览不等于运行无人机仿真。

### B. 下载一份代码到电脑，并准备离线库

按第4节下载ZIP并解压。以下命令以Windows PowerShell为例，假设解压目录为`D:\UAV-path-planning-terrain-main`；请换成你自己的目录。本节需要已经安装Python，三维获取/初筛脚本使用Python 3.11或以上。

在PowerShell中输入：

尚未安装Python时，可按[Python官方Windows使用说明](https://docs.python.org/3/using/windows.html)准备环境；先输入`py --version`确认命令可用。ZIP下载步骤也可参考[GitHub官方源码压缩包说明](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives)。本项目运行示例实际使用Python 3.12.14。

```powershell
cd "D:\UAV-path-planning-terrain-main"
py tools/download_vendor.py
```

该命令下载固定版本绘图和GeoTIFF读取库，不下载全部真实地形。在线地图原件仍需网络；要完全离线读取原始高程，应先下载TIF，再用网页的本地文件入口打开。保留整个仓库目录。

### C. 下载完整栅格原件

仍在仓库根目录，任选需要的一组：

```powershell
py tools/download_dataset.py fine "D:\UAV-data\fine"
py tools/download_dataset.py global "D:\UAV-data\global"
```

`fine`下载64份瑞士精细原件，`global`下载136份区域原件，合计约2.89GB。工具校验记录的散列，并在输出目录写入清单；不是下载100个城市的完整精细测量。无需为了看网页先下载这两组。

### D. 第一次运行双机示例

此步骤是最适合课堂演示的代码运行入口。先在仓库根目录建立独立Python环境，仅安装本示例所需numpy；不需要激活脚本。

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install numpy
.\.venv\Scripts\python.exe precision3d/evaluate.py precision3d/tasks/calibration_n2_r0p25_w14.json precision3d/worlds/synthetic_bridge_w14.json precision3d/example_submission.json --output my_first_result.json
```

最后一行使用已经准备好的轨迹做检查，不是在该命令中自动求出新路线。命令已在本项目当前代码中实际跑通。

打开生成的`my_first_result.json`，应看到：

```json
{
  "status": "PASS",
  "completed_agents": 2,
  "total_agents": 2,
  "task_completion_fraction": 1.0,
  "team_success": true,
  "total_path_length_m": 77.60644303149061,
  "makespan_s": 22.521288606298125
}
```

上面节选只列出部分字段。`PASS`表示在这个合成场景和约束下通过；`makespan_s`是最后一架到达时刻；`total_path_length_m`是两架总路长。`runtime_wall_s`是提交记录中的规划耗时，`evaluator_wall_s`是此次检查器耗时，两者不同；独立排名不能只相信提交者填写的耗时。

进一步运行：

```powershell
.\.venv\Scripts\python.exe precision3d/test_evaluate.py
.\.venv\Scripts\python.exe precision3d/build_tasks.py
```

第一条运行检查器验收，第二条重建30个合成任务、运行三种简单启发式并生成参考结果。后者可能生成`reference_runs/`，更新校准记录；如果没有解析真实建筑原件，会提示真实候选构建需要`prepare_geometry.py`，不妨碍合成校准完成。不要把这些运行称为外部算法完整比较。

### E. 下载和处理真实三维原件

这部分面向有Python基础的使用者，不作为第一次课堂演示必做项。当前原件约1.82GB，需要Python 3.11+：

先完成D节的`.venv`环境创建，再执行下面命令。

```powershell
.\.venv\Scripts\python.exe -m pip install numpy laspy lazrs
.\.venv\Scripts\python.exe precision3d/acquire.py
.\.venv\Scripts\python.exe precision3d/acquire_bridge.py
.\.venv\Scripts\python.exe precision3d/prepare_geometry.py
.\.venv\Scripts\python.exe precision3d/prepare_bridge.py
.\.venv\Scripts\python.exe precision3d/endpoint_validation/screen_endpoints.py
```

下载器将完整原件保存到`precision3d/raw/`，处理程序生成几何资料/审计等文件；网页已有的抽样预览与本地新生成的完整处理产物分开看。CityGML解压内容较大，处理原件需要比文件下载体积更多的内存/存储空间。端点初筛会按参考配置重新生成32个位置结果，不会自动将候选升级为起降认证。

`tools/validation/`中的精细/区域栅格诊断另需numpy、rasterio、scipy，属于进一步复现内容。第一次教学可先阅读已有审计JSON，不必启动全部数据实验。

## 自己设计任务怎么做

1. 保留原始场景，确认尺度、坐标、垂直基准和未知区域。
2. 复制一份任务，给它新ID，保持`world_id`与场景一致。
3. 修改飞机数量、尺寸、起终点或约束，记录使用的假设。点质点结果不能冒充有限尺寸飞机结果。
4. 用自己的算法生成轨迹提交，保证`task_id`、飞机ID与新任务一致；使用本检查器时需要兼容当前球体/分段常加速度模型。
5. 运行评测器，保存成功及失败，不同配置的成绩分开说明。自行设计新规则或机体模型时需要相应的检查器支持。

真实端点候选见`precision3d/endpoint_validation/endpoint_screening.json`：`ground_contact_reference_lv95_ln02_m`是地面支承参考，`airborne_departure_reference_lv95_ln02_m`是离地后的参考，`hover_reference_lv95_ln02_m`是悬停参考。它们不是三个都能直接互换的飞行坐标。`final_takeoff_status`等当前保留`UNQUALIFIED`。

##  常见问题

|现象/疑问|解释与处理|
|---|---|
|GitHub显示一大段代码，怎么打开网页？|GitHub文件页负责读代码，使用第3节Pages网址看网站；本地则解压后双击HTML|
|我下载了ZIP，为什么没有几GB的TIF/点云？|原件不随代码仓库打包；按需运行下载器或点击官方原件入口|
|地图能放很大，是否已经是高精度？|放大显示不提高源数据精度；检查目录中的分辨率和误差|
|DSM有桥面，是否能计算桥下航线？|二维高度场不能表达完整桥下分层结构；用合适三维资料并核验未知空间|
|6个候选是否已经形成3对航线？|没有，单点初筛与点对连通性是两个检查|
|`SEARCH_RESOURCE_LIMIT`是否就是无路？|不是，只表示在该搜索预算下没有完成|
|`DO_NOT_RANK`、`UNQUALIFIED`是什么意思？|未通过资格，不应作为正式成绩或已知安全任务|
|`PASS_MODEL_CONDITIONAL`是什么意思？|在声明的闭合模型假设下通过，需与观测证据赛道分开|
|Python找不到numpy？|用同一个环境的Python安装与运行；按第8节的`.venv`完整命令执行|
|脚本提示文件不存在？|先确认PowerShell当前在仓库根目录；路径有空格时加引号，保留目录结构|


> 我们提供完整范围的真实地图和可选研究任务，帮助别人快速开始和复现实验。现阶段并非所有真实地图都配齐推荐端点；真实单点候选、已经通过的合成任务及完整真实航线资格分别标识，使用时看清楚对应记录。
