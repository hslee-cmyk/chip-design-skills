"""
symmetry.matching_pairs의 current_forced(축A) 선언이 실제 근거를 가지는지 양방향으로
대조하는 audit 스크립트.

배경(2026-08-05, 세션10 L1/L2 구현 논의 중 설계): L1이 kind를 current_forced(bool)/
matching_sensitivity("ratio"|"offset") 두 축으로 분해하면서, "같은 gate+rail 공유"만으로는
current_forced=true의 근거가 안 된다는 원칙이 세션8~10 내내 반복 확인됐다(진짜 근거는
(a) 진짜 2단자 KCL 노드 또는 (b) sizing_roles.theta의 명시적 forcing뿐 -- 세션9의
two_stage_ota M5/M7, 세션10의 current_reuse M58/M57이 둘 다 "같은 gate+rail"만 보고
잘못 선언된 실제 사례). theta 기반 근거를 matching_pairs에 다시 문자열로 중복 기록하면
두 곳이 어긋날 위험만 커지므로, 새 스키마 필드를 만드는 대신 이 스크립트가 sizing_roles.theta
와 matching_pairs를 자동으로 대조한다.

양방향 검사:
1. current_forced=true인데 theta 어디에도 강제 근거가 없는 쌍 -- 과다선언 의심(⚠️).
2. current_forced=false인데 theta가 실제로 그 쌍을 같은 값으로 강제하고 있는 쌍 --
   과소선언(진짜 버그) 의심(🔴). M58/M57이 정확히 이 패턴이었다(2026-08-05 세션10 발견,
   커밋 8409c0a).

sizing_roles 자체가 없는 회로(folded_cascode/nmcnr_amplifier/two_stage_ota -- 전부 폐형식
사이징, theta 그리드서치를 안 씀)는 대조 대상이 없으므로 자동으로 "정보성"(theta 없음) 표시만
하고 실패로 안 친다 -- 그 회로들의 current_forced 근거는 이 스크립트가 아니라 netlist
connectivity 직접 검토(topology_to_markdown.py)로 확인해야 한다는 뜻이다.

**정직한 한계**: theta 근거가 간접(예: current_reuse의 M10/M19 -- 각자 다른 A_signed 수식으로
독립적으로 계산되지만 그 수식의 구성요소가 이미 서로 같은 값으로 강제된 쌍들이라 결과적으로
같아지는 경우)이면 이 스크립트는 못 잡고 "근거 없음"으로 보수적으로 flag한다 -- 그 경우는
사람이 직접 사슬을 추적해 판단할 것(예: sizing_recipe.py의 kcl_sink_M10/M19 주석 참고).
false negative(진짜 근거가 있는데 못 찾음)는 사람 확인으로 안전하게 처리되지만, false
positive(근거 없다고 flag했는데 실은 있음)는 이 스크립트가 놓치지 않는 것을 목표로 한다.

사용법: `python audit_current_forced.py [topology.json 경로 ...]`
        인자 없으면 library/ 아래 *.topology.json 전부를 대상으로 한다.
        exit code: 🔴(과소선언, 진짜 불일치)가 하나라도 있으면 1, 아니면 0
        (⚠️는 사람 확인 요청일 뿐 실패로 안 침 -- theta 없는 회로에서 전 항목이 이걸 받는 게
        정상이므로 CI 게이트로 쓰려면 🔴만 봐야 함).
"""
import sys
import os
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stick_diagram import load_topology  # noqa: E402


def _as_set(names_field) -> set:
    """theta feed의 root/reference는 문자열 하나 또는 리스트 둘 다 올 수 있다."""
    if names_field is None:
        return set()
    if isinstance(names_field, str):
        return {names_field}
    return set(names_field)


def _theta_evidence_for_pair(a: str, b: str, thetas: list) -> str | None:
    """(a,b) 쌍이 어느 theta에 의해 강제되는 직접 근거가 있으면 그 theta 이름을 반환,
    없으면 None. 두 가지 feed 모양만 직접 근거로 인정한다(간접/연쇄 추론은 사람 몫,
    docstring의 "정직한 한계" 참고):
    - type A/A_signed: root가 리스트고 {a,b}가 둘 다 root 안에 있으면(같은 theta_value로
      동시에 시드됨 -- sizing_recipe.py의 r_diode_M11a/r_classab_battery 등이 실제로 이
      패턴) 근거로 인정.
    - type C: target/reference가 정확히 (a,b) 또는 (b,a)면(예: mirror_M18a) 근거로 인정."""
    for theta in thetas:
        feeds = theta.get("feeds")
        if not isinstance(feeds, dict):
            continue
        ftype = feeds.get("type")
        if ftype in ("A", "A_signed"):
            root_set = _as_set(feeds.get("root"))
            if a in root_set and b in root_set:
                return theta["name"]
        elif ftype == "C":
            pair = {feeds.get("target"), feeds.get("reference")}
            if pair == {a, b}:
                return theta["name"]
    return None


