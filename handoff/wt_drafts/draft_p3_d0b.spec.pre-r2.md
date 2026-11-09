---
id: 20260930-p3-registry-dest
phase: 3
evidence_type: red-green
gate_change: no
approval: 20260930-30-module-split-design
---
## 의도

design `30-module-split`(**v8.5** -- 2026-10-02 UD-0 승인, 승인 기록 `20260930-30-module-split-design` 커밋 대기) §6.2 '규칙'·'결과 조건'(D-31), §6.4 'D0b 재측정 조건', §6.5(FU, D-29), §8 D0b 행, card D0b. 계획 N3.10 517행 "Phase 3 design 문서가 그 열(레지스트리 '이관 목적지')에서
이관표와 실제 의존 그래프를 생성한다"를 **실제 저장소에서 끝낸다**: D0a 도구 `tools/migrate/move_plan.py plan`이 낸 단위 → MOD 배정(이관표)을 레지스트리
`docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`의 '이관 목적지' 열에 옮겨 적고(+ `근거 규칙` 열), 그 열이 도구 출력과 같다는 것과
이동 전 계층 사전 검사(PLAN-LAYER)·D-22 전제(`import_time_high`)·`__future__`/import 출처 갈림(`import_conflicts`, D-30)을 **새 계약 test** `A/tests/contracts/test_p3_registry_dest.py`가 Phase 3의 모든 card V1에서 단언하게 한다.
A = `skills/analog-gmid-design/assets`. 지금 열은 N3.10 이전 판 이름을 쓴다(design §6.1: MOD 이름 없는 셀 62, MOD1·5·6 행 0, 두 MOD 셀 16).

이 card가 하는 일은 셋이다. (1) **이관표 확정**: D0b 자신의 base(**B34 → b26pre → backfill → B26-1 → B33 → G1 → FU → D0a**가 모두 병합된 gate `master` -- design §6.4·§8 D0b 행·§8.1, FU는 B33 뒤 D0b 전 아무 때나)에서
`plan`을 처음 계산한다. 그 전의 `plan` 출력(D0a 계약 8 (a), 이 card '작성 전 실측')은 관찰이지 이관표가 아니다. (2) **레지스트리 열 재생성**(code-author):
대상 행의 목적지 칸 = 도구가 배정한 MOD 파일 줄기 하나, `근거 규칙` 칸 = 그때의 규칙 ID. 레지스트리 §7 `보류(Phase 3)` 9행의 처리 열 = `보류(Phase 4)`(D-10 -- 옮기고 D 유지).
(3) **계약 test**(test-author): `plan` exit 0과 판정 목록 **일곱**(`upward`·`cycles`·`unassigned`·`conflicts`·`reg_mismatch`·`import_time_high`·`import_conflicts`) 전부 빈 목록, MOD7 배정은 MOD7 파일의 단위뿐,
레지스트리 열 = 도구 출력, 손적용 사실 표본(oracle (d)-1).
**손으로 쓰지 않는다**: 목적지 칸은 도구 출력과 바이트로 같아야 하고 test가 대상 행 전부를 대조한다(계약 6). 규칙으로 풀리지 않는 충돌은 열을 고쳐 덮지 않고
**멈춘다**(계약 8) -- UD-0(승인됨)이 덮는 N3.10 개정은 `p3_doc_amendments.md` §1·§9(3건 + D-19 (가) + v8.4 A-1 충돌 보정 8건(토큰 11개) + v8.5 책임 보정 1건 (h) MOD9 `_kv_table`)뿐이고 그 밖의 개정은 따로 사용자 승인을 받는다(design D-11).
원칙: test는 코드 구조·계획서·레지스트리만 읽는다(topology 무관 -- 회로·넷·소자 이름, `library/`·`*.topology.json` 없음). 엔진 파일 이름은 design §6.3 `MP_ARGS`의
인자로만 쓰고, MOD 파일 이름은 계획서 N3.10 표(`import_layering.mod_table`)에서 읽는다. 숫자 임계값 없음(판정 목록이 빈지, 칸이 같은지만 -- WP-03).
**동결 시작**: 이 card 병합부터 F2 병합까지 엔진 파일(`A/*.py`, `workspaces/run_harness.py`)·`tools/gates/**`·`tools/migrate/**`·레지스트리 '이관 목적지' 열을 바꾸는
Phase 3 밖 card는 병합하지 않는다(design D-27). 그런 card가 병합되면 이 card의 계약 test가 `reg_mismatch`로 깨지고 D0b를 다시 계산한다(레지스트리 열 재생성 card).
병합은 **Phase 2 DoD PASS 뒤**(`phase: 3` card -- 계획 991행, design D-23, 확정 순서상 자동 성립)이고 FU·D0a 병합 뒤다. 그 전에는 spec card 초안·작성 전 실측만 한다.

## 관찰 가능한 계약

1. **범위**(이 card `Change-Id` 커밋들의 diff로 한정): code 커밋이 바꾸는 파일 = 레지스트리 `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md` 하나,
   test 커밋이 더하는 파일 = `A/tests/contracts/test_p3_registry_dest.py` 하나. 엔진(`A/*.py`, `workspaces/run_harness.py`)·`tools/**`·계획서·design 문서 변경 0.
   N3.10 추가 개정이 필요하면 이 card 커밋이 아니라 별도 승인 기록과 오케스트레이터 문서 커밋으로 들어간다(계약 8).
2. **이관표 = 도구 출력**. 이관표의 정본은 D0a 계약 1 CLI를 design 30 §6.3 `MP_ARGS` 그대로(bash 배열 -- `--split` 다섯·`--keep` 하나·`--aliases` JSON) `--rev HEAD`로
   돌린 `plan` 출력의 `assignment`(단위 키 → `mod`·`rule`)다. 배정 규칙과 규칙 ID 집합의 정본은 D0a 계약 2(design 30 §6.2·D-31: 모듈 docstring 제외, A-0·A-1·A-2·A-3·A-4(승격, MOD7 상한)·A-K·A-5·A-6·A-7, 단조 고정점)다.
   실행하는 도구는 그 커밋의 `tools/migrate/move_plan.py`다(D0b~F2에 `tools/**` 변경 0 -- design D-16·D-27 -- 이라 판정 기록 사본 `code_commit` 판과 같은 파일이다).
   레지스트리 열은 이관표 중 레지스트리 행이 있는 단위의 사본이다(레지스트리에 행이 없는 정의·최상위 문장은 열에 없고 도구 출력에만 있다 -- 그래서 열만으로 이관표를 다시 만들지 않는다).
   Phase 진행 중에도 규칙 A-0(D0a 계약 2·8 (b))으로 같은 사상이 나온다.
3. **`plan` 판정**(이 card 병합본, 그리고 그 뒤 Phase 3 모든 card의 병합본 -- 배선): exit 0, `verdict` = `PASS`, 판정 목록 일곱 `upward`·`cycles`·`unassigned`·`conflicts`·`reg_mismatch`·
   `import_time_high`·`import_conflicts`가 모두 빈 목록(design §8 D0b 행 v8.4). `import_conflicts`(D0a 계약 2, design D-30)는 한 MOD로 가는 단위들의 import 출처 갈림과 `__future__` 기능 집합 갈림이다 --
   `__future__` 갈림은 준비 card FU(design §6.5·D-29)가 D0b 전에 병합되어야 비고, 이 단언이 그것을 FAIL로 잡는다(만들면 배선). `mod_imports`는 판정하지 않는다(M card 몫 -- design §8 M행).
   `absent_split`도 판정하지 않는다(F2 뒤 shim 파일 부재는 오류가 아니다 -- D0a 계약 8 (c)).
