---
id: 20261021-it2a-snapshot-derive
phase: 해당 없음 (DEC-86 -- merge_gate 미사용, N6.3 절차)
evidence_type: red-green
gate_change: no
approval: 20261021-it2-o67-scope, 20261022-it2a-seal-signature-ext, 20261022-it2a-o94-ext
---

> **[상태 표지 2026-10-29] 완료 이력** -- IT-2a 판정 PASS(`integ/it12:.ai/verification/20261021-it2a-snapshot-derive.json`, code `bddef887`), master 미병합. 이 master 사본은 판정 전 동결본이다 -- 판정한 판(approval `20261022-it2a-seal-signature-ext`·`20261022-it2a-o94-ext`, keep = base writer ∪ 봉인 4 호출 목록)은 `integ/it12`에 있고 통합 병합 때 그 판으로 바뀐다. 후속 = card IT-2e(계획 v6.38.4 N6.6 범위 5 -- 같은 집합식을 함수 하나로, spec card 미작성). 본문은 기록이며 덧대지 않는다(O-169).

## 의도

- **절차(phase)**: 계획 DEC-86(285행)·N3.12 머리(669행)로 역할 분리 gate·spec card 흐름·merge_gate가 꺼졌다. 판정 = N6.3(매 변경 뒤 새 test 전체 실행, 작성자 ≠ test 작성자 WP-13, 약화 보고, 변경당 커밋 1) + 독립 측정·검증 agent이고 merge_gate가 아니다. 머리 블록은 형식 호환용이다(공통 문서 '절차 상태').

card IT-2a -- 스냅샷 파생 규칙. 범위: design 41 4.7-3c(41:750-756) -- 계획 N3.3 '스냅샷 파생 규칙'·N6.6 범위 4·완료 조건 (11), 사용자 결정 O-59 (2)(원래 취지와 다름, 승인)·O-61 P1. 앞 card = IT-1 code. 뒤 card IT-2d의 커널 밖 writer(`dc_window_refine`·`metrics_icm_front`) 필드와 IT-2c의 봉인 뒤 블록(`ss_nodal`·`icm_config`) 필드가 parent → child로 낡은 채 실리지 않게 하는 전제다.

- 공통: card base·경로 접두·사용자 결정 원문·병합 관계·착수 조건·절차 상태·graph 단일 정본 계약 G1~G7 정의·정의 불능 code·판정 분해능·S-OS1/S-OS2·작성 전 실측 1~13·승인 기록 초안은 `docs/02-design/specs/20261021-it2-common.md`(옛 IT-2 단일 card 본문, 내용 불변)에 있다. 이 card는 그 가운데 아래 범위만 판정한다.
- 나눔 근거: 사용자 결정 O-69 (2)(2026-10-21) -- IT-2를 IT-2a(스냅샷 파생)·IT-2b(커널 창)·IT-2c(측정 구성)·IT-2d(다듬은 창·front) 넷으로, IT-1 code 위 같은 통합 브랜치, master 병합은 IT-1과 함께 한 번(O-19 (2)). 순서 IT-1 → IT-2a → IT-2b → IT-2c → IT-2d. 나눔은 판정 단위만 바꾸고 design·완료 조건은 그대로다.
- 이 card는 **동작 변경**(design 41 4.7-8). `E/` = `skills/analog-gmid-design/gmid_engine/`, `41:n` = design 41 v1.12.3 줄(master `468e6e73`); 현 base design 41 v1.12.4(master `0de6a34a`)에서는 735행 이상 +1 -- '(v1.12.4)' 표시 줄은 새 판 줄. 공통 문서 '동결 갱신' 참조.

## 관찰 가능한 계약

