---
template: plan
version: 0.11
---

# graph-consumption Planning Document

> **Summary**: graph 필드가 만들어진 그대로 실제로 쓰이게 하고, KVL·KCL 관계를 graph에 한 번만 두어 엔진 계산이 그 정본을 읽게 한다. 결과의 KVL·KCL 성립은 계산 경로와 다른 모델(SPICE 오라클)로 확인한다. 네 갈래다.
> 1. **구조 규칙 L(규칙 L-1~L-5)**: 진입점에서 도달하는 writer 밖 실제 읽기, 출력 전용 선언과 진입점 도달, 블랭킷 READS 금지, 하위 칸 reader, 정본 술어 재계산 거부. 기존 위반은 card id를 붙인 **항목 집합이 기준선의 부분집합으로만 줄어드는 목록**(부채 목록)에 두고, 규칙 코드·매개변수까지 기준선 지문으로 묶는다.
> 2. **필드별 처리**: 문서·계획이 소비자를 지정한 필드는 그 소비자에 배선하고, 정본 우회 재계산(R1·R2)은 정본 읽기로 바꾸며, 나머지는 출력 전용 선언 또는 삭제(삭제는 사용자 승인)한다.
> 3. **KVL·KCL 관계 단일 정본**: 엔진이 실제로 푸는 관계(쓰기 계획의 숲과 종속 분류, 전류 기저)를 정본으로 두고, 쓰이지 않는 S1 관계 사본(`rel_kvl_branch`·`gvgs_summary`·`rel_kcl_group`·`rel_vds_eq_vgs` 등)을 지운다. KVL 정본에는 '같은 DC' 변을 넣지 않는다(사용자 결정 B2·K-3). VDS 변을 지나는 부등식 사이클은 headroom-chain HC-1 소관이다. 트리 경로는 쓰기 계획 블록이 넷별 뿌리 경로를 자기 출력 S0 필드로 한 번 쓰고, 소비자 셋(이 계획, headroom-chain, design 41 §6.7)이 읽는다(사용자 결정 O-14 (1) (가′)).
> 4. **결과 검증**: 독립 경로는 SPICE 오라클 forced 모드(넷별 KCL 잔차)·free 모드(노드전압)이고 배선은 U16이다. 엔진 안에는 보조 검사 둘(쓰기 계획 숲 회계 불변량, `node.terminals` 결선 점검)만 둔다. 출발 전류의 조용한 자리값 대체는 꺼지지 않는 충돌 표지로 바꾸고 기저를 거친다.
>
> **Project**: chip-design-skills (analog-gmid-design skill) · **Author**: Claude Code
> **Status**: **계획 v0.11 -- 승인됨(사용자 O-48 "승인", 2026-10-20, `wt/_drafts/user_decisions.md` O-48 행; 전체 정합 검증 3차 + 마지막 diff 확인 승인 차단 없음)**. O-26·O-27·O-32·O-33 후속 정정과 O-34·O-36·O-43~O-46 반영(2026-10-19, `wt/_drafts/user_decisions.md` 645·646·652·653·654·656행). O-36: X-G13 승인(`size_and_seal_local` 배선 대기, 기한 = gain-budget v6.19 card LA-1 병합), GD-14 L-1 '호출자 0 내부 함수' 확장 넣기. GC-8에서 `ls_swing` 제외(O-26 (1), gain-budget card DE-1), layout 동작점 사본 부채 항목(O-27, card LI-1), 출력 함수 판정 기준과 GD-1 독립 검증, 선언 triode 'LUT 정의역 하한 항' 구분(O-33 (9)), 전류 대칭 결과 필드 소유 문언, 착수 조건 cProfile 기준선(WP-10, O-33 (1)). 이전: 계획 v0.10 -- 승인됨(사용자 O-21 "모두 승인", 같은 문서 640행, 승인 대상 `9090593a`, 최종 diff 확인 `c57b9f5d` '승인 가능'). 사용자 결정 O-15(`wt/_drafts/user_decisions.md` 634행)의 (A) U-G4 범위 보완(`conduction_mask`)과 (E) 원칙 감사 범위 확장(GC-9, X-G12), (C)에 따른 B-G2 흡수를 반영했다. v0.9는 O-14(같은 문서 633행) 반영본이다 -- 트리 경로를 쓰기 계획 블록의 자기 출력 필드로, WP-10 계측 완료 조건, 상위 card IT-1 병합. v0.8은 O-13(같은 문서 632행) 반영본으로 diff 확인 '승인 가능'이었다. 착수 근거는 사용자 결정 O-10 (2)(같은 문서 628행)이다. 다음 단계는 v0.11 독립 검증 → 사용자 승인 → GC-0a(card 0 측정) → GC-D(상위 문서 개정 → design)다.
>
> **이력**: 경위, 재측정 근거, 검증 반영 기록은 [graph-consumption.history.md](graph-consumption.history.md)에 있다.
> **상위 계획**: [gain-budget-gmid-sizing.plan.md](gain-budget-gmid-sizing.plan.md). 상위 원칙(N1.4 NFR, N2 결정, N6.3 병합 전 확인)을 따른다. 관계는 N2 표, 상위 문언과 다른 곳은 N5와 N3.10에 있다.
> **관련 계획**: [headroom-chain.plan.md](headroom-chain.plan.md)(`vds_saturation` 대체, S0 제약 그래프, 출발 구간. 이 계획은 v0.7.6 -- 브랜치 `plan/headroom-v076` `aa6e064c` -- 을 기준으로 읽는다(v0.7.5 최종은 `c0d96517`, 승인 `b7f457e9`). Gs⁺·경로 문언의 줄 인용은 v0.7.1(`ecceaed4`) 기준이 남아 있다), [oracle-portability.plan.md](oracle-portability.plan.md)(오라클 입력 스키마).

---

## N0. 문서 안내

* **담는 것**: 목적·범위, 확정 결정과 상위 계획과의 관계, 규칙·정의, 정본 위치, 게이트, 원래 취지와 다른 항목, 선행 측정(card 0), card 단계, 완료 조건, 위험, 원문 근거, 열린 결정.
* **담지 않는 것**: 경위, 측정값과 그 해석, 버전 이력. 이것은 history에 둔다. 계획에는 측정의 결론과 지시만 적는다.
* **값 원칙**: 이 문서에는 새 수치 상수를 두지 않는다. 허용오차는 이미 선언된 값(봉인 `tol_V`·`tol_I`, 봉인 3의 MOS 없는 행 부동소수 한계 식, 오라클 `kcl_abs_A`)을 참조하고, 선언된 값이 없는 곳은 사용자 결정으로 올린다.
* **이름 원칙**: 규칙·코드·판정에 회로·소자·넷 이름을 쓰지 않는다. 이름은 측정 대상(N6)과 history에만 사례로 나온다.
* **물리 원칙(P-1)**: 모든 제한·예외는 물리 유도(KVL·KCL·영역 조건·층 의존성)나 확인된 사실이 있어야 둔다. 물리 근거가 없는 기존 동작을 보존할 때는 '근거 없음, 보존만'으로 적는다. 알고리즘 제한은 점검표(N3.11)에 '알고리즘'으로 따로 적는다.
* **인용 규칙**: 코드는 `파일:줄`로 적는다. 기준은 master `5fea301`(이 worktree `wt/graph-consumption-plan`의 병합 커밋 `aebe7e8`)이다. v0.1 base `52945ce`와 엔진·도구 코드 diff가 0이고, 상위 계획의 인용 줄 번호도 같다(history H2-5). 인용한 줄은 모두 이 worktree에서 직접 읽어 확인했다. 경로 약어는 다음과 같다.
  * `E/` = `skills/analog-gmid-design/gmid_engine/`
  * `O/` = `skills/analog-gmid-design/tools/spice_oracle/`
  * 상위 계획 = `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`
  * design 41 = `docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md`
  * headroom-chain v0.7.1 = `git show ecceaed4:docs/01-plan/features/headroom-chain.plan.md`
* **오케스트레이터 기본안**: 사용자 결정·상위 문서가 정하지 않은 것을 원칙으로 정할 때 '(기본안)'으로 표시한다. 사용자가 바꿀 수 있다.
* **번호 충돌 주의**: 구조 규칙 L의 하위 규칙은 항상 **'규칙 L-1'~'규칙 L-5'**로 적는다. 사용자 결정 L-1~L-3(옛 엔진 삭제, `user_decisions.md` 617·620·626행)과 다른 것이다.
* **card id 규칙**: 부채 목록 항목과 처리 표의 card 칸에는 card id만 쓴다(결정 id U-G*·백로그 id B-G*는 쓰지 않는다). 처리가 결정을 기다리면 '읽는 결정' 칸에 따로 적는다(N7.1).

### N0.1 용어

| 용어 | 정의 |
|---|---|
| 필드 | 권한표 `E/search/s0_fields.py` `S0_WRITERS`(S2·S1v·metrics·search 권한표의 합)와 `E/layout/_ly_fields.py` `LY_WRITERS`에 (kind, field)로 등록된 graph 값이다. writer는 필드마다 하나다(상위 DEC-83) |
| 엔진 진입점 | 단계 A·B, 탐색 진입점, 수렴 진입점이다. 목록은 design이 닫는다(GD-1) |
| 실제 읽기 | 엔진 코드(tests 제외)의 `.value/.column/.field/.column_fields` 접근 가운데 필드 인자가 그 필드로 풀리고, **그 접근을 담은 함수가 엔진 진입점에서 호출 그래프로 도달하는** 것이다. READS 선언만으로는 읽기로 치지 않는다. 실행 스냅샷 전체 덤프(`E/search/archive.py` `write_snapshot`)도 읽기로 치지 않는다 |
| 출력 전용 필드 | 실제 읽기가 출력 함수(보고·결과 JSON)에만 있는 필드다. 그 출력 함수는 엔진 진입점에서 도달할 수 있어야 한다 |
| 블랭킷 READS | 블록 READS가 실제로 읽지 않는 열을 포함하는 것이다. 예: S1 필드 전부(`E/graph/s1_values.py:206` `S1_READS`)를 선언하는 블록 |
| 하위 칸 | 필드 값 형식(frozen dataclass)의 칸이다 |
| 정본 술어 | graph 필드로 이미 계산된 판정이다(예: `device.is_diode`, `graph.gs_groups`의 (kind, gate, source) 묶음) |
| 정본 우회 재계산 | 정본 술어·관계가 있는데 같은 것을 핀·연결에서 다시 계산하는 것이다 |
| 부채 목록 | 구조 규칙 L의 기존 위반을 담은 목록이다. 항목 키는 (규칙, 최소 단위 대상)이다. 최소 단위는 필드 규칙이면 (kind, field), READS 규칙이면 (블록, 열), 하위 칸 규칙이면 (형식, 칸), 술어·동적 접근 규칙이면 (파일, 줄 자리)다. 현재 항목 집합은 기준선 항목 집합의 부분집합이어야 한다(N3.1-6) |
| Gs⁺ | 쓰기 계획이 노드 전압을 쓰는 그래프다. 용어와 정의는 headroom-chain v0.7.1 N0.1과 같다(상위 FR-9). 고정 노드 F = 레일 ∪ 노드 목표 ∪ 선언 입력 포트. 변 = MOS (gate, source) 변 + 저항 변. **'같은 DC' 변(`input_tie`)은 없다**(사용자 결정 B2·K-3, design 41 §6.7-1a). 입력 DC 미선언 입력 포트를 포함하는 성분은 성분마다 뿌리·오프셋이 하나이고, 포트가 여럿이면 나머지 포트는 MOS writer가 쓰는 넷이다. 그래서 포트 사이 MOS 경로가 둘 이상이면 하나는 트리 경로로 다른 포트를 쓰고, 나머지 경로의 비트리 MOS 변이 포트 차 ΔV를 소거한 KVL 하나를 닫는다(비트리 MOS 종속 -- 보통 `cycle_vgs`, 경우에 따라 `parallel_vgs`·`fixed_vgs`, `E/sizing/writer_plan.py:191-196`. 사용자 결정 O-13 (1), 아래 'KVL 관계'). as-built 쓰기 계획은 아직 '같은 DC' 변을 넣는다(F-G19) |
| KVL 관계 | Gs⁺(F를 한 점으로 묶음)의 신장 숲에서 비트리 MOS 변 하나가 닫는 기본 사이클이다. 사이클마다 종속 소자 하나와 ΔV 출처(레일 차·노드 목표·선언 입력 DC·0)가 있다. **등식 사이클만 이 계획 소관이다.** VDS 변을 하나 이상 지나는 부등식 사이클(포화 하한)은 headroom-chain HC-1 제약 그래프 소관이다. 입력 DC 미선언 입력 포트 사이의 포트 차 고리(DEC-64 v1)는 **사용자 결정 O-13 (1)**(`wt/_drafts/user_decisions.md` 632행)대로 다룬다: 같은 DC 등식(두 포트 DC가 같다는 제약)은 없앤다. 포트 경로가 둘 이상인 v1 고리는 ΔV를 소거한 KVL 하나가 남는다(예: 파일럿 M1b `cycle_vgs`, VGS1a − VGS1b = VGS4a − VGS4b). 이 KVL은 등식 사이클이므로 이 계획 소관이다. 회로가 대칭이면 그 KVL은 대칭 묶음(`domain.ties`)과 중복이다 |
| 종속 분류 | 쓰기 계획이 비트리 MOS 변에 매기는 세 분류 `fixed_vgs`(gate·source가 둘 다 F), `parallel_vgs`(같은 (kind, gate, source) 트리 변이 있음), `cycle_vgs`(나머지)다(`E/sizing/writer_plan.py:186-196`) |
| 트리 경로 | 쓰기 계획 숲에서 넷 하나가 자기 뿌리(F 또는 W4 창 뿌리)까지 가는 부호 있는 변 열이다. **정본은 `node.dc_writer` 자체다**: 넷마다 `NodeWrite`(관계, 원소, 읽는 아는 쪽 노드 `known`)가 부모 포인터다(`E/sizing/s2_values.py:268-277`). **사용자 결정 O-14 (1) (가′)**: 쓰기 계획 블록이 넷별 뿌리 경로(변 열·부호, θ 무관)를 **자기 출력 S0 필드로 한 번 쓰고**, 소비자 셋이 그 필드를 읽는다(N3.3-3). 그 필드의 writer는 쓰기 계획 블록 하나다 |
| KCL 관계 | 레일이 아닌 넷마다의 KCL 행과 그 유리수 기약 행사다리꼴 해, 즉 전류 기저 `graph.dc_current_basis`다(`E/sizing/current_basis.py:1-14, :78-143`) |
| 독립 검증 | 계산 경로와 다른 모델·다른 풀이로 결과의 KVL·KCL 성립을 재는 검사다. 이 계획에서는 SPICE 오라클이다(N3.5). 같은 결선 출처·같은 전류값으로 다시 더하는 검사는 독립 검증이 아니다(항등식) |
| 엔진 보조 검사 | 엔진 안에서 실행당 한 번 도는 θ 무관 구조 검사다. 독립 검증이 아니고, 조립·분류 구현 오류를 잡는다(N3.5-3) |

---

## N1. 목적·범위·요구

### N1.1 목적

사용자 2026-10-16 원문: "code를 작성할 때 계산식을 작성하여 값을 얻는 대상이 이미 graph에 계산되어 있는지를 확인하고 계산식을 사용하여 작성하게 해. 원래 graph를 완성하여 계산되어 있다면 KVL과 KCL이 항상 성립해야 겠지만, 이 KVL과 KCL에 따라 계산을 수행하는 엔진에서는 이 계산을 수행하여 결과를 내야 하는거지. 이 관계가 엔진에 적용되어 있는지도 확인해."

재측정(history H2)의 결론은 다섯이다.
* 필드 131개 가운데 writer 밖 실제 읽기가 0인 필드가 26개다(test만 읽음 24, 아무도 안 읽음 2). 출력 함수에서만 읽히는 필드가 14개이고, 그중 4개는 선언이 없거나 출력 함수가 진입점에서 도달하지 않으며, 2개는 동적 접근으로만 읽힌다.
* 엔진은 KVL·KCL을 **실제로 풀어** 결과를 낸다. KVL은 노드전압 정식화와 쓰기 계획 신장 숲으로, KCL은 유리수 전류 기저로 푼다(F-G4·F-G5). 그런데 그 관계를 graph S1 관계 필드에서 읽지 않고 커널 쪽에서 따로 다시 만든다. S1 관계 필드(`rel_kcl_group`, `rel_vds_eq_vgs`, `rel_matching_ratio`, `rel_matching_offset`, `gvgs_summary`)는 엔진 소비자가 0이고, `rel_kvl_branch`는 봉인 8만 읽으며 쓰기 계획과 정의가 다르다(F-G6·F-G7). 상위 V9는 `matching_offset`·`matching_ratio` 멤버를 검증 소비자로 지정한다(F-G34).
* 엔진 안 결과 검사는 대부분 같은 파생값을 다시 쓰는 항등식이다. 봉인 8은 봉인 2가 소자별로 잰 같은 양의 합이다(F-G31). 봉인 3은 봉인 2와 상관된 더 엄격한 집계다(K-d). 공급 전류 합과 결선 대조는 결선 행렬 항등식이다(F-G21·F-G22). MNA 상대 잔차는 후진 안정 LU에서 공허하다(F-G28). 계산 경로와 독립인 KCL·KVL 확인은 SPICE 오라클이고, 엔진 → 오라클 입력 배선은 U16이다(F-G23).
* 출발 구간은 θ 전류가 0 이하이거나 정해지지 않은 소자에 소자별 자리값을 둔다. 그 자리값은 KCL 기저를 거치지 않는다(F-G12). 출발 실행 가능 판정은 매크로 목표를 끈 뒤와 면적 예산이 없을 때 실패 표지를 보지 않고, 사다리 아래 칸은 판정하지 않는다(F-G32).
* 정본 술어를 핀에서 다시 계산하는 곳이 있다(diode 판정, (gate, source) 묶음, F-G13).

이 기능의 목표는 다섯이다.
1. 구조 규칙 L로 '만들고 안 쓰는 필드'와 '정본 우회 재계산'을 기계적으로 거부한다. 기존 위반은 부채 목록으로 시작해 줄어들기만 하게 한다.
2. 위반 필드마다 원칙대로 처리한다(배선, 정본 읽기, 출력 전용 선언, 삭제).
3. KVL·KCL 관계를 엔진이 실제로 푸는 형태로 graph에 한 번만 둔다. 계산은 그 정본을 읽고, 쓰이지 않는 사본은 지운다.
4. 결과가 KVL·KCL을 만족하는지는 계산 경로와 독립된 모델(오라클)로 확인한다. 엔진 안에는 항등식이 아닌 구조 불변량만 보조로 둔다.
5. 변경 종류별 기준(사용자 결정 O-34)으로 판정한다: 결정성은 항상 비트 동일, 순수 리팩터링은 base와 필드별 비교, 동작 변경은 정의 오라클 toy·봉인 불변식·SPICE oracle·검증자 원인 변화표(N4-0).

### N1.2 범위

| 포함 | 제외 |
|---|---|
| 구조 규칙 L(규칙 L-1~L-5) 구현과 부채 목록(GC-1) | 새 전류 사슬, 종속 전류 구간 결합 (a)~(c)(O-10 (4)로 백로그) |
| 필드별 처리: 이 계획이 소유하는 필드의 출력 전용 선언·삭제·블랭킷 READS 정리·동적 접근의 정적 해석 형태 전환(GC-7) | 지정 소비자가 아직 없는 필드의 배선 자체. 소비자를 만드는 card가 맡는다(층 0 전체판 단위 8, U17 ②, U16 -- N3.2 표) |
| KVL 단일 정본: 쓰기 계획의 `gs_groups` 읽기, `gvgs_self_edge` 정지 이전, 봉인 8 처리(U-G9), 숲 회계 불변량, S1 사본 삭제(GC-2) | VDS 변 부등식 사이클(포화 하한)과 그 출발 구간 반영. headroom-chain HC-1 소유다 |
| KCL 단일 정본: `rel_kcl_group` 삭제, `node.terminals` 결선 점검(GC-3) | 입력 DC 미선언 입력 포트의 '같은 DC' 변 폐기(K-3) 구현. K-3 구현 card(design 41 §6.7-1a) 소유다(N7.2) |
| 독립 검증 경로 정의(오라클 forced·free)와 그 배선 의존의 상위 개정 항목(U16) | 오라클 입력 생성기 구현(U16, oracle-portability OP-*) |
| 출발 전류: 음수·0 자리값 → 꺼지지 않는 충돌 표지, 기저 경유, 사다리 칸 단위 처리(GC-5) | 출발 구간 gm/ID·L 규칙(headroom-chain 소유), 소신호 회로 정식화 변경, MNA 조건수 기록(백로그 B-G1) |
| 정본 술어 우회 교체(R1·R2, graph 층 안 R1″, 쓰기 계획의 (kind, gate, source) 재유도)(GC-6) | R6(layout 파생 판정)의 교체(U16 배선 card) |
| R3(전도 하한 필드 대 search 칸 하한) 공동분석 자료(card 0 M-G6)와 그 결정 뒤 처리(GC-7) | 위쪽 방향 VDS 변 정본 필드와 개념 정의(headroom-chain HC-1·N3.4 소유). 이 계획은 소비자 셋 배선만(GC-8) |
| 상위 문서·CONTRACT 개정안, 다른 card 완료 조건 변경(N3.10) | design 40·41의 다른 절, headroom-chain 계획 본문 |
| 원칙 감사 범위(O-15 (E), X-G12): 기저 행 float 변환 1회, 정확 MOS 전류 공용 함수, `current_cone`의 기저 읽기(GC-9), 블록 안 local memo와 같은 점 재풀이 금지(GC-5) | 위쪽 방향 차분 제약 그래프의 정본 필드·개념 정의(O-15 (C), headroom-chain 소관 -- 배선 셋은 GC-8로 포함). `_vds_floor`의 `lut.derived` 이동(headroom-chain HC-S로 옮김, 오케스트레이터 기본안) |
| 13회로(library 9 + heldout 4) 변경 종류별 판정 증거(N4-0) | 회로 spec 변경 |

### N1.3 기능 요구

| ID | 요구 |
|---|---|
| FR-G1 | **규칙 L-1 reader 존재**: 필드마다 writer 블록 밖 엔진 코드에, 엔진 진입점에서 도달하는 실제 읽기가 1곳 이상 있어야 한다(N3.1-1) |
| FR-G2 | **규칙 L-2 출력 전용**: 실제 읽기가 출력 함수에만 있으면 출력 전용 목록에 있어야 하고, 그 출력 함수가 엔진 진입점에서 도달해야 한다(N3.1-2) |
| FR-G3 | **규칙 L-3 READS = 실제 읽기**: 블록 READS의 열마다 그 블록 안 실제 읽기가 있어야 한다. 블랭킷 선언은 펼쳐서 같은 검사를 한다(N3.1-3) |
| FR-G4 | **규칙 L-4 하위 칸**: 필드 값 형식의 칸마다 클래스 본문 밖 엔진 읽기가 있거나, 출력 전용·지문 전용 목록에 있어야 한다(N3.1-4) |
| FR-G5 | **규칙 L-5 정본 술어**: 등록된 정본 술어를 writer 파일 밖에서 다시 계산하면 거부한다. 기준선은 F-G13 자리 전부를 담는다(N3.1-5) |
| FR-G6 | **부채 목록**: 기존 위반은 card id가 붙은 목록에만 있고, 현재 항목 집합은 기준선 항목 집합의 부분집합이며, 낡은 항목은 실패다. 규칙 L 코드·매개변수도 기준선 지문 대상이다(N3.1-6) |
| FR-G7 | **필드별 처리**: N3.2 표대로 처리한다. 삭제는 사용자 승인 항목(U-G3)이다 |
| FR-G8 | **KVL 정본**: KVL 관계의 정본은 쓰기 계획 출력(`node.dc_writer` 숲 + `device.dc_coord` 종속 분류)이다. 사이클 멤버가 필요한 곳은 쓰기 계획 블록이 같은 블록 출력으로 쓰는 넷별 뿌리 경로 필드(O-14 (1) (가′), N3.3-3)를 읽는다. S1 `rel_kvl_branch`·`gvgs_summary`는 지운다(N3.3) |
| FR-G9 | **같은 VGS 정본**: 쓰기 계획의 `parallel_vgs` 판정은 `graph.gs_groups`를 읽는다. (kind, gate, source) 묶음을 다시 만들지 않는다(N3.3-5) |
| FR-G10 | **KCL 정본**: KCL 관계는 `graph.dc_current_basis` 하나다. `rel_kcl_group`은 지운다(U-G3, N3.4) |
| FR-G11 | **MNA**: 이 계획은 MNA 코드를 바꾸지 않는다. 상대 잔차는 공허하다(F-G28). 조건수 기록은 백로그 B-G1이다 |
| FR-G12 | **출발 전류**: 0 이하 전류를 조용히 자리값으로 바꾸지 않고, 매크로 목표 해제·예산 유무와 무관하게 꺼지지 않는 충돌 표지로 기록한다. 자리값은 기저 자유 원소에만 두고 나머지 전류는 기저 행으로 계산한다. 충돌 칸의 처리는 사다리 칸 단위로 정한다(U-G13, N3.6) |
| FR-G13 | **정본 술어 교체**: R1·R2·R1″ 자리와 쓰기 계획의 묶음 재유도를 정본 읽기로 바꾼다(N3.7) |
| FR-G14 | **옛 경로 삭제**: 대체된 필드·블록·문언과 그 등록(지문 파일 목록·모듈 지도·패키지 공개 이름)은 같은 변경에서 지운다(상위 레지스트리 규칙) |
| FR-G15 | **변경 종류별 판정**(사용자 결정 O-34): 모든 card에서 결정성(두 번 실행 비트 동일), 순수 리팩터링 card(GC-2·GC-3·GC-6·GC-9와 GC-7의 리팩터링 부분)는 13회로 결과가 base와 필드별로 같고(이산 정확, 연속 분해능 이내), 동작 변경 card(GC-5·GC-8과 GC-7의 `conduction_mask` 통일 부분)는 정의 오라클 toy·봉인 불변식·SPICE oracle 대조와 검증자 원인 변화표로 판정한다(N4-0) |
| FR-G16 | **정지 보존**: `gvgs_self_edge` fail-closed 정지는 `gvgs_cycles.py`를 지우기 전에 다른 블록으로 옮기고, 정지 시점·판정식·사유 코드가 base와 같다(N3.3-6) |
| FR-G17 | **엔진 보조 검사**: 쓰기 계획 숲 회계 불변량(종속 수 = \|E\| − \|V\| + 성분 수)과 `node.terminals` 결선 점검을 θ 무관 S0 검사로 실행당 한 번 한다. 거부를 먼저 보인다(N3.5-3) |
| FR-G18 | **독립 검증 경로**: 결과의 KCL·KVL 독립 확인은 오라클 forced·free 대조다. 그 배선은 U16 완료 조건이고, 이 계획은 그 변경을 상위·관련 계획 개정 항목(S-7)으로 올린다(N3.5-2, N3.10, U-G10) |

### N1.4 비기능 요구

상위 계획 N1.4 NFR-1~NFR-6과 N2.2 작업 원칙을 그대로 적용한다. 이 기능에서는 다음을 강제한다.

| ID | 요구 |
|---|---|
| NFR-G0 | **물리 정합(P-1, 최우선)**: 정본으로 고르는 관계는 물리적으로 가장 일반적인 형태(엔진이 실제로 푸는 방정식 전체)다. 모든 한정 조건은 N3.11 점검표의 유도나 '근거 없음, 보존만' 표시를 가진다 |
| NFR-G1 | **이름 금지**: 규칙 코드에 회로·소자·넷 이름 리터럴 0 |
| NFR-G2 | **상수 발명 금지**: 새 허용오차는 기존 선언값이나 기존 식만 쓴다. 없으면 사용자 결정이다 |
| NFR-G3 | **graph 단일 정본**: 개념 하나에 필드 하나, writer 하나(상위 DEC-83·FR-9). 트리 경로는 쓰기 계획 블록이 자기 출력 필드로 한 번 쓰고(writer 하나), 소비자는 그 필드를 읽는다. 같은 경로를 블록 밖에서 다시 재구성하지 않는다(N3.3-3, O-14 (1)) |
| NFR-G4 | **계산 재사용**: θ 무관 검사(숲 불변량, 결선 점검)는 실행마다 처음 한 번 계산하고 그 실행 안에서 재사용한다(상위 NFR-2, 원래 취지 "처음 topology를 실행할 때는 항상 계산하고 그 계산된 값이 나머지 최적화를 진행할 때 재사용"). 넷별 뿌리 경로도 쓰기 계획 블록이 실행당 한 번 쓰고 소비자가 읽는다(O-14 (1)). 새 캐시는 만들지 않는다. **블록 안 local memo는 허용한다**(O-15 (E)): 수명은 그 블록 호출 하나, 상한이 있어야 하고, 블록 밖으로 나가지 않는다. 블록 안에서도 같은 인자 반복 계산은 0이어야 한다. 예: `start_intervals`의 `bracket_root` 뒤 `solve(candidate)`(`E/search/start_intervals.py:392-394`)가 탐색 중 이미 푼 같은 점을 다시 푸는 것은 금지다(그 점의 상태를 local memo에서 읽는다). 재사용은 상위 WP-10(315행 -- 반복 안 계산은 쓰는 순간 캐시, 근거는 cProfile과 중복 인자 계측)대로 계측으로 보인다: cProfile과, **블록 밖 함수를 포함한** 같은 인자 반복 호출 계수 0(완료 조건 9) |
| NFR-G5 | **만들면 배선**: 새 필드·검사는 만드는 변경에서 소비자에 배선한다. 소비자 없는 기록은 만들지 않는다. 소비자를 다른 card로 미루는 것은 부채 목록 항목 + 사용자 승인(U-G6)이다 |
| NFR-G6 | **fail-closed**: 규칙 L은 정적으로 풀지 못하면 위반이다. 새 검사는 거부를 먼저 보인 뒤 통과를 본다. 조용한 대체·생략은 금지다. 지우는 모듈이 가진 정지는 지우기 전에 옮긴다. 실패 표지는 다른 설정(매크로 목표 해제 등)으로 꺼지지 않는다 |
| NFR-G7 | **작성자≠검증자**: card 0 측정, 부채 목록 기준선과 그 지문, 항목 제거 확인, 변경 종류별 판정(결정성·필드별 비교·값 변화표, N4-0), 13회로 계수는 검증자가 한다. 규칙 L 코드와 거부 픽스처는 test 역할이 쓴다 |

---

## N2. 확정 결정과 상위 계획과의 관계

