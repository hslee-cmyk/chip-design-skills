"""전달 뷰 수집 (설계 41 §1.1, 계획 N3.2-2 '여기 뷰 수집').

진입점: `collect_views(model, spec) -> (tuple[ViewSeed], tuple[Finding])`. 기본 포트 뷰 규칙 `default_port_seeds(inputs, outputs)` 는 이 파일의 규칙 하나다(측정 구성이 S1v 없는 스냅샷에서 같은 규칙을 부른다).

* **선언된 전달 뷰**: spec 제약의 `ViewDecl` 마다 하나. mode `port`·`loop`(β = 1 이든 선언 β 든 SP1 의 구조 뷰는 같은 여기·관측)은
  `weights`/`sense`, `transfer` 는 `ExciteSense`, `ratio` 는 분자·분모 각각. mode `sense`(출력 포트 관측, 여기 없음)·`none`·
  결정 대기(`pending`)는 구조 뷰를 만들지 않는다. 같은 (여기, 관측) 은 한 번만 센다(spec 의 `(excite, sense)` 키 정의 그대로).
* **기본 포트 뷰**(`default_port_seeds`): 입력 포트 role 이 차동 쌍(p·n 각 하나, 다른 입력 없음)이면 가중 ±1/|D| 의 기모드 여기 하나, 아니면 입력 포트마다 단일 여기(가중 1)
  하나. 관측 = 출력 포트 전부(차동 출력쌍이면 그 둘). role 어휘 밖 입력이 섞인 차동 후보는 단일 여기로 가른다. **선언 뷰와 늘 함께 든다**(카드 IT-2c): 선언 씨앗 다음에 기본
  씨앗을 붙이고 같은 (여기, 관측) 키는 먼저 온 씨앗 하나로 합친다(선언이 먼저라 같은 키에서는 출처가 선언으로 남는다). 씨앗의 키가 기본 포트 뷰 키 집합 안이면
  `default_port` True(합쳐진 선언 씨앗 포함). 입력 포트가 하나도 없고 선언 뷰도 없어 뷰가 하나도 없을 때만 `view_required` 기록(정지는 호출자).
* 전류 입력·트랜스임피던스 뷰는 만들지 않는다(DEC-59 정지 -- 선언이 오면 `unsupported_view` 기록).
* 순서: (여기, 관측) 정렬. spec 이 None 이면 기본 뷰만.
"""
import dataclasses

from gmid_engine.core import sorted_items

from .s1v_values import (
    PORT_ROLE_DIFF_N,
    PORT_ROLE_DIFF_P,
    SEVERITY_UNSUPPORTED,
    SPEC_VIEW_LOOP,
    SPEC_VIEW_PORT,
    SPEC_VIEW_RATIO,
    SPEC_VIEW_TRANSFER,
    VIEW_SOURCE_DECLARED,
    VIEW_SOURCE_DEFAULT,
    VIEW_TRANSFER,
    Finding,
    ViewSeed,
)

_DEFAULT_SOURCE = VIEW_SOURCE_DEFAULT
_DECLARED_SOURCE = VIEW_SOURCE_DECLARED


def _seed(excite, sense, source):
    return ViewSeed(VIEW_TRANSFER, sorted_items(excite), sorted_items(frozenset(sense)), source)


def _from_weights(weights, sense_decl):
    if sense_decl is None or not weights:
        return None
    nets = tuple(net for net in (sense_decl.sense_p, sense_decl.sense_n) if net is not None)
    return _seed(weights, nets, _DECLARED_SOURCE)


def _from_excite_sense(es):
    nets = tuple(net for net in (es.sense_p, es.sense_n) if net is not None)
    return _seed(es.ac_excite, nets, _DECLARED_SOURCE)


def _declared(spec):
    seeds = []
    for constraint in (() if spec is None else spec.judged_constraints):
        view = constraint.view
        if view is None:
            continue
        if view.mode in (SPEC_VIEW_PORT, SPEC_VIEW_LOOP):
            seeds.append(_from_weights(view.weights, view.sense))
        elif view.mode == SPEC_VIEW_TRANSFER and view.transfer is not None:
            seeds.append(_from_excite_sense(view.transfer))
        elif view.mode == SPEC_VIEW_RATIO:
            seeds.extend(_from_excite_sense(side) for side in (view.num, view.den) if side is not None)
    return [seed for seed in seeds if seed is not None]


def default_port_seeds(inputs, outputs):
    """기본 포트 뷰 씨앗(모듈 머리말) -- `inputs`·`outputs` = ((넷, role), ...) (`NetModel.inputs`·`.outputs` 꼴)."""
    sense = tuple(net for net, _ in outputs)
    roles = dict(inputs)
    differential = {PORT_ROLE_DIFF_P, PORT_ROLE_DIFF_N}
    if len(roles) == len(differential) and set(roles.values()) == differential:
        half = 1.0 / len(differential)
        weights = tuple((net, half if role == PORT_ROLE_DIFF_P else -half) for net, role in inputs)
        return [_seed(weights, sense, _DEFAULT_SOURCE)]
    return [_seed(((net, 1.0),), sense, _DEFAULT_SOURCE) for net, _ in inputs]


def collect_views(model, spec):
    defaults = default_port_seeds(model.inputs, model.outputs)
    default_keys = frozenset((seed.excite, seed.sense) for seed in defaults)
    unique = {}
    for seed in _declared(spec) + defaults:
        key = (seed.excite, seed.sense)
        unique.setdefault(key, dataclasses.replace(seed, default_port=key in default_keys))
    findings = []
    if not unique:
        findings.append(Finding("view_required", SEVERITY_UNSUPPORTED, "", tuple(net for net, _ in model.inputs),
                                "전달 뷰를 만들 입력 포트가 없다", ("N3.2-2",)))
    return tuple(seed for _, seed in sorted_items(unique)), tuple(findings)
