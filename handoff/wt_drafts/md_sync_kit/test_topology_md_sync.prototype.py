"""library 추적 topology.md 표 <-> json connectivity 일치 계약(20261001-topology-md-sync, 백로그 B47).

[오케스트레이터 사전 시험용 프로토타입 -- 커밋하지 않는다. 실제 test는 gmid-test-author가 card만으로 쓴다.]

spec card `docs/02-design/specs/20261001-topology-md-sync.spec.md` 계약 1~5·7을 판정한다(계약 6·8·9는 auditor 측정).
판정 대상 = `A/library/` 바로 아래 `*.topology.md` 전부. 기대값은 같은 이름의 json을 `json`으로 읽은 데이터에서만
만든다 -- md 생성 스크립트·topology 로더를 import·실행하지 않는다(계약 6).

oracle 대조(계획 N3.12.3):

* test_mdsync_library_has_md -- (d) card 계약 1 (a): 판정 대상 md가 1개 이상(빈 판정 금지).
* test_mdsync_library_tables_match_json -- (d) 판정 시점 `A/library/<n>.topology.json`(사용자 승인 connectivity 원본)에서
  card 계약 2~5 정의대로 만든 기대값. 표 형식(머리·셀·`t<i>`·합계 문형)은 card 문장.
* test_mdsync_selfcheck_* -- (a) 판정기 자기 점검: card '거부해야 할 입력'의 합성 md·json 짝. 실패 계약 집합이 괄호의
  집합과 정확히 같은지(거부)·빈 집합인지(통과)를 본다.
"""
import collections
import json
import pathlib
import re

import pytest

# contracts -> tests -> assets(A)
_MDSYNC_LIB = pathlib.Path(__file__).resolve().parents[2] / "library"

_MDSYNC_WARN = " ⚠️"
_MDSYNC_INFO = " ℹ️"
_MDSYNC_H_DEV = "| Name | Kind | Source | Drain | Gate |"
_MDSYNC_H_PAS = "| Name | Kind | Terminals |"
_MDSYNC_H_SRC = "| Name | Kind | Terminals | Value | Implementable |"
_MDSYNC_H_NET = "| Net | 연결된 단자 (device.terminal) | 단자 수 |"
_MDSYNC_SEC_DEV = "## 소자별 연결 표"
_MDSYNC_SEC_PAS = "## 수동 소자 표"
_MDSYNC_SEC_SRC = "## ⚡ Ideal source 표"
_MDSYNC_SEC_NET = "## Net별 연결 표"
_MDSYNC_TOTAL_RE = re.compile(r"총 (\d+)개 소자 \+ (\d+)개 수동소자 \+ (\d+)개 ideal source, (\d+)개 net\.")
_MDSYNC_BT_RE = re.compile(r"`([^`]*)`")
_MDSYNC_NET_RE = re.compile(r"`([^`]*)`(" + _MDSYNC_WARN + "|" + _MDSYNC_INFO + ")?")
_MDSYNC_DEV_KEYS = ("name", "kind", "source", "drain", "gate")


# ---------- 파싱 ----------
def _mdsync_lines(text):
    return text.replace("\r\n", "\n").split("\n")


def _mdsync_cells(row):
    s = row.strip()
    if not (s.startswith("|") and s.endswith("|")) or len(s) < 2:
        raise ValueError(f"표 행 형식 아님: {row!r}")
    return [c.strip() for c in s[1:-1].split("|")]


def _mdsync_bt(cell):
    m = _MDSYNC_BT_RE.fullmatch(cell)
    if m is None:
        raise ValueError(f"백틱 셀 아님: {cell!r}")
    return m.group(1)


def _mdsync_heads(lines, prefix):
    return [i for i, ln in enumerate(lines) if ln.startswith(prefix)]


