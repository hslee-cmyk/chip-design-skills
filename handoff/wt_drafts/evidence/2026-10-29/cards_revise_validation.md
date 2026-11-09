# card 개정 독립 검증 -- `cards/revise-1029` (2026-10-29)

- 역할: 독립 검증자(작성자 아님). 읽기만 함: 문서·git 쓰기 0, 이 결과 파일만 Write. git은 `git -C` 읽기만.
- 대상: worktree `wt/cards-revise`, 브랜치 `cards/revise-1029` = `49044328`·`7d7bae15`·`4fd12c14`·`e544aaa8`·`b3000af0`, base `052465ed`. HEAD `b3000af0`, 작업 트리 깨끗함.
- 기준: 감사 `card_audit_{A,B,C}.md`, `chip-design-skills/CLAUDE.md` 33항(base판: 원칙 1·2 = O-179·O-178 개정판), `user_decisions.md` O-173~O-181, master 계획 v6.38.4(`052465ed:docs/01-plan/features/gain-budget-gmid-sizing.plan.md`, 아래 `P:줄`).
- 측정 스크립트·중간 산출: `C:/Users/HSLEE/AppData/Local/Temp/claude/C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills/63c6146a-ab1d-4035-a169-bae810986922/scratchpad/cardV/`(`struct.py`·`body.py`·`ver.py`·`parsechk.py`·`full.diff`·`uniq.txt`·`lut.txt`).

## 판정: **병합 가능** -- Major 0, Minor 7(모두 비차단, 후속 정정 권고)

## 1. 동결 본문 무수정 -- 통과(실측)

- 98 파일, +630 −34. 파일 구성 = card spec 47 + interface 46 + `it2-common.md` 1 + design 3 + `_TEMPLATE.spec.md` 1.
- **삭제 34줄의 정체**: (a) 옛 대체 표지 11줄(consistency 2·b26-rail 2·IT-1 2·IT-2 공통 1·IT-2c 2·IT-2d 2 -- 모두 `> **[대체 표지 2026-10-29 -- 검증 대기]` 줄, 새 표지로 교체) (b) design 05 머리 `> **Date**` 줄 1(같은 줄에 `[폐기 -- DEC-86 …]` 표기를 끼운 교체, 나머지 문자 동일) (c) 템플릿 22줄(머리 키 4 = `phase` 자리표시·`activated_ic_case`·`_rename`·`noop_activation_id`, 작성 전 실측 2~11의 10줄, 주석 8줄). 템플릿 밖 card·design 본문 삭제 0.
- **추가 줄 전수**(`struct.py`): template 밖 모든 `+` 줄이 {표지 줄, 빈 줄, `## 변경 이력`, `- 2026-10-29 \`cards/revise-1029\`…` 이력 줄} 중 하나. 위반 0/97 파일.
- **본문 동일성**(`body.py`): 표지·이력·`## 변경 이력`·05 Date 줄을 뺀 비공백 줄 열이 base와 HEAD에서 같음 -- 다름 0/97.
- **자리**: spec 47 = 머리 블록 닫는 `---` 뒤(빈 줄만 사이), interface 46 = H1 뒤, 표지 파일당 1개. 이력 줄은 모두 파일 끝, 기존 `## 변경 이력`이 있던 11 파일은 그 절에 한 줄 추가(절 중복 0).
- 옛 파서 영향(`parsechk.py`, `tools/gates/role_paths.py:666-719 parse_spec_card`를 그대로 실행): card spec 47개 모두 base·HEAD 결과 같음(전부 ok). 엔진·tools(gates 밖)에서 `docs/02-design/specs`·이 design들을 읽는 코드 = `tools/migrate/extract_selftest.py` 주석 참조뿐(머리 표지 무관).

## 2. 표지 문언 사실 정확성 -- 통과(표본 = 우선 8 전부 + 34 card, 사실상 전수)

