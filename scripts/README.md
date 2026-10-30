# 只读检查工具

`audit_xfoil_polar.py`检查有限迎角表的保存覆盖、缺角及指定攻角支撑；不求解、不补点，不证明收敛。

`extract_qpr_bem.py`仅用于已核实的HAWT Rotor BEM archive310043十数组布局。优先原生导出；不支持VAWT/DMS/AC，也不解释未核实的弯矩列。

两者只需Python3.10及以上的标准库。输出写入独立分析目录，保留原始输入；运行前用`--help`查看参数，详细边界见[分析与验收](../references/analysis-and-acceptance.md)。
