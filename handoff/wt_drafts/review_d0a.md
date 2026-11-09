# D0a spec card 독립 검토 (`20260930-p3-move-plan-tool`, 초안 `draft_p3_d0a.spec.md` 12:46판)

검토자: 독립 reviewer(작성자 아님). 2026-10-02. 기준 gate `master` = `36e170e`(실제 저장소 HEAD = gate/master 같음).
대상: `_drafts/draft_p3_d0a.spec.md`, `_drafts/d0a_briefs.md`, 대조 `docs/02-design/features/gain-budget-gmid-sizing.30-module-split.design.md`(v8.5 승인본, `6c8287f`),
`docs/02-design/specs/_TEMPLATE.spec.md`, `_drafts/draft_p3_d0b.spec.md`(12:47판).
측정: 격리 복제본 `C:/g212/r`(`git clone --no-local --no-hardlinks`, origin 제거, 빈 hooksPath, `core.autocrlf false`, TMP/TEMP `C:/g212/tmp`), 끝에 `C:/g212` 삭제.
실제 저장소 쓰기 없음(HEAD·`status --porcelain` md5·reflog 첫 줄 시작과 같음 -- 끝 절).

## 판정

**D0a: 조건부 통과 -- B 0, S 3, minor 7.** 계약 1~10의 문언 자체(conf 포함)는 독립 재구현으로 실행 가능했고 합성 단계 21개가 card 문장대로 나왔다.
다만 **card 문언대로 구현하면 실제 트리 결과가 card·design·D0b가 적은 관찰("`upward` 0·`cycles` 0")과 다르다**(S1) -- D0a 판정에는 영향 없지만(합성 입력 판정)
**D0b에는 B**다(아래 '교차 card B'). S1~S3을 고치고 D0b 쪽 해소 경로를 정한 뒤 착수 권고.

## 측정 방법(재구현 -- 작성자 시제품 열람 없음)

* `C:/g212/mp_re.py`: card 계약 2·3 문장만 보고 `plan`을 다시 짰다(G1 공개 표면 `SourceIndex(files)`·`tree`·`units`·`global_names`·`binding_origin`만 사용, 게이트 `mod_table`·`read_section_table`·`read_tree`).
  단위 키 = 계약 2 정의(함수·클래스 이름, 문장 = 바인딩 이름 정렬 `,` 연결, 무바인딩 `<stmt:해시12>`), docstring 제외, A-0·A-1(conf)·A-2·A-3·A-4(승격·MOD7 상한, N3.10 번호만)·A-K·A-5·A-6·A-7, A-3/A-4 선착석 + 단조(올리기만) 고정점, A-7 뒤 재고정점,
  `upward`·`cycles`(MOD SCC)·`reg_mismatch`·`import_time_high`·`import_conflicts` (i)~(iv)·`mod_imports`(이름별 출처 집합).
* 트리: `36e170e`(UD-0 N3.10 개정 v8.5 + D-19 (가) 커밋됨) → **FU 대역**(`design_report.py`·`audit_current_forced.py` 첫 import 앞 `from __future__ import annotations`) →
  **G1 시제품**(`g1_kit/g1_core.py` `b3c4e391…`를 `reachability.py` main 블록 앞에 붙임 -- `install_proto.py` `5790433c…`는 `36e170e`에서 앵커 `mc print` 0개로 실패, minor m7).
* 비교 변형: (가) 계약 그대로 (나) **G1 시제품 한계 모사**(문장 단위 키를 항상 `<stmt:해시>` -- D0b 실측 3이 쓴 사슬과 같은 조건).

## 실제 트리 결과(`36e170e` + FU 대역 + G1 시제품, §6.3 `MP_ARGS`)

