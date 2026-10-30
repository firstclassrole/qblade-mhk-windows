# QBlade MHK Windows Skill

面向小型水流发电转子的 QBlade 中文 agent skill：把选型、几何缩尺、翼型曲线、原生 Optimize、数值核查和 CAD 导出连成可追溯的流程。

整理依据包括一份大学 QBlade 教学课件、官方文档与开发者解释，以及 CE 2.0.9.7b_beta Windows 的实际操作记录。本仓库是原创方法总结，不是官方插件；未附原始课件、课程 brief、项目工程或软件安装包。

## 适合什么任务

- 三叶片水平轴轴流转子：尺寸、截面、扭角、低雷诺数 polar、BEM 初步性能。
- 升力型垂直轴/横流转子：拓扑辨认、VAWT 参数与 DMS/AC 的适用范围。
- 解释负功率、审查原生 Optimize 是否真正执行、核对导出尺寸与三叶片装配。
- 按用户规定的验收节点推进设计，保留基准与独立对照。

它不把 QBlade 当通用 CFD，也不把水轮机 BEM 当泵性能、Savonius 或半浸没水轮的验证工具。

## 安装与使用

把包含 `SKILL.md` 的整个文件夹放入你的技能目录，并保持名称为 `qblade-mhk-windows`。Codex 常见位置是 `~/.codex/skills/qblade-mhk-windows`；若已有版本，先备份并比较，再替换。

在支持该目录式 skill 的环境里，可以直接调用：

```text
使用 $qblade-mhk-windows，先读取 brief 并确认转子类型、流向和尺寸。
先完成选型，在进入水动力分析前提示我；暂不考虑轴和传动。
```

```text
使用 $qblade-mhk-windows，核查我现有工程的低Re极曲线和原生Optimize设置。
保留原始叶片，建立独立对照，不要把自动结果直接称为最优。
```

skill 本身不会安装 QBlade，也不会提供绕过许可证的 CLI。GUI 自动化需要运行环境里受支持的电脑控制工具；手动操作也可按参考文件进行。

## 内容导航

| 文件 | 内容 |
|---|---|
| [SKILL.md](SKILL.md) | agent 入口与关键约束 |
| [教学流程](references/teacher-workflow.md) | 教程各环节的用途和常见误读 |
| [物理与缩尺](references/physics-and-scaling.md) | 流向、能量、尺寸、Re与相似关系 |
| [极曲线与Optimize](references/polars-and-optimize.md) | 低Re缺点、360°、offset及实际优化记录 |
| [分析与验收](references/analysis-and-acceptance.md) | 工况、负功率、数值与物理核查 |
| [Windows操作](references/windows-gui.md) | 本机UI经验及保存核对 |
| [几何导出](references/geometry-export.md) | BLD精度、STL单位、三叶片与CAD |
| [横流布局](references/crossflow.md) | Darrieus、Savonius、水轮和冲击式的区别 |
| [来源](references/sources.md) | 官方链接、论文与经验边界 |

## 两个只读检查工具

Python 3.10及以上，无第三方运行依赖。它们不会运行 QBlade、覆盖工程或修复缺失数据。

```bash
python scripts/audit_xfoil_polar.py polar.txt --alpha-min -8 --alpha-max 12 --alpha-step 0.5 --check-alpha 4 5
python scripts/extract_qpr_bem.py --help
```

第二个工具只适合已核实的特定 HAWT archive 布局，不能读任意 QPR。细节见[分析与验收](references/analysis-and-acceptance.md)。

## 经验如何使用

本文区分三类证据：教学示范说明操作顺序；官方来源说明功能与方法；本机观察说明特定版本的实际行为。180 mm、全 NACA4412、4°以及其他案例参数只作方法示例，不是所有水轮机的推荐答案。

公开资料链接仍应随软件更新复核。通过代数检查不能代替收敛审查或实验，正稳态功率也不能保证发电机启动和加载发电。