def _mdsync_table(lines, prefix, header):
    """'<prefix>로 시작하는 절'의 표 데이터 행(셀 목록들). 절 0개·2개 이상·표 없음·머리 다름·열 수 다름은 ValueError."""
    heads = _mdsync_heads(lines, prefix)
    if len(heads) != 1:
        raise ValueError(f"{prefix!r} 절 {len(heads)}개")
    i = heads[0] + 1
    while i < len(lines) and not lines[i].startswith("|"):
        if lines[i].startswith("## "):
            raise ValueError(f"{prefix!r} 절에 표 없음")
        i += 1
    if i >= len(lines):
        raise ValueError(f"{prefix!r} 절에 표 없음")
    j = i
    while j < len(lines) and lines[j].startswith("|"):
        j += 1
    rows = lines[i:j]
    if rows[0] != header:
        raise ValueError(f"{prefix!r} 표 머리 다름: {rows[0]!r}")
    ncol = len(_mdsync_cells(header))
    out = []
    for r in rows[2:]:
        cells = _mdsync_cells(r)
        if len(cells) != ncol:
            raise ValueError(f"{prefix!r} 열 수 {len(cells)} != {ncol}: {r!r}")
        out.append(cells)
    return out


def _mdsync_terms(cell):
    return () if cell == "" else tuple(_mdsync_bt(x) for x in cell.split(", "))


# ---------- json 쪽 기대값 ----------
def _mdsync_T(j, load_linked):
    elems = list(j["netlist"])
    for f in j.get("linked_topology_files") or []:
        elems.extend(load_linked(f)["netlist"])
    for d in elems:
        if not isinstance(d, dict) or any(k not in d for k in _MDSYNC_DEV_KEYS):
            raise ValueError(f"netlist 원소 형식 위반: {d!r}")
    return elems


def _mdsync_P(j):
    return list(j.get("passive_elements") or [])


def _mdsync_S(j):
    return list(j.get("ideal_sources") or [])


def _mdsync_N(j, load_linked):
    n = collections.defaultdict(collections.Counter)
    for d in _mdsync_T(j, load_linked):
        for t in ("source", "drain", "gate"):
            n[d[t]][(d["name"], t)] += 1
    for e in _mdsync_P(j) + _mdsync_S(j):
        for i, net in enumerate(e.get("terminals") or []):
            n[net][(e["name"], f"t{i}")] += 1
    return n


# ---------- 계약 판정기(각각 사유 문자열 목록) ----------
def _mdsync_c1(n, lines, j):
    out = []
    if j.get("topology_name") != n:
        out.append(f"json topology_name {j.get('topology_name')!r} != {n!r}")
    h1 = _mdsync_heads(lines, "# ")
    want = f"# {n} -- topology connectivity table"
    if len(h1) != 1 or lines[h1[0]] != want:
        out.append(f"H1 {[lines[i] for i in h1]!r} != {want!r}")
    return out


def _mdsync_c2(n, lines, j, load_linked):
    rows = _mdsync_table(lines, _MDSYNC_SEC_DEV, _MDSYNC_H_DEV)
    got = collections.Counter((r[0], r[1], _mdsync_bt(r[2]), _mdsync_bt(r[3]), _mdsync_bt(r[4])) for r in rows)
    want = collections.Counter(tuple(d[k] for k in _MDSYNC_DEV_KEYS) for d in _mdsync_T(j, load_linked))
    if got != want:
        return [f"소자 표 md만 {sorted((got - want).elements())} json만 {sorted((want - got).elements())}"]
    return []


def _mdsync_side_table(lines, elems, prefix, header, what):
    if not elems:
        k = len(_mdsync_heads(lines, prefix))
        return [f"{what} 비었는데 {prefix!r} 절 {k}개"] if k else []
    rows = _mdsync_table(lines, prefix, header)
    got = collections.Counter((r[0], r[1], _mdsync_terms(r[2])) for r in rows)
    want = collections.Counter((e["name"], e.get("kind", "?"), tuple(e.get("terminals") or [])) for e in elems)
    if got != want:
        return [f"{what} 표 md만 {sorted((got - want).elements())} json만 {sorted((want - got).elements())}"]
    return []


def _mdsync_c3(n, lines, j):
    return (_mdsync_side_table(lines, _mdsync_P(j), _MDSYNC_SEC_PAS, _MDSYNC_H_PAS, "passive_elements")
            + _mdsync_side_table(lines, _mdsync_S(j), _MDSYNC_SEC_SRC, _MDSYNC_H_SRC, "ideal_sources"))