| 항목 | (나) 시제품 모사 | (가) **계약 그대로** | card·D0b 기재 |
|---|---|---|---|
| exit / verdict | 1 / FAIL(`reg_mismatch`만) | 1 / FAIL | 1 |
| 배정 | **403** | **403** | 403 |
| 규칙 | A-4 229·A-5 64·A-1 60·A-2 38·A-6 7·A-K 2·A-7 2·A-3 1 | **A-4 236·A-5 57**·A-1 60·A-2 38·A-6 7·A-K 2·A-7 2·A-3 1 | (나)와 같음(D0b 실측 3) |
| MOD별 | gmid_lut 8·TA 18·CSG 82·GSE 102·CM 21·TS 11·SD 110·SLC 32·IRB 17·ACF 2 | gmid_lut **7**·GSE **105**·SD **111**·SLC **30**·IRB **16**(나머지 같음) | (나)와 같음 |
| `upward` / `cycles` | 0 / 0 | **1 / 1** | 0 / 0 |
| `unassigned`·`conflicts`·`import_time_high`·`import_conflicts` | 0·0·[]·0 | 0·0·[]·0 | 0 |
| MOD7 파일 밖 MOD7 배정 | 0 | 0 | 0 |
| `reg_mismatch` | 79 | 79 | 79 |
| FU 없음(`36e170e` 엔진) `import_conflicts` | 2(IRB·TA `__future__`) | 2(같음) | 2(MOD2·MOD9) |

* (나)가 D0b 실측 3의 수치(규칙 분포·MOD별 10개·`reg_mismatch` 79·목록 0)를 **바이트 단위로 재현** -- 재구현이 맞다는 교차 확인.
* (가)의 `upward` 1 = `sizing_recipe.py::SemiEmpiricalGmIdLUT`(A-1, MOD1) → `sizing_recipe.py::_QUERY_CACHE_MAX`(A-4, MOD4), `cycles` 1 = {`gmid_lut.py`, `gmid_sizing_engine.py`}.
  원인: 계약 2 단위 키대로면 상수 문장 7개(`_COMPENSATION_REGISTRY`·`_FEASIBLE_L_WINDOW_CACHE`·`_KNEE_L_CACHE`·`_LUT_VDSAT_ROLES`·`_L_ROLE_TARGETS`·`_QUERY_CACHE_MAX`·SD `INSTANCE_TOP_FIELDS`)가 레지스트리 행과 짝지어져
  A-5 → A-4가 된다. 그중 `_QUERY_CACHE_MAX`(레지스트리 277행, 칸 `gmid_sizing_engine.py(+ S0 LUT 지문은 circu…` → MOD4 하나)는 `SemiEmpiricalGmIdLUT._query` 몸체(`sizing_recipe.py:390`)가 읽는다.
  277행의 '책임' 칸("4D 배열 적재, shape 검증 … 캐시 dict 5종 생성")은 사실 `SemiEmpiricalGmIdLUT.__init__` 설명이다 -- 레지스트리 행 이름표가 바로 위 문장(`sizing_recipe.py:257 _QUERY_CACHE_MAX = 400_000`)에 붙은 생성 흔적.
* 해소 후보 실측(같은 사슬, (가)): ① N3.10 MOD1 `대표 대상`에 `` `_QUERY_CACHE_MAX` `` → `upward` 0·`cycles` 0·일곱 목록 중 `reg_mismatch` 80만, 배정 403(A-1 61·A-4 235)
  ② 레지스트리 277행 함수 칸을 `` `SemiEmpiricalGmIdLUT.__init__` ``로 → `_QUERY_CACHE_MAX` A-5 `gmid_lut.py`, `upward`·`cycles` 0, `reg_mismatch` 80. ①은 N3.10 개정(D-11 별도 승인, UD-0 밖), ②는 레지스트리 이름표 수정(D0b 계약 1·6 범위 밖).
* 그 밖 확인(가): 단위 키 충돌 0, 같은 키가 두 파일에 있는 단위 0, MOD10 배정 0, `--keep` 참조자 A-5 0, 고정점 순서 무관(동시 갱신 / 순차 정순 / 순차 역순 배정 같음),
  v8.5 반대 읽기(R(u) 최댓값에 `--keep` 번호 포함 + 상한 끔) 배정·규칙 같음(card 84~85행 문장 성립), D0b (d)-1 표본 25개 모두 (가)·(나) 기대 줄기와 같음(규칙도 표와 같음).

## 합성 단계(card 'oracle' 절 -- plan 쪽, 기대는 card 문장에서 손으로)

`C:/g212/syn.py`(합성 git 저장소 + `36e170e` `tools/gates` + G1 시제품): **21개 모두 card 문장대로**.

