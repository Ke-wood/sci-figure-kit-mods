# figwork: name=带散点的柱状图（SCI 风格）
# figwork: data=data.csv
# figwork: size=nature1
# figwork: dpi=300
# figwork: out=out.png
# figwork: vector=pdf,svg
#
# 数据契约（长表）：data.csv 需要两列 ——
#     group  分组名（字符串，重复出现）
#     value  数值
# 换成自己的列名：改下面 COLS 与 read_csv 的 usecols 即可。
#
# 这个模板示范了本 skill 的三条硬约束，改图时别把它们弄丢：
#   ① 中文必须显式设字体 + axes.unicode_minus = False（否则负号是方框）
#   ② figsize 必须**精确**等于声明的毫米数，且**不要**用 bbox_inches="tight"
#      —— tight 会把图裁窄，产物尺寸就和 front-matter 声明对不上了，
#      投稿时也就不是你要的栏宽
#   ③ 脚本里**任何地方**（含注释）都不要写出 U+2212 那个减号字符；SimHei 没有
#      它的字形。axes.unicode_minus 只管自动刻度负号，管不了你字符串里写的字。
#      渲染器对脚本做的是文本扫描，不区分代码与注释 —— 所以这里只用文字描述它，
#      不把那个字符本身写出来

import matplotlib
matplotlib.use("Agg")                      # 无头：工作台与 agent 都在无显示环境跑
import matplotlib.pyplot as plt
import pandas as pd

# ---- 中文字体（必须在任何绘图调用之前设）----
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Noto Sans SC"]
plt.rcParams["axes.unicode_minus"] = False

# ---- 矢量输出的字体设置 —— **必须在任何 savefig 之前设** ----
# matplotlib 这两个默认值都会安静地毁掉矢量图，投稿时才被打回：
#   pdf.fonttype 默认 3      = Type 3 字体，Nature/Elsevier 的作者指南明令拒收
#   svg.fonttype 默认 "path" = 所有文字被转成路径，Illustrator 里一个字都改不了
matplotlib.rcParams["pdf.fonttype"] = 42      # TrueType，可嵌入
matplotlib.rcParams["ps.fonttype"] = 42
matplotlib.rcParams["svg.fonttype"] = "none"  # 保留真 <text>，矢量里文字可编辑

# ---- 期刊尺寸（mm），要与 front-matter 的 size= 一致 ----
W_MM, H_MM, DPI = 89, 60, 300

# 色盲安全分类色板基线（Okabe-Ito）。禁用 jet / rainbow / hsv。
OKABE_ITO = ["#E69F00", "#56B4E9", "#009E73", "#F0E442",
             "#0072B2", "#D55E00", "#CC79A7", "#999999"]

# ---- 读数据。check.names 的 Python 对应物：不要改列名 ----
df = pd.read_csv("data.csv", encoding="utf-8")
GROUPS = list(dict.fromkeys(df["group"]))          # 保持出现顺序
means = df.groupby("group")["value"].mean().reindex(GROUPS)
sems = df.groupby("group")["value"].sem().reindex(GROUPS)

# ---- 作图 ----
fig, ax = plt.subplots(figsize=(W_MM / 25.4, H_MM / 25.4), dpi=DPI)
xs = range(len(GROUPS))

ax.bar(xs, means, width=.6, color="none", edgecolor="#3c4043", linewidth=.8,
       yerr=sems, capsize=2,
       error_kw={"elinewidth": .8, "ecolor": "#3c4043"})

for i, g in enumerate(GROUPS):
    pts = df.loc[df["group"] == g, "value"]
    # 固定偏移，不用随机抖动 —— 随机数会让同一张图每次都不一样，无法复现
    off = [((j % 5) - 2) * .045 for j in range(len(pts))]
    ax.scatter([i + o for o in off], pts, s=9, zorder=3,
               color=OKABE_ITO[i % len(OKABE_ITO)], label=g)

ax.set_xticks(list(xs))
ax.set_xticklabels(GROUPS)
ax.set_ylabel("测量值 (a.u.)")     # 注意：是 ASCII 连字符，不是 U+2212
ax.spines[["top", "right"]].set_visible(False)
ax.tick_params(width=.8, length=2.5)
for s in ax.spines.values():
    s.set_linewidth(.8)

fig.tight_layout()
fig.savefig("out.png", dpi=DPI)     # **不要**加 bbox_inches="tight"（见文件头）

# ---- 矢量：投稿要 PDF，进 PPT 要 SVG ----
# 同样**不要**加 bbox_inches="tight"：tight 会裁掉空白，矢量的外框就和
# front-matter 声明的毫米数对不上（矢量没有截断误差，闸门比 PNG 更严）。
fig.savefig("out.pdf")   # 投稿：字体已嵌入，换台机器不掉字
fig.savefig("out.svg")   # 进 PPT / Inkscape：文字是真 <text>，可编辑
