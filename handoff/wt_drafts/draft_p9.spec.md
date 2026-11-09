---
id: 20260930-p9-kcl-edges
phase: 2
evidence_type: equivalence
gate_change: no
approval: 20260923-20-dead-code-dup-design
approval: 20260930-p9-e1-correction
---
## 의도

design `20-dead-code-dup` §6.2·§8 P9·§10 E1(2026-09-30 정정 커밋 6398a28, 승인 `20260930-p9-e1-correction`): KCL 엣지(내부 2단자 넷 + `current_forced` 매칭 쌍)의
**정의가 두 곳에 있다**. 정본 후보 `stick_diagram._kcl_and_matching_edges`와, 같은 규칙을 본문에 다시 쓴 `stick_diagram.kcl_series_union`이다. 정의를 한 곳으로 모아
규칙이 바뀔 때(B26 -- 계획 DF-19·DF-26, 담당 Phase 4) 한 곳만 고치면 되게 한다(WP-14). A = `skills/analog-gmid-design/assets`, SD = `A/stick_diagram.py`, SR = `A/sizing_recipe.py`.

**통합 방향 -- 정정된 design 원문 그대로**(§6.2, 134행): "정본 후보 `stick_diagram._kcl_and_matching_edges`(레일 판정을 넷 이름 상수 `_RAIL_NETS`로 한다 -- 확정은 B26,
계획 DF-19·DF-26 담당 Phase 4). 중복 = `kcl_series_union` 본문의 엣지 정의(넷별 단자 사용 목록·레일 제외·2단자 판정·매칭 쌍 사슬). `kcl_series_union` 자체는 엣지가 아니라
KCL 그룹(엣지의 연결 성분)을 돌려주는 다른 질문이고 엔진 운영 호출자가 2곳이라 지우지 않는다 -- 엣지 정의 자리에서 정본을 불러 union한다(이름·시그니처·반환 불변)."
운영 호출자 2곳 = SR `_build_theta_evaluator`의 `stack_groups_kcl`(SR 8055), SD `_kcl_branch_map`(SD 7310). 지우는 것은 본문의 중복 엣지 정의(SD 3023-3026·3041-3048)이고,
그 자리에서 `_kcl_and_matching_edges(netlist, matching_pairs)`를 불러 union한다(design §2.2-3 "정본의 시그니처는 바꾸지 않는다").

**`_metric_kcl_residual`은 P9 대상이 아니다** -- 정정된 §6.2 원문: "이 metric은 엣지를 만들지 않는다(노드별 부호 붙은 전류 합, float 반환 -- F3 성격, 다른 개념). 겹치는 것은 MOS
단자 전류 부호 규약(`_kcl_terminal_sign`)과 레일 이름 집합(B26)이고 이 Phase의 대상이 아니다." 실측: 소자 `ID`를 노드에 부호 붙여 더하고(SR 4307·4309) 레일 이름 집합은
SR 4293 인라인 튜플(`_RAIL_NETS`·`_DEFAULT_RAIL_HI/_LO`와 함께 세 번째 사본)이다. 이 card는 레지스트리 §2 행을 이 사실로 고친다(계약 8).

**정본은 topology 무관이어야 한다(사용자 원칙 2026-09-30)**: `_kcl_and_matching_edges`는 레일 판정을 넷 이름 상수 `_RAIL_NETS`(`{"vdd","gnd","vss"}`, SD 2983)로 한다 --
그래서 레지스트리 상태는 계속 **'정본 후보(B26 해소 뒤 확정)'**이고, 이 card는 그것이 해소됐다고 적지 않는다. B26 = `.ai/context.md` 14963행 백로그(레일 판정을 `supply_nets`
선언에서 읽도록). P9는 `_RAIL_NETS`를 고치지 않고, **새 이름 리터럴을 하나도 더하지 않는다**(계약 5). P9 뒤 `_RAIL_NETS`를 읽는 KCL 엣지 코드는 한 곳(정본)뿐이 되어
B26의 교체 지점이 하나 준다.

**영구 test와 auditor 측정의 나눔(판정 유형 근거 참조)**: base에서 실패하는 구조 판정(계약 1, 6(b))은 영구 test에 두지 않고 auditor AST 측정으로 둔다. 영구 test
(`A/tests/contracts/test_dup_kcl_edges.py`)는 동작 계약(2, 3(b))만 판정하고 base·병합본 모두에서 PASS한다.

## 관찰 가능한 계약