| 단계 | 결과 |
|---|---|
| `a1-conflict`(새) | 두 행(MOD2·MOD4) `f` + 레지스트리 칸 MOD4 → exit 1·FAIL, `assignment`에 `f` 없음, `conflicts` = `[{"unit":"src.py::f","mods":["m2.py","m4.py"]}]`, `unassigned`·`reg_mismatch` 0. 한 행만 → `m4.py` A-1, `conflicts`·`reg_mismatch` 0 |
| `doc-excluded` | docstring 단위 없음, 두 번째 문자열 `Expr`은 대상(`unassigned`에 1 -- 참조·참조자 없음, N3.10 밖) |
| `keep-residual` | `tool.py::helper` = `tool.py` A-K, 칸 있는 `h2` = A-4 |
| `lift-a4` | 칸 MOD2 `f` → `m4.py` A-4(`upward` 0), 칸 MOD5 `f2` 그대로. exit 1은 `reg_mismatch` 1(칸 m2 ≠ m4) 때문(minor m4) |
| `lift-cap-mod7` | 칸 MOD2 → `m2.py` 그대로 + `upward` 1, 칸 MOD7 → `m7.py` |
| `a6-ref-follow` | max(2, 5) = `m5.py` A-6 |
| `a7-isolated` | N3.10 파일 `m6.py` 두 함수 A-7, N3.10 밖 split → `unassigned` 2 |
| `monotone-seed` | 두 입력 순서 모두 `C` = `m2.py` A-5, `f` = `m2.py` |
| `import-time-high` (i)~(v) | (i) `[f, C]` exit 1 (ii) 0 (iii-a) `[f, Jcls]` exit 1 (iii-b) 0 (iv) `[TABLE, g]` exit 1 (v) 0 -- (i)(iii-a)(iv)는 다른 목록 전부 빈 목록 |
| `mod-imports-dedup` | `mod_imports[m3]`의 `_a`·`a`·`b` 출처 각 1개, `import_conflicts` 0, exit 0 |
| `mod-imports-conflict` | 같은 MOD → `x` 1, exit 1 / 한쪽만 → 0 |
| `future-mixed` | 갈림 → `__future__` 1(파일별 집합), exit 1 / 둘 다 있음 → 0 |

`check` 쪽 단계(v6 `order-*`·`shim-*`, v8.4 `import-dup`·`move-rejected`)는 재구현하지 않았다(이번 검토 범위 = 개정된 plan 규칙·conf).

## red 모양·interface card·parse_spec_card

* evidence_type `red-green`, 신규 모듈. 계약 10(모든 test 앞 도구 존재·첫 줄 JSON·`tool` 단언)대로 쓴 test는 도구 없는 트리에서 **`AssertionError`**(수집 오류·ImportError 아님) -- 같은 test에서
  존재 단언을 뺀 exit-2 test는 `python: can't open file`(exit 2)로 **공허 PASS**(`C:/g212/redshape`, 1 failed·1 passed) -- 계약 10이 필요한 이유 확인. 계획 N3.12.3 순서 3
  ('ImportError만의 실패는 신규 함수일 때만')과 충돌 없음. D0b 계약 11 (a)('test마다 자기 단언에서 red')는 D0b 행 고유 규칙이고, 기존 도구가 있는 D0b와 달리 D0a는 신규 모듈이라 머리 단언 red가 정당(선례 `test_extract_selftest.py`).
* `36e170e` `tools/gates/interface_card.py <초안> --root <36e170e 사본>`: D0a **'기존 함수 0개'**, 신규 `move_plan`(`*`)·`main` 두 행. D0b도 0개·두 표 빈 표.
* `role_paths.parse_spec_card(<초안>, expect_id)`: D0a·D0b 모두 통과 -- `phase` 3·`red-green`·`gate_change` no·`approval` [`20260930-30-module-split-design`]·절 11개(양식 `_TEMPLATE.spec.md` 11절과 같은 순서), `activated_ic_case`·`noop_activation_id` [].
  승인 기록 `.ai/approvals/20260930-30-module-split-design.md`(`36e170e`)가 109행에 D0a를 든다.

## S