| ID | 결정·원칙 | 출처 |
|---|---|---|
| O-10 | (2) graph 소비 정합 새 기능 계획 착수: 구조 규칙 L(L-1 writer 밖 실제 읽기 ≥ 1, L-2 출력 전용 선언·진입점 도달, L-3 블랭킷 READS 금지, L-4 하위 칸 reader, L-5 정본 술어 재계산 거부). 기존 위반은 card id를 붙인 줄어들기만 하는 목록. 필드별 처리(지정 소비자가 있으면 배선, R1·R2는 정본 읽기로 교체, 나머지는 출력 전용 선언 또는 삭제 -- 삭제는 승인). R3 정의역 차이는 공동분석.<br>(4) KCL: 새 전류 사슬 만들지 않음. `start_intervals.py:117-119` 음수 전류 자리값 조용한 대체는 충돌 기록으로(graph 소비 정합 또는 headroom-chain 출발 구간 card). 종속 전류 구간 결합 (a)~(c)와 DC 저항 θ 기저 방향 표현은 백로그 | 사용자 2026-10-16 "v0.6.5 승인, 나머지 세 가지는 권고대로"(`user_decisions.md` 628행) |
| P-1 | 규칙에서 가장 중요한 원칙은 물리적 사실과의 정합성이다. 임의로 제한하거나 특정 응용에만 맞추기 전에 항상 가장 일반적인 규칙으로 적용될 수 있는지 확인한다 | 사용자 2026-10-16(`user_decisions.md` 619행) |
| KK-1 | 계산식을 쓰기 전에 graph에 이미 계산되어 있는지 확인하고 그것을 쓴다. 엔진은 KVL·KCL에 따라 계산을 수행해 결과를 내야 하고, 그 관계가 엔진에 적용되어 있는지 확인한다(원문은 N1.1) | 사용자 2026-10-16(오케스트레이터 전달). 역할 agent 절차 반영: `agents/gmid-code-author.md`·`agents/gmid-verification-auditor.md`(커밋 `3ddb27c`) |
| B2 | DEC-64 v1 입력 포트 차 고리는 계획대로 제약을 만들지 않고, 커널 쓰기 계획(`input_tie`로 v1 고리 멤버 종속)을 계획에 맞게 고친다 | 사용자 2026-10-12 "B는 권고대로"(`user_decisions.md` 225행), design 41 §6.7-1a·§6.7-10 (P4) |
| K-3 | 입력 DC 미선언 시 입력 포트를 같은 DC로 묶던 `input_tie`(U2 기본안 (a)) 폐기, 대칭 포트는 U2 자기동형 묶음(`domain.ties`)이 대신, 구현 순서는 결정 6(d/s 맞바꿈) 다음. **이 순서 조건은 이미 충족됐다**: 결정 6(상위 U-62, 닫힘)은 U17 ①-d 병합 `c8d156e3`으로 들어갔고 이 worktree HEAD의 조상이다(F-G36) | 사용자 2026-10-12 "K-1~K-3도 권고대로"(`user_decisions.md` 243행), design 41 §6.7-1a |
| O-13 | (1) DEC-64 v1 해석 (가): 같은 DC 등식은 없앤다. 포트 경로가 둘 이상인 v1 고리는 ΔV를 소거한 KVL 하나가 남고(파일럿 VGS1a − VGS1b = VGS4a − VGS4b, M1b `cycle_vgs`), 대칭이면 묶음과 중복이다. 정정 자리는 design 41 1499행·IT-1·headroom-chain N0.1·155행·이 계획 P-G1 자리다.<br>(4) 이 계획 v0.7의 U-G 권고 전부: U-G1 (가), U-G3 항목별 삭제(card 0 대조 일치 항목), U-G4 (가), U-G6 미룸, U-G8 넣기, U-G9 (가), U-G10 오라클 대조·U16 완료 조건, U-G11 (가), U-G12 GC-2·GC-3·GC-8 착수 승인(GC-8은 B-G2 뒤 재질문), U-G13 (가) + 아래 끝 전류 충돌 경우 (가-1)(X-G11 원래 취지와 다름 승인) | 사용자 2026-10-19 "1~5까지 권고대로"(`wt/_drafts/user_decisions.md` 632행) |
| O-14 | (1) 재계산 빈틈 (가′): U-G1 뼈대(KVL 정본 = 쓰기 계획 출력, 별도 사이클 블록 없음) 유지, 단 쓰기 계획 블록이 넷별 뿌리 경로(변 열·부호, θ 무관)를 자기 출력 S0 필드로 한 번 쓰고 소비자 셋(이 계획 M-G1/GC-2, headroom-chain κ_n, design 41 §6.7 의존 묶음)이 읽는다(O-13 (4) U-G1 (가)의 '경로 저장 안 함' 부분 개정). 이 계획과 headroom-chain의 완료 조건에 WP-10 계측(cProfile + 블록 밖 함수 포함 같은 인자 반복 호출 0).<br>(2) 상위 계획 v6.16 card IT-1/IT-0 승인(master `f2852c36` 병합) | 사용자 2026-10-19 "1은 (가′), 2 승인, 3 기본안, 4 권고대로"(`wt/_drafts/user_decisions.md` 633행) |
| O-43 | 전체 정합 검증(근거 `wt/_drafts/evidence/2026-10-19/full_audit_summary.md`) 결정. 이 계획에 걸리는 것: D2 -- 사용자 결정 H-B(R-1′ 관계식 거르기)를 새 층 0(gain-budget LA-1)의 국소 봉인 후보·조립점·수리점에 적용하고, Halton·상자 중심은 층 0 무동작 회로 출발점으로만 남긴다(FX-1·GC-5는 그 경로에서 유지 -- 이 경로는 gain-budget v6.19 `6ab294c9` LA-1 범위 6·DEC-73 (3)(b)와 headroom-chain `a2ae9df6`대로 **층 0 무동작 회로 + 층 0 조립 실패 경로(LA-Q2 (b))** 의 출발 경로다), headroom-chain·이 계획에 LA-1 대응 행(N7.2) | 사용자 2026-10-19 "권고대로"(`wt/_drafts/user_decisions.md` 663행) |
| O-36 | (1) X-G13 승인: `size_and_seal_local`은 지우지 않고 gain-budget v6.19 card LA-1이 배선할 때까지 '배선 대기'(원래 취지와 다름 승인, 기한 = LA-1 병합). (2) GD-14: 규칙 L-1을 '호출자 0 내부 함수' 탐지로 확장(넣기) | 사용자 2026-10-19 "권고대로"(`wt/_drafts/user_decisions.md` 656행) |
| O-34 | (1) 변경 종류별 판정 기준: 결정성 = 비트 동일(항상), 순수 리팩터링 = 필드별(이산 정확 + 연속 분해능, NFR-4), 동작 변경 = 정의 오라클 toy + 봉인 불변식 + SPICE oracle 대조 + 검증자 값 변화표(원인 미설명 0), 기준선 갱신은 변화표 근거, 사용자 승인은 원인 미설명 변화가 있을 때만. 각 계획의 '비트 동일' 완료 조건을 변경 종류 표시로 정리(N4-0) | 사용자 2026-10-19 "1, 2 모두 승인"(`wt/_drafts/user_decisions.md` 654행) |
| O-26·O-27·O-32·O-33 | O-26 (1): `ls_swing` 자체 제약계·VGS 휴리스틱 삭제, 스윙·ICMR은 DC 동작 범위로(gain-budget v6.19 card DE-1) → GC-8에서 `ls_swing` 제외. O-27: layout 동작점 사본(`LayoutInput`·`ly_point`)을 card id를 붙여 GC-1 부채 목록에 등록, 해소 card = 'layout 입력 정본화'(gain-budget LI-1). O-32: 대신호 양도 엔진은 gm/ID 손계산, 정확도는 SPICE oracle로 검증(이 계획에 직접 걸리는 문언 없음). O-33 (1): 착수 전 블록별 cProfile 기준선(WP-10). O-33 (9): 선언 triode는 DC 범위 정의에서 포화 조건 제외, R-1′ on_mask VDS 하한은 'LUT 정의역 하한 항'이라는 다른 개념·다른 이름 | 사용자 2026-10-19(`wt/_drafts/user_decisions.md` 645·646·652·653행) |
| O-15 | 원칙 감사(사용자 2026-10-19 'graph에 값을 유지하는 것은 함수마다 재사용을 해서 반복계산이나 서로 다른 값을 사용하는 것을 막기 위해서') 결과. 이 계획에 걸리는 것: (A) U-G4 범위 보완 -- 칸별 전도 술어를 LUT memo 파생 `conduction_mask(kind, w_key)` 하나로, `sctx.cell_floors` 캐시 제거, `dc_conduction_floor` 출력 전용 유지(GC-7). (C) 위쪽 방향 차분 제약 그래프는 R-1′ 변 목록을 정본으로(정본·개념 정의는 headroom-chain v0.7.5 N3.4, 이 계획은 `headroom_bound`·`order_terms` 배선 -- GC-8, O-16 (3) 문구 정정 포함. `ls_swing`은 v0.11에서 빠짐 -- O-26 (1), gain-budget DE-1). (E) 범위 확장(X-G12, GC-9·GC-5·완료 조건 3·NFR-G4) | 사용자 2026-10-19 "A~E 권고대로, oracle 승인"(`wt/_drafts/user_decisions.md` 634행) |
| X-22 | card B로 낡은 `structure.json` rule_hash 재기록 승인(Role: data). 지문을 판정 로직에만 묶는 개선은 백로그 | 사용자 2026-10-16 "모두 권고대로"(`user_decisions.md` 629행), 백로그 `wt/_drafts/engine/U17_FOLLOWUPS.md` 58행 |
| S-7(상위 관행) | 계획과 다른 부분이 생기면 계획부터 고친다 | 사용자 2026-10-16(offset-strategy N2 S-7) |
| X-20·X-21 | 블록 결과 색인 키 = (블록, 분할, 입력 판)뿐, 실행 바깥 지문 금지, 디스크 저장 금지 | `user_decisions.md` 611·612행 |
| (원칙) | 만들면 반드시 배선한다. 배선할 수 없으면 승인을 받는다 | 사용자 전역 원칙 |

**이 계획과 관계된 상위 항목**(줄 번호는 master `5fea301`):

| 상위 항목 | 위치 | 상위 내용 요지 | 이 계획에서의 관계 |
|---|---|---|---|
| DEC-83 | 282행 | 단일 정본 = Circuit State Graph. 설계 상태는 graph 필드로만, 필드마다 writer 1개. S0 수준 파생값도 graph 필드 | 규칙 L은 '필드는 있는데 아무도 안 읽음'과 '필드가 있는데 다시 계산함'을 막아 DEC-83을 소비 쪽에서 완성한다. 쓰기 계획 출력도 S0 graph 필드이므로, KVL 정본을 거기 두는 것은 DEC-83 안이다(N3.3) |
| FR-9 | 179행 | 개념 하나에 이름 하나·저장 위치 하나 | 같은 관계의 두 인코딩(S1 관계 필드 대 커널 재유도)을 하나로 줄인다. 용어 Gs⁺를 headroom-chain과 통일한다. 트리 경로는 쓰기 계획 블록 자기 출력 필드 하나(저장 위치 하나, writer 하나)이고 소비자는 그것을 읽는다(O-14 (1)) |
| G_vgs 용어 | 92행 | G_vgs = MOS gate–source 무향 엣지와 레일 병합 고정 노드, 기본 사이클을 `equal_vgs`/포트 차/`kvl_branch`/VDS 하나 부등식으로 분류 | Gs⁺(쓰기 계획)로 개정 대상(N3.10) |
| NFR-2 · WP-23 | 186행 · 328행 | 같은 값을 다시 계산하지 않는다. S0 수준 블록은 실행마다 처음 한 번 계산하고 재사용한다 | 정본 우회 재계산 제거(규칙 L-5), 블랭킷 READS 제거(규칙 L-3). 새 보조 검사는 θ 무관이라 S0에서 한 번. 트리 경로 재구성은 함수 하나 |
| DEC-64 | 263행 | G_vgs 스패닝 트리 비트리 변마다 기본 사이클 = KVL. v0 `equal_vgs`, v1 포트 차 루프(입력 DC 미선언이면 '동일 가정' 기록, 제약 없음), v2 `kvl_branch` 등식. **루프 소속은 S1 관계 엣지 `kvl_branch`로 기록**. 측정 기대(J12-c) | 정본을 쓰기 계획 출력으로 옮긴다 → **X-G1**. v1은 O-13 (1)대로다: 같은 DC 등식은 없고(B2·K-3), 포트 경로가 둘 이상이면 ΔV를 소거한 KVL 하나가 남으며, 대칭이면 묶음과 중복이다. 상위 263행 v1 문언은 상위 계획 card IT-1 반영 커밋 `3fd202b`(상위 계획 v6.16)에서 O-13 (1) 문언으로 정정됐고 master `f2852c36`에 병합됨(O-14 (2) 승인). 이 계획은 그 문언을 고치지 않는다. v0.1의 X-G2는 철회 |
| DEC-15 | 215행 | `kvl_branch` 멤버는 S1 관계 엣지로 기록, DC 역할은 바꾸지 않음 | X-G1과 같이 개정 |
| DEC-17 | 217행 | L 동치류 주인 tail = `kcl_group`에서 공통 source 전류를 공급하는 바이어스 전류원 | 실제 tail 판정은 `kcl_group`을 읽지 않는다(F-G25). 문언을 그 정의로 맞춘다(N3.10, 사실 정정) |
| S1 구조 | 400행 | 관계 엣지 type 9종(`equal_vgs`·`vds_eq_vgs`·`stacked_vsb`·`matching_ratio`·`kcl_group`·`kvl_branch`·`same_as`·`l_class`·`matching_offset`), '개념마다 정의 하나' | 9종 중 `stacked_vsb`·`same_as`는 S1 관계 엣지로 구현되지 않았다(F-G29). 소비자 0이거나 정본 사본인 관계 엣지를 지우면 이 목록이 바뀐다 → **X-G7**, U-G3 |
| LR5 | 553행 | 초기 L 목표: 미러(`equal_vgs` 멤버) = kind별 knee | `equal_vgs` 멤버를 `gs_groups` 멤버로 문언 개정(N3.10) |
| V9 | 920행 | 물리 불변식 검증: `matching_offset` 멤버의 (W/L, gm_id) 일치, `matching_ratio` 멤버의 (W/L 비 = 선언 비율, gm_id 일치) -- contracts test | 엔진 소비자는 0이지만 **검증 소비자로 지정돼 있다**(F-G34). 삭제 전에 V9의 멤버 출처를 `matching_groups`·`gs_groups`로 옮기는 상위 개정이 필요하다(N3.10) |
| DEC-70 · DEC-08 | 269행 · 208행 | DC 원소 전류 = θ 전류 기저의 선형식. 선언 이상 전류원은 고정값(DEC-08 상태 '부분(KCL 잔차 metric만 소비)') | KCL 정본 = `dc_current_basis`(N3.4). 'KCL 잔차 metric'(`kcl_residual_amp`)은 결선 행렬 항등식이라 판정을 더하지 않는다(F-G21). 상태 칸 문언을 사실로 맞춘다(N3.10) |
| DEC-88 · N3.6 봉인 표 | 287행 · 461-477행 | W = ID·L/IDu. 봉인 2 VGS 정합, 봉인 3 KCL 잔차 ≤ tol_I, 봉인 8 `kvl_branch` 등식('봉인 1·2가 통과하면 자동 성립하므로, W2 블록이 등식을 풀지 않은 경로를 잡는 게이트') | 472행이 봉인 8에 맡긴 일은 봉인 2가 θ마다 소자별로 이미 한다(F-G31). 처리는 U-G9. 봉인 3은 봉인 2와 상관된 더 엄격한 집계임을 사실로 적는다(X-G4) |
| DEC-27 | 227행 | VDS-1 루프 전압을 gm_id 탐색 상한으로 | headroom-chain이 대체한다. 이 계획은 `gvgs_summary`의 나머지 칸만 다룬다 |
| DEC-95 (3) | 294행 | 종속 gm_id 소자 선택의 구조 순서 | 쓰기 계획이 이 순서로 고른다. 새 선택 규칙 없음 |
| N6.3 | 1153행 | 병합 전 graph 단일 정본 확인(G-8 lint 등), `graph_canon_check`·`reuse_check` 보고 | 규칙 L이 그 확인의 '소비' 쪽 기계 검사가 된다. 보고 칸에 규칙 L 계수를 더한다 |
| N6.1 단위 8 | N6.1 표 | 층 0 전체판 + GB3 결합변수 y | `graph/coupling` 3필드의 지정 소비자다(N3.2) |
| design 40 §2.4.8 | 필드 소유표 | 필드·writer·층 | reader 칸이 없다. 규칙 L-1이 reader를 기계 판정한다. 소유표에 reader 칸을 더할지는 GD-6 |
| design 41 §5 | 589행, 917행 | 층 0 등식 목록(`equal_vgs`·`stacked_vsb`·`kvl_branch`), §5.5 조립 공유량(`equal_vgs` 공통 VGS, 미러 비, `kvl_branch` 종속 gm/ID) | 관계 엣지 이름을 정본(`gs_groups`, 쓰기 계획 출력)으로 개정(N3.10, GD-8) |
| design 41 §6.7-1 | 1491-1494행 | 'KVL 고리의 출처 -- 새 탐지기를 만들지 않는다': 쓰기 계획(`node.dc_writer` + `device.dc_coord`)을 읽는다. 1491행은 쓰기 계획을 'S1 G_vgs 고리(`graph.rel_kvl_branch`)를 … 컴파일한 것'으로 적는다 | KVL 정본 = 쓰기 계획 출력(BD-1)과 같은 방향이다. 1491행의 `rel_kvl_branch` 출처 문언은 개정 대상(N3.10) |
| design 41 §6.7-1a | 1496-1500행 | 입력 DC 미선언이면 '같은 DC' 엣지를 넣지 않는다. 대칭 포트 y는 `domain.ties`로 묶는다. '종속 수 = 순환수 불변식은 같은 DC 엣지 없는 G_vgs 기준'. 구현은 별도 card(§6.7-10 P4) | KVL 정본 정의에서 tie 변 제외. 숲 불변량(N3.5-3)도 이 기준이다. GC-2는 K-3 구현 card 뒤(N7.2) |
| design 41 §6.7-10 | 1533행 | (P1) 층 0은 `kvl_branch` 등식을 조립 단계에서 푼다 | `kvl_branch` 이름을 쓰기 계획 종속 분류로 개정(N3.10) |

---

## N3. 규칙·정의·구조

### N3.0 현황 사실(읽기 확인, master `5fea301`)

| ID | 사실 | 근거 |
|---|---|---|
| F-G1 | 권한표 필드는 131개다(S0 117 + layout 14). `@compute_block` 블록은 53개이고, 그 READS·WRITES는 정적 해석으로 모두 풀린다(미해석 0) | 재측정 history H2-1 |
| F-G2 | writer 밖 실제 읽기가 0인 필드는 26개다: test만 읽음 24, 아무도 안 읽음 2(`graph/stage_b`의 `residual_probe`·`dof_numeric`). 목록은 N3.2 표 | 재측정 history H2-1 |
| F-G3 | 출력 함수에서만 읽히는 필드는 14개다.<br>• 정상 8개(출력 함수가 진입점에서 도달하고 필드 인자가 모듈 수준 tuple로 풀림): `graph/ach: area_bound·buffer_window_report·count_budget·curve_checks·dof·headroom_rows·verdict·warnings`(단계 B 보고, `E/pipeline/stage_b.py:117-118, :123-124`)<br>• 동적 접근으로만 읽히는 2개: `graph/s1v: applied_facts·declared`(`E/graph/structure_tables.py:33`의 이름 tuple 루프만 읽는다. `E/pipeline/stage_a.py:100`의 `"applied_facts"`는 실패 보고 사전의 키 문자열이지 필드 읽기가 아니다)<br>• 문제 4개: `graph/layout: ly_rows`(유일한 reader `E/layout/outputs.py:44 layout_outputs`의 엔진 안 호출자 0), `graph/coupling: vars·column_block_map·bias_columns`(단계 A 보고만 읽고, docstring은 소비자를 층 0 조립으로 지정, `E/pipeline/stage_a.py:12-15`) | 재측정 H2-1, H2-6 |
| F-G4 | KCL: 전류 기저는 레일이 아닌 넷마다 KCL 행을 세워 유리수로 푼다. 미지수는 S1 `device.dc_nets`가 있고 잎 가지치기되지 않은 원소 전류다. 원소 방향(`_ends`)은 핀과 kind로 정한다. 커널의 원소 전류는 기저 행으로 정확히 계산된다 | `E/sizing/current_basis.py:1-14, :48-54, :86-88`, `E/sizing/block_currents.py:24` |
| F-G5 | KVL(as-built): 쓰기 계획은 F = 레일 ∪ 노드 목표 ∪ (입력 DC 선언 시) 입력 포트, G_vgs = MOS (gate, source) + 저항(잎 가지치기된 저항 포함) + 미선언 입력 포트 '같은 DC' 변으로 Kruskal 숲을 만든다. 비트리 MOS 변은 `fixed_vgs`·`parallel_vgs`·`cycle_vgs`로 종속된다. 비트리 저항 변은 `dc_resistor_cycle`로 멈춘다. 노드전압은 트리 변 식으로 쓰이므로 모든 등식 루프의 KVL은 항등으로 성립한다. 종속 소자의 ln IDu는 노드 VGS 순방향 LUT 값이다 | `E/sizing/writer_plan.py:8-27, :146-196`, `E/sizing/block_columns.py:749` |
| F-G6 | S1 `s1_gvgs`는 다른 G_vgs를 만든다: F = 레일만, MOS 변만(저항·같은 DC 변 없음), 평행 변은 이름순 첫 소자 하나, 입력 포트 단계별로 숲을 키운다. 출력은 `rel_kvl_branch`(v2)·`gvgs_summary`(개수 4칸·`fixed_vgs`·`port_diff`·`vds_saturation`)다 | `E/graph/gvgs_cycles.py:1-23, :56-118` |
| F-G7 | S1 관계 필드의 엔진 소비자:<br>• `rel_kvl_branch`: 봉인 8만(`E/sizing/seal_kvl_branch.py:18, :28`)<br>• `rel_equal_vgs`: `E/graph/coupling_vars.py:94`만(그 출력은 보고 전용, F-G3)<br>• `rel_l_class`: `E/graph/l_classes.py`(L 동치류)<br>• `rel_kcl_group`·`rel_vds_eq_vgs`·`rel_matching_ratio`·`rel_matching_offset`·`gvgs_summary`: 0(검증 소비자는 F-G34)<br>`graph.gs_groups` docstring은 '`equal_vgs`·`matching_ratio`·`l_class`가 이 필드 하나를 읽는다'고 적는다 | grep(tests 제외), `E/graph/gs_groups.py:1-8` |
| F-G8 | 봉인 8은 S1 `rel_kvl_branch` 사이클만 돌며, 멤버별 \|ln IDu_forward − ln IDu\|/(gm/ID)의 합 ≤ 멤버 tol_V 합을 잰다. 사이클이 0개면 행이 0이다 | `E/sizing/seal_kvl_branch.py:1-33` |
| F-G9 | 봉인 3은 원소 결선을 기저의 `basis.ends`에서 그대로 받는다. MOS 전류 = `idu_forward`·W/L이고, W = ID·L/exp(ln IDu)다(W_request 소자는 요청 W). 저항 전류 = 노드전압 차/R, 이상 전류원 = `dc_current`. MOS가 있는 넷의 허용오차는 max(tol_V·gm), MOS 없는 넷은 부동소수 한계 식이다 | `E/sizing/seal_kcl.py:36-60`, `E/sizing/block_widths.py:47` |
| F-G10 | 공급 전류 합 `kcl_residual_amp` = Σ 레일 전류는 계산되어 결과 묶음 detail로 실려 가지만, 판정하는 곳은 없다 | `E/metrics/supply.py:10, :70`, `E/metrics/dc_metrics.py:130`, `E/search/objectives.py:28`, `E/search/search_values.py:141` |
| F-G11 | MNA 풀이는 특이면 NaN + undefined로 남기고, 풀이 잔차나 조건수는 기록하지 않는다 | `E/metrics/mna_solve.py:1-12`(잔차 grep 0) |
| F-G12 | 출발 구간 `_state`는 θ 자유 원소 전류가 0 이하면 '정해지지 않음'으로 센다(117행). MOS 전류가 0 이하면 None으로 바꾼다(119행). None인 소자마다 자리값 max(정해진 전류 기하평균, W_min·IDu/L)을 **소자별로** 둔다(128행). 자리값은 기저 행을 거치지 않는다. 자리값이 하나라도 없으면 면적 추정은 None이다(131-132행) | `E/search/start_intervals.py:108-133` |
| F-G13 | 정본 술어 우회 재계산 자리:<br>• diode 판정(`g == d`) metrics 2곳: `E/metrics/block_gain_model.py:166`, `E/metrics/ls_swing.py:46`(이 자리는 `ls_swing._constraints`(39-50행, VGS 휴리스틱 조건) 안이라 O-26 (1) gain-budget card DE-1의 삭제 범위다. DE-1이 GC-6보다 먼저 병합되면 대상 코드가 사라져 부채 항목도 지운다)<br>• diode 판정 graph 층 안 4곳(3파일): `E/graph/cells.py:53, :117`(속성 꼴 `m.g == m.d`), `E/graph/net_model.py:75`, `E/graph/node_impedance.py:22`<br>• (gate, source) 묶음 metrics 1곳: `E/metrics/block_gain_model.py:170`<br>• (kind, gate, source) 묶음을 쓰기 계획이 트리 변에서 다시 만듦: `E/sizing/writer_plan.py:186`(변수 경유 꼴: 트리 변 tuple에서 풀어 낸 `a`·`b`로 키를 만든다)<br>정본 writer는 `E/graph/s1_structure.py:67`(is_diode), `E/graph/gs_groups.py`(gs_groups)다 | grep(tests 제외) |
| F-G14 | VGS = 0 누설 전류·전도 술어를 네 곳이 계산한다: 봉인 9(`E/sizing/seal_conduction.py:27-31`, 필드 `dc_off_current`·`dc_conduction_floor`의 writer), search 칸 하한(`E/search/cell_floor.py:53-85` `_conduction_floor`, 캐시 `sctx.cell_floors`), search 전류 상자(`E/search/current_box.py:20-33`), **LUT memo 파생 `edge_costs`의 전도 마스크**(`E/lut/derived_fns.py:36-47` `_conduction_ok`, 63-74행에서 사용 -- O-15 (A)로 추가). 격자판 전도 술어 둘(`_conduction_floor`·`_conduction_ok`)은 마스크가 다르다(분지 요구, VGS = 0 마디의 on 검사, `zero_first`가 아니면 누설 조건을 없앰). VGS = 0 마디 찾기도 세 가지다(`current_box.py:24` ulp, `cell_floor.py:58` spacing, `derived_fns.py:43` 첫 마디만). 봉인 9의 소자별 I_off 동작점 보간(`seal_conduction.py:26-31` `_off_current`)은 **검증 경로(판정 권한)라 단일화의 예외**다(사용자 결정 O-16 (3) 표시 보완). 봉인 9 docstring은 'search가 읽는 하한'과 '오라클 `off_current_A`(pipeline `oracle_input`이 내는 값)'를 소비자로 적는다. 새 엔진에 `oracle_input`을 내는 엔진 코드는 없다(생산자는 gain-budget card EO-1). 사용자 결정 O-46 (2)로 oracle 합격 판정은 `off_current_A` 스칼라를 쓰지 않게 되므로(I_off = SPICE op 점의 VDS·VSB에서 읽은 엔진 LUT 값), `dc_off_current`의 oracle 소비는 EO-1~OP-5 사이(옛 ε = 1 판정)에만 있다 | `E/sizing/seal_conduction.py:8, :12-13`, grep `oracle_input` |
| F-G15 | 블랭킷 READS: `build_s1v`(`E/graph/s1v_fields.py:249`)와 `coupling_vars`(`E/graph/coupling_vars.py:170`)가 S1 필드 전부를 선언한다 | 해당 줄 |
| F-G16 | 구조 test는 규칙 A~I·K와 복사 등록부다(`E/tests/structure/structure_checks.py`, 1191행). writer는 있는데 reader가 없는 것, 정본 우회 재계산을 잡는 규칙은 없다 | `E/tests/structure/structure_checks.py:321-1191` |
| F-G17 | 하위 칸 계수: 엔진 frozen dataclass 337개, 칸 2047개 중 엔진 읽기 0인 칸이 292개다. 이 수는 graph 필드 값 형식에 한정하지 않은 전체이고, 이름 기반이라 하한이다 | 재측정 H2-2 |
| F-G18 | `graph.dc_current_basis`는 커널·봉인 3·θ 스키마·search·metrics가 읽는다. `current_cone`·쓰기 계획 출력(`node.dc_writer`, `device.dc_coord`)도 정상 배선이다 | 재측정 H2-1, `E/sizing/theta_check.py:48` |
| F-G19 | **K-3 미구현**: as-built 쓰기 계획은 입력 DC 미선언이면 F 밖 입력 포트를 이웃 쌍마다 '같은 DC' 변으로 잇고(키 순위 최상위), 트리 변이면 `input_tie`로 쓰며, 그 성분 뿌리의 y 키를 `INPUT_GROUP_KEY`로 둔다. K-3 구현 card는 상위 계획 card **IT-1**(상위 N6.5, card 정의는 master `f2852c36`에 병합됨 -- O-14 (2) 승인. 구현은 아직)이다. red test는 `E/tests/sizing/test_writer_plan.py` 안의 새 test 함수다(상위 X-IT3 -- design 41의 test 파일 경로를 구조 규칙 H 때문에 바꿈) | `E/sizing/writer_plan.py:10-11, :104-105, :157-159, :213-214, :234`, design 41 §6.7-1a·§6.7-10 (P4) '구현은 별도 card' |
| F-G20 | **self-edge 정지**: MOS gate = source가 같은 비레일 넷이면 `s1_gvgs`가 `gvgs_self_edge`로 멈춘다(core `StructureUnresolvedError`, reason `unsupported_rule_branch`). gate·source가 둘 다 레일이면 멈추지 않고 `fixed_vgs`로 기록한다. 이 정지의 엔진 안 사용처는 이곳 하나다. 쓰기 계획은 같은 소자를 비트리 MOS 변으로 받아 `cycle_vgs`(gate·source가 F 점이면 `fixed_vgs`)로 분류하고 멈추지 않는다 | `E/graph/gvgs_cycles.py:68-79`, `E/graph/s1_values.py:125`(grep 사용처 1), `E/sizing/writer_plan.py:164-167, :176-196` |
| F-G21 | **공급 전류 합은 결선 행렬 항등식이다**: `metrics_dc`는 기저 `ends`와 커널 `dc_current`(기저 행 값)로 동작점을 만들고, 레일 전류는 같은 가지 전류를 레일 노드에서 더한 값이다. 모든 가지는 한 넷에서 나와 다른 넷으로 들어가므로 Σ(모든 넷) = 0이 항등이고, Σ 레일 전류 = −Σ(내부 넷 KCL 잔차)다. 내부 넷 KCL은 기저가 정확히 풀었으므로 이 합은 부동소수 반올림만 남는다 | `E/metrics/dc_metrics.py:73-90`, `E/metrics/supply.py:26-44, :70` |
| F-G22 | **결선 대조는 항등식이다**: 기저 원소 = `device.dc_nets`가 있고 가지치기되지 않은 원소이고(`E/sizing/current_basis.py:86-88`), 넷 쌍은 같은 `device.pins`에서 나온다. `node.terminals`도 같은 핀에서 만든다(`E/graph/s1_structure.py:51, :55`) | 해당 줄 |
| F-G23 | **오라클 KCL·KVL 대조**: forced 모드는 소자 단자 넷마다 예측 전압의 고정원을 choke로 걸고(`O/oracle_netlist.py:486-497`), 넷별 고정원 전류 `hold_current_A`(= SPICE 모델로 잰 그 넷의 KCL 잔차)를 `kcl_abs_A`로 판정한다(`O/oracle_compare.py:365-367`). free 모드는 SPICE가 푼 노드전압을 예측과 대조한다. 엔진 → 오라클 입력 생성은 U16이고, 새 엔진에 그 코드는 아직 없다 | 해당 줄 |
| F-G24 | **rule_hash 대상 파일**: `structure_rule_fp` = `S1V_RULE_FILES`(27파일: `cells.py`·`net_model.py`·`node_impedance.py`·`s1v_fields.py`·`l_classes.py` 포함) + `STRUCTURE_RULE_EXTRA_FILES`(`composite_diode.py`·`dc_roles.py`·`gs_groups.py`·`matching_groups.py`)의 파일 바이트 지문이다. 저장소의 `structure.json`은 2개다(library) | `E/graph/s1v_values.py:14-21`, `E/graph/s1v_key.py:25, :29`, `git ls-files` |
| F-G25 | **tail 판정**: L 동치류 주인의 tail은 'DC 역할이 바이어스 전류원이고 drain이 둘 이상 소자의 공통 source 넷인 멤버'다. `rel_kcl_group`을 읽지 않는다 | `E/graph/l_classes.py:7-9` |
| F-G26 | **S1 관계 사본**: `rel_equal_vgs`는 `gs_groups` 묶음을 하나씩 그대로 다시 담는다. `rel_l_class`·`rel_matching_ratio`는 gate가 레일이 아닌 `gs_groups` 묶음을 다시 담는다. `rel_vds_eq_vgs`는 `is_diode` 참인 소자를 다시 담는다 | `E/graph/rel_vgs.py:31-37`, `E/graph/rel_matching.py:35-40` |
| F-G27 | **도달하지 않는 reader**: `size_and_seal_local`의 엔진 안 호출자는 0이다(정의 파일 밖 grep 0). 이런 함수 안의 읽기는 규칙 L-1에서 읽기로 치지 않는다 | `E/sizing/size_and_seal_local.py:113`, grep(tests 제외) |
| F-G28 | **MNA 풀이 방식**: ω = 0은 LU 1회, ω > 0은 `numpy.linalg.solve`(부분 피벗 LU) 묶음 풀이다. 부분 피벗 LU는 후진 안정이라 상대 잔차는 조건수와 무관하게 기계 엡실론 수준이다. 그래서 그 잔차는 해의 정확도를 알려 주지 않는다 | `E/metrics/mna_solve.py:6-9` |
| F-G29 | S1 구조 400행의 관계 엣지 9종 중 `stacked_vsb`·`same_as`는 S1 관계 엣지 상수·writer가 없다. `stacked_vsb`는 결합변수 K3 종류 설명에만 나온다 | `E/graph/s1_values.py:77-85`, `E/graph/coupling_values.py:17`, grep |
| F-G30 | 규칙 L-1의 정적 해석으로 풀리지 않는 동적 필드 접근(고정 허용 파일 밖): `E/search/search_context.py:69-70`(`_field(key, name)`), `E/graph/structure_tables.py:33`(이름 tuple 루프), `E/layout/canonical_naming.py:96`(`value = lambda field: ...`) | 해당 줄 |
| F-G31 | **봉인 8 = 봉인 2 양의 합**: 봉인 2는 θ마다 **모든 MOS**에 대해 \|ln IDu_forward − ln IDu\|/(gm/ID) ≤ tol_V를 판정한다(`E/sizing/seal_vgs_match.py:25`). 봉인 8은 같은 양을 사이클 멤버마다 더해 멤버 tol_V 합과 비교한다(`E/sizing/seal_kvl_branch.py:29`). 그래서 상위 472행이 봉인 8에 맡긴 일('W2 블록이 등식을 풀지 않은 경로')은 봉인 2가 소자 단위로 이미 잡는다 | 해당 줄 |
| F-G32 | **출발 실행 가능 판정의 빈틈**: `feasible`은 `within and not (use_macro and macro_failed)`다(`E/search/start_intervals.py:364-367`). 가장 느슨한 끝에서도 매크로가 풀리지 않으면 `use_macro`를 끄고(379-381행) 그 뒤에는 `macro_failed`를 보지 않는다. 면적 예산이 없으면 면적이 None이어도 `within`이 참이다. 사다리 아래 칸은 실행 가능 판정 없이 사다리에 들어간다(401-405행).<br>• **양 끝 모두 실행 불가일 때의 대체 경로**: 최상 칸이 실행 불가면 `final = bottom`(384행)으로 두고, 아래 끝도 실행 불가면 면적 충돌 하나만 기록한다(387-389행). 그 `final`이 그대로 사다리 칸 0이 된다(401행). t = 0이면 아래 칸은 없다(402행). `_report`는 `covered = {c for c, _v in rungs[0].theta}`(453행)로 칸 0을 무조건 읽으므로 빈 사다리면 IndexError다. 아래층 `layer0_start`는 `sctx.rungs or (None,)`(`E/search/layer0_center.py:656`)로 빈 사다리를 받아 상자 중심 한 점에서 출발한다(`:654-655` 주석, `_box_centre` `:126-135`).<br>• **1회차 전류의 소비처**: `first = _state(ctx, g_lo0, first_L)`(285행)의 MOS 전류는 None이면 `first.refs` 자리값으로 채워 `currents1`이 된다(286행). 소비처는 **네 함수, 여섯 호출 자리**다: `gain_l_bounds`(292행, `first.elements`), `matching_bounds`(295·332행), `area_bounds`(296·327행), `noise_bounds`(333행)(뒤 셋은 `currents1`). 전류·원소 값이 없을 때 처리는 함수마다 다르고, 비활성 사유로 남는 것은 일부뿐이다.<br>&nbsp;&nbsp;– `gain_l_bounds`: 비활성 경로가 없다. 원소가 `elements`에 없으면 `_row`가 None(`E/search/iv_gain_l.py:64-65`)이고 그 L 앵커를 건너뛴다(117-119행). 모든 앵커가 빠지면 `found = anchors[-1]`로 L 하한을 최대 앵커로 두고 `SRC_GAIN_L` '이득 목표 미달' 충돌을 기록한다(125-127행). 이 경로는 **지금도 살아 있다**: `start_intervals.py:117`이 0 이하 θ 자유 원소를 `elements`에서 빼기 때문이다. 원인(전류 없음)과 다른 사유(목표 미달)로 기록되고 L 하한이 강제된다.<br>&nbsp;&nbsp;– `area_bounds`: 전류가 None인 소자는 `_per_amp`가 None(`E/search/iv_area.py:57-58`)이라 68-69행 `continue`로 W_min gm/ID 하한을 **기록 없이** 건너뛴다. `WHY_NO_CURRENT`(83행)는 면적 예산이 선언됐을 때만 기록된다(예산이 없으면 81-82행에서 먼저 반환).<br>&nbsp;&nbsp;– `matching_bounds`: 절대 정합 목표나 offset 가드가 선언됐을 때, 입력·부하 소자 중 하나라도 전류가 None이면 117-118행에서 정합 L 경계(`SRC_MATCH_L`)와 가드 경계를 모두 내지 않고 반환한다. 사유는 `(SRC_OFFSET_GUARD, WHY_NO_CURRENT)` 하나뿐이라, 절대 정합 목표만 있고 가드가 없으면 `SRC_MATCH_L` 경계가 사라진 사유는 남지 않는다(`E/search/iv_matching_l.py:107-118`).<br>&nbsp;&nbsp;– `noise_bounds`: 잡음 가드 목표가 선언됐을 때만, 입력·부하 전류가 None이면 가드 경계를 `WHY_NO_CURRENT`로 비활성 처리한다(`E/search/iv_noise.py:73-78`).<br>θ 자유 원소가 아닌 원소 값은 117행의 부호 거르기를 받지 않고 `elements`에 남는다(115-117행) | 해당 줄 |
| F-G33 | **`NodeWrite`**: 넷마다 (tier, relation, element, `known` = 읽는 아는 쪽 노드, y_key, order)다. `known`이 숲의 부모 포인터다(F·W4 뿌리는 None) | `E/sizing/s2_values.py:268-277`, `E/sizing/writer_plan.py:211-220` |
| F-G34 | **검증 소비자**: 상위 V9가 `matching_offset` 멤버의 (W/L, gm_id) 일치와 `matching_ratio` 멤버의 (W/L 비, gm_id 일치)를 물리 불변식 검증(contracts test)으로 지정한다 | 상위 계획 920행 |
| F-G35 | **`gvgs_cycles.py` 등록 자리**: S1 지문 파일 목록 `S1_RULE_FILES`, 모듈 지도 `_module_map`, 패키지 공개 이름, S1 조립 import | `E/graph/s1_values.py:222-225`, `E/_module_map.py:98, :470`, `E/graph/__init__.py:29`, `E/graph/s1_build.py:35` |
| F-G37 | **기저 전류의 반복 계산(O-15 (E))**: 기저 행의 유리수 → float 변환을 `_mos_currents`가 `_state` 호출마다(`E/search/start_intervals.py:100`), `current_model`이 호출마다(`E/search/iv_currents.py:120`) 다시 한다(루프 불변). 같은 θ에서 MOS 전류를 유리수로 정확히 평가하는 곳이 셋이다: `E/sizing/theta_check.py:45-50`, `E/sizing/block_currents.py:31`, `E/search/cone_rows.py:16-24`. `theta_schema.current_cone`은 기저 MOS 행을 다시 담은 필드다(`E/sizing/theta_schema.py:30` '`current_cone`: KCL 기저 행 중 MOS 행마다') | 해당 줄 |
| F-G38 | **`_vds_floor`의 자리(O-15 (E))**: sizing의 `_vds_floor`(`E/sizing/block_columns.py:101-118`)는 LUT 슬라이스만으로 정해지는 값인데, LUT memo `derived` 영역에 sizing 모듈 안에서 등록한다(`lut.memo.lookup("derived", "sizing_vds_floor", …)`, 118행). 이 값은 R-1′의 'LUT 정의역 하한 항'(선언 triode 소자의 LUT on_mask VDS 하한, O-33 (9) -- 포화 조건과 다른 개념)으로 HC-1(search)도 쓰므로, `lut.derived`로의 이동은 GC-9가 아니라 headroom-chain HC-S(LUT 파생 포화·정의역 정본 card)가 HC-1보다 앞서 한다(오케스트레이터 기본안) | 해당 줄 |
| F-G39 | **부모 포인터 읽기 자리**: `NodeWrite.known`을 **한 단계**만 읽는 곳(아는 쪽 노드 값 읽기)은 여럿이다(`E/sizing/block_columns.py:309, :352, :430-434, :474-481, :760-765`, `E/search/layer0_center.py:485`). 포인터를 **두 단계 이상** 따라가는 곳은 같은 DC tie 사슬 두 곳이다(`E/sizing/block_columns.py:181-184`, `E/sizing/scc_order.py:122-127` -- 둘 다 IT-1 삭제 대상). `E/metrics/achievability.py:315-317`은 tie 관계를 한 단계 읽는다(같은 IT-1 대상) | 해당 줄, `git grep "\.known"` |
| F-G36 | **결정 6(d/s 맞바꿈)은 이미 병합됐다**: 상위 U-62는 닫혔고(사이징 결과는 선언 방향, 틀린 선언은 봉인 7 거부), 구현은 U17 ①-d 병합 `c8d156e3`이며 이 worktree HEAD의 조상이다(`git merge-base --is-ancestor c8d156e3 HEAD` 참). `s1_symmetry`가 MOS d/s 부호(`reverses_orientation`)를 계산하고, 전도 MOS 자기 맞바꿈은 `ds_self_swap_zero_current`로 멈춘다. headroom-chain v0.7.1도 'K-3의 순서 조건 결정 6 다음은 이미 충족'으로 적는다 | 상위 계획 1371행(U-62), `E/graph/s1_symmetry.py:14-15, :16-20, :125-133`, headroom-chain v0.7.1 490행 |

