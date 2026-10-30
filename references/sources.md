# 来源、版本与证据边界

整理更新：2026-10-30。适用实践版本为QBlade CE2.0.9.7b_beta Windows。本文是独立原创总结，不是官方发布；其他版本须核对界面与输出。

## 教学来源

`EG-3100 - Week 3 - QBlade`，34页大学课程教学课件。已读取全套文字，并依据原始嵌入图核对关键示例控件。只归纳工作流程和列出页码，未重新发布课件、截图、课程brief或登录后资源。公开仓库不要求取得原课件才能使用。

## 官方资料

| 来源 | 用途 |
|---|---|
| [翼型生成](https://docs.qblade.org/src/user/airfoil/airfoil.html) | NACA/圆形、导入与几何编辑 |
| [叶片定义](https://docs.qblade.org/src/user/blade/blade.html) | 站位、offset、pitch axis及多polar |
| [BEM](https://docs.qblade.org/src/user/bem/bem.html) | 三种子模块、自变量及稳态分析边界 |
| [DMS/AC](https://docs.qblade.org/src/user/bem/dms.html) | VAWT方法、流体及求解设置 |
| [坐标约定](https://docs.qblade.org/src/user/coordinates/coordinates.html) | 轴向/垂直轴pitch与坐标 |
| [MHK设置](https://docs.qblade.org/src/user/turbine/marinehydrokinetic.html) | 水物性及完整MHK模型注意点 |
| [CLI](https://docs.qblade.org/src/user/interfaces/commandline.html) | 当前文档标为EE功能 |
| [Optimize offset开发者解释](https://qblade.org/qblade-forum/topic/optimize-blade-twist-angle-distribution/) | 最大L/D攻角加相对偏移 |
| [多Re开发者解释](https://qblade.org/qblade-forum/topic/reynold-number-setting/) | 仿真按有效Re插值 |
| [攻角与叶片](https://qblade.org/qblade-forum/topic/angle-of-attack-in-blade-design/) | 真实AoA与运行/诱导条件有关 |
| [Savonius适用性回复](https://qblade.org/qblade-forum/topic/savonius-wind-turbine-simulation-in-qblade/) | 分离阻力转子不宜用该升力方法验证 |

当前官方手册与本机行为存在描述差异时，明确两者及版本，不用旧源码代替当前实现。[官方源码说明](https://qblade.org/qblade-forum/topic/request-for-qbladece-2-0-9-2-full-source-package-for-non-commercial-research/)也提示公开源码版本与当前执行文件不一定一致。

## 文献与技术分类

- [Scandura等，JMSE2026，14(3):236](https://doi.org/10.3390/jmse14030236)：参考叶轮、解析初形与BEM修正的区分；论文参数不是所有小转子的最佳参数。
- [Whelan等，2009](https://doi.org/10.1017/S0022112009005916)：自由液面与阻塞效应。
- [DOE水轮机类型](https://www.energy.gov/cmei/water/types-hydropower-turbines)：喷嘴冲击式与其他布局的区分。

## 本机观察及其限制

已观察：原生foil/polar/BLD导入、XFOIL批次与有限角度导出、两种原生Betz扭角设置、独立对象保存、BLD精度、STL尺度检查，以及先前HAWT保存数组的物理恒等式。

本机案例不是可推广的实验证据。特别是“17°再偏移−13°”、UI显示舍入、保存复制行为、圆盘归一化及archive布局，均有具体版本/案例范围。公开仓库保留可重复的方法和代码，不附私人工作工程，也不声称新的D180水动力性能已经通过。

课件对流程的示范、官方资料对功能的说明、我们的工程判断应分别表述。不得把以往被撤回的原型身份或探索曲线写成已验收结果。
