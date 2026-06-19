#!/usr/bin/env python3
"""전역 장기지식 RAG 검색 (L4-global) — fpga 전 프로젝트 공유.

증류된 일반 원칙(failure-taxonomy, RTL 패턴, 방법론)을 의미검색 + 메타필터로 회수.
프로젝트 어디서든 호출 가능 (단기 프로젝트 지식은 각 프로젝트 graphify로).

Usage:
    "$KB_PY" .tools/kb-global/kb_search.py "fifo pointer wrap" -k 5
    "$KB_PY" .tools/kb-global/kb_search.py "deadlock" --kind pattern --json
"""
from __future__ import annotations
import argparse, json, os, sqlite3, struct, sys
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        try: _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception: pass

HERE = Path(__file__).resolve().parent
WS = HERE.parents[1]                               # fpga 워크스페이스 (위치 무관)
DB_PATH = WS / ".tools" / "kb-global" / "kb.sqlite"   # 인덱스는 런타임(재생성)
MODEL_CACHE = Path(os.environ.get("KB_MODEL_CACHE", WS / ".tools" / "hf-cache"))
MODEL_NAME = "BAAI/bge-small-en-v1.5"


def pack(vec):
    v = vec.tolist() if hasattr(vec, "tolist") else list(vec)
    return struct.pack(f"{len(v)}f", *v)


def connect():
    import sqlite_vec
    con = sqlite3.connect(str(DB_PATH))
    con.enable_load_extension(True); sqlite_vec.load(con); con.enable_load_extension(False)
    con.row_factory = sqlite3.Row
    return con


def embed_query(q):
    from fastembed import TextEmbedding
    return pack(next(iter(TextEmbedding(MODEL_NAME, cache_dir=str(MODEL_CACHE)).embed([q]))))


def search(con, qvec, k, filters):
    has = any(filters.get(c) for c in ("kind", "domain", "tag"))
    total = con.execute("SELECT COUNT(*) FROM vec_chunks").fetchone()[0]
    rows = con.execute("""SELECT rowid AS id, distance AS dist FROM vec_chunks
                          WHERE embedding MATCH ? ORDER BY distance LIMIT ?""",
                       (qvec, total if has else max(k, 1))).fetchall()
    out = []
    for r in rows:
        c = con.execute("SELECT * FROM chunks WHERE id=?", (r["id"],)).fetchone()
        if filters.get("kind") and c["kind"] != filters["kind"]: continue
        if filters.get("domain") and c["domain"] != filters["domain"]: continue
        if filters.get("tag") and filters["tag"] not in (c["tags"] or ""): continue
        out.append({"score": round(1.0 / (1.0 + r["dist"]), 4),
                    "rel": c["rel"], "title": c["title"], "heading": c["heading"],
                    "kind": c["kind"], "domain": c["domain"], "tags": c["tags"], "text": c["text"]})
        if len(out) >= k: break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query"); ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--kind"); ap.add_argument("--domain"); ap.add_argument("--tag")
    ap.add_argument("--json", action="store_true"); ap.add_argument("--full", action="store_true")
    a = ap.parse_args()
    if not DB_PATH.exists():
        print(f"전역 인덱스 없음: {DB_PATH}\n먼저 kb_index.py 실행.", file=sys.stderr); return 2
    con = connect()
    res = search(con, embed_query(a.query), a.k,
                 {"kind": a.kind, "domain": a.domain, "tag": a.tag})
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2)); return 0
    if not res:
        print("결과 없음."); return 0
    for i, r in enumerate(res, 1):
        loc = r["rel"] + (f" > {r['heading']}" if r["heading"] else "")
        meta = " ".join(f"[{k}={r[k]}]" for k in ("kind", "domain") if r[k])
        print(f"\n#{i}  score={r['score']}  {loc}\n    {meta}")
        body = r["text"] if a.full else (r["text"][:300].replace("\n", " ") +
                                         ("…" if len(r["text"]) > 300 else ""))
        print("    " + body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