1. **엣지 정의 한 곳(auditor AST 측정 -- 영구 test가 아니다)**: 병합본 `stick_diagram.kcl_series_union`의 본문(docstring 제외 AST)이 (a) `_kcl_and_matching_edges`를 1번 이상
   호출하고 (b) `_RAIL_NETS`를 참조하지 않으며 (c) 속성 `.source`·`.drain`에 접근하지 않는다(넷별 단자 사용 목록을 직접 만들지 않는다). base에서는 (a)(b)(c) 모두 어긋난다
   -- auditor는 base·병합본 두 판정을 모두 판정 기록 `checks.V2.basis`에 적는다. 이것이 design E1이 가리키는 "P9 = `kcl_series_union` 본문의 `_RAIL_NETS` 참조·`.source`/`.drain`
   접근 0과 정본 호출(`20260930-p9-kcl-edges` 계약 1)"의 기계 판정이다. 판정기 자기 점검은 '거부해야 할 입력'의 합성 소스로 한다.
2. **시그니처·반환 불변(영구 test)**: `kcl_series_union(netlist: list, matching_pairs: list) -> dict`. 반환은 `{대표: [구성원, ...]}`이고 구성원 집합은 (내부 2단자 넷으로 이어진
   소자 쌍 + 매칭 쌍 안의 이웃 소자 쌍)을 엣지로 한 그래프의 연결 성분, 대표 = 그 성분에서 `netlist` 순서가 가장 앞선 소자, 구성원 목록 = `netlist` 순서.
   엣지에 닿지 않는 소자는 자기 혼자 그룹이다. 판정 입력은 구성으로 정답이 정해진 합성 넷리스트(아래 '거부해야 할 입력'), 기대값은 손으로 적은 리터럴. base·병합본 모두 PASS.
3. **정본 불변**: (a) auditor: `stick_diagram._kcl_and_matching_edges`의 시그니처와 docstring 포함 `ast.dump`가 base와 같다. (b) 영구 test: 반환 `(a, b, kind, detail)` 목록의 모양 --
   `kind` ∈ {`"internal_series"`(detail = 넷 이름), `"declared_matching_pair"`(detail = `None`)} -- 을 합성 입력에서 **집합**(순서 무관)으로 판정한다.
4. **동작 보존(DIFF-DUP -- design §3·§6.2, 판정은 auditor)**: library 로드 가능한 회로 **전부**(실측 9개 -- `_TEMPLATE.topology.json`은 회로가 아니라 로드 실패)마다 두 입력 --
   (i) `load_topology` 메타의 `current_forced` 매칭 쌍(SR `_build_theta_evaluator`와 같은 호출 형태) (ii) `[]`(SD `_kcl_branch_map`과 같은 호출 형태) -- 에서
   `list(kcl_series_union(trs, P).items())`(대표·구성원 순서 포함)와 `_kcl_and_matching_edges(trs, P)`(목록 그대로)가 base와 병합본에서 같다(18 + 18 비교).
   레일 이름 넷이 정확히 두 번 쓰이는 경우(레일 제외 분기가 결과를 바꾸는 유일한 경우)는 library에 `two_stage_ota`의 `gnd` 하나가 있고, auditor는 그와 별도로
   라이브러리 밖 이름의 합성 넷리스트 하나(레일 이름 넷 2회 사용 포함)로 같은 base·병합본 비교를 더한다. 그리고 E-LIB·E-INST(파일럿·`folded_cascode`)가 base와 같다.
   이 결과가 design E1의 "P9 = DIFF-DUP·E-LIB·E-INST가 base = 병합본"(판정 기록 `checks.V2`)이다.
5. **topology 무관 -- 전 범위**: (a) auditor: 병합본 `A/*.py`·`workspaces/run_harness.py`의 문자열 상수(docstring 제외) 다중집합이 base 다중집합의 부분집합이다(새 이름
   리터럴·새 문자열 0). (b) auditor: SD의 `_RAIL_NETS` 참조 줄 수가 base보다 크지 않다(실측 18줄, 기대 17줄 -- `kcl_series_union` 안 1줄이 빠진다). (c) 영구 test는
   레일 이름 판정을 계약으로 삼지 않는다: 합성 입력에서 이름이 `vdd`·`gnd`·`vss`(대소문자 무관)인 넷은 쓰지 않거나, 쓰면 단자 사용 수가 2가 아니다(결과가 레일
   이름 규칙에 기대지 않는다 -- B26이 이 규칙을 `supply_nets` 선언으로 바꿀 때 이 test를 고칠 필요가 없게). (d) 레지스트리 §2 KCL 엣지 행의 정본 칸은 계속
   '정본 후보'와 'B26'을 담는다.
