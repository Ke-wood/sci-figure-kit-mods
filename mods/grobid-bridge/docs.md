# grobid-bridge（文献结构化桥）

> 封装 `grobid-client-python`（PyPI 0.2.2，Apache-2.0）的桥 mod。调用 GROBID 服务，从学术 PDF 提取标题/作者/参考文献/正文结构化元数据。
>
> **requires_review = true**：本 mod 依赖外部 GROBID Java 服务，本机未部署时**不得安装**。仅作桥接草稿保留。

## 用途

针对文献语料缺口（只有目录无正文、`_meta.json` 缺书目元数据）：

- 从 PDF 提取**篇名 / 作者 / DOI / 期刊 / 参考文献**
- 批量处理文献目录，产出「篇名 / DOI / 主题」结构化表

## 实测调用（grobid-client-python 0.2.2，本机核对源码）

真实 API：

```python
from grobid_client.grobid_client import GrobidClient

# 构造参数是 grobid_server，不是 server；check_server=False 避免构造即连网抛错
client = GrobidClient(grobid_server="http://127.0.0.1:8070", check_server=False)

resp, code = client.service_status()          # 探活，code == 200 才算可用

# 单篇：service 名是第一参数（闭集见下），返回 (tei_xml, status, error)
xml, status, err = client.process_pdf("processFulltextDocument", "paper.pdf")

# 整目录批量：
client.process_paths("processFulltextDocument", ["a.pdf", "b.pdf"], output="out/")
```

service 名闭集：`processFulltextDocument` / `processHeaderDocument` /
`processReferences` / `processCitationList`。

> 注意：**没有** `process_fulltext` / `process_header` 这两个方法，构造参数也**不是** `server=`。
> 包同时还提供 CLI：`grobid_client --input papers/ --output out/ --n 10 processFulltextDocument`。

## 前置：GROBID 服务

本 mod 依赖 **GROBID Java 服务**（官方仓库 `grobidOrg/grobid`，Apache-2.0）。建议用官方容器运行，不占用 sci-figure-kit 的本机隔离环境：

```bash
docker run --rm -t -p 8070:8070 lfoppiano/grobid:full
```

服务不可用时模板降级提示并以退出码 2 结束（不会抛 traceback）。

## 数据要求

- 输入为 PDF；输出统一写 TSV（file / title / doi / authors / status）。
- 该桥只负责「结构化提取」，不做语义主题判定，主题字段需下游补齐。

## 模板

`templates/extract_corpus.py`：读一目录 PDF → 逐篇 `process_pdf` → TEI 解析 → TSV。

```bash
python templates/extract_corpus.py --input-dir papers/ --out corpus.tsv \
    --server http://127.0.0.1:8070 --service processFulltextDocument
```

## 注意事项

- 输出为文本抽取结果，仍需人工校验，勿当作已核验的元数据。
- **本机无 GROBID 服务时不要安装本 mod**；它标了 `requires_review`，`mod.py install` 会直接拒绝，这是有意的。

## 回退

服务不可用 → `pdftotext` + 正则提取；仅应急，不推荐用于正式语料库。
