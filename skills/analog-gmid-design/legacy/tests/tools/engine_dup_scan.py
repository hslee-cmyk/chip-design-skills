"""probe 안 엔진 식 재구현 스캐너 (정적 AST 도구, 표준 라이브러리만; 엔진 모듈을 import하지 않는다).

spec card `docs/02-design/specs/20260929-probe-engine-dup.spec.md` 계약 1이 정본이다.

    python engine_dup_scan.py --root <저장소 루트>

`<root>/skills/analog-gmid-design/assets/tests/probes/**/*.py`를 훑어 발견마다 한 줄 JSON
`{"path","line","rule","concept","exempt"}`를 출력한다. 면제되지 않은 발견 0 -> exit 0, 1개 이상 -> 1,
입력 오류(없는 루트·구문 오류 파일·잘못된 인자) -> 2.

규칙(접근 = 속성 `.gate`, 첨자 `["gate"]`, `.get("gate")`):
  lut-private        메서드 `._query(...)`·`._w_ref_effective(...)` 호출
  diode-inline       gate 접근과 drain 접근을 ==·!= 로 비교
  mirror-key         한 튜플 리터럴 안에 gate 접근과 source 접근
  gate-source-share  한 and 안에 gate끼리 비교와 source끼리 비교
  rail-set           문자열 상수 2개 이상, 원소가 모두 레일 이름 후보인 집합·리스트·튜플 리터럴

면제: `<root>/.ai/approvals/*.md`(이름이 `_`로 시작하지 않는 것) 머리 블록에 `target_kind: decision`이 있는
기록의 `target:` 값(`,` 구분) 원소 `<path>::<rule>`과 같은 발견.
"""
import ast
import json
import pathlib
import sys

PROBES_REL = ("skills", "analog-gmid-design", "legacy", "tests", "probes")  # 2026-10-07 legacy 이동
_LEGACY_PREFIX = "skills/analog-gmid-design/legacy/"
_PRE_LEGACY_PREFIX = "skills/analog-gmid-design/assets/"
_PRIVATE_METHODS = ("_query", "_w_ref_effective")
_RAIL_NAMES = frozenset(("vdd", "vss", "gnd", "agnd", "avdd", "avss", "dvdd", "dvss"))

_CONCEPT = {
    "lut-private": "LUT private 조회 재구성 -> SemiEmpiricalGmIdLUT.id_density_at_vgs",
    "diode-inline": "diode 판정 인라인 -> sizing_recipe.is_diode_connected",
    "mirror-key": "미러군 키 (gate, source) 인라인 -> sizing_recipe.true_current_mirror_groups",
    "gate-source-share": "게이트·소스 공유 인라인 판정 -> sizing_recipe.true_current_mirror_groups",
    "rail-set": "레일 집합 재선언 -> sizing_recipe._DEFAULT_RAIL_HI/_DEFAULT_RAIL_LO",
}


def _access_name(node):
    """`x.gate`·`x["gate"]`·`x.get("gate")`의 이름 `gate`, 접근이 아니면 None."""
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        key = node.slice
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            return key.value
        return None
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get"
            and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
        return node.args[0].value
    return None


def _compare_pairs(node):
    """Compare의 (왼, 오른, 연산자) 인접 쌍."""
    operands = [node.left] + list(node.comparators)
    return [(operands[i], operands[i + 1], node.ops[i]) for i in range(len(node.ops))]


def _is_same_access_compare(node, name):
    """Compare 안에 양쪽이 모두 `name` 접근인 쌍이 있는가."""
    return any(_access_name(a) == name and _access_name(b) == name for a, b, _ in _compare_pairs(node))


def scan_source(source: str, path: str) -> list:
    """`source`의 발견 목록(exempt는 모두 False). 구문 오류는 SyntaxError로 전파한다."""
    tree = ast.parse(source, filename=path)
    hits = set()

    def add(node, rule):
        hits.add((node.lineno, rule))

    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in _PRIVATE_METHODS):
            add(node, "lut-private")
        elif isinstance(node, ast.Compare):
            for a, b, op in _compare_pairs(node):
                if isinstance(op, (ast.Eq, ast.NotEq)) and {_access_name(a), _access_name(b)} == {"gate", "drain"}:
                    add(node, "diode-inline")
                    break
        elif isinstance(node, ast.Tuple):
            names = {_access_name(e) for e in node.elts}
            if "gate" in names and "source" in names:
                add(node, "mirror-key")
        elif isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
            cmps = [v for v in node.values if isinstance(v, ast.Compare)]
            if (any(_is_same_access_compare(c, "gate") for c in cmps)
                    and any(_is_same_access_compare(c, "source") for c in cmps)):
                add(node, "gate-source-share")
        if isinstance(node, (ast.Set, ast.List, ast.Tuple)):
            elts = node.elts
            if (len(elts) >= 2 and all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in elts)
                    and all(e.value.lower() in _RAIL_NAMES for e in elts)):
                add(node, "rail-set")

    return [{"path": path, "line": line, "rule": rule, "concept": _CONCEPT[rule], "exempt": False}
            for line, rule in sorted(hits)]


def _read_exemptions(root):
    """`<root>/.ai/approvals/*.md` decision 기록의 target 원소 집합(`<path>::<rule>`)."""
    out = set()
    adir = root / ".ai" / "approvals"
    if not adir.is_dir():
        return out
    for rec in sorted(adir.glob("*.md")):
        if rec.name.startswith("_"):
            continue
        lines = rec.read_text(encoding="utf-8").splitlines()
        if not lines or lines[0].strip() != "---":
            continue
        head = {}
        for ln in lines[1:]:
            if ln.strip() == "---":
                break
            key, sep, val = ln.partition(":")
            if sep:
                head.setdefault(key.strip(), val.strip())
        if head.get("target_kind") != "decision":
            continue
        out.update(el.strip() for el in head.get("target", "").split(",") if el.strip())
    return out


def main(argv: list) -> int:
    if len(argv) != 2 or argv[0] != "--root":
        print("usage: engine_dup_scan.py --root <repo root>", file=sys.stderr)
        return 2
    root = pathlib.Path(argv[1])
    if not root.is_dir():
        print("root not found: %s" % root, file=sys.stderr)
        return 2
    try:
        exempt = _read_exemptions(root)
        records = []
        probes = root.joinpath(*PROBES_REL)
        files = sorted(probes.rglob("*.py")) if probes.is_dir() else []
        for f in files:
            rel = f.relative_to(root).as_posix()
            records.extend(scan_source(f.read_text(encoding="utf-8"), rel))
    except (SyntaxError, UnicodeDecodeError, OSError) as exc:
        print("input error: %s" % exc, file=sys.stderr)
        return 2
    unexempted = 0
    for rec in records:
        # 2026-10-07 legacy 이동: 이동 전 승인 기록(.ai/approvals, 이력이라 고치지 않음)은 옛 자리
        # `skills/analog-gmid-design/assets/tests/probes/...` 경로로 적혀 있다 -- 같은 파일(git rename)이므로 옛 경로도 본다.
        old_path = rec["path"].replace(_LEGACY_PREFIX, _PRE_LEGACY_PREFIX, 1) if rec["path"].startswith(_LEGACY_PREFIX) else None
        if ("%s::%s" % (rec["path"], rec["rule"]) in exempt
                or (old_path is not None and "%s::%s" % (old_path, rec["rule"]) in exempt)):
            rec["exempt"] = True
        else:
            unexempted += 1
        print(json.dumps(rec, ensure_ascii=False))
    return 1 if unexempted else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
