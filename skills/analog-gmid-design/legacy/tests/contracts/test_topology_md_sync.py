"""library 추적 topology.md 표 <-> json connectivity 일치 계약(20261001-topology-md-sync, 백로그 B47).

spec card `docs/02-design/specs/20261001-topology-md-sync.spec.md` 계약 1~5(실제 library 판정)와 계약 7(판정기 자기 점검)을
판정한다. 계약 6(oracle 독립)·8(base PASS와 `D^` 거부)·9(범위)는 auditor 측정이라 여기서 다루지 않는다.

이 파일은 md를 만든 렌더러나 topology 로더를 import·호출·실행하지 않는다(계약 6). 기대값은 `json` 표준 모듈로 읽은
`A/library/<n>.topology.json` 데이터에서 card 계약 2~5의 정의대로 만든다. md 파일은 읽기만 한다.

* 계약 1: 판정 대상 md(`A/library/*.topology.md`) 1개 이상, 짝 json 존재, json `topology_name` == n, H1 줄 하나 ==
  `# <n> -- topology connectivity table`. 짝 json이 없으면 계약 2~5는 판정하지 않는다.
* 계약 2: `## 소자별 연결 표` 절의 (Name, Kind, Source, Drain, Gate) 다중집합 == T(J)의 5짝 다중집합.
* 계약 3: `## 수동 소자 표`·`## ⚡ Ideal source 표` 절의 (Name, Kind, Terminals 순서 튜플) 다중집합 == P(J)·S(J). 비었으면 절 없음.
* 계약 4: `## Net별 연결 표`의 net 집합·net별 (소자, 단자) 다중집합·단자 수 == N(J).
* 계약 5: 합계 줄 하나, 문형 `총 <a>개 소자 + <b>개 수동소자 + <c>개 ideal source, <k>개 net.`, 수 == (|T|, |P|, |S|, |N|).

oracle 대조(계획 N3.12.3):

* test_mdsync_library_has_md / test_mdsync_library_tables_match_json -- (d) 실측 원자료: 판정 시점의
  `A/library/<n>.topology.json`(사용자 승인을 거친 connectivity 원본)을 `json`으로 읽어 card 계약 1~5 정의대로 기대값을
  만든다. 표 머리·셀 형식·`t<i>` 단자 이름·합계 줄 문형은 card 계약 문장 그대로다.
* test_mdsync_selftest_* -- (a) 구성 입력: card '거부해야 할 입력'의 합성 md·json 짝을 손으로 적었다. 무엇을 바꿨는지가 곧
  거부 여부·실패 계약 집합이다(각 케이스 주석에 근거).
"""
import collections
import json
import pathlib
import re

import pytest

_MDSYNC_CONTRACTS_DIR = pathlib.Path(__file__).resolve().parent
# contracts -> tests -> assets
_MDSYNC_ASSETS = _MDSYNC_CONTRACTS_DIR.parents[1]
_MDSYNC_LIBRARY = _MDSYNC_ASSETS / "library"

_MDSYNC_FLAG_WARN = " \u26a0\ufe0f"  # 공백 + U+26A0 + U+FE0F (card '플래그 문자')
_MDSYNC_FLAG_INFO = " \u2139\ufe0f"  # 공백 + U+2139 + U+FE0F

_MDSYNC_HEAD_DEVICE = "| Name | Kind | Source | Drain | Gate |"
_MDSYNC_HEAD_PASSIVE = "| Name | Kind | Terminals |"
_MDSYNC_HEAD_IDEAL = "| Name | Kind | Terminals | Value | Implementable |"
_MDSYNC_HEAD_NET = "| Net | 연결된 단자 (device.terminal) | 단자 수 |"

_MDSYNC_SEC_DEVICE = "## 소자별 연결 표"
_MDSYNC_SEC_PASSIVE = "## 수동 소자 표"
_MDSYNC_SEC_IDEAL = "## \u26a1 Ideal source 표"
_MDSYNC_SEC_NET = "## Net별 연결 표"

_MDSYNC_TOTAL_RE = re.compile(r"총 (\d+)개 소자 \+ (\d+)개 수동소자 \+ (\d+)개 ideal source, (\d+)개 net\.")
_MDSYNC_BACKTICK_RE = re.compile(r"`([^`]*)`")
_MDSYNC_NET_CELL_RE = re.compile(r"`([^`]*)`(" + _MDSYNC_FLAG_WARN + "|" + _MDSYNC_FLAG_INFO + ")?")

_MDSYNC_PARSE_ERRORS = (ValueError, KeyError, IndexError)