| 확인 항목 | 결과 | 출처 |
|---|---|---|
| '판정 기록 `.ai/verification/<id>.json`(FAIL 0)' 39 card | 39/39 존재, FAIL 0 | `ver.py`(base 트리) |
| '이 card의 커밋은 master에 병합' | `code_commit` 있는 27개 모두 base 조상, 나머지 12개(test-only, code null)도 `git log 052465ed --grep=<id>` 2~9 커밋 | `ver.py` |
| 머리 `phase:`와 표지 'Phase n' | 41/41 일치 | 표 실측 |
| 경로 `legacy/tests/tools/{reg_check,regression_runner,interleave_splits,engine_dup_scan,derive_achievable_bounds}.py`, `legacy/workspaces/run_harness.py`, `legacy/tests/contracts/{test_topology_md_sync,test_ts6_probe_relocate,test_df35_harness_paths}.py`, `legacy/tests/unit/{_library_sized_contexts,test_probe_*×6}.py`, `assets/sky130_nfet_pfet_lut_sample.npz`, `gmid_engine/authoring/rails.py` | 모두 base에 있음; `tools/gates/reg_check.py` 없음 | `git cat-file -e` |
| O-180 삭제 대상 | `data/lut-v2-only` D 목록에 sample npz·test_probe_* 6·`_library_sized_contexts`·`test_ts6_probe_relocate`·`test_df35_harness_paths`·`derive_achievable_bounds`·probes 30(32 중) 모두 있음; `run_harness.py`는 M(남음) | `lut.txt` |
| 계획 행 인용 | N6.1 '옛 Phase 처리' 0.5·1·2·3·4행(P:1244-1249), N3.11 'TS0~TS6 폐기'(P:71·769), N4.1 머리(P:1052), DEC-09 'DF-23 닫힘'(P:209), DEC-26(P:226), DEC-38·DEC-40 폐기(P:237·239), DEC-86(P:285), DEC-99(P:298), N4.2 V3 행이 v3-changed-stmt-scope 지칭(P:1078), N3.12·N4.2·N4.3 폐기 절(P:772·1068·1087), 관련 문서 표 레지스트리 행(P:41) | 모두 문언과 맞음 |
| 커밋 | `60727b06`(legacy 이동)·`07964dfe`(cards/simplify 병합, '검증 10 병합 가능 판정')·`67e7b182`(S-1 (c) 삭제)·`c237d96e`·`1451b1da` = base 조상; `bddef887`·`431d2e7b` ∈ `integ/it12`; `d95c8ff8` ∈ `card/it2c`; `e92e6b84`·`212f76a9` base 밖 | `git log`/`merge-base` |
| IT 판정 기록(`integ/it12`) | it0 base `c237d96e`, V2·V4 PASS(나머지 N/A); it1 code `14e0ca2a`; it2a code `bddef887`; it2b code `431d2e7b` -- 모두 PASS | `git show integ/it12:.ai/verification/…` |
| it2a 판정본 | approval `20261021-it2-o67-scope, 20261022-it2a-seal-signature-ext, 20261022-it2a-o94-ext`, keep = base writer ∪ 봉인 4 호출 목록 | `integ/it12` spec:6·20 |
| it2b 판정본 | `Window` 칸 다섯(:42)·helper 이동 금지(:86)·(S4-나) 확정(:83)·op_mismatch 단언 → EO-1(:95) | `integ/it12` spec |
| design 판 | master 40·41 = v1.14.2(plan_version 6.37), `design/v115` = v1.15.3 미병합 | 머리 |
| library 13·held-out 0 | base `assets/library` 13회로, `assets/heldout` 없음 | `ls-tree` |
| **LT-1·O-180 문장 병합 전후 참** | LT-1: '`legacy/`로 옮겨졌고(현재)·LT-1 뒤 tag `legacy-final`에만' -- 전후 참(계획 DEC-99·P:1142 '로컬 tag `legacy-final`로만 보존' 문언과 같음). O-180: '병합 전 `legacy/` 아래, 병합 뒤 git 이력에만' -- 전후 참. 단 덧붙인 '(LT-1보다 먼저 지워짐)'은 병합 순서 예측(Minor m4) | |

## 3. tag 이름 -- 사실

- 표지의 'LT-1 뒤 tag `legacy-final`' = 계획 DEC-99(P:298 '로컬 git 태그 `legacy-final`로만 보존')·N6.4 범위 (7)(P:1362 '로컬 tag `legacy-final` = 순서 0에서 기록한 base sha')와 일치. 아직 만들어지지 않음(`git tag -l`에 없음 -- LT-1 순서 0에서 만듦, 정상).
- 현재 tag `legacy-engine-v1` = `6df4bd7`(DEC-82 P:281, P:42·198·1142): 옛 엔진 이동 **전** 동결 기준선 tag. 계획이 정한 별개 이름이고 `legacy-final`을 대신하지 않는다 -- 두 이름 모두 계획 지정, 충돌 없음. 표지는 `legacy-engine-v1`을 언급하지 않음(정확).

## 4. IT-2 내용 개정 -- 통과

