# UD-6 편집 독립 검토 ([D-11] (가) · [W-1] (가)) -- 2026-10-02

검토자 = 작성자 아님. gate `master` `4a286f0`(작업 시작·끝 같음). 실제 저장소는 `git -C` 읽기만. 스크래치 `C:/g231`만(`git clone -c core.autocrlf=false --no-local` 작업 트리 → origin 제거·빈 hooksPath, TMP/TEMP `C:/g231/tmp`). 작성자 `p3ud6_kit/out/`은 증거로 쓰지 않았다(내 출력 `C:/g231/out` -- 검토 뒤 삭제). 시뮬레이터(`p3kit_m1/move_plan_sim.py`·`sim5.py`·`mk_reject.py`·`regen_registry.py`)는 D0a 도구가 아직 없어 작성자 키트를 **내 복제본에서 다시 돌렸다**. 그 밖은 독립 스크립트(아래 표시).

## 판정: **B 1 · S 2 · minor 5** -- B1을 고치기 전에는 runbook대로 실행하지 말 것. 승인 기록·T0·D0a·D0b 문서 자체는 수치·인용 모두 재현됐다.

## B (막는 결함)

**B1. runbook §1·§2-7 순서가 design 05 §12와 EL1 push 규칙에 어긋난다.** runbook은 "단독 문서 커밋을 지금(다음 gate 슬롯) 넣는다", "card 35(V3 범위) 병합과 무관하게 어느 슬롯에든 들어갈 수 있다(문서·승인 기록만 -- 게이트 판정 대상 경로 아님)"라고 적었다.
* design 05 §12 머리: "역할 브랜치가 있는 동안 문서 커밋의 gate push는 EL1이 거부". gate 판 `tools/gates/role_hooks.py` `_judge_push`: `git push gate master:master`이면 `refs/heads/role/` 브랜치가 하나라도 있을 때 **경로와 무관하게** 거부("진행 중인 변경이 있어(역할 브랜치 …) 문서 커밋 push를 거부한다").
* 지금 실제 저장소: `role/test/20260930-v3-changed-stmt-scope`(4a286f0)와 worktree `wt/20260930-v3-changed-stmt-scope-test`가 있다(card 35 진행 중). 그래서 §2-6 push는 거부된다.
* 더 나쁜 경우: push 전에 로컬 `master`에 두 커밋을 먼저 만들면 card 35 §12-8(`git merge --ff-only gate/master`)이 로컬 master 분기 때문에 실패한다.
* 고칠 것: §1의 "지금" → "card 35 정리(§12 '정리' -- 역할 브랜치 0) 뒤, 다음 card 순서 0 전". §2-1 시작 확인에 `git -C <repo> for-each-ref refs/heads/role/` 빈 출력 추가. §2-7 문장 교체. 선례도 같다: card 35 문서 커밋 `a5566c8`은 그 card 역할 브랜치 생성 전.

## S (보완)

**S1. 승인 기록 머리 `scope`와 본문 조건 목록이 다르다.** `scope`: "`conflicts`·A-1 원천 `upward`·`cycles`·`import_time_high`·MOD7 밖 배정이 나오면 멈추고". 본문 '범위 설명' 조건과 D0b 계약 8·`d0b_launch.sh` S-5: `conflicts`·`upward`(원천 무관)·`cycles`·`unassigned`·`import_time_high`·`import_conflicts`·MOD7 밖.
→ `scope`에 `unassigned`·`import_conflicts`가 빠졌고, `upward`를 'A-1 원천'으로 좁혔다. 파싱되는 쪽은 `scope`다. 본문과 같은 일곱 항목(여섯 목록 + MOD7 밖)으로 맞출 것.