**S1 -- 작성 전 실측의 실제 트리 결과가 이 card 계약의 단위 키로는 성립하지 않는다**(286~290행 v8.4 '규칙 근거 실측', 84~85행 '지금 트리 … 같다'의 전제, 의도 38행의 '두 독립 재구현' 맥락).
'`upward` 0·`cycles` 0·…·배정 403'은 G1 시제품의 문장 단위 키(`<stmt:해시>`)로 잰 값이다. 계약 2의 키(바인딩 이름)로는 상수 문장 7개가 레지스트리 행과 짝지어져 `upward` 1·`cycles` 1,
규칙 A-4 236·A-5 57이 된다(위 표). D0b는 이 한계를 '대상 행 분류(상수 7행 비대상)'로만 적었고 배정 영향은 적지 않았다. D0a 판정(합성 입력)은 그대로지만 사실 문장이 틀렸다.
고칠 것: 그 문장에 '시제품 키 한계 -- 계약 키로는 `upward` 1(`SemiEmpiricalGmIdLUT` → `_QUERY_CACHE_MAX`)·`cycles` 1' 관찰을 더하고, design §6.2 '결과' 문장(승인본)은 D0b가 재측정해 D-11 경로로 정정한다고 적는다.
(design·D0b·M card 배정 수치를 모두 이 시제품 한계로 잰 것이라 G1 시제품 `units` 문장 키를 계약 키로 바꾼 측정 키트를 먼저 만드는 것을 권고.)

**S2 -- `d0a_briefs.md`(10-01 23:14판)가 v8.4/v8.5/conf 이전 판이다.** test-author 브리프 5항은 필수 합성 단계를 'v6 … v7 …'만 적고 v8.4 10단계(`mod-imports-dedup`·`mod-imports-conflict`·`future-mixed`·`doc-excluded`·`keep-residual`·
`lift-a4`·`lift-cap-mod7`·`a6-ref-follow`·`a7-isolated`·`monotone-seed`)와 `a1-conflict`가 없다. code-author 브리프 6·7항은 D-31(docstring 제외·A-K·A-6·A-7·승격·MOD7 상한·선착석 단조)·`mod_imports`·`import_conflicts`·`import-dup`·conf를 모르고
'A-2·A-3·A-5 반복'만 적는다. 0.3은 아직 '결정 필요', 착수 조건은 'UD-0 아직 아님', auditor V10 probe에 계약 2 v8.4 항목 없음. `d0a_launch.sh`가 이 브리프 1·2·3절을 역할에게 넘긴다(373행).
D0b 브리프는 12:30에 갱신됐는데 D0a 브리프는 그대로다. card가 역할 입력의 정본이어도 브리프가 단계 목록을 '필수'로 좁혀 적으므로 누락 위험 -- 갱신 필요.

**S3 -- `mod_imports`·`import_conflicts`가 '배정 대상이지만 배정이 없는 단위'(conf 단위·미배정 단위)를 출처로 읽는 이름을 정하지 않는다.** 계약 2의 `("def", f, n)` 갈래는
'w의 배정 MOD가 k / 다른 j / w가 배정 대상이 아님' 셋뿐이다. D0b R-A2(MOD2 행에 `compute_metric`) 사본에서 이 재구현(fail-closed -- 보고)은 `import_conflicts` 2(`gmid_sizing_engine.py`·`sizing_layout_convergence.py`의
`compute_metric`)를 냈고, D0b r3 재구현은 0이었다('그 밖 목록 0'). conf가 막으려던 '두 독립 재구현이 다르게 잰 틈'이 같은 자리에 하나 더 있다. conf 문장 '들지 않는다'에 '그 단위를 출처로 하는 이름은
`mod_imports`·`import_conflicts`에서 건너뛴다(그 단위가 이미 `conflicts`/`unassigned`로 exit 1)' 또는 '충돌로 보고한다' 중 하나를 명시. D0b T-A는 `conflicts`를 먼저 단언하므로 겨눔은 그대로다.

## minor

* m1 낡은 문장: 의도 10행 'design … (초안 v8)'(지금 v8.5 승인본), 30~31행 D-19 '질문 중: (가)/(나)'(2026-10-02 (가) MOD2 결정, `6c8287f` N3.10 MOD2 행에 `rail_declaration`), 결정 필요 항목 274~275행
  'UD-0은 … 3건 + D-19만'(지금 3건 + D-19 + v8.4 보정 8건(토큰 11개) + v8.5 (h) -- D0b 의도 문장과 다름).
* m2 `reg_mismatch` 정의(104행) '목적지 셀이 MOD 파일 이름 **하나**'와 A-4 토큰 규칙('`--aliases` 키를 MOD로 바꾼 집합이 하나')의 문언이 다르다. 별칭만 있는 칸 17행 중 배정이 `theta_search`가 아닌 7행
  (`_optimize_theta_slsqp` 등 → SLC)이 읽기에 따라 들고 빠진다(base 79 대 72). 'A-4의 토큰 규칙으로 MOD 하나'로 맞출 것(D0b 관찰 79는 별칭 포함 읽기).
