# review_kits_4a2 -- 독립 검토(작성자 아님), 2026-10-02

판정: **B 0 / S 0 / minor 4** (둘 다 진행 가능. minor는 선택 보강)

범위: (1) `_drafts/b26_1_carry.sh` 248~256행(V3 --out 대조) vs `b26_1_carry.sh.pre-4a2.bak`, (2) G1 `draft_p3_g1.spec.md`(89719c85…) vs `b758140a…`(pre-r3)·pre-4a2.bak, 승인 문안·g1_kit 양식·`g1_launch.sh` check_apr_draft·check_quote.
환경: 실제 저장소 읽기 전용(`git -C … show/grep/rev-parse`만, HEAD `4a286f0`), 모래상자 `C:/g238`(TMP·TEMP 그 아래, 끝에 삭제). 실제 저장소 status 37줄(대화 시작 스냅숏과 같음)·reflog HEAD@{0} = `4a286f0` 그대로.

## 1. b26_1_carry.sh V3 --out 대조

### 근거(card 35 @ 4a286f0 계약 4·5, 묶기 card 병합본 도구)
* 계약 5: 대상 밖 변이는 실행하지 않고 `--out`에 `{"id","result":"not_targeted"}`로 대상 레코드와 섞어 적는다. JSON은 묶기 card 키 뒤에 `not_targeted`(수)·`targets_by_def`. `mutants`(= 결과 레코드 수) = **대상 변이 수**(not_targeted 레코드는 결과 목록에 없음).
* 계약 4: 대상 밖은 면제 판정을 하지 않음 -> `exempt` 레코드는 대상 변이만. 지금 도구(`mutate_changed.py` 426~453행)에서 `exempt` 레코드는 `results`에 들어가 `mutants`에 세어진다.
* 그래서 `run = result != "not_targeted"` (killed·survived·exempt) == `mutants`, `len(recs) - len(run)` == `not_targeted` 가 계약 5와 정확히 일치한다.

### diff
bak 대비 변경은 이 한 덩어리(주석 2줄 + 단정 6줄)뿐. 나머지 595행 바이트 동일 -> `lc_repo_guard`·`lc_need_real/sandbox`·옵션 위치 가드·`set -Eeuo pipefail`+`inherit_errexit`+ERR trap 그대로.
`worktree remove`·`branch -D`는 436·439행 `echo`만, push는 `lc_push_cmd`(printf)만 -- 실행하는 줄 0(grep). 실행되는 git 쓰기는 기존 그대로 `local` 단계의 `g commit` 하나(설계상).
`local v3; v3=$(python …)` 꼴은 python 실패 시 set -e로 멈춤(같은 셸 옵션으로 실측 exit 1).

### 합성 실행(C:/g238, 추출한 heredoc 두 판을 같은 입력으로)
| 사례 | 새 | 옛 | 비고 |
|---|---|---|---|
| A01 pre-35 정상(exempt 1, nt 키 없음) | PASS | PASS | 회귀 없음 |
| A02 post-35 정상(nt 2·exempt 1) | PASS | FAIL | 옛 단정은 35 병합본 출력을 거부 -- 고칠 필요가 실재 |
| A03 nt 키 없음 / A04·A05 nt 값 1·3 / A06 "2" / A07 null | FAIL | FAIL | |
| A08 mutants=전체 레코드 수(옛 의미) | FAIL | PASS | 계약 5대로 거부 |
| A09 mutants 없음 / A10 "4" | FAIL | FAIL | |
| A11·A12·A13 id 중복(nt↔대상, nt↔생존, 대상↔대상) | FAIL | FAIL | |
| A14·A15 id·result 키 없음 | FAIL(KeyError) | FAIL | |
| A16 생존을 not_targeted로 숨김(수 맞춤) | FAIL | FAIL | 생존 = [mid] 단정 |
| A17 killed를 nt로 재분류(JSON·out 함께 자기일관 조작) | PASS | FAIL | 산출물 둘을 함께 위조하면 대조로는 못 막음(본질적 한계, 약화 아님) |
| A18 생존 2 / A25 exempt->survived / A26 killed 수 / A33 survivors 2 | FAIL | FAIL | |
| A19 미지 result "foo"(mutants 5) | **PASS** | FAIL* | *옛 단정도 pre-35 꼴이면 PASS(len==mutants만 봄) -- 회귀 아님 |
| A20 "NOT_TARGETED"(대소문자) | FAIL | FAIL | |
| A21 nt=True / A22 nt=1.0 (레코드 1) | **PASS** | FAIL | Python 1==True==1.0 |
| A23 nt 레코드에 여분 키 | **PASS** | FAIL | 계약 5 모양 미검사 |
| A24 exempt 없음 / A27 빈 줄 / A31 pre-35+nt 0 / A32 nt 0 | PASS | (post-35면 FAIL) | |
| A28 잘린 줄 / A29 빈 out / A35 비객체 줄 | FAIL | FAIL | |
| A30 pre-35 JSON + post-35 out | FAIL | FAIL | |
| A34 targets_by_def 합 불일치 | **PASS** | FAIL | 교차 대조 없음 |