**S2. T0 계약 11 (b) `is`와 `t0_briefs.md` auditor 문단의 측정법이 다르다.** card: "같은 객체(`is`)". brief: "같은 프로세스에서 두 판을 import하지 말고 판마다 새 프로세스로 모듈 이름·`__qualname__`·`__module__`을 대조".
→ 이름 대조는 `is`보다 약하다. 그런데 T0은 엔진을 바꾸지 않아 E 모듈이 병합본에 그대로 있으므로, **병합본 한 프로세스에서 `test_mod.<이름> is E.<이름>`**으로 card 그대로 잴 수 있다. brief를 card 문언(`is`)에 맞출 것. base 대조는 수집 id·판정 비교만으로 충분하다.

## minor

* m1. runbook §2-2 `python -B _drafts/p3fq_kit/variant.py <repo> qtok`: 오케스트레이터 cwd(`chip-design-skills`)에서는 상대 경로 `_drafts/`가 풀리지 않는다. `wt/_drafts` 절대 경로로 적을 것. §6 재현 명령도 같다.
* m2. 승인 기록 '효과'의 "MOD1 단위 7 → 8"(계약 키)과 질문 선택지의 "MOD1은 8단위 그대로"(시제품 해시 키 -- `hash_q`에서는 `_QUERY_CACHE_MAX`가 이름 단위가 아니다)는 둘 다 사실이다. 키가 다르다는 한 문장을 범위 설명에 더하면 독자가 모순으로 읽지 않는다.
* m3. '사용자에게 보인 것' 3의 `ce687938` 인용: 원문은 `**(M1-2) 상수 \`_QUERY_CACHE_MAX\`의 배정**:`(굵게)다. '요약 -- 원문은 jsonl'이라고 밝혀 결함은 아니지만, 큰따옴표 안 문자열은 원문과 같게(굵게 표시 포함) 두거나 따옴표를 빼는 편이 바이트 대조 원칙에 맞다.
* m4. `d0b_launch.sh` S-7은 `_QUERY_CACHE_MAX`의 `mod` 줄기만 본다(`gmid_lut`). runbook §3과 승인 기록 '재검토'는 `A-1`까지 요구한다. 자동 확인에 rule을 더하거나, 수동 확인 항목으로 runbook에 적을 것.
* m5. T0 계약 11은 interface card를 '기존 함수 6개'로 유지하려고 nmcnr_predict_ac_response를 백틱 없이 적었다. 6개 유지는 확인했고(아래 2) 기능 문제는 없다. 다만 생성기를 형식으로 피한 것이라, 그 이유 한 줄이 card '작성 전 실측'에만 있다. brief 계약 11 문단에도 "이름은 표·brief가 정본, interface card에는 없다"를 적어 두면 test-author가 헷갈리지 않는다.

## 확인 결과

### (1) 승인 기록 `approval_20261002-p3-d11-query-cache-max.md`
* 사용자 원문 바이트 대조(세션 jsonl 10877·10883행, 독립 Python 대조): 아래가 모두 기록 안에 바이트 그대로 있다.
  * 답 `> (가) 계획 표 MOD1에 추가 (Recommended)`와 `답: "…"`.
  * [D-11] 질문 전문, 두 선택지 라벨·설명.
  * [W-1] 질문 전문·답.
  * headers `[D-11] 표 1건`·`[W-1] shim`.
  * uuid `07519f8c…`·`8b8cfd7b…`, 시각 `04:35:31.525Z`·`04:38:47.216Z`.
  * `toolUseResult.questions` == tool_use input.
  * 메시지 `845a9ec0` 원문 같음, `cd90c928` 인용 같음. 질문 직전(04:34:39~04:35:31) 사용자에게 보인 다른 text 블록 없음.
* `target`: 스크래치에서 4a286f0 + 521행 교체(앵커 1회, '현재' 문안 = 521행 바이트 같음, `git diff --numstat` 1/1) → blob `8f6e21db…`.
  * gate 판 `merge_gate.py diff-hash` = `441b80e153a5a9e9174986ab069a50088e687448fbac3167ce864ccf16799a99` -- 기록·runbook 사전값과 같다.
  * `p3fq_kit/variant.py qtok` 출력 diff와도 같은 바이트.
  * 실제 작업 트리는 CRLF(`core.autocrlf=true`, 시스템 설정)이지만 `newline=""` 쓰기라 정규화 blob이 같다.