- **E-13 귀속**: P N6.35 E-13 행 소유 칸 = '**WB-1 범위 3a-0·3a**'(P:2311) -- 표지 정정과 일치. IT-2c 범위 6 = E-09·E-22(P:1594) -- 공통 (2) 목록·IT-2c 표지에서 E-13을 빼고 별문으로 옮긴 것 맞음.
- **67e7b182 반영**: P:1598 'IT-2c 착수 실측 (a) servo 피벗 a_e·δA_num (b) 진짜 A = 0 대칭 사례 하나, 옛 (c) vntol·reltol 뺌(승인 O-173 S-1)'과 일치.
- **재동결 조건 (i)~(iv)**: (i) = P:1598·O-173 S-1 (ii) = O-178 (1) ME-1·model_error 삭제(본문 `IcmWindow.model_error_ref` = it2-common:65·251) (iii) = O-181(library 13·held-out 0·A' 판정 정지) (iv) design v1.15.x 승인 뒤 = 원칙 17(design 승인 → card)과 P:1196 'design 41 §6.7-1a·40 §3.7 정정 → IT-0b'의 귀결. 결정 밖 새 결정 0. (iv)의 'ME-1 → CL-1'은 미승인 v6.38.5 문언을 조건부로 언급(m6).

## 5. 템플릿 -- 통과(Minor 2)

- 원칙 칸 정확성: 원칙 2 칸 = base CLAUDE.md 원칙 2(O-173·O-178)의 E-0·정의 동일성·가드 없음·front 최종 oracle·SPICE 수치 동일성 기준 아님·e_m 없음과 일치. 원칙 1 칸 = O-179·원칙 1 'C 열 기본'과 일치(주파수 양 한정도 원칙 1 문언 그대로). 원칙 7 칸 = fpga/CLAUDE.md 규칙 1~6 + P N6.3 '같은 입력 재계산 0 래칫'(P:1306~ 절, 기준선 래칫 문언 확인). 원칙 8·9·11·12·16·24·O-171(원칙 21 네 칸) 칸 문언 일치. 작성 전 실측 5·8 = P N6.3 'WP-13·기대값은 오라클에서만·`criteria_weakened` 필드'와 일치.
- 옛 파서 호환: 템플릿 머리 키 {id, phase, evidence_type, gate_change, approval} ⊆ `SPEC_KEYS_SINGLE ∪ SPEC_KEYS_MULTI`(role_paths.py:666-667) -- 맞음. 템플릿 자체는 id 자리표시 때문에 base·HEAD 모두 파서 거부(원래 `_` 접두로 대상 밖, 변화 없음). 단 m3.
- 폐기 절차 잔존: m2.

## 6. 작성자가 감사 제안을 바꾼 3곳 + 추가 1곳 -- 4/4 타당

| 곳 | 감사 제안 | 작성자 | 판정 |
|---|---|---|---|
| DEC-38 충돌(템플릿 쓰기 경로) | C §3.8 '…test 주체는 interface card만' | 'WP-13·DEC-86 (1)·N6.3, 기대값은 오라클에서만(N3.11)' | **타당** -- 'test-author는 interface card만 입력'은 DEC-38 옛 형태 그대로이고 DEC-38은 폐기(P:237). 작성자 문언은 P N6.3 줄('코드 작성 주체와 test·기대값 작성 주체가 다르다(WP-13). 기대값은 오라클에서만 만든다(N3.11)') 그대로 |
| O-109 D4(it2b 표지) | C §3.5 'E-09, O-109 D1' | 'N6.6 범위 6·N6.35 E-09, O-109 D4' | **타당** -- `node.dc_output_structure` 삭제의 승인 근거는 P:1594 범위 6·P:2307 E-09 행 모두 'O-109 D4'. D1은 '뿌리 아닌 입력 포트·선언 포트 `node.dc_window` 항목' 삭제(P:1589)라 다른 대상 -- 작성자는 그 문장을 뺐다(틀린 문장 없음, 열거 축소만) |
| reg_check 경로(registry-grade-fix) | B '`tools/gates/reg_check.py`로 적힌 도구는 실제로 legacy…' | '본문의 도구 `A/tests/tools/reg_check.py`는 지금 `legacy/tests/tools/reg_check.py`' | **타당** -- 본문은 design §10의 `tools/gates/` 안을 거부하고 `A/tests/tools/reg_check.py`에 둔다고 적음(spec:18-19·44·58); `tools/gates/reg_check.py`는 base에 없음 |
| 추가: df35 O-180 문장 | (감사 없음) | `test_df35_harness_paths.py`는 O-180 삭제 대상 | **타당** -- df35 card 커밋이 그 파일을 만들었고(+255), `data/lut-v2-only` D 목록에 있음 |

## 7. 원칙 위반 점검 -- 위반 0(Minor 문언 m1·m3 제외)

- 새 결정: 0(표지·템플릿 문언은 계획 행·O-번호·원칙 인용; 재동결 순서는 원칙 17·계획 순서의 귀결). 기준 약화: 0(삭제한 템플릿 항목은 폐기 절차 V3·V5·V7·N3.12.2·IC gate 키; 대체 항목이 원칙 9·18을 그대로 둠). as-built 근거: 0(엔진 경로 인용은 '어디 있나'·재작성 범위뿐, it2b 표지가 '보존 근거가 아니다(원칙 8)' 명시). 결정·선례를 근거 칸에 쓴 곳: 0(O-·DEC-번호는 '무엇이 확정됐나' 사실로만). graph 정본: 해당 없음(문서 표지, 새 필드·cache 0). heredoc: 커밋 산출물 형태로는 판단 불가 -- 결과물 바이트 검사상 이상 없음.

## Minor(비차단)

- **m1** IT-1 표지 '재동결 범위 = 범위 1 + 재작성 범위 2~5(DEC-106·E-19) + 범위 6'이 번호 체계를 섞는다: 계획 N6.5 '재작성' 절의 범위는 1~6이고 그 **범위 1(차동 입력쌍 한 점 -- DEC-106 핵심, P:1547)**이 문장에서 빠진 것으로 읽힌다. 옛 card 범위 3 나머지·범위 5(소비자 표)도 언급 없음. 권고: '재동결 범위 = 옛 범위 1(+남는 범위 3·5) + 계획 N6.5 IT-1 범위 재작성 절 범위 1~6(DEC-106·E-19·P9 B4)'처럼 출처 절 번호로.
- **m2** 템플릿 폐기 절차 잔존: 작성 전 실측 13의 '허용 예외 타입(00-common §8.1)' = 판정 기록 스키마(00-common §8 머리 'N3.12.5', 판정 기록 폐기 P:121); 주석 '신규 시그니처 표는 interface card로 옮겨진다'(interface card 폐기 P:120); 주석 '`## dispute 기록` 절(원문 인용 + blob id)'(N3.12 흐름). 다만 DEC-86 뒤 IT card가 interface card·dispute를 실제로 썼다(O-94 IT-2a dispute) -- 계획 용어표와 관행의 불일치는 이 브랜치 이전부터. 권고: '형식 호환·관행(계획 용어표상 폐기)'으로 표기하거나 줄 삭제.
- **m3** 템플릿 작성 전 실측 9 '사용자 결정(O-번호)이 `approval` 줄에 있다'는 주석의 '옛 파서와 호환' 주장과 충돌: `ID_RE = ^[0-9]{8}-[a-z0-9][a-z0-9-]*`(role_paths.py:49)가 `O-173`을 거부한다(`parsechk.py` 실측 False). 계획 P:122는 승인 기록 폐기 뒤 `approval_id`가 history H1 항목을 가리킨다고 적음. 권고: approval 값 형식을 하나로 정해 적기(예: O-번호는 본문 절, 머리 `approval`은 옛 형식 id 또는 키 생략).
- **m4** O-180 문장의 '(LT-1보다 먼저 지워짐)'(promote-clean·differential·relocate·df35 spec·interface 8 파일)은 병합 순서 예측이다. O-180 정리는 계획 v6.38.4 card가 아니고 LT-1과의 순서를 정한 문서가 없다 -- LT-1이 먼저 병합되면 거짓. 권고: '(LUT 정리가 LT-1보다 먼저 병합되면)' 또는 삭제. 나머지 문장('병합 전 `legacy/` 아래, 병합 뒤 git 이력에만')은 전후 참.
- **m5** probe-promote-clean 표지 '이 card가 만들거나 옮긴 파일 가운데 … `test_ts6_probe_relocate.py`': 그 파일은 probe-relocate가 만들고 promote-clean은 고쳤다(+84줄). '만들거나 고친'.
- **m6** IT-2 공통 (iv)·관련 표지의 'ME-1 → CL-1'은 미승인 v6.38.5 이름이다. '승인 뒤'로 조건을 달아 결정은 아니지만, 승인 전 이름은 '(v6.38.5 안)' 표기 권고.
- **m7** 커밋 `7d7bae15` 메시지에 트레일러 앞 빈 줄이 없어 `git interpret-trailers --parse`가 본문 줄을 트레일러로 읽는다(원칙 28 트레일러). 기록만(reset 금지 -- 고치지 않음, 다음 커밋부터 `--trailer`).

## 관찰(지적 아님)

- it2b 표지는 O-109 D1 몫(뿌리 아닌 입력 포트·선언 포트 `node.dc_window` 항목 삭제, P:1589)을 열거에서 뺐다 -- 틀린 문장은 없음.
- 감사 B §5 '계획 P:1349·2576 md 10개(library 6 + heldout 4)'는 O-181 뒤 낡은 계획 문언 -- 이 브랜치 범위 밖(계획 개정 몫).
