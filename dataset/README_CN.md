# 多场景真实地形数据集：首批

完成32个登记地点、64个完整官方瓦片，约408MB。每地点包含DTM 2m与DSM 0.5m；原始GeoTIFF在raw文件夹，未自行裁剪500米窗口。viewer/index.html可离线浏览，数据目录.csv可检索来源。

场景：城市8、山地6、农村6、森林6、湖泊河流6。地点名和场景属于预声明语境标签，尚未由独立地类掩膜逐像元审核。混合场景和地理邻近必须保留；32个登记地点不等于32个统计独立样本。未来划分应按geographic_cluster隔离，不把同一地点的两种高程分到不同划分。

来源：Source: Federal Office of Topography swisstopo。遵守swisstopo OGD条款并保留来源；不是CC BY或本项目MIT代码许可。生产数据来自官方STAC，不使用仅限测试的sample文件。全部64个下载文件与官方SHA256一致，原始文件未改写；校验不能替代测量精度的独立验证。

DSM包括建筑和植被，DTM为裸地。年份记录为STAC名义产品时间；两者不保证同年，不能相减后当作灾前灾后变化或直接宣称真实树高。缺测保持缺测，没有填补。

当前均为瑞士官方数据，仍有地理覆盖偏倚。海岸、荒漠和更多国家是后续扩充方向，尚未完成；不能把规划数量当作现有数量。原变化地形10来源组继续单独保留，尚未重新完成来源许可和精度审查，不与本批64份静态产品混作同一质量等级。

这是独立的探索数据集建设；没有创建无人机飞行结果，没有改动原论文冻结任务或模型，没有打开Ben Nevis、Toubkal、Drakensberg、Torres del Paine或Jotunheimen留出地形。正式训练/验证/测试划分和飞行任务仍待另行冻结。

官方资料：
- https://www.swisstopo.admin.ch/en/height-model-swisssurface3d-raster
- https://www.swisstopo.admin.ch/en/height-model-swissalti3d
- https://www.swisstopo.admin.ch/en/faq-free-geodata

在线目录提供官方原始下载地址与校验值；不在Git仓库中重复保存约408MB原始GeoTIFF。