def _mdsync_c4(n, lines, j, load_linked):
    rows = _mdsync_table(lines, _MDSYNC_SEC_NET, _MDSYNC_H_NET)
    want = _mdsync_N(j, load_linked)
    out, seen = [], collections.Counter()
    for r in rows:
        m = _MDSYNC_NET_RE.fullmatch(r[0])
        if m is None:
            raise ValueError(f"Net 셀 형식 아님: {r[0]!r}")
        net = m.group(1)
        seen[net] += 1
        pieces = r[1].split(", ")
        got = collections.Counter()
        for p in pieces:
            dev, dot, term = p.rpartition(".")
            if not dot:
                raise ValueError(f"단자 조각에 '.' 없음: {p!r}")
            got[(dev, term)] += 1
        if got != want.get(net, collections.Counter()):
            out.append(f"net {net!r} 단자 md {sorted(got.elements())} json {sorted(want.get(net, collections.Counter()).elements())}")
        if int(r[2]) != len(pieces):
            out.append(f"net {net!r} 단자 수 {r[2]} != 조각 {len(pieces)}")
    if set(seen) != set(want):
        out.append(f"net 집합 md만 {sorted(set(seen) - set(want))} json만 {sorted(set(want) - set(seen))}")
    rep = sorted(k for k, v in seen.items() if v > 1)
    if rep:
        out.append(f"net 행 중복 {rep}")
    return out


def _mdsync_c5(n, lines, j, load_linked):
    tl = [ln for ln in lines if ln.startswith("총 ")]
    if len(tl) != 1:
        raise ValueError(f"합계 줄 {len(tl)}개")
    m = _MDSYNC_TOTAL_RE.fullmatch(tl[0])
    if m is None:
        raise ValueError(f"합계 줄 문형 다름: {tl[0]!r}")
    got = tuple(int(x) for x in m.groups())
    want = (len(_mdsync_T(j, load_linked)), len(_mdsync_P(j)), len(_mdsync_S(j)), len(_mdsync_N(j, load_linked)))
    return [f"합계 {got} != json {want}"] if got != want else []


def _mdsync_judge(n, md_text, j, load_linked):
    """md 하나의 실패 쌍 목록 [(계약, n, 사유)]. j is None = 짝 json 없음(계약 1 (b), 2~5 판정 안 함)."""
    if j is None:
        return [(1, n, "짝 json 없음")]
    lines = _mdsync_lines(md_text)
    fails = []
    checks = ((1, lambda: _mdsync_c1(n, lines, j)),
              (2, lambda: _mdsync_c2(n, lines, j, load_linked)),
              (3, lambda: _mdsync_c3(n, lines, j)),
              (4, lambda: _mdsync_c4(n, lines, j, load_linked)),
              (5, lambda: _mdsync_c5(n, lines, j, load_linked)))
    for k, fn in checks:
        try:
            reasons = fn()
        except (ValueError, KeyError, IndexError) as e:
            reasons = [f"파싱 실패: {type(e).__name__}: {e}"]
        fails.extend((k, n, r) for r in reasons)
    return fails


def _mdsync_md_names(lib):
    return sorted(p.name[: -len(".topology.md")] for p in lib.glob("*.topology.md") if p.is_file())


def _mdsync_judge_dir(lib):
    names = _mdsync_md_names(lib)
    if not names:
        return [(1, "-", "판정 대상 md 0개")]

    def load_linked(fname):
        p = lib / fname
        if not p.is_file():
            raise ValueError(f"linked_topology_files 파일 없음: {fname}")
        with p.open(encoding="utf-8") as f:
            return json.load(f)

    fails = []
    for n in names:
        md_text = (lib / f"{n}.topology.md").read_bytes().decode("utf-8")
        jp = lib / f"{n}.topology.json"
        j = None
        if jp.is_file():
            with jp.open(encoding="utf-8") as f:
                j = json.load(f)
        fails.extend(_mdsync_judge(n, md_text, j, load_linked))
    return fails


