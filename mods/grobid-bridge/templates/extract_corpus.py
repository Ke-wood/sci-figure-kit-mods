#!/usr/bin/env python3
"""从一目录 PDF 提取书目元数据（篇名/DOI/作者），产出 TSV。

依赖外部 GROBID 服务（Java）。真实 API（grobid-client-python 0.2.2 实测）：
    from grobid_client.grobid_client import GrobidClient
    c = GrobidClient(grobid_server="http://127.0.0.1:8070", check_server=False)
    xml, status, err = c.process_pdf("processFulltextDocument", "paper.pdf")
  服务名闭集：processFulltextDocument / processHeaderDocument / processReferences / processCitationList
  注意：**没有** process_fulltext / process_header，也没有 server= 这个构造参数。

用法：
    python extract_corpus.py --input-dir papers/ --out corpus.tsv --server http://127.0.0.1:8070
服务未起时：打印提示并以退出码 2 结束，不抛 traceback。
"""
from __future__ import annotations

import argparse
import glob
import os
import sys
import xml.etree.ElementTree as ET

TEI = "{http://www.tei-c.org/ns/1.0}"


def parse_tei(xml_text: str) -> dict:
    """从 GROBID 的 TEI-XML 里取 title / doi / authors。取不到就给空串。"""
    out = {"title": "", "doi": "", "authors": ""}
    if not xml_text:
        return out
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return out

    # 标题：titleStmt/title
    t = root.find(f".//{TEI}titleStmt/{TEI}title")
    if t is not None and t.text:
        out["title"] = " ".join(t.text.split())

    # DOI：idno[@type='DOI']
    for idno in root.iter(f"{TEI}idno"):
        if (idno.get("type") or "").upper() == "DOI" and idno.text:
            out["doi"] = idno.text.strip()
            break

    # 作者：analytic/sourceDesc 的 persName，或 biblStruct 里的 persName
    names = []
    for pers in root.iter(f"{TEI}persName"):
        parts = [p.text.strip() for p in pers
                 if p.text and p.text.strip()]
        if parts:
            names.append(" ".join(parts))
        if len(names) >= 8:
            break
    out["authors"] = "; ".join(names)
    return out


def server_alive(client) -> bool:
    """service_status() 返回 (Response, status)。任何异常都当不可用。"""
    try:
        _resp, code = client.service_status()
        return code == 200
    except Exception:
        return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="GROBID 文献结构化桥：PDF -> 书目 TSV")
    ap.add_argument("--input-dir", required=True, help="PDF 所在目录")
    ap.add_argument("--out", default="corpus.tsv", help="输出 TSV 路径")
    ap.add_argument("--server", default="http://127.0.0.1:8070", help="GROBID 服务地址")
    ap.add_argument("--service", default="processFulltextDocument",
                    choices=["processFulltextDocument", "processHeaderDocument",
                             "processReferences", "processCitationList"])
    args = ap.parse_args(argv)

    if not os.path.isdir(args.input_dir):
        print(f"找不到目录：{args.input_dir}", file=sys.stderr)
        return 2
    pdfs = sorted(glob.glob(os.path.join(args.input_dir, "*.pdf")))
    if not pdfs:
        print(f"目录里没有 PDF：{args.input_dir}", file=sys.stderr)
        return 2

    try:
        from grobid_client.grobid_client import GrobidClient
    except ImportError:
        print("未安装 grobid-client-python：pip install 'grobid-client-python>=0.2.2'",
              file=sys.stderr)
        return 2

    client = GrobidClient(grobid_server=args.server, check_server=False)
    if not server_alive(client):
        print(f"GROBID 服务不可用（{args.server}）。请先启动服务，例如：\n"
              f"  docker run --rm -t -p 8070:8070 lfoppiano/grobid:full\n"
              f"本 mod 依赖外部 Java 服务，未起服务时不应安装/使用。", file=sys.stderr)
        return 2

    rows = []
    for pdf in pdfs:
        try:
            xml, status, err = client.process_pdf(args.service, pdf, generate_ids=False)
        except Exception as exc:  # 单篇失败不拖垮整批
            rows.append((os.path.basename(pdf), "", "", "", f"ERROR:{exc}"))
            continue
        if status != 200 or not xml:
            rows.append((os.path.basename(pdf), "", "", "", f"HTTP{status}:{err or ''}"))
            continue
        meta = parse_tei(xml)
        rows.append((os.path.basename(pdf), meta["title"], meta["doi"],
                     meta["authors"], "OK"))

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("file\ttitle\tdoi\tauthors\tstatus\n")
        for r in rows:
            fh.write("\t".join(str(x).replace("\t", " ") for x in r) + "\n")

    ok = sum(1 for r in rows if r[4] == "OK")
    print(f"处理 {len(rows)} 篇，成功 {ok} 篇 -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