- `run_kernel` parent 분기 = `parent.snapshot.derive_child(keep)`, keep = base writer(`ctx.base.block_versions` 키 -- 그 매핑에서 읽음, 사본 목록 금지) ∪ **봉인 4가 받는 호출 목록의 블록 이름** = 커널 블록(`steps`·`later` 목록에서 읽음) ∪ 봉인 항목 블록 여덟(`E/sizing/seal.py` 모듈 상수 하나 -- 블록 객체 tuple, `seal_dc` 호출 순서와 keep이 모두 그 상수를 읽음, 이름 사본 금지; extras는 `seal_dc` 안 블록 객체 키 지역 매핑, 키 누락·초과는 예외)(design 41 v1.12.8 753, 계획 v6.31 N3.3, 사용자 결정 O-94 (2)·O-95). `dc_seal_report`는 keep 밖 → 같은 입력이면 S3 graft(원래 취지와 다름(작음), 승인 O-94 (2)). 실패 경로 부분 스냅샷의 parent keep 필드는 이 card에서 바꾸지 않음(백로그 B69). `_CONTEXT_WRITERS`(`E/search/search_context.py:44`)는 옮기지도 읽지도 않는다(O-61 P1).
- `GraphSnapshot.derive_child(keep_writers)`: writer ∈ keep인 필드와 그 writer의 `block_version`만 남긴 새 스냅샷(권한표·구조 공유, eager -- '없음'이 '낡은 값'보다 안전).
- parent 일치 검사(`kernel_run.py:73`)를 base writer 전부로 넓힘, 어긋나면 `ValueError`.
- `seal_versions(snapshot, calls, base)` 끝에 (3) coverage(모든 필드 writer ∈ base writer ∪ calls, 위반 detail `("foreign_writers", 정렬 tuple)`) (4) 서로소(base writer ∩ calls = ∅, 위반 detail `("base_call_overlap", 정렬 tuple)`) -- 어느 하나 위반이면 `SEAL_FAIL`. 기존 (1)(2) 그대로. `seal_dc`는 `run_kernel`에서 `ctx.base`를 넘겨받는다 -- `seal_dc`의 `base`는 기본값 없는 필수 키워드, `seal_versions`·`seal_dc`에 base None이면 `TypeError`, `if base is not None` 건너뛰기 분기 없음(design 41 v1.12.8 756, O-94 (3)).
- `E/sizing/CONTRACT.md` 서명 문구(재검증 참고 `:119·554·558`)에 base 필수 반영.
- 판정 단언 L11 (a)(b)(c)(d)(design 41 v1.12.8 L11).

graph 단일 정본 검사(이 card 범위): G2(새 cache·사본 목록 0 -- keep은 `ctx.base.block_versions`·호출 목록에서 읽음, `git grep` 상수 writer 목록 0), G5(스냅샷 파생 -- L11), G7(같은 θ ss 재평가 graft·`computes` 증분 0 -- L11 (c)). 새 graph 필드 없음(G1·G3·G4·G6 해당 없음 -- 감사가 '해당 없음'을 확인).

정의 불능 code·S-OS1/S-OS2·판정 분해능 문언은 공통 문서 해당 절이 정본이다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `gmid_engine.core.graph_snapshot` | `GraphSnapshot.derive_child` | `def derive_child(self, keep_writers) -> GraphSnapshot` |
| `gmid_engine.sizing.seal_versions` | `seal_versions` | `def seal_versions(snapshot, calls, base)` |

## 판정 유형 근거

red-green. 새 이름은 존재 부재 red(`ImportError`·`AttributeError` -- 00-common §8.1, '신규 시그니처' 표 대조), 행동 red는 시그니처 불변 진입점이 맡는다(새 키워드 직접 호출 `TypeError`는 red로 세지 않는다). 결정성 비트 동일은 감사의 equivalence 측정(같은 head 두 번).

## oracle 종류와 출처

(손) 이름 없는 toy 연결의 손계산(design 41 4.7-7), (식) design 식 그대로, (비교) 같은 스냅샷 필드로 부른 같은 순수 함수의 두 경로 같음, (독립) `RunCounters`·perf 증분·`git grep`. 피검 함수로 기대값을 만들지 않는다. SPICE 다리는 **보류**(card EO-1, 41:816).

## library 회로 적용 여부

