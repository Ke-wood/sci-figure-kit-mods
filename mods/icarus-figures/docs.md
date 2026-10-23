# icarus-figures（包名 paperfig）

顶刊风格 Python 绘图库，约 50 个图型函数 + 自带 `paperfig.mplstyle`（MIT）。

来源：https://github.com/TAO-QKV/Icarus-Figures

## 什么时候用它

- 要的图型 cnsplots（figkit 默认）没有：raincloud、sankey、chord、
  manhattan、ternary、ridgeline、streamplot_field、hexbin_density…
- 想用 matplotlib 但要有「论文感」的默认样式

## ⚠️ 两个必须知道的点

1. **绝不能按名字 pip install paperfig。** PyPI 上的 `paperfig` 是
   `sekika/paperfig`（另一个项目，JSON 驱动拼图）。本 mod 走的是源码安装
   （pysrc），装的是本仓库的包。
2. **它装在 omicverse 环境，不在 figkit。** 调用时必须用 omicverse 的
   python，见 SKILL.md 的调用块。这样才不会顶动 figkit 里
   `matplotlib==3.10.8` 的钉版（cnsplots 要求 <3.11）。

## 用法

```python
import paperfig as pf
pf.register_style()          # 注册 paperfig 样式，之后 plt.style.use("paperfig") 可用
fig, ax = pf.raincloud(df, "value", "group")
pf.save(fig, "out.png")
```

顶层公开名见下面的实测清单；具体签名用前先
`inspect.signature(pf.<函数名>)` 实测，不要凭记忆写参数。

## 实测 API

**paperfig 顶层公开名（实测 dir()）**（2026-10-06T00:20:37+08:00 由 `mod.py verify --write-docs` 实测写入，非凭记忆）

```
LINESTYLES
MARKERS
PALETTE
STYLE_PATH
alignment_scatter
archetypes
attention_map
bar_err
bland_altman
box
bubble
calibration
chord
confusion
contour_field
convergence_curve
dendrogram
ecdf
embedding_scatter
feature_importance
forest
grouped_bar
heatmap
hexbin_density
histogram
image_panel
jointplot
manhattan
network_graph
paper_style
pareto
phase_portrait
pr_curve
qq
radar
raincloud
register_style
residual_diag
ridgeline
roc_curve
sankey
save
scatter_fit
scientific
slopegraph
sorted_bar
spectrum
streamplot_field
style
surface3d
survival
ternary
timeseries_ci
tornado
trajectory
venn2
violin
volcano
```
