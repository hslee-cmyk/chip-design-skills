# design 41 v1.12.8 정오 검증 (독립 design-validator, 2026-10-22)

- 대상: `wt/design-o94` 브랜치 design/o94 커밋 `9a24b676` -- `docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md` 17·753·756·757·813행 (5줄 교체, 줄 추가 없음)
- 대조: 계획 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` 448(N3.3 스냅샷 파생 규칙)·521(N3.6 표 4행)·1514(N6.6 범위 4)·1520(완료 조건 (11)), 사용자 결정 O-94(`wt/_drafts/user_decisions.md` 끝 줄)
- 코드 실측: `wt/it2a-code` 커밋 `973daf49`(code `867d6455` 포함)을 `git archive`로 scratchpad에 두 벌 풀어 실행(프로젝트 파일 수정 없음)
  - `src` = 커밋 그대로, `errata` = 정오 문언대로 고친 모의 구현(아래 §2.1)
  - scratch 경로: `C:\Users\HSLEE\AppData\Local\Temp\claude\C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills\63c6146a-ab1d-4035-a169-bae810986922\scratchpad\v1128\` (`probe_src.jsonl`, `probe_errata.jsonl`, `full_src.txt`, `full_errata.txt`)
- 점수: **88/100**, 판정: **조건부 통과**(필수 수정 2, 권고 3)

## 1. design↔계획 gap

| 계획 자리 | 계획 문언 | v1.12.8 | 판정 |
|---|---|---|---|
| N3.3 (448) | keep = base writer ∪ '그 평가가 부르는 계산 블록' | base writer ∪ 봉인 4가 받는 호출 목록(커널 4 + 봉인 항목 8) | 옛 좁힘(봉인 항목 8 누락)은 해소. `dc_seal_report` 하나만 계획 글자보다 좁다 |
| N3.6 표 4행 (521) | coverage: writer ∈ base ∪ 그 평가의 호출 블록; 서로소 | 봉인 4의 `calls` = 커널 4 + 봉인 항목 8(seal.py:53-54) | 일치. 봉인 4 시점의 '호출 블록' = `calls`로 읽으면 N3.3 keep과 같은 집합 |
| N6.6 범위 4 (1514) | 착수 실측 넷 | 757 (i)에 DC 열세 블록 outcome 기대 추가 | 넓힘 아님(실측 결과 기록) |
| 완료 조건 (11) (1520) | (a)(b)(c) | L11 (a)(b)(c) + (d) 추가 | (d)는 (11) 밖 추가 red. N3.3 재사용 계약을 지키는 test라 취지 안. 계획 (11)에 반영 안 됨(아래 S-1) |

- `dc_seal_report` 제외 표시: 753행에 **'원래 취지와 다름(작음), 승인 O-94 (2)'**로 적혀 있다. 이유도 함께 적혀 있다. 봉인 4 뒤에 불려서 `calls`에 들 수 없고, 남기면 `foreign_writers`가 된다. 이 이유는 실측과 맞다(seal.py:54·57, seal_versions.py:35-36). 해석이라는 표시는 맞게 되어 있다.
- 남는 gap 하나(**S-1, 필수**): 계획 N3.3·N3.6 4행·N6.6 범위 4는 여전히 '그 평가가 부르는 (계산) 블록'이라고만 적혀 있다. design만 '봉인 4가 받는 호출 목록(`dc_seal_report` 제외)'으로 좁혀 읽는다. 사용자 원칙 '계획과 다르면 계획부터 고친다'(2026-10-16)에 따르면 design 안의 승인 표시만으로는 부족하다. 계획 문언 정오가 따로 필요하다. 넓힘 쪽 gap은 없다.

## 2. 실현 가능성 (it2a-code 실측)

### 2.1 정오 모의 구현 (scratch만)
- `seal.py`에 `SEAL_ITEM_BLOCKS = (dc_tolerances, dc_seal_node_conflict, dc_seal_vgs_match, dc_seal_kcl, dc_seal_bulk_reverse, dc_seal_saturation, dc_seal_kvl_branch, dc_seal_conduction)` 추가. `seal_dc`는 이 상수 순서로 부르고 extras를 블록 키로 짝짓는다. `base`는 필수 키워드.
- `kernel_run.py:84` keep에 `{b.name for b in SEAL_ITEM_BLOCKS}`를 더한다. import는 `from .seal import SEAL_ITEM_BLOCKS, seal_dc`.

### 2.2 같은 θ parent 재평가 outcome (probe, `ctx_c`·`ctx_passive`)

| 경우 | src(커밋 그대로) reuse/graft/compute | errata reuse/graft/compute | 봉인 4 (errata) | fp·report 같음 |
|---|---|---|---|---|
| same θ (`test_same_theta_with_parent_zero_compute`) | 4 / 9 / 0 | **12 / 1 / 0** (dc_seal_report만 graft) | pass, blocks (), n_checked 12, foreign (), overlap () | 예 |
| passive Cz만 | 4 / 9 / 0 | **12 / 1 / 0** | pass | 예 |
| passive Rz만 | 4 / 9 / 0 | **12 / 1 / 0** | pass | 예 |
| passive 둘 다 | 4 / 9 / 0 | **12 / 1 / 0** | pass | 예 |
| y 변경(0.45→0.55) parent | 2 / 0 / 11 | 2 / 0 / 11 | pass | parent 없는 같은 θ 평가와 fp·report 같음(낡은 값 새지 않음) |

- reuse 판정은 `compute_block.py:143` `snapshot.block_version(name) == version`이다. `derive_child`가 keep writer의 `block_version`을 남기므로(graph_snapshot.py:167) 봉인 항목 블록은 입력이 같으면 reuse다. `dc_seal_report`는 keep 밖이라 버전이 지워진다. 그래서 `donors.find`로 graft된다(compute_block.py:146-149).
- passive θ: `capacitance`·`ss_resistance`는 DC 블록 extras에 들어가지 않는다(kernel_run.py:76-80·100, s2_values.py:58-62). 그래서 봉인 항목의 입력 버전이 바뀌지 않는다. 실측도 reuse 12다.
- EVAL13 구성(test_size_and_seal.py:27-29) = 커널 4 + 봉인 항목 8 + report 1 = 13. 이 13에 대해 0/12/1이 나온다.

### 2.3 낡은 값이 새는 경로
- 정상 경로에서는 새지 않는다. `seal_dc`는 봉인 항목 여덟을 조건 없이 모두 부른다(seal.py:47-53). 남긴 필드는 입력 버전이 다르면 다시 계산(또는 graft)되고, 같으면 reuse로 정확하다. 이어서 봉인 4 (1)(2)가 블록마다 입력 버전을 다시 잰다.
- 예외 경로(**N-1, 관찰, 이번 정오가 새로 만든 것 아님**): 봉인 항목 k에서 후보 실패가 나면 `attach_partial`로 붙는 부분 스냅샷에 parent의 k+1..8 필드가 낡은 채 남는다. 이 스냅샷은 봉인 4를 거치지 않는다. `search/kernel.py:90`에 `snapshot_fp`로 기록된다. 같은 성질은 이미 커널 블록에도 있다(예: `dc_currents` 실패 시 parent의 `dc_columns`·`dc_widths` 필드). keep을 넓히면 이 노출 범위도 넓어진다. 부분 스냅샷 지문이 lineage에 따라 달라질 수 있으므로 design에 한 구절로 적어 두기를 권고한다(R-3).

## 3. seal.py 모듈 상수 -- 정본·import 방향
- 정본: 지금 봉인 항목 구성원·순서는 `seal_dc` 지역 tuple 하나에만 있다(seal.py:36-45). 그 tuple을 모듈 상수로 올리고 지역 tuple을 지우면 정의는 여전히 하나다. `s2_values.py:130-137`의 writer 이름 상수는 권한표용 이름이고 구성원 목록이 아니므로 사본이 아니다. 계산값이 아니라 정적 블록 선언이라 cache·memo·sctx 슬롯에도 해당하지 않는다.
- import 방향: `kernel_run.py:33`이 이미 `from .seal import seal_dc`를 한다. `seal.py`는 kernel_run을 import하지 않는다. 순환이 없다(errata 모의 실행에서 import 성공).
- **R-1(권고)**: design 753은 'extras는 상수 순서에 맞춰 짝짓고 길이 불일치는 예외'라고 적었다. 그런데 길이가 같고 순서만 어긋나면 이 검사가 잡지 못한다. 예를 들어 `dc_seal_kcl`의 `(resistances,)`와 `dc_seal_conduction`의 `(lut,)`가 자리가 바뀌어도 통과한다. extras를 블록 객체 키 mapping으로 만들고 상수 순서로 꺼내는 쪽을 권고한다(키 불일치 = 예외). 원칙 점검: 지역 인자 묶음이라 값 사본·cache가 아니다. 정본은 여전히 상수 하나다.

## 4. 영향받는 test·code 소비자 (전수 실측: sizing·core·search·metrics 3,722개, 두 벌 비교)
- src 실패 13 = dispute 5(`test_empty_calls_pass` 1 + reuse 13 기대 4) + 이전부터 있던 `metrics/test_verified_by.py` 8(두 벌 공통, 이번 변경과 무관).
- errata 실패 37 = 위 13(reuse 기대 4는 '4 == 13' → '12 == 13'으로 바뀜) + **`seal_dc` base 필수로 생긴 TypeError 24**. 위치: `test_seal.py:21`(helper, 실패 19), `test_scc_newton.py:791`, `test_seal_conduction.py:218·227·303·375`.
- **S-2(필수)**: O-94 (3)은 '단위 test seal_dc 호출 6곳에 base=ctx.base'라고 적었다. 실제로 필요한 곳은 **7곳**이다. 일곱째 `test_seal.py:163`(`test_seal_dc_run_pair_keywords_required`, B-T16)은 base가 빠져도 TypeError가 나므로 errata에서도 **통과**한다. 즉 donors·counters가 필수인지 더는 가려내지 못하는 공허한 test가 된다(실측: errata에서 pass). 이 자리에도 `base=ctx.base`를 넣어야 원래 판별력이 유지된다. design 757 (i)·O-94 확장 기록에 일곱째를 적어야 한다.
- 다른 소비자: search `test_kernel.py:253 test_parent_reuses_lineage`는 `dc_columns`·`dc_currents`의 computes만 단언하므로 영향이 없다(errata 통과). metrics `test_ss_evaluate.py:655·723` ss graft 기대도 영향이 없다(통과). integration 계수 항등식 test(`test_g10_*`, `test_run_isolation`)는 이번 실행 범위 밖이다. 다만 calls = reuse+graft+replay+compute 항등식은 outcome 배분과 무관하다.
- 문언 정밀도(N-2): 757 (i) '`test_same_theta_with_parent_zero_compute`·`test_passive_theta_only_change_zero_dc_compute` 셋'은 test 함수 2개, test 항목 4개(parametrize 3)다. O-94는 '4개'라고 적었다. '함수 둘(항목 넷)'로 맞추기를 권고한다.

## 5. graph 단일 정본 규칙 점검 (별도 항목)
1. 계산값은 graph 필드만: 새 계산값이나 둘째 생산자가 없다. keep은 `ctx.base.block_versions`와 블록 선언에서 읽는다. -- 통과
2. 재사용 두 길: 봉인 항목은 graph reuse, `dc_seal_report`는 S3 graft다. 새 cache·memo·sctx 슬롯·값 칸이 없다. -- 통과
3. 같은 정의 한 필드: 해당 없음. -- 통과
4. 참조 전달: `seal_dc`에 `base` 스냅샷 참조를 넘긴다(사본 없음). -- 통과
5. 스냅샷 파생 규칙: keep = base writer ∪ 그 평가가 부르는 블록(봉인 4 `calls`)이다. 서로소 단언은 실측 pass(overlap ()). `_CONTEXT_WRITERS`는 쓰지 않는다. -- 통과, 단 S-1(계획 문언)
6. 정본 자리: 봉인 항목 구성원 = seal.py 상수 하나. -- 통과
7. 남은 우회(**R-2, 권고**): `seal_versions.py:31` `if base is not None`이 (3)(4)를 건너뛰는 길이 남아 있다. `seal_dc(base=None)`처럼 명시적으로 None을 넘기면 필수 키워드여도 우회된다. O-94 (3) 취지('기본값 None = 봉인 4 우회 = 기준 약화')를 다 막으려면 design 756에 다음을 더해야 한다: `seal_versions`·`seal_dc`의 base None은 거부(TypeError), 건너뛰는 분기는 삭제. 현재 이 분기를 쓰는 test는 0개다(test_seal_versions.py 호출 전부가 스냅샷을 넘김).

## 6. 수정 제안 (제안 / 원칙 점검 / 근거)

| id | 제안 | 원칙 점검 | 근거 |
|---|---|---|---|
| S-1 필수 | 계획 N3.3·N3.6 4행·N6.6 범위 4의 '그 평가가 부르는/호출 블록'을 '봉인 4가 받는 호출 목록(`dc_seal_report` 제외 -- 봉인 4 뒤 호출)'으로 계획 정오. 완료 조건 (11)에 (d) 추가 | 계획과 다르면 계획부터, 원래 취지와 다름 보고(O-94 (2) 이미 승인) | plan:448·521·1514·1520, design:753·813 |
| S-2 필수 | base=ctx.base 추가 대상 6곳 → 7곳(`test_seal.py:163` 포함). design 757 (i)·O-94 확장 기록 정정 | 게이트가 실제로 거부하는지 확인(공허 test 금지), 작성자≠검증자(test 주체 몫) | errata 실측: 163 test pass(공허), TypeError 24건 |
| R-1 | extras를 블록 키 mapping으로 짝짓기(순서 불일치 방지) | 정본 하나 유지, 사본·cache 아님 | seal.py:36-45 |
| R-2 | `seal_versions`·`seal_dc`의 base None 거부, (3)(4) 건너뛰는 분기 삭제 | 우회/skip 금지, 기준 약화 금지 | seal_versions.py:31, design:756 |
| R-3 | 실패 부분 스냅샷에 parent의 뒤 블록 필드가 남는 점을 design에 한 구절로(이번 변경 밖이면 백로그) | 원래 취지와 다름 보고 | seal.py:50-51, kernel_run.py:59-61, search/kernel.py:90 |
| N-2 | 757 '셋' → '함수 둘(항목 넷)' | 문언 정확 | test_size_and_seal.py:90-96·163-176 |