def _mdsync_message(fails):
    return "\n".join(f"계약 {k} {n}: {r}" for k, n, r in fails)


# ---------- 실제 library ----------
def test_mdsync_library_has_md():
    assert _mdsync_md_names(_MDSYNC_LIB), "계약 1 -: 판정 대상 md 0개"


def test_mdsync_library_tables_match_json():
    fails = _mdsync_judge_dir(_MDSYNC_LIB)
    assert fails == [], _mdsync_message(fails)


# ---------- 합성 자기 점검(계약 7) ----------
_MDSYNC_SYN_JSON = {
    "topology_name": "syn",
    "netlist": [
        {"name": "M1", "kind": "nmos", "source": "gnd", "drain": "out", "gate": "in"},
        {"name": "M2", "kind": "pmos", "source": "vdd", "drain": "out", "gate": "in"},
    ],
    "passive_elements": [{"name": "C1", "kind": "capacitor", "terminals": ["out", "gnd"]}],
    "ideal_sources": [],
}
_MDSYNC_I1 = {"name": "I1", "kind": "current_source", "terminals": ["vdd", "in"], "value_amp": 1e-6, "implementable": False}

_MDSYNC_SYN_MD = "\n".join([
    "# syn -- topology connectivity table",
    "",
    "소스: `library/syn.topology.json`. 합성 입력.",
    "",
    "## ⚠️ 자동 플래그 (사람 재확인 필요)",
    "",
    "- **구동 소자 없는 net(gate로만 참조됨)**: in",
    "",
    "## Net별 연결 표 (이 net에 물린 모든 단자)",
    "",
    _MDSYNC_H_NET,
    "|---|---|---|",
    "| `gnd` | C1.t1, M1.source | 2 |",
    "| `in`" + _MDSYNC_WARN + " | M1.gate, M2.gate | 2 |",
    "| `out` | C1.t0, M1.drain, M2.drain | 3 |",
    "| `vdd` | M2.source | 1 |",
    "",
    "## 소자별 연결 표 (name/kind/source/drain/gate)",
    "",
    _MDSYNC_H_DEV,
    "|---|---|---|---|---|",
    "| M1 | nmos | `gnd` | `out` | `in` |",
    "| M2 | pmos | `vdd` | `out` | `in` |",
    "",
    "## 수동 소자 표 (R/C 등 -- netlist 밖 `passive_elements`)",
    "",
    _MDSYNC_H_PAS,
    "|---|---|---|",
    "| C1 | capacitor | `out`, `gnd` |",
    "",
    "총 2개 소자 + 1개 수동소자 + 0개 ideal source, 4개 net.",
    "",
])

_MDSYNC_SRC_SECTION = "\n".join([
    "## ⚡ Ideal source 표 (전류원/전압원 -- netlist 밖 `ideal_sources`, **구현 불가 소자**)",
    "",
    _MDSYNC_H_SRC,
    "|---|---|---|---|---|",
    "| I1 | current_source | `vdd`, `in` | 1e-06 | ⚠️ False |",
    "",
    "",
])


def _mdsync_syn_json2():
    j = json.loads(json.dumps(_MDSYNC_SYN_JSON))
    j["ideal_sources"] = [dict(_MDSYNC_I1)]
    return j


def _mdsync_sub(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"합성 치환 대상이 정확히 하나가 아님: {old!r} x{text.count(old)}")
    return text.replace(old, new)


def _mdsync_syn_md2():
    md = _mdsync_sub(_MDSYNC_SYN_MD, "| `in`" + _MDSYNC_WARN + " | M1.gate, M2.gate | 2 |",
                     "| `in`" + _MDSYNC_WARN + " | I1.t1, M1.gate, M2.gate | 3 |")
    md = _mdsync_sub(md, "| `vdd` | M2.source | 1 |", "| `vdd` | I1.t0, M2.source | 2 |")
    md = _mdsync_sub(md, "총 2개 소자 + 1개 수동소자 + 0개 ideal source, 4개 net.",
                     _MDSYNC_SRC_SECTION + "총 2개 소자 + 1개 수동소자 + 1개 ideal source, 4개 net.")
    return md


