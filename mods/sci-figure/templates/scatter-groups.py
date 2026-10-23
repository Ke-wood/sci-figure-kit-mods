# figwork: name=分组散点 + 拟合线
# figwork: data=data.csv
# figwork: size=nature2
# figwork: dpi=300
# figwork: out=out.png
# figwork: vector=pdf,svg
#
# 数据契约（长表）：data.csv 需要三列 ——
#     x, y    数值
#     group   分组名
#
# 双栏 183mm 是给「一组散点 + 一个图例」留的宽度；只要单栏就把 front-matter
# 改成 size=nature1 并把下面的 W_MM 改成 89（**两处都要改** —— 只改一处
# 渲染器会在尺寸闸门上报 FAIL，这正是那道闸门存在的意义）。

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Noto Sans SC"]
plt.rcParams["axes.unicode_minus"] = False

# ---- 矢量输出的字体设置 —— **必须在任何 savefig 之前设** ----
# matplotlib 这两个默认值都会安静地毁掉矢量图：pdf.fonttype 默认 3 是 Type 3
# 字体（Nature/Elsevier 作者指南明令拒收），svg.fonttype 默认 "path" 会把
# 所有文字转成路径（Illustrator 里一个字都改不了）。
matplotlib.rcParams["pdf.fonttype"] = 42      # TrueType，可嵌入
matplotlib.rcParams["ps.fonttype"] = 42
matplotlib.rcParams["svg.fonttype"] = "none"  # 保留真 <text>，矢量里文字可编辑

W_MM, H_MM, DPI = 183, 60, 300
OKABE_ITO = ["#E69F00", "#56B4E9", "#009E73", "#F0E442",
             "#0072B2", "#D55E00", "#CC79A7", "#999999"]

df = pd.read_csv("data.csv", encoding="utf-8")
GROUPS = list(dict.fromkeys(df["group"]))

fig, ax = plt.subplots(figsize=(W_MM / 25.4, H_MM / 25.4), dpi=DPI)

for i, g in enumerate(GROUPS):
    sub = df[df["group"] == g]
    ax.scatter(sub["x"], sub["y"], s=10, alpha=.85, linewidths=0,
               color=OKABE_ITO[i % len(OKABE_ITO)], label=g, zorder=3)
    if len(sub) >= 3:                       # 两个点拟合不出斜率，直接跳过
        k, b = np.polyfit(sub["x"], sub["y"], 1)
        xr = np.linspace(sub["x"].min(), sub["x"].max(), 50)
        ax.plot(xr, k * xr + b, linewidth=.9, color=OKABE_ITO[i % len(OKABE_ITO)])

ax.set_xlabel("自变量")
ax.set_ylabel("因变量")
ax.legend(frameon=False, fontsize=7, loc="best")
ax.spines[["top", "right"]].set_visible(False)
for s in ax.spines.values():
    s.set_linewidth(.8)
ax.tick_params(width=.8, length=2.5)

fig.tight_layout()
fig.savefig("out.png", dpi=DPI)

# ---- 矢量：投稿要 PDF，进 PPT 要 SVG ----
# 不加 bbox_inches="tight"：tight 会让矢量外框与声明的毫米数对不上，
# 而矢量没有截断误差，尺寸闸门比 PNG 更严。
fig.savefig("out.pdf")   # 投稿：字体已嵌入
fig.savefig("out.svg")   # 进 PPT / Inkscape：文字可编辑