6. **배선(auditor AST 측정)**: 새 def 0. (a) 병합본에서 `kcl_series_union`의 엔진 호출 위치가 base와 같다(SR `_build_theta_evaluator`, SD `_kcl_branch_map` -- AST 호출 2곳).
   (b) `_kcl_and_matching_edges`의 엔진 호출 위치는 base의 2곳(`audit_vertical_stack_id_vs_kcl`, `propose_vertical_stack_id_gap_fill`)에 `kcl_series_union` 1곳이 더해진다
   ((b)는 base에서 어긋나므로 영구 test에 두지 않는다).
7. **범위(auditor)**: 병합본에서 base와 다른 엔진 파일은 `A/stick_diagram.py` 하나이고, 그 안에서 AST가 바뀐 최상위 정의는 `kcl_series_union` 하나다(docstring 갱신 허용).
   SR(`_metric_kcl_residual` 포함)·`workspaces/run_harness.py`·library는 base와 바이트 동일.
8. **레지스트리**(`docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`, code-author): (a) §2 'KCL 엣지' 행(실측 43행) -- 중복 칸에서 `_metric_kcl_residual`을 빼고
   사유(엣지를 만들지 않음, 겹치는 것은 부호 규약·레일 이름 집합 -- 다른 개념)를 적으며, `kcl_series_union`은 '엣지 생성부 정본 호출로 통합 완료(20260930-p9-kcl-edges)'로,
   상태 칸의 '행동 보존 통합 가능'을 '엣지 정의 통합 완료, 정본 확정은 B26 뒤'로 고친다. 정본 칸의 '정본 후보(… `_RAIL_NETS` …, B26 해소 뒤 확정)'는 유지하되, 병합 뒤
   낡는 '(stick_diagram 3148행)'은 이름 참조(`_kcl_and_matching_edges` 안 `_RAIL_NETS` 판정)로 바꾼다. (b) §6 `kcl_series_union`·`_kcl_and_matching_edges` 행(실측 472·473행)
   비고를 병합 뒤 사실로(472행의 낡은 'SD:3298'·'SD:3188-3212'·'독자 구현' 문장 포함 -- P8의 §6 `size_transistor` 행 선례처럼 §6에 둔다, §1 집계 불변). (c) `_metric_kcl_residual`을
   언급하는 세 행 -- §4 `_metric_kcl_residual`(308), §5 `trace_vdd_to_gnd_branches`(428), §6 `_kcl_terminal_sign`(474) -- 의 낡은 줄 번호(308의 4456·3882-3883·4448, 428의
   SD:1216-1224·SD:3580·SR:4469-4472, 474의 SR:4469-4472)를 이름 참조로 바꾸고 겹침이 부호 규약·레일 이름 집합임을 적는다. (d) 병합본에서
   `A/tests/tools/reg_check.py --registry … --root …`가 exit 0(실측 HEAD: '발견 0', exit 0).
9. **성능(관찰값)**: E-INST 두 회로의 실행 시간을 base와 병합본에서 재서 기록한다(임계값 없음 -- `kcl_series_union`은 호출마다 엣지 목록 하나를 더 만든다).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

equivalence: 동작 보존 변경이다(design §8 P9 행 -- 정정본 "equivalence | (a) 합성 넷리스트 + (c) DIFF-DUP·E-LIB·E-INST", 계획 N3.12.3 686행 "동작을 보존하는 변경(TS1,
Phase 2 통합, Phase 3 이동)은 `equivalence`"). 새 함수가 없어 dup-w-calc(P8)처럼 ImportError red의 근거도 없다.

**base에서 실패하는 새 test를 equivalence에 둘 수 있는가 -- 두지 않는다.** 규칙 원문:
* 계획 N3.12.3 순서 3(680행): "red-green이면 base에서 assertion 실패 확인 …, **equivalence면 base에서 통과 확인**".
* 계획 N3.12.3(686행): equivalence = "test 커밋이 그대로이고 **base와 병합본 모두 통과**".
* 계획 N4.2 V2(838행): "equivalence: test 커밋 불변 + **base·병합본 모두 PASS** + 유형별 동등 증명".
* design 05 §10-4(289행)는 equivalence의 커밋 모양만 정하고("같음, 단 ①의 `Role: test`가 0개면 M^1 = `old`") 증거는 §10-6대로 auditor의 V2에 맡긴다 -- 예외 조항이 없다.

