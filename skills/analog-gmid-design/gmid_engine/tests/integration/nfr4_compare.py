"""NFR-4 결정성 비교기(test 쪽 도구 -- 엔진을 import 하지 않는다). interface card nfr4c2 C7, 설계 40 §2.4.13 (2)~(5).

입력 = 실행 기록 두 개(`nfr4_run_dump.py` 가 회로 하나·실행 하나마다 쓴 JSON)와 비교 종류. 출력 = 비교 보고 JSON.

실행 기록 형식(`format` = "nfr4_run_record/1"):
- `circuit`, `code_fp`(엔진 코드 지문), `searched`(탐색이 있는 실행), `env_fp` = [[기록 자리("stage_a"|"runs"), 값], ...],
  `eval_budget_source`(결과 perf 값), `stops_wall_budget`(결과 perf 값), `stop_values` = [[경로, 문자열], ...](층 0 stop·Halton 사유·ε stop·aborts·
  failed_eps·L-b stops 의 문자열 -- 전제 (나)), `context` = {grid_m, w_min_m, rails: {레일: V}, node_mos: {노드: [MOS]}, mos_tol_v: {MOS: dc_tol_v}}.
- `fields` = {경로: {"cls": D|C|K|T, "value": 값, "zone": 구역, "fp": true(값이 연속값을 담은 지문 문자열), "res": {"kind": 분해능 종류, ...}}}.
  C 값 = `float.hex` 문자열(또는 fp 지문), T 값 = `float.hex`, D·K 값 = JSON 값. 연속 칸이 정의되었는가(None·NaN·무한)는 D 다(기록 쪽이 D 로 쓴다).

판정(설계 40 §2.4.13 (2)·(5)):
- 같은 환경(두 실행 env_fp 같음·code_fp 같음) 1차 검사 `first_pass`: 비트 동일 집합(T 칸만 뺀 모든 칸)이 같으면 PASS, 하나라도 다르면 FAIL(필드별로
  넘어가지 않는다 -- C 칸이 분해능 안이어도 FAIL). env_fp·code_fp 가 다르면 이 검사를 할 수 없다(ValueError).
- 다른 환경·수치 보존 리팩터링 `fieldwise`: D 정확히 같음(아니면 FAIL), C |Δ| ≤ 분해능(같은 구역 D 가 모두 같을 때만 -- 아니면 NOT_COMPARED),
  분해능을 만들 자료가 없으면 판정 불능, K·T 는 판정 없이 보고(REPORT).
- 전제(1차 검사·필드별 공통, 두 기록 각각): (가) E_B 선언(`eval_budget_source` == "declared", 탐색이 있는 실행만), (나) 벽시계 정지 없음
  (`stops_wall_budget` == 0 이고 `stop_values` 어디에도 "wall_budget" 없음), (다) 같은 실행의 env_fp 기록이 모두 같고 단계 A 기록이 있으며, 탐색이
  있으면 runs 줄 기록이 있다. 하나라도 어기면 그 비교는 판정 불능(PASS·FAIL 아님) -- 모든 비교 칸이 판정 불능으로 세진다.
- 보고 맨 위 `undecidable` = 판정 불능 칸 수.

분해능(설계 40 §2.4.13 (4) 표를 독립 구현 -- 엔진 함수를 부르지 않는다): `resolution(field, context)`.
"""
from __future__ import annotations

import json
import sys

FORMAT = "nfr4_run_record/1"
CLASSES = ("D", "C", "K", "T")
PASS, FAIL, UNDECIDABLE, REPORT, NOT_COMPARED = "PASS", "FAIL", "UNDECIDABLE", "REPORT", "NOT_COMPARED"
DECLARED = "declared"
WALL = "wall_budget"


# ---------------------------------------------------------------- 분해능 (40 §2.4.13 (4))

def _ctx(context, key):
    v = (context or {}).get(key)
    return None if v is None else float(v)