4. **`import_time_high` = []**(design §2.2 D-22 (2)의 전제 -- 4차 검토 S5, 키 정의는 D0a 계약 2): 배정 MOD 번호가 위쪽 재수출을 받는 split 파일 번호보다 큰 단위가
   import 시점(데코레이터·기본값·`__future__` 없는 파일의 주석·클래스 몸체·모듈 문장)에 그 번호 이상 MOD의 이름을 읽지 않는다. 이 목록이 비어 있어야 MOD8·MOD9의
   번호 7 이상 모듈 import를 파일 끝에 두는 D-22 배치가 `NameError` 없이 성립한다. 계약 3과 별도로 적는 이유: 위반은 import 줄 위치로 풀 수 없고(머리 배치 = 순환,
   끝 배치 = `NameError`, 함수 안 지연 import = 금지 -- design F3) **배정을 바꿔야** 하므로 멈춤 경로가 계약 8 (c)로 따로다.
5. **MOD7은 자기 파일의 단위만**(design 3차 검토 m4 -- 옮길 card가 없다): `assignment`에서 `mod`가 N3.10 MOD7 파일(계획서 `mod_table`에서 번호 7의 줄기 + `.py`)인 단위는
   전부 키의 파일 부분이 그 파일이다. split 파일 중 MOD7 파일 밖 단위가 MOD7로 배정되면 FAIL. (승격 상한(D-31)이 규칙 쪽에서 막고, 이 단언이 결과 쪽에서 막는다.)
6. **레지스트리 열 모양**(code 커밋이 만든다, test가 대조한다). '레지스트리 함수 표' = 머리에 `함수` 열과 `이관 목적지` 열이 **둘 다** 있는 표 전부(D0a 계약 2 A-4 정의 그대로 --
   열 위치는 머리에서 찾는다, 칸 나누기는 `\|`가 칸 안 문자). 그 표마다:
   (a) 머리에서 `이관 목적지` 바로 뒤에 `근거 규칙` 열이 있다(구분선 칸 수도 같이 는다).
   (b) **대상 행** = 함수 칸 첫 백틱 토큰의 `.` 앞(메서드 행 `Class.method`는 클래스)이 `assignment` 단위 키의 `::` 뒤 부분과 같은 행(design §8 D0b 행 '대상 행'). 대상 행의 `이관 목적지` 칸 =
       그 단위 `mod`의 줄기(`.py` 없이, 백틱·공백·다른 글자 없이 정확히 그 문자열 -- `--keep` 파일로 남는 A-K 단위는 그 파일 줄기). `〃` 금지(대상 행마다 명시). 같은 키에 단위가 둘 이상이고 `mod`가 갈리면 FAIL(지금 0 -- 실측 2).
   (c) 대상 행의 `근거 규칙` 칸 = **D0a 계약 2가 정의한 규칙 ID 집합**의 원소 하나(지금 정의 = {`A-0`, `A-1`, `A-2`, `A-3`, `A-4`, `A-K`, `A-5`, `A-6`, `A-7`} -- design §6.2 D-31.
       test는 이 집합을 상수 하나로 두고 출처(D0a 계약 2)를 주석으로 적는다; 집합이 바뀌면 그 D0a 후속 card가 이 test를 함께 고친다). 값은 재생성 시점 `plan`의 `rule`(이력)이고 auditor가 V10에서
       D0b base 출력과 대조한다. 재생성 뒤에는 열이 A-4 입력이 되어 도구의 `rule`이 바뀌므로(실측 4: A-7 2 → 0, A-6 7 → 3, A-4 230 → 240 등) test가 현재 `rule`과 대조하지 않는다(design §8 D0b 행).
   (d) **중첩 행**(함수 칸이 `└`로 시작하는 하위 def 표기)과 **비대상 행**(키에 맞는 단위가 `--split`·N3.10 파일에 없는 행 -- 하네스·LUT 생성 도구·`topology_to_markdown` 등,
       실측 2)은 `이관 목적지` 칸 불변, `근거 규칙` 칸 `-`(design §8 D0b 행 v8.4가 정했다). 불변은 auditor가 base 대비 diff로 본다(test는 base를 모른다).
   (e) 대상 행 수 > 0, 레지스트리 함수 표 수 > 0(공허 통과 방지).
7. **§7 처리 열**(design D-10, U-02 승인 `20260923-u02-d-list` 1항 원문 "보류(Phase 3 모듈 이동·Phase 4 배선)"): 레지스트리에 `보류(Phase 3)` 문자열 0개. base에서 `보류(Phase 3)`이던 행(지금 9행)은 `보류(Phase 4)`이고
   그 밖의 처리 칸은 불변(auditor diff). 보류 **집합**은 그대로다(design 20 REG 판정식). 이 card가 병합될 때 그 9단위는 아직 옮겨지지 않았다 -- **Phase 3 이동 의무는 이 card가 쓴 '이관 목적지' 열과
   `move_plan` `plan`·`check`(M card `move-set`)가 넘겨받는다**(그래서 처리 칸에서 'Phase 3'을 지워도 이동 몫이 사라지지 않는다). 기존 `tests/tools/reg_check.py`(`disposition`·`count`·`stale`)는
   재생성 뒤에도 발견 0이어야 한다(V1의 `test_reg_check.py`가 실제 저장소로 돈다).
8. **멈춤 조건(열을 쓰기 전 -- code-author가 아니라 오케스트레이터 절차, design §6.2·§8 D0b 행 '멈춤 경로'·§9.1·D-11)**: D0b base에서 `plan`을 돌려
   (a) `conflicts`, 또는 원천이 A-1(N3.10 토큰)인 `upward`·`cycles`가 있으면 열을 쓰지 않는다. 오케스트레이터가 N3.10 '대표 대상' 토큰 개정 diff를 만들어 사용자 승인(`target_kind: diff`, UD-0 밖 -- 위임받지 않음)을
   받고 문서 커밋으로 병합한 뒤 다시 계산한다. 그 승인 id를 이 card 머리 `approval` 줄에 더한다.
   (b) 규칙 공백(`unassigned`, 원천이 A-1이 아닌 `upward`)이면 design §6.2 규칙 개정(D0a 후속 card, red-green)을 먼저 병합한다.
   (c) `import_time_high`가 비지 않으면 같은 경로(a)로 **배정**을 바꾼다(위치 규칙으로 풀지 않는다 -- 계약 4).
   (d) `import_conflicts`가 비지 않으면: `name` = `__future__`이면 FU 병합을 확인한다(FU 없이 돌리면 MOD2·MOD9 두 곳이 갈린다 -- v8.5 문서 개정 (h)로 DR의 HTML 표 도우미가 MOD9로 가서 MOD4는 빠졌다, 실측 3·design §6.5 v8.5 -- 이 절에서는 엔진 함수 이름을 백틱으로 적지 않는다: interface card 생성기가 '기존 함수'로 잡는다, 실측 15); 이름 출처 갈림이면 배정 변경(N3.10 밖 개정이면 (a)의 D-11 경로).
   (e) MOD7 파일 밖 단위의 MOD7 배정이 있으면 (a)의 경로(N3.10 개정, D-11 별도 승인). M7은 승인된 design §8 M7 행대로 M2·M3·M9에 흡수된 빈 card 금지 항목이라(UD-0) 'M7을 실제 card로' 하는 길은 없다 -- 옛 결정 D0b-7은 닫혔다.
   (f) `reg_mismatch`만 비어 있지 않으면 멈추지 않는다 -- 그것이 이 card가 고치는 red다.
   이 card의 test·code 커밋은 (a)~(e)가 모두 빈 base(= 그 해소가 병합된 gate `master`)에서 만든다. 지금 실측(시제품, UD-0 v8.5 개정 (h) 포함 + FU 대역 + D-31 규칙)으로는 (a)~(e) 모두 비어 있다(실측 3) -- D0b base에서 다시 잰다.