선례: P5 `20260923-d-delete-dead`(새 GONE test가 base에서 AssertionError, V2 PASS)와 P5b `20260923-d-delete-telescopic`(새 test 55 중 8건 base AssertionError, 판정 기록 V2 basis
"equivalence는 red 필드에 쓰지 않는다", V2 PASS)는 auditor가 받아들였다. 그러나 이것은 판정 기록에 적힌 auditor 해석이고 계획·design 규칙 문장에는 없다. 반대 방향 선례로
P8 `20260930-dup-w-calc`는 AST 구조 판정이 base에서 18개로 실패하자 red-green으로 갔다(spec card 판정 유형 근거). 규칙 문장이 선례보다 우선하고, P9를 red-green으로
바꾸면 방금 승인된 design §8 P9 행(equivalence)과 어긋나 또 정정이 필요하다. 그래서 **base에서 어긋나는 구조 판정(계약 1, 6(b))은 auditor AST 측정으로 옮기고**, 영구 test는
base·병합본 모두 PASS하는 동작 계약만 둔다. 잃는 것: 누가 나중에 엣지 정의를 다시 인라인하면 영구 test가 잡지 못한다 -- 레지스트리 §2·§6 행(계약 8)과 Phase 3 MOD3 이동
(`circuit_state_graph`)의 AST 해시 대조가 그 자리를 본다.

실측(2026-09-30, HEAD cd64170 -- base 070cf69와 SD 3003-3160·7304-7310, SR 전체가 같다): 두 함수의 엣지 규칙이 줄 단위로 같고(SD 3023-3026·3041-3048 대 3142-3154, 같은
`_RAIL_NETS` 판정·같은 `len(uses) == 2 and uses[0] != uses[1]`·같은 `zip(names, names[1:])`), union 순서도 같다(내부 넷 → 매칭 쌍) -- 그래서 union-find 구조까지 같고,
대표는 넷리스트 순서로 다시 고르므로 결과가 비트 단위로 같다. library 9회로 × 2입력 18/18에서 `kcl_series_union` 그룹 = `_kcl_and_matching_edges` 엣지의 연결 성분(scratch `p9_diff.py`).
증거: 기존 test 전부와 새 test가 base·병합본 PASS, 계약 1·3(a)·5(a)(b)·6·7 auditor AST 측정, DIFF-DUP·E-LIB·E-INST base = 병합본(계약 4). V3는 바뀐 def
`kcl_series_union`에 적용된다 -- 합성 입력(대표 순서·3회 사용·같은 소자 source=drain·세 소자 매칭 튜플)이 그 변이를 죽이도록 짠다.

## oracle 종류와 출처

(a) 구성 입력(우선): 합성 넷리스트(라이브러리 밖 소자·넷 이름)마다 기대 그룹과 기대 엣지 집합을 KCL 물리 규칙(외부 공급이 없는 2단자 노드에서는 두 소자 전류가 같다 --
전하 보존)과 매칭 선언에서 **손으로** 적는다. test는 `kcl_series_union` 출력을 `_kcl_and_matching_edges` 출력으로 만든 기대값과 비교하지 않는다(둘 다 피검 심볼 -- V4 (1),
design §6.2 "두 피검 함수를 서로의 기대값으로 쓰지 않는다"). 두 함수 사이의 차등은 auditor의 (c) 측정(계약 4)이 맡는다. (c) 동작 보존: DIFF-DUP·E-LIB·E-INST 기대값 = base
실행 결과(auditor). 계약 1·3(a)·5(a)(b)·6·7은 auditor AST 판정(구성: 합성 소스로 판정기가 실제로 거부·통과하는지 자기 점검).

## 거부해야 할 입력

합성 넷리스트(소자 이름 예 `qa1`·`qb2`, 넷 이름 예 `nx_7` -- 라이브러리 밖): 사슬 A-B-C(내부 넷 둘) → 한 그룹 / 세 소자가 같은 넷을 씀(3회 사용) → 그 넷으로 묶지 않음 /
한 소자의 source = drain 넷(사용 2회, 같은 소자) → 묶지 않음 / 넷을 공유하지 않는 매칭 쌍 → 한 그룹 / 세 소자 매칭 튜플 → 사슬로 한 그룹 / 매칭 쌍을 넷리스트 역순으로
선언 → 대표는 넷리스트 순서 첫 소자 / 레일 이름 넷을 세 번 이상 쓰는 입력 → 그 넷으로 묶지 않음(3회 사용 규칙으로 -- 계약 5(c)). auditor 계약 1 판정기 자기 점검: 본문에
`_RAIL_NETS` 참조·`.source` 접근이 있는 합성 `kcl_series_union` 소스 → 거부, 정본 호출만 있는 합성 소스 → 통과. 계약 5(a) 판정기: 합성 병합본에 새 문자열 상수 → 발견.