결론: 정확(계약 5와 같은 셈), 옛 단정 대비 약화 없음(pre-35 입력에서 새 = 옛, post-35에서 옛은 정상 출력을 거부하던 것), 운반 절차(design 05 §12 'V5 승인 운반' -- 기록 4 diff 해시·blob 운반)와 무관한 V3 기록 5 출처 확인만 바뀜. 실제 저장소 가드·출력 전용 명령 유지.

### minor
* **m1** result 값 닫힌 집합 미검사(A19). 묶기 card + 35 뒤 값은 `killed|survived|exempt|not_targeted` 넷뿐 -- `assert {r["result"] for r in recs} <= {...}` 한 줄 권장(옛 단정도 없던 것이라 회귀 아님).
* **m2** 타입 느슨(A21·A22): `type(v.get("not_targeted", 0)) is int and type(v["mutants"]) is int` 권장.
* **m3** `v.get("not_targeted", 0)`이 pre-35 JSON을 받는다 -- 주석은 "착수 조건 6 -- 35 병합본 도구로 잰다"인데 여기서는 강제하지 않는다. 조건 6은 launch(`chk 20260930-v3-changed-stmt-scope`, draft_b26_1 478행)가 강제하므로 방어 심층 차원. `v["not_targeted"]`(필수)·`"targets_by_def" in v`로 바꾸면 35 뒤 도구 출력과 정확히 맞고 더 닫힌다.
* **m4**(선택) not_targeted 레코드 모양(키 정확히 `id`,`result`)·`targets_by_def` 합(Σtargeted = mutants, Σnot_targeted = not_targeted) 교차 대조 없음(A23·A34).

## 2. G1 spec card 초안·승인 문안

* sha256: `draft_p3_g1.spec.md` = `89719c852cdd88571e13909285ae041bbc49888f5a39968781753129ad63d8ff`, `pre-r3.md` = `b758140a…`, `pre-4a2.bak` = `d895993c…`.
* 절 단위 바이트 대조(`## ` 분할, 머리 블록 포함 13조각): `b758140a…` 대비 다른 절 = **'의도'·'작성 전 실측' 둘뿐**, 나머지 11조각(머리 블록, '관찰 가능한 계약' -- 계약 12 redteam 32 표 131행~ 포함, 신규 시그니처 등) 바이트 동일. pre-4a2.bak 대비도 같은 두 절만.
* '의도' 27행: 바뀐 것은 괄호 안 소비자 스크립트 수와 목록(7 -> 8, `disc.py` 추가)뿐. 계약 8(관찰 가능한 계약)은 수를 적지 않고 "이름·시그니처·결과 유지"만 -- 사실 갱신이지 계약 변경 아님.
  실측: `git -C … grep -nE "(mc|mutate_changed)\.(changed_defs|def_hash)\(" 4a286f0 -- . ':!*.jsonl' ':!tools/gates'` = 호출 9줄·8 스크립트(df36 2, dup-w-calc 1, p9 1, df23 3, exempt-binding `disc.py:140·142`) + docstring 2줄 + design 30 309행 문장 -- 초안 문장과 일치.
  (정보: design 30 309행은 아직 "스크립트 4개"라 적혀 있다 -- 설계 문서의 측정 시점 문장이고 이 card 계약과 무관.)
* 승인 문안 pin 문단(`approval_20260930-p3-gate-move-aware.md` 46~49행)과 `g1_kit/approval_…md` 양식: 둘의 diff = 자리표시 3곳(date·답 원문·질문 출처 문단)뿐 -> pin 문단 동기화됨. pre-4a2.bak 대비 승인 문안 변경은 pin 문단(46행 -> 46~49행)뿐, 사용자 원문 줄 무변경. 문단의 "나머지 11절(머리 블록 포함)" 수도 위 대조와 일치.
* `g1_launch.sh` check_apr_draft(heredoc 추출, 실제 양식·채운 판·spec 초안 입력): **exit 0** -- "양식에서 자리표시 줄만 다름, 단계 수 = spec card 계약 12 (red 8 + 거부 23 = 31단계)".
* check_quote(같은 방식, jsonl `63c6146a-….jsonl`, tool_use `toolu_01VKN8qT3BbTikfZQyV9sdQi`, 기대 답 "(가) 전역 이동 인식 (Recommended)"): **exit 0**, 답 2026-10-02T02:05:20Z = 2026-10-02 KST = 문안 date.
  추가로 줄 단위 정확 대조: `* 질문 [UD-5] 원문: "<question>"` 줄과 `  선택지: "<label>" -- "<description>" / …` 줄이 jsonl 값으로 재구성한 문자열과 **줄 전체가 같음**(부분 문자열이 아니라 완전 일치), 선택지 3개, multiSelect false.

## 정리
모래상자 `C:/g238` 삭제. 실제 저장소 변경 없음.