9. **재생성 멱등**(손 편집 방지의 두 번째 선, auditor V10): 재생성 전 커밋(D0b base)의 `plan` `assignment`에서 (단위 키 → `mod`) 사상 = 병합본 `plan`의 사상(파일 부분·`rule`은
   비교에서 뺀다 -- D0a 계약 8 (b)와 같은 비교). 열이 A-4 입력이 되어도 배정이 바뀌지 않아야 한다(판정 목록이 빈 base에서 성립 -- 실측 4).
10. **이관표 산출물**(M card '작성 전 실측'의 한 벌 -- design §8.1 "D0b 이관표 한 벌에서 결정적으로"): auditor가 판정 기록 `.ai/verification/20260930-p3-registry-dest/out/`에
    D0b base(재생성 전)와 병합본의 `plan` JSON 전체, 그로부터 뽑은 MOD별 단위 목록(`order` 순)·`reexports`(split 파일별 재수출 줄 -- D-22 (1)의 SD MOD8·MOD9 재수출 포함)·`mod_imports`(M card import 머리의 원본 -- D-30)·
    규칙 분포를 남긴다. 이것은 증거이고 정본이 아니다(정본은 계약 2 -- 언제든 다시 계산된다). M card spec card의 '파일:줄'·import 머리는 각 M card base에서 이 도구 출력으로 다시 잰다.
11. **test 모양**:
    (a) **red 모양 -- test 함수마다 base red가 그 test 자신의 계약 단언에서 나온다**(D0b 검토 S1, design §8 D0b 행). base에서 이미 참인 단언(계약 3의 `reg_mismatch` 밖 여섯 목록·계약 5 MOD7·계약 6 (b)의 같은 키 갈림 0·
    계약 6 (e) 표/행 수 > 0, 행 없는 표본의 `plan` `mod`)은 **혼자 test가 되지 않고** 진짜 red 단언과 같은 test 안에 그 앞에 둔다. 모든 test에 같은 머리 단언을 앞세우지 않는다(그러면 red가 머리 단언 하나에서만 나와
    각 test의 실제 단언이 base에서 한 번도 기록되지 않는다). test 함수는 다섯(이름은 예시, 접두 `test_p3rd_`):

    | test | 단언 순서(앞 = base에서 참, 끝 = base red) | base red의 원천 |
    |---|---|---|
    | T-A `test_p3rd_plan_verdict` | 도구 출력 첫 줄 JSON·`"tool": "move_plan"` → `conflicts`·`upward`·`cycles`·`unassigned`·`import_time_high`·`import_conflicts` 각각 `== []` → MOD7 파일 밖 MOD7 배정 0(계약 5) → **`reg_mismatch == []`** → exit 0·`verdict` `PASS` | `reg_mismatch` 비지 않음(실측 79) |
    | T-B `test_p3rd_dest_cells_match_plan` | 함수 표 수 > 0 → 대상 행 수 > 0 → 같은 키 `mod` 갈림 0 → **대상 행마다 `이관 목적지` 칸 == `mod` 줄기**(계약 6 (b)) | 대상 행 칸 불일치(실측: 대상 347 중 base 칸 = 줄기 128, 다름 219 -- `reg_mismatch` 79는 그중 칸이 MOD 하나인 행) |
    | T-C `test_p3rd_rule_column` | **표마다 `이관 목적지` 바로 뒤 `근거 규칙` 머리**(계약 6 (a)) → 대상 행 `근거 규칙` 칸 ∈ 규칙 ID 집합(6 (c)) | 머리에 `근거 규칙` 없음 |
    | T-D `test_p3rd_hold_phase3_gone` | **레지스트리의 `보류(Phase 3)` 수 == 0**(계약 7) | 9 |
    | T-E `test_p3rd_fact_samples` | (d)-1 표의 각 행: 행 있는 표본은 대상 행이고 칸 == 기대 줄기, 모든 표본은 `plan` `mod` 줄기 == 기대 줄기 -- 어긋난 표본을 모아 **빈 목록 단언** 하나 | 행 있는 표본 23 중 22의 칸이 기대와 다름(실측 5) |

    (b) 도구는 하위 프로세스(인자 목록, 셸 없음 -- `--aliases` JSON이 쪼개지지 않는다)로 부르고, 출력 첫 줄이 JSON이며 `"tool": "move_plan"`임을 단언한 뒤 판정한다(도구가 없거나
    exit 2이면 판정 목록 단언 전에 FAIL -- D0a 계약 10과 같은 이유). T-A·T-B·T-E가 이 출력을 쓴다. (c) `plan`은 test 모듈 실행당 한 번(모듈 범위 캐시, 상한 1 -- 실측 19~33초, NFR-2).
    (d) 저장소 루트는 test 파일 위치에서 계산하고 `--root`로 넘긴다(V1 격리 복제본에서도 같은 판). (e) **레지스트리·계획서는 `git show HEAD:<경로>`로 읽는다** -- 도구가 `--rev HEAD` 커밋을 읽으므로
    두 입력이 같은 커밋이 된다(D0b 검토 m2: 작업 트리를 읽으면 미커밋 편집이 있을 때 열과 도구 입력이 갈린다). 그래서 거부 입력은 사본에 **커밋**해야 test에 보인다.
    (f) 이름: 보조 함수·상수는 `_p3rd_` 접두. 삭제된 이름 토큰(T0 card 계약 9 목록, `test_d_*` 전수 스캔 대상)과 `print` 판정(`test_ts3_no_print_verdicts`) 없음.
12. **topology·이름 무관**: test 소스에 회로·넷·소자 이름과 `library`·`topology.json` 없음. 엔진 파일 이름은 `MP_ARGS`(design §6.3 정본) 인자 리터럴로만, MOD 파일 이름은
    계획서 `mod_table`에서 읽는다(MOD7 판정 포함). 결정 사실 표본(oracle (d)-1)의 단위 이름·기대 줄기는 'oracle 종류와 출처' 절의 표에서 온다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

red-green: code 커밋(레지스트리)이 있으므로 test-only가 아니다(선례 `20260930-registry-grade-fix` -- 레지스트리 문서 수정 + 계약 test, red-green). 새 test 파일의 다섯 test가 base에서
각자의 계약 단언으로 `AssertionError` FAIL한다(계약 11 (a) 표 -- T-A `reg_mismatch`, T-B 대상 행 칸, T-C `근거 규칙` 머리, T-D `보류(Phase 3)` 9, T-E 표본 칸). 병합본에서 green.
equivalence가 아닌 이유: test가 새로 생기고 base에서 실패한다(동작 보존 증명 대상이 아니다). 신규 심볼 없음 -- red는 `ImportError`가 아니라 assertion이다(계획 680행).
V3: 바뀌는 소스 def 0(레지스트리·test만) → `targets []`. V7: 새 def 0. V5: 새 파일만 → `diff_paths []`. V4: interface card 두 표가 비어 `--interface-card`만으로는
`test_lint` ERROR('피검 심볼이 없다')이다 -- **interface card 두 표가 빈 card의 DESIGN-GAP 우회**로 auditor는 `--module-dir tools/migrate --subject move_plan:main`으로 돈다. 선례는 이 card처럼 **card가 바꾸지 않는 도구**를
subject로 준 `20260922-ts7-ic-xfail`(`--module-dir tools/gates --subject merge_gate:read_plan_tables …`)과 `20260923-v4-decision-exempt`(`--module-dir tools/gates --subject test_lint:main`)다(D0b 검토 m1 --
`20260922-sections-major-merge`는 그 card가 고친 도구를 subject로 줬으므로 선례로 들지 않는다). test가 도구를 하위 프로세스로만 부르므로 판정 문장은 NO-SUBJECT이고(작성 전 실측 9), V4가 실질을 갖는 곳은
판정 기록 basis의 oracle 대조 문장((d)-1 표·계약 3~7)뿐이다.