* m3 정하지 않은 가장자리: 같은 단위 키 둘(브리프 0.1 마지막 행 -- card 침묵), A-5에서 가장 낮은 참조자가 `--keep` 단위(도구 번호)일 때, A-6 최댓값에 `--keep` 번호를 넣는지, 레지스트리 키가 두 파일의 단위에 맞을 때.
  실제 트리에서는 모두 0(실측) -- 문장 한 줄씩(오류/규칙) 권고.
* m4 `lift-a4` 단계는 구성상 `reg_mismatch` 1(칸 MOD2 ≠ 배정 MOD4)로 exit 1이다 -- card는 `upward` 0만 적는다. test-author가 exit 0을 단언하지 않도록 기대 목록에 적을 것.
* m5 N3.10 MOD10 '대표 대상'의 백틱 `search`·`output_dir`·`instrument`·`activations_out`(인자 이름)은 A-1 식별자 토큰이 된다 -- 같은 이름의 최상위 단위가 생기면 MOD10 배정·`conflicts`. 지금 0. 관찰(백로그).
* m6 (D0b 정합) D0b 계약 11 (b) "도구가 없거나 **exit 2이면** 판정 목록 단언 전에 FAIL"은 D0a 계약 1과 맞지 않는다 -- 오류 출력도 첫 줄 JSON에 `"tool": "move_plan"`이 있어 머리 단언을 통과하고 다음 목록 단언에서
  `KeyError`(AssertionError 아님)로 끝난다. D0b 머리 단언에 `verdict != "ERROR"`(또는 exit ≠ 2)를 더할 것.
* m7 G1 키트 `install_proto.py`가 `36e170e`에서 앵커 `mc print` 0개로 멈춘다(`mutate_changed.py`가 V3 면제 묶기 `dd01d1d`로 바뀜). 다음 실측 전에 키트 갱신.

## 교차 card B (D0b)

**D0b-B -- 계약 8 멈춤 조건이 D0b base에서 발동한다.** 계약 그대로의 D0a(`plan`)는 FU·개정 적용 트리에서 `upward` 1(원천 `SemiEmpiricalGmIdLUT` = **A-1 토큰**)·`cycles` 1을 낸다 → D0b 계약 8 (a)
'원천이 A-1인 `upward`·`cycles` → N3.10 토큰 개정 diff + 별도 사용자 승인(UD-0 밖)'. D0b 실측 3 '(a)~(e) 모두 비어 있다', 재현할 수치 관찰(A-4 229·A-5 64, MOD별), 실측 2 대상 행 347(상수 7행 비대상), 실측 6 R-* 측정은
모두 시제품 키 한계 위의 값이다. test-author 착수 전에: (1) 문장 키를 계약대로 낸 측정으로 실측 2·3·5·6 재측정 (2) 해소안 선택 -- ① N3.10 MOD1 `_QUERY_CACHE_MAX` 토큰(D-11 승인 필요, 실측 `upward`·`cycles` 0)
② 레지스트리 277행 이름표 정정(`SemiEmpiricalGmIdLUT.__init__` -- 같은 결과, D0b 범위 밖 문서 수정) (3) (d)-1 표·거부 입력 표의 '그 밖 목록 0' 재확인.
공유 정의는 맞다: 판정 목록 일곱(이름·순서), exit 0/1/2, 규칙 ID 집합 9개, '레지스트리 함수 표' 정의(이 재구현 15표·372행), `MP_ARGS`, R-A2의 conf 처리(`conflicts` 1·`mods` [`circuit_metrics.py`, `topology_authoring.py`]·배정 402·`compute_metric` 배정·`unassigned`·`reg_mismatch` 없음 -- 재현).

## 정리 확인

* 스크래치: `C:/g212`만 사용, 작업 끝에 삭제.
* 실제 저장소: HEAD `36e170e` = gate/master(시작과 같음), `git status --porcelain` md5 `dcc7b56b…`(시작과 같음), reflog 첫 줄 `36e170e HEAD@{0}: commit: docs: 승인 기록 …`(같음).
