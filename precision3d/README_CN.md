公开仓库布局：本目录直接打开 `index.html`；`viewer/index.html` 指本地完整包布局。完整原件不随Git仓库分发，使用下载脚本从官方源获取；完整包保存于本地 `E:\lsy\UAV_LowAltitude_3D_Benchmark_20261028_v3`。网页保留完整范围，显示点数降采样。

# 精密低空三维多无人机规划数据与规范 v0.1

[真实起飞、悬停与降落点核验](真实起飞悬停降落点核验_CN.md)：已对32个预登记真实位置完成原始点云几何初筛，6个列入综合待复核清单；当前实机起降/悬停认证点仍为0。代码、全部失败/未知记录和筛选假设位于`endpoint_validation/`。

提供可选的参考飞机参数、低空点到点/桥下穿越/多机交叉让行/到达占位任务及成功条件。使用者可以直接使用场景，自行设计或修改任务；仅在同一组算法比较中统一任务与配置。自定义结果应注明参数和评测版本。

后续研究范围见[针对性定位与数据纳入规则](针对性定位与数据纳入规则_CN.md)。关于真实比例、飞机尺寸和具体执行任务，见[地图尺度与任务包设计](地图尺度与任务包设计_CN.md)：正式包同时提供场景、固定任务及评测器，网页缩放不改变物理尺度。

这次新增的重点是建筑立面、桥面、桥墩/拉索及真实桥梁扫描。完整原件保留，不裁剪、不用虚构建筑高度填补空白。现有100个登记地点、200份栅格数据保持原样；本增强版单独保存，不将相关文件重复计作独立场景。

## 直接使用

双击 `viewer/index.html`：可离线旋转、平移、放大真实点云；下拉选择苏黎世建筑/桥梁或伯明翰运河桥三个作者版本。图例可开关类别，按钮可只看桥面与桥墩/拉索。网页是抽样显示；完整几何在 `raw/`。

先读 `统一多无人机路径规划基准规范_CN.md`，再读 `创新点与现有基准对照_CN.md`。规范是本项目研究预发布协议，不是已获认可的行业标准。

## 数据实物与许可

|原件|内容|来源与许可|
|---|---|---|
|两份完整1km² COPC|苏黎世相邻瓦片，52,936,486点；裸地、植被、建筑屋顶/立面、桥面、桥墩/拉索、电力线等|[swissSURFACE3D](https://www.swisstopo.admin.ch/en/height-model-swisssurface3d)，[swisstopo OGD](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices)，必须署名 Federal Office of Topography swisstopo|
|完整CityGML ZIP|9,214个有坐标对象；与两块点云相交936个；保留原始屋顶、立面等几何，不是任意高度挤出|[swissBUILDINGS3D 3.0 Beta](https://www.swisstopo.admin.ch/en/landscape-model-swissbuildings3d-3-0-beta)，同上OGD条款|
|三份PCD|伯明翰运河桥原始、标注、旋转版本；同一次采集组，不能算三个独立场景|[Fang等，2025，DOI 10.17632/znxxsgn2ky.2](https://data.mendeley.com/datasets/znxxsgn2ky/2)，[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)|

六份完整原件均通过发布方SHA-256校验。`source_manifest.json`、`bridge_source_manifest.json`、`receipts/`、`source_evidence/`保留证据。OGD不是CC BY，不能将整个数据集统一改授权为CC BY或仓库代码许可证。网页点云抽样、局部平移、建筑面抽样属于本项目派生；原件本身未修改。原始PCD分别14,760,647 / 8,448,075 / 17,043,155点，后两者不是额外独立实测。

PCD头及获取的元数据未明示可核验的坐标单位与轴向，默认VIEWPOINT不证明实际扫描站。瑞士建筑与点云名义年份分别2019/2024，不能当同一时刻的无误差地图。当前桥下真实安全航线通过资格数量为0；这表示证据不足，不表示没有通道。

另核验到Calgary Inglewood Bridge的CC BY-NC 4.0扫描。因其限制商业使用，本版未下载并入可广泛复用的核心包，避免把“可下载”误当“无用途限制”。

## 可运行的统一接口

依赖：Python 3.10+，numpy；原件处理另需laspy+lazrs。当前环境路径为 `E:\lsy\paper2_FACO_PPO_DDPG\.venv\Scripts\python.exe`。重新获取原件运行 `acquire.py`、`acquire_bridge.py`，解析运行 `prepare_geometry.py`、`prepare_bridge.py`。

```powershell
python test_evaluate.py
python build_tasks.py
python evaluate.py tasks/calibration_n2_r0p25_w14.json worlds/synthetic_bridge_w14.json example_submission.json --output my_result.json
```

最后一个示例的提交格式见下面说明；可从 `reference_runs/serialized/calibration_n2_r0p25_w14.json` 取其中的 `submission` 字段另存。程序提交必须与task_id、agent IDs一一匹配，所有坐标有限，每段给出p、v、a和dt；未提交的飞机仍算失败。

`tasks/`为30个明确标为合成的协议校准任务；`reference_runs/`为三种简单启发式的90条提交与连续检查结果。它们不替代论文外部对比实验。`candidate_tasks/`为真实苏黎世的5种机队规模候选，全部标为未通过资格、不得排名；起终点只是接口样例，不是已知可飞端点。真实世界的free_boxes为空，严格评测会拒绝未知穿越。

当前启发式校准结果：无协调6/30全队成功；2秒错峰28/30；完全串行28/30。后两者的两个失败均保留，说明等待邻机仍可能冲突。三者轨迹几何本就相同，仅时间安排不同；不能据成功样本均值声称路径更短。运行时仅本地微型实现的同进程计时，不能对外部规划器做性能排名。

## 文件作用

- `geometry_audit.json`：真实点云分类计数、建筑解析和资格边界。
- `bridge_geometry_audit.json`：PCD头、范围、默认VIEWPOINT、原始标签值与尺度证据缺口。
- `geometry/building_surfaces_overlap.json`：相交区域对象的原始面环提取，包含内环；不是已认证可直接碰撞的三角网格。
- `evaluate.py`：连续时间独立检查器；球体+分段常加速度+AABB，尚无姿态/风/能耗。
- `evaluator_acceptance.json`、`browser_acceptance.json`：必要安全检查和四个离线三维场景验收。
- `reference_summary.json`：校准汇总；失败和未完成保留在分母。

## 尚欠缺的核心工作

真实桥下扫描可见性或闭合桥体证据、PCD尺度/轴向独立核验、建筑时相与拓扑/缺失面审查、更多独立城市/乡村/桥梁场景、真实任务资格与区域拆分、至少三个外部算法完整适配、外部计时与独立测试、控制器闭环验证。尚未补完的部分不能用文字润色或提高网页分辨率代替。

本版可作为真实几何资料、接口开发包与统一协议的可运行原型使用；目前不能直接当“完整且实飞认证的多无人机标准数据集”。