# ---------------------------------------------------------------------------------------------------------------
# md 파싱 (card '절과 표'·'셀'·'백틱 셀' 정의)
# ---------------------------------------------------------------------------------------------------------------

def _mdsync_lines(text):
    """줄 끝 CRLF·LF를 같게 다룬다."""
    return text.replace("\r\n", "\n").split("\n")


def _mdsync_cells(row):
    s = row.strip()
    if not (s.startswith("|") and s.endswith("|")) or len(s) < 2:
        raise ValueError("표 행 형식 아님: %r" % row)
    return [c.strip() for c in s[1:-1].split("|")]


def _mdsync_count_prefix(lines, prefix):
    return sum(1 for ln in lines if ln.startswith(prefix))


def _mdsync_section_rows(lines, prefix, header):
    """`prefix`로 시작하는 절의 표 데이터 행(셀 목록)들. 형식 위반은 ValueError."""
    idx = [i for i, ln in enumerate(lines) if ln.startswith(prefix)]
    if len(idx) != 1:
        raise ValueError("%r로 시작하는 줄 %d개(정확히 1개여야 함)" % (prefix, len(idx)))
    i = idx[0] + 1
    while i < len(lines) and not lines[i].startswith("|"):
        if lines[i].startswith("## "):
            raise ValueError("%r 절에 표 없음(다음 절 먼저)" % prefix)
        i += 1
    table = []
    while i < len(lines) and lines[i].startswith("|"):
        table.append(lines[i])
        i += 1
    if len(table) < 2:
        raise ValueError("%r 절에 표 없음 또는 구분 행 없음" % prefix)
    if table[0].strip() != header:
        raise ValueError("%r 표 머리 다름: %r" % (prefix, table[0]))
    n_cols = len(_mdsync_cells(header))
    rows = []
    for row in table[2:]:
        cells = _mdsync_cells(row)
        if len(cells) != n_cols:
            raise ValueError("%r 열 수 %d != 머리 %d: %r" % (prefix, len(cells), n_cols, row))
        rows.append(cells)
    return rows


def _mdsync_backtick(cell):
    m = _MDSYNC_BACKTICK_RE.fullmatch(cell)
    if m is None:
        raise ValueError("백틱 셀 아님: %r" % cell)
    return m.group(1)


def _mdsync_terminals_cell(cell):
    if cell == "":
        return ()
    return tuple(_mdsync_backtick(p) for p in cell.split(", "))


# ---------------------------------------------------------------------------------------------------------------
# json 쪽 기대값 (card T(J)·P(J)·S(J)·N(J) 정의)
# ---------------------------------------------------------------------------------------------------------------

