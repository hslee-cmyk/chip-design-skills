"""SP1 진입점 -- S1 위에 S1v 필드(`graph/s1v`)를 쓰고 `기록만` 분기면 정지한다 (설계 40 §2.4.2·§2.4.8 v1.9.1 D1·§10.1, 41 §0 단계 A3·§1).

진입점: `build_s1v(s1, spec, *, count_budget, declared=(), structure=None, declared_loop_cuts=(), stop_on_unsupported=True) -> S1Graph`.

* `s1` = `build_s1` 결과(권한표가 S1 필드를 덮는 S1Graph -- S0 수준 스냅샷 위의 것도 받는다). `spec` = `SizingSpecDoc` 또는 None(None 이면 기본 전달 뷰만).
  `count_budget` = 계수 예산 N_S(양의 정수 -- 사이클 열거·복합 블록 경로 수의 상한. 시간과 무관해 같은 입력은 늘 같은 S1v, 41 §0).
* `declared` = declared stage 묶음 ((출처, (소자 이름 tuple, ...)), ...) -- 유도의 입력이 아니라 대조용(U-50). `structure` = `load_structure_facts` 결과(ratified
  사실과 해시 불일치 기록) 또는 None. `declared_loop_cuts` = 안정도 제약이 선언된 루프 뷰의 끊는 gate 넷 이름들(단계 A 진입점이 spec 에서 계산해 넘긴다).
* 스냅샷 권한표를 `S1V_WRITERS` 로 넓힌 뒤 계산 블록 `s1v_fields`(writer `build_s1v`)를 부른다 -- 입력 버전이 같으면 재사용(계산 0, 같은 S0 의 디스크 스냅샷 위에서도).
  결과 = 같은 S1 키의 `S1Graph`(필드 `graph/s1v: views·l_classes·findings·declared·applied_facts` 를 담은 스냅샷). 묶음 객체는 없다(v1.9.1 D1).
* **정지**: `기록만`(unsupported_rule_branch) 기록이 하나라도 있으면 `StructureUnresolvedError`(reason `unsupported_rule_branch`, exit 2)로 멈춘다 --
  `stop_on_unsupported=False` 는 구조 표·측정을 위해 필드를 그대로 돌려받는 진단 모드다(정지 규칙을 우회하는 경로가 아니다: 호출자가 `s1v_findings` 의 unsupported 를 보고
  멈춰야 한다). `review_needed` 는 정지가 아니라 기록이며 GB4 앞에서 정지한다.
"""
from gmid_engine.core import StructureUnresolvedError

from .s1_model import S1Graph
from .s1_values import S1_WRITERS, S1V_WRITERS, UNSUPPORTED_RULE_BRANCH
from .s1v_fields import s1v_fields
from .s1v_findings import s1v_findings


def _stop(s1, unsupported):
    names = frozenset(name for name, _cls in s1.column("device", "element_class"))
    devices = sorted({name for f in unsupported for name in f.subject if name in names})
    raise StructureUnresolvedError(devices=devices, detail={
        "reason": UNSUPPORTED_RULE_BRANCH,
        "rule_branch": unsupported[0].code,
        "branches": tuple(sorted({f.code for f in unsupported})),
        "findings": tuple(f.code + "|" + f.view + "|" + ",".join(f.subject) for f in unsupported),
    })


def build_s1v(s1, spec, *, count_budget, declared=(), structure=None, declared_loop_cuts=(), stop_on_unsupported=True):
    if not isinstance(s1, S1Graph) or not s1.snapshot.writers.covers(S1_WRITERS):
        raise TypeError("build_s1v: s1 은 graph.build_s1 결과 S1Graph 여야 한다")
    if isinstance(count_budget, bool) or not isinstance(count_budget, int) or count_budget < 1:
        raise TypeError("build_s1v: count_budget 은 1 이상 int 여야 한다")
    judged = () if spec is None else tuple(spec.judged_constraints)
    facts = () if structure is None else tuple(structure.facts)
    stale = () if structure is None else tuple(structure.findings)
    snapshot = s1v_fields(s1.snapshot.widen(S1V_WRITERS), judged, count_budget, tuple(declared), facts, stale, tuple(declared_loop_cuts))
    result = S1Graph(s1.key, snapshot)
    if stop_on_unsupported:
        unsupported = s1v_findings(result)[2]
        if unsupported:
            _stop(result, unsupported)
    return result