* `plan_tables_hash`: 전·후 모두 `7167e02839f86c4ecbcd91a63a9833c4d83a8aab8008bfe2d8cfc36206d2596d`(gate 판 `plan-tables-hash`). 바뀐 줄이 판정 표 밖이라는 주장이 맞다.
* `parse-approval`: 자리표시자를 실제 값으로 채운 사본(`<id>.md` 이름)은 통과, `id` 일치.
* 선례 대조: UD-0(`6c8287f` → `36e170e`), Q-P2DOD-E2(`1a464e4` → `dc196cd`)와 같은 모양이다 -- 절 구성, 문서 커밋 `Role: doc` + `Change-Id`. gate EL4 `judge_commit_change` 기준으로 판정 표 불변이면 문서 커밋에 승인 기록이 필요 없고, `.ai/approvals/**`는 오케스트레이터 경로 `없음` 조건이다.

### (2) T0 계약 11
* 독립 AST 스캔(`git show 4a286f0`, E 최상위 def·class·대입과 N3.10 파일 import 제외 정의):
  * 3파일 모두 24행. 이름 수 8·52·4.
  * 잔여 TL `math`(TL 26행 `import math`). SR `_dc_replace`(42)·`json`(37)·`math`(38)·`nmcnr_predict_ac_response`(1411, 모듈 최상위)·`np`(45). DR `os`(30).
  * = 3줄·7이름·서로 다른 6. 사용 횟수(2 / 31·11·2·1·1 / 8)와 DR 13행 `import os`도 card와 같다.
* 약화 아님: import 줄만 바뀌고 test 함수·기대값 불변, (c) 잔여 0과 (b) 객체 동일이 auditor 판정이다. 거부 입력 두 가지(`math` 남김 → (c) 1, `import cmath as math` → (b) 불일치)는 판정 정의상 성립한다.
* 계약 9 금지 토큰: 세 파일 24행에 0. 새로 쓰는 24행 `+` 줄이 걸리지 않는다.
* `is`는 성립한다: 표준 모듈과 `dataclasses.replace`는 `sys.modules`로 같은 객체, nmcnr은 SR도 `topology_library`에서 묶는다. 측정법은 S2 참고.
* interface card: 새 판·pre-ud6 판 모두 gate 판 `interface_card.py`로 '기존 함수 6개', 출력 파일 바이트 같다. `parse_spec_card` 통과(T0·D0a·D0b 셋 모두, D0b `approval` 2개).

### (3) D0a·D0b 재측정 (내 복제본 `C:/g231/r`)
사슬: `4a286f0` → FU 대역 → G1 시제품 = B `5a28702` → 521행 = Q `6ce82fd` → regen + hold_swap = RG `3f7c69f`. 계약 키 `MP_STMT_KEY=names`.

**B(토큰 없음)**
* exit 1, `upward` 1(`SemiEmpiricalGmIdLUT -> _QUERY_CACHE_MAX`), `cycles` 1(`gmid_lut`↔`gmid_sizing_engine`).
* `reg_mismatch` 79, 배정 403, A-4 236.

**Q(토큰)**
* 여섯 목록 0, MOD7 밖 0, `reg_mismatch` **80**, 배정 **403**.
* 규칙 A-4 235·A-5 57·A-1 61·A-2 38·A-6 7·A-K 2·A-7 2·A-3 1.
* MOD별 `gmid_lut` 8·SE 104·SD 111·SLC 30·IRB 16·TA 18·CSG 82·CM 21·TS 11·ACF 2.
* B 대비 사상 차이 1(`_QUERY_CACHE_MAX` MOD4 → MOD1, A-1).