def resolution(field, context):
    """C 칸의 분해능 -> (값 또는 None(판정 불능), 출처 문자열). field["res"] = {"kind": ...} + 종류별 인자."""
    res = dict(field.get("res") or {"kind": "unsourced"})
    kind = res.get("kind")
    if kind in ("c", "t", "margin"):
        return 1.0, {"c": "ConstraintRow.c 분해능 1", "t": "층 0 t 봉인 허용오차 한 칸", "margin": "failure.margin 허용오차 단위 1"}[kind]
    if kind == "W":
        g = _ctx(context, "grid_m")
        return g, "제조 격자 grid_m"
    if kind == "area":
        g, w = _ctx(context, "grid_m"), _ctx(context, "w_min_m")
        return (None if g is None or w is None else g * w), "b_A = grid_m x w_min_m"
    if kind == "power":
        tol = res.get("tol_i") or {}
        rails = (context or {}).get("rails") or {}
        if not tol or any(r not in rails for r in tol):
            return None, "b_P: 레일 tol_I 또는 전위 없음"
        return sum(abs(float(rails[r])) * float(t) for r, t in sorted(tol.items())), "b_P = sum_k |V_k| tol_I,k"
    if kind == "kcl":
        tol = res.get("tol_i") or {}
        if not tol:
            return None, "레일 tol_I 없음"
        return sum(float(t) for _r, t in sorted(tol.items())), "sum_k tol_I,k"
    if kind == "current":
        t = res.get("tol_i")
        return (None if t is None else float(t)), "소자 전류 tol_I"
    if kind == "metric":
        r = res.get("resolution")
        return (None if r is None else float(r)), "MetricResult.resolution"
    if kind == "theta":
        h = res.get("h")
        return (None if h is None else abs(float(h))), "그 점 FD 스텝 h_i(스냅샷 없으면 판정 불능)"
    if kind == "node_v":
        mos = ((context or {}).get("node_mos") or {}).get(res.get("node")) or []
        tv = (context or {}).get("mos_tol_v") or {}
        vals = [float(tv[m]) for m in mos if tv.get(m) is not None]
        return (min(vals) if vals else None), "노드에 채널이 닿는 MOS dc_tol_v 최솟값(MOS 없으면 판정 불능)"
    if kind == "max_decl_prop":
        decl, _src = resolution({"res": {"kind": res.get("declared")}}, context)
        prop = res.get("propagated")
        if decl is None or prop is None:
            return None, "max(선언, 감도 전파) -- 전파 없음(NFR4-F2 전 판정 불능)"
        return max(decl, float(prop)), "max(선언, 감도 전파)"
    if kind == "unsourced":
        return None, "출처 없는 칸 -- 감도 전파(NFR4-F2 전 판정 불능)"
    raise ValueError("분해능 종류를 모른다: %r" % (kind,))


# ---------------------------------------------------------------- 전제

def _env_values(record):
    return [(w, v) for w, v in record.get("env_fp") or []]


def env_of(record):
    """같은 실행의 env_fp 기록이 모두 같으면 그 값, 아니면 None."""
    vals = {v for _w, v in _env_values(record)}
    return next(iter(vals)) if len(vals) == 1 and None not in vals else None


def preconditions(record):
    """1차 검사·필드별 비교의 전제 위반 목록(빈 목록 = 전제 성립)."""
    out = []
    if record.get("format") != FORMAT:
        out.append("record_format")
    searched = bool(record.get("searched"))
    if searched and record.get("eval_budget_source") != DECLARED:                                  # (가)
        out.append("eval_budget_not_declared")
    sw = record.get("stops_wall_budget")
    if searched and sw != 0:                                                                     # (나)
        out.append("stops_wall_budget")
    for path, v in record.get("stop_values") or []:
        if isinstance(v, str) and WALL in v:
            out.append("wall_budget_stop:" + str(path))
    envs = _env_values(record)                                                                   # (다)
    if not any(w == "stage_a" and v is not None for w, v in envs):
        out.append("env_fp_missing_stage_a")
    if searched and not any(w == "runs" and v is not None for w, v in envs):
        out.append("env_fp_missing_runs")
    if len({v for _w, v in envs}) > 1:
        out.append("env_fp_differs_within_run")
    return out