적용(동작 변경). 감사가 9회로 변화표(원인 칸 = card 0 IT-0 기록 대비, 41:816 (1)~(7))·결정성·G-10 9회로 0을 잰다. 회로·소자·넷 이름 코드 0(EP-1).

## 거부해야 할 입력

- base writer 버전이 `ctx.base`와 다른 parent → `ValueError`.
- 봉인 4 위반 픽스처 둘 → `SEAL_FAIL`(`foreign_writers` / `base_call_overlap`) -- **'통과'가 아니라 '실제로 거부'를 먼저 확인**.

## 무동작 판정 입력(무발동 값)

parent 없는 평가(스냅샷 = `ctx.base`)는 봉인 4를 통과한다(keep을 옛 `_CONTEXT_WRITERS`로 구현하면 red). 커널 블록 값·front 결과는 바뀌지 않는다 -- 9회로 결과 비트 동일(제외: ss 블록 outcome `reuse` → `graft`, `dc_seal_report` outcome `reuse` → `graft`, 블록 계수 칸; 봉인 항목 블록 여덟은 `reuse` 그대로).

## 재현할 수치

없음(계수 증분 0과 detail 문자열).

## 결정 필요 항목

없음(U-1은 O-69 (2)로 결정). 착수 조건(공통 문서): IT-1 code 커밋, card 0 IT-0 기록. C-5는 해소됨(design 41 v1.12.4 735행 `_transfer_resolution`, 사용자 결정 O-72 (1)) -- IT-2c code 착수에는 대신 IT-2c 착수 실측 (a)~(c) 기록(공통 문서 'IT-2c 착수 실측')이 필요하다. 그 밖 design에 없는 판단은 멈추고 보고.

## code 작성자 멈춤 조건

- C-4(41:756 (iii)): parent 없는 평가 스냅샷(`ctx.base`, 탐색 경로 `base = dc_ctx.base.widen(S0_WRITERS)` 뒤 S0 블록 포함)의 writer 가운데 평가 θ를 읽는 writer가 있으면 멈춤(서로소 전제 깨짐).
- 착수 실측 41:756 (i) ss 블록 `reuse` 계수 단언 search test 목록(→ `graft`, 변화표·test 주체), (ii) S3 색인 등록이 빠지는 ss 실패 경로(있으면 변화표), (iv) `lift_s1` writer 귀속 불변(확인됨).
- 공통 멈춤: design에 없는 것을 정해야 하면 멈추고 보고(as-built 결정 금지), 정본 자리가 없으면 만들지 않는다(CLAUDE.md graph 단일 정본 규칙 6, 공통 문서 C-7). 범위 밖 하위 card의 일을 당겨오지 않는다.

## test 작성 주체 몫(code 주체는 고치지 않는다)

- 41:756 (i)의 ss 블록 `reuse` 계수 단언 search test → `graft` 기대(변화표에 적음, 약화 아님).
- 승인 기록 `20261022-it2a-o94-ext` 범위 1~3: `test_empty_calls_pass` 픽스처 base = 그 스냅샷, `test_size_and_seal.py` 4항목 DC 열세 블록 기대 = computes 0·reuse 12(커널 4·봉인 항목 8)·graft 1(`dc_seal_report`), 단위 test `seal_dc` 호출 7곳 `base=ctx.base`.
- 새 test: `tests/core/test_graph_snapshot.py`(있으면 그 파일)에 `derive_child`, `tests/sizing/test_kernel_run.py`·seal test 파일에 L11.

## 작성 전 실측

공통 문서 '작성 전 실측' 1~13을 따른다. 이 card 사실(master `468e6e73`, 2026-10-21): `E/sizing/kernel_run.py:72-75`(parent 분기·`PLAN_WRITERS` 검사), `E/sizing/seal_versions.py:14`(`seal_versions(snapshot, calls)`), `derive_child` 엔진 0건(master `468e6e73`). V3 규모(8): **미확인 (IT-1 code 뒤)** -- 착수 base(IT-1 code 뒤)에서 오케스트레이터가 `tools/gates/mutate_changed.py`로 채운 뒤 동결.

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20261021-it2a-snapshot-derive.spec.md`.