def audit_topology(topology_path: str) -> dict:
    """한 topology.json을 감사해 {"forward_ok": [...], "forward_flagged": [...],
    "reverse_violations": [...], "no_theta": bool} 반환. names가 3개 이상인 그룹은
    모든 쌍별 조합으로 펼쳐서 검사한다(matching_pairs의 N-소자 그룹 관례, audit_row_split()
    과 동일 계약).

    검사하지 않는 것: theta 근거가 간접/연쇄(구성요소가 이미 다른 theta로 강제돼 결과적으로
    같은 값이 되는 경우)이면 추적하지 않고 "근거 없음"으로 보수적으로 flag만 한다.
    sizing_roles.theta가 아예 없는 회로(폐형식 사이징)는 대조 대상이 없어 전부 정보성
    표시만 하고 근거를 검증하지 않는다.
    영역: 없음(스키마)
    """
    import itertools
    _, meta = load_topology(topology_path)
    pairs_meta = meta["symmetry"]["matching_pairs"]
    thetas = ((meta.get("sizing_roles") or {}).get("theta")) or []

    # 어떤 (a,b) 쌍이 서로 다른 matching_pairs 항목에 **둘 다** 나타날 수 있다(예:
    # current_reuse의 M8/M17이 7-소자 current_forced=false 문서용 그룹에도, 별도 2-소자
    # current_forced=true 선언에도 동시에 등장 -- "겹쳐도 무방"이라고 명시적으로 주석까지
    # 있음, sizing_recipe.py 참고). 역방향 검사(현재 false인데 theta가 강제)는 그 쌍이
    # **어디에도** current_forced=true로 선언돼 있지 않을 때만 진짜 불일치다 -- 먼저 전체
    # 선언을 훑어 "true로 한 번이라도 선언된 쌍" 집합을 만든 뒤 역방향 검사에서 제외한다.
    declared_true_pairs = {
        frozenset((a, b))
        for p in pairs_meta if p["current_forced"]
        for a, b in itertools.combinations(p["names"], 2)
    }

    forward_ok, forward_flagged, reverse_violations = [], [], []
    for p in pairs_meta:
        for a, b in itertools.combinations(p["names"], 2):
            evidence = _theta_evidence_for_pair(a, b, thetas)
            if p["current_forced"]:
                if evidence:
                    forward_ok.append((a, b, evidence))
                else:
                    forward_flagged.append((a, b))
            else:
                if evidence and frozenset((a, b)) not in declared_true_pairs:
                    reverse_violations.append((a, b, evidence))

    return {
        "forward_ok": forward_ok,
        "forward_flagged": forward_flagged,
        "reverse_violations": reverse_violations,
        "no_theta": not thetas,
    }


def render_report(topology_path: str) -> tuple[str, bool]:
    """(리포트 텍스트, has_violation) 반환 -- has_violation=True면 🔴(과소선언) 있음."""
    name = os.path.splitext(os.path.splitext(os.path.basename(topology_path))[0])[0]
    result = audit_topology(topology_path)
    lines = [f"## {name}"]

    if result["no_theta"]:
        lines.append(f"- (정보) sizing_roles.theta 없음(폐형식 사이징) -- 이 스크립트는 대조 "
                      f"대상이 없어 current_forced 선언 {len(result['forward_flagged'])}건 전부 "
                      f"자동으로 '사람 확인 필요'로 표시됨. netlist connectivity 직접 검토로 "
                      f"근거를 확인할 것(topology_to_markdown.py).")
    if result["forward_ok"]:
        lines.append(f"- ✅ 근거 확인됨 ({len(result['forward_ok'])}건):")
        for a, b, ev in result["forward_ok"]:
            lines.append(f"    {a}/{b} <- theta '{ev}'")
    if result["forward_flagged"] and not result["no_theta"]:
        lines.append(f"- ⚠️ current_forced=true인데 theta 근거 없음 ({len(result['forward_flagged'])}건, "
                      f"사람 확인 필요 -- 간접/연쇄 근거일 수 있음, docstring 참고):")
        for a, b in result["forward_flagged"]:
            lines.append(f"    {a}/{b}")
    if result["reverse_violations"]:
        lines.append(f"- 🔴 current_forced=false인데 theta가 실제로 강제 중 ({len(result['reverse_violations'])}건, "
                      f"과소선언 -- 재분류 필요):")
        for a, b, ev in result["reverse_violations"]:
            lines.append(f"    {a}/{b} <- theta '{ev}'가 같은 값으로 강제")
    if not result["forward_ok"] and not result["forward_flagged"] and not result["reverse_violations"]:
        lines.append("- (해당 없음: current_forced 선언 없음)")

    return "\n".join(lines), bool(result["reverse_violations"])


if __name__ == "__main__":
    try:  # Windows 콘솔 기본 코드페이지(cp949/cp1252)가 한글을 못 찍는 문제 방지
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    paths = sys.argv[1:]
    if not paths:
        lib_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "library")
        # _TEMPLATE.topology.json은 실제 회로가 아니라 자리표시자 예시라 제외(Transistor
        # 필드가 실제 값이 아니라 설명 문자열이라 load_topology()가 그대로 못 읽음).
        paths = sorted(p for p in glob.glob(os.path.join(lib_dir, "*.topology.json"))
                        if not os.path.basename(p).startswith("_"))

    print("# current_forced audit -- matching_pairs 축A 선언과 sizing_roles.theta 양방향 대조\n")
    any_violation = False
    for path in paths:
        report, has_violation = render_report(path)
        print(report)
        print()
        any_violation = any_violation or has_violation

    if any_violation:
        print("결과: 🔴 과소선언(진짜 불일치) 발견 -- matching_pairs 재검토 필요", file=sys.stderr)
        sys.exit(1)
    print("결과: 🔴 과소선언 없음(⚠️는 위 출력에서 개별 확인할 것)", file=sys.stderr)
    sys.exit(0)
