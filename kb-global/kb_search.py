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
# 다국어 bi-encoder (kb_index와 반드시 동일). dim=384.
MODEL_NAME = os.environ.get("KB_EMBED_MODEL",
                            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
# 다국어 cross-encoder reranker (2단계). KB_RERANK_MODEL로 override, KB_RERANK_POOL=후보 N.
RERANK_MODEL = os.environ.get("KB_RERANK_MODEL", "jinaai/jina-reranker-v2-base-multilingual")
RERANK_POOL = int(os.environ.get("KB_RERANK_POOL", "20"))


def pack(vec):
    v = vec.tolist() if hasattr(vec, "tolist") else list(vec)
    return struct.pack(f"{len(v)}f", *v)


def connect():
    import sqlite_vec
    con = sqlite3.connect(str(DB_PATH))
    con.enable_load_extension(True); sqlite_vec.load(con); con.enable_load_extension(False)
    con.row_factory = sqlite3.Row
    return con


# 프로세스 내 모델 1회 로드 캐시 (CLI는 호출당 1회라 영향 없음; eval은 다회 호출 → 가속)
_EMB = None
_CE = None


def _embedder():
    global _EMB
    if _EMB is None:
        from fastembed import TextEmbedding
        _EMB = TextEmbedding(MODEL_NAME, cache_dir=str(MODEL_CACHE))
    return _EMB


def _reranker():
    global _CE
    if _CE is None:
        from fastembed.rerank.cross_encoder import TextCrossEncoder
        _CE = TextCrossEncoder(RERANK_MODEL, cache_dir=str(MODEL_CACHE))
    return _CE


def embed_query(q):
    return pack(next(iter(_embedder().embed([q]))))


def _rerank(query, cands, k):
    """cross-encoder로 후보를 재정렬. 실패 시 bi-encoder 순서 유지(graceful fallback)."""
    if len(cands) <= 1:
        return cands[:k]
    try:
        scores = list(_reranker().rerank(query, [c["text"] for c in cands]))
        for c, s in zip(cands, scores):
            c["rerank"] = round(float(s), 4)
        cands.sort(key=lambda c: c["rerank"], reverse=True)
    except Exception as e:
        sys.stderr.write(f"[rerank skip → bi-encoder 순서] {e}\n")
    return cands[:k]


def search(con, qvec, k, filters, query=None, rerank=True, pool=None):
    # stage 1: bi-encoder + 메타필터 → 후보 pool (rerank면 N개, 아니면 k개)
    npool = (pool or RERANK_POOL) if (rerank and query) else k
    has = any(filters.get(c) for c in ("kind", "domain", "tag"))
    total = con.execute("SELECT COUNT(*) FROM vec_chunks").fetchone()[0]
    rows = con.execute("""SELECT rowid AS id, distance AS dist FROM vec_chunks
                          WHERE embedding MATCH ? ORDER BY distance LIMIT ?""",
                       (qvec, total if has else max(npool, 1))).fetchall()
    cands = []
    for r in rows:
        c = con.execute("SELECT * FROM chunks WHERE id=?", (r["id"],)).fetchone()
        if filters.get("kind") and c["kind"] != filters["kind"]: continue
        if filters.get("domain") and c["domain"] != filters["domain"]: continue
        if filters.get("tag") and filters["tag"] not in (c["tags"] or ""): continue
        cands.append({"score": round(1.0 / (1.0 + r["dist"]), 4),  # bi-encoder 점수(2차)
                      "rel": c["rel"], "title": c["title"], "heading": c["heading"],
                      "kind": c["kind"], "domain": c["domain"], "tags": c["tags"], "text": c["text"]})
        if len(cands) >= npool: break
    # stage 2: cross-encoder rerank
    if rerank and query:
        return _rerank(query, cands, k)
    return cands[:k]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query"); ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--kind"); ap.add_argument("--domain"); ap.add_argument("--tag")
    ap.add_argument("--json", action="store_true"); ap.add_argument("--full", action="store_true")
    ap.add_argument("--no-rerank", action="store_true", help="cross-encoder rerank 비활성(bi-encoder만)")
    ap.add_argument("--pool", type=int, default=RERANK_POOL, help="rerank 후보 N (기본 %d)" % RERANK_POOL)
    a = ap.parse_args()
    if not DB_PATH.exists():
        print(f"전역 인덱스 없음: {DB_PATH}\n먼저 kb_index.py 실행.", file=sys.stderr); return 2
    con = connect()
    res = search(con, embed_query(a.query), a.k,
                 {"kind": a.kind, "domain": a.domain, "tag": a.tag},
                 query=a.query, rerank=not a.no_rerank, pool=a.pool)
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2)); return 0
    if not res:
        print("결과 없음."); return 0
    for i, r in enumerate(res, 1):
        loc = r["rel"] + (f" > {r['heading']}" if r["heading"] else "")
        meta = " ".join(f"[{k}={r[k]}]" for k in ("kind", "domain") if r[k])
        sc = f"rerank={r['rerank']} (vec={r['score']})" if "rerank" in r else f"score={r['score']}"
        print(f"\n#{i}  {sc}  {loc}\n    {meta}")
        body = r["text"] if a.full else (r["text"][:300].replace("\n", " ") +
                                         ("…" if len(r["text"]) > 300 else ""))
        print("    " + body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
