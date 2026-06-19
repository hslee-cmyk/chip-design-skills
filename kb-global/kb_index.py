#!/usr/bin/env python3
"""전역 장기지식 RAG 인덱서 (L4-global) — fpga 전 프로젝트 공유.

증류된 일반 원칙만 색인한다 (특정 프로젝트 버그 instance 아님):
  principles/**/*.md  — failure-taxonomy(T1..T9), 일반화 RTL 패턴, 방법론.

프로젝트 단기지식(모듈 분석·설계·프로젝트 버그)은 각 프로젝트 graphify(L3)가 담당.
승격: 프로젝트 docs/solutions 패턴이 일반화되면 principles/ 로 격상 후 재색인.

스택: 공유 venv(graphifyy/fastembed/sqlite-vec), 공유 모델캐시 ../hf-cache.

Usage:
    "$KB_PY" .tools/kb-global/kb_index.py            # 증분
    "$KB_PY" .tools/kb-global/kb_index.py --rebuild
"""
from __future__ import annotations
import hashlib, os, re, sqlite3, struct, sys
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        try: _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception: pass

HERE = Path(__file__).resolve().parent
# 위치 무관: 런타임(.tools/kb-global)이든 정본(chip-design-skills/kb-global)이든 parents[1]=workspace.
WS = HERE.parents[1]                               # fpga 워크스페이스
KIT = WS / "chip-design-skills"
# 정본 코퍼스를 직접 색인 (런타임에 principles 복사본을 두지 않는다 → 단일 정본·유실 불가).
PRINCIPLES = Path(os.environ.get("KB_PRINCIPLES", KIT / "kb-global" / "principles"))
TAXONOMY = KIT / "agent-kit" / "failure-taxonomy.md"   # 정본 taxonomy 직접 색인
DB_PATH = WS / ".tools" / "kb-global" / "kb.sqlite"    # 인덱스는 런타임(재생성)
MODEL_CACHE = Path(os.environ.get("KB_MODEL_CACHE", WS / ".tools" / "hf-cache"))
MODEL_NAME = "BAAI/bge-small-en-v1.5"
DIM = 384
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def parse_fm(text):
    m = FM_RE.match(text)
    body = text[m.end():] if m else text
    if not m: return {}, body
    try:
        import yaml; fm = yaml.safe_load(m.group(1)) or {}
    except Exception: fm = {}
    return (fm if isinstance(fm, dict) else {}), body


def split_sections(body):
    parts = re.split(r"(?m)^(##\s+.+)$", body)
    out = []
    if parts[0].strip(): out.append(("", parts[0].strip()))
    for i in range(1, len(parts), 2):
        heading = parts[i].lstrip("#").strip()
        text = (parts[i] + parts[i + 1]).strip() if i + 1 < len(parts) else parts[i].strip()
        if text: out.append((heading, text))
    return out or [("", body.strip())]


def pack(vec):
    v = vec.tolist() if hasattr(vec, "tolist") else list(vec)
    return struct.pack(f"{len(v)}f", *v)


def connect():
    import sqlite_vec
    con = sqlite3.connect(str(DB_PATH))
    con.enable_load_extension(True); sqlite_vec.load(con); con.enable_load_extension(False)
    return con


def init_schema(con):
    con.execute("CREATE TABLE IF NOT EXISTS files(rel TEXT PRIMARY KEY, file_hash TEXT)")
    con.execute("""CREATE TABLE IF NOT EXISTS chunks(
        id INTEGER PRIMARY KEY, rel TEXT, title TEXT, heading TEXT,
        kind TEXT, domain TEXT, tags TEXT, text TEXT)""")
    con.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(embedding float[{DIM}])")


def del_chunks(con, rel):
    for (cid,) in con.execute("SELECT id FROM chunks WHERE rel=?", (rel,)).fetchall():
        con.execute("DELETE FROM vec_chunks WHERE rowid=?", (cid,))
    con.execute("DELETE FROM chunks WHERE rel=?", (rel,))


def main():
    rebuild = "--rebuild" in sys.argv
    MODEL_CACHE.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if rebuild and DB_PATH.exists(): DB_PATH.unlink()
    if not PRINCIPLES.exists():
        print(f"정본 코퍼스 없음: {PRINCIPLES}\n"
              f"(chip-design-skills repo가 워크스페이스에 있어야 함, 또는 KB_PRINCIPLES 지정)")
        return 2
    con = connect(); init_schema(con)

    # 정본 principles/*.md + 정본 taxonomy 를 직접 색인 (rel = 파일명, 위치 무관)
    files = list(PRINCIPLES.rglob("*.md"))
    if TAXONOMY.exists(): files.append(TAXONOMY)
    on_disk = {p.name: (p, sha256(p)) for p in sorted(set(files))}
    indexed = {r: h for r, h in con.execute("SELECT rel, file_hash FROM files")}
    for rel in list(indexed):
        if rel not in on_disk:
            del_chunks(con, rel); con.execute("DELETE FROM files WHERE rel=?", (rel,))
            print(f"[del] {rel}")
    todo = [(rel, p, h) for rel, (p, h) in on_disk.items() if indexed.get(rel) != h]
    if not todo:
        con.commit()
        n = con.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        print(f"변경 없음. 전역 원칙 청크 {n}개. ({DB_PATH})"); return 0

    pending = []
    for rel, p, h in todo:
        fm, body = parse_fm(p.read_text(encoding="utf-8", errors="replace"))
        title = (H1_RE.search(body).group(1).strip() if H1_RE.search(body) else p.stem)
        kind = str(fm.get("kind", "") or ""); domain = str(fm.get("domain", "") or "")
        tags = ",".join(fm.get("tags", []) if isinstance(fm.get("tags"), list) else [])
        for heading, sect in split_sections(body):
            pending.append((rel, h, title, heading, kind, domain, tags, sect))

    print(f"임베딩: 파일 {len(todo)} → 청크 {len(pending)}. 모델 로드...")
    from fastembed import TextEmbedding
    emb = TextEmbedding(MODEL_NAME, cache_dir=str(MODEL_CACHE))
    vecs = list(emb.embed([f"{c[2]} :: {c[3]}\n{c[7]}" for c in pending]))
    for rel in {t[0] for t in todo}: del_chunks(con, rel)
    for c, vec in zip(pending, vecs):
        cur = con.execute("""INSERT INTO chunks(rel,title,heading,kind,domain,tags,text)
                             VALUES(?,?,?,?,?,?,?)""", (c[0], c[2], c[3], c[4], c[5], c[6], c[7]))
        con.execute("INSERT INTO vec_chunks(rowid,embedding) VALUES(?,?)", (cur.lastrowid, pack(vec)))
    for rel, p, h in todo:
        con.execute("INSERT INTO files(rel,file_hash) VALUES(?,?) "
                    "ON CONFLICT(rel) DO UPDATE SET file_hash=excluded.file_hash", (rel, h))
    con.commit()
    total = con.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    print(f"완료: {len(pending)} 청크. 총 {total}. ({DB_PATH})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
