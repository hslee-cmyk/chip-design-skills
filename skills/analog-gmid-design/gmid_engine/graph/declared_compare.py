"""declared stage 와 유도 결과 대조 (설계 41 §1.10, 계획 DEC-43·U-50).

진입점: `declared_compare(views, declared) -> tuple[Finding]`.

declared stage(손으로 선언한 stage 멤버십)는 **유도의 입력이 아니다**(U-50 -- 태그 키는 엔진이 읽지 않는다). 호출자가 선언을 `declared` 로 넘기면
유도 결과(첫 전달 뷰의 블록과 stage)와 대조해 불일치를 `declared_stage_mismatch`(review_needed)로 올린다.

* `declared` = 선언 묶음 tuple. 묶음 하나 = (출처 이름, (소자 이름 tuple, ...)) -- 소자 이름 tuple 하나가 declared stage 하나(예: stage_devices 의 한 원소).
* 판정: 선언 stage 하나의 소자들 중 **블록 멤버**(역할 input·cascode·follower·mirror·pass)인 것을 모아, (가) 모두 같은 stage 번호의 블록에 있고 (나) 그 stage
  의 블록들에서 같은 역할의 멤버(input·cascode·follower) 중 선언 밖인 소자가 없으면 일치. 아니면 어긋난 소자·stage 를 근거로 기록한다.
  블록에 들지 않는 소자(tail·load·바이어스)는 대조하지 않는다 -- 선언이 부하·바이어스를 적지 않는 것은 결함 선언이지 규칙의 오류가 아니다(plan 규칙 8).
* 전달 뷰가 없으면 대조할 유도가 없어 빈 tuple.
"""
from .s1v_values import (
    ROLE_CASCODE,
    ROLE_FOLLOWER,
    ROLE_INPUT,
    ROLE_MIRROR,
    ROLE_PASS,
    SEVERITY_REVIEW,
    VIEW_TRANSFER,
    F_DECLARED_MISMATCH,
    Finding,
)

_MEMBER_ROLES = (ROLE_INPUT, ROLE_CASCODE, ROLE_FOLLOWER, ROLE_MIRROR, ROLE_PASS)
_SIGNAL_ROLES = (ROLE_INPUT, ROLE_CASCODE, ROLE_FOLLOWER)


def declared_compare(views, declared):
    transfer = [v for v in views if v.kind == VIEW_TRANSFER]
    if not transfer:
        return ()
    view = transfer[0]
    stage_of = {}
    for block in view.blocks:
        for name, role in block.roles:
            if role in _MEMBER_ROLES:
                stage_of[name] = (block.stage, role)
    findings = []
    for source, stages in declared:
        for devices in stages:
            placed = {d: stage_of[d] for d in devices if d in stage_of}
            numbers = {s for s, _ in placed.values()}
            if len(numbers) > 1:
                findings.append(Finding(F_DECLARED_MISMATCH, SEVERITY_REVIEW, view.id, tuple(sorted(placed)),
                                        source + ": 선언된 한 stage 의 소자들이 유도된 서로 다른 stage 에 있다 " + repr(sorted(numbers)),
                                        ("DEC-43", "U-50")))
                continue
            if not numbers:
                continue
            stage = next(iter(numbers))
            extra = sorted(d for d, (s, role) in stage_of.items() if s == stage and role in _SIGNAL_ROLES and d not in devices)
            if extra:
                findings.append(Finding(F_DECLARED_MISMATCH, SEVERITY_REVIEW, view.id, tuple(extra),
                                        source + ": 유도된 stage " + str(stage) + " 의 입력·캐스코드·follower 소자가 선언에 없다",
                                        ("DEC-43", "U-50")))
    return tuple(findings)