# ---------------------------------------------------------------- 비교

def _fields(record):
    return dict(record.get("fields") or {})


def _hex(v):
    return float.fromhex(v) if isinstance(v, str) else float(v)


def _entry(path, cls, b, o, verdict, delta=None, res=None, source=None, note=None):
    out = {"path": path, "cls": cls, "base": None if b is None else b.get("value"), "other": None if o is None else o.get("value"),
           "delta": delta, "resolution": res, "source": source, "verdict": verdict}
    if note:
        out["note"] = note
    return out


def _cls(b, o):
    return (b or o)["cls"]


def _report(kind, fieldwise, base, other, entries, pre):
    n_und = sum(1 for e in entries if e["verdict"] == UNDECIDABLE)
    if pre["base"] or pre["other"]:
        verdict = UNDECIDABLE
    elif any(e["verdict"] == FAIL for e in entries):
        verdict = FAIL
    elif n_und:
        verdict = UNDECIDABLE
    else:
        verdict = PASS
    return {"undecidable": n_und, "verdict": verdict, "kind": kind, "fieldwise": fieldwise,
            "circuit": base.get("circuit"), "env_fp": [env_of(base), env_of(other)], "code_fp": [base.get("code_fp"), other.get("code_fp")],
            "preconditions": pre, "diffs": sorted(e["path"] for e in entries if e.get("note") == "bit_diff"),
            "fields": entries}


def _bit_diffs(fb, fo):
    out = []
    for path in sorted(set(fb) | set(fo)):
        b, o = fb.get(path), fo.get(path)
        if (b is not None and b["cls"] == "T") or (o is not None and o["cls"] == "T"):
            continue
        if b is None or o is None or b.get("cls") != o.get("cls") or b.get("value") != o.get("value") or bool(b.get("fp")) != bool(o.get("fp")):
            out.append(path)
    return out


def first_pass(base, other):
    """같은 환경·같은 코드 1차 검사(비트 동일 집합 = T 칸만 뺀 모든 칸). env_fp·code_fp 가 서로 다르면 ValueError."""
    eb, eo = env_of(base), env_of(other)
    if (eb is not None and eo is not None and eb != eo) or base.get("code_fp") != other.get("code_fp"):
        raise ValueError("1차 검사는 같은 실행 환경·같은 코드 두 실행만 비교한다: env_fp %r / %r, code_fp %r / %r"
                         % (eb, eo, base.get("code_fp"), other.get("code_fp")))
    fb, fo = _fields(base), _fields(other)
    pre = {"base": preconditions(base), "other": preconditions(other)}
    diffs = set(_bit_diffs(fb, fo))
    entries = []
    for path in sorted(set(fb) | set(fo)):
        b, o = fb.get(path), fo.get(path)
        cls = _cls(b, o)
        if cls == "T":
            entries.append(_entry(path, cls, b, o, REPORT, source="T 시간 칸 -- 비교하지 않는다"))
        elif pre["base"] or pre["other"]:
            entries.append(_entry(path, cls, b, o, UNDECIDABLE, source="전제 위반", note="bit_diff" if path in diffs else None))
        elif path in diffs:
            entries.append(_entry(path, cls, b, o, FAIL, source="비트 동일 집합", note="bit_diff"))
    return _report("same_env", False, base, other, entries, pre)