### N3.1 구조 규칙 L

모든 하위 규칙은 AST만 쓴다(엔진 import·실행 없음). 형식은 기존 규칙 A~K와 같다. 정적으로 풀지 못하면 위반이다(fail-closed).

1. **규칙 L-1 reader 존재**
   * 판정: 권한표(F-G1의 두 표)의 (kind, field)마다, writer 블록 함수 밖 엔진 코드(tests 제외)에 실제 읽기가 1곳 이상 있어야 한다.
   * **도달 조건**: 읽기를 담은 함수는 엔진 진입점(GD-1)에서 호출 그래프로 도달해야 한다. 도달하지 않는 함수(예: F-G27 `size_and_seal_local`)의 읽기는 세지 않는다. 도달을 풀지 못하면 위반이다. 호출 그래프는 규칙 L-2와 같은 것을 쓴다.
   * 필드 인자는 상수 해석으로 푼다. 모듈 수준 tuple을 도는 루프 변수는 그 tuple로 펼친다.
   * 동적 필드 접근은 고정 파일 목록(core 접근자와 봉인 판 검사)에서만 허용한다. 그 밖의 동적 접근은 위반(`field_arg_dynamic`)이다. 기존 동적 접근(F-G30)은 부채 목록에 '정적 해석 형태로 바꾸기'로 두고, 허용 파일 목록을 늘리지 않는다. 그 자리로만 읽히는 필드(F-G3의 `applied_facts`·`declared`)도 그 기간에는 reader 0으로 세어 부채 항목이 된다.
   * 읽기로 치지 않는 것: READS 선언, 실행 스냅샷 전체 덤프, 이름이 같은 다른 객체의 속성(예: 선언 객체의 `.value` 속성 -- 재측정에서 1건 확인, H2-1), 사전 키 문자열.
2. **규칙 L-2 출력 전용 선언과 도달**
   * 판정: 실제 읽기가 모두 출력 모듈에 있으면 그 필드는 출력 전용 목록에 있어야 한다. 목록 항목은 (필드, 출력 함수, 근거)다.
   * 출력 함수는 엔진 진입점에서 호출 그래프로 도달해야 한다. 도달을 풀지 못하면 위반이다.
   * **출력 모듈 판정 기준**(v0.11, 계획이 정한다): 함수가 출력 함수인 것은 (i) 그 함수의 반환값·부수 산출물을 읽는 엔진 reader가 0이고(엔진 진입점에서 도달하는 다른 계산이 그 값을 쓰지 않는다), (ii) 진입점에서 그 함수까지의 호출 경로가 결과 JSON·보고 경로(결과 JSON 작성, 단계 보고, 실행 기록)에만 있을 때다. 모듈 단위가 아니라 이 기준을 함수마다 적용하고, 출력 모듈 목록은 그 결과다. 목록의 구체 범위(파일·함수 이름)는 design이 이 기준으로 만든다(GD-1).
   * **GD-1 결과의 독립 검증**: 검증자가 GD-1의 진입점 목록과 출력 함수 목록을 위 기준으로 독립 측정 스크립트(규칙 L 코드가 아닌 것)로 다시 재고, design 목록과 다른 자리를 GC-1 판정 기록에 적는다. 다르면 GC-1을 멈춘다(기준선 지문에 묶이는 목록이라, 넓게 잡히면 기준 약화다).
   * **초기 출력 전용 목록**: F-G3의 정상 8개는 GC-1에서 처음부터 이 목록에 넣는다(부채 항목이 아니다). 동적 접근 2개는 GC-7이 `structure_tables.py:33`을 정적 형태로 바꾸는 변경에서 이 목록에 넣고 부채 항목을 지운다. 문제 4개는 부채 목록 '배선 대기'다(N3.2).
3. **규칙 L-3 READS = 실제 읽기**
   * 판정: 블록 READS의 열마다 그 블록 함수(그리고 투영을 넘겨받는 같은 패키지 함수 한 단계) 안에 그 열의 실제 읽기가 있어야 한다.
   * 블랭킷 선언(`S1_READS` 등)은 펼쳐서 같은 검사를 한다. helper를 따라가지 못하면 위반(`reads_unverifiable`)이다.
   * 근거: READS는 블록 입력 판(재계산 키)이다. 안 읽는 열이 READS에 있으면 그 열이 바뀔 때 결과가 같은 블록을 다시 계산하게 된다(상위 NFR-2 위반).
4. **규칙 L-4 하위 칸 reader**
   * 대상: graph 필드 값 형식(각 패키지 값 선언 모듈의 frozen dataclass, design 40 §2.4.10 ② 목록과 같은 출처)의 칸이다.
   * 판정: 칸마다 클래스 본문 밖 엔진 코드에 속성 읽기·상수 `getattr`·레지스트리 문자열 중 하나가 있어야 한다. 없으면 출력 전용 칸 목록이나 지문 전용 칸 목록에 있어야 한다.
   * 한계(알고리즘): 이름 기반이다. 다른 클래스의 같은 이름 칸 읽기도 읽힘으로 세므로, 죽은 칸을 놓칠 수는 있어도 살아 있는 칸을 죽었다고 하지는 않는다.
5. **규칙 L-5 정본 술어 재계산 거부**
   * 등록표: {개념: (정본 필드, writer 파일, 금지 AST 패턴)}. 패턴은 AST 노드 일치로 정의한다(문자열 grep 아님).
   * 초기 개념(기본안 BD-8): diode 판정(MOS gate 핀 = drain 핀 비교), 같은 VGS 묶음((kind, gate, source) 또는 (gate, source) 핀 tuple을 묶음 키로 쓰기). VGS = 0 누설·전도 술어는 U-G4 (가) + O-15 (A)로 정본이 LUT memo 파생 `conduction_mask(kind, w_key)`가 됐으므로, 그 술어(격자 VGS = 0 마디 찾기, 칸별 전도 마스크)를 등록한다(기본안, GC-7에서 정본이 생긴 뒤). **동작점 사본**(v0.11, 오케스트레이터 기본안 -- O-33 범위): O-27이 부채 목록에 넣으라고 한 layout 동작점 사본(N3.2 표)을 잡기 위해 등록한다. 탐지 정의는 다음과 같다(AST 정적 해석, 규칙 L의 다른 하위 규칙과 같은 방식).
     * **출처**: graph `column("device", "dc_op")`(또는 `value("device", …, "dc_op")`)에서 온 값, 즉 `DeviceOp`(`E/sizing/s2_values.py:381-396`)와 그 칸이다. 출처는 데이터 흐름으로 추적한다: 변수 대입·루프 변수·튜플 풀기를 거친 경우와 `float()`·`int()`로 감싼 경우도 출처로 본다.
     * **사본의 정의**(오케스트레이터 기본안, O-33 범위): 출처의 칸 값(또는 `DeviceOp` 객체 자체)을 **그대로**(같은 값, 또는 `float()`·`int()` 형 변환만) **영속되는 자리**에 담는 것이다.
       * 영속 자리 = (i) graph 필드 쓰기(블록 출력 dict의 값, `snapshot.write` 입력), (ii) S3 기록, (iii) 결과 JSON·보고 객체, (iv) **호출보다 오래 사는 객체의 속성**(모듈 전역, 실행 컨텍스트·캐시 객체의 속성).
       * 사본이 아닌 것: 호출 안에서만 쓰이고 버려지는 계산용 임시 묶음(예: `NoiseDevice`, `GateArea`, `SatDevice`)은 계산 입력이다. 칸으로 계산한 산술 결과는 새 값이다(그 값을 다른 곳에서도 재계산하면 L-5의 다른 개념이나 다른 규칙의 대상이다). 예: `SsDevice`는 graph 필드 `ss_dev`의 값이라 영속 자리에 있지만, 칸(`gm`·`gds`·`cgg` 등)이 `op`에서 계산한 산술 결과라 사본이 아니다(`E/metrics/ss_linearize.py:70-75`).
       * 값 형식 집합은 쓰지 않는다: 영속 여부로 판정하므로 '엔진 값 형식(frozen dataclass)이면 위반'이라는 v0.11 첫 정의를 대신한다.
     * **추적 범위**: 출처에서 영속 자리까지 호출 그래프를 따라 추적한다. 전파 경로는 (a) 함수 인자(함수 경계를 넘는다), (b) **반환값**, (c) **객체 칸(필드 단위)** 이다. 반환으로 나간 임시 묶음은 받은 쪽에서 계속 추적한다(escape 판정): 받은 쪽이 그 묶음이나 출처 칸을 영속 자리에 담으면 사본이다. 출처 값이 산술로 끊기면 그 값의 추적은 끝난다. 대상 코드는 규칙 L-1과 같은 도달 조건(엔진 진입점에서 호출 그래프로 도달)을 만족하는 것만이다. 예: LI-1 경로 `layout_input_of`(`E/convergence/layout_input.py:61-72`, `LayoutDevice`에 `op` 칸을 담아 반환) → `E/convergence/place_layout.py:38-39`(`run_layout`에 넘김) → `E/layout/run.py:98`(`snapshot.write`로 graph 필드 쓰기)이 반환·객체 칸 전파로 잡힌다.
     * **fail-closed**: 출처에서 나온 값이 영속 자리에 닿는지를 정적으로 풀지 못하면 위반이다.
     * **정본 쓰기**: `device.dc_op`를 쓰는 블록 자신의 생성은 출처가 graph 읽기가 아니므로 대상이 아니다.
     * **출력 함수 면제**: 영속 자리가 (iii) 결과 JSON·보고 객체이고 그 함수가 N3.1-2의 출력 함수 판정 기준(엔진 reader 0, 결과 JSON·보고 경로에만 도달)을 만족하면 면제한다. 판정 기준은 N3.1-2와 같고, 면제 목록은 GD-1 출력 함수 목록이다(검증자 독립 재측정 대상).
     * **미리 알려진 자리와 card id**: `E/convergence/layout_input.py:72`(`LayoutDevice(... op.W, op.L, op.current, op.gm_id, op.vds, op.vsb ...)`)와 card B의 `ly_point` = **LI-1**(O-27). 이 둘이 이 정의의 부채 항목이다.
     * **이 정의로 분류한 다른 자리**(base `b2c72a01`, 코드 직접 확인):
       * `E/metrics/metrics_aux.py:125` `SatDevice(..., op.vgs, sat, sat_tol, ...)`: `_swing`(`E/metrics/metrics_aux.py:256-262`)이 만들어 `ls_swing`에 넘기고, `ls_swing`이 돌려주는 `SwingIcmr`(`E/metrics/ls_swing.py:119`)에는 `op` 칸이 없다. 그래서 **계산 입력이라 사본이 아니다**(부채 항목 아님 -- v0.11 첫 분류 'DE-1 항목'을 철회). `SatDevice.vgs_v` 칸은 gain-budget card DE-1이 지우는 코드(`ls_swing._constraints`, 유일한 소비자 `ls_swing.py:47`)에만 쓰이므로 그 칸 삭제는 DE-1 범위로 올린다(N3.10 상위 개정 항목).
       * `E/sizing/size_and_seal_local.py:128` `SnapshotFragment(tuple((m, ops[m]) ...))`: `DeviceOp` 객체를 결과 묶음 `LocalSeal.snapshot_fragment`에 담는다. 이 함수는 `dc_op` writer가 아니다. `_module_map`에 'entry'로 올라 있지만 엔진 안 호출자가 0이다(F-G27). 지정 소비자는 층 0 블록 국소 후보(상위 DEC-71 (5))다. 그래서 L-5로는 **도달 조건으로 대상 밖**이고, 이 함수 자체는 '만들고 안 쓰는' 상태라 **'배선 대기' 부채 항목**으로 둔다(N3.2 표, card id = gain-budget v6.19 card **LA-1**, 사용자 결정 O-36 (1)). 그 card가 배선할 때 `snapshot_fragment`가 `DeviceOp` 사본 대신 `dc_op` 참조를 담게 바꾸는 것은 상위 개정 항목이다(N3.10).
       * `E/metrics/dc_metrics.py:113` `GateArea(o.W, o.L, label=m)`: 소비자는 같은 호출 안의 `area_search`(`E/metrics/area.py:12-30`) 하나이고, 거기서 Σ W·L로 `AreaSearch`(새 값)를 만든 뒤 `GateArea` 묶음은 버려진다. **계산 입력이라 사본이 아니다**.
       * `E/search/front_query.py:26-31` `NodeRow(... getattr(op, f) ...)`: 사용자 S3 조회 `node_across_front`(`_module_map` 'entry', 엔진 안 호출자 0)가 돌려주는 보고 객체다. N3.1-2 출력 함수 기준(엔진 reader 0, 보고 경로에만)을 만족하므로 **출력 함수 면제**다. GD-1 목록에 이 함수를 진입점·출력 함수로 넣고 검증자가 확인한다.
     * **기준선 절차**: GC-1 기준선 측정(검증자 독립 스크립트)은 이 정의로 모든 자리를 다시 재고, 위에서 분류한 자리(LI-1 항목, 도달 밖, 계산 입력, 출력 함수 면제)와 대조한다. 분류에 없는 자리가 나오면 card id를 배정하기 전에 GC-1을 멈추고 보고한다(부채 목록에 card id 없는 항목을 두지 않는다, N3.1-6 (f)). `ly_point`는 card B 병합 뒤 같은 절차로 재측정한다.
   * 판정: writer 파일 밖에서 패턴이 나오면 위반이다. 등록 개념의 writer 파일이 없으면 위반이다.
   * **기준선 완전성(거부 증거)**: GC-1은 F-G13의 7자리 전부가 규칙 L-5 위반으로 잡혀 기준선에 들어감을 자리별로 보인다. 특히 속성 꼴(`E/graph/cells.py:53, :117`의 `m.g == m.d`)과 변수 경유 꼴(`E/sizing/writer_plan.py:186`, 트리 변 tuple에서 풀어 낸 변수로 키를 만듦)을 패턴이 잡는지 그 자리 그대로 보인다. 잡지 못하는 자리가 있으면 패턴을 그 꼴까지 넓히고, 넓힐 수 없으면 GC-1을 멈추고 보고한다(자리를 조용히 빼지 않는다).
   * **검증 독립성과의 관계**: 봉인이 결과를 재는 계산(잔차·정합)은 술어 재계산이 아니다. 봉인은 정본 필드를 읽고 다른 경로로 잰다. 그래서 봉인 코드에 면제를 주지 않는다. 봉인이 정본 술어 자체를 다시 만들면 위반이다.
   * 한계(알고리즘): 등록한 개념만 잡고, 패턴과 AST 꼴이 같은 것만 잡는다. 같은 비교를 자료 흐름으로 더 멀리 나눈 꼴(비교를 helper 함수 안에 숨김, 여러 문장에 걸친 변수 전달)은 잡지 못할 수 있다. 나머지는 리뷰와 gap 분석 몫이다(N3.11 A-3, N6.3 확인에 포함).
6. **부채 목록(항목 집합이 줄어들기만 하는 목록)**
   * 형식: 항목 키는 (규칙 id, 최소 단위 대상)이다(N0.1). 묶음 키(예: 파일 하나에 여러 자리)는 쓰지 않는다. 항목마다 (처리 종류, card id, 사유)를 갖는다. 처리 종류는 '배선 대기', '정본 읽기로 교체', '출력 전용 선언 대기', '삭제 승인 대기', '공동분석 대기', '정적 해석 형태로 바꾸기' 중 하나다.
   * 판정:
     * (a) 현재 위반은 모두 목록에 있어야 한다.
     * (b) 목록 항목은 모두 지금도 위반이어야 한다. 이미 고쳐진 항목이 남아 있으면 실패다(규칙 I `test_rule_i_exemptions_are_used`와 같은 방식).
     * (c) **목록의 항목 키 집합 ⊆ 기준선 항목 키 집합**. 기준선 집합은 GC-1에서 검증자가 잰 결과이고(N6 M-G3 재측정), test 코드에 상수로 박는다. **검증자는 기준선을 규칙 L 코드로 재지 않고, 규칙 L 코드와 따로 쓴 독립 측정 스크립트로 잰다**(작성자≠검증자, NFR-G7). 규칙 L 코드가 내는 위반 집합과 독립 스크립트의 집합이 다르면 그 차이를 GC-1 판정 기록에 적고 멈춘다. 개수 비교가 아니므로 항목 하나를 지우고 다른 항목을 더하는 것도 실패다.
     * (d) **기준선 지문의 대상**: 검증자가 GC-1 판정 기록(`.ai/verification/<id>.json`)에 지문 하나를 적는다. 대상은 기준선 집합만이 아니라 **판정을 바꿀 수 있는 모든 것**이다: 규칙 L test 코드 자체(규칙 L 전용 파일만이다. 규칙 L 코드는 기존 `structure_checks.py`와 다른 별도 파일에 두고, 지문은 그 파일에만 묶는다 -- LT-1 등이 같은 `structure_checks.py`를 고칠 때 규칙 L과 무관한 수정이 기준 변경으로 잡히지 않게. GD-9), 엔진 진입점 목록(GD-1), 출력 모듈 범위, 동적 접근 허용 파일 목록, 규칙 L-5 등록표, 규칙 L-4 출력 전용·지문 전용 칸 목록, 규칙 L-2 출력 전용 필드 목록. 이후 card마다 검증자가 다시 재어 기록과 같은지 본다. 다르면 그 차이는 기준 변경이고, 넓히는 쪽(대상 축소·허용 확대)은 기준 약화(상위 N0.4)라 `criteria_weakened` 보고와 사용자 승인이 필요하다.
     * (e) **항목 제거 조건**: 항목은 그 대상 코드(필드 reader, READS 열, 칸, 술어 자리)가 실제로 바뀌어 위반이 사라졌을 때만 지운다. 검증자가 card 판정에서 그 대상 코드 diff를 확인한다. 규칙 매개변수(위 (d)의 목록)를 바꿔 위반을 없애는 것은 제거가 아니라 기준 변경이다.
     * (f) card id는 이 계획 또는 상위·관련 계획의 card 표에 있는 id여야 한다(결정·백로그 id 금지, N0). 문서 대조는 검증자가 GC-V와 각 card 판정에서 한다(test가 계획 문서를 파싱하지 않는다).
   * 새 필드·새 블록에는 목록 항목을 줄 수 없다. 새 것은 처음부터 규칙 L을 통과해야 한다(만들면 배선).

### N3.2 필드별 처리 원칙과 처리 표

**원칙**(O-10 (2) 그대로, 적용 순서):
1. 문서·계획이 소비자를 지정했고 그 소비자가 있으면 배선한다.
2. 지정 소비자가 아직 없으면(다른 card가 만든다) 부채 목록 '배선 대기'로 두고 card id를 붙인다. 이 미룸은 사용자 승인 대상이다(U-G6).
3. 정본 우회 재계산(R1·R2)은 정본 읽기로 바꾼다.
4. 나머지는 출력 전용 선언(출력 함수가 진입점에서 도달해야 함) 또는 삭제다. 삭제는 사용자 승인이다(U-G3). 상위 문서가 검증 소비자로 지정한 것은 그 지정을 정본으로 옮기는 상위 개정이 먼저다(N3.10).
5. 정의역이 다른 같은 식(R3)은 공동분석이다(U-G4).

**처리 표**(기본안. 대상은 F-G2의 26개, F-G3의 문제 4개와 동적 접근 2개, F-G13의 재계산 자리, F-G26의 사본, F-G30의 동적 접근):

