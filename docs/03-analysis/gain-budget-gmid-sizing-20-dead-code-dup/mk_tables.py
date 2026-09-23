"""U-02 제안표 초안 생성 -- d_inventory.json(실측)에서 기계적으로 분류한다.

분류 규칙(설계 §에 그대로 적는다):
  R-0 저장소 전체 참조 0                      -> 삭제
  R-1 참조가 test/probe(+문서)뿐              -> tests 이관(픽스처·러너) 또는 삭제
  R-2 엔진 참조가 있으나 호출자가 D·self-test -> 사슬 통째 삭제
  R-3 참조가 workspaces 진단 스크립트뿐        -> 삭제(스크립트 처리는 사용자 확인)
  R-4 운영 경로 참조 있음                     -> 유지 + 레지스트리 등급 정정
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
items = json.load(open(os.path.join(HERE, "d_inventory.json"), encoding="utf-8"))

DEAD_TAGS = {"engine_caller_is_D", "engine_caller_is_DUP", "engine_selftest"}


def bucket(it):
    rc = it.get("ref_counts", {})
    eng = [r for r in it.get("refs_excluding_own_body", {}).get("engine", [])]
    live_eng = [r for r in eng if r.get("tag") not in DEAD_TAGS]
    non_doc = sum(v for k, v in rc.items() if k not in ("docs", "docs_md"))
    if non_doc == 0:
        return "R-0"
    if live_eng:
        return "R-4"
    if eng:
        return "R-2"
    if rc.get("workspaces") and not (rc.get("test") or rc.get("probe")):
        return "R-3"
    return "R-1"


PROPOSAL = {"R-0": "삭제", "R-1": "tests 이관", "R-2": "사슬 삭제", "R-3": "삭제(스크립트 확인)",
            "R-4": "유지·등급 정정"}

rows = []
for it in items:
    b = bucket(it)
    rc = it.get("ref_counts", {})
    d = (it.get("definitions") or [{}])[0]
    cnt = " ".join("%s %d" % (k, v) for k, v in sorted(rc.items()) if v)
    rows.append({
        "name": it.get("registry_name") or it["name"],
        "file": os.path.basename(d.get("file", "")),
        "line": d.get("lineno"),
        "lines": d.get("lines"),
        "bucket": b,
        "proposal": PROPOSAL[b],
        "refs": cnt or "0",
        "callees": ", ".join(list((d.get("engine_callees") or {}).keys())[:4]),
        "df": ", ".join(it.get("df_refs", []) if isinstance(it.get("df_refs"), list) else []),
        "dest": (it.get("registry_destination") or "").strip(),
    })

out = []
for b in ("R-0", "R-1", "R-2", "R-3", "R-4"):
    sel = [r for r in rows if r["bucket"] == b]
    out.append("\n### %s (%d) -- 제안 %s\n" % (b, len(sel), PROPOSAL[b]))
    out.append("| 함수 | 위치 | 줄수 | 참조(경로군별) | 레지스트리 이관 목적지 |")
    out.append("|---|---|---|---|---|")
    for r in sorted(sel, key=lambda x: (x["file"], x["line"] or 0)):
        out.append("| `%s` | %s:%s | %s | %s | %s |" % (
            r["name"], r["file"], r["line"], r["lines"], r["refs"], r["dest"][:60]))

md = "\n".join(out) + "\n"
open(os.path.join(HERE, "u02_tables.md"), "w", encoding="utf-8", newline="\n").write(md)
print({b: sum(1 for r in rows if r["bucket"] == b) for b in PROPOSAL})