def fieldwise(base, other):
    """다른 환경·수치 보존 리팩터링의 필드별 비교. 분해능은 기준(base) 기록의 칸·context 로 만든다."""
    fb, fo = _fields(base), _fields(other)
    pre = {"base": preconditions(base), "other": preconditions(other)}
    paths = sorted(set(fb) | set(fo))
    diffs = set(_bit_diffs(fb, fo))
    if pre["base"] or pre["other"]:
        entries = [_entry(p, _cls(fb.get(p), fo.get(p)), fb.get(p), fo.get(p),
                          REPORT if _cls(fb.get(p), fo.get(p)) in ("K", "T") else UNDECIDABLE, source="전제 위반",
                          note="bit_diff" if p in diffs else None) for p in paths]
        return _report("fieldwise", True, base, other, entries, pre)
    entries = []
    bad_zones = set()
    for p in paths:                                                      # D 먼저(구역 판정)
        b, o = fb.get(p), fo.get(p)
        if _cls(b, o) != "D":
            continue
        same = b is not None and o is not None and b["cls"] == o["cls"] and b.get("value") == o.get("value")
        if not same:
            bad_zones.add((b or o).get("zone"))
        entries.append(_entry(p, "D", b, o, PASS if same else FAIL, source="이산 -- 정확히 같음", note=None if same else "bit_diff"))
    for p in paths:
        b, o = fb.get(p), fo.get(p)
        cls = _cls(b, o)
        if cls in ("K", "T"):
            entries.append(_entry(p, cls, b, o, REPORT, source="K 경로 계수 -- 보고만" if cls == "K" else "T 시간 -- 보고만",
                                  note="bit_diff" if p in diffs else None))
            continue
        if cls != "C":
            continue
        zone = (b or o).get("zone")
        if zone in bad_zones:
            entries.append(_entry(p, cls, b, o, NOT_COMPARED, source="같은 구역 D 불일치 -- C 비교 안 함",
                                  note="bit_diff" if p in diffs else None))
            continue
        if b is None or o is None or b["cls"] != o["cls"]:
            entries.append(_entry(p, cls, b, o, FAIL, source="한쪽에만 있는 연속 칸(정의 여부 = D)", note="bit_diff"))
            continue
        res, src = resolution(b, base.get("context"))
        if res is None:
            entries.append(_entry(p, cls, b, o, UNDECIDABLE, res=None, source=src, note="bit_diff" if p in diffs else None))
            continue
        if b.get("fp") or o.get("fp"):
            same = b.get("value") == o.get("value") and bool(b.get("fp")) == bool(o.get("fp"))
            entries.append(_entry(p, cls, b, o, PASS if same else UNDECIDABLE, res=res,
                                  source=src + " (지문 칸 -- 값이 다르면 |Δ| 를 잴 수 없다)", note=None if same else "bit_diff"))
            continue
        delta = abs(_hex(b["value"]) - _hex(o["value"]))
        entries.append(_entry(p, cls, b, o, PASS if delta <= res else FAIL, delta=delta, res=res, source=src,
                              note="bit_diff" if p in diffs else None))
    entries.sort(key=lambda e: e["path"])
    return _report("fieldwise", True, base, other, entries, pre)


def compare(base, other, kind):
    """kind = "same_env"(1차 검사) | "other_env" | "refactor"(필드별)."""
    if kind == "same_env":
        return first_pass(base, other)
    if kind in ("other_env", "refactor"):
        rep = fieldwise(base, other)
        rep["kind"] = kind
        return rep
    raise ValueError("비교 종류: %r" % (kind,))


def load_record(path):
    with open(path, encoding="utf-8") as f:
        rec = json.load(f)
    if rec.get("format") != FORMAT:
        raise ValueError("실행 기록 형식이 아니다: %s" % path)
    return rec


def write_report(report, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1, sort_keys=False)


def main(argv=None):
    """python nfr4_compare.py <기준 기록.json> <비교 기록.json> <same_env|other_env|refactor> <보고.json>"""
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 4:
        print(main.__doc__)
        return 2
    rep = compare(load_record(args[0]), load_record(args[1]), args[2])
    write_report(rep, args[3])
    print("%s undecidable=%d verdict=%s diffs=%d" % (rep["kind"], rep["undecidable"], rep["verdict"], len(rep["diffs"])))
    return 0 if rep["verdict"] == PASS else 1


if __name__ == "__main__":
    sys.exit(main())