**hash 키 Q:** `reg_mismatch` 79, A-4 229·A-5 63, SE 102·SD 110·SLC 32·IRB 17.

**RG:** exit 0, 일곱 목록 0, 사상 차이 0, A-4 245·A-5 53·A-1 61·A-2 39·A-6 3·A-K 2. diff 409/409, 대상 354·중첩 7·비대상 18, `보류(Phase 3)` 9 → `(Phase 4)` 23.

**(d)-1과 다섯 test 모사**
* (d)-1: 28행(B26-1 둘 제외 26, 행 있는 24). Q `plan` 대조 불일치 0. `_QUERY_CACHE_MAX` 행은 S-7 파서가 읽는 표 안에 있다.
* Q: T-A 80·T-B 225·T-C 머리·T-D 9·T-E 23. RG: 다섯 모두 PASS.

**거부 입력 14개:** 모두 spec 표대로 재현. R-A2는 배정 402·대상 행 353·`conflicts` `compute_metric`(MOD5·MOD2).

**독립 확인**
* `_QUERY_CACHE_MAX` 사용처는 `sizing_recipe.py:390`(`SemiEmpiricalGmIdLUT._query`) 하나.
* 레지스트리 277행 함수 칸 첫 토큰이 그 상수다.
* '모든 토큰' 읽기 변형(시뮬레이터 사본 한 곳 수정)으로 재면 B·Q 모두 `upward`·`cycles`가 하나씩 늘고(`load_topology -> check_topology_name_uniqueness`, `circuit_state_graph`↔`stick_diagram`) 배정 차이 5다. D0a UD-6 문단 주장과 같다.
  * 따라서 첫 토큰 읽기는 정지 여부를 바꾸는 선택이다. 그래도 UD-0 승인 근거 실측(F5v85·시제품)과 같은 읽기라 기준 변경이 아니라는 card의 설명은 타당하다.
  * `reg-first-token` 합성 단계의 기대(`upward` `src.py::c -> src.py::a`, 칸 `mj`면 exit 0, 모든 토큰 구현은 `upward` 2로 FAIL)도 규칙상 맞다.

**`d0b_launch.sh` S-1 (`approval_rc` + `cond_1` 원문을 추출해 내 트리에서 실행)**

| 트리 | 결과 |
|---|---|
| 토큰 없음 + 승인 기록 | 3 (토큰 없음) |
| 토큰 + 승인 기록 | 0 |
| 토큰만 | 3 (승인 기록 없음) |
| 토큰을 MOD2 행에 | 3 |
| 승인 기록 형식 위반 | 3 (parse-approval 실패) |

* 토큰 없는 트리를 거부한다.
* `APPR_IDS`는 spec 머리 `approval` 두 줄과 같은 순서다.

### (4) runbook·EL 규칙
* 순서는 B1.
* 경로 권한: 오케스트레이터 `docs/01-plan/**`·`.ai/approvals/**` 조건 `없음`이다. 판정 표가 불변이라 EL3·EL4가 문서 커밋에 승인 기록을 요구하지 않는다.
* 트레일러 `--trailer`, push `master:master` 단독 형태는 EL1 허용 형태와 맞다(역할 브랜치 0일 때만).
* 실행 시점 영향: `d0a_launch.sh`·`d0b_launch.sh`의 `MEAS_PATHS`에 계획서가 있어, 문서 커밋 뒤 두 card의 measured 앵커는 재측정 대상이 된다. runbook §2-7이 이미 이를 적었다.
* `m_cards_plan.md` §6은 14:36 판에 남아 있다.

## 격리 확인
* 실제 저장소 `HEAD` = `gate/master` = `4a286f0`, `status --porcelain` md5, reflog 첫 줄 -- 시작과 끝이 같다.
* 스크래치 `C:/g231`만 썼고 끝에 지웠다.
* 작성자 `p3ud6_kit/out/` 최신 파일 시각은 14:07 그대로다(내 실행이 쓰지 않음).