def _mdsync_no_linked(fname):
    raise ValueError(f"합성 입력에 연결 파일 없음: {fname}")


def _mdsync_contracts(n, md, j):
    return {k for k, _, _ in _mdsync_judge(n, md, j, _mdsync_no_linked)}


def _mdsync_base():
    return "syn", _MDSYNC_SYN_MD, json.loads(json.dumps(_MDSYNC_SYN_JSON))


def _mdsync_case_pass(name):
    n, md, j = _mdsync_base()
    if name == "crlf":
        md = md.replace("\n", "\r\n")
    elif name == "source_line_path":
        md = _mdsync_sub(md, "소스: `library/syn.topology.json`", "소스: `skills/x/assets/library/syn.topology.json`")
    elif name == "net_flag_removed":
        md = _mdsync_sub(md, "| `in`" + _MDSYNC_WARN + " |", "| `in` |")
    elif name == "net_flag_info":
        md = _mdsync_sub(md, "| `in`" + _MDSYNC_WARN + " |", "| `in`" + _MDSYNC_INFO + " |")
    elif name == "flag_prose_changed":
        md = _mdsync_sub(md, "- **구동 소자 없는 net(gate로만 참조됨)**: in", "- 다른 문장")
    elif name == "rows_shuffled":
        md = _mdsync_sub(md, "| `gnd` | C1.t1, M1.source | 2 |\n| `in`",
                         "| `in`")
        md = _mdsync_sub(md, "| `vdd` | M2.source | 1 |", "| `vdd` | M2.source | 1 |\n| `gnd` | M1.source, C1.t1 | 2 |")
        md = _mdsync_sub(md, "| M1 | nmos | `gnd` | `out` | `in` |\n| M2 | pmos | `vdd` | `out` | `in` |",
                         "| M2 | pmos | `vdd` | `out` | `in` |\n| M1 | nmos | `gnd` | `out` | `in` |")
    elif name == "with_source_base2":
        md, j = _mdsync_syn_md2(), _mdsync_syn_json2()
    elif name == "with_source_value_cols_changed":
        md, j = _mdsync_syn_md2(), _mdsync_syn_json2()
        md = _mdsync_sub(md, "| 1e-06 | ⚠️ False |", "| 2e-06 | True |")
    return n, md, j


_MDSYNC_PASS_CASES = ["base", "crlf", "source_line_path", "net_flag_removed", "net_flag_info",
                      "flag_prose_changed", "rows_shuffled", "with_source_base2", "with_source_value_cols_changed"]


@pytest.mark.parametrize("case", _MDSYNC_PASS_CASES)
def test_mdsync_selfcheck_accepts(case):
    n, md, j = _mdsync_case_pass(case)
    assert _mdsync_contracts(n, md, j) == set()