| 대상 | 지정 소비자·사유 | 처리(기본안) | card | 읽는 결정 |
|---|---|---|---|---|
| `graph/stage_b: residual_probe`·`dof_numeric` | design 40 §2.4.8 531-532행: 블록 배선은 소비자(층 0)와 함께 U17 ② | 배선 대기 | U17 ② | U-G6 |
| `graph/layout: ly_rows`(L-2) | design 40 §2.4.8: U16 결과 JSON이 `layout_outputs`를 설계점마다 부르게 배선(42 D-LY5) | 배선 대기 | U16 | U-G6 |
| `graph/coupling: vars·column_block_map·bias_columns`(L-2) | `E/pipeline/stage_a.py:12-15`: 소비자는 층 0 조립(41 §5.5) | 배선 대기(지금은 출력 전용으로도 선언하지 않는다 -- 엔진 소비자가 지정돼 있다) | 상위 N6.1 단위 8 | U-G6 |
| `graph/s1v: applied_facts`·`declared` | 단계 A 구조 보고(`structure_tables`), 동적 루프로만 읽힘(F-G3) | `structure_tables.py:33`을 정적 형태로 바꾸고 출력 전용 선언 | GC-7 | -- |
| `device: dc_off_current` | 봉인 9 docstring: 오라클 `off_current_A` 입력. 사용자 결정 O-46 (2)로 oracle 합격 판정의 I_off는 SPICE op 점의 VDS·VSB에서 읽은 엔진 LUT 값이 되어 `off_current_A` 스칼라를 쓰지 않는다 -- 그래서 이 필드의 소비자는 **gain-budget card EO-1(엔진 점 → oracle 입력 생산자) 병합부터 oracle OP-5 병합 전까지만**(옛 ε = 1 '꺼짐' 판정 기간) 있고, OP-5 병합 뒤 0이 된다 | EO-1~OP-5 사이는 배선(EO-1이 oracle 입력으로 낸다). **OP-5 병합 때 출력 전용 선언**(X-G6 (가)의 `dc_conduction_floor`와 같은 처리, 오케스트레이터 기본안 -- 삭제는 사용자 승인 필요라 택하지 않는다) | EO-1(배선), OP-5 병합 card(출력 전용 선언) | U-G6·O-46 (2) |
| `device: dc_conduction_floor` | 봉인 9 docstring: 'search가 θ 전류 상자·제약을 조일 때 읽는 하한'. 실제 search는 LUT 격자에서 따로 계산(F-G14) | 출력 전용 선언(U-G4 (가)). 격자판 전도 술어는 LUT memo 파생 `conduction_mask` 하나로 합친다(O-15 (A)) | GC-7 | U-G4·O-15 (A) |
| `device: start.point`·`start.row`, `graph/start: area_est_m2·area_fraction·conflicts·inactive·macro·records·uncovered` | `E/search/start_intervals.py:5` '출발값과 보고에만'. 보고서가 읽지 않는다 | 출력 전용 선언 대기. 출력 함수 = U16 결과 JSON 진단 칸 | U16 | U-G6 |
| `graph/dc: dc_scc_log`·`dc_tie_breaks` | SCC 풀이 진단, 결정성 기록(상위 NFR-4) | 출력 전용 선언 대기(U16 결과 JSON) | U16 | U-G6 |
| `graph/layout: ly_dispositions` | 소비자 미기재 | 출력 전용 선언 대기(`layout_outputs` 경유) | U16 | U-G6 |
| `graph/s1: column_orphans` | `E/graph/columns.py:15` 'review_needed(정지 아님)' -- 어느 review 목록에도 오르지 않음 | 배선: 단계 A 보고 `review_needed`에 올린다(진입점 도달) | GC-7 | -- |
| `graph/s1: column_pairs` | '0인 쌍도 기록(J13-c)' | 출력 전용 선언(단계 A 구조 보고) | GC-7 | -- |
| `graph/s1: gvgs_summary` | `vds_saturation`은 headroom-chain이 대체. 나머지 칸(개수 4칸·`fixed_vgs`·`port_diff`)은 소비자 미기재. `port_diff`(v1)는 S1 판 계수이고, v1 고리에 남는 ΔV 소거 KVL의 정본은 쓰기 계획의 비트리 MOS 종속(보통 `cycle_vgs`, N0.1 Gs⁺)이다(O-13 (1)) | `vds_saturation`은 HC-1이 지운다. 나머지와 필드 자체는 삭제 승인 대기 | GC-2 | U-G3 |
| `graph/s1: rel_kvl_branch` | 봉인 8만(F-G7). 정의가 엔진 방정식과 다름(N3.3) | 봉인 8 처리(U-G9) 뒤 삭제 승인 대기 | GC-2 | U-G3·U-G9 |
| `graph/s1: rel_kcl_group` | 소비자 0. 같은 사실을 기저가 더 일반적으로 가진다(N3.4). DEC-17 tail도 읽지 않는다(F-G25) | 삭제 승인 대기(card 0 M-G2에서 기저 행과 일치 확인 뒤) | GC-3 | U-G3 |
| `graph/s1: rel_vds_eq_vgs` | 소비자 0. `device.is_diode` 사본(F-G26) | 삭제 승인 대기 | GC-7 | U-G3 |
| `graph/s1: rel_matching_ratio` | 엔진 소비자 0. `gs_groups` 사본(F-G26). **상위 V9가 검증 소비자로 지정**(F-G34) | V9 멤버 출처를 `gs_groups`(gate 비레일 묶음)로 옮기는 상위 개정(N3.10) 뒤 삭제 승인 대기 | GC-7 | U-G3 |
| `graph/s1: rel_l_class` | 유일 reader `E/graph/l_classes.py`. `gs_groups` 비레일 gate 묶음의 사본(F-G26) | `l_classes`가 `gs_groups`를 읽게 바꾸고 삭제 승인 대기. `l_classes.py`는 rule_hash 대상이다(U-G11) | GC-7 | U-G3·U-G11 |
| `graph/s1: rel_matching_offset` | 엔진 소비자 0. 차동쌍 후보 소비는 `matching_groups`가 한다. **상위 V9가 검증 소비자로 지정**(F-G34) | V9 멤버 출처를 `matching_groups`로 옮기는 상위 개정(N3.10) 뒤 삭제 승인 대기. `matching_groups.py`는 rule_hash 대상이다(U-G11) | GC-7 | U-G3·U-G11 |
| `graph/s1: rel_equal_vgs`(필드 자체는 A) | 유일 reader `coupling_vars`. `gs_groups` 1:1 사본(F-G26) | `coupling_vars`가 `gs_groups`를 읽게 바꾸고 삭제 승인 대기. 같은 묶음이 정의로 같으므로 측정은 필요 없다 | GC-7 | U-G3 |
| `device: value`·`value_key` | 소비자 0. 수동소자 값 정본은 spec `element_values`(`E/sizing/dc_inputs.py:7, :36`)다(R9, 값 출처 이원화) | 삭제 승인 대기 | GC-7 | U-G3 |
| `node: dc_branch_node` | 소비자 미기재 | 삭제 승인 대기 | GC-7 | U-G3 |
| 블랭킷 READS(F-G15, L-3) | -- | `build_s1v`·`coupling_vars` READS를 실제 읽는 열로 줄인다. `s1v_fields.py`는 rule_hash 대상이다(U-G11) | GC-7 | U-G11 |
| 동적 필드 접근(F-G30, L-1) | -- | 정적 해석 형태로 바꾼다(상수 필드 인자, 모듈 수준 tuple 루프). 허용 파일 목록은 늘리지 않는다 | GC-7 | -- |
| R1·R1′·R2(F-G13 metrics 3자리) | 정본 `is_diode`·`gs_groups` | 정본 읽기로 교체 | GC-6 | -- |
| R1″(F-G13 graph 층 안 4자리) | 같은 층 재유도 | 정본 읽기로 교체(기본안 BD-7. 면제 없음 -- P-1·FR-9). 투영 경로는 design(GD-5). 세 파일 모두 rule_hash 대상이다(U-G11) | GC-6 | U-G11 |
| 쓰기 계획의 (kind, gate, source) 재유도(F-G13) | 정본 `gs_groups` | 정본 읽기로 교체 | GC-2 | -- |
| R4(`E/metrics/headroom_bound.py`, `E/metrics/ls_swing.py`의 포화 부등식 그래프) | headroom-chain S0 제약 그래프와 같은 개념, 변 규칙이 다름. O-15 (C)가 지목한 위쪽 방향 차분 제약 그래프는 네 곳(`headroom_bound`·`ls_swing`·`iv_headroom`·`order_terms`)이었으나, `ls_swing`의 것은 O-26 (1)로 gain-budget card DE-1이 지운다. 남는 세 곳(`headroom_bound`·`iv_headroom`·`order_terms`)이 R-1′ 제약 그래프 변 목록을 정본으로 읽는다(정본·개념 정의는 headroom-chain v0.7.6 `aa6e064c` N3.4) | 정본 읽기로 교체 + 정책 통일 + 사본 삭제. `headroom_bound`·`order_terms`는 GC-8, `iv_headroom`은 HC-1. `ls_swing` 자체 제약계는 지운다(O-26 (1), gain-budget v6.19 card DE-1 -- 이 계획 범위 밖) | GC-8 | O-15 (C)·O-16 (3) |
| layout 동작점 사본(사용자 결정 O-27): `LayoutInput` 동작점(`E/convergence/layout_input.py:72` `LayoutDevice(... op.W, op.L, op.current, op.gm_id, op.vds, op.vsb ...)`)과 card B(XRUN-F1)가 만드는 `ly_point`(O-24, base `b2c72a01`에는 아직 없음) | 정본 `device.dc_op`(`E/sizing/s2_values.py:381-396`)의 두 단계 사본. O-27: card B는 이 상태로 병합하고 사본은 후속 card가 지운다(원래 취지와 다름 -- 후속 card 완료까지 사본 잔존, 부채 목록으로 증가 금지) | **GC-1 부채 목록에 등록**. 규칙: 규칙 L-5 등록표에 개념 '동작점 사본'(정본 `device.dc_op`, 정의 = 칸 값을 그대로 영속 자리에 담기, N3.1-5)을 더하고, 자리마다 항목 키 (L-5, 파일·줄 자리)로 둔다(오케스트레이터 기본안 -- 사본을 잡는 규칙이 없으면 항목이 '지금도 위반' 판정(N3.1-6 (b))을 받을 수 없다). `ly_point` 자리는 card B 병합 뒤 기준선에 넣는다 | gain-budget v6.19 card **LI-1**(N6.12, layout 입력 정본화, 브랜치 `plan/gb-v619` `6ab294c9`, 승인 전 -- card id는 그 계획 병합 뒤 유효) | O-27 |
| `size_and_seal_local`(`E/sizing/size_and_seal_local.py`, `_module_map` 'entry', 엔진 안 호출자 0 -- F-G27) | 지정 소비자 = 층 0 블록 국소 후보(상위 DEC-71 (5)). 지금은 '만들고 안 쓰는' 상태다 | **'배선 대기' 부채 항목**(사용자 결정 O-36 (1) 승인, 기한 = LA-1 병합). 원래 취지와 다름: 배선 대기 기간 동안 미배선 함수가 남는다(X-G13, 승인됨). 이 상태는 **규칙 L-1 확장 '호출자 0 내부 함수'**(진입점 목록 GD-1에 없고 엔진 안 호출자가 0인 함수 = 위반, O-36 (2), GD-14)가 잡는다. 항목 키는 (L-1 확장, 함수)이고, 그 규칙으로 부채 목록 판정 (b)('지금도 위반')가 성립한다 | gain-budget v6.19 card LA-1 | O-33 (1)·O-36 |
| R6(convergence의 layout 파생 판정 3자리) | `layout_outputs` 미배선 때문에 생긴 사본 | U16이 `layout_outputs`를 배선할 때 같은 변경에서 교체 | U16 | -- |
| 하위 칸(L-4) | -- | GC-0a M-G3c 계수 뒤, 보고 덤프 칸은 출력 전용 칸 목록, 출처 지문 칸은 지문 전용 칸 목록, 나머지는 삭제 승인 대기(항목별) | GC-7 | U-G3 |

### N3.3 KVL 관계 단일 정본

1. **정의 차이**(F-G5·F-G6·F-G19):

   | 항목 | 쓰기 계획(엔진이 푸는 것, K-3 뒤) | as-built 쓰기 계획과 다른 점 | S1 `s1_gvgs` |
   |---|---|---|---|
   | 고정 노드 F | 레일 ∪ 노드 목표(W3) ∪ 선언 입력 포트 | 같음 | 레일만 |
   | 변 | MOS (gate, source), 저항 | as-built는 미선언 입력 포트 '같은 DC' 변을 더 넣는다 | MOS (gate, source)만 |
   | 평행 변 | 소자마다 변, `parallel_vgs`로 분류 | 같음 | 이름순 첫 소자 하나 |
   | 미선언 입력 포트 | 입력 포트를 포함하는 성분은 성분마다 뿌리·오프셋 하나(뿌리 = 성분 안 포트 중 (구조 색, 이름) 최소), 나머지 포트는 MOS writer가 쓰는 넷, 대칭 포트 y는 `domain.ties`(design 41 §6.7-1a, headroom-chain v0.7.1 N0.1). 같은 DC 등식은 없고, 포트 경로가 둘 이상이면 ΔV를 소거한 KVL 하나가 비트리 MOS 종속(보통 `cycle_vgs`, 경우에 따라 `parallel_vgs`·`fixed_vgs`, `E/sizing/writer_plan.py:191-196`)으로 남는다(대칭이면 묶음과 중복, O-13 (1)) | as-built는 포트를 '같은 DC' 변으로 이어 포트 차 고리를 등식으로 닫고, 성분 y 키를 공동 키로 둔다 | 포트 단계별 숲, v1(포트 차)은 제약 없음 |
   | 종속 선택 | DEC-95 (3) 키 Kruskal | 같음 | 이름순 숲 |
   | VDS 변 | 없음(등식만). VDS 변 부등식은 HC-1 제약 그래프 | 같음 | `vds_saturation`(VDS-1) |
   | 층 | S0(노드 목표·입력 DC 선언은 spec 값) | 같음 | S1 |
2. **정본(기본안 BD-1)**: KVL 관계의 정본은 **쓰기 계획 블록이 쓰는 S0 graph 필드**, 즉 `node.dc_writer`(숲)와 `device.dc_coord`(종속 분류)다. 별도 '종속 사이클' 블록·필드는 만들지 않는다. 사이클 멤버가 필요한 소비자는 쓰기 계획 블록이 함께 쓰는 넷별 뿌리 경로 필드(3)를 읽는다.
   * 근거 1(P-1, 가장 일반적인 형태): KVL 등식 사이클에 들어가는 원소는 MOS VGS만이 아니다. 저항 강하·노드 목표·입력 DC 선언이 들어가고, 쓰기 계획은 그것을 모두 담는다. S1 판은 그 부분집합이라 엔진 방정식이 아니다.
   * 근거 2(층 의존성): F에 노드 목표와 입력 DC 선언이 들어가므로 사이클 집합은 spec에 의존한다. 그래서 S1 필드로는 엔진 방정식을 담을 수 없다.
   * 근거 3(DEC-83, design 41 §6.7-1): 쓰기 계획 출력도 graph 필드다. design 41 §6.7-1은 이미 '새 탐지기를 만들지 않는다 -- 쓰기 계획을 읽는다'로 정했다.
   * **tie 변 제외의 근거**(P-1, B2·K-3): 입력 DC가 선언되지 않으면 두 입력 포트의 DC가 같다는 물리 제약은 없다. 같은 값은 회로가 대칭일 때만 성립하므로 대칭 묶음(`domain.ties`)이 그 경우만 담는다. 등식 변으로 넣으면 비대칭 회로에서도 없는 제약을 커널이 푼다. tie 변을 빼도 포트 사이 MOS 경로가 둘 이상이면 ΔV를 소거한 KVL 하나는 물리적으로 남는다. 이것은 Gs⁺의 비트리 MOS 변이 닫는 등식 사이클(비트리 MOS 종속, 보통 `cycle_vgs`)이고, 회로가 대칭이면 묶음과 중복이다(O-13 (1)).
   * 다른 안: (나) 관계 블록(숲과 사이클)을 따로 두고 쓰기 계획이 그것을 읽는다. 종속 선택이 숲 선택과 같아서 두 블록 사이에 같은 결정이 걸린다. 모듈 분리가 필요하면 design에서 파일 분할로만 다룬다(GD-2). 사용자 선택은 U-G1이다.
3. **트리 경로(사용자 결정 O-14 (1) (가′), BD-10, NFR-G3)**:
   * **필드**: 쓰기 계획 블록이 넷별 뿌리 경로(넷에서 자기 뿌리 -- F 또는 W4 창 뿌리 -- 까지의 변 열과 부호, θ 무관)를 **자기 출력 S0 필드로 한 번 쓴다**. 이 필드의 writer는 쓰기 계획 블록 하나다. 경로는 블록이 숲을 만들 때 이미 가진 부모 포인터(`NodeWrite.known`, F-G33)를 따라 그 블록 안에서 만든다. 두 넷 사이 기본 사이클 멤버는 두 넷의 뿌리 경로에서 얻는다. 필드 이름·값 형식은 GD-2가 정한다.
   * **'저장하면 사본' 논리 철회**: v0.3~v0.8은 경로를 필드로 저장하면 `node.dc_writer`의 사본이라 FR-9·DEC-83과 충돌한다고 적었다. 그러나 이 필드는 `node.dc_writer`를 쓰는 **같은 블록의 자기 출력**이고 writer가 하나다. 그래서 사본이 아니고 DEC-83 '필드마다 writer 하나'를 충족한다. 오히려 소비자 셋이 각자 포인터를 따라 경로를 다시 만드는 쪽이 같은 계산의 반복이다(상위 NFR-2·WP-10). O-14 (1)은 O-13 (4) U-G1 (가)의 '경로 저장 안 함' 부분만 개정한다. U-G1 뼈대(KVL 정본 = 쓰기 계획 출력, 별도 사이클 블록 없음)는 그대로다.
   * **소비자(셋, 규칙 L-1 대상)**: 이 계획(GC-0b M-G1 대조, GC-2), headroom-chain HC-1 제약 그래프(κ_n), design 41 §6.7(의존 묶음, U17 ②). 새 필드는 규칙 L-1 대상이다: 만드는 card가 병합될 때 진입점에서 도달하는 실제 읽기가 1곳 이상 있어야 한다(만들면 배선). 소비자는 필드를 읽고 경로를 다시 만들지 않는다.
   * **Gs⁺ VGS 변 필드**(headroom-chain v0.7.5 완료 조건 12): 같은 쓰기 계획 블록이 Gs⁺의 VGS 변(변 목록·방향)도 자기 출력 S0 필드로 쓴다. 소비자는 HC-1(`iv_headroom` VGS 절반)과 GC-8(`headroom_bound._edges` VGS 절반)이다. 두 필드(넷별 뿌리 경로, Gs⁺ VGS 변)는 writer가 쓰기 계획 블록 하나이고, 만드는 card 규칙도 아래와 같다.
   * **만드는 card와 K-3/IT-1과의 관계**: IT-1(K-3 구현, 상위 card, 계획 정의는 master `f2852c36`에 병합됨, 구현은 아직)이 쓰기 계획의 숲(같은 DC 변 제거)을 바꾸므로 경로 필드의 내용도 IT-1 전후로 바뀐다. 그래서 필드는 **IT-1 병합 뒤의 card에서 추가한다**. 그 card는 IT-1 뒤에 쓰기 계획 블록을 처음 고치는 소비자 card다. 지금 순서(GC-2는 HC-1 뒤, BD-6)에서는 **HC-1**이고, HC-1이 이 필드들(뿌리 경로 필드와 Gs⁺ VGS 변 필드 둘 다) 없이 병합되면 **GC-2가 첫 단계로 만든다**(기본안). 먼저 병합되는 card가 만들고 뒤 card는 읽는다. 오케스트레이터는 HC-D design 브리핑에 이것을 넣는다.
   * GC-0b M-G1은 엔진 무변경 측정이다. 그때 필드가 아직 없으면 측정 스크립트가 `NodeWrite.known` 포인터를 따라가고 그 사실을 기록한다(측정 도구일 뿐 엔진 소비자가 아니다).
   * headroom-chain v0.7.1은 제약 그래프가 '경로 목록은 저장하지 않는다'고 적는다(N3.1 317행 표). O-14 (1)로 이 문언은 그 계획에서 개정 대상이다(headroom-chain 계획 소관, 이 계획은 고치지 않는다).
4. **봉인 8**(U-G9):
   * 사실: 상위 472행이 봉인 8에 맡긴 일('W2 블록이 등식을 풀지 않은 경로를 잡는 게이트')은 봉인 2가 θ마다 소자별로 이미 한다. 봉인 8의 행 값은 봉인 2가 모든 MOS에 대해 재는 같은 양의 사이클 합이다(F-G31). 그래서 봉인 8은 봉인 2에 함의되고(K-c), 봉인 8만 잡는 결함은 없다.
   * 숲 회계 불변량(N3.5-3)은 봉인 8을 대체하지 않는다. 그것은 union-find 회계(`dc_coord` 누락, 트리·비트리 오분류) 같은 쓰기 계획 구현 오류를 잡는 별개의 보조 검사다.
   * 선택지: (가) 봉인 8 삭제(역할은 봉인 2가 이미 함) (나) 봉인 8 유지, 목록만 `rel_kvl_branch`에서 쓰기 계획 종속 분류로 교체(v0.1안). 기본안은 (가)다. 근거: θ마다 같은 양을 한 번 더 더하는 계산이라 정보가 없다(상위 NFR-2). (나)는 사이클 멤버를 θ마다 펼치는 비용이 더해진다. 상위 472행 개정이 따른다(X-G10).
5. **같은 VGS**: 쓰기 계획의 `parallel_vgs` 판정은 `graph.gs_groups`에서 같은 묶음의 트리 소자를 찾는다. (kind, gate, source) 키를 다시 만들지 않는다(F-G13, 규칙 L-5). `gs_groups`의 묶음 키도 (kind, gate, source)라 판정은 정의로 같다. 분류 순서(`fixed_vgs`를 먼저 판정)는 그대로 둔다. GC-2는 순수 리팩터링 card라 종속 분류(이산 값)는 base와 정확히 같아야 한다(N4-0, 완료 조건 3).
6. **`gvgs_self_edge` 정지 이전**(FR-G16):
   * `gvgs_cycles.py`를 지우면 유일한 `gvgs_self_edge` 정지가 사라진다(F-G20). 쓰기 계획은 같은 소자를 멈추지 않고 종속으로 분류하므로, 정지 없이 지우면 지원하지 않는 구조가 조용히 계산된다.
   * 그래서 GC-2의 첫 단계는 정지를 옮기는 것이다. 판정식(MOS gate·source가 같은 비레일 넷), 레일 g = s의 `fixed_vgs` 허용, 사유 코드(`unsupported_rule_branch`, rule_branch `gvgs_self_edge`)는 그대로 둔다.
   * 위치(기본안 BD-11): S1 쪽 블록. 근거: base와 **같은 층·같은 시점**에 멈춘다. 쓰기 계획으로 옮기면 노드 목표 넷에서 판정이 달라진다(쓰기 계획에서는 목표 넷이 F라 `fixed_vgs`가 된다). 구체 블록은 design이 정한다(GD-10). 옮길 블록 파일이 `S1V_RULE_FILES`·`STRUCTURE_RULE_EXTRA_FILES`에 들면 GC-2도 U-G11(rule_hash) 대상이다.
   * **물리 근거 없음(P-1, 보존만)**: 레일 g = s(`fixed_vgs`, 허용)와 비레일 g = s(정지)는 물리적으로 같은 상황(VGS가 구조로 0인 소자)이다. 이 비대칭에는 물리 근거가 없고, 비레일 쪽 정지는 '그 구조를 다루는 규칙이 없다'는 지원 범위 표시다. 이 계획은 base 동작 보존만 하고 일반화(같은 처리로 통일)는 정하지 않는다(백로그 B-G3).
   * 순서: 옮긴 정지가 거부 픽스처를 실제로 거부함을 먼저 보인 뒤 `gvgs_cycles.py`를 지운다(같은 card 안).
7. **삭제**(U-G3 승인 뒤): S1 `rel_kvl_branch`, `gvgs_summary`(HC-1이 `vds_saturation`을 지운 뒤 나머지), 그리고 그 둘만 쓰는 `E/graph/gvgs_cycles.py` 모듈 전체. 같은 변경에서 그 등록도 지운다: `S1_RULE_FILES`(`E/graph/s1_values.py:222-225`), `_module_map`(`E/_module_map.py:98, :470`), 패키지 공개 이름(`E/graph/__init__.py:29`), S1 조립 import(`E/graph/s1_build.py:35`). J12-c 측정 기대(상위 DEC-64 끝)는 card 0 M-G1의 대조 기록으로 남긴다.
8. **v1 포트 차 루프**(사용자 결정 O-13 (1)): 같은 DC 등식은 없앤다(B2·K-3). 포트 경로가 둘 이상인 v1 고리는 ΔV를 소거한 KVL 하나가 남는다(파일럿 M1b `cycle_vgs`: VGS1a − VGS1b = VGS4a − VGS4b). 이 KVL은 쓰기 계획이 비트리 MOS 변의 종속(보통 `cycle_vgs`, 경우에 따라 `parallel_vgs`·`fixed_vgs`)으로 푸는 등식이라 KVL 정본(BD-1)에 들고, 회로가 대칭이면 대칭 묶음(`domain.ties`)과 중복이다. 이 계획은 K-3 구현 card가 '같은 DC' 변을 없앤 뒤의 쓰기 계획을 정본으로 본다. v0.1의 'as-built 동작을 문언으로 정정'(X-G2·U-G2)은 철회했다(N5).

### N3.4 KCL 관계 단일 정본

1. **정본**: KCL 관계의 정본은 `graph.dc_current_basis` 하나다. 레일이 아닌 모든 넷의 KCL을 풀었으므로 '직렬 가지 = 같은 전류'(`rel_kcl_group`)는 그 특수형이다(P-1, 가장 일반적인 형태).
2. **`rel_kcl_group`**: 소비자가 0이다. card 0 M-G2에서 묶음마다 멤버 전류가 기저 행에서 같은 선형식인지 잰다. 같으면 삭제 승인 대기(U-G3). 다르면 그 사례를 공동분석으로 올린다.
3. **DEC-17 tail 문언**: 실제 tail 판정은 `l_classes.py:7-9`의 정의(F-G25)다. 측정 없이 상위 217행 문언을 그 정의로 맞춘다(N3.10, 사실 정정).
4. **새 전류 사슬 금지**(O-10 (4)): 이 계획은 기저 밖에 전류 관계를 새로 만들지 않는다.

### N3.5 결과 검증

1. **엔진 안 검사의 성격(사실)**:
   * 봉인 8: 봉인 2 양의 합이라 봉인 2에 함의된다(F-G31, K-c). 처리는 U-G9.
   * 봉인 3: 기본 경로에서 W = ID·L/IDu(DEC-88)이므로 MOS 항은 ID·(IDu_forward/IDu_coord) = ID·e^Δ이다(Δ = ln IDu_forward − ln IDu_coord). 넷 잔차의 MOS 몫은 Σ ID·(e^Δ − 1)이고, 1차 근사로 Σ gm·ΔVGS다(Δ = (gm/ID)·ΔVGS). 봉인 2가 멤버마다 |ΔVGS| ≤ tol_V를 보장하면 잔차 상한은 1차 근사로 Σ gm·tol_V(합)이다. 봉인 3의 허용오차는 max(gm·tol_V)라 그보다 작다. 그래서 봉인 2는 봉인 3을 **함의하지 않는다**. 봉인 3은 봉인 2와 상관되지만 더 엄격한 집계다(K-d, X-G4). 이것은 결함이 아니라 DEC-88에서 나오는 성질이다. 봉인 3이 상관 없는 잔차를 내는 경로는 W가 ID에서 오지 않는 곳, 즉 W_request(LY3)와 실현 기하 재평가다. card 0 M-G4에서 그 경로에서 봉인 3이 실제로 도는지 확인하고, 안 돌면 해당 card(MOD8 소유)에 배선 대기로 올린다.
   * 공급 전류 합(`kcl_residual_amp`)과 기저 결선 대조는 항등식이다(F-G21·F-G22). 판정을 더하지 않는다(v0.1 BD-3·BD-4 철회).
2. **독립 검증 경로(기본안 BD-12, U-G10)**:
   * **KCL**: 오라클 forced 모드. 소자 단자 넷을 엔진 예측 전압에 고정하고, 넷별 고정원 전류(= SPICE 소자 모델로 잰 그 넷의 KCL 잔차)를 오라클의 `kcl_abs_A`로 판정한다(F-G23). 계산 경로(LUT·기저)와 다른 모델·다른 풀이다.
   * **KVL**: 오라클 free 모드. SPICE가 푼 노드전압을 엔진 노드전압과 대조한다.
   * **배선**: 엔진 결과 → 오라클 입력(OP-0 입력 스키마)은 U16이 만든다. 이 계획은 그 배선을 만들지 않는다. U16 완료 조건에 '13회로 forced·free 대조 실행'을 더하는 것은 다른 card의 완료 조건 변경이라 S-7에 따라 상위·관련 계획 개정 항목으로 올린다(N3.10).
   * 허용오차는 오라클이 이미 선언한 값(`kcl_abs_A` 등)을 쓴다. 새 상수는 없다.
3. **엔진 보조 검사**(GC-2·GC-3, FR-G17. 독립 검증이 아니다):
   * **쓰기 계획 숲 회계 불변량**: Gs⁺(F를 한 점으로 묶음)의 순환수 \|E\| − \|V\| + 성분 수가 `device.dc_coord`의 종속 소자 수와 같다. 비트리 저항 변은 이미 멈추므로(F-G5) 비트리 변은 모두 MOS다. 순환수는 연결에서 세고, 종속 수는 쓰기 계획 출력에서 센다. 잡는 것은 union-find 회계 오류(`dc_coord` 누락, 트리·비트리 오분류)다. 봉인 8을 대체하지 않는다(N3.3-4). 다르면 사유 코드로 멈춘다. θ 무관이고 실행당 한 번이다(NFR-G4). 위치는 쓰기 계획 블록 밖 S0 검사다(GD-11).
   * **성립 조건**(검증자 유도로 정확, design 항목 GD-11): E = MOS마다 (gate, source) 변 하나(평행·diode·gate = source 자기 고리 포함) + 잎 가지치기된 저항을 포함한 모든 저항 변. V = F를 한 점으로 병합한 뒤 변 끝점 노드. K-3 뒤에는 '같은 DC' 변이 없다. 포트 경로가 둘 이상인 v1 고리에 남는 ΔV 소거 KVL(O-13 (1))은 Gs⁺의 비트리 MOS 변 하나이므로 순환수 \|E\| − \|V\| + 성분 수에 들고 비트리 MOS 종속 하나(보통 `cycle_vgs`, 분류와 무관하게 하나)로 세어진다. 그래서 불변량(종속 수 = 순환수)은 이 고리를 포함해 성립한다. K-3 병합 전 as-built에서 잴 때는 '같은 DC' 변을 E에 넣어야 한다.
   * **`node.terminals` 결선 점검**: 기저 원소의 (넷 a, 넷 b)가 `node.terminals`의 그 넷 항목에 그 원소로 들어 있는지 본다. `node.terminals`도 같은 핀에서 만들어지므로(F-G22) 넷리스트 오류는 잡지 못하고, 기저 조립의 색인·방향 처리 오류만 잡는다. θ 무관, 실행당 한 번이다(GD-4).
   * 두 검사 모두 거부 픽스처로 거부를 먼저 보인다.
4. **MNA**: 이 계획은 바꾸지 않는다. 상대 잔차는 공허하다(F-G28). 해의 정확도를 알려 주는 조건수의 기록은 소비자·판정 기준이 없어 백로그 B-G1로 둔다.
5. **포화 부등식(G3)**: 사후 판정(봉인 7)만 있는 것은 headroom-chain 범위다. 이 계획은 다루지 않는다.

### N3.6 출발 전류(start_intervals)

1. **충돌 표지**(O-10 (4)): θ 자유 원소 전류나 기저 행으로 정해진 MOS 전류가 0 이하이면, 지금처럼 '정해지지 않음'으로 조용히 바꾸지 않는다. 그 상태(`_State`)에 **전류 충돌 표지**를 세우고 출발 충돌(`StartConflict`)로 원소 이름과 값을 남긴다. 이 표지는 매크로 목표 해제(`use_macro`)·면적 예산 유무와 무관하게 꺼지지 않는다(F-G32의 빈틈을 지나가지 않게). 표지는 기존 `macro_failed`와 별개다.
2. **기저 경유**(기본안 BD-5, X-G8):
   * 자리값은 정해지지 않은 **기저 자유 원소**에만 둔다. 자리값 식은 지금 식(정해진 전류 기하평균과 W_min·IDu/L 중 큰 쪽)을 그대로 쓴다. **근거 상태(v0.11)**: W_min·IDu/L은 선언량(PDK 최소 finger 폭)과 LUT에서 닫힌 식으로 나온다. '정해진 전류 기하평균'은 물리 유도나 선언이 없다. 근거는 코드 주석(`E/search/start_intervals.py:120-121`, '눈금이 다른 가지를 섞으면 미러·적층의 DC가 무너진다')의 정성 이유뿐이고, design 41 1260행은 이 식을 BP1 입력의 닫힌 식으로 분류할 뿐 기하평균을 유도하지 않는다. 그래서 이 항은 **'추정'**(출발값 휴리스틱 -- 판정에 쓰지 않는다)으로 표기하고, 유도는 백로그 B-G5로 둔다. 이 계획은 식을 바꾸지 않고(동작 보존) 자리만 기저 자유 원소로 옮긴다.
   * 나머지 원소 전류는 기저 행으로 계산한다. 그 결과가 0 이하이면 충돌 표지를 세운다.
   * 근거(P-1, KCL): 지금은 같은 기저 원소를 공유하는 직렬 소자도 서로 다른 자리값을 가질 수 있다. 그러면 면적 추정과 출발 사다리 선택이 KCL을 어긴 전류로 계산된다.
   * 자유 원소가 MOS일 때 W_min·IDu/L의 IDu·L을 어느 소자 것으로 쓰는지(자유 원소 자신인지, 그 원소 행을 공유하는 소자 중 무엇인지), 자유 원소가 MOS가 아닐 때(저항·이상원)의 자리값은 design이 기존 식에서 정한다(GD-7). 새 상수는 만들지 않는다.