def _mdsync_read_json(path):
    """json 파일을 읽는다. 파일 없음(OSError)은 ValueError로 바꿔 올린다(card 허용 예외 3종)."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except OSError as exc:
        raise ValueError("json 읽기 실패 %s: %s" % (path, exc))


def _mdsync_str(value, what):
    if not isinstance(value, str):
        raise ValueError("%s 값이 문자열 아님: %r" % (what, value))
    return value


def _mdsync_devices(j, folder):
    """T(J): 진입 json `netlist` + `linked_topology_files`(같은 폴더)의 `netlist`. 5짝 튜플 목록."""
    if not isinstance(j, dict):
        raise ValueError("json 최상위가 dict 아님")
    elems = list(j["netlist"])
    linked = j.get("linked_topology_files") or []
    for name in linked:
        sub = _mdsync_read_json(folder / _mdsync_str(name, "linked_topology_files"))
        if not isinstance(sub, dict):
            raise ValueError("연결 파일 %s 최상위가 dict 아님" % name)
        elems.extend(sub["netlist"])
    out = []
    for d in elems:
        if not isinstance(d, dict):
            raise ValueError("netlist 원소가 dict 아님: %r" % (d,))
        out.append(tuple(_mdsync_str(d[k], k) for k in ("name", "kind", "source", "drain", "gate")))
    return out


def _mdsync_terminal_elems(j, key):
    """P(J)(key=passive_elements)·S(J)(key=ideal_sources): (name, kind 또는 '?', terminals 튜플) 목록. 진입 json만."""
    if not isinstance(j, dict):
        raise ValueError("json 최상위가 dict 아님")
    out = []
    for e in j.get(key) or []:
        if not isinstance(e, dict):
            raise ValueError("%s 원소가 dict 아님: %r" % (key, e))
        terms = tuple(_mdsync_str(t, "terminals") for t in (e.get("terminals") or []))
        out.append((_mdsync_str(e["name"], "name"), _mdsync_str(e.get("kind", "?"), "kind"), terms))
    return out


def _mdsync_net_map(devices, passives, ideals):
    """N(J): net -> Counter((소자, 단자))."""
    nets = collections.defaultdict(collections.Counter)
    for name, _kind, src, drn, gat in devices:
        nets[src][(name, "source")] += 1
        nets[drn][(name, "drain")] += 1
        nets[gat][(name, "gate")] += 1
    for name, _kind, terms in list(passives) + list(ideals):
        for i, net in enumerate(terms):
            nets[net][(name, "t%d" % i)] += 1
    return nets


# ---------------------------------------------------------------------------------------------------------------
# 계약별 판정기 -- 실패 사유 문자열 목록을 돌려준다(빈 목록 = 통과)
# ---------------------------------------------------------------------------------------------------------------

def _mdsync_check_c2(lines, j, folder):
    try:
        want = collections.Counter(_mdsync_devices(j, folder))
        rows = _mdsync_section_rows(lines, _MDSYNC_SEC_DEVICE, _MDSYNC_HEAD_DEVICE)
        got = collections.Counter(
            (r[0], r[1], _mdsync_backtick(r[2]), _mdsync_backtick(r[3]), _mdsync_backtick(r[4])) for r in rows)
    except _MDSYNC_PARSE_ERRORS as exc:
        return ["파싱 실패: %r" % (exc,)]
    if got != want:
        return ["소자 표 차이 md만 %s / json만 %s" % (sorted((got - want).elements()), sorted((want - got).elements()))]
    return []


def _mdsync_check_c3_one(lines, j, key, prefix, header):
    try:
        want = collections.Counter(_mdsync_terminal_elems(j, key))
        if not want:
            n = _mdsync_count_prefix(lines, prefix)
            return [] if n == 0 else ["%s 비었는데 %r 절 %d개" % (key, prefix, n)]
        rows = _mdsync_section_rows(lines, prefix, header)
        got = collections.Counter((r[0], r[1], _mdsync_terminals_cell(r[2])) for r in rows)
    except _MDSYNC_PARSE_ERRORS as exc:
        return ["%s 파싱 실패: %r" % (key, exc)]
    if got != want:
        return ["%s 표 차이 md만 %s / json만 %s" % (key, sorted((got - want).elements()),
                                                  sorted((want - got).elements()))]
    return []


def _mdsync_check_c3(lines, j):
    return (_mdsync_check_c3_one(lines, j, "passive_elements", _MDSYNC_SEC_PASSIVE, _MDSYNC_HEAD_PASSIVE)
            + _mdsync_check_c3_one(lines, j, "ideal_sources", _MDSYNC_SEC_IDEAL, _MDSYNC_HEAD_IDEAL))


def _mdsync_expected_nets(j, folder):
    return _mdsync_net_map(_mdsync_devices(j, folder), _mdsync_terminal_elems(j, "passive_elements"),
                           _mdsync_terminal_elems(j, "ideal_sources"))


def _mdsync_check_c4(lines, j, folder):
    reasons = []
    try:
        want = _mdsync_expected_nets(j, folder)
        rows = _mdsync_section_rows(lines, _MDSYNC_SEC_NET, _MDSYNC_HEAD_NET)
        seen = collections.Counter()
        got = {}
        counts_bad = []
        for r in rows:
            m = _MDSYNC_NET_CELL_RE.fullmatch(r[0])
            if m is None:
                raise ValueError("Net 셀 형식 아님: %r" % r[0])
            net = m.group(1)
            seen[net] += 1
            pieces = r[1].split(", ") if r[1] != "" else []
            terms = collections.Counter()
            for p in pieces:
                dev, sep, term = p.rpartition(".")
                if sep == "":
                    raise ValueError("단자 조각에 '.' 없음: %r" % p)
                terms[(dev, term)] += 1
            got[net] = terms
            if int(r[2]) != len(pieces):
                counts_bad.append(net)
    except _MDSYNC_PARSE_ERRORS as exc:
        return ["파싱 실패: %r" % (exc,)]
    repeated = sorted(n for n, c in seen.items() if c > 1)
    if repeated:
        reasons.append("net 행 중복 %s" % repeated)
    if set(got) != set(want):
        reasons.append("net 집합 차이 md만 %s / json만 %s" % (sorted(set(got) - set(want)), sorted(set(want) - set(got))))
    diff = sorted(n for n in set(got) & set(want) if got[n] != want[n])
    if diff:
        reasons.append("단자 다중집합 차이 net %s" % diff)
    if counts_bad:
        reasons.append("단자 수 열 틀림 net %s" % sorted(counts_bad))
    return reasons


def _mdsync_check_c5(lines, j, folder):
    try:
        devices = _mdsync_devices(j, folder)
        passives = _mdsync_terminal_elems(j, "passive_elements")
        ideals = _mdsync_terminal_elems(j, "ideal_sources")
        want = (len(devices), len(passives), len(ideals), len(_mdsync_net_map(devices, passives, ideals)))
        totals = [ln for ln in lines if ln.startswith("총 ")]
        if len(totals) != 1:
            raise ValueError("'총 '으로 시작하는 줄 %d개" % len(totals))
        m = _MDSYNC_TOTAL_RE.fullmatch(totals[0])
        if m is None:
            raise ValueError("합계 줄 문형 다름: %r" % totals[0])
        got = tuple(int(g) for g in m.groups())
    except _MDSYNC_PARSE_ERRORS as exc:
        return ["파싱 실패: %r" % (exc,)]
    if got != want:
        return ["합계 %s != json %s" % (got, want)]
    return []


def _mdsync_md_paths(lib_dir):
    return sorted(pathlib.Path(lib_dir).glob("*.topology.md"))


def _mdsync_judge_nonempty(lib_dir):
    """계약 1 (a): 판정 대상 md 0개면 실패 쌍 하나."""
    if len(_mdsync_md_paths(lib_dir)) == 0:
        return [(1, "*", "판정 대상 md 0개")]
    return []


def _mdsync_judge_md(md_path):
    """md 하나에 계약 1 (b)~(d)·2·3·4·5를 모두 판정해 (계약, n, 사유) 목록을 돌려준다."""
    md_path = pathlib.Path(md_path)
    folder = md_path.parent
    n = md_path.name[: -len(".topology.md")]
    lines = _mdsync_lines(md_path.read_bytes().decode("utf-8"))
    fails = []

    h1 = [ln for ln in lines if ln.startswith("# ")]
    if h1 != ["# %s -- topology connectivity table" % n]:
        fails.append((1, n, "H1 줄 %r" % (h1,)))

    json_path = folder / ("%s.topology.json" % n)
    if not json_path.is_file():
        fails.append((1, n, "짝 json 없음"))
        return fails
    try:
        j = _mdsync_read_json(json_path)
    except _MDSYNC_PARSE_ERRORS as exc:
        fails.append((1, n, "짝 json 읽기 실패: %r" % (exc,)))
        return fails
    if not isinstance(j, dict):
        fails.append((1, n, "짝 json 최상위가 dict 아님"))
        return fails
    if j.get("topology_name") != n:
        fails.append((1, n, "topology_name %r != %r" % (j.get("topology_name"), n)))

    for k, reasons in ((2, _mdsync_check_c2(lines, j, folder)), (3, _mdsync_check_c3(lines, j)),
                       (4, _mdsync_check_c4(lines, j, folder)), (5, _mdsync_check_c5(lines, j, folder))):
        fails.extend((k, n, r) for r in reasons)
    return fails


def _mdsync_judge_dir(lib_dir):
    fails = []
    for p in _mdsync_md_paths(lib_dir):
        fails.extend(_mdsync_judge_md(p))
    return fails


def _mdsync_message(fails):
    return "\n".join("계약 %d %s: %s" % f for f in fails)


# ---------------------------------------------------------------------------------------------------------------
# 실제 library 판정 (계약 1~5) -- oracle (d)
# ---------------------------------------------------------------------------------------------------------------

def test_mdsync_library_has_md():
    """계약 1 (a): 판정 대상 md가 1개 이상(빈 판정 금지)."""
    fails = _mdsync_judge_nonempty(_MDSYNC_LIBRARY)
    assert len(fails) == 0, _mdsync_message(fails)
    assert len(_mdsync_md_paths(_MDSYNC_LIBRARY)) >= 1


def test_mdsync_library_tables_match_json():
    """계약 1 (b)~(d)·2·3·4·5: md 파일마다 모두 판정해 실패 쌍을 모은 뒤 한 번에 판정한다."""
    fails = _mdsync_judge_dir(_MDSYNC_LIBRARY)
    assert len(fails) == 0, _mdsync_message(fails)


# ---------------------------------------------------------------------------------------------------------------
# 판정기 자기 점검 (계약 7) -- oracle (a) 구성 입력. md는 card 계약 2~5 정의대로 손으로 적었다.
# ---------------------------------------------------------------------------------------------------------------

# 합성 기준 짝(card '거부해야 할 입력' 첫 문장): M1(nmos gnd/out/in), M2(pmos vdd/out/in), C1(capacitor [out, gnd]).
# N(J) 손 계산: gnd = {M1.source, C1.t1}, in = {M1.gate, M2.gate}, out = {M1.drain, M2.drain, C1.t0}, vdd = {M2.source}.
_MDSYNC_BASE_JSON = {
    "topology_name": "syn",
    "netlist": [
        {"name": "M1", "kind": "nmos", "source": "gnd", "drain": "out", "gate": "in"},
        {"name": "M2", "kind": "pmos", "source": "vdd", "drain": "out", "gate": "in"},
    ],
    "passive_elements": [{"name": "C1", "kind": "capacitor", "terminals": ["out", "gnd"]}],
    "ideal_sources": [],
}

_MDSYNC_BASE_MD = """# syn -- topology connectivity table

