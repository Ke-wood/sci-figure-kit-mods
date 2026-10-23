#!/usr/bin/env python
"""网络毒理：STRING PPI → 拓扑指标 → hub 基因 → Cytoscape 可读文件。

用法（figkit 环境）：
  {root}/envs/figkit/Scripts/python.exe ppi_network.py \
      --genes targets.txt --species 9606 --score 400 --out results

输入：每行一个基因符号（人用大写，鼠用首字母大写 + 小写其余）
输出（结果契约）：
  results/edges.csv        边表（node1, node2, score）
  results/nodes.csv        每个节点的 degree / betweenness / clustering / 是否 hub
  results/hub_genes.csv    按 degree 排序的 top-N
  results/network.graphml  Cytoscape 可直接打开
  results/stats.json       查询参数、节点/边数、输入哈希
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import pandas as pd
import requests

API = "https://string-db.org/api"


def read_genes(path: str) -> list[str]:
    out, seen = [], set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            g = line.strip().split("\t")[0].split(",")[0].strip()
            if g and not g.startswith("#") and g not in seen:
                seen.add(g)
                out.append(g)
    return out


def fetch_network(genes: list[str], species: int, score: int, timeout: int = 60) -> pd.DataFrame:
    url = f"{API}/tsv/network"
    params = {"identifiers": "\r".join(genes), "species": species,
              "required_score": score, "caller_identity": "sci-figure-kit"}
    resp = requests.post(url, data=params, timeout=timeout)
    resp.raise_for_status()
    text = resp.text.strip()
    if not text:
        return pd.DataFrame()
    from io import StringIO
    return pd.read_csv(StringIO(text), sep="\t")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--genes", required=True)
    ap.add_argument("--species", type=int, default=9606)
    ap.add_argument("--score", type=int, default=400, help="STRING 置信度阈值（400=中，700=高）")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--out", default="results")
    args = ap.parse_args()

    import networkx as nx

    genes = read_genes(args.genes)
    if len(genes) < 2:
        print("! 至少需要 2 个基因", file=sys.stderr)
        return 2

    edges = fetch_network(genes, args.species, args.score)
    if edges.empty:
        print("! STRING 没有返回任何互作 —— 降低 --score 或确认基因符号与物种", file=sys.stderr)
        return 1

    keep = ["preferredName_A", "preferredName_B", "score"]
    edges = edges[keep].rename(columns={"preferredName_A": "node1",
                                        "preferredName_B": "node2"})
    edges["score"] = pd.to_numeric(edges["score"], errors="coerce")
    edges = edges.dropna(subset=["score"])

    graph = nx.Graph()
    for row in edges.itertuples(index=False):
        graph.add_edge(row.node1, row.node2, weight=float(row.score))

    # 未连上的基因也保留为孤立节点，方便看出"打进去但没网"
    for g in genes:
        if g not in graph:
            graph.add_node(g)

    betweenness = nx.betweenness_centrality(graph, weight=None) if graph.number_of_edges() else {}
    clustering = nx.clustering(graph) if graph.number_of_edges() else {}

    nodes = pd.DataFrame([
        {
            "gene": n,
            "degree": int(graph.degree(n)),
            "betweenness": round(float(betweenness.get(n, 0.0)), 6),
            "clustering": round(float(clustering.get(n, 0.0)), 4),
        }
        for n in graph.nodes()
    ]).sort_values(["degree", "betweenness"], ascending=False)

    nodes["is_hub"] = nodes["degree"] >= max(3, nodes["degree"].quantile(0.75))
    hub = nodes[nodes["is_hub"]].head(args.top)

    os.makedirs(args.out, exist_ok=True)
    edges.to_csv(os.path.join(args.out, "edges.csv"), index=False)
    nodes.to_csv(os.path.join(args.out, "nodes.csv"), index=False)
    hub.to_csv(os.path.join(args.out, "hub_genes.csv"), index=False)
    nx.write_graphml(graph, os.path.join(args.out, "network.graphml"))

    stats = {
        "species": args.species,
        "required_score": args.score,
        "n_input": len(genes),
        "n_nodes": graph.number_of_nodes(),
        "n_edges": graph.number_of_edges(),
        "n_isolated": sum(1 for n in graph.nodes() if graph.degree(n) == 0),
        "density": round(nx.density(graph), 5) if graph.number_of_nodes() > 1 else 0,
        "top_hubs": hub["gene"].tolist()[:10],
        "input_sha256": hashlib.sha256("\n".join(genes).encode()).hexdigest(),
    }
    with open(os.path.join(args.out, "stats.json"), "w", encoding="utf-8") as fh:
        json.dump(stats, fh, ensure_ascii=False, indent=2)

    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