## library 회로 적용 여부

적용: 계약 4(DIFF-DUP 9회로 × 2입력), E-LIB(9회로), E-INST(파일럿·`folded_cascode` -- SR `_build_theta_evaluator`가 `kcl_series_union`을 부른다).

## 무동작 판정 입력(무발동 값)

library 회로 전부와 기존 test 전부 -- 판정·산출물이 base와 같다(결과가 비트 단위로 같으므로). 새 산출물 필드 없음.

## 재현할 수치

`kcl_series_union` 그룹 수(auditor가 독립 실행으로 재현, 입력 (i) current_forced / (ii) `[]`; base 070cf69와 HEAD cd64170에서 같음): `common_gate_amplifier` 1/1,
`current_reuse_telescopic_ota` 17/29, `folded_cascode` 5/9, `ngcc_3stage_ff` 11/12, `nmcnr_amplifier` 7/10, `pushpull_follower_buffer` 3/3, `sf_pushpull_output_opamp` 11/12,
`two_stage_ota` 3/4, `two_stage_ota_sf` 4/5. 병합본에서 같은 값. SD `_RAIL_NETS` 참조 줄 수 base 18 → 병합본 17.

## 결정 필요 항목

없음. 착수 조건이던 design E1·§6.2·§8 P9 행·196행 정정은 사용자가 승인했다(2026-09-30 원문 "E1 문구 정정 승인하고 topology.json주석은 보류해." -- 승인 기록
`20260930-p9-e1-correction`, `target_kind: diff`, diff 6398a28, 커밋 ab90ec5). 회로 해석 없음(순수 connectivity 규칙, 동작 보존).

오케스트레이터 참고(결정 아님):
* `approval` 두 줄: 계획 N3.12.3(674행) "승인 기록이 둘 이상 필요하면 나눈다"는 이 card에 걸리지 않는다고 본다 -- 둘째 승인은 design 정정(착수 조건)이지 card가 요구하는
  판정 예외가 아니고, 승인 기록 여러 줄을 단 선례가 있다(`20260929-probe-engine-dup` 3줄, `20260930-restore-plan-functions` 3줄).
* 계획 N6.2 `2`(1017행)의 "PASS 후 옛 함수 삭제" 문장은 승인 범위 밖이다(승인 기록 '덮지 않는 것: 계획 N6.2 문장'). Phase 2 DoD는 design E1이 이 문장의 측정식이므로 이 card에서
  계획을 고치지 않는다.

## 작성 전 실측

(재측정 HEAD = gate `master` cd64170, 2026-09-30. 초안 base 070cf69 이후 바뀐 것: SD는 DF-36의 `save_instance_json` 부근(8964행 뒤) 한 곳만, SR·레지스트리·library·계획서·
`workspaces/run_harness.py`는 불변, design 20은 6398a28 정정, 승인 기록 2개 추가. 명령은 저장소 루트에서 읽기 전용, python은 `C:\Python314\python.exe -B`.)
1. 사실 문장 재측정: `grep -n "def kcl_series_union\|def _kcl_and_matching_edges\|^_RAIL_NETS\|kcl_series_union(\|_kcl_and_matching_edges(" A/stick_diagram.py A/sizing_recipe.py` → SD 2983 `_RAIL_NETS`,
   3003 `kcl_series_union`, 3134 `_kcl_and_matching_edges`, 호출 SD 3206(`audit_vertical_stack_id_vs_kcl`, def 3158)·3291(`propose_vertical_stack_id_gap_fill`, def 3261), SD 7310(`_kcl_branch_map`,
   def 7304)·SR 8055(`_build_theta_evaluator`, def 7930). `load_topology`(def 8550)가 SD 8643에서 `propose_vertical_stack_id_gap_fill`을 부른다. `sed -n 3015,3055p`·`3138,3156p` →
   두 엣지 규칙 줄 단위 동일. `sed -n 4293p;4305,4310p A/sizing_recipe.py` → 레일 튜플 4293, 부호 4307·4309, 엣지 생성 없음(`_metric_kcl_residual` def 4267).
   `grep -n '"kcl_residual"' A/library/*.json` → 파일럿 1998 하나. `grep -c _RAIL_NETS A/stick_diagram.py` → 18. scratch `p9_diff.py`·`p9_railtwice.py` HEAD 재실행 → 출력이
   070cf69 때와 바이트 동일(9회로 × 2입력 18/18 equal, `_TEMPLATE` 로드 실패, 레일 이름 넷 정확히 2회 사용은 `two_stage_ota`의 `gnd`뿐).
   레지스트리: 43(§2 KCL 엣지, '(stick_diagram 3148행)' -- HEAD에서 맞고 병합 뒤 낡음), 308·428·472·473·474행 내용 확인, `reg_check.py` exit 0('발견 0').
   design 20: 134(§6.2)·136(차등)·193(§8 P9, slug `p9-kcl-edges`)·196(판정 유형 문장)·218(E1, 명령 `PT <iso>/…/tests/contracts -k "dup_w_calc or dup_kcl_edges"`).