def _mdsync_case_reject(name):
    n, md, j = _mdsync_base()
    if name == "gate_changed":
        md = _mdsync_sub(md, "| M1 | nmos | `gnd` | `out` | `in` |", "| M1 | nmos | `gnd` | `out` | `out` |")
    elif name == "device_repeated_row":
        md = _mdsync_sub(md, "| M1 | nmos | `gnd` | `out` | `in` |", "| M1 | nmos | `gnd` | `out` | `in` |\n| M1 | nmos | `gnd` | `out` | `in` |")
    elif name == "device_row_missing":
        md = _mdsync_sub(md, "| M2 | pmos | `vdd` | `out` | `in` |\n", "")
    elif name == "device_section_missing":
        md = _mdsync_sub(md, "## 소자별 연결 표 (name/kind/source/drain/gate)", "## 다른 절")
    elif name == "json_extra_passive":
        j["passive_elements"].append({"name": "C2", "kind": "capacitor", "terminals": ["in", "gnd"]})
    elif name == "passive_section_missing":
        md = _mdsync_sub(md, "## 수동 소자 표 (R/C 등 -- netlist 밖 `passive_elements`)\n\n" + _MDSYNC_H_PAS
                         + "\n|---|---|---|\n| C1 | capacitor | `out`, `gnd` |\n\n", "")
    elif name == "passive_terminals_reversed":
        md = _mdsync_sub(md, "| C1 | capacitor | `out`, `gnd` |", "| C1 | capacitor | `gnd`, `out` |")
    elif name == "json_only_source":
        j["ideal_sources"] = [dict(_MDSYNC_I1)]
    elif name == "md2_against_base_json":
        md = _mdsync_syn_md2()
    elif name == "source_section_only_added":
        md = _mdsync_sub(md, "총 2개 소자", _MDSYNC_SRC_SECTION + "총 2개 소자")
    elif name == "net_terminal_missing":
        md = _mdsync_sub(md, "| `out` | C1.t0, M1.drain, M2.drain | 3 |", "| `out` | C1.t0, M1.drain | 3 |")
    elif name == "net_count_wrong":
        md = _mdsync_sub(md, "| `vdd` | M2.source | 1 |", "| `vdd` | M2.source | 2 |")
    elif name == "net_extra_row":
        md = _mdsync_sub(md, "| `vdd` | M2.source | 1 |", "| `vdd` | M2.source | 1 |\n| `x9` | M2.bulk | 1 |")
    elif name == "net_repeated_row":
        md = _mdsync_sub(md, "| `vdd` | M2.source | 1 |", "| `vdd` | M2.source | 1 |\n| `vdd` | M2.source | 1 |")
    elif name == "net_cell_no_backtick":
        md = _mdsync_sub(md, "| `vdd` | M2.source | 1 |", "| vdd | M2.source | 1 |")
    elif name == "net_cell_other_flag":
        md = _mdsync_sub(md, "| `vdd` | M2.source | 1 |", "| `vdd` ❗ | M2.source | 1 |")
    elif name == "total_passive_wrong":
        md = _mdsync_sub(md, "+ 1개 수동소자", "+ 2개 수동소자")
    elif name == "total_line_missing":
        md = _mdsync_sub(md, "총 2개 소자 + 1개 수동소자 + 0개 ideal source, 4개 net.", "")
    elif name == "total_line_wording":
        md = _mdsync_sub(md, "총 2개 소자 + 1개 수동소자", "총 2개 트랜지스터 + 1개 수동소자")
    elif name == "device_header_changed":
        md = _mdsync_sub(md, _MDSYNC_H_DEV, "| Name | Type | Source | Drain | Gate |")
    elif name == "h1_name_differs":
        md = _mdsync_sub(md, "# syn -- topology connectivity table", "# other -- topology connectivity table")
    elif name == "file_name_differs":
        n = "syn_b"
        md = _mdsync_sub(md, "# syn -- topology connectivity table", "# syn_b -- topology connectivity table")
    elif name == "json_missing":
        j = None
    return n, md, j


_MDSYNC_REJECT_CASES = [
    ("gate_changed", {2}), ("device_repeated_row", {2}), ("device_row_missing", {2}), ("device_section_missing", {2}),
    ("json_extra_passive", {3, 4, 5}), ("passive_section_missing", {3}), ("passive_terminals_reversed", {3}),
    ("json_only_source", {3, 4, 5}), ("md2_against_base_json", {3, 4, 5}), ("source_section_only_added", {3}),
    ("net_terminal_missing", {4}), ("net_count_wrong", {4}), ("net_extra_row", {4}), ("net_repeated_row", {4}),
    ("net_cell_no_backtick", {4}), ("net_cell_other_flag", {4}),
    ("total_passive_wrong", {5}), ("total_line_missing", {5}), ("total_line_wording", {5}),
    ("device_header_changed", {2}),
    ("h1_name_differs", {1}), ("file_name_differs", {1}), ("json_missing", {1}),
]


@pytest.mark.parametrize("case,want", _MDSYNC_REJECT_CASES, ids=[c for c, _ in _MDSYNC_REJECT_CASES])
def test_mdsync_selfcheck_rejects(case, want):
    n, md, j = _mdsync_case_reject(case)
    assert _mdsync_contracts(n, md, j) == want


def test_mdsync_selfcheck_rejects_empty_dir(tmp_path):
    assert {k for k, _, _ in _mdsync_judge_dir(tmp_path)} == {1}
