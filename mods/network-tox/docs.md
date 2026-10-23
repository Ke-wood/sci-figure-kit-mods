# network-tox

网络毒理：把"毒物打到的靶点"变成可解释的网络 —— 取 PPI、算拓扑、排 hub、接富集。

## 典型流程

```
靶点预测（SwissTargetPrediction / STITCH / CTD）
        ↓ 与疾病靶点取交集（UpSet / Venn）
PPI 网络（STRING，本 mod）
        ↓ 拓扑：degree / betweenness / clustering
hub 基因（本 mod）
        ↓ 富集（clusterProfiler / gseapy）
通路机制 → 毒物-靶点-通路网络图
```

## 调用

```powershell
{root}/envs/figkit/Scripts/python.exe "<skill>/mods/network-tox/templates/ppi_network.py" `
    --genes targets.txt --species 9606 --score 400 --out results
```

- `--genes`：每行一个基因符号（人用 `TP53`，鼠用 `Tp53`，斑马鱼小写）；
- `--species`：9606 人 / 10090 鼠 / 7955 斑马鱼 / 7227 果蝇；
- `--score`：STRING 置信度，400 中、700 高、150 低。

产物：`edges.csv`、`nodes.csv`（含三个拓扑指标）、`hub_genes.csv`、
`network.graphml`（Cytoscape 直接打开）、`stats.json`。

## 实测（2026-10-24，10 个靶点）

```
节点 10 / 边 16 / 孤立节点 1 / 密度 0.356
hub：TP53 > NQO1 > SOD1 > CYP1A1 > ESR1
```

STRING API v12.5，不需要 key。

## 拓扑指标怎么读

| 指标 | 含义 | 用途 |
|---|---|---|
| **degree** | 直接互作数 | 最常用的 hub 判据，但大蛋白（TP53、AKT1）天然连接多 |
| **betweenness** | 位于多少最短路径上 | 找"桥梁"节点，比 degree 更能反映调控地位 |
| **clustering** | 邻居之间互相连的比例 | 高 = 处于紧密模块内；低 = 跨模块连接子 |

**只看 degree 会把"研究得多的蛋白"当成"关键毒理靶点"。** 至少 degree + betweenness 一起看，
并在讨论里说明该偏差（文献偏倚）。

## 坑

| 坑 | 现象 | 正解 |
|---|---|---|
| 基因符号物种不匹配 | STRING 返回空或很少 | 确认物种码，人全大写、鼠首字母大写 |
| 阈值太低 | 网络成毛球，hub 无意义 | 400 起；要更严用 700 |
| 丢掉孤立节点 | 漏掉"没已知互作"的新靶点 | 本模板保留孤立节点（`n_isolated` 记在 stats） |
| 把 PPI 当因果 | 互作 ≠ 调控方向 | 结论写"关联/共表达"，别写"调控" |
| 交集用错背景 | 靶点预测阈值不同，交集大小不可比 | 固定预测阈值并写进方法 |

## 和其他 mod / 后端的配合

- 交集图：`cnsplots` 的 UpSet，或 `matplotlib-venn`；
- 富集：`clusterProfiler`（R，需注释库）或 `gseapy`（Python，离线）；
- 网络图：`networkx` 画分层（毒物-靶点-通路），或把 `network.graphml` 拖进 Cytoscape 排版。