소스: `library/syn.topology.json`. 합성 입력.

## \u26a0\ufe0f 자동 플래그 (사람 재확인 필요)

- **구동 소자 없는 net(gate로만 참조됨)**: in

## Net별 연결 표 (이 net에 물린 모든 단자)

| Net | 연결된 단자 (device.terminal) | 단자 수 |
|---|---|---|
| `gnd` | C1.t1, M1.source | 2 |
| `in` \u26a0\ufe0f | M1.gate, M2.gate | 2 |
| `out` | C1.t0, M1.drain, M2.drain | 3 |
| `vdd` | M2.source | 1 |

## 소자별 연결 표 (name/kind/source/drain/gate)

| Name | Kind | Source | Drain | Gate |
|---|---|---|---|---|
| M1 | nmos | `gnd` | `out` | `in` |
| M2 | pmos | `vdd` | `out` | `in` |

## 수동 소자 표 (R/C 등 -- netlist 밖 `passive_elements`)

| Name | Kind | Terminals |
|---|---|---|
| C1 | capacitor | `out`, `gnd` |

총 2개 소자 + 1개 수동소자 + 0개 ideal source, 4개 net.
"""

# 합성 기준 짝 2: I1(current_source [vdd, in]) 추가. N(J) 손 계산: in += I1.t1, vdd += I1.t0.
_MDSYNC_I1 = {"name": "I1", "kind": "current_source", "terminals": ["vdd", "in"], "value_amp": 1e-6,
              "implementable": False}
_MDSYNC_BASE2_JSON = dict(_MDSYNC_BASE_JSON, ideal_sources=[_MDSYNC_I1])

_MDSYNC_IDEAL_SECTION = """## \u26a1 Ideal source 표 (전류원/전압원 -- netlist 밖 `ideal_sources`)