3. **충돌 칸 처리(사다리 칸 단위, U-G13, X-G11)**:
   * **성립 조건(P-1)**: '0 이하 전류 = 물리 동작점이 아님'은 전류 부호가 고정된 기준 방향(선언 d/s 방향)에 대한 것일 때만 성립한다. 결정 6(d/s 맞바꿈, 사이징 결과는 선언 방향, 틀린 선언은 봉인 7 거부 -- 상위 U-62)이 그 방향을 고정한다. 결정 6은 이미 병합됐으므로(`c8d156e3`, F-G36) 이 조건은 지금 성립한다(BD-13 충족).
   * 선택지:
     * (가) 다음 넷으로 이루어진다.
       * **최상 칸 선택**: 충돌 표지가 선 상태는 `feasible`에서 항상 실행 불가다(`use_macro`·예산과 무관).
       * **아래 칸**: 칸마다 충돌 표지를 판정하고, 표지가 선 칸은 사다리에 넣지 않고 칸 번호·원소·값을 충돌로 기록한다. 0 이하 θ 자유 원소에는 자리값을 두지 않는다(그 원소가 든 기저 행의 전류가 정해지지 않으므로 그 상태 전체가 충돌이다).
       * **충돌의 t 의존(사실)**: 기저 행 계수(유리수)는 t와 무관하다. 그러나 원소 값은 매크로 gm(t)의 아핀식이다(`E/search/start_intervals.py:95-96, :114-115`). 그래서 θ 자유 원소 값과, 계수 부호가 섞인 기저 행의 MOS 전류는 t에 따라 부호가 바뀔 수 있다. 충돌 칸 집합은 t에 대해 구간이 아닐 수 있고, 지금의 이분 탐색(392행, 실행 가능성이 t에 단조라고 가정)은 충돌에 대해 성립하지 않는다.
       * **선택점(칸 0) 고르기 -- 아래 끝(t = 0)이 전류 충돌인 경우(최상 칸 무관)**: 지금 코드는 최상 칸이 실행 불가면 아래 끝으로 가고(384행), 아래 끝도 실행 불가면 이분 탐색을 건너뛴다(387행). 그래서 아래 끝이 전류 충돌이면 충돌 없는 t가 있어도 찾지 않는다. 대상은 다음 셋이다. (a) 최상 칸이 충돌 없이 면적·매크로로만 실행 불가인 혼합 경우, (b) 최상 칸과 아래 끝이 모두 충돌이고 중간 t만 충돌 없는 경우, (c) 선택 후보(격자 점과 t = 0)가 모두 전류 충돌인 경우. 최상 칸이 충돌 없고 실행 가능하면 지금처럼 t = 1이 선택점이라 이 항목의 대상이 아니다. **결정(O-13 (4), U-G13): (가-1)**. 결정 때 함께 올린 (가-2)·(가-3)은 선택되지 않았고, 아래에 기록으로만 남긴다:
         * (가-1) **사다리 격자 탐색**(결정됨): 칸 0 후보를 사다리 격자 t_k = 2^-k(k = 0..steps)와 t = 0에서 고른다. 우선순위는 다음과 같다.
           * (i) 충돌 없고 실행 가능한 **최대** t(지금 '실행 가능한 최대 t' 규칙과 같다, docstring 7번).
           * (ii) 없으면 충돌 없는(면적·매크로로만 실행 불가) **최소** t. 지금 코드의 아래 끝 대체는 '가장 느슨한 끝'(gm/ID가 낮을수록 면적·매크로 실행 가능 쪽, `E/search/start_intervals.py:23-26` docstring 7번, 382행 주석)을 고르는 것이므로, 같은 성격은 실행 가능성에 가장 가까운 충돌 없는 최소 t다. 최대 t로 하면 혼합 경우 (a)에서는 정의상 늘 t = 1(실행 가능성에서 가장 먼 점)이 된다.
           * **(ii) 점의 실행 불가 원인 기록과 `use_macro`**: (ii)로 고른 점(충돌 없는 최소 t = t_p)은 면적 초과뿐 아니라 **매크로 실패만으로도** 실행 불가일 수 있다. docstring 7번(`start_intervals.py:24-26`)대로 흔한 경우다. 지금 코드는 매크로 목표 달성 불가를 아래 끝(t = 0) 상태로 판정한다: `bottom.macro_failed`이면 `use_macro`를 끄고 '매크로 목표 달성 불가' 충돌을 기록한다(380-383행). 그런데 (가-1)에서는 아래 끝이 전류 충돌이라 그 상태는 동작점이 아니다(P-1). 그래서 이 판정 자리를 충돌 없는 후보 중 가장 느슨한 점인 (ii) 점으로 옮긴다(같은 성격: '실행 가능 쪽 끝에서도 목표를 못 맞춘다'). 정의는 다음과 같다.
             * (ii) 점이 `macro_failed`이면 `use_macro`를 끄고 '매크로 목표 달성 불가' 충돌을 **t_p와 함께** 기록한다. 그 뒤 충돌 없는 격자 점들의 실행 가능성을 면적만으로 다시 보고 (i)을 다시 적용한다. 격자 점 상태는 다시 풀지 않는다(기존 385행이 `use_macro`를 끈 뒤 `top`을 다시 풀지 않고 `feasible(top)`만 다시 보는 것과 같다). 다시 적용해서도 실행 가능 점이 없으면 (ii) 점을 쓴다.
             * 최종 선택점이 여전히 실행 불가면 **원인마다** 충돌을 기록한다. 면적 초과(또는 면적 예산이 있는데 충돌 없는 상태의 면적 추정이 없음)는 면적 충돌로, 매크로 실패는 위의 매크로 충돌로, 둘 다면 둘 다 기록한다. 각 기록은 그 점의 t를 담는다(형식은 GD-7).
             * 전류 충돌인 아래 끝의 `macro_failed`는 `use_macro` 해제 판정에 쓰지 않는다(동작점이 아닌 상태다).
           * (iii) 없으면 빈 사다리다.
           * 아래 끝이 충돌 없으면 지금 흐름(아래 끝 실행 가능이면 이분 탐색, 아니면 아래 끝 대체)을 그대로 쓴다. 이분 탐색 결과 상태가 충돌이면 `feasible`이 거짓이므로 기존 395행대로 버린다.
           * 근거: 단조 가정이 필요 없다. 분해능은 사다리 칸 폭과 같고, 372행 주석이 t 탐색 분해능으로 그 폭이면 충분하다고 이미 정했다.
           * 재사용(NFR-G4)은 **조건부**다: 격자 점 상태를 사다리 아래 칸 계산(402-405행 `solve(t/2^k, refine=False)`)에 다시 쓸 수 있는 것은 고른 선택점에서 시작한 사다리의 t가 격자 점과 겹치고 정제 설정(`refine`, `use_macro`)이 같을 때뿐이다. 그 밖에는 따로 푼다. 고른 점을 `refine=True`로 다시 풀지는 GD-7이 정한다.
         * (가-2) **충돌 없는 구간 안 이분 탐색**(선택 안 됨, 기록): 격자로 충돌 없는 실행 가능 점을 먼저 찾고, 그 점과 그 위 격자 점 사이에서 기존 이분 탐색을 한다. 분해능은 더 곱다. 그러나 그 사이에서도 충돌이 t에 단조가 아닐 수 있어 결과 상태를 다시 확인해야 하고, 계산이 더 든다.
         * (가-3) **v0.4 정의 그대로**(선택 안 됨, 기록): 아래 끝이 전류 충돌이면 빈 사다리다. 충돌 없는 중간 t를 버린다.
       * **빈 사다리 -- 선택 후보가 모두 전류 충돌일 때**: 선택 후보(격자 점과 t = 0)가 모두 전류 충돌일 때(위 (c))다. **전류 충돌 상태는 칸 0으로 쓰지 않는다**. 사다리는 빈 tuple이고, 칸 0이 정했을 θ 성분(ln_idu·θ 전류·보상 커패시터·L과 L 칸)은 모두 `uncovered`로 남는다. 층 0은 지금 빈 사다리 처리(`E/search/layer0_center.py:656` `sctx.rungs or (None,)`)대로 상자 중심에서 출발한다. `_report`는 빈 사다리를 받아야 한다: `covered`는 칸 0이 있을 때만 그 θ로 만들고 없으면 빈 집합이다(지금 453행의 `rungs[0]`은 빈 사다리에서 IndexError라 그대로 두면 안 된다). 소자 행(`StartRow`)은 마지막으로 푼 상태의 값을 보고하되 충돌 소자의 전류·폭은 None이고, 충돌은 `graph/start: conflicts`에 칸 t와 함께 남는다. 출력 형식은 GD-7이다.
       * **원인과 다른 면적 충돌 기록**: 지금 387-389행은 아래 끝이 실행 불가면 원인과 무관하게 '면적 충돌'(`estimate_at_gm_id_lo` = `bottom.area`)을 기록한다. 전류 충돌 상태는 면적이 None이라 차이가 nan인 면적 충돌이 된다. (가)에서는 그 상태가 전류 충돌이면 면적 충돌을 기록하지 않고 전류 충돌만 남긴다. 면적 충돌은 충돌 없는 상태가 면적 예산을 넘을 때만 기록한다(지금 뜻 그대로). (가-1) (ii)로 t ≠ 0을 고르면 지금 라벨 `estimate_at_gm_id_lo`(t = 0에서의 추정이라는 뜻)와 매크로 충돌 라벨 `macro_target_unattainable_at_gm_id_lo`(383행)는 틀리므로, 두 기록에 고른 t를 담는 형식은 GD-7이 정한다.
       * **면적만 실행 불가인 아래 끝**은 지금처럼 칸 0 후보다(면적 예산 초과는 물리 동작점 위반이 아니다. 동작 보존).
       * **빈 사다리는 실제로 일어난다**: 결정 6 뒤에는 사이징 결과가 선언 방향이므로, d/s를 거꾸로 선언한 소자의 기저 행은 선언 방향 기준으로 부호가 뒤집힌다. 그 행의 항이 모두 양의 θ 원소에 음의 계수인 경우(예: 그 소자가 θ 원소 하나의 가지 전류를 그대로 나르는 경우) 전류는 t와 무관하게 0 이하이고 모든 후보가 충돌한다(그 선언은 봉인 7이 거부하는 틀린 선언이다, 상위 U-62). 계수 부호가 섞인 행은 t에 따라 충돌 여부가 바뀌므로(위 't 의존') 일부 칸만 충돌할 수 있다. 해당 회로·칸 수는 GC-5 착수 측정(N4-4)에서 잰다.
       * **1회차 전류(285-286행)의 0 이하 처리**: 1회차 상태도 같은 충돌 표지를 세운다. 표지가 선 원소·소자의 값은 `currents1`·`first.elements`에 넣지 않고 자리값(`first.refs`)으로도 채우지 않는다. 그 값을 받는 곳은 **네 함수, 여섯 호출 자리**다(`gain_l_bounds` 292행, `matching_bounds` 295·332행, `area_bounds` 296·327행, `noise_bounds` 333행). 지금 처리는 함수마다 다르므로(F-G32) GC-5는 함수마다 다음을 고친다. 사유 코드 이름은 GD-7이 정한다.
         * `gain_l_bounds`: 원소가 전류 충돌로 빠진 블록은 '이득 목표 미달'(`SRC_GAIN_L`) 충돌과 최대 앵커 L 하한을 만들지 않는다(지금 `iv_gain_l.py:125-127`). 그 블록 경계를 전류 충돌 사유로 비활성 기록한다. 이 자리는 `start_intervals.py:117` 때문에 **지금도 원인과 다른 사유로 기록되는 살아 있는 경로**다.
         * `area_bounds`: 충돌 소자의 W_min gm/ID 하한을 기록 없이 건너뛰는 자리(`iv_area.py:68-69`)에서, 면적 예산 유무와 무관하게 전류 충돌 사유 비활성을 기록한다.
         * `matching_bounds`: 절대 정합 목표·offset 가드 중 선언된 것마다 전류 충돌 사유를 `WHY_NO_CURRENT`와 구분해 기록한다. 지금 117-118행 반환은 정합 L 경계(`SRC_MATCH_L`)와 가드 경계를 함께 없애면서 사유는 `(SRC_OFFSET_GUARD, WHY_NO_CURRENT)` 하나만 남긴다. 절대 정합 목표만 있고 가드가 없으면 `SRC_MATCH_L` 경계가 사라진 사유가 기록되지 않는다(`iv_matching_l.py:107-118`). 그래서 `SRC_MATCH_L`의 전류 충돌 사유도 기록한다.
         * `noise_bounds`: 잡음 가드 목표가 선언됐을 때 가드 경계 비활성 사유를 전류 충돌 사유로 구분해 기록한다(`iv_noise.py:77-78`).
         * 1회차 충돌 자체를 `StartConflict`로 남긴다.
         * 그래서 표지의 소비처는 이 여섯 호출 자리의 비활성 사유와 충돌 기록이다. 표지만 세우고 이 경로에서 읽지 않으면 조용한 대체·생략이라 FR-G12·완료 조건 6 위반이다. 정해지지 않은(0 이하가 아닌) 전류의 자리값은 N3.6-2(기저 자유 원소에만)대로 둔다.
     * (나) 자리값을 쓰되 충돌 기록에 '대체값'과 대체된 원소를 명시하고, 면적 추정·사다리 칸에 대체 표지를 단다(선택은 바꾸지 않는다).
     * (다) 출발 단계를 멈춘다.
   * **결정(O-13 (4), U-G13)은 (가)이고, (가) 안의 '아래 끝이 전류 충돌인 경우'는 (가-1)이다.** 결정 때의 근거: 근거: 성립 조건 아래 0 이하 전류는 물리 동작점이 아니고(P-1), 실패 표지가 꺼지지 않으며(fail-closed), 새 값을 만들지 않는다.
   * **모든 후보가 충돌일 때 (다) 정지가 아니라 상자 중심에서 계속 탐색하는 근거**: 출발 단계는 판정 단계가 아니다(`E/search/start_intervals.py:5` '판정은 외층 봉인·metric이 한다', EP-7). 틀린 d/s 선언의 거부는 봉인 7 한 곳이 한다. 출발 단계가 따로 멈추면 같은 판정을 두 곳에 두게 된다. 또 모든 후보 충돌이 언제나 틀린 선언에서만 온다는 것은 증명되지 않았다(계수 부호가 섞인 행은 t에 의존한다). 그래서 상자 중심 탐색이 동작점을 찾을 여지를 남기고, 못 찾으면 봉인이 거부한다.
   * (가)는 출발 사다리 선택을 바꾼다(아래 끝이 전류 충돌일 때의 격자 탐색, 모든 후보가 충돌이면 칸 0 대체 대신 빈 사다리 → 상자 중심 출발). 원래 결정 O-10 (4)는 '충돌 기록'만 정했으므로 원래 취지와 다르다(X-G11). 바뀌는 회로·칸 수는 GC-5 착수 때 잰다(LUT가 필요해서 card 0 범위 밖).
4. **범위 밖**: 종속 전류 구간 결합 (a)~(c)는 백로그다(O-10 (4)). 이 card는 점 값만 다룬다.
5. **순서**: headroom-chain HC-1이 같은 파일을 고친다. 그래서 GC-5는 HC-1 뒤에 병합한다(N7.2).

### N3.7 정본 술어 교체

* metrics 3자리(R1·R1′·R2)는 `device.is_diode`·`graph.gs_groups`를 READS로 선언하고 읽는다.
* graph 층 안 4자리(R1″)는 같은 층에서도 정본 필드를 읽는다. net model이 S1 투영에서 만들어지므로 투영의 `is_diode` 열을 쓴다(경로는 GD-5).
* 쓰기 계획의 묶음 재유도는 N3.3-5.
* GC-6은 순수 리팩터링 card라 결과는 base와 필드별로 같아야 한다(N4-0). 정의가 다른 경우(예: R2는 kind 조건·궤도 결합이 다르다)는 card 0 M-G5에서 재고, 다르면 바꾸지 않고 공동분석으로 올린다.
* R1″ 세 파일(`cells.py`·`net_model.py`·`node_impedance.py`)은 `structure_rule_fp` 대상이라 고치면 `structure.json` rule_hash 재기록이 필요하다(U-G11).

### N3.8 재작성 범위 판정(사용자 원칙 '틀린 구조는 전체 재작성')

| 대상 | 구조 판정 | 범위(기본안) | 근거 |
|---|---|---|---|
| 노드전압 정식화·쓰기 계획 숲(`E/sizing/writer_plan.py`, `block_columns.py`) | 맞다. KVL을 엔진 방정식 그대로 푼다('같은 DC' 변은 K-3 card가 지운다) | 부분 수정: `gs_groups` 읽기 | F-G5 |
| 전류 기저(`E/sizing/current_basis.py`) | 맞다. KCL 전체를 정확히 푼다 | 변경 없음 | F-G4 |
| S1 G_vgs 사이클(`E/graph/gvgs_cycles.py`) | **틀렸다**: 엔진 방정식이 아닌 사본이고 정의가 다르다 | 정지 이전 뒤 모듈 전체 삭제와 등록 삭제(HC-1 뒤, U-G3) | N3.3-1·6·7 |
| 봉인 8(`E/sizing/seal_kvl_branch.py`) | 봉인 2 양의 합이다 | 기본안 삭제(U-G9) | N3.3-4 |
| 봉인 3(`E/sizing/seal_kcl.py`) | 계산식은 맞다. 봉인 2와 상관된 더 엄격한 집계다 | 변경 없음(문언만, X-G4) | N3.5-1 |
| 출발 전류(`E/search/start_intervals.py` `_state`의 전류 부분과 `feasible`·사다리 칸 판정) | **틀렸다**: KCL을 거치지 않는 소자별 자리값, 꺼지는 실패 표지, 판정 없는 아래 칸 | 함수 단위 재작성(전류 배정 부분, 실행 가능 판정, 사다리 칸 판정) | N3.6 |
| S1 관계 필드 모듈(`E/graph/rel_kcl.py`, `rel_vgs.py`, `rel_matching.py`, `matching_groups.py`의 `rel_matching_offset`) | 소비자가 없거나 정본 사본인 인코딩이다 | 출력이 모두 지워지는 모듈은 모듈 삭제(등록 포함), 일부만 지워지면 그 출력만 삭제(U-G3) | N3.2 |
| MNA 풀이(`E/metrics/mna_solve.py`) | 맞다 | 변경 없음 | N3.5-4 |

### N3.9 계산 재사용

* 숲 회계 불변량과 `node.terminals` 결선 점검은 θ 무관이다. 실행마다 처음 한 번 계산하고 그 실행 안에서 재사용한다. 블록 결과 재사용은 XRUN-F1 card B 블록 결과 색인이 맡고, 키는 X-20·X-21을 따른다. 새 캐시는 만들지 않는다.
* 트리 경로는 쓰기 계획 블록이 실행당 한 번 자기 출력 필드로 쓴다(N3.3-3, O-14 (1)). 소비자 셋은 그 필드를 읽고, 블록 밖에서 같은 경로를 다시 만드는 함수를 두지 않는다.
* S1 관계 블록과 봉인 8(U-G9 (가))을 지우면 S1 계산과 θ마다의 봉인 계산이 줄어든다. 블랭킷 READS를 줄이면 무관한 S1 열 변화로 생기던 재계산 의존이 사라진다(결과 값은 같다).
* 같은 입력 재계산은 0이어야 한다(상위 G-10 계수, 완료 조건 9).

### N3.10 상위·관련 문서 개정 목록(S-7: 계획 승인 → 상위 개정 → design)

| 문서 | 자리 | 개정 |
|---|---|---|
| 상위 계획 | 용어집 G_vgs 92행 | 정의를 Gs⁺(쓰기 계획: F = 레일 ∪ 노드 목표 ∪ 선언 입력 포트, MOS·저항 변, '같은 DC' 변 없음)로. 분류에서 `equal_vgs`·`kvl_branch` 관계 엣지 이름을 쓰기 계획 종속 분류로 |
| 같은 문서 | DEC-64 263행 | 루프 소속 기록 위치를 'S1 관계 엣지 `kvl_branch`'에서 '쓰기 계획 출력(`node.dc_writer`·`device.dc_coord`)과 같은 블록이 쓰는 넷별 뿌리 경로 필드'로(X-G1, O-14 (1)). J12-c 측정 기대는 card 0 대조 기록으로. v1 문언은 상위 계획 IT-1 커밋 `3fd202b`에서 O-13 (1) 문언(같은 DC 등식 없음, 포트 경로 둘 이상이면 ΔV 소거 KVL 하나 남음, 대칭이면 묶음과 중복)으로 정정됐고 master `f2852c36`에 병합됨. 이 개정 항목은 v1 부분을 다시 고치지 않는다 |
| 같은 문서 | DEC-15 215행 | X-G1과 같이 |
| 같은 문서 | DEC-17 217행 | tail 정의의 '`kcl_group`에서 공통 source 전류를 공급하는'을 F-G25의 정의('drain이 둘 이상 소자의 공통 source 넷인 바이어스 전류원')로(사실 정정) |
| 같은 문서 | S1 구조 400행 | 관계 엣지 목록에서 삭제 승인된 type을 지우고, 구현되지 않은 `stacked_vsb`·`same_as`의 상태를 사실로 적는다(X-G7, U-G3) |
| 같은 문서 | LR5 553행 | 미러 정의 '`equal_vgs` 멤버'를 '`gs_groups` 멤버(gate 비레일)'로 |
| 같은 문서 | V9 920행 | `matching_offset` 멤버 출처를 `matching_groups`로, `matching_ratio` 멤버 출처를 `gs_groups`(gate 비레일)로. 이 개정이 `rel_matching_offset`·`rel_matching_ratio` 삭제의 선행이다 |
| 같은 문서 | 봉인 표의 봉인 8 행(master 472행, v6.19 `plan/gb-v619` `6ab294c9` 488행) | U-G9 (가) 결정(O-13)대로: 행 삭제와 '그 역할은 봉인 2가 소자별로 한다'는 사실 기록(X-G10). 숲 회계 불변량은 별개 보조 검사로 따로 적는다. 봉인 집합 표기는 gain-budget v6.19가 이미 '커널 = 봉인 전 항목'(`6ab294c9` 491행 -- 항목 번호를 나열하지 않음)으로 바꿨고 봉인 9도 표에 들었다(전체 정합 검증 B-M5 반영 끝남). 그래서 봉인 8 행을 지우면 커널 봉인 집합은 그 문언대로 따라간다. 이 행의 봉인 8 삭제 반영은 v6.19 병합 뒤 그 표 기준으로 한다 |
| 같은 문서 | 봉인 표 467행(봉인 3)·`tol_I` 477행 | 기본 경로에서 봉인 2와 상관된 더 엄격한 집계임을 사실로(X-G4) |
| 같은 문서 | DEC-08 208행 상태 칸 | 'KCL 잔차 metric만 소비'에 '그 잔차는 결선 행렬 항등식이라 판정하지 않음, 독립 KCL 확인은 오라클 forced'를 더한다 |
| 같은 문서 | N6.3 1153행 | 병합 전 확인에 규칙 L green과 부채 목록 계수(기준선 지문 대조 포함)를 더한다 |
| 같은 문서 | card 표 U16 완료 조건 | '13회로 오라클 forced·free 대조 실행'과 'U16 card id 부채 항목 0'을 더한다(N3.5-2). oracle-portability 계획의 관련 card에도 같은 문언이 필요한지는 그 계획 개정 때 확인 |
| 같은 문서 | card 표 N6.1 단위 8·U17 ② 완료 조건 | '해당 card id 부채 항목 0'을 더한다 |
| 같은 문서 | card 표 | K-3 구현 card = 상위 card IT-1(N6.5, card 정의 master `f2852c36`에 병합됨, F-G19). 이 계획이 더할 개정은 없다 |
| 같은 문서 v6.19(브랜치 `plan/gb-v619` `6ab294c9`, 승인 전) | card DE-1(N6.8) 소비자 표 F-DE7 | `SatDevice.vgs_v` 칸(`E/metrics/aux_types.py:102`)과 그 값을 채우는 `op.vgs` 전달(`E/metrics/metrics_aux.py:125`)의 삭제를 DE-1 범위에 더한다. 근거: 그 칸은 DE-1이 지우는 코드(`ls_swing._constraints`, 유일한 소비자 `ls_swing.py:47`)에만 쓰인다. 지우지 않으면 소비자 없는 칸이 남는다(규칙 L-4). `SatDevice`는 계산 입력이라 L-5 부채 항목은 아니다(N3.1-5). 지금 F-DE7은 `aux_types.py:139-172, :251-260`만 적는다 |
| 같은 계획 v6.19(작성 중) | 층 0 손계산 card **LA-1**(O-36) | `size_and_seal_local`(`E/sizing/size_and_seal_local.py`)을 층 0 블록 국소 후보(DEC-71 (5))에 배선하고, 그때 `LocalSeal.snapshot_fragment`가 `DeviceOp` 사본 대신 `dc_op` 참조를 담게 바꾼다. 이 계획 부채 목록의 '배선 대기' 항목(N3.2 표) card id다 |
| design 41 | §5 589행 | 층 0 등식 목록의 `equal_vgs`·`kvl_branch`를 정본 이름(`gs_groups`, 쓰기 계획 종속 분류)으로. `stacked_vsb`는 S1 관계 엣지가 아님을 적는다 |
| 같은 문서 | §5.5 917행 | 조립 공유량(`equal_vgs` 공통 VGS, 미러 비, `kvl_branch` 종속 gm/ID)의 출처를 정본으로(GD-8) |
| 같은 문서 | §6.7-1 1491행 | 쓰기 계획을 'S1 G_vgs 고리(`graph.rel_kvl_branch`)를 … 컴파일한 것'으로 적은 문언을 '쓰기 계획이 KVL 정본'으로 |
| 같은 문서 | §6.7-10 1533행 | (P1)의 `kvl_branch` 등식을 쓰기 계획 종속 분류의 등식으로 |
| `E/graph/CONTRACT.md` | 관계 엣지·`gvgs_summary` 절 | 삭제 반영, `gvgs_self_edge` 정지 위치 이동 |
| `E/sizing/CONTRACT.md` | 쓰기 계획·봉인 3·8 절 | KVL 정본 = 쓰기 계획 출력, 넷별 뿌리 경로 필드(쓰기 계획 블록 출력), 숲 회계 불변량 검사, 봉인 8 처리 |
| `E/search/CONTRACT.md` | 출발 전류 절 | 충돌 표지, 기저 경유, 사다리 칸 단위 처리(U-G13) |
| design 40 §2.4.8 | 필드 소유표 | 삭제 행, 새 검사 행, reader 칸 여부(GD-6) |
| design 40 §2.4.10 | 구조 규칙 | 규칙 L 추가 |

이 계획은 headroom-chain 계획을 고치지 않는다. v0.7.1 개정안이 Gs⁺를 K-3 뒤 기준으로 이미 맞췄다. O-14 (1)이 그 계획에 지시한 것(제약 그래프의 '경로 목록은 저장하지 않는다' 문언을 쓰기 계획 블록의 경로 필드 읽기로 바꾸기, 완료 조건에 WP-10 계측 넣기)은 headroom-chain 계획 개정 소관이다(N3.3-3).

**대기·후속 항목**(P-G1은 O-13 (1)로 닫혀 v0.8에서 고쳤다. P-G2는 지금 고치지 않는다):

| ID | 대상 | 내용 | 대기 조건 |
|---|---|---|---|
| P-G1 | 이 계획의 DEC-64 v1 고리 문언 | **결정됨(O-13 (1), v0.8 반영)**. 정정 내용: 같은 DC 등식은 없앤다. 포트 경로가 둘 이상인 v1 고리는 ΔV를 소거한 KVL 하나가 남고(파일럿 M1b `cycle_vgs`: VGS1a − VGS1b = VGS4a − VGS4b), 대칭이면 묶음과 중복이다. 고친 자리(줄 번호는 **v0.8 기준**):<br>• N0.1 'Gs⁺' 정의(53행 -- 나머지 포트 MOS writer와 남는 KVL의 관계 보강), 'KVL 관계' 정의(54행)<br>• N2 상위 항목 표 DEC-64 행(161행), N3.2 처리 표 `gvgs_summary` 행(289행 `port_diff`)<br>• N3.3-1 표 '미선언 입력 포트' 행(317행), N3.3-2 'tie 변 제외의 근거'(325행), N3.3-8(344행)<br>• N3.5-3 숲 불변량 성립 조건(366행 -- 이 고리를 포함해 불변량이 성립함을 한 줄)<br>• N3.10 상위 DEC-64 개정 행(453행 -- 상위 v1 문언 개정 여부는 정하지 않음 표시)<br>• N3.11 K-a′(490행), N7.2 headroom-chain 항목의 Gs⁺ 문장(600행 -- 정의와 남는 KVL이 맞음)<br>• 고치지 않은 경계 자리: N2 design 41 §6.7-1a 행(176행, design 문언 요약), N3.10 상위 용어집 G_vgs 개정 행(452행, '같은 DC 변 없음' 개정 문안). v1 고리에 제약이 없다는 전제를 담지 않는다<br>• 302행 지목(v0.3 재검증)은 해당 문언이 없어 위 자리로 대신했다(history H2-7) | 닫힘 |
| P-G2 | headroom-chain 완료 조건 문언 | 트리 경로가 쓰기 계획 블록의 필드 하나로만 만들어지고 블록 밖 재구성이 0이라는 확인(이 계획 완료 조건 3, GC-V 검증자 확인 항목)을 headroom-chain HC-1 완료 조건에도 같은 문언으로 둘지 권고만 기록한다(O-14 (1)의 WP-10 계측은 그 계획에 이미 지시됐다). 이 계획은 headroom-chain 계획을 개정하지 않는다 | headroom-chain 계획 개정 때 오케스트레이터가 판단 |

### N3.11 제한 조건 점검표(P-1)

| ID | 조건 | (a) 유도·사실 | (b) 일반형 | (c) 처리 |
|---|---|---|---|---|
| K-a | KVL 정본은 S0 | F에 spec 값(노드 목표·입력 DC 선언)이 들어가므로 사이클 집합이 spec에 의존한다 | 엔진 방정식 전체(MOS·저항 변) | 쓰기 계획 출력 |
| K-a′ | KVL 정본에 '같은 DC' 변 없음 | 입력 DC 미선언이면 두 포트 DC가 같다는 물리 제약이 없다. 같음은 대칭일 때만이다(B2·K-3). 포트 경로가 둘 이상이면 ΔV를 소거한 KVL 하나는 남는다(O-13 (1)) | 대칭 묶음 `domain.ties`, 남는 KVL은 비트리 MOS 종속(보통 `cycle_vgs`, 대칭이면 묶음과 중복) | K-3 card 뒤 쓰기 계획 |
| K-a″ | 이 계획은 등식 사이클만 | VDS 변을 지나는 사이클은 포화 부등식이다(DEC-64 VDS-1) | 제약 그래프(headroom-chain N3.1) | HC-1 소관 |
| K-b | KCL 정본은 기저 | 모든 내부 넷 KCL의 해가 직렬 같은 전류를 포함한다 | 전체 KCL | 기저 하나 |
| K-c | 봉인 8은 봉인 2에 함의됨 | 봉인 8 행 = 봉인 2가 모든 MOS에 대해 재는 양의 사이클 합(F-G31). 멤버마다 \|오차\| ≤ tol_V면 합도 ≤ 합 tol_V | -- | U-G9(기본안 삭제) |
| K-d | 봉인 3은 봉인 2와 상관된 더 엄격한 집계 | DEC-88 W = ID·L/IDu라 MOS 잔차 몫 = Σ ID(e^Δ − 1) ≈ Σ gm·ΔVGS(1차). 봉인 2가 주는 상한은 합, 봉인 3 허용오차는 max | 상관 없는 잔차는 W가 ID에서 오지 않는 경로 | 사실 기록 + 그 경로 배선 확인(M-G4) |
| K-e | 공급 합·결선 대조는 판정하지 않음 | 결선 행렬 항등식, 같은 출처(F-G21·F-G22) | 독립 KCL = 오라클 forced | 판정 없음 |
| K-f | MNA 상대 잔차 없음 | 부분 피벗 LU는 후진 안정이라 잔차가 조건수와 무관하다(F-G28) | 조건수 | 백로그 B-G1 |
| K-g | 출발 자리값은 자유 원소에만 | KCL: 종속 원소 전류는 자유 원소의 선형식이다 | 점 값 전체 | 구간 결합은 백로그 |
| K-h | 비레일 g = s는 정지, 레일 g = s는 `fixed_vgs` | **물리 근거 없음**: 둘 다 VGS가 구조로 0인 소자다. 비레일 정지는 지원 범위 표시다(F-G20) | 같은 처리 | 보존만, 일반화는 백로그 B-G3 |
| K-i | 숲 회계 불변량 = 순환수 | 신장 숲의 비트리 변 수는 \|E\| − \|V\| + 성분 수다(그래프 이론). 비트리 저항은 멈추므로 비트리 변은 모두 MOS다. 성립 조건은 N3.5-3 | -- | S0 검사 |
| K-j | 0 이하 전류 = 동작점 아님 | 선언 d/s 방향으로 부호가 고정됐을 때만 성립한다. 결정 6이 그 방향을 고정하고, 결정 6은 `c8d156e3`으로 이미 병합됐다(F-G36) | -- | 지금 성립(BD-13 충족). GC-5의 추가 선행 아님 |
| A-1 | 규칙 L-3 helper 추적 한 단계 | 알고리즘. 더 깊은 추적은 정적 해석 비용이 커지고 못 풀면 위반이므로 보수적이다 | -- | 유지, 못 풀면 위반 |
| A-2 | 규칙 L-4 이름 기반 | 알고리즘. 놓칠 수는 있으나 살아 있는 칸을 죽었다고 하지 않는다 | -- | 하한으로 보고 |
| A-3 | 규칙 L-5 등록 개념·AST 꼴만 | 알고리즘. 패턴 일치는 helper 안 비교나 여러 문장에 걸친 변수 전달 같은 자료 흐름 꼴을 잡지 못할 수 있다. 기존 자리(F-G13)는 거부 증거로 모두 잡음을 보인다 | -- | 리뷰·gap 분석이 나머지를 맡는다 |
| A-4 | 부채 목록 기준선과 규칙 매개변수 지문 | 알고리즘(감소 강제). 기준선은 측정값이지 발명값이다. 지문은 검증자 기록에 고정 | -- | 넓히기 = 기준 약화(승인) |
| A-5 | 규칙 L-1·L-2 호출 그래프 도달 | 알고리즘. 정적 호출 그래프는 동적 호출을 못 따라간다 | -- | 못 풀면 위반 |

