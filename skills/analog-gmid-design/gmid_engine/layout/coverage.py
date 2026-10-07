"""MOD7 소자 누락 판정 `check_stick_diagram_coverage` -- 옛 stick_diagram.py 본문 복사(L10).

복사 정의의 SD 행·AST 해시·본문 리터럴 집합은 `_copy_manifest.py`. 정의 본문(docstring·주석 포함)은
수정 금지 -- 바꾸려면 복사를 끊고 새 정의로 쓰며 manifest 항목을 지운다.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CoverageVerdict:
    ok: bool
    missing: set


def check_stick_diagram_coverage(sized_device_names, stick_diagram_devices: dict) -> CoverageVerdict:
    """리포트를 완료로 선언하기 **직전** 반드시 호출한다 — sizing이 끝난 소자 이름 전부가
    실제로 어떤 stick-diagram 물리 행에든 배치돼 있는지, 단순 집합 차집합으로 확인한다.

    ⚠️ 왜 필요한가: `run_full_circuit_audit()`(§6.6)는 caller가 넘긴 `devices` dict **안의**
    정합성(matching/hub-merge/box-shape)만 본다 — 그 dict 자체에서 소자가 통째로 빠지면
    (예: CMFB/bias-gen/Class-AB 서브블록 전체를 stick diagram 단계에서 깜빡하고) 애초에
    검사 대상이 아니므로 못 잡는다. 이 함수는 사이징 단계의 정본(예: `sizing_results.json`
    또는 그에 준하는 소자 이름 목록)과 stick diagram 단계의 정본을 **서로 다른 두 산출물**로
    보고 직접 대조한다 — 같은 스크립트 안에서 한쪽만 업데이트하고 다른 쪽을 깜빡해도 잡힌다.

    **입력**:
    - `sized_device_names`: 사이징이 끝난 모든 소자 이름의 집합/리스트(§3 사이징 표 전체).
    - `stick_diagram_devices`: `{row_name: [device_name, ...]}` — 실제 stick diagram 각
      물리 행에 실제로 배치된 소자 이름들(`build_stick_diagram()`에 넘긴 `Transistor`
      리스트의 `.name`들, 또는 `transistor_sequence`에서 뽑은 고유 이름 집합).

    **반환**: `CoverageVerdict(ok, missing)` — `missing`이 비어있지 않으면 그 소자들은
    사이징만 되고 물리 행이 없다는 뜻 — **리포트를 완료로 선언하지 않는다.**

    ⚠️⚠️ **"게이트 함수를 import만 하고 실제로 호출·assert하지 않은 채 완료 선언"도 그
    자체로 이 사고의 일부였다** — `run_full_circuit_audit`/`audit_row_split`/
    `check_stick_diagram_coverage`(이 함수) 같은 게이트를 코드 상단에 import해뒀다는
    사실은 "확인했다"는 증거가 되지 않는다. 리포트를 완료로 선언하기 전, 실제 소스에
    `run_full_circuit_audit(`/`check_stick_diagram_coverage(` **호출문**이 있고 그 반환값의
    `.ok`를 실제로 확인(assert 등)했는지 grep으로 직접 재확인할 것.

    검사하지 않는 것: 배치된 소자가 실제로 Euler/box-shape 조건을 만족하는지는 검사하지
    않고 이름의 집합 포함 여부만 본다. 같은 소자가 여러 행에 중복 배치돼도 합집합으로만
    계산해 잡히지 않는다.
    영역: 없음(배치)
    """
    covered = set()
    for names in stick_diagram_devices.values():
        covered.update(names)
    missing = set(sized_device_names) - covered
    return CoverageVerdict(ok=not missing, missing=missing)