## oracle 종류와 출처

(d) 계획서·레지스트리·도구 출력. **동어반복 방지로 둘로 나눈다**(design §8 D0b 행 v8.4, 1차 검토 §2 (3) V4 -- 레지스트리가 같은 도구 출력이라 '열 = 도구 출력'만으로는 도구와 열이 함께 틀린 것을 못 잡는다):
* **(d)-1 결정 사실 표본(손적용, 도구 실행 없이 정해진 기대값)**: 계획서 N3.10(UD-0 문서 개정 `p3_doc_amendments.md` §1 (a)(가)~(d)·§9 (e)~(h) 적용 판 -- v8.5, 2026-10-02 승인)과 레지스트리 칸(재생성 전)·엔진 소스의 호출 관계에서
  design §6.2 규칙(D-31)을 **손으로 적용해** 정한 단위 → 목적지. 규칙마다 한 행 이상(A-1·A-2·A-3·A-4 일반 칸·A-4 별칭 `optimizer`·A-4 `〃`·A-5·A-K·A-6·A-7 -- design §8 D0b 행).
  **행 있는 표본**(아래 '행' 열 ○): test는 그 행이 대상 행이고 `이관 목적지` 칸이 기대 줄기와 같으며 같은 단위의 `plan` `mod` 줄기도 같은지 단언한다. **행 없는 표본**(×): `plan` `mod`만 단언한다
  (레지스트리에 그 단위의 함수 행이 없다 -- 이 card는 행을 더하지 않는다, 계약 1·'무동작 판정 입력'. D0b 검토 B1 (a)).
  표본 선택은 도구 출력(관찰)을 보고 했지만 기대값은 아래 '근거' 열의 문서·소스에서 정했다. 선택 관찰에서 이 단위들은 `upward`의 원천도 대상도 아니다(판정 목록이 모두 빈 관찰 -- 실측 3). D0b base에서 표의 근거를
  다시 확인하고, 해소 문서 커밋(계약 8)이나 B26-1·B34가 표의 단위를 옮기거나 근거를 바꾸면 오케스트레이터가 test-author 착수 **전에** 표를 고친다(기대값이 test 커밋 뒤에 바뀌지 않게).

  | 단위(함수 칸 첫 토큰) | 기대 목적지 | 행 | 규칙 | 근거(손적용) |
  |---|---|---|---|---|
  | `load_topology` | `circuit_state_graph` | ○ | A-1 | 문서 개정 §1 (b) MOD3 토큰 |
  | `validate_theta_declaration_order` | `circuit_state_graph` | ○ | A-1 | §1 (b) MOD3 토큰 |
  | `require_declared_spec_source` | `circuit_state_graph` | ○ | A-1 | §1 (b) MOD3 토큰(v8.4 보정 -- MOD2 행에서는 백틱 없이 설명만) |
  | `optimize_full_circuit_budget` | `sizing_layout_convergence` | ○ | A-1 | §1 (d) MOD8 토큰, D-3 |
  | `_optimize_theta_slsqp` | `sizing_layout_convergence` | ○ | A-1 | §1 (c)(d) v8.4 -- MOD6 행에서 빠지고 MOD8 토큰(Phase 3 위치) |
  | `GmIdLUT` | `gmid_lut` | ○ | A-1 | N3.10 MOD1 토큰 |
  | `compute_metric` | `circuit_metrics` | ○ | A-1 | N3.10 MOD5 토큰 |
  | `apply_theta_feed` | `circuit_metrics` | ○ | A-1 | §9 (f)(g) v8.4 -- MOD4 행에서 빠지고 MOD5 토큰 |
  | `true_current_mirror_groups` | `circuit_state_graph` | ○ | A-1 | N3.10 MOD3 토큰 |
  | `find_hub_merge_candidates` | `circuit_state_graph` | ○ | A-1 | §1 (b) v8.4 MOD3 토큰(레지스트리 칸 `stick_diagram`을 덮는다) |
  | `run_topology_pipeline_with_finger_fixup` | `sizing_layout_convergence` | ○ | A-1 | N3.10 MOD8 토큰 |
  | `render_html_report` | `instance_report_builder` | ○ | A-1 | N3.10 MOD9 `design_report.render_html_report`(`<모듈>.<이름>` 토큰) |
  | `NameCollisionVerdict` | `circuit_state_graph` | ○ | A-2 | dataclass, 참조자는 `check_topology_name_uniqueness` 하나(아래 행 -- MOD3) → 가장 낮은 참조자 MOD3, 자기 참조 0이라 승격 없음. A-2가 A-4보다 먼저라 레지스트리 칸 `stick_diagram`(MOD7)을 쓰지 않는다 |
  | `run_full_circuit_audit` | `stick_diagram` | ○ | A-3 | 칸 "stick_diagram 또는 instance_report_builder" = MOD7·MOD9 → 가장 작은 7, 부르는 트리 안 단위(SD 감사 레코드·검사 함수, `find_hub_merge_candidates` MOD3, `Transistor`)에 MOD8·MOD9 없음 → max = 7 |
  | `_invert_gm_id_for_current` | `gmid_sizing_engine` | ○ | A-4 일반 | 칸 `gmid_sizing_engine.py` = MOD4, 부르는 트리 안 단위 `GmIdLUT`(MOD1)뿐 → 승격 없음 |
  | `quantize_L` | `theta_search` | ○ | A-4 별칭 | 칸 `optimizer` → `--aliases` MOD6, 부르는 트리 안 단위 0 |
  | `_theta_evidence_for_pair` | `instance_report_builder` | ○ | A-4 `〃` | (ACF 단위) 칸 `〃` → 위 행 `render_html_report` 칸 `` `instance_report_builder.render_design_r… `` → MOD9, 부르는 단위 `_as_set`(칸 `topology_authoring.py`, MOD2) → 승격 없음 |
  | `_kv_table` | `instance_report_builder` | ○ | A-1 | 문서 개정 §9 (h)(v8.5, UD-0 승인) MOD9 토큰 `_kv_table`. 레지스트리 칸은 §3 '기타 모듈' 표의 `〃` 번짐(파일 열이 없어 TL 행 `miller_ota_topology`의 `gmid_sizing_engine.py`까지 이어진다 -- A-4라면 MOD4)이지만 A-1이 A-4보다 먼저다 -- 토큰이 칸을 덮는 표본 |
  | `save_html_report` | `instance_report_builder` | ○ | A-4 `〃` + 승격 | 같은 `〃` 번짐으로 칸 MOD4, 부르는 `render_html_report`가 MOD9(A-1) → max(4, 9) = 9(MOD7 아님 -- 상한 무관) |
  | `_topology_ref_relpath` | `instance_report_builder` | × | A-5 | 레지스트리 행 없음, 참조자 `save_instance_json`(N3.10 MOD9 토큰 `save_instance_json`) 하나 → MOD9, 부르는 트리 안 단위 0 |
  | `check_topology_name_uniqueness` | `circuit_state_graph` | × | A-5 | 레지스트리 행 없음(221행 첫 토큰은 `NameCollisionVerdict`), 참조자 `load_topology`(MOD3) 하나 → MOD3, 부르는 것은 `NameCollisionVerdict`(MOD3)뿐 |
  | `render_report` | `audit_current_forced` | ○ | A-K | 칸 `audit_current_forced.py`는 N3.10 파일·별칭이 아니라 A-4로 정해지지 않고, `--keep` 파일의 단위라 그 파일에 남는다 |
  | `solve_diode_stack_current` | `gmid_sizing_engine` | ○ | A-6 | 칸 "삭제 후보"(§7 `보류(Phase 4)`), 엔진 안 참조자 0(docstring 언급뿐), 부르는 단위 `GmIdLUT`(MOD1)·`_invert_gm_id_for_current`(위 행, MOD4) → 최댓값 MOD4 |
  | `MultiLeafHubParityVerdict` | `stick_diagram` | ○ | A-7 | 칸 "test util", 엔진 안 참조는 아래 행과 서로뿐 → 다른 규칙으로 정해지지 않고 N3.10 MOD7 파일 `stick_diagram.py`에 있다 |
  | `check_multi_leaf_hub_parity` | `stick_diagram` | ○ | A-7 | 같음 |
  | `RailDeclaration` | `topology_authoring` | × | A-2 | design §6.4 -- 참조 단위 중 가장 낮은 MOD2(구조 제안 함수의 `rails: RailDeclaration` 주석), D-19 답과 무관. **B26-1 병합 뒤에만 있다** |
  | `rail_declaration` | `topology_authoring` | × | A-1 | D-19 답 (가) MOD2(2026-10-02, 승인 기록 `20260930-30-module-split-design` 커밋 대기) -- 문서 개정 §1 (a)(가) MOD2 토큰 `rail_declaration`. B26-1 병합 뒤에만 있다 |

  지금 레지스트리에서 행 있는 표본 23개 중 22개의 칸이 기대 줄기와 다르다(같은 것은 `run_topology_pipeline_with_finger_fixup` 하나 -- 칸 `sizing_layout_convergence`; 작성 전 실측 5) -- T-E의 base red다.
  `〃` 표본은 동어반복 방지의 핵심이다: 도구와 열이 함께 틀리는 경우(거부 입력 R-E1 -- 재생성 뒤 `_theta_evidence_for_pair` 칸을 `instance_report_builder`에서 `theta_search`로 바꾸면 도구가 그 칸을 읽어(A-4, 승격 없음) MOD6으로 배정하고 `plan` exit 0·`reg_mismatch` 0, T-B도 통과한다)는 이 표만 잡는다.
  (v8.5: 옛 R-E1 표본 `_kv_table`은 이제 A-1 토큰이 칸을 덮어 칸을 바꾸면 `reg_mismatch` 1로 T-A가 잡는다 -- 도구·열이 함께 틀리는 예가 아니라 바꿨다, 작성 전 실측 6.)
* **(d)-2 실제 트리 drift guard**: 계약 3~7을 실제 저장소 `HEAD`에서 -- 도구 출력과 열의 일치(대상 행 전부), 판정 목록 일곱 빈 목록, MOD7, `import_time_high`, `보류(Phase 3)` 0.
  이 쪽은 Phase 3 이후 card가 엔진·열을 바꿔 생기는 어긋남(D-27 위반 포함)을 잡는 배선이다.
* 규칙 손적용 **합성 입력**은 이 card의 test에 두지 않는다(design §8 D0b 행 v8.4) -- 합성 저장소에서 도구를 부르는 test는 base(D0a 병합 뒤)에서도 통과해 V2 red가 될 수 없다.
  합성 입력으로 규칙을 검증하는 것은 D0a test(`A/tests/tooling/test_move_plan.py`, D0a oracle (a) -- v8.4 합성 단계 `doc-excluded`·`keep-residual`·`lift-a4`·`lift-cap-mod7`·`a6-ref-follow`·`a7-isolated`·`monotone-seed`)의 몫이다.

## 거부해야 할 입력

(test가 FAIL해야 하는 저장소 상태. test-author는 합성하지 않는다 -- 판정은 실제 트리 하나이고 아래는 계약의 반례다. auditor는 V10 ⑥에서 **병합본 사본에 하나씩 커밋해**(계약 11 (e)) 해당 test가
**그 test 고유 단언에서** FAIL하는지 잰다 -- test 함수마다 하나 이상(D0b 검토 S1 (3)). '측정' 열은 작성 전 실측 6에서 `plan` 시제품으로 판정 목록이 실제로 비지 않음을 확인한 것.)

| id | 겨누는 test(단언) | 만드는 법(병합본 사본) | 측정 |
|---|---|---|---|
| R-A1 | T-A `upward` | 계획서 N3.10 MOD1 행 '대표 대상' 칸 끝에 `` , `save_html_report` `` 추가 | `upward` 1(+ `reg_mismatch` 1) |
| R-A2 | T-A `conflicts` | 계획서 N3.10 MOD2 행 '대표 대상' 칸 끝에 `` , `compute_metric` `` 추가(MOD5 행과 겹침) | `conflicts` 1 |
| R-A3 | T-A `unassigned` | `A/sizing_recipe.py` 끝에 참조·참조자 없는 최상위 함수 `def _p3rd_orphan(): return 0` 추가(SR은 N3.10 파일이 아니라 A-7 밖) | `unassigned` 1 |
| R-A4 | T-A `import_time_high` | `A/stick_diagram.py` `def save_instance_json(` 머리 마지막 인자 뒤에 `_p3rd_probe=build_stick_diagram` 기본값 인자 추가(MOD9 단위가 import 시점에 MOD7 이름을 읽음) | `import_time_high` 1 |
| R-A5 | T-A `import_conflicts` | `A/design_report.py`의 FU 줄 `from __future__ import annotations` 삭제 | `import_conflicts` 1(MOD9) |
| R-A6 | T-A MOD7 | 계획서 N3.10 MOD7 행 '대표 대상' 칸 끝에 `` , `_as_set` `` 추가(ACF 단위가 MOD7로 -- 부르는 쪽은 MOD9뿐이라 `upward` 없음) | MOD7 밖 1(+ `reg_mismatch` 1) |
| R-A7 | T-A·T-B·T-E 도구 출력 단언 | `tools/migrate/move_plan.py` 삭제 | -- (첫 줄 JSON 단언) |
| R-B1 | T-B 칸 = 줄기 | 레지스트리 `quantize_L` 행 `이관 목적지` 칸 `theta_search` → `gmid_lut`(+ T-A `reg_mismatch`) | -- |
| R-B2 | T-B 정확 일치 | 같은 칸을 `theta_search(S3)`로(도구는 토큰으로 MOD6을 읽어 `plan` exit 0 -- T-B만 잡는다) | `plan` exit 0, 목록 모두 빈 목록 |
| R-B3 | T-B `〃` 금지 | 대상 행 하나(`_theta_evidence_for_pair`)의 칸을 `〃`로 되돌림 | -- |
| R-C1 | T-C 머리 | 함수 표 하나의 머리 `근거 규칙` → `근거규칙` | -- |
| R-C2 | T-C 집합 | 대상 행 하나의 `근거 규칙` 칸 → `A-9`(D0a 계약 2 집합 밖) | -- |
| R-D1 | T-D | §7의 `보류(Phase 4)` 하나(base에서 `보류(Phase 3)`이던 행)를 `보류(Phase 3)`로 되살림 | -- |
| R-E1 | T-E 표본(도구·열 함께 틀림) | 레지스트리 `_theta_evidence_for_pair` 행 칸 `instance_report_builder` → `theta_search` | `plan` exit 0·목록 일곱 모두 빈 목록·`_theta_evidence_for_pair` `mod` = `theta_search.py`(다른 단위 사상 차이 0) -- T-A·T-B는 통과, T-E만 FAIL |

**거부하지 않아야 할 것**: shim 파일이 없는 트리(`absent_split` -- F2 뒤), 옮겨진 단위(A-0)만 있는 MOD 파일, 비대상 행·중첩 행의 옛 목적지 문구, `mod_imports` 내용(판정 밖).

## library 회로 적용 여부

해당 없음(코드 구조·문서 판정). 회로 실행 없음.

## 무동작 판정 입력(무발동 값)

엔진 소스·기존 test·게이트 도구·D0a 도구는 바뀌지 않는다. 레지스트리에서 바뀌는 것은 대상 행의 `이관 목적지` 칸, 모든 함수 표의 `근거 규칙` 열, §7의 `보류(Phase 3)` 9칸뿐이다(계약 6 (d)·7 --
auditor가 base 대비 줄 단위 diff로 그 밖의 변경 0을 확인). 열을 더해도 기존 레지스트리 소비자(`tests/tools/reg_check.py` -- 머리 이름으로 열을 찾는다, `test_reg_check*.py`·
`test_df23_inventory.py`)의 결과가 같다(작성 전 실측 4: 재생성 + `보류` 치환을 함께 한 트리에서 그 세 파일 210 passed, `reg_check` 발견 0 -- D0b 검토 m5).

## 재현할 수치

auditor가 판정 기록 `reproduced_numbers`에 적는다(값은 **D0b base에서 처음 계산** -- 아래 괄호는 지금 관찰(시제품, 실측 3·4)이고 기대값이 아니다):
* `assigned_units`(병합본 `plan` `assignment` 수 -- 관찰 403), `assigned_per_mod`(MOD별 -- 관찰은 작성 전 실측 3), `rules`(규칙 분포, 재생성 전 base 출력 기준 -- 관찰 A-4 229·A-5 64·A-1 60·A-2 38·A-6 7·A-K 2·A-7 2·A-3 1)
* `reg_mismatch_base`(D0b base `reg_mismatch` 수 = T-A red의 크기 -- 관찰 79) / `reg_mismatch_merge` = 0
* `registry_tables`(함수 표 수 -- 관찰 15), `target_rows`·`nested_rows`·`non_target_rows`(관찰 347·7·25, 시제품 -- 문장 단위 키 차이로 상수 행 7개가 비대상으로 셌다, 실제 도구에서는 대상, 실측 2)
* `hold_phase3`(9 → 0), `hold_phase4`(14 → 23)
* `idempotent_mod_diff` = 0(계약 9), `fact_samples_base_equal`(행 있는 표본 중 base 칸 = 기대 -- 관찰 1/23), `plan_seconds`(test 한 번의 `plan` 시간 -- 관찰 19~33초)
명령: §10 `MP_ARGS`로 `"$S/move_plan.py" plan --root "$ISO" --rev <커밋>`(D0b base, 병합본 각각), 레지스트리 표 분류는 auditor 스크립트(계약 6 정의 그대로).

## 결정 필요 항목

**남은 결정 없음** -- design 30 v8.5 승인(2026-10-02 UD-0 "승인"·D-19 "(가) MOD2"·UD-5 "(가)"·UD-1 "(가)", `_drafts/user_decisions.md` 끝 절; 승인 기록 `20260930-30-module-split-design` 커밋 대기)이 아래를 모두 닫았다.
**design v8.4가 닫은 것(결정 이력 `phase3_revision_log.md` '초안 v8.3 → v8.4' 7~11)**: 옛 D0b-1(계층 충돌 해소 → N3.10 A-1 충돌 보정 8건(토큰 11개, 문서 개정 §1·§9, UD-0)과 승격 규칙(MOD7 상한, D-31)),
D0b-2(규칙 빈칸 → 모듈 docstring 제외·A-K·A-6·A-7·단조 고정점, D0a 계약 2), D0b-3(비대상 행 칸 불변·`-`), D0b-4(합성 입력은 D0a test, 이 card는 실제 단위 표본), D0b-5(`근거 규칙` = 재생성 시점 규칙, 형식 = D0a 규칙 ID 집합).
승격이 계획 517행 '열 = 정본'을 '칸 = 하한'으로 읽는 것은 UD-0 질문 본문의 사실이었다(D-31, v8.5 '기준에 닿는 기본값') -- 이 card의 재생성이 열을 다시 이관표와 같게 만든다.
**v8.5 승인으로 닫힌 것**: 옛 D0b-6(D-19 답 → (가) MOD2 -- (d)-1 표 `rail_declaration` = `topology_authoring` A-1로 고정, test-author 착수 막힘 해소).
옛 D0b-7(MOD7 파일 밖 MOD7 배정 시 M7 card 여부 → 승인된 design §8 M7 행 'M2·M3·M9에 흡수(빈 card 금지)' -- 생기면 계약 8 (e) = (a)의 N3.10 개정 경로(D-11, 별도 승인)뿐. 지금 0, 실측 3).
옛 D0b-8(`〃` 번짐으로 DR `_kv_table`이 MOD4 -- 문서 개정 §9 (h)(v8.5) N3.10 MOD9 토큰 `_kv_table`로 닫힘: (d)-1 표 `_kv_table` = `instance_report_builder` A-1, design §6.5 갈리는 MOD 셋 → 둘. 백로그로 넘기지 않는다).
이 밖의 N3.10 개정이 D0b base에서 필요하면 계약 8의 멈춤 경로(UD-0 밖, D-11 별도 승인)다 -- 결정 항목이 아니라 절차다.

## 작성 전 실측

(**v8.5 재측정** -- gate `master` **`dd60db6`**(2026-10-02 작업 시작·끝 같음). 격리 복제본 `C:/g189/r`(`git clone --no-local`, origin·gate 제거, 빈 hooksPath, TMP/TEMP도 `C:/g189` 아래, 작업 끝에 `C:/g189` 삭제)에서만. 실제 저장소 쓰기 없음(`status`·`HEAD`·reflog 시작과 같음).
B34·b26pre·backfill·B26-1·B33·G1·FU·D0a는 **모두 미병합** -- 복제본 커밋 사슬: `dd60db6` → **FU 대역**(`design_report.py` 28행·`audit_current_forced.py` 38행 앞에 `from __future__ import annotations` -- design §6.5와 같은 자리) →
**UD-0 문서 개정 v8.5 적용**(`p3_doc_amendments.md` §1 (a)(가)~(d)·§9 (e)~(h)의 '현재 `plan.md:N`' 블록 8개 -- 521·522·523·524·525·526·528·529행, '현재' 전부 정확 일치 단언 뒤 교체, 522행은 D-19 (가) 문안) → **G1 시제품**(`_drafts/g1_kit/install_proto.py` `5790433c…` + `g1_core.py` `b3c4e391…`, 작업 트리).
비교 가지: `amd84fu`(개정 v8.4까지 -- (h) 없음), `amd85nofu`(v8.5 개정, FU 없음), `regen85`(`amd85fu` + 재생성 모의).
D0a는 시제품 `_drafts/p3kit_d0a/move_plan_proto.py`(`d2f3da97…`, `plan`만)에 **D0a 계약 2 v8.4/v8.5 문언만 보고 다시 얹은 D-31 규칙**의 스크래치 사본(생성기 `mk85.py` `ead4caec…`, 작업 끝에 삭제): 모듈 docstring(파일 첫 문장 문자열 `Expr`) 대상 제외, A-3·A-4 칸 MOD 먼저 앉히기(단조 -- 반복은 올리기만),
A-2·A-4·A-5 승격(max(기준, R(u) 배정 MOD 최댓값 -- N3.10 번호만), 결과가 MOD7이고 기준이 MOD7이 아니면 기준 -- 상한), A-3은 상한 없음, A-K(`--keep` 파일의 A-1~A-4 밖 단위 → 그 파일), A-5(참조자 최소 MOD → 승격), A-6(참조자 없음 → R(u) 최댓값),
A-7(고정점 뒤 미배정이고 N3.10 파일 → 그 MOD, 다시 고정점), `import_conflicts` (i) 이름 import 갈림·(ii) k 파일 출처 다름(k 파일이 있을 때)·(iii) 충돌 출처·(iv) `__future__` 기능 집합 갈림. 측정 스크립트는 `_drafts/p3kit_d0b/`(`analyze_plan.py`·`regen_registry.py` 그대로)와 스크래치 사본.
**전부 관찰 -- 기대값 근거 아님, D0b base에서 다시 잰다.** 앞 판(v8.4, `C:/g179`)의 수치 `reg_mismatch` 78·`import_conflicts`(FU 없이) 3은 (h) 전 값이다(`amd84fu` 가지가 그대로 재현 -- 아래 3).
시제품 한계: G1 시제품 `units`는 문장 단위의 키를 `<stmt:해시>`로 내서 D0a 계약 2(바인딩 이름을 이은 것)와 다르다 -- 상수 행 7개(`_KNEE_L_CACHE`·`_COMPENSATION_REGISTRY` 등)가 시제품에서는 비대상으로 센다.)

1. 이름 충돌(앞 판 그대로 -- 계약 test 경로 무변경): `ls A/tests/contracts` → `test_p3_*`·`registry_dest` 0. `git grep "glob("` → contracts 전수 스캔은 `test_ic_markers_match_plan.py:91`(`gmid_ic` 표식만)·`test_d_*`·
   `test_ts3_no_print_verdicts.py` -- 피할 것은 삭제 이름 AST 참조와 `print`(계약 11 (f)). `p3-registry-dest`·`test_p3_registry_dest` 저장소 참조 0.
2. 사실(레지스트리): `regen_registry.py`(D0a 계약 2 A-4 표 정의) → 함수 표 **15개**, 행 분류(아래 3의 `amd85fu` `plan` 기준) 대상 **347**·중첩 7·비대상 **25**(하네스 `canonical_spec`·`_spec_*`·`SPECS`·`run`·`derived_spec`, LUT 도구 `_gen_netlist`·`_run_combo` 등,
   `topology_to_markdown` 4행, 상수 7행)·같은 키 다른 MOD 0·한 행에 단위 둘 이상 0, 대상 행 중 base 칸 = 배정 줄기 128·다름 219. `grep -c "보류(Phase 3)"` → **9**, `보류(Phase 4)` 14. N3.10 표(개정 적용) 머리 4열·10행.
3. **`plan`(D-31 변형) -- `amd85fu`(FU 대역 있음) / `amd85nofu`(없음)**: exit 1 / 1, `upward` **0** / 0, `cycles` **0** / 0, `unassigned` **0** / 0, `conflicts` 0 / 0, `import_time_high` [] / [], **`import_conflicts` 0 / 2**
   (FU 없이: `topology_authoring`(ACF ∅ 대 SR·SD `annotations`)·`instance_report_builder`(DR·ACF ∅ 대 SD) -- 둘, design §6.5 v8.5·부록 A F5v85와 같다; v8.4 판의 `gmid_sizing_engine`(DR ∅)은 `_kv_table`이 MOD9로 가서 빠졌다), MOD7 파일 밖 MOD7 배정 0 / 0,
   `reg_mismatch` **79** / 79(= v8.4 판 78 + `_kv_table` 칸 1), 배정 **403**(A-4 229·A-5 64·A-1 60·A-2 38·A-6 7·A-K 2·A-7 2·A-3 1), 대상에서 뺀 모듈 docstring 5(SR·SD·TL·DR·ACF). MOD별: `gmid_lut` 8·`topology_authoring` 18·`circuit_state_graph` 82·
   `gmid_sizing_engine` 102·`circuit_metrics` 21·`theta_search` 11·`stick_diagram` 110·`sizing_layout_convergence` 32·`instance_report_builder` 17·`audit_current_forced`(A-K) 2. A-7 = `MultiLeafHubParityVerdict`·`check_multi_leaf_hub_parity`,
   A-K = `render_report`·ACF `sys.path.insert` 문장, A-3 = `run_full_circuit_audit`(MOD7). **`_kv_table` = `instance_report_builder.py` A-1**(`amd84fu`에서는 `gmid_sizing_engine.py` A-4 -- 그 밖의 단위 배정은 `amd84fu`와 같다: `amd84fu` = 일곱 중 여섯 0·`reg_mismatch` 78·
   A-4 230·A-1 59, v8.4 판 수치 재현). design 부록 A F5v85(`C:/g185`)의 `amd85fu`·`amd85nofu`·`amd84fu` 수치와 같다.
4. **재생성 모의**(`amd85fu`에서 `regen_registry.py --write`(대상 행 칸 = 배정 줄기, 표마다 `근거 규칙` 열) + `보류(Phase 3)` → `보류(Phase 4)` 9칸 → 측정 커밋 `regen85` → 같은 변형으로 `plan` 재실행): exit **0**, `verdict` PASS, 판정 목록 일곱 모두 빈 목록, MOD7 밖 0,
   `reg_mismatch` 79 → **0**, (키 → `mod`) 사상 차이 **0**(멱등, 키 차이 0), `rule` 분포 A-4 239·A-5 60·A-1 60·A-2 39·A-6 3·A-K 2(A-7 2 → 0, A-3 1 → 0 -- 열이 A-4 입력이 되므로, 계약 6 (c)), 레지스트리 diff 409+/409−, 대상 행 347 모두 칸 = 줄기.
   `보류(Phase 3)` 0·`보류(Phase 4)` 23. 그 커밋에서 `reg_check.py --registry … --root …` exit 0 `발견 0`, `test_reg_check.py`·`test_reg_check_df23.py`·`test_df23_inventory.py` **210 passed**(`-c tools/gates/pytest_gate.ini --gmid-phase=3 --gmid-strict=`).
5. **(d)-1 표본 대조**(스크래치 스크립트, 기대값은 위 표 -- 도구 출력과 비교만): 표본 **25개**(B26-1 뒤 둘 제외 -- 앞 판의 '24개·행 있는 22개'는 셈 오류였다, 표의 ○ 행은 23) 모두 `amd85fu` `plan`·재생성 뒤 `plan`의 `mod` 줄기 = 기대, 행 있는 **23개** 모두 재생성 뒤 칸 = 기대.
   base 칸 = 기대는 **1/23**(`run_topology_pipeline_with_finger_fixup`). 표본 단위 모두 `upward` 간선에 없다(목록 0). `NameCollisionVerdict` 레지스트리 칸 `stick_diagram`(A-4라면 MOD7)이 A-2로 MOD3 -- 우선순위 확인 표본. `_kv_table` 칸 `〃`(A-4라면 MOD4)이 A-1로 MOD9 -- 토큰 우선 확인 표본.
   원문 확인(손적용 근거): `stick_diagram.py:8478` `class NameCollisionVerdict`·`:8486` `def check_topology_name_uniqueness`·`:8610`(`load_topology` 안 호출)·`:8956` `def _topology_ref_relpath`·`:8990`(`save_instance_json` 안 호출),
   `solve_diode_stack_current`·`check_multi_leaf_hub_parity`의 엔진 안 등장은 docstring뿐(`git grep`), 레지스트리 221행 첫 토큰 `NameCollisionVerdict`, §3 '기타 모듈' 표 249~258행 `〃` 사슬(파일 열 없음), `_theta_evidence_for_pair`·`_as_set`은 ACF 단위(`audit_current_forced.py:47` `def _as_set` -- FU 대역 뒤 줄 번호),
   `save_html_report` 몸체는 `render_html_report`만 부른다(`_kv_table`은 `render_html_report` 안 호출), 계획서 N3.10 MOD9 행(개정 뒤)의 `_kv_table` 토큰은 한 행에만 있다.
6. **거부 입력 실측**(`regen85` 사본에 하나씩 커밋, 같은 변형 `plan`): R-A1 `upward` 1(`save_html_report -> render_html_report`)·`reg_mismatch` 1·`cycles` 0(v8.4 판은 `cycles` 1 -- (h) 뒤 0이 된 관찰; T-A는 `upward` 단언에서 FAIL하므로 겨눔은 같다), R-A2 `conflicts` 1, R-A3 `unassigned` 1(`sizing_recipe.py::_p3rd_orphan`), R-A4 `import_time_high` 1,
   R-A5 `import_conflicts` 1(MOD9), R-A6(새 -- `_as_set` MOD7 토큰) MOD7 밖 1(`audit_current_forced.py::_as_set`)·`reg_mismatch` 1·그 밖 목록 0, R-B2 exit 0·목록 모두 빈 목록(`quantize_L` `mod` `theta_search.py` 그대로 -- T-B 정확 일치만 잡는다),
   R-E1(새 -- `_theta_evidence_for_pair` 칸 → `theta_search`) exit 0·일곱 목록 모두 빈 목록·MOD7 밖 0·`_theta_evidence_for_pair` `mod` = `theta_search.py`(A-4)·다른 단위 사상 차이 0 -- 대상 행 칸 = 줄기라 T-B 통과, (d)-1 대조(위 5의 스크립트)는 그 표본 하나를 잡는다(`plan` `mod`·칸 모두 기대 `instance_report_builder`와 다름).
   **옛 판 입력의 v8.5 결과(바꾼 이유)**: 옛 R-A6(MOD7 행에 `_kv_table`) → `conflicts` 1(MOD7·MOD9 두 행 토큰)·MOD7 밖 0 -- T-A가 MOD7 단언이 아니라 `conflicts` 단언에서 FAIL해 R-A6의 겨눔이 맞지 않는다.
   옛 R-E1(`_kv_table` 칸 변경 -- 재생성 뒤 칸 `instance_report_builder`를 `gmid_sizing_engine`으로) → exit 1·`reg_mismatch` 1(A-1 토큰이 칸을 덮어 배정이 MOD9 그대로) -- T-A가 잡으므로 '도구와 열이 함께 틀림' 표본이 아니다.
   나머지(R-A7·R-B1·R-B3·R-C*·R-D1)는 test 단언이 직접 보는 문자열이라 `plan` 측정 대상이 아니다.
7. 기존 레지스트리 소비자(앞 판 그대로): `git grep -l function-registry -- '*.py'` → `tests/tools/reg_check.py`(열을 머리 이름으로 찾음, `처리` 값 `^보류\(Phase [0-9]+[a-z]?\)`)·`contracts/test_reg_check.py`
   (실제 저장소 `test_main_on_this_repository_is_clean`·`test_repository_section7_lacks_r4_names`), 나머지는 `.ai/verification/**` 증거 스크립트 6개(기록된 base에서 재실행 -- 대상 아님). `tools/gates`의 레지스트리 읽기 0.
8. 원칙: topology 무관·이름 무관 -- 계약 12, 손으로 쓰지 않음 -- 계약 6·9, 만들면 배선 -- 계약 3(이후 모든 card V1·DoD E4, FU의 `import_conflicts` 배선), 조용한 기본값 금지 -- 계약 8(멈춤), 재계산 없음 -- 계약 11 (c),
   게이트는 실제로 거부한다 -- '거부해야 할 입력' test별 표와 실측 6.
9. **V 도구 모양**(앞 판 키트 `sim_chain_vtools.sh`, `5f643a9` 사슬 -- 이번 판은 바뀌는 파일 모양(레지스트리 + 새 contracts test 하나)이 같아 재실행하지 않았다): V3 PASS `targets []`·`mutants 0`, V5 PASS `diff_paths []`, V6 PASS `targets []`,
   V7 PASS `new_defs []`, V4 `--interface-card`(생성본 -- 기존 함수 0·신규 0)만 → **ERROR '피검 심볼이 없다'**, `--module-dir tools/migrate --subject move_plan:main` → PASS(판정 문장 모두 NO-SUBJECT).
   V4 선례 원문 확인: `.ai/verification/20260922-ts7-ic-xfail.json`("interface card만으로 돌리면 ERROR(피검 심볼 없음 -- card 두 표가 비어 있다…)라 (b) --module-dir tools/gates --subject merge_gate:…"),
   `.ai/verification/20260923-v4-decision-exempt.json`("--module-dir tools/gates --subject test_lint:main -- interface card 두 표가 모두 비어 있어 card만으로는 '피검 심볼이 없다' ERROR").
10. 쓰기 경로(계획 N3.12.2, 603·626행): 레지스트리 = gmid-code-author(오케스트레이터 `docs/03-analysis/**` 행은 레지스트리를 제외한다), `A/tests/contracts/test_p3_registry_dest.py` = gmid-test-author,
    N3.10 개정(계약 8) = 오케스트레이터 `docs/01-plan/**` + 승인 기록. role_paths: 레지스트리·contracts test 모두 게이트 코드 밖 → `gate_change: no`.
11. 계획서 소비자: 지우거나 옮기는 이름 없음(열 값만 바뀐다). `git grep -n "이관 목적지" -- docs/01-plan docs/02-design` → 계획 517행 문장(이 card가 이행), design 문서들의 설명 -- 줄 바뀜 없음.
12. 미배선: 새 def 0(test 보조 함수만). 도구(`move_plan.py`)의 배선 (i)이 이 card다(D0a 계약 9 -- "D0b 병합 전에 (i)이 없으면 D0b card가 막는다"; (i)의 exit 0 단언에 `import_conflicts`가 든다).
13. V3 규모: 바뀌는 소스 def 0 → `targets []`(레지스트리는 `_is_source` 밖). 실행 비용은 V1에 `plan` 1회(19~33초)가 card마다 더해진다(D0b 뒤 Phase 3 card M1~M6·M8·M9·M10·T1·F1·F2 12개(T0가 D0b 뒤면 13개) + DoD E4·E5 두 전체 실행).
14. 같음 판정: 칸 비교는 문자열 정확 일치(앞뒤 공백은 칸 나누기에서 제거), 사상 비교는 정렬된 (키, `mod`) 튜플 목록, 판정 목록은 `== []`. red 모양: 허용 예외 `AssertionError`만(계약 11 (a)), 새 키워드 인자 없음.
15. `parse_spec_card`(v8.5 개정 판 -- gate `dd60db6` `tools/gates`를 `git archive`로 `C:/g189/gt`에 꺼냄, `expect_id` = 이 id): exit 0, 머리 `id` 일치·`phase` 3·`evidence_type` red-green·`gate_change` no·`approval` 1개(`20260930-30-module-split-design`),
    절 11개(양식 그대로), `activated_ic_case`·`noop_activation_id` 빈 목록. 같은 판 `interface_card.py <이 초안> --root <복제본>` → exit 0 '기존 함수 0개', 두 표 모두 빈 표
    (oracle 절 (d)-1 표의 백틱 엔진 이름은 생성기가 잡지 않는다 -- V4 DESIGN-GAP 우회 전제 유지). 주의(v8.5 개정 중 관찰): '관찰 가능한 계약' 절에 엔진 함수 이름을 백틱으로 적으면 생성기가 '기존 함수'로 잡는다
    (계약 8 (d)에 HTML 표 도우미 이름을 백틱으로 적은 중간 판 → '기존 함수 1개' `design_report._kv_table`) -- 그 절에서는 백틱 없이 적었다.