| Name | Kind | Terminals | Value | Implementable |
|---|---|---|---|---|
| I1 | current_source | `vdd`, `in` | 1e-06 | \u26a0\ufe0f False |

"""


def _mdsync_sub(text, old, new):
    """합성 변형: `old`가 정확히 한 번 있어야 한다(케이스 구성 오류는 ValueError로 드러낸다)."""
    if text.count(old) != 1:
        raise ValueError("합성 변형 대상 %r 횟수 %d" % (old, text.count(old)))
    return text.replace(old, new)


def _mdsync_make_base2_md():
    md = _MDSYNC_BASE_MD
    md = _mdsync_sub(md, "| `in` \u26a0\ufe0f | M1.gate, M2.gate | 2 |", "| `in` \u26a0\ufe0f | I1.t1, M1.gate, M2.gate | 3 |")
    md = _mdsync_sub(md, "| `vdd` | M2.source | 1 |", "| `vdd` | I1.t0, M2.source | 2 |")
    md = _mdsync_sub(md, "총 2개 소자 + 1개 수동소자 + 0개 ideal source", _MDSYNC_IDEAL_SECTION + "총 2개 소자 + 1개 수동소자 + 1개 ideal source")
    return md


_MDSYNC_BASE2_MD = _mdsync_make_base2_md()


def _mdsync_write_pair(folder, name, md_text, j, crlf=False):
    folder = pathlib.Path(folder)
    if md_text is not None:
        text = md_text.replace("\n", "\r\n") if crlf else md_text
        (folder / ("%s.topology.md" % name)).write_bytes(text.encode("utf-8"))
    if j is not None:
        (folder / ("%s.topology.json" % name)).write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")


def _mdsync_kinds(tmp_path, name, md_text, j, crlf=False):
    _mdsync_write_pair(tmp_path, name, md_text, j, crlf=crlf)
    fails = _mdsync_judge_dir(tmp_path)
    return sorted({k for k, _n, _r in fails}), fails


def _mdsync_shuffled_md():
    md = _MDSYNC_BASE_MD
    md = _mdsync_sub(md, "| `gnd` | C1.t1, M1.source | 2 |\n| `in` \u26a0\ufe0f | M1.gate, M2.gate | 2 |\n",
                     "| `in` \u26a0\ufe0f | M1.gate, M2.gate | 2 |\n| `gnd` | C1.t1, M1.source | 2 |\n")
    md = _mdsync_sub(md, "| M1 | nmos | `gnd` | `out` | `in` |\n| M2 | pmos | `vdd` | `out` | `in` |\n",
                     "| M2 | pmos | `vdd` | `out` | `in` |\n| M1 | nmos | `gnd` | `out` | `in` |\n")
    return md


# 통과해야 할 변형(card '통과해야 할 변형'). (id, md, json, crlf)
_MDSYNC_ACCEPT_CASES = [
    ("base", _MDSYNC_BASE_MD, _MDSYNC_BASE_JSON, False),
    ("base2_with_ideal", _MDSYNC_BASE2_MD, _MDSYNC_BASE2_JSON, False),
    ("crlf_line_ends", _MDSYNC_BASE_MD, _MDSYNC_BASE_JSON, True),
    ("source_line_path_changed",
     _mdsync_sub(_MDSYNC_BASE_MD, "소스: `library/syn.topology.json`", "소스: `C:/elsewhere/syn.topology.json`"),
     _MDSYNC_BASE_JSON, False),
    ("net_flag_removed", _mdsync_sub(_MDSYNC_BASE_MD, "| `in` \u26a0\ufe0f |", "| `in` |"), _MDSYNC_BASE_JSON, False),
    ("net_flag_to_info", _mdsync_sub(_MDSYNC_BASE_MD, "| `in` \u26a0\ufe0f |", "| `in` \u2139\ufe0f |"),
     _MDSYNC_BASE_JSON, False),
    ("auto_flag_sentence_changed",
     _mdsync_sub(_MDSYNC_BASE_MD, "- **구동 소자 없는 net(gate로만 참조됨)**: in", "- 다른 문장으로 바꾼 플래그 설명"),
     _MDSYNC_BASE_JSON, False),
    ("row_order_shuffled", _mdsync_shuffled_md(), _MDSYNC_BASE_JSON, False),
    ("base2_value_implementable_changed",
     _mdsync_sub(_MDSYNC_BASE2_MD, "| 1e-06 | \u26a0\ufe0f False |", "| 2.5e-06 | True |"), _MDSYNC_BASE2_JSON, False),
]


@pytest.mark.parametrize("case_id,md_text,j,crlf", _MDSYNC_ACCEPT_CASES, ids=[c[0] for c in _MDSYNC_ACCEPT_CASES])
def test_mdsync_selftest_accepts(tmp_path, case_id, md_text, j, crlf):
    """통과 케이스: 실패 집합이 비었다. oracle (a): connectivity를 바꾸지 않은 변형만 했다."""
    kinds, fails = _mdsync_kinds(tmp_path, "syn", md_text, j, crlf=crlf)
    assert kinds == [], _mdsync_message(fails)


_MDSYNC_C2 = dict(_MDSYNC_BASE_JSON,
                  passive_elements=_MDSYNC_BASE_JSON["passive_elements"]
                  + [{"name": "C2", "kind": "capacitor", "terminals": ["in", "gnd"]}])
_MDSYNC_BASE_MD_PLUS_IDEAL = _mdsync_sub(_MDSYNC_BASE_MD, "총 2개 소자", _MDSYNC_IDEAL_SECTION + "총 2개 소자")
_MDSYNC_BASE_MD_NO_PASSIVE = _mdsync_sub(
    _MDSYNC_BASE_MD,
    "## 수동 소자 표 (R/C 등 -- netlist 밖 `passive_elements`)\n\n| Name | Kind | Terminals |\n|---|---|---|\n"
    "| C1 | capacitor | `out`, `gnd` |\n\n", "")
_MDSYNC_BASE_MD_NO_DEVICE = _mdsync_sub(
    _MDSYNC_BASE_MD,
    "## 소자별 연결 표 (name/kind/source/drain/gate)\n\n| Name | Kind | Source | Drain | Gate |\n|---|---|---|---|---|\n"
    "| M1 | nmos | `gnd` | `out` | `in` |\n| M2 | pmos | `vdd` | `out` | `in` |\n\n", "")

# 거부해야 할 변형(card '거부해야 할 입력'). (id, 파일 이름 n, md, json, 기대 실패 계약 집합)
# 기대 집합의 근거 = card 괄호(무엇을 바꿨는지로 정해진다).
_MDSYNC_REJECT_CASES = [
    ("device_gate_changed",
     _mdsync_sub(_MDSYNC_BASE_MD, "| M1 | nmos | `gnd` | `out` | `in` |", "| M1 | nmos | `gnd` | `out` | `vdd` |"),
     _MDSYNC_BASE_JSON, [2]),
    ("device_repeated_row",
     _mdsync_sub(_MDSYNC_BASE_MD, "| M2 | pmos | `vdd` | `out` | `in` |\n",
                 "| M2 | pmos | `vdd` | `out` | `in` |\n| M2 | pmos | `vdd` | `out` | `in` |\n"),
     _MDSYNC_BASE_JSON, [2]),
    ("device_row_removed", _mdsync_sub(_MDSYNC_BASE_MD, "| M2 | pmos | `vdd` | `out` | `in` |\n", ""),
     _MDSYNC_BASE_JSON, [2]),
    ("device_section_missing", _MDSYNC_BASE_MD_NO_DEVICE, _MDSYNC_BASE_JSON, [2]),
    ("json_only_passive_c2", _MDSYNC_BASE_MD, _MDSYNC_C2, [3, 4, 5]),
    ("passive_section_missing", _MDSYNC_BASE_MD_NO_PASSIVE, _MDSYNC_BASE_JSON, [3]),
    ("passive_terminals_reversed",
     _mdsync_sub(_MDSYNC_BASE_MD, "| C1 | capacitor | `out`, `gnd` |", "| C1 | capacitor | `gnd`, `out` |"),
     _MDSYNC_BASE_JSON, [3]),
    ("json_only_ideal_i1", _MDSYNC_BASE_MD, _MDSYNC_BASE2_JSON, [3, 4, 5]),
    ("md2_against_json_without_ideal", _MDSYNC_BASE2_MD, _MDSYNC_BASE_JSON, [3, 4, 5]),
    ("ideal_section_only_added", _MDSYNC_BASE_MD_PLUS_IDEAL, _MDSYNC_BASE_JSON, [3]),
    ("net_terminal_removed",
     _mdsync_sub(_MDSYNC_BASE_MD, "| `out` | C1.t0, M1.drain, M2.drain | 3 |", "| `out` | C1.t0, M1.drain | 2 |"),
     _MDSYNC_BASE_JSON, [4]),
    ("net_count_column_wrong",
     _mdsync_sub(_MDSYNC_BASE_MD, "| `vdd` | M2.source | 1 |", "| `vdd` | M2.source | 2 |"), _MDSYNC_BASE_JSON, [4]),
    ("net_extra_row",
     _mdsync_sub(_MDSYNC_BASE_MD, "| `vdd` | M2.source | 1 |\n", "| `vdd` | M2.source | 1 |\n| `xtra` | M9.gate | 1 |\n"),
     _MDSYNC_BASE_JSON, [4]),
    ("net_repeated_row",
     _mdsync_sub(_MDSYNC_BASE_MD, "| `vdd` | M2.source | 1 |\n", "| `vdd` | M2.source | 1 |\n| `vdd` | M2.source | 1 |\n"),
     _MDSYNC_BASE_JSON, [4]),
    ("net_cell_no_backtick", _mdsync_sub(_MDSYNC_BASE_MD, "| `vdd` | M2.source | 1 |", "| vdd | M2.source | 1 |"),
     _MDSYNC_BASE_JSON, [4]),
    ("net_cell_other_flag", _mdsync_sub(_MDSYNC_BASE_MD, "| `in` \u26a0\ufe0f |", "| `in` \u274c |"),
     _MDSYNC_BASE_JSON, [4]),
    ("total_passive_count_wrong",
     _mdsync_sub(_MDSYNC_BASE_MD, "+ 1개 수동소자 +", "+ 2개 수동소자 +"), _MDSYNC_BASE_JSON, [5]),
    ("total_line_missing",
     _mdsync_sub(_MDSYNC_BASE_MD, "총 2개 소자 + 1개 수동소자 + 0개 ideal source, 4개 net.\n", ""),
     _MDSYNC_BASE_JSON, [5]),
    ("total_line_wording",
     _mdsync_sub(_MDSYNC_BASE_MD, "총 2개 소자 + 1개 수동소자 + 0개 ideal source, 4개 net.",
                 "총 2개 소자 + 1개 수동소자, 4개 net."), _MDSYNC_BASE_JSON, [5]),
    ("device_header_changed",
     _mdsync_sub(_MDSYNC_BASE_MD, "| Name | Kind | Source | Drain | Gate |", "| Name | Type | Source | Drain | Gate |"),
     _MDSYNC_BASE_JSON, [2]),
    ("h1_name_differs",
     _mdsync_sub(_MDSYNC_BASE_MD, "# syn -- topology connectivity table", "# other -- topology connectivity table"),
     _MDSYNC_BASE_JSON, [1]),
]


@pytest.mark.parametrize("case_id,md_text,j,expected", _MDSYNC_REJECT_CASES, ids=[c[0] for c in _MDSYNC_REJECT_CASES])
def test_mdsync_selftest_rejects(tmp_path, case_id, md_text, j, expected):
    """거부 케이스: 판정기가 낸 실패 계약 집합이 card 괄호의 집합과 정확히 같다. 예외로 끝나지 않는다."""
    kinds, fails = _mdsync_kinds(tmp_path, "syn", md_text, j)
    assert kinds == expected, _mdsync_message(fails)


def test_mdsync_selftest_rejects_file_name_vs_topology_name(tmp_path):
    """파일 이름 n과 json topology_name이 다름 -> {1}. oracle (a): md·json은 기준 짝 그대로, 파일 이름과 H1만 syn2."""
    md = _mdsync_sub(_MDSYNC_BASE_MD, "# syn -- topology connectivity table", "# syn2 -- topology connectivity table")
    kinds, fails = _mdsync_kinds(tmp_path, "syn2", md, _MDSYNC_BASE_JSON)
    assert kinds == [1], _mdsync_message(fails)


def test_mdsync_selftest_rejects_missing_json(tmp_path):
    """짝 json 없음 -> {1}(2~5는 판정하지 않는다). oracle (a): json을 쓰지 않았다."""
    kinds, fails = _mdsync_kinds(tmp_path, "syn", _MDSYNC_BASE_MD, None)
    assert kinds == [1], _mdsync_message(fails)


def test_mdsync_selftest_rejects_empty_dir(tmp_path):
    """판정 대상 md 0개 -> 계약 1 실패. oracle (a): 빈 임시 폴더."""
    fails = _mdsync_judge_nonempty(tmp_path)
    assert sorted({k for k, _n, _r in fails}) == [1]
    assert len(_mdsync_judge_dir(tmp_path)) == 0


# T(J) 형식 위반: card는 '계약 2 FAIL(예외로 끝나지 않음)'만 정한다. 계약 4·5도 T(J)를 쓰므로 집합을 단정하지 않고
# 2가 들어 있음만 본다(오케스트레이터 주의 1).
_MDSYNC_BAD_T_CASES = [
    ("netlist_elem_not_dict", dict(_MDSYNC_BASE_JSON, netlist=_MDSYNC_BASE_JSON["netlist"] + ["M3"])),
    ("netlist_elem_missing_gate",
     dict(_MDSYNC_BASE_JSON, netlist=[_MDSYNC_BASE_JSON["netlist"][0],
                                      {"name": "M2", "kind": "pmos", "source": "vdd", "drain": "out"}])),
    ("linked_file_absent", dict(_MDSYNC_BASE_JSON, linked_topology_files=["absent_part.topology.json"])),
]


@pytest.mark.parametrize("case_id,j", _MDSYNC_BAD_T_CASES, ids=[c[0] for c in _MDSYNC_BAD_T_CASES])
def test_mdsync_selftest_malformed_netlist_fails_c2(tmp_path, case_id, j):
    """T(J) 원소가 dict 아님·필수 키 없음·연결 파일 없음 -> 계약 2 실패로 기록되고 예외로 끝나지 않는다. oracle (a)."""
    kinds, fails = _mdsync_kinds(tmp_path, "syn", _MDSYNC_BASE_MD, j)
    assert 2 in kinds, _mdsync_message(fails)


def test_mdsync_selftest_accepts_linked_netlist(tmp_path):
    """T(J) = 진입 netlist + 연결 파일 netlist, P·S는 진입 json 것만(card T(J)·P(J) 정의).

    oracle (a): M2를 연결 파일로 옮기고 연결 파일에 수동 소자 C9를 두었다 -- 정의상 md는 기준 짝 그대로 통과한다.
    """
    entry = dict(_MDSYNC_BASE_JSON, netlist=[_MDSYNC_BASE_JSON["netlist"][0]],
                 linked_topology_files=["syn_part.topology.json"])
    part = {"topology_name": "syn_part", "netlist": [_MDSYNC_BASE_JSON["netlist"][1]],
            "passive_elements": [{"name": "C9", "kind": "capacitor", "terminals": ["vdd", "gnd"]}]}
    _mdsync_write_pair(tmp_path, "syn_part", None, part)
    kinds, fails = _mdsync_kinds(tmp_path, "syn", _MDSYNC_BASE_MD, entry)
    assert kinds == [], _mdsync_message(fails)