---

## N4. 13회로 적용 판정

판정은 규칙으로 한다. 회로는 library 9 + heldout 4다. 기저 단계에서 멈추는 회로(`StructureUnresolvedError` 등)는 그 사유를 그대로 남기고, 멈추기 전까지의 필드로 판정한다.

0. **변경 종류별 판정 기준**(사용자 결정 O-34 (1), `wt/_drafts/user_decisions.md` 654행 -- 상위 N6.3·NFR-4의 공통 규칙). card마다 변경 종류를 표시하고 그 기준으로만 판정한다.

   | 종류 | 이 계획의 card | 판정 |
   |---|---|---|
   | 결정성 | 모든 card | 같은 코드·환경·입력으로 두 번 실행한 결과가 비트 동일. 항상 검사한다 |
   | 순수 리팩터링(동작 보존 선언) | GC-2, GC-3, GC-6, GC-9, GC-7의 리팩터링 부분 | base와 **필드별** 비교: 이산 값은 정확히 같고, 연속 값은 기존 선언에서 유도한 분해능 이내(NFR-4, 상위 NFR-4 필드 분류·비교기) |
   | 동작 변경(규칙·정의·계산법을 바꿈) | GC-5, GC-8, GC-7의 동작 변경 부분 | 비트 동일을 요구하지 않는다. 판정 = 정의 문장으로 만든 손계산 오라클 toy + 봉인 불변식(KVL·KCL·영역) + SPICE oracle 대조(선언 모델 오차 이내) + 검증자 값 변화표(원인 미설명 변화 0). 기준선은 기록이고, 갱신은 검증자 변화표를 근거로 한다(IT-Q3 (가) 방식의 일반화). 사용자 승인은 원인 미설명 변화가 있을 때만이다. **판정 다리 보류·대상 없음**은 gain-budget v6.19(브랜치 `plan/gb-v619` `6ab294c9`) N6.3 1232행 규칙을 따른다(정본, 이 계획은 인용만 한다): (i) 보류 -- 채울 수 없는 다리가 있으면 그 card는 미완료이고 통과로 세지 않는다, (ii) 대상 없음 -- 바뀌는 값이 SPICE로 정의되지 않는 값뿐이고 그 값을 판정에 쓰는 소비자 0을 `git grep` 증거로 남길 때만, (iii) 출발 단계만 바꾸는 card(FX-1, headroom-chain HC-1, 이 계획 GC-5)의 SPICE oracle 다리 = 시작점의 ngspice 판정(DEC-98 A' 기준). **모든 동작 변경 card의 SPICE 다리 선행 = gain-budget card EO-1**(N6.20, 엔진 점 → oracle 입력 생산자·판정 배선, 사용자 결정 O-44 (1)). 이 계획에서 SPICE 다리가 있는 동작 변경 card는 이 표의 GC-5, GC-8, GC-7의 동작 변경 부분(`conduction_mask` 통일)이고, 셋 다 EO-1을 **완료 판정 선행**으로 둔다(N7.1). **병합 규칙**은 N6.3 (iv)(정본, 이 계획은 인용만 한다)다: (가) 보류 다리를 채울 card id(여기서는 EO-1)가 판정 기록에 적혀 있을 때만 병합할 수 있고, 병합해도 '미완료'로 남아 완료 계수에 들지 않는다 (나) 채울 card id가 없으면 병합하지 않고 멈춰 사용자에게 보고한다. 그래서 EO-1 전에 이 셋을 병합하려면 판정 기록에 SPICE 다리 '보류(채울 card = EO-1)'가 있어야 하고, 그 card는 EO-1 뒤 다리를 채울 때까지 미완료다. **다리 상태 어휘는 둘뿐이다**(N6.3 (iv)): '보류'(채울 card id와 함께)와 '대상 없음'((ii)의 증거와 함께). 채워진 다리는 상태어 없이 판정 결과(통과·거부)로 적는다. **EO-1 뒤 OP-5 전 기간**(같은 N6.3 1232행, 3차 감사 N5): oracle OP-5 병합 전에는 합격 판정의 '꺼짐'이 옛 식(ε = 1)이라, 판정 기록에 '꺼짐 정의 판'(옛 ε = 1 식 / 봉인 9 식)을 적고, 옛 식으로 판정한 SPICE 다리는 '보류(채울 card = OP-5)'로 둔다 -- OP-5 병합 뒤 봉인 9 식으로 다시 판정한다. 모든 card는 완료 조건에 변경 종류와 다리 상태를 적는다 |
   | 측정·문서·test만 | GC-0a, GC-0b, GC-D, GC-1 | 엔진 운영 코드 변경 0 |

   * **GC-7은 부분별로 나눠 표시한다**(headroom-chain HC-S와 같은 방식): `conduction_mask` 통일(두 격자판 마스크의 차이를 하나로 맞춤, R3 처리 포함)은 **동작 변경**이다. 출력 전용 선언, `coupling_vars`·`l_classes`의 `gs_groups` 읽기, 블랭킷 READS 정리, 동적 접근의 정적 형태 전환, `sctx.cell_floors` 제거(값을 LUT memo 파생 함수로 옮김), 승인된 삭제는 **순수 리팩터링**(필드별)이다. 검증자는 부분마다 해당 기준으로 판정한다.
   * **GC-9는 순수 리팩터링이다**: 원래 취지가 동작 보존 단일화이고(v0.10 '비트 동일, N4-1 대상'), 내용(기저 float 변환 1회, 정확 전류 공용 함수, `current_cone`의 기저 읽기)도 같은 값을 한 곳으로 모으는 것이다. 부동소수 합산 순서 차이는 순수 리팩터링 기준의 '연속 값 선언 분해능 이내'가 이미 받는다. 동작 변경으로 표시하면 판정 기준을 약하게 바꾸는 것이라(사용자 승인 필요) 그렇게 두지 않는다.
1. **순수 리팩터링 card(GC-2·GC-3·GC-6·GC-9, GC-7의 리팩터링 부분)**: 비교 대상은 DC 필드(노드전압·소자 op·전류), 봉인 판정(통과·거부·margin), front 지문이다. 지운 필드·지운 봉인 행과 새 보조 검사 결과는 비교에서 빼고 따로 단언한다. 나머지는 base와 필드별 비교(N4-0)로 같아야 한다. GC-2의 base는 K-3 구현 card가 병합된 master다(K-3은 입력 DC 미선언 회로의 결과를 바꾼다, design 41 §6.7-1a).
2. **봉인 8**(U-G9 (가)): 지운 행은 비교에서 뺀다. base에서 봉인 8 거부가 있었던 회로·θ가 있으면 그 거부가 봉인 2 거부에도 있었는지 대조해 보고한다(K-c 확인). 봉인 2 거부가 없는 봉인 8 거부가 있으면 결함으로 보고하고 삭제를 멈춘다.
3. **보조 검사**: 숲 회계 불변량과 결선 점검은 13회로에서 통과해야 한다(card 0 M-G7로 K-3 병합 master에서 먼저 확인).
4. **GC-5(출발 전류, 동작 변경 card -- N4-0)**: 자리값을 쓰지 않고 충돌 표지도 서지 않는 회로는 출발 기록이 변화표에 나오지 않아야 한다(원인이 없는 변화 0). 그 밖의 회로는 바뀐 출발 칸마다 원인('기저 경유 자리값' 또는 '충돌')이 기록과 변화표에 있어야 한다. 해당 회로 수와 U-G13 (가)로 빠지는 칸 수는 GC-5 착수 때 잰다(LUT가 필요해서 card 0 범위 밖). 같은 착수 측정에서 `E/search/start_intervals.py:264` 조기 반환(모든 L에서 LUT 곡선 미정의)에 걸리는 회로 수도 잰다(측정 **M-G8**, 기대 0. 산출: 회로 수와 회로 목록. 측정 주체는 검증자. LUT가 필요해 card 0(N6, LUT 없이 도는 측정) 표에는 두지 않는다). 그 조기 반환의 `uncovered` 정렬(GD-7)은 충돌이 없는 회로의 출력도 바꾸므로, 해당 회로가 있으면 그 회로의 `graph/start: uncovered` 변화는 변화표에 원인('조기 반환 정렬, GD-7')을 달아 기록하고 '칸 0 성분 전부'임을 따로 단언한다(N4-0 동작 변경 기준이라 별도 예외 승인은 필요 없다).
5. 제외 목록은 검증자가 소유한다.

---

## N5. 원래 취지와 다름(따로 보고)

| ID | 내용 | 원래 결정·취지 | 상태 |
|---|---|---|---|
| X-G1 | **KVL 루프 소속의 정본을 S1 관계 엣지 `kvl_branch`에서 쓰기 계획 출력(`node.dc_writer`·`device.dc_coord`, 그리고 같은 블록이 쓰는 넷별 뿌리 경로 필드 -- O-14 (1))으로 옮기고, S1 `rel_kvl_branch`·`gvgs_summary`와 `gvgs_cycles` 모듈을 지운다.** 근거: S1 판은 엔진 방정식이 아니고(F 정의·저항 변 차이), 엔진 방정식은 spec에 의존해 S1에 담을 수 없다(N3.3-2). design 41 §6.7-1도 쓰기 계획을 고리 출처로 정했다 | 상위 DEC-64 263행·DEC-15 215행('루프 소속은 S1 관계 엣지 `kvl_branch`로 기록'), J12-c 측정 기대 | 승인(O-13, U-G1·U-G3) |
| X-G2 | **철회(v0.2)**. v0.1은 as-built '같은 DC' 변 동작을 상위 DEC-64 v1 문언으로 올리자고 했다. 이것은 사용자 결정 B2·K-3과 반대였다 | 상위 DEC-64 v1, B2, K-3 | 철회 |
| X-G4 | **봉인 3의 '독립 KCL 잔차' 요구를 엔진 안에서는 그대로 만족할 수 없다는 사실을 보고한다.** 기본 경로의 W가 DEC-88에 따라 KCL 전류에서 나오므로, 봉인 3 잔차는 봉인 2 불일치와 상관된다. 다만 허용오차가 max(봉인 3) 대 합(봉인 2가 주는 1차 상한)이라 봉인 2가 봉인 3을 함의하지는 않는다(더 엄격한 집계). 독립 KCL 확인은 오라클 forced 모드다(N3.5-2) | 오케스트레이터 범위 초안 (3) '봉인 3이 LUT 전류로 노드별 KCL 잔차를 독립 계산' | 보고, 승인(O-13, U-G10) |
| X-G5 | **지정 소비자가 아직 없는 필드(층 0 조립 3필드, 단계 B 2필드, `ly_rows`, `dc_off_current`, 출발·진단 기록)는 이 계획에서 배선하지 않고 부채 목록 '배선 대기'로 두며, 소비자를 만드는 card(단위 8, U17 ②, U16)가 배선한다.** 그 card들의 완료 조건 변경은 상위 개정 항목이다(N3.10). `dc_off_current`는 O-46 (2) 뒤 소비자가 EO-1~OP-5 사이에만 있으므로, EO-1이 배선하고 OP-5 병합 때 출력 전용으로 선언한다(N3.2 표) | 범위 초안 (4), 원칙 '만들면 배선' | 승인(O-13, U-G6) |
| X-G6 | **`dc_conduction_floor`의 docstring 소비자('search가 읽는 하한')는 단계 순서상 성립하지 않을 수 있다는 의견을 공동분석으로 올린다.** 의견: search 상자는 θ 확정 전(칸 전체 보수 하한)에 만들고, 필드는 평가된 설계점 하나의 값이다. 읽으면 평가 뒤 값을 평가 전 상자에 쓰는 순환이 된다. 확신도 중간(근거: `E/search/cell_floor.py:53`, `E/search/current_box.py:1-10`, `E/sizing/seal_conduction.py:12-13`) | 봉인 9 docstring, O-10 'R3 정의역 차이는 공동분석' | 승인(O-13, U-G4 (가)) |
| X-G7 | **소비자 없거나 정본 사본인 S1 관계 엣지 type(`kcl_group`·`vds_eq_vgs`·`matching_ratio`·`matching_offset`, 그리고 소비 이동 뒤 `equal_vgs`·`l_class`)을 지운다.** 상위 S1 구조 400행이 관계 엣지 목록으로 설계한 층을 줄인다. `matching_ratio`·`matching_offset`은 상위 V9의 검증 소비자 지정을 정본으로 옮긴 뒤다. 목록의 `stacked_vsb`·`same_as`는 이미 S1 관계 엣지로 구현되지 않았다(F-G29) | 상위 400행·V9 920행, design mod3 3.2 | 승인(O-13, U-G3 항목별) |
| X-G8 | **출발 전류를 KCL 기저로 거치게 한다.** O-10 (4)는 음수 자리값 조용한 대체를 충돌 기록으로 바꾸는 것만 정했다. 이 계획은 자리값 자체도 자유 원소에만 두고 나머지를 기저 행으로 계산한다(범위 초안 (5) G4). 새 전류 사슬은 아니고 기존 기저를 쓴다. 출발값이 바뀌는 회로가 생긴다 | O-10 (4) | 승인(O-13, U-G8) |
| X-G9 | **범위가 O-10 (2)·(4)보다 넓다.** O-10 (2)는 규칙 L·부채 목록·필드별 처리·R3 공동분석, (4)는 출발 음수 자리값 충돌 기록만 정했다. GC-2(KVL 정본 이동·봉인 8 처리·S1 사본 삭제·정지 이전·숲 회계 불변량), GC-3(`rel_kcl_group` 삭제·결선 점검), GC-8(R4 처리 -- O-10은 R3만 공동분석으로 정했다)은 사용자 원문 KK-1('관계가 엔진에 적용되어 있는지도 확인해')과 소비 정합 조사에서 나온 처리이고, '확인'을 넘어 엔진을 고친다 | O-10 (2)·(4), KK-1 원문 | 승인(O-13, U-G12). GC-8 재질문 대상은 소멸했다 -- 그 내용(위쪽 방향 차분 제약 그래프가 R-1′ 변 목록을 정본으로 읽음)이 O-15 (C)·O-16 (3) 승인 범위다 |
| X-G10 | **봉인 8을 지운다**(U-G9 기본안). 상위 472행이 봉인 8에 맡긴 일은 봉인 2가 θ마다 소자별로 이미 한다(F-G31). 숲 회계 불변량은 봉인 8을 대체하지 않는 별개 보조 검사다. 상위 봉인 표가 정한 봉인 하나가 없어진다 | 상위 472행 | 승인(O-13, U-G9 (가)) |
| X-G12 | **원칙 감사로 범위를 넓힌다**(O-15 (E), card GC-9와 GC-5·GC-2의 일부): 기저 행 float 변환 1회, 정확 MOS 전류 공용 함수 하나와 `current_cone` 사본의 기저 읽기 전환·삭제 절차(`_vds_floor`의 `lut.derived` 이동은 headroom-chain HC-S로 옮김, 오케스트레이터 기본안), 완료 조건 3을 '두 단계 이상 따라가는 경로 재구성'으로 좁힘, 블록 안 local memo 허용과 `bracket_root` 뒤 같은 점 재풀이 금지. 원래 O-10 범위(규칙 L·필드별 처리·출발 음수 자리값) 밖의 엔진 변경이다. 근거는 원칙 감사(사용자 2026-10-19 'graph에 값을 유지하는 것은 함수마다 재사용을 해서 반복계산이나 서로 다른 값을 사용하는 것을 막기 위해서') | O-10 (2)·(4) | 승인(O-15 (E)) |
| X-G13 | **`size_and_seal_local`을 지우지 않고 '배선 대기'로 둔다**(v0.11). 엔진 안 호출자가 0인 함수는 원칙 '만들면 배선'에 어긋나지만, 지정 소비자(층 0 블록 국소 후보, DEC-71 (5))를 gain-budget v6.19 card LA-1이 만들므로 LA-1 병합까지 부채 항목으로 둔다. 그 기간에는 미배선 함수와 그 안의 `DeviceOp` 담기(`snapshot_fragment`)가 남는다 | 사용자 전역 원칙 '만들면 배선' | O-36 (1) 승인(기한 = LA-1 병합) |
| X-G11 | **출발 충돌 칸을 사다리 선택에서 뺀다**(U-G13 기본안). O-10 (4)는 '충돌 기록'만 정했다. 기본안은 충돌 표지가 선 상태를 최상 칸 선택에서 실행 불가로 세고, 아래 칸에서는 사다리에 넣지 않는다. 아래 끝(t = 0)이 전류 충돌이고 최상 칸이 실행 불가면(최상 칸의 충돌 여부 무관) 사다리 격자에서 고른다: 충돌 없고 실행 가능한 최대 t, 없으면 충돌 없는 최소 t(기본안 (가-1)). 그 점이 매크로 실패면 `use_macro` 해제를 그 점에서 판정한다(지금은 아래 끝에서 판정). 빈 사다리는 선택 후보(격자 점과 t = 0)가 **모두** 전류 충돌일 때만이다. 그때는 지금처럼 아래 끝을 칸 0으로 쓰지 않고 빈 사다리로 두어 층 0이 상자 중심에서 출발한다(d/s를 거꾸로 선언한 회로에서 실제로 일어난다, N3.6-3). 1회차 전류 충돌은 자리값 없이 경계 비활성·충돌 기록이다. `gain_l_bounds`가 지금 원인과 다른 '이득 목표 미달'을 기록하는 경로도 바뀐다. 출발 사다리 선택이 바뀌는 회로가 생긴다 | O-10 (4) | 승인(O-13, U-G13 (가) + (가-1)) |

(X-G3 번호는 비웠다. 봉인 8이 봉인 2에 함의되는 사실은 상위 472행이 이미 적고 있어 원래 취지와 다르지 않다. history H1에 적었다.)

---

## N6. 선행 측정 -- card 0 (엔진 무변경)

* 측정 주체는 검증자다. 엔진 코드는 바꾸지 않는다.
* 스크립트는 저장소 밖 측정 전용 경로에 두고, 결과를 회로마다 파일에 append한다.
* 기준 base는 측정 시작 때 master 해시로 고정해 기록한다.
* **LUT 없이** 돈다. S1 graph 구성과 `dc_current_basis`·`dc_writer_plan` 블록만 실행한다(블록 입력: S1 투영, spec의 노드 목표·입력 DC 선언·선언 전류원).
* 13회로를 **하나씩 순차로**, 회로마다 새 프로세스에서 실행하고 최대 메모리를 기록한다. 기저 단계에서 멈추는 회로는 멈춘 사유를 기록하고 그 앞까지 잰다.
* **K-3 뒤 기준이 필요한 측정(M-G1·M-G1b·M-G7)은 K-3 구현 card가 병합된 master에서 잰다**(GC-0b). as-built를 고쳐 K-3을 모사하지 않는다. 모사가 실제 구현과 갈라질 수 있기 때문이다(headroom-chain v0.7.1 448-451행과 같은 관행).
* **M-G3(규칙 L 기준선)은 두 번 잰다**: GC-0a에서 예비 계수(규모 파악), GC-1에서 GD-1(진입점·출력 모듈)이 닫힌 design 기준으로 기준선을 다시 잰다. 기준선 상수는 뒤의 것이다.

| ID | 측정 | 산출 | card |
|---|---|---|---|
| M-G1 | **KVL 대조**: 쓰기 계획의 종속 소자(분류별)와 각 기본 사이클(쓰기 계획 블록의 넷별 뿌리 경로 필드에서 -- 그 필드가 아직 엔진에 없으면 측정 스크립트 안에서 `NodeWrite.known` 포인터를 따라가고 그 사실을 기록, N3.3-3)을 S1 `rel_kvl_branch`·`gvgs_summary.port_diff`·`fixed_vgs`와 대조한다. 기저 무관 불변량(사이클 공간 차원, 비다리 변 합집합)으로 비교하고, 차이마다 원인을 (i) 저항 변 (ii) 노드 목표 F (iii) 선언 입력 F (iv) 평행 변 (v) 숲 선택 중 하나 이상으로 붙인다 | 회로별 표. 정의가 다른 실제 사례 목록. 원인 없는 차이 = 0이어야 한다 | GC-0b |
| M-G1b | **봉인 8 대조 자료**: 회로별 base 봉인 8 행 수(= `rel_kvl_branch` 수) 대 종속 소자 수 | U-G9 근거 | GC-0b |
| M-G2 | **KCL 대조**: `rel_kcl_group` 묶음마다 멤버 전류가 기저 행에서 같은 선형식인지 | 일치 여부. 다르면 사례 | GC-0a |
| M-G3 | **규칙 L 계수**: 규칙 L-1~L-5 위반 항목 집합(도달 조건 포함). 정적 해석이다(LUT·실행 없음). 검증자의 독립 측정 스크립트로 잰다(규칙 L 코드를 쓰지 않는다, N3.1-6 (c)) | GC-0a: 예비 계수. GC-1: 기준선 집합(검증자 지문 고정) | GC-0a·GC-1 |
| M-G3c | **하위 칸 범위 계수**: 규칙 L-4 대상을 graph 필드 값 형식으로 한정했을 때의 0 칸 수와 칸별 분류(보고 덤프·지문·그 밖) | GC-7 처리 목록 | GC-0a |
| M-G4 | **봉인 3 상관 없는 경로**: W_request(LY3)·실현 기하 재평가 경로에서 봉인 3이 호출되는지(코드 경로 읽기) | 배선 대기 항목 필요 여부 | GC-0a |
| M-G5 | **정본 술어 교체 동치**: R1·R1′·R1″·R2 자리의 지금 판정과 정본 필드 판정이 13회로에서 같은지(S1만으로 가능한 것만) | 교체 가능 목록. 다르면 공동분석 | GC-0a |
| M-G6 | **R3 공동분석 자료**: 봉인 9 필드와 search 두 계산의 식·정의역·호출 시점을 표로(읽기) | U-G4 근거 | GC-0a |
| M-G9 | **L-1 확장 대상 사전 측정(AST)**: 규칙 L-1 확장 '호출자 0 내부 함수'(GD-14)의 대상을 AST 호출 그래프로 미리 잰다. 엔진 진입점 후보 목록에 없고 엔진 안 호출자가 0인 함수 전부(이름 grep이 아니라 호출 그래프 -- docstring 언급은 호출이 아니고, import 시 실행되는 호출도 센다). 이름 grep 사전 조사(diff 확인 때)에서 `size_and_seal_local` 밖에 후보 셋(`pin_blas_threads` `E/core/blas_env.py`, `CanonPointer` `E/core/canon_pointer.py`, `resolve_lut_location` `E/lut/data_location.py`)이 나왔다. 이 셋은 지금 분류하지 않고 이 측정 결과로 처리한다 | 대상 목록과 함수마다 근거(호출 경로 없음·import 시 실행 등). 배선·삭제·진입점 등록은 사용자 승인 항목으로 올린다. GC-1이 예상하지 못한 대상으로 멈추지 않게 한다 | GC-0a |
| M-G7 | **보조 검사 base 확인**: 13회로에서 숲 순환수(N3.5-3 성립 조건) = 종속 소자 수인지, 기저 `ends`가 `node.terminals`와 맞는지, `gvgs_self_edge`로 멈추는 회로 수 | 보조 검사가 base에서 통과함(아니면 결함 보고). 정지 이전의 비교 기준 | GC-0b |

(v0.1의 M-G1c·M-G2b·M-G2c는 지웠다. M-G1c는 `rel_equal_vgs`가 `gs_groups` 1:1 사본이고 `parallel_vgs` 키가 `gs_groups` 키와 같아 정의로 같다(F-G26, N3.3-5). M-G2b는 코드 읽기로 답이 나왔다(F-G25). M-G2c는 항등식이다(F-G22).)

---

## N7. card 단계·순서·완료 조건

### N7.1 card

**공통 착수 조건**: 다음이 모두 갖춰져야 엔진 card를 시작한다.
* design 문서 `docs/02-design/features/graph-consumption.design.md`가 있고 독립 검증과 사용자 승인을 받았다.
* N3.10 상위·관련 문서 개정이 승인됐다.
* 그 card가 읽는 결정이 닫혀 있다. GC-2·GC-3·GC-8은 U-G12(범위 확장 착수 승인)도 닫혀 있어야 한다.
* **cProfile 기준선(WP-10, v0.11)**: 그 card의 base에서 검증자가 13회로 실행의 cProfile과, 블록별 계산 수, **블록 밖 함수를 포함한** 같은 인자 반복 호출 계수를 재어 기준선으로 기록했다(상위 WP-10, 사용자 결정 O-33 (1)의 '착수 전 블록별 cProfile 기준선' 관행). 완료 조건 9의 계측은 이 기준선과 비교한다. LUT가 필요해서 card 0(N6) 범위 밖이고, 엔진 card마다 그 base에서 잰다.

| card | 범위 | 선행 | 읽는 결정 |
|---|---|---|---|
| GC-0a (검증자, 측정) | N6의 K-3 무관 측정(M-G2·M-G3 예비·M-G3c·M-G4·M-G5·M-G6·M-G9). 엔진 무변경 | 이 계획 승인 | -- |
| GC-0b (검증자, 측정) | N6의 K-3 뒤 측정(M-G1·M-G1b·M-G7). 엔진 무변경 | 이 계획 승인, K-3 구현 card 병합 | -- |
| GC-D (문서) | 상위·관련 문서 개정(N3.10) → 독립 검증·승인 → design(GD-1~GD-11, test 목록, 배선표, 파일 분할) | GC-0a(GC-0b 결과가 필요한 design 항목은 GC-0b 뒤) | X-G1·X-G4~X-G11, U-G1~U-G13 |
| GC-1 (test 역할 + 검증자 기준선) | 규칙 L-1~L-5 구현(규칙 L 전용 별도 파일, GD-9), 거부 픽스처(거부 먼저, L-5는 F-G13 7자리 전부), 초기 출력 전용 목록(F-G3 정상 8개), 부채 목록(layout 동작점 사본 항목 포함, card LI-1 -- O-27, 규칙 L-5 '동작점 사본' 개념), 검증자의 기준선 재측정(M-G3, 규칙 L 코드가 아닌 독립 측정 스크립트로), GD-1 진입점·출력 함수 목록의 검증자 독립 재측정(N3.1-2)과 기준선·규칙 매개변수 지문 기록. 엔진 운영 코드 무변경 | GC-D | U-G6 |
| GC-2 (엔진, KVL) | 순서대로: (1) `gvgs_self_edge` 정지 이전(거부 먼저), (2) `parallel_vgs`의 `gs_groups` 읽기, (3) 숲 회계 불변량 S0 검사(거부 먼저), (4) 봉인 8 처리(U-G9), (5) `rel_kvl_branch`·`gvgs_summary`·`gvgs_cycles.py`와 그 등록 삭제(F-G35), (6) CONTRACT·graph test 표 갱신(test 역할). 트리 경로가 필요한 곳은 쓰기 계획 블록의 넷별 뿌리 경로 필드를 읽는다. HC-1이 쓰기 계획 블록의 두 필드(넷별 뿌리 경로 필드와 Gs⁺ VGS 변 필드) 없이 병합됐으면 GC-2가 (1) 앞에서 쓰기 계획 블록에 두 필드를 더한다(N3.3-3, 소비자 배선과 같은 변경). 옮긴 정지 블록이 rule_hash 대상 파일이면 rule_hash 재기록(Role: data) | GC-1, headroom-chain HC-1 병합, **K-3 구현 card 병합** | U-G1·U-G3·U-G9·U-G11·U-G12 |
| GC-3 (엔진, KCL 보조) | `node.terminals` 결선 점검 S0 검사(거부 먼저), `rel_kcl_group` 삭제 | GC-1 | U-G3·U-G12 |
| GC-5 (엔진, 출발 전류) | 충돌 표지(꺼지지 않음), 기저 경유 자리값, 사다리 칸 단위 처리, 아래 끝이 전류 충돌일 때의 칸 0 고르기(U-G13 결정대로), 모든 후보 충돌 시 빈 사다리(`_report` 빈 사다리 처리, 원인과 다른 면적 충돌 기록 제거, `start_intervals.py:264` 조기 반환과 출력 정렬, GD-7), 1회차 전류 충돌의 네 함수·여섯 호출 자리 처리(`gain_l_bounds`의 '이득 목표 미달' 오기록, `area_bounds`의 무기록 건너뜀, `matching_bounds`의 `SRC_MATCH_L` 사유 누락 포함, N3.6-3), 면적 충돌 기록 형식(GD-7), 착수 측정 M-G8, `bracket_root` 뒤 같은 점 재풀이 금지(블록 안 local memo, NFR-G4, O-15 (E)) | GC-1, headroom-chain HC-1 병합, GC-9 병합(파일 겹침 순서 GC-9 → GC-5 → FX-1, gain-budget N6.1 -- N7.2). **완료 판정 선행**: gain-budget card EO-1(SPICE 다리를 채우는 데 필요, 사용자 결정 O-44 (1), gain-budget `6ab294c9` N6.3 1232행 (iii)·N6.20). EO-1 전 병합은 N6.3 (iv) (가)대로만 -- 판정 기록에 다리 '보류(채울 card = EO-1)'가 있을 때만, 병합해도 미완료. (결정 6은 `c8d156e3`으로 이미 병합돼 충족, BD-13) | U-G8·U-G13 |
| GC-6 (엔진, 정본 술어) | R1·R1′·R1″·R2 교체, rule_hash 재기록(Role: data) | GC-1, M-G5 | U-G11 |
| GC-7 (엔진, 필드 정리) | N3.2 표의 GC-7 항목: 출력 전용 선언, `column_orphans` review 배선, 블랭킷 READS 정리, 동적 접근의 정적 해석 형태 전환, `coupling_vars`·`l_classes`의 `gs_groups` 읽기, R3 처리(U-G4 (가) + O-15 (A): LUT memo 파생 `conduction_mask(kind, w_key)` 신설, `cell_floor`·`edge_costs`가 읽음, VGS = 0 마디 찾기 한 곳, `sctx.cell_floors` 캐시 제거 -- 같은 캐시를 쓰던 `_peak_floor`도 LUT memo 파생 함수로, `dc_conduction_floor` 출력 전용 선언), 승인된 삭제(V9 개정 뒤), 하위 칸 처리, rule_hash 재기록(Role: data). **변경 종류는 부분별**(N4-0): `conduction_mask` 통일 = 동작 변경, 나머지(출력 전용 선언·`gs_groups` 읽기·블랭킷 READS·정적 형태 전환·`sctx.cell_floors` 제거·승인된 삭제) = 순수 리팩터링 | GC-1. **완료 판정 선행**(동작 변경 부분 `conduction_mask` 통일만): gain-budget card EO-1(SPICE 다리, O-44 (1), gain-budget `6ab294c9` N6.3 1232행 (iii)). EO-1 전 병합은 N6.3 (iv) (가)대로만(판정 기록에 '보류(채울 card = EO-1)', 그 부분 미완료) | U-G3·U-G4·U-G11 |
| GC-8 (엔진, R4 -- 위쪽 방향 VDS 변 정본 읽기) | O-15 (C)·O-16 (3)과 headroom-chain v0.7.4(`752659ee`)·v0.7.5 최종(`c0d96517`)·v0.7.6(브랜치 `plan/headroom-v076` `aa6e064c`) N3.4·F-23·완료 조건 12로 범위가 정해졌다. 정본은 R-1′ 제약 그래프 S0 필드의 변 목록(소자, 위쪽 방향, 항 종류)이다. 배선 분담은 `iv_headroom` = HC-1, `headroom_bound`·`order_terms` = GC-8이다. **`ls_swing`은 GC-8 범위에서 뺀다**(v0.11, 사용자 결정 O-26 (1) -- `ls_swing` 자체 제약계·VGS 휴리스틱을 지우고 스윙·ICMR을 DC 동작 범위로 옮긴다. 삭제는 gain-budget 계획 v6.19(브랜치 `plan/gb-v619` `6ab294c9`, 승인 전) card DE-1(N6.8) 소관). GC-8이 DE-1보다 먼저 병합돼도 `ls_swing`은 배선하지 않는다(지울 코드에 배선하지 않는다). GC-8 범위: (1) 소비자 둘 배선 -- `headroom_bound`(`E/metrics/headroom_bound.py:58-96`), `order_terms`(`E/sizing/block_columns.py:172-177`)가 VDS 변의 방향·변 목록·항 종류를 R-1′ 정본 필드에서 읽는다. `headroom_bound._edges`의 VGS 절반은 쓰기 계획 블록의 **Gs⁺ VGS 변 필드**(변 목록·방향)를 읽는다(headroom-chain v0.7.5 완료 조건 12가 GC-8에 넘김). (2) 정책 통일 -- headroom-chain N3.4 소비자별 처리 표대로 같은 개념은 하나로 맞춘다. **선언 triode**(사용자 결정 O-33 (9)): DC 범위 정의(스윙·ICMR 등)에서는 선언 triode 소자를 포화 조건에서 뺀다. R-1′의 선언 triode 항(LUT on_mask VDS 하한)은 포화 조건이 아니라 **'LUT 정의역 하한 항'이라는 다른 개념·다른 이름**이다(LUT가 그 VDS 아래 동작점을 표현하지 못한다는 데이터 사실). GC-8 소비자는 이 둘을 섞지 않는다. **`headroom_bound`의 규칙**(headroom-chain v0.7.6 `plan/headroom-v076` `aa6e064c` N3.4 338행, 오케스트레이터 기본안 -- O-33 범위): `headroom_bound`는 **정의 값(VDS ≥ VDSAT)의 상한 인증**이다. tol은 엔진 판정 여유(O-33 (8))라 VDS 변 비용에 넣지 않는다(tol ≥ 0이라 빼도 비용이 줄 뿐이어서 상한은 유지된다). 선언 triode 변은 **비용 0 방향 변**(VDS ≥ 0, 위쪽 방향)으로 둔다 -- 변을 빼지 않고 방향을 남겨 `order_terms`의 방향 변과 같은 개념 하나로 둔다. 'LUT 정의역 하한 항'은 DC 범위 개념이 아니라 `headroom_bound`에서 쓰지 않는다. **design 넘김**: 비용 0 방향 변 때문에 레일에서 닿지 않는 넷이 생기면(as-built `STATUS_UNKNOWN` 창) `iv_headroom` 예산이 빠지는 처리를 design이 정한다. 대체값은 금지다. **전도 집합**(오케스트레이터 기본안 -- 같은 개념을 쓸 수 있는 정보로 평가한다. headroom-chain 334·335행 문언과 맞춘다):<br>• θ가 있는 소비자(R-1′)는 θ에서의 전도로 비전도 소자의 변을 뺀다(`ls_swing`은 v0.11에서 GC-8 범위 밖).<br>• θ가 없는 소비자(`headroom_bound` 크기 전, `order_terms` θ 무관, `iv_headroom` -- 출발 구간 1단계 `headroom_bounds`(`E/search/iv_headroom.py:152-175`)는 소자 전류(`E/search/start_intervals.py:99-119`)보다 앞이다): 구조적 전도로 평가한다. 근거: 전도 MOS의 자기 맞바꿈(구조적 0 전류)은 graph가 정지시키고(`E/graph/s1_symmetry.py:16-18`), KCL상 항상 0인 MOS는 전류 기저가 정지시키며(`E/sizing/current_basis.py:13-14`), 대칭·KCL이 0으로 정하는 구조적 0 전류 가지는 search `zeros`로 θ에서 빠진다(`E/search/CONTRACT.md:590-591`). 그래서 남은 MOS는 구조적으로 전도할 수 있는 소자이고, 구조적 0 전류로 확정된 MOS가 없으면 제외는 없다. 구조적 0으로 확정된 MOS가 있으면 그것만 뺀다(headroom-chain v0.7.6 `aa6e064c` 344-346행과 같은 문장).<br>• **구조적 0 전류 MOS 집합의 정본**(오케스트레이터 기본안 -- 같은 개념 하나): `zeros`는 search 값이다(`E/search/current_symmetry.py:110-131`, `E/search/search_domain.py:166`). 그 값은 `graph/kernel: search_domain` 필드의 칸 `SearchDomain.zeros`(`E/search/search_values.py:92`)에 있지만, 그 필드의 writer는 search 층(6)이고(`E/search/s0_fields.py:20, :27`, `E/search/search_domain.py:166, :173`), 소비자 `order_terms`(sizing 층 4)·`headroom_bound`(metrics 층 5)는 아래 층이다. 아래 층이 위 층 필드를 읽으면 데이터 흐름이 역전된다(층 규칙 '작은 번호 쪽으로만', `E/tests/structure/structure_checks.py:24-30`). 그래서 **`zeros`만이 아니라 전류 대칭 결과 전체(`ties`·`negated`·`zeros` -- `E/search/current_symmetry.py:75-131`의 한 번의 유리수 기약 행사다리꼴 결과)를 sizing 층 이하의 S0 graph 필드 하나로 올린다**(`dc_current_basis` 쪽, 이름·위치는 design). 그 writer의 입력은 graph `orbits`·`current_symmetry` 생성자·`dc_colour`, 전류 기저 행, 그리고 spec `search.untie_orbits`다(`current_symmetry.py:15, :40-51`). `search_domain`은 그 필드를 읽기만 하고 자체 계산(`search_domain.py:166` 부근)을 지운다. **이 필드를 만드는 card는 HC-1이다**: θ가 없는 구조적 전도 소비자인 `iv_headroom`(HC-1이 배선)이 처음 읽기 때문이다. HC-1이 이 필드 없이 병합되면 GC-8이 만든다. `order_terms`·`headroom_bound`(GC-8)는 그 뒤에 읽는다. 필드의 writer는 만든 card가 둔 블록 하나이고 뒤 card는 읽기만 한다(headroom-chain v0.7.6 `aa6e064c` 347행 '이 필드는 HC-1이 만들고, 못 하면 GC-8이 만든다'와 같은 문언).<br>• 근거: '전도'는 같은 개념이고, 소비자마다 알 수 있는 정보(θ 유무)가 다를 뿐이다. θ 없는 소비자에게 θ 전도를 요구하면 그 값이 없다.<br>(3) 사본 삭제 -- 각자의 방향 계산(`_edges`의 VDS 부분, `_edges`의 VGS 변 목록·방향, `order_terms`의 방향 계산)을 지운다(`ls_swing._constraints`는 DE-1이 지운다)(`iv_headroom._edge_nets`는 HC-1이 지운다). (4) '다른 이름의 다른 개념' **두 가지**(VDS 변 격자 하한 비용, VGS 변 격자 하한 비용)는 headroom-chain N3.4 표가 정본이고, GC-8은 그 정의대로 이름을 붙인다. v0.7.6(`aa6e064c`)에서 'VDS 변 격자 하한 비용'의 정의는 포화일 수 있는 격자점의 VDSAT 최솟값으로 바뀌었다(tol 제외, as-built 'VDSAT 최솟값 + tol 최솟값'에서 변경). 포화 항 변에만 쓰고 선언 triode 변의 비용은 0이다. v0.10 첫 판의 '신호 고정 VGS 변'은 headroom-chain v0.7.5가 철회했다. `ls_swing`의 VGS 등식 변(VGS 휴리스틱)은 O-26 (1)로 DE-1이 `ls_swing` 자체 제약계와 함께 지우므로 이 계획의 질문이 아니다. 'VDS 변 격자 하한 비용' 이름 부여 대상에는 `edge_costs.vds_min_v`의 다른 소비자 셋도 든다: `E/search/start_intervals.py:280`, `E/search/_helpers_curves.py:111`, `E/lut/derived_fns.py:106`. **`order_terms`는 v0.10 이전 이 계획의 R4 범위(`headroom_bound`·`ls_swing`)에 없었고 O-15 (C)로 들어왔다. `ls_swing`은 v0.11에서 빠졌다(O-26 (1), DE-1).** 이 card는 `headroom_bound`·`order_terms`의 결과를 바꿀 수 있다(선언 triode·전도 규칙 통일). 그래서 동작 변경 card(N4-0)이고, 바뀐 회로·값은 검증자가 변화표로 기록한다(IT-Q3 (가) 준용). 완료 조건은 headroom-chain 완료 조건 12의 GC-8 몫이다: 같은 개념에 소비자별로 다른 규칙이 남은 곳 0(검증자 확인) | GC-1, headroom-chain HC-1 병합(정본 필드를 만드는 card) ← 그 앞의 HC-S 병합(포화 기준 정본 함수 `sat_threshold`와 봉인 7이 쓰는 `device.dc_sat_v`, `_vds_floor` 이동). 순서: HC-S → HC-1 → GC-8. **완료 판정 선행**: gain-budget card EO-1(SPICE 다리, O-44 (1), gain-budget `6ab294c9` N6.3 1232행 (iii)). EO-1 전 병합은 N6.3 (iv) (가)대로만(판정 기록에 '보류(채울 card = EO-1)', 미완료) | U-G12, O-15 (C), O-16 (3) |
| GC-9 (엔진, 기저·LUT 파생 단일화 -- 원칙 감사 O-15 (E)) | (1) 기저 행 float 변환을 컨텍스트에서 1회로(`start_intervals.py:100`, `iv_currents.py:120`, F-G37). (2) 정확(유리수) MOS 전류 평가 공용 함수 하나로 `theta_check.py:45-50`·`block_currents.py:31`·`cone_rows.py:16-24`를 바꾼다. (3) `theta_schema.current_cone` 소비자(`theta_check`·`cone_rows`·`fd_jacobian`·`gate_run`·`layer0_center`·`search_domain`)가 `dc_current_basis` MOS 행을 읽게 하고, 사본 필드 `current_cone`의 삭제는 U-G3과 같은 절차(항목별 사용자 승인, 대조 일치 확인 뒤)로 한다. `_vds_floor`의 `lut.derived` 이동은 이 card가 아니다 -- 'LUT 정의역 하한 항'(O-33 (9))으로 HC-1(search)이 먼저 쓰므로 headroom-chain HC-S가 한다(F-G38, 오케스트레이터 기본안). 순수 리팩터링 card(N4-0)라 결과는 base와 필드별로 같아야 한다(이산 정확, 연속 분해능 이내) | GC-1, headroom-chain HC-S·HC-1 병합(`start_intervals.py`·`iv_currents.py` 겹침, `_vds_floor` 이동), XRUN-F1 card C와 파일 겹침 확인 | O-15 (E), U-G3(삭제 절차) |
| GC-V (검증자) | 완료 조건 판정, 13회로 변경 종류별 판정(N4-0 -- 결정성, 리팩터링 필드별 비교, 동작 변경 값 변화표), 부채 목록 재계수와 지문 대조, 항목 제거 확인, gap 분석 | 각 엔진 card | -- |

(GC-4 번호는 비웠다. v0.2의 MNA card는 백로그 B-G1로 내렸다.)

### N7.2 다른 계획과의 순서

* **K-3 구현 card = 상위 card IT-1**(design 41 §6.7-1a, 상위 N6.5, card 정의 master `f2852c36`에 병합됨(구현은 아직), red test는 `E/tests/sizing/test_writer_plan.py` 안 새 test 함수 -- 상위 X-IT3, F-G19):
  * K-3은 결정 6(d/s 맞바꿈) 다음이다(사용자 결정 K-3). 이 순서 조건은 이미 충족됐다(결정 6 = `c8d156e3`, HEAD 조상, F-G36, headroom-chain v0.7.1 490행). 상위 계획 v6.16(card IT-1 정의)은 승인·병합됐으므로(master `f2852c36`, O-14 (2)) IT-1을 막는 것은 착수뿐이다. GC-2·GC-0b는 K-3 card 뒤다. 근거: 둘 다 `E/sizing/writer_plan.py`를 고치고, GC-2의 숲 불변량·KVL 정본 정의가 '같은 DC 변 없는 Gs⁺'를 전제한다.
  * card id는 IT-1로 부여됐다(상위 계획 v6.16, master `f2852c36` 병합). N3.10의 card id 부여 항목은 그것으로 닫힌다.
* **순서의 정본과 동작 변경 card 병합 원칙**(전체 정합 검증 B-M4): 같은 파일을 고치는 card가 겹친다 -- FX-1·GC-5·GC-9가 `E/search/start_intervals.py`·`E/search/iv_currents.py`를, GC-9·LA-1이 `E/search/layer0_center.py`·`E/search/fd_jacobian.py`를 고친다. card 사이 순서는 **gain-budget 계획 N6.1(유일한 순서 정본)** 이 정하고, 이 계획은 그것을 따른다(이 절의 순서 문장은 그 표와 다르면 그 표가 이긴다). 원칙: **동작 변경 card끼리는 따로 병합한다** -- 같은 출발 기록·같은 13회로 결과에서 두 card의 변화를 섞으면 검증자 변화표에서 원인을 나눌 수 없기 때문이다(O-34 동작 변경 판정은 '원인 미설명 변화 0'). 순수 리팩터링 card(GC-9 등)는 필드별 비교가 끝난 뒤 동작 변경 card와 순서만 맞추면 된다. **확정 순서**(gain-budget v6.19 `plan/gb-v619` `6ab294c9` N6.1 1147행 'card 사이 파일 겹침 순서', FX-1 행 1134행·LA-1 행 1139행): `start_intervals.py`·`iv_currents.py`는 **GC-9 → GC-5 → FX-1**(정본 데이터 먼저, 그 위의 출발 논리, 그 위의 재조회), `layer0_center.py`·`fd_jacobian.py`는 **GC-9 → LA-1**(LA-1이 `dc_current_basis` 정본 위에서 층 0 경로를 다시 쓴다). 이 계획의 card 내부 의존과 충돌하지 않는다: GC-9의 선행(GC-1, headroom-chain HC-S·HC-1, card C)과 GC-5의 선행(GC-1, HC-1)은 서로를 요구하지 않으므로 GC-9를 GC-5 앞에 두어도 된다. GC-5는 GC-9가 만든 기저 float 행·정확 전류 함수 위에서 출발 전류를 기저 경유로 다시 쓴다.
* **gain-budget card LA-1(층 0 손계산 조립, v6.19 N6.14, 사용자 결정 O-33 (1)·O-43 D2)**: 새 층 0은 국소 봉인 후보·조립점·수리점에 R-1′ 관계식 거르기(사용자 결정 H-B)를 쓰고, 상자 중심·Halton·사다리는 **층 0 무동작 회로와 층 0 조립 실패 경로(LA-Q2 (b))의 출발 경로**에만 남는다(O-43 D2, gain-budget v6.19 `6ab294c9` LA-1 범위 6·DEC-73 (3)(b), headroom-chain `a2ae9df6`). GC-5의 처리(빈 사다리 처리, 상자 중심 출발 -- N3.6-3, 완료 조건 6)는 그 경로에서 그대로 유지된다. LA-1이 그 경로의 코드(`E/search/layer0_center.py` 사다리 순회)를 줄이거나 옮기면 GC-5의 빈 사다리 처리는 LA-1이 남긴 출발 경로에 붙는다. LA-1은 `size_and_seal_local` 배선 대기 부채 항목의 card다(O-36, N3.2 표).
* **결정 6(d/s 맞바꿈)**: K-j의 성립 조건이다. 이미 병합됐으므로(`c8d156e3`, 상위 U-62 닫힘, F-G36) GC-5의 선행은 충족됐다(BD-13).
* **headroom-chain**(v0.7.6 -- 브랜치 `plan/headroom-v076` `aa6e064c`, card HC-S → HC-1 순서):
  * HC-S(포화 기준 정본 함수 `sat_threshold`, 봉인 7의 `device.dc_sat_v`, `_vds_floor`의 `lut.derived` 이동 -- 오케스트레이터 기본안)는 HC-1 앞이다. GC-8은 HC-1 뒤이고, 따라서 HC-S 뒤다. GC-9는 `_vds_floor` 이동을 HC-S에 맡긴다.
  * HC-1이 `gvgs_summary.vds_saturation`을 지우고 S0 제약 그래프를 만든다(그 계획 FR-H9·X-6). GC-2는 HC-1 뒤에 병합해 나머지 칸과 모듈을 지운다(기본안 BD-6). 근거: 승인된 계획의 삭제 소유를 존중하고, 같은 파일(`gvgs_cycles.py`, graph test 표)의 겹침을 피한다.
  * HC-1의 제약 그래프(κ_n)는 쓰기 계획 블록의 넷별 뿌리 경로 필드를 읽는다(O-14 (1) (가′)). v0.7.1 317행의 '경로 목록은 저장하지 않는다'는 O-14 (1)로 개정 대상이고 그 계획 소관이다. HC-1은 IT-1 뒤 쓰기 계획을 처음 고치는 소비자 card라 그 필드를 만드는 card다(기본안, N3.3-3). HC-1이 만들지 않고 병합되면 GC-2가 만든다. 오케스트레이터가 HC-D design 브리핑에 알린다.
  * v0.7.1의 Gs⁺는 이미 K-3 뒤 기준이다(성분마다 뿌리·오프셋 하나, 나머지 포트는 MOS writer). 이 계획 N0.1·N3.3-1도 같은 정의를 쓴다. 이 정의는 O-13 (1)의 '포트 경로가 둘 이상이면 ΔV를 소거한 KVL 하나가 남는다'와 맞는다: 나머지 포트를 쓰는 트리 경로 밖의 포트 경로가 비트리 MOS 변으로 그 KVL을 닫는다. headroom-chain N0.1·155행의 v1 문언 정정은 O-13 (1)이 그 계획에 지시한 것이고 이 계획이 고치지 않는다.
  * GC-1이 HC-1보다 먼저 병합되면 HC-1의 새 필드도 규칙 L을 통과해야 한다(만들면 배선). 오케스트레이터가 HC-1 브리핑에 알린다.
  * GC-5는 HC-1 뒤다(같은 `start_intervals.py`).
* **XRUN-F1**: card C는 search 층을 고친다. GC-5는 HC-1을 거쳐 그 뒤다. GC-2·GC-3·GC-6·GC-7은 graph·sizing·metrics 층이라 card C와 파일이 겹치지 않는다. GC-9는 search 층(`start_intervals.py`·`iv_currents.py`·`cone_rows.py`·`fd_jacobian.py`·`gate_run.py`·`layer0_center.py`·`search_domain.py`)을 고치므로 card C와 HC-1 뒤에 병합한다. 블록을 지우면 블록 결과 색인의 대상도 줄 뿐 키 규칙은 그대로다(X-20·X-21). card B의 data 역할이 재기록한 `structure.json` rule_hash는 GC-6·GC-7(그리고 경우에 따라 GC-2)이 다시 바꾼다(U-G11).
* **LT-1**(옛 엔진·태그 삭제): `E/tests/structure/structure_checks.py`를 고친다. 규칙 L 코드는 그 파일과 다른 별도 파일에 두므로(GD-9) 규칙 L 지문은 LT-1의 수정에 영향받지 않는다. 그래도 두 card가 같은 디렉터리의 등록 자리를 고치면 늦게 병합하는 쪽이 rebase한다.
* **oracle-portability / U16**: 독립 검증 경로(forced·free)의 입력은 오라클 입력 생성기(U16 -- 지금은 gain-budget card EO-1로 앞당겨짐, OP-0 입력 스키마)다. `dc_off_current`는 EO-1~OP-5 사이에만 oracle이 소비하고(옛 ε = 1 판정), O-46 (2)로 OP-5 병합 뒤 소비자 0이라 그때 출력 전용으로 선언한다(N3.2 표). U16 완료 조건 변경은 N3.10 개정 항목이다.
* **offset-strategy F-1 fixture**: GC-5가 출발값을 바꾸면 fixture 결과도 바뀔 수 있다. 병합 시점이 겹치면 오케스트레이터가 알린다.
* **상위 단위 8·U16·U17 ②**: 부채 목록 '배선 대기' 항목의 card다. 그 card의 완료 조건에 '해당 부채 항목 0'을 더하는 것은 N3.10 개정 항목이다.

### N7.3 완료 조건(기능 전체, 측정 가능)

1. **규칙 L**: 규칙 L-1~L-5 test가 green이다. 거부 픽스처로 각 규칙이 실제로 거부함을 먼저 보인다(정적 해석 실패·도달 불가 = 위반 포함). 규칙 L-5는 F-G13 7자리가 모두 기준선에 들어감을 자리별로 보인다.
2. **부채 목록**: 항목 키 집합 ⊆ 기준선 집합, 기준선·규칙 매개변수 지문 = GC-1 판정 기록의 지문, 낡은 항목 0, 지워진 항목마다 대상 코드 변경을 검증자가 확인, 모든 항목에 card id(결정·백로그 id 0). 이 계획 소유 card id(GC-0a~GC-7, GC-9) 항목은 0이다. 이 계획 소유 GC-8 항목도 0이다. 남은 항목은 다른 card(단위 8, U16, U17 ②, HC-1, layout 동작점 사본의 LI-1 -- O-27, `size_and_seal_local` 배선 대기의 LA-1) id뿐이다.
3. **KVL 정본**: `rel_kvl_branch`·`gvgs_summary`·`s1_gvgs`·`gvgs_cycles` 참조 grep 0(등록 자리 포함, GC-2 뒤). `gvgs_self_edge` 정지가 옮겨진 자리에서 거부 픽스처를 거부하고, 13회로 정지 회로 집합이 base와 같다. 숲 회계 불변량 검사가 조작 픽스처(`dc_coord` 누락, 분류 뒤바꿈)를 거부하고 13회로에서 통과한다. 쓰기 계획 안 (kind, gate, source) 키 재유도 0이고, 종속 분류(이산 값)는 base(K-3 병합 master)와 정확히 같다(순수 리팩터링, N4-0). 넷별 뿌리 경로 필드는 하나이고 writer는 쓰기 계획 블록이며, 소비자 셋 중 병합된 것은 그 필드를 읽는다(규칙 L-1 green). **부모 포인터를 두 단계 이상 따라가는 경로 재구성 코드는 쓰기 계획 블록 안 하나뿐이다**(O-15 (E)로 좁힘). 한 단계 읽기(아는 쪽 노드 값 읽기, F-G39)는 경로 재구성이 아니라 대상이 아니다. 이 단일성은 **검증자 확인 항목**이다(GC-V): 검증자가 `NodeWrite.known`을 반복해 따라가는 코드 자리(반복문·재귀 안의 `.known` 갱신)를 엔진 전체(tests 제외)에서 직접 찾아, 쓰기 계획 블록 안의 그 자리 하나뿐임을 판정 기록에 적는다(작성자 보고를 증거로 받지 않는다).
4. **KCL·독립 검증**: 결선 점검이 원소 색인을 조작한 기저 픽스처를 거부함을 먼저 보이고, 13회로 통과를 본다. `rel_kcl_group`(승인 시) 참조 grep 0. U16 완료 조건 개정(N3.10)이 상위 계획에 반영돼 있다(GC-V가 확인).
5. **MNA**: MNA 코드 변경 0.
6. **출발 전류**: 0 이하 전류의 조용한 대체가 0이다(충돌 기록으로 보인다). 충돌 표지가 `use_macro` 해제·예산 없음 픽스처에서도 서 있음을 먼저 보인다. 모든 후보가 충돌인 픽스처에서 사다리가 비고 `_report`가 오류 없이 칸 0 성분 전부를 `uncovered`로 내며, 원인과 다른 면적 충돌이 없고, 층 0이 상자 중심에서 출발함을 보인다. 아래 끝이 전류 충돌인 세 픽스처((a) 최상 칸이 면적·매크로로만 실행 불가, (b) 최상·아래 끝 모두 충돌이고 중간만 충돌 없음, (c) 모두 충돌)에서 U-G13 결정대로 칸 0이 골라짐(또는 빈 사다리)을 보인다. (가-1)이면 (ii) 점의 원인별 픽스처도 보인다. (ii) 점이 매크로 실패만으로 실행 불가인 경우에는 `use_macro`가 꺼지고, t_p를 담은 매크로 충돌이 기록되고, 면적만으로 (i)이 다시 적용된다. 면적 초과만인 경우와 둘 다인 경우에는 원인마다 t를 담은 충돌이 기록된다. 전류 충돌인 아래 끝의 `macro_failed`로는 `use_macro`가 꺼지지 않는다. 1회차 전류 충돌 픽스처에서 **네 함수, 여섯 호출 자리**(`gain_l_bounds` 292행, `matching_bounds` 295·332행, `area_bounds` 296·327행, `noise_bounds` 333행) 각각이 자리값 없이 전류 충돌 사유로 비활성 처리하고 충돌을 기록함을 여섯 자리마다 보인다(`gain_l_bounds`는 '이득 목표 미달' 충돌·최대 앵커 L 하한이 없어야 한다). 출발 전류가 기저 행을 정확히(유리수 계산) 만족한다. 사다리 아래 칸마다 충돌 판정이 있다. GC-5는 동작 변경 card(N4-0)라 비트 동일을 요구하지 않는다: 자리값과 충돌이 없는 회로의 출발 기록 변화는 0이어야 하고(원인 없는 변화 0), 바뀐 칸은 모두 검증자 변화표에 원인이 있어야 한다(`start_intervals.py:264` 조기 반환 회로의 `uncovered` 변화는 원인 'GD-7 정렬', N4-4·M-G8). 충돌 칸 처리는 U-G13 결정대로다. 빈 사다리 처리와 상자 중심 출발은 gain-budget LA-1 뒤에도 층 0 무동작 회로와 층 0 조립 실패 경로(LA-Q2 (b))의 출발 경로에서 유지된다(O-43 D2, gain-budget `6ab294c9` LA-1 범위 6·DEC-73 (3)(b), N7.2). GC-5의 SPICE oracle 다리는 시작점의 ngspice 판정(DEC-98 A' 기준)이다(gain-budget `6ab294c9` N6.3 1232행 (iii), N4-0). EO-1은 완료 판정 선행이다: EO-1 전이면 이 다리는 '보류(채울 card = EO-1)'이고, 병합은 N6.3 (iv) (가)대로 판정 기록에 그 보류가 적혀 있을 때만이며 병합해도 GC-5는 미완료다. EO-1 뒤라도 OP-5 병합 전이면 판정 기록에 '꺼짐 정의 판'을 적고 옛 식(ε = 1) 판정 다리는 '보류(채울 card = OP-5)'다(gain-budget `6ab294c9` N6.3 1232행, 3차 감사 N5). 완료 기록에 변경 종류(동작 변경)와 다리 상태(어휘는 '보류'·'대상 없음' 둘뿐 -- 채워진 다리는 판정 결과로 적는다)를 적는다.
7. **변경 종류별 판정(N4-0, O-34)**: 모든 card에서 결정성(두 번 실행 비트 동일)이 성립한다. 순수 리팩터링 card(GC-2·GC-3·GC-6·GC-9와 GC-7의 리팩터링 부분) 뒤 13회로 결과가 base와 필드별 비교(이산 정확, 연속 분해능 이내)로 같다. 동작 변경 card(GC-5·GC-8과 GC-7의 `conduction_mask` 통일 부분)는 정의 오라클 toy·봉인 불변식·SPICE oracle 대조를 통과하고 검증자 변화표의 원인 미설명 변화가 0이다. 비교에서 빼는 칸은 검증자가 소유하고 판정 기준 변경으로 보고한다.
8. **이름·상수**: 새로 쓰거나 고친 코드에 회로·소자·넷 이름 리터럴 0, 새 수치 상수 0(규칙 D·E).
9. **재사용**: 결과 JSON `perf`에서 같은 입력 재계산 0(상위 G-10). 새 θ 무관 검사와 넷별 뿌리 경로 필드의 계산 수 = 실행당 1. S1 블록 계산 수는 base 이하다. **WP-10 계측**(상위 WP-10 315행, 사용자 결정 O-14 (1)): 검증자가 13회로 실행의 cProfile과, **블록 밖 함수를 포함한** 같은 인자 반복 호출 계수를 재어 이 계획이 고친·더한 함수의 같은 인자 반복 호출이 0임을, 착수 전 기준선(N7.1 공통 착수 조건)과 비교해 판정 기록에 적는다(블록 결과 색인 계수만으로는 블록 밖 함수의 반복을 못 본다).
10. **배선**: 새 검사·함수가 실제 경로에서 호출된다(규칙 L-1이 이 계획의 새 것에도 green).
11. **rule_hash**: rule_hash 대상 파일을 고친 card는 U-G11 결정대로 `structure.json` 재기록이 같은 card에서 끝나 있고, stale 0이다.
12. **gap·bkit**: 상위 N6.3 확인(규칙 L 계수 포함)과 design 대 구현 gap 분석을 통과한다.
13. **원칙 감사 항목(O-15 (A)·(E))**:
   * 칸별 전도 마스크와 gm/ID 정점(분지) 마디를 계산하는 코드는 LUT memo 파생 함수 각 한 곳이다(`cell_floor`·`edge_costs`의 자체 계산 0). `sctx.cell_floors` 참조는 0이다.
   * 격자 VGS = 0 마디 찾기는 `conduction_mask` 모듈의 한 함수다. `cell_floor`·`edge_costs`·`current_box` 셋 다 그 함수를 부르고, 자체 찾기는 0이다. `current_box`의 I_off 값(θ 전류 상자 하한)은 다른 개념이라 이 항목의 단일화 대상이 아니다(원칙 감사 '준수').
   * **예외(O-16 (3) 표시 보완)**: 봉인 9의 소자별 I_off 동작점 보간(`E/sizing/seal_conduction.py:26-31` `_off_current`)은 검증 경로(판정 권한)라 이 단일화 대상에서 뺀다.
   * 기저 행 float 변환은 실행당 1회, 정확 MOS 전류 평가 함수는 하나다. `current_cone` 소비자는 기저 MOS 행을 읽는다(사본 삭제는 승인된 경우).
   * 이 항목의 결과 판정은 N4-0 부분별 표시를 따른다: GC-7의 `conduction_mask` 통일은 동작 변경 기준(검증자 변화표의 원인 미설명 변화 0), GC-7의 `sctx.cell_floors` 제거와 GC-9 전체(기저 float 1회, 정확 전류 함수, `current_cone` 기저 읽기)는 순수 리팩터링 기준(필드별)이다. `_vds_floor` 이동은 headroom-chain HC-S 소관이라 이 항목에 없다.

---

## N8. 원문 근거표

| R | 원문 | 웹 | 로컬 | 쪽·위치 | 쓰는 곳 |
|---|---|---|---|---|---|
| R1 | 사용자 결정 O-10·P-1·B2·K-3·X-22, 사용자 원문 2026-10-16(KK-1) | -- | `wt/_drafts/user_decisions.md` 225·243·619·628·629행 | -- | N1.1, N2 |
| R2 | 필드 소비자 조사(정적) | -- | `wt/_scratch_deadfields/deadfields_report.md`, 스크립트 `decls.py`·`consumers.py`·`classify.py`·`attrs.py`·`attrs2.py` | §1·§3·§3b·§4·§5 | F-G1~F-G3, F-G13, F-G15~F-G17, N3.1. 수치는 계획 작성 때 재측정(history H2) |
| R3 | KVL·KCL 관계 조사 | -- | `wt/_scratch_kvlkcl/kvlkcl_findings.md`, `s1_counts.jsonl` | 항목 1~5 | F-G4~F-G12. 코드 줄은 이 worktree에서 다시 읽음 |
| R4 | KCL 계수 | -- | `wt/_scratch_kcl/kcl_count.jsonl` | 회로별 행 | N4 머리(기저 단계 정지 회로) |
| R5 | 역할 agent 절차 | -- | `agents/gmid-code-author.md`, `agents/gmid-verification-auditor.md`(커밋 `3ddb27c`) | '계산식을 쓰기 전 graph 정본 확인', 'graph 정본·소비 확인' | N2 KK-1 |
| R6 | design 41 §5·§6.7 | -- | design 41 | 589·917행, §6.7-1(1491-1494행), §6.7-1a(1496-1500행), §6.7-10(1532-1538행) | N0.1, N2, N3.3, N3.10 |
| R7 | headroom-chain 계획 v0.7.1 개정안(브랜치 `plan/headroom-chain-k3` `ecceaed4`), v0.7.5 최종(`c0d96517`), v0.7.6(브랜치 `plan/headroom-v076` `aa6e064c` -- N3.4 소비자별 처리 표, F-23, 완료 조건 12, HC-S) | -- | `docs/01-plan/features/headroom-chain.plan.md` | N0.1 68-72행, N3.1 206-227행, 317행, 448-451행 | N0.1 Gs⁺, N3.3-3, N6, N7.2 |
| R8 | v0.1 독립 검증 결과 요약, v0.2 재검증 결과(오케스트레이터 전달) | -- | `wt/_drafts/SESSION_HANDOFF_2026-10-16.md` '추가: graph-consumption 계획 v0.1 독립 검증 결과' 절 | 42-51행 | history H3 |
| R9 | 지문 개선 백로그 | -- | `wt/_drafts/engine/U17_FOLLOWUPS.md` | 58행 | U-G11 |
| R10 | 상위 계획 용어·LR5·V9 | -- | 상위 계획 | 92·553·920행 | N2, N3.10 |

이 계획은 회로 해석을 하지 않는다. 논문 원문 근거는 없다.

---

## N9. 위험과 대응

| ID | 위험 | 대응 |
|---|---|---|
| R-G1 | 규칙 L의 정적 해석이 새 코드 형태를 못 풀어 위반이 늘어난다 | 못 풀면 위반(fail-closed)이 원칙이다. 동적 접근 허용 파일 목록은 고정이고, 늘리는 것은 기준 변경이다. 기존 동적 접근은 정적 형태로 바꾼다(GC-7) |
| R-G2 | 부채 목록이 '면제 창고'가 되거나 규칙 매개변수를 바꿔 우회된다 | 최소 단위 키, 항목 집합 부분집합 판정, 규칙 코드·매개변수까지 지문 고정, 항목 제거는 대상 코드 변경 확인, 낡은 항목 실패, 새 필드 항목 금지, card id 필수(N3.1-6) |
| R-G3 | S1 관계 필드 삭제가 아직 알려지지 않은 설계 의도(층 0 조립·검증의 관계 엣지 입력)를 지운다 | 삭제는 사용자 승인(U-G3). 상위·design의 관계 엣지 소비 지정(V9, LR5, design 41 §5·§6.7)은 정본으로 옮기는 개정을 먼저 한다(N3.10, GD-8) |
| R-G4 | 봉인 8 삭제로 잡던 결함이 빠진다 | 봉인 8 행은 봉인 2 양의 합이다(F-G31). base에서 봉인 2 거부 없는 봉인 8 거부가 있으면 삭제를 멈춘다(N4-2) |
| R-G5 | 출발 전류 변경이 출발 사다리를 바꿔 기준선이 흔들린다 | HC-1 뒤 병합(결정 6은 `c8d156e3`으로 이미 병합), 바뀐 칸마다 출처 기록(N4-4), offset-strategy fixture 알림, 빠지는 칸 수 착수 때 측정, X-G11로 보고 |
| R-G6 | K-3 card가 늦어 GC-2·GC-0b가 막힌다 | GC-2·GC-0b만 막힌다. GC-0a·GC-1·GC-3·GC-6·GC-7은 K-3과 무관하게 진행한다. K-3 card는 상위 card IT-1(card 정의 master `f2852c36` 병합, 구현 전)이고, 지연 위험은 IT-1 착수·병합 시점이다 |
| R-G7 | 정본 술어 교체로 metrics 값이 바뀐다 | M-G5에서 동치를 먼저 잰다. 다르면 교체하지 않고 공동분석 |
| R-G8 | GC-2·GC-6·GC-7이 rule_hash 대상 파일을 고쳐 ratified `structure.json` 사실이 stale이 된다 | U-G11 결정을 card 착수 조건으로 둔다. 재기록은 Role: data로 같은 card에서 한다(X-22 선례) |
| R-G9 | 트리 경로가 두 계획에서 따로 만들어진다(필드 둘, 또는 블록 밖 재구성) | 쓰기 계획 블록의 필드 하나로 정하고(O-14 (1)), 먼저 병합되는 card(기본안 HC-1)가 만들고 뒤 card는 읽는다. 오케스트레이터가 HC-D 브리핑에 넣는다. 완료 조건 3이 '필드 하나, 블록 밖 재구성 0'을, 완료 조건 9가 같은 인자 반복 호출 0을 잰다 |

---

## N10. 열린 결정

### N10.1 오케스트레이터 기본안(원칙으로 정함, 사용자가 바꿀 수 있음)

| ID | 항목 | 기본안 | 근거 원칙 |
|---|---|---|---|
| BD-1 | KVL 정본 | 쓰기 계획 출력(`node.dc_writer` + `device.dc_coord`), 별도 종속 사이클 필드 없음, '같은 DC' 변 없음(K-3 뒤) | P-1(엔진 방정식 전체), 층 의존성, DEC-83, B2·K-3, 만들면 배선 |
| BD-2 | KCL 정본 | `dc_current_basis` 하나, `rel_kcl_group`은 삭제 후보 | P-1, FR-9 |
| BD-3 | **철회(v0.2)**. v0.1 '봉인 3 결선 대조'는 항등식이다(F-G22) | -- | -- |
| BD-4 | **철회(v0.2)**. v0.1 '공급 합 판정'은 결선 행렬 항등식이다(F-G21) | -- | -- |
| BD-5 | 출발 자리값 | 기저 자유 원소에만, 나머지는 기저 행, 0 이하 = 꺼지지 않는 충돌 표지. MOS 자유 원소의 W_min 식 소자 선택은 GD-7 | KCL, fail-closed |
| BD-6 | GC-2 순서 | HC-1 뒤, K-3 구현 card 뒤 병합 | 승인된 계획 소유 존중, 파일 겹침, K-3 전제 |
| BD-7 | R1″(graph 층 안) | 면제 없이 정본 읽기 | FR-9, P-1 |
| BD-8 | 규칙 L-5 초기 개념 | diode 판정, 같은 VGS 묶음, 전도 술어(`conduction_mask`, U-G4 (가) + O-15 (A), GC-7에서 정본이 생긴 뒤 등록), 동작점 사본(정본 `device.dc_op`, O-27 부채 항목을 잡기 위해 -- v0.11) | 측정된 우회 자리 |
| BD-9 | 부채 목록 증가·우회 방지 | 최소 단위 키, 기준선 집합 + 규칙 코드·매개변수 지문(검증자 고정), 항목 제거는 대상 코드 변경 확인, 넓히기 = 기준 약화(승인) | 상위 N0.4, 작성자≠검증자 |
| BD-10 | 트리 경로 | **사용자 결정 O-14 (1) (가′)로 바뀜**: 쓰기 계획 블록이 넷별 뿌리 경로(변 열·부호, θ 무관)를 자기 출력 S0 필드로 한 번 쓰고(writer 하나), HC-1(κ_n)·이 계획(M-G1·GC-2)·design 41 §6.7(의존 묶음)이 읽는다. 만드는 card는 IT-1 뒤 먼저 병합되는 소비자 card(기본안 HC-1, 아니면 GC-2) | 단일 정본(FR-9·DEC-83 -- 자기 출력이라 사본 아님), NFR-2·WP-10(재계산 0) |
| BD-11 | `gvgs_self_edge` 정지 위치 | S1 쪽 블록(같은 판정식·사유 코드, base와 같은 층·같은 시점) | fail-closed, base 동작 보존 |
| BD-12 | 독립 검증 경로 | 오라클 forced(KCL)·free(KVL), 배선 U16(상위 개정 항목). 엔진 안은 보조 검사 둘 | 다른 모델 = 독립, 항등식 배제 |
| BD-13 | GC-5 선행 | 결정 6(d/s 맞바꿈) 구현 뒤 -- **충족**(`c8d156e3`, HEAD 조상, F-G36) | K-j: 0 이하 전류 판정은 고정 방향에서만 물리 의미 |

### N10.2 사용자 결정(모두 결정됨, O-13 (4))

사용자 결정 O-13 (4)(2026-10-19 "1~5까지 권고대로", `wt/_drafts/user_decisions.md` 632행)로 아래 결정이 모두 권고대로 닫혔다. 각 행 머리의 '결정됨(O-13)'이 결정이고, 나머지 칸은 결정 때의 질문·권고 기록이다.

| ID | 질문 | 기본안·권고와 근거 | 착수 조건 card |
|---|---|---|---|
| U-G1 | **결정됨(O-13): (가)**, 단 **O-14 (1) (가′)로 '경로 저장 안 함' 부분 개정**: 뼈대(KVL 정본 = 쓰기 계획 출력, 별도 사이클 블록 없음)는 그대로이고, 쓰기 계획 블록이 넷별 뿌리 경로를 자기 출력 S0 필드로 한 번 써서 소비자 셋이 읽는다(N3.3-3). 아래 (가) 문언의 '트리 경로 함수'는 이 필드로 읽는다. **(X-G1)** KVL 관계 정본 위치: (가) 쓰기 계획 출력(`node.dc_writer`·`device.dc_coord`) + 그 위의 트리 경로 함수, 별도 사이클 필드 없음 (나) 별도 S0 관계 블록(숲·사이클)을 두고 쓰기 계획이 읽음 (다) S1 `rel_kvl_branch`를 유지하고 엔진이 읽게 함 | **(가)**. (다)는 S1에 spec 의존 F를 담을 수 없어 엔진 방정식이 될 수 없다. (나)는 종속 선택(DEC-95 (3))이 숲 선택과 같아 두 블록이 같은 결정을 나눠 갖는다 | GC-D |
| U-G2 | **철회(v0.2)**. v0.1 질문(DEC-64 v1 문언을 as-built로 정정)은 사용자 결정 B2·K-3과 반대였다 | -- | -- |
| U-G3 | **결정됨(O-13): 항목별 삭제 승인 -- card 0 대조(M-G1·M-G2 등)가 일치를 보인 항목만**. **(X-G7, 삭제 승인)** 필드별 삭제: `rel_kvl_branch`, `gvgs_summary`(남은 칸), `gvgs_cycles.py`(정지 이전 뒤, 등록 포함), `rel_kcl_group`, `rel_vds_eq_vgs`, `rel_matching_ratio`·`rel_matching_offset`(V9 개정 뒤), `rel_equal_vgs`·`rel_l_class`(소비 이동 뒤), `device.value`·`value_key`, `node.dc_branch_node`, 그리고 M-G3c 뒤의 하위 칸 목록 | 항목별 승인 권고. 근거: 엔진 소비자 0이거나 `gs_groups`·`is_diode` 사본이고 더 일반적인 정본이 있다(N3.2 표, F-G26). 상위 검증 소비자 지정(V9)은 정본으로 옮긴다. card 0 대조(M-G1·M-G2)가 일치를 보인 항목만 올린다 | GC-2·GC-3·GC-7 |
| U-G4 | **결정됨(O-13): (가)**, **O-15 (A)로 범위 보완**: 칸별 전도 술어의 정본은 LUT memo 파생 함수 `conduction_mask(kind, w_key)` 하나다(마스크와 곡선별 첫 전도 마디·보간 근, VGS = 0 마디 찾기도 이 한 곳). `cell_floor`(search 칸 하한)와 `edge_costs`(`derived_fns.py` `_conduction_ok` 자리)가 그것을 읽는다. `sctx.cell_floors` 캐시는 허용 저장소가 아니라 지운다. `dc_conduction_floor`는 출력 전용 그대로다(F-G14, GC-7). **(X-G6, 공동분석)** R3: `dc_conduction_floor`·`dc_off_current`와 search 칸 하한·전류 상자의 관계. (가) search는 지금대로 θ 전 보수 하한을 계산하고, `dc_conduction_floor`는 봉인 9 상세의 출력 전용으로 선언(docstring 정정) (나) search가 필드를 읽게 바꿈 (다) `dc_conduction_floor` 삭제 | 의견 **(가)**, 확신도 중간. 단계 순서상 search 상자는 평가 전이고 필드는 평가 뒤 값이다. `dc_off_current`는 EO-1~OP-5 사이만 oracle이 소비하고(옛 ε = 1 판정), OP-5 병합 때 출력 전용 선언(X-G6 (가)의 `dc_conduction_floor`와 같은 처리, O-46 (2) -- v0.11 갱신). M-G6 자료로 확정 | GC-7 |
| U-G6 | **결정됨(O-13): 미룸**. **(X-G5)** 지정 소비자가 아직 없는 필드의 배선을 소비자 card(단위 8, U17 ②, U16)로 미루고, 그때까지 부채 목록 '배선 대기'로 둘지 | 미룸 권고. 소비자가 구현되지 않은 엔진 기능이라 이 계획에서 만들면 범위를 넘는다. 대신 그 card 완료 조건에 '부채 항목 0'을 넣는 상위 개정을 한다(N3.10) | GC-1 |
| U-G8 | **결정됨(O-13): 넣기**. **(X-G8)** 출발 전류의 기저 경유를 O-10 (4)의 충돌 기록과 함께 넣을지 | 넣기 권고. 새 전류 사슬이 아니라 기존 기저를 쓰고, 지금 자리값은 KCL을 어긴 전류로 면적·사다리를 고른다(P-1) | GC-5 |
| U-G9 | **결정됨(O-13): (가) 봉인 8 삭제**. **(X-G10)** 봉인 8: (가) 삭제(472행이 맡긴 역할은 봉인 2가 θ마다 소자별로 이미 함) (나) 유지하고 목록만 쓰기 계획 종속 분류로 교체 | **(가)**. 봉인 8 행은 봉인 2가 재는 같은 양의 합이라 새 정보가 없다(F-G31, K-c). (나)는 θ마다 사이클 멤버를 펼치는 계산만 더한다. 숲 회계 불변량은 어느 쪽이든 별개 보조 검사로 둔다. M-G1b·N4-2로 확인 | GC-2 |
| U-G10 | **결정됨(O-13): 넘기기(오라클 forced·free 대조, U16 완료 조건)**. **(X-G4)** 결과의 독립 KCL·KVL 확인 경로를 오라클 forced·free 대조로 하고, 그 배선을 U16 완료 조건으로 넘기는 상위 개정을 할지 | 넘기기 권고. 엔진 안 재합산은 항등식이고(F-G21·F-G22), 오라클은 다른 모델·다른 풀이다(F-G23). 엔진 → 오라클 입력 생성기가 U16 범위다 | GC-D |
| U-G11 | **결정됨(O-13): (가) card마다 rule_hash 재기록**. GC-2(정지 블록 위치에 따라)·GC-6·GC-7이 rule_hash 대상 파일(`cells.py`·`net_model.py`·`node_impedance.py`·`s1v_fields.py`·`l_classes.py`·`matching_groups.py` 등)을 고치면 `structure.json` 2개의 rule_hash가 stale이 된다: (가) card마다 rule_hash 재기록 승인(Role: data, X-22 선례) (나) 백로그 '지문을 판정 로직(AST)에만 묶기'를 이 계획 범위에 넣어 GC-6 앞에 card로 둠 (다) (나) + 그래도 판정 로직이 바뀌는 파일은 (가) | **(가)**. 이 card들은 판정 로직 자체(정본 읽기, READS)를 바꾸므로 지문을 AST에 묶어도 재기록이 필요하다. 지문 개선은 이 계획의 목적(graph 소비 정합)과 별개라 백로그에 둔다 | GC-2·GC-6·GC-7 |
| U-G12 | **결정됨(O-13): 승인 -- GC-2·GC-3 착수 승인, GC-8은 B-G2 결론 뒤 다시 묻는다**. **재질문 대상 소멸 -- O-15 (C) 승인 범위**: B-G2의 결론(위쪽 방향 차분 제약 그래프가 R-1′ 변 목록을 정본으로 읽고, 같은 개념은 하나로 -- O-16 (3))을 사용자가 O-15 (C)·O-16 (3)으로 승인했다. GC-8 범위는 headroom-chain v0.7.5 N3.4가 정한 배선 분담대로다(N7.1). **(X-G9)** O-10 범위 밖인 GC-2·GC-3·GC-8(엔진 KVL·KCL 정본 정리, 보조 검사, R4 처리)의 착수를 승인할지 | 승인 권고. KK-1 원문의 '관계가 엔진에 적용되어 있는지 확인'과 소비 정합 조사에서 나온 단일 정본 정리이고, GC-2·GC-3은 계산 결과가 바뀌지 않는다(N4-1, v0.11부터 '순수 리팩터링' 표시 -- N4-0). (결정 때 권고는 'GC-8은 B-G2 결론 뒤 다시 묻는다'였다. 그 재질문 대상은 O-15 (C)·O-16 (3) 승인으로 소멸했다) | GC-2·GC-3·GC-8 |
| U-G13 | **결정됨(O-13): (가) + 아래 끝 전류 충돌 경우 (가-1)**(X-G11 원래 취지와 다름 승인). **(X-G11)** 출발 충돌 칸 처리(N3.6-3): (가) 충돌 표지(꺼지지 않음)가 선 상태는 최상 칸 선택에서 실행 불가, 아래 칸은 칸마다 판정해 충돌 칸을 사다리에서 빼고 기록, 0 이하 θ 자유 원소에 자리값 없음, 아래 끝이 전류 충돌인 경우(최상 칸 무관)의 칸 0 고르기는 (가-1) 사다리 격자에서 충돌 없고 실행 가능한 최대 t, 없으면 충돌 없는 최소 t(그 점이 매크로 실패면 `use_macro` 해제 뒤 면적만으로 다시 고름, 실행 불가 원인마다 t를 담아 기록) / (가-2) 충돌 없는 구간 안 이분 탐색 / (가-3) 빈 사다리, 선택 후보가 모두 충돌이면 칸 0도 빼고 빈 사다리(θ 성분 `uncovered`, 층 0 상자 중심 출발, `_report` 빈 사다리 처리, 원인과 다른 면적 충돌 기록 안 함), 1회차 전류 충돌은 네 함수·여섯 호출 자리에서 자리값 없이 전류 충돌 사유로 비활성·기록 (나) 자리값 사용 + 대체값 명시·대체 표지(선택은 그대로) (다) 출발 단계 정지 | **(가)**, 아래 끝이 전류 충돌인 경우는 **(가-1)**(단조 가정 없음, 사다리 칸 폭 분해능, 실행 불가 대체는 지금처럼 가장 느슨한 쪽(최소 t), 사다리 계산은 격자·정제 설정이 겹칠 때만 재사용 -- (가-2)는 계산이 더 들고 단조가 아니어서 재확인이 필요, (가-3)은 충돌 없는 중간 t를 버린다). 모든 후보가 충돌일 때 (다) 정지 대신 상자 중심에서 계속하는 것은 출발 단계가 판정 단계가 아니고(EP-7) 틀린 d/s 선언 거부는 봉인 7 한 곳이 하기 때문이다(N3.6-3). 선언 방향은 결정 6(`c8d156e3`, 이미 병합)으로 고정됐으므로 0 이하 전류는 물리 동작점이 아니고(P-1, K-j), 지금 코드는 `use_macro` 해제·예산 없음에서 실패 표지를 놓치고 아래 칸을 판정하지 않는다(F-G32). 사다리 선택이 바뀌므로 원래 취지와 다르다. 바뀌는 칸 수는 GC-5 착수 때 잰다 | GC-5 |

(U-G5·U-G7은 v0.3에서 결정 목록에서 내려 백로그 B-G1·B-G2로 옮겼다.)

### N10.3 design에서 닫을 항목

| ID | 항목 | card |
|---|---|---|
| GD-1 | 출력 모듈 범위와 엔진 진입점 목록(규칙 L-1 도달·L-2), 호출 그래프 도달 판정 방식. 출력 함수 판정 기준은 계획 N3.1-2가 정한다(엔진 reader 0이고 결과 JSON·보고 경로에만 도달). design은 그 기준을 적용한 목록을 만들고, 그 목록은 검증자가 독립 재측정한다(N3.1-2) | GC-1 |
| GD-2 | 쓰기 계획 파일 분할, 쓰기 계획 블록 출력 두 필드 -- **넷별 뿌리 경로 필드**(변 열·부호, 뿌리 종류 F/W4)와 **Gs⁺ VGS 변 필드**(변 목록·방향) -- 의 이름·(kind, field)·값 형식, writer = 쓰기 계획 블록(WRITES 등록, 권한표 등록), 소비자들의 READS(HC-D design과 같은 필드). 만드는 card는 HC-1, 못 하면 GC-2. 전류 대칭 결과(`ties`·`negated`·`zeros`) S0 graph 필드(sizing 층 이하, `dc_current_basis` 쪽, writer 입력에 spec `search.untie_orbits` 포함)의 이름·위치·writer와, `search_domain`이 그 필드를 읽기만 하도록 바꾸는 방식(층 역전 방지, GC-8 (2)). 이 필드를 만드는 card는 HC-1, 못 하면 GC-8. 쓰기 계획 블록 두 필드는 만드는 card(HC-1 또는 GC-2)에 맞춘 배치 | 쓰기 계획 두 필드: GC-2, 전류 대칭 결과 필드: GC-8 (둘 다 HC-1이 먼저 만들면 HC-D design과 공유) |
| GD-3 | 부채 목록의 파일 위치·형식, 최소 단위 키 표기, 기준선 집합 상수, 지문 대상 목록과 직렬화 규칙, 동적 접근 허용 파일 목록 | GC-1 |
| GD-4 | `node.terminals` 결선 점검의 위치(블록 이름·writer), 사유 코드 | GC-3 |
| GD-5 | graph 층 안 diode 판정(R1″)을 정본 열로 바꾸는 투영 경로 | GC-6 |
| GD-6 | design 40 §2.4.8 필드 소유표에 reader 칸을 더할지(규칙 L-1이 기계 판정하므로 표는 사람용 요약) | GC-D |
| GD-7 | 출발 자리값: 기저 자유 원소가 MOS일 때 W_min·IDu/L의 IDu·L을 어느 소자 것으로 쓰는지, MOS가 아닐 때의 자리값(기존 식에서), 충돌 표지 이름과 사유 코드(네 함수·여섯 호출 자리의 전류 충돌 비활성 사유 포함, `WHY_NO_CURRENT`와 구분), 고칠 자리(`iv_gain_l.py:64-65, :117-119, :125-127`의 원소 없음 → '이득 목표 미달' 경로, `iv_area.py:68-69`의 무기록 건너뜀, `iv_matching_l.py:107-118`의 `SRC_MATCH_L`·`SRC_OFFSET_GUARD` 사유 분리, `iv_noise.py:77-78`), 사다리 칸 충돌 기록 형식, 아래 끝이 전류 충돌일 때 격자 탐색에서 고른 점을 `refine=True`로 다시 풀지, **실행 불가 원인별 충돌 기록 형식**: 면적 충돌(지금 `start_intervals.py:388` 라벨 `estimate_at_gm_id_lo`)과 매크로 목표 달성 불가 충돌(지금 383행 라벨 `macro_target_unattainable_at_gm_id_lo`)은 둘 다 t = 0이라는 뜻이라 (가-1) (ii)로 t ≠ 0을 고르면 틀린다. 고른 t와 그 t의 면적 추정·매크로 기록을 담는 형식(t_p는 사다리 격자 점이라 실제 경계의 격자 기준 근사다 -- 기록 문구에 '격자 기준'을 명시한다), 두 원인이 겹칠 때 둘 다 남기는 형식, (ii) 점에서 `use_macro`를 끈 기록 형식. **빈 사다리 출력 형식**: `rungs` = (), `uncovered` = 칸 0이 정했을 θ 성분 전부, `area_est_m2` = None, `area_fraction` = None(선택점 없음), 소자 행은 마지막으로 푼 상태(충돌 소자 전류·폭 None). `E/search/start_intervals.py:264` 조기 반환(`rungs` = (), `uncovered` = (), `area_fraction` = None, 사유 `lut_curve_undefined_for_all_l`)과는 `uncovered` 규칙이 어긋나므로 같은 규칙('칸이 없으면 칸 0 성분 전부')으로 맞추고 사유(inactive 대 전류 충돌)로 두 경우를 구분한다(기본안. 두 필드는 엔진 reader가 없는 출력 기록이다 -- grep). **아래 칸 표지는 `_placed` 고정점 반복(`E/search/start_intervals.py:171-182`)의 마지막 상태(`solve(lower, refine=False)`가 돌려주는 상태)에서 읽는다. 표지를 위해 새 계산을 하지 않는다**(NFR-G4) | GC-5 |
| GD-8 | design 41 §5.5 조립 공유량 입력을 정본(`gs_groups`, 쓰기 계획 출력·넷별 뿌리 경로 필드)에서 읽도록 하는 개정 | GC-D(단위 8에 전달) |
| GD-9 | 규칙 L test 파일 분할(`E/tests/structure/`의 규칙 H 대응 포함). **규칙 L 코드는 `structure_checks.py`와 다른 별도 파일에 두고, 기준선 지문의 '규칙 L test 코드'는 그 파일만이다**(N3.1-6 (d)). LT-1처럼 같은 `structure_checks.py`를 고치는 card의 무관한 수정이 기준 변경으로 잡히지 않게 한다. 규칙 L 코드가 다른 파일의 helper를 부르면 그 helper도 판정을 바꿀 수 있으므로 지문 대상이다((d)). 그래서 design은 파일 경로와 함께 규칙 L이 `structure_checks.py`의 helper에 기대지 않는 파일 구성을 정한다 | GC-1 |
| GD-10 | `gvgs_self_edge` 정지를 옮길 S1 블록과 그 거부 픽스처, 그 파일의 rule_hash 대상 여부 | GC-2 |
| GD-11 | 숲 회계 불변량 검사의 위치(쓰기 계획 블록 밖 S0 검사), 사유 코드, 성립 조건(E = MOS마다 (gate, source) 변 하나 + 가지치기된 저항 포함 모든 저항 변, V = F 한 점 병합 뒤 변 끝점, K-3 전 as-built 측정 시 '같은 DC' 변 포함), 봉인 8 삭제에 따른 봉인 판 어휘 정리 | GC-2 |
| GD-12 | `conduction_mask(kind, w_key)`의 반환 형식(마스크, 곡선별 첫 전도 마디·보간 근), 지금 두 격자판 마스크(분지 요구, VGS = 0 마디 on 검사, `zero_first` 처리)를 하나로 합칠 때의 정의와 그 차이가 결과를 바꾸는지의 측정. **VGS = 0 마디 찾기는 `conduction_mask` 모듈의 한 함수로 모으고 `current_box`도 그것을 부른다(닫힘 -- O-15 (A))**. `current_box`의 I_off 값 자체(θ 전류 상자 하한)는 다른 개념이라 그대로 둔다. **gm/ID 정점(분지) 마디도 LUT memo 파생 함수 한 곳에서 계산한다**: 지금 `cell_floor._peak_floor`(`E/search/cell_floor.py:45-46`)와 `derived_fns._conduction_ok`(`E/lut/derived_fns.py:39-41`)가 따로 계산한다(오케스트레이터 기본안 -- 같은 개념 하나). `sctx.cell_floors`를 지울 때 같은 캐시를 쓰던 `_peak_floor`(`E/search/cell_floor.py:36-50`)는 LUT만의 순수 함수이므로 같은 원칙(O-15 (A))으로 **LUT memo 파생 함수로 둔다(확정, 허용 저장소 = LUT memo 파생 함수)**. design은 두 파생 함수의 이름·키만 정한다 | GC-7 |
| GD-13 | GC-9의 정확 MOS 전류 공용 함수 위치·서명, 기저 float 행의 컨텍스트 자리, `current_cone` 소비자 여섯 곳의 읽기 전환 방식(`_vds_floor`의 이름은 headroom-chain HC-S design) | GC-9 |
| GD-14 | 규칙 L-1 확장 '호출자 0 내부 함수': 엔진 진입점 목록(GD-1)에 없고 엔진 안 호출자가 0인 함수(`_module_map` 'entry' 표시만으로는 진입점이 아님)를 위반으로 잡는 판정과 거부 픽스처. **넣기로 결정됨(O-36 (2))** -- design은 판정 방식과 거부 픽스처를 정한다. 판정은 **AST 호출 그래프**로 한다(이름 grep 금지 -- docstring 언급을 호출로 세거나 import 시 실행되는 호출을 놓친다). 대상은 GC-0a M-G9가 미리 잰다. `size_and_seal_local` 배선 대기 항목은 이 규칙의 부채 항목이다(N3.2 표) | GC-1 |

### N10.4 백로그(이 계획에서 정하지 않음)

| ID | 항목 | 근거 | 이 계획과의 관계 |
|---|---|---|---|
| B-G1 | MNA 조건수 기록과 그 소비자·판정 기준 | 상대 잔차는 공허(F-G28), 조건수는 의미가 있으나 소비자·선언 기준이 없다 | MNA 코드 변경 없음 |
| B-G2 | **O-15 (C)·O-16 (3)으로 닫힘**. R4: `headroom_bound`·`ls_swing` 포화 부등식 그래프와 HC-1 제약 그래프의 관계. O-15 (C)는 위쪽 방향 차분 제약 그래프 네 곳(`ls_swing`·`headroom_bound`·`iv_headroom`·`order_terms`)이 R-1′ 제약 그래프 변 목록을 정본으로 읽는다고 정했고, O-16 (3)이 '같은 개념은 하나로, 물리적으로 다른 양은 다른 이름의 다른 개념'으로 문구를 정정했다. 정의 차이 판단은 headroom-chain v0.7.5 N3.4 소비자별 처리 표다 | O-15 (C)·O-16 (3) | GC-8(`headroom_bound`·`order_terms`), HC-1(`iv_headroom`). `ls_swing`은 O-26 (1)로 자체 제약계를 지운다(gain-budget card DE-1) |
| B-G3 | 비레일 g = s 정지와 레일 g = s 허용의 비대칭 일반화 | 물리 근거 없음(K-h) | 이 계획은 보존만 |
| B-G5 | 출발 자리값의 '정해진 전류 기하평균' 항(N3.6-2) 유도(B-G4는 O-36으로 지운 번호라 쓰지 않는다): 선언·물리 유도가 없는 출발값 휴리스틱이다('추정' 표기). 손계산 기준(예: 같은 기저 행·같은 묶음의 정해진 전류를 쓰는 식)으로 대체할지 | 전체 정합 검증 A-F12(`wt/_drafts/evidence/2026-10-19/full_audit_summary.md`) | GC-5는 식을 바꾸지 않는다(동작 보존). 대체는 별도 card·사용자 결정 |
| (기존) | `structure_rule_fp`를 판정 로직(AST)에만 묶기 | `wt/_drafts/engine/U17_FOLLOWUPS.md` 58행 | U-G11 기본안은 포함하지 않음 |