2. 이름 충돌: 새 test `A/tests/contracts/test_dup_kcl_edges.py` -- E1의 `-k "dup_w_calc or dup_kcl_edges"`에 모듈 이름으로 걸린다(P8 `test_dup_w_calc.py`와 같은 방식). `ls A/tests/contracts/`에
   같은 이름 없음. `grep -rn "glob(" A/tests/` → `*.py`(엔진·tests 전수 스캔), `probe_*.py`·`test_probe_*.py`·`*.topology.json`(HEAD에서 `test_df36_instance_relpath.py:58` 추가 -- library 전용),
   `*.md`(tools) 패턴과 겹치지 않음. `*.py` 전수 스캔 test(`test_ts3_no_print_verdicts`, `test_d_delete_dead`·`test_d_delete_telescopic`의 GONE, `test_d_move_tests` 소비자 검사,
   `test_ic_markers_match_plan`의 contracts `*.py` IC 표식 스캔)는 새 파일을 판정 대상으로 읽을 뿐 -- 새 test는 print 판정 금지·삭제 이름 AST 참조 금지·IC 표식 없음을 지킨다.
3. 원칙의 계약화: 정본 topology 무관(이름 리터럴 추가 0, 레일 이름 규칙을 영구 test 계약으로 삼지 않음, 정본 후보 상태 유지) → 계약 5(a)~(d)·8(a). 만들면 배선 → 계약 6.
   equivalence 규칙 문장(계획 680·686·838행) → 계약 1·6(b)를 auditor 측정으로.
4. 쓰기 경로(계획 N3.12.2, 599-640행): `A/stick_diagram.py`(599행)·레지스트리(603행) = gmid-code-author, `A/tests/contracts/test_dup_kcl_edges.py`(618행) = gmid-test-author(소스 열람 없이
   interface card만 -- interface card에 `stick_diagram.kcl_series_union`·`stick_diagram._kcl_and_matching_edges`·`stick_diagram.Transistor` 시그니처를 싣는다), DIFF-DUP·E-LIB·E-INST·계약 1·3(a)·5(a)(b)·6·7
   AST 대조와 판정 기록(621-622행) = auditor. design 정정은 이미 gate에 있다(6398a28).
5. 계획서 소비자: 지우거나 바꾸는 이름 없음. `grep -rn "kcl_series_union\|_kcl_and_matching_edges\|_metric_kcl_residual" docs/01-plan docs/02-design` → 계획 523(MOD3 목적지 -- 그대로 맞음),
   history(이력, 불변), design 20 :88·134·136·193·218(정정본과 이 card 일치), specs `20260922-ic5-gate-docstrings.interface.md:98`·`20260923-probe-promote-consistency.*`(이력, 불변).
6. 미배선: 새 def 없음. `_kcl_and_matching_edges`는 이미 운영 경로(`load_topology` → `propose_vertical_stack_id_gap_fill`, SD 8643)에 있고 이 card로 호출자가 하나 는다. V7 면제 불필요.
7. 기존 계약 test: `grep -rni "kcl" A/tests/contracts/` → `test_ic5.py:59`(`audit_vertical_stack_id_vs_kcl` 영역 표기 -- 이 card가 바꾸지 않음) 하나. `test_reg_check.py::test_main_on_this_repository_is_clean`은
   레지스트리 §7만 본다(§2·§4·§5·§6 수정과 무관, 계약 8(d)로 확인). 조정 불필요, V5 없음.
