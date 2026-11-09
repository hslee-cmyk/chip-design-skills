# 계획 v6.31 정오 + design 41 v1.12.8 재검증 (독립 검증자, 2026-10-22)

- 대상
  - 계획: `wt/plan-o94` plan/o94 `1d76ea5e`·`eb16c7e7` (base master `627eec63`) -- plan.md 3·11·332(N2.1 O-94 행)·449(N3.3)·522(N3.6 4행)·1515(N6.6 범위 4)·1521(완료 조건 (11)(d)), history.md H1 v6.31 행
  - design: `wt/design-o94` design/o94 `9a24b676`·`ad3e93b1` -- design 41 17·753·756·757·813행
  - 승인 기록 `wt/integ-it12/.ai/approvals/20261022-it2a-o94-ext.md`, 사용자 결정 O-94(`_drafts/user_decisions.md` 끝 줄), 앞 검증 `design41_v1128_validation.md`
- 실측: `wt/it2a-code` `973daf49`를 `git archive`로 scratch에 풀고 정오 문언대로 모의 구현(프로젝트 파일 수정 없음)
  - scratch: `C:\Users\HSLEE\AppData\Local\Temp\claude\C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills\63c6146a-ab1d-4035-a169-bae810986922\scratchpad\recheck631\` (`e/` 모의본, `full_e.txt` 전체 결과, `probe.txt`), 패치 스크립트 `scratchpad\recheck631_patch.py`
  - 모의 내용: `seal.py` 모듈 상수 `SEAL_ITEM_BLOCKS` + extras 블록 키 지역 매핑(키 집합 ≠ 상수면 예외) + `base` 기본값 없는 필수 키워드; `seal_versions` base None → TypeError, `if base is not None` 분기 삭제; `kernel_run` keep에 `{b.name for b in SEAL_ITEM_BLOCKS}`; test 7곳 `base=ctx.base`; `test_empty_calls_pass` base = 그 스냅샷; `test_size_and_seal` 두 함수 기대 = reuse 12(EVAL13[:12])·`dc_seal_report` graft 1·reuse 0
- 점수 **91/100**, 판정: **계획 v6.31 병합 가능 / design v1.12.8은 G-1 한 줄 보완 후 병합 가능(조건부)**

## 1. 앞 검증 지적 해소 여부

| id | 지적 | 해소 | 근거 |
|---|---|---|---|
| S-1 | 계획 N3.3·N3.6 4행·N6.6 범위 4·(11)에 '부르는 블록 = 봉인 4 호출 목록, 보고서 제외' 정오 | **해소**. 세 자리 모두 정의 삽입, (11)(d) 추가, 보고서 제외는 N3.3에 '원래 취지와 다름(작음), 승인 O-94 (2)' 표시, N2.1 O-94 행·history H1 v6.31 행 있음 | plan.md:449·522·1515·1521·332, history.md:1419 |
| S-2 | base 추가 test 호출 6 → 7곳(`test_seal.py:163` 포함) | **해소**(승인 기록 3항이 7곳을 줄 번호로 열거, :163 이유 명시). design은 '승인 기록 몫'으로 넘김(17행) | 20261022-it2a-o94-ext.md 범위 3 |
| R-1 | extras 블록 키 매핑 | **해소**. 753: 블록 객체 키 지역 매핑, 순서 = 상수, 키 빠짐·상수 밖 키 예외 | design:753 |
| R-2 | base None 거부·건너뛰기 분기 삭제 | **해소**(design 756·계획 522). 단 거부 형태 미지정·L11 누락 → 아래 G-1 | design:756, plan:522·1521 |
| R-3 | 실패 부분 스냅샷 사실 한 구절 | **해소**(사실·백로그 문구). 단 백로그 id 없음·취지 표시 없음 → 아래 N-3 | design:753 |
| N-2 | '셋' → 함수 둘·항목 넷 | **해소** | design:757 |

새로 생긴 모순: 아래 G-1(계획 (11)(d) 일부가 design L11에 없음), N-1(계획 (11)(a) 용어). 그 밖 없음.

## 2. 계획↔design gap (현재)

| 계획 자리 | 계획 결정 | design | 판정 |
|---|---|---|---|
| N3.3 (449) | keep = base writer ∪ 봉인 4 호출 목록(커널 ∪ 봉인 항목), 보고서 블록 keep 밖·S3 graft, eager | 753 같은 집합, 정본 = seal.py 상수 하나, 보고서 제외 이유·취지 표시 | 일치 |
| N3.6 4행 (522) | coverage·서로소, 호출 블록 = 봉인 4 호출 목록, base 필수·None 거부 | 756 (3)(4), `seal_dc` base 필수 키워드, `seal_versions` None 거부·분기 삭제 | 일치(거부 형태 미지정 -- G-1) |
| N6.6 범위 4 (1515) | 같은 정의 괄호, 착수 실측 | 753·757 | 일치 |
| (11)(d) (1521) | (가) 봉인 항목 reuse(커널만 keep이면 red) (나) 보고서 graft(keep에 넣으면 red) (다) computes 0 (라) **봉인 4에 base None → 거부(건너뛰면 red)** | L11 (d)(813): (가)(나)(다)만 | **G-1: (라) 누락** |

- **G-1 (필수, 작음)**: 계획 완료 조건 (11)(d) 끝 '봉인 4에 base 없음(None)을 주면 거부(건너뛰면 red)'가 design L11 (d)에 없다. 승인 기록은 그 test를 '허용'만 하므로 test 작성자가 빠뜨려도 완료 판정이 걸리지 않는다. 또 design 756은 '거부'의 형태(예외 종류 또는 `SEAL_FAIL`)를 정하지 않아 test가 단언할 계약이 없다.
  - 제안: design 813 L11 (d) 끝에 "`seal_versions(snapshot, calls, None)`·`seal_dc(…, base=None)` → `TypeError`(건너뛰어 pass면 red)"를 더하고, 756 '거부'를 'TypeError(호출 계약 위반 -- B-T16 필수 키워드 누락과 같은 종류)'로 적는다.
  - 원칙 점검: 계획부터(계획엔 이미 있음 → design만 보완), 게이트가 실제로 거부함을 test로 확인(우회 금지), 기준 약화 아님. 새 필드·cache 없음.
  - 근거: plan.md:1521 (11)(d) 끝 구절, design:813·756, 모의 `probe.txt`(None → TypeError 3경우 확인).

## 3. 계획 내부 정합 (grep '부르는 블록'·'호출 블록'·'seal_versions'·'base writer'·'커널 블록')

- 옛 좁은 정의('keep = 커널 블록만')나 '봉인 4 base 생략 가능'을 말하는 자리: **없음**. 345행(N2.1 O-61 행 '그 평가의 호출 블록')은 결정 기록 원문이라 그대로 맞다. 449 뒤쪽 '봉인 4가 … 그 평가의 호출 블록'은 같은 문단 앞 정의를 받는다.
- **N-1 (권고)**: (11)(a) "parent에 **커널 밖 writer** 필드가 있어도 child 스냅샷 커밋에는 그 필드가 없음"(plan.md:1521). v6.31이 '커널 블록 ∪ 봉인 항목 블록'으로 '커널 블록'을 좁게 쓰기 시작해, 글자대로 읽으면 봉인 항목 블록(커널 밖, 그러나 keep)과 (d)가 충돌한다. design L11 (a)는 `dc_window_refine`로 구체화해 문제 없음.
  - 제안: (11)(a) '커널 밖 writer' → '봉인 4 호출 목록·base writer 밖 writer(예 `dc_window_refine`)'.
  - 원칙 점검: 용어 하나 = 정의 하나(규칙 3), 문언 정밀. 근거: plan.md:1521, plan.md:449 정의 문장.

## 4. R-1·R-2 실현 가능성과 소비자

- R-1 지역 매핑: `seal_dc` 호출마다 만들고 버리는 인자 묶음(lut·resistances·linear_devices 참조)이다. 실행·평가 사이에 남지 않고 graph 필드 값의 사본도 아니며 sctx 슬롯·memo가 아니다 → graph 단일 정본 규칙 위반 아님. 매핑 키가 8 블록을 한 번 더 나열하지만 키 집합 = 상수 단언(예외)이 매 호출 지키므로 둘째 정본이 아니라 대조된 결합표다. import 방향 `kernel_run → seal` 단방향(순환 없음, 모의 import 성공).
- R-2 분기 삭제의 호출자 전수(`git grep 'seal_versions(' / 'seal_dc('`, `973daf49`):
  - `seal_versions`: 엔진 `seal.py:54` 하나(+ CONTRACT.md:558 문서), test `test_seal_versions.py` 12곳 -- 모두 스냅샷을 넘김(None 0). `:55` `test_empty_calls_pass`는 O-94 (1)대로 base = 자기 스냅샷.
  - `seal_dc`: 엔진 `kernel_run.py:101`(base=base), test 7곳(`test_seal.py:21`·`:163`, `test_scc_newton.py:791`, `test_seal_conduction.py:218`·`:227`·`:303`·`:375`) -- 지금은 기본값 None으로 (3)(4)를 건너뛰고 있었다.
  - `if base is not None` 분기는 code 작성자가 `867d6455`에서 넣은 것(그 앞 `seal_versions(snapshot, calls)`엔 없음) -- history v6.31의 '작성자가 넣은' 서술 맞음.
- **핵심 실측(앞 검증이 재지 않은 것)**: 7곳에 `base=ctx.base`를 넣으면 그 단위 test들이 처음으로 coverage·서로소 단언을 받는다. 모의본 전체 실행 결과 **3714 pass / 8 fail**이고, 8 fail은 모두 `metrics/test_verified_by.py::test_oracle_measure_key_exists_in_oracle_sources[...]`(앞 검증에서 src·errata 공통이던 기존 실패, 이번 변경과 무관). 즉 7곳 단위 test·`test_empty_calls_pass`(base=스냅샷)·`test_size_and_seal` 넷(reuse 12·graft 1)·`test_seal.py:163` 모두 통과하고, 분기 삭제로 깨지는 호출자 없음. 근거 `recheck631/full_e.txt` 마지막 줄 "8 failed, 3714 passed".
- 문서 소비자(code 작성자 몫, 참고): `E/sizing/CONTRACT.md:119·554·558`의 `seal_dc`·`seal_versions` 서명 문구에 base 필수·None 거부 반영 필요.

## 5. graph 단일 정본 규칙 점검 (별도 항목)

1. 계산값은 graph 필드만 -- 새 필드·둘째 생산자 없음. keep은 `ctx.base.block_versions`와 seal.py 상수(정적 블록 선언)에서 읽음. 통과
2. 재사용 두 길 -- 봉인 항목 graph reuse, `dc_seal_report` S3 graft. 새 cache·memo·sctx 슬롯·EvalResult 값 칸 없음(R-1 매핑은 호출 지역 인자). 통과
3. 같은 정의 한 필드 -- 해당 없음. 단 용어 '커널 블록'의 두 뜻(N-1)은 문서 차원 정리 권고. 통과
4. 참조 전달 -- `base` 스냅샷 참조 전달, 사본 없음. 통과
5. 스냅샷 파생 규칙 -- keep = base writer ∪ 봉인 4 호출 목록, 서로소 단언 실측 pass, `_CONTEXT_WRITERS` 미사용. 통과
6. 정본 자리 -- 봉인 항목 구성원 = seal.py 상수 하나. 통과
7. 우회 -- base None 길 차단(계획·design), 단 L11 test 의무화는 G-1. 조건부 통과

## 6. '원래 취지와 다름' 미표시 점검

- 보고서 블록 keep 제외: 계획 N3.3·N2.1·design 753·history 모두 표시. 맞음.
- **N-3 (권고, 표시 누락)**: 실패 경로 부분 스냅샷(design 753 R-3 구절). 계획 N3.3은 keep 밖을 지우는 근거로 "'없음'이 '낡은 값'보다 안전 -- fail-closed"를 적는데, v1.12.8로 봉인 항목 k에서 후보 실패가 나면 부분 스냅샷(`exc.partial`, 실패 줄 `snapshot_fp` = `search/kernel.py:90`)에 k+1..8 봉인 항목 필드가 parent 값으로 남는다(v1.12.7 keep에서는 '없음'). 커널 블록에 이미 있던 성질의 확장이고 값 판정에는 안 쓰이지만, 계획이 든 원칙과 반대 방향이라 '원래 취지와 다름(작음)'으로 표시하거나 계획 N3.3 한 구절로 '부분 스냅샷은 봉인 4를 거치지 않는 진단 기록이라 이 원칙 밖'이라 적어야 한다. 또 design의 '백로그로 분석한다'에 백로그 id가 없다(`_drafts/backlog_additions.md` grep 0).
  - 제안: design 753 R-3 구절에 '원래 취지와 다름(작음)' 또는 계획 N3.3 예외 구절 + 백로그 id 등록.
  - 원칙 점검: 원래 취지와 다른 판단은 반드시 보고(2026-10-15), 원칙 충돌은 충돌로 올림. 근거 design:753, plan:449('없음'이 '낡은 값'보다 안전), seal.py:50-51, search/kernel.py:90.
- **N-4 (참고)**: 사용자 결정 O-94 (3) 원문은 'seal_dc 호출 6곳', 승인 기록은 7곳. 기계적·강화 방향이고 기록이 S-2 근거를 적었으므로 약화 아님. 다만 사용자 문언과 수가 다르므로 user_decisions O-94 행에 '7곳(검증 S-2)' 주석을 남기면 추적이 맞는다.

## 7. 기타

- **N-2 (참고)**: design front matter `version: 1.12.7`·`plan_version: 6.28`(design:3·4)이 본문 v1.12.8·계획 v6.31과 다르다. 올릴 것.
- 계획 머리말(11행)·N2.1 행·history 경위·바꾼 옛 문장 목록은 실제 diff와 일치(eb16c7e7은 '짝 design 41·40·42' → '41(design/o94)' 표기 정정만).

## 8. 수정 제안 요약

| id | 등급 | 제안 | 원칙 점검 | 근거 |
|---|---|---|---|---|
| G-1 | 필수(병합 전, design) | L11 (d)에 base None → TypeError 단언(건너뛰면 red) 추가, 756 '거부' 형태 = TypeError 명시 | 계획 결정 design 누락 금지, 게이트 실거부 확인 | plan:1521, design:756·813, probe.txt |
| N-1 | 권고(계획) | (11)(a) '커널 밖 writer' → '봉인 4 호출 목록·base writer 밖 writer(예 dc_window_refine)' | 한 용어 한 정의 | plan:1521·449 |
| N-3 | 권고(취지 표시) | 실패 부분 스냅샷의 parent 값 잔존을 '원래 취지와 다름(작음)' 표시 또는 계획 예외 구절, 백로그 id 등록 | 취지 다름 보고 | design:753, plan:449, search/kernel.py:90 |
| N-4 | 참고 | user_decisions O-94에 7곳 주석 | 승인 추적 | approval 범위 3, user_decisions O-94 |
| N-2 | 참고 | design front matter version 1.12.8·plan_version 6.31 | 문언 정확 | design:3·4 |
