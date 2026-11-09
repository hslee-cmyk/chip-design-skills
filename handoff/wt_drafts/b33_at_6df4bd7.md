# B33 사전 재측정 -- gate master `6df4bd7`(b26pre 병합·판정 기록 + backfill 병합·판정 기록 + B26-1 승인·spec card) (2026-10-07)

읽기 전용 사전 측정. B33 초안(`draft_b33.final.spec.md`)·`b33_launch.sh`·키트 스크립트는 고치지 않았다. 실제 저장소는 읽기만 했다(HEAD·gate master `6df4bd7`, status는 시작 때와 같음).
격리 복제본 `C:/g420`(TMP·TEMP 그 안, origin 제거, 빈 hooksPath, `-c core.autocrlf=false`, 모래상자 gate `C:/g420/gate.git`를 remote gate로) -- 끝나고 삭제.
키트(`run_headline.sh`·`run_attack33.sh`·`run_redteam_variants.py`·`a33_table.py`·`summarize.py`)는 무수정 실행.
출력: `_drafts/b33_kit/out/head_6df4bd7/`(head.txt·m1·m4·m5·summary.json·p3435.jsonl·headline.log·a33.log), `a33_6df4bd7.{jsonl,table.md}`.

## 0. launch 모드 실행 결과(모래상자 `--repo C:/g420/r --state C:/g420/st/… --wt C:/g420/wt`)

* `conds`: **이 스크립트에 없는 모드다** -- 사용법 오류(exit 2, `kit-cmds|pre|local|doc|card|appr|final|after-push`만 있음). 다른 launch 스크립트의 모드 이름과 혼동한 것으로 보인다.
* `kit-cmds`: 정상 출력(gate master 6df4bd7). 결함 1개(아래 §5 K1): ④ 34·35 미리보기 명령에 `HOME`·`APPDATA`가 없다.
* `pre --pred-missing-ok`(초안 그대로): 선행 5개 판정 기록 확인(B26-1만 없음 -- 허용) 뒤 **V7 그래프 입력 대조에서 멈춤**(measured rev `dafe5cf` 대 6df4bd7, 286파일). 예상대로.
* `pre --pred-missing-ok --draft-spec <사본>`(사본 = 초안 끝에 아래 §1 수치로 쓴 6df4bd7 모의 '(착수 재측정…' 문단 하나만 더함, `C:/g420` 안): **pre OK** -- 사실 문장 grep 전부 통과,
  문서 패치 applied 2(V7 행 321·거부 줄 338)·재실행 already applied, headline 불변식 10개 성립·문단 수치 8묶음 일치, `_approved_ids` 40, plan_tables_hash `16b899d1…aec1`.
  즉 문단만 다시 쓰면 지금 rev에서도 pre가 통과한다(실제 착수는 B26-1 병합 뒤라 그때 다시 잰다).

## 1. 머리 수치 -- 6c724de 대 6df4bd7

| 항목 | 6c724de | 6df4bd7 | 차이 |
|---|---|---|---|
| 파일 / src def | 128 / 494 | 130 / 494 | +2 파일(`test_b26pre_existing_paths.py`·`test_b26_backfill_interdig.py`), src def 0 |
| test 함수(test_nodes) | 567 | **591** | **+24**(b26pre 19 + backfill 5) |
| 미도달 base union / +R3 / 두 벌 | 115 / 116 / 116·122 | 115 / 116 / 116·122 | 0 |
| 미도달 개정(+R3, 두 벌) | 39 (39/39) | 39 (39/39) | 0 -- base·개정 미도달 목록이 6c724de와 같음(목록 비교), `vs_old`(0f23786) 차이 4종 모두 빈 목록 |
| 비운영 노드 누수(noR3 → 개정+R3) | 66 → 0 | 66 → 0 | 0 |
| 면제 두 id 도달 | 없음 | 없음 | 0 |
| V3 쌍 base → 개정 | 37,053 → 48,783(1.317배) | **39,424 → 52,591(1.334배)** | **+2,371 / +3,808**, 문단 표기 1.32배 → **1.33배** |
| 인벤토리 0 base → 개정 | 82 → 19(회귀 0) | 82 → 19(회귀 0) | 0 |
| 중앙값 base → 개정 | 64 → 70 | **65 → 73** | **+1 / +3** |
| 옛 간선 제거(전부 dunder) / 도달 감소 | 4 / 0 | 4 / 0 | 0 |
| m5 표본(개정) width_from_id_density / compute_metric / `_evaluate` / apply_theta_feed / kcl_series_union / optimize | 349 / 90 / 63 / 69 / 75 / 63 | 373 / 102 / 64 / 70 / 87 / 64 | +24 / +12 / +1 / +1 / +12 / +1 |
| 과거 V7 쌍 / 기록 | 32 / 33 | **33 / 34** | **+1**: `20261001-b26-backfill-interdig-final-audit`(`863a037`→`0bb2278`, new_defs 0). 33쌍 전부 base·시제품 verdict·unreached·uwa 같음, 전부 PASS, `--config` 전부 head 트리, new_defs 있는 쌍 4 그대로 |

**m4 정규식 사각(새 발견)**: b26pre 판정 기록 V7 근거는 `--base ae1b588… --head e4d5833…`(말줄임표 U+2026)로 적혀 있어 `m4_records.py` PAT(`[0-9a-f]{6,40}\s+--head`)에 안 걸린다
-> 과거 V7 쌍으로 세지 않았다(기록 34 = backfill 하나만 늘어남). 같은 쌍을 같은 세 도구로 따로 재었다(`C:/g420/m4one.py`): base·fixed·draft 모두 PASS, new_defs []·unreached []·uwa [] -- 같음.
그래서 수치가 바뀌는 건 아니고, 표기가 "쌍 33(기록 34)"이면 b26pre 쌍이 빠졌다는 것만 알면 된다(정확히는 33 + 정규식 밖 1). 카드 문장에 남길지는 오케스트레이터 판단(아래 §4 P5).

## 2. 공격 33 · 34/35 미리보기

* 공격 33(30단계): base 13 FAIL / 17 PASS, 시제품 fixed 30 PASS. 변형 xout·bare·nosuper 29/1, draft 24/6, loose 21/9.
  `a33_6df4bd7.table.md`가 `a33_6c724de.table.md`·`a33r3_0f23786.table.md`와 **바이트 단위로 같다**(cmp).
* 34·35 무동작 미리보기(`--only 34-v3-exempt-binding --only 35-v3-changed-scope`, base 도구 대 시제품): 17단계(34 6·35 11) 양쪽 PASS(케이스 PASS 2), 단계 판정·exit가 6c724de `p3435.jsonl`과 34키 전부 같음.
  주의: 첫 실행은 kit-cmds ④ 문장 그대로(HOME·APPDATA 없음) 돌려 양쪽 모두 16 FAIL·1 PASS(exit 2, `BaselineFailed` -- 자식 Python이 사용자 site의 pytest를 못 찾음)였다. `env HOME=… APPDATA=…`를 붙여 다시 돌린 값이 위 결과다(§5 K1).

## 3. 6c724de..6df4bd7 V7 그래프 입력 차이

* `tests/contracts/test_b26pre_existing_paths.py`(593줄, test 19) + `test_b26_backfill_interdig.py`(206줄, test 5): test 함수 +24, V3 쌍·중앙값·m5 증가가 모두 여기서 온다.
* `sizing_recipe.py` `run_matching_safety_with_finger_growth`(11755~11875, +4/−5): def 수 변화 없음. 6452(`super().__init__(message)`)보다 아래라 인용 줄은 그대로.
* `.ai/verification/` 206파일(두 판정 기록 + 증거 디렉터리) -> 과거 V7 쌍 +1(backfill. b26pre는 §1 정규식 사각).
* `tools/`·계획서·design 05 변화 0 -> 인용 줄 전부 그대로: mutate 519·621·661·726(출력 줄), rt 592·666, reachability 69·97·160·175·180·223·230, sizing_recipe 6452(`super().__` 1건). 계획 121·843행 같음.
* `a6eaec3`·`6df4bd7`(B26-1 승인 기록·spec card·interface card)은 docs·`.ai/approvals`만 -- V7 그래프 입력 변화 없음.

## 4. 바뀌어야 하는 card 문장·고정값

| # | 위치 | 지금 | 6df4bd7 값 / 조치 |
|---|---|---|---|
| P1 | 초안 '작성 전 실측' 마지막 '(착수…' 문단(measured rev 단일 출처) | `dafe5cf`, test 556, V3 35,946 → 47,452(1.32배), 중앙값 62 → 68, 옛 간선 3, 과거 V7 쌍 31(기록 32) | 6df4bd7이면 test 591, V3 39,424 → 52,591(1.33배), 중앙값 65 → 73, 옛 간선 4, 쌍 33(기록 34). 나머지(115/116/116·122 → 39(39/39), 누수 66 → 0, 인벤토리 0 82 → 19(회귀 0), 도달 감소 0) 같음. **단 B26-1 병합 뒤 한 번만 다시 쓴다**(6df4bd7 문단은 중간값) |
| P2 | 같은 문단의 공격 33·34/35 문장 | 30단계 13 FAIL / 30 PASS, 변형 표 바이트 같음, 17단계 차이 0 | 그대로 |
| P3 | 인용 줄 문장(mutate·rt·reachability·`sizing_recipe.py` 6452) | dafe5cf 값 | 6df4bd7에서 전부 같음. B26-1이 SR 2207·4293(6452 위)을 고치므로 **6452는 B26-1 뒤 움직일 가능성이 크다**(pre는 출력만 하므로 멈추지 않음 -- 문장 표기만 갱신) |
| P4 | 마지막 문장 "B34·B26pre·backfill·B26-1이 이 card 앞에 병합되면…" | 네 card | B34·b26pre·backfill은 병합됨 -> 남은 것은 B26-1 하나 |
| P5 | '작성 전 실측' 7·문단의 "과거 판정 기록 V7 쌍 N" | 정규식 기준 | b26pre 기록이 정규식 밖(말줄임 해시)이라는 사실을 한 줄 덧붙일지 결정. pre의 불변식 "m4 완료(쌍 수 = 스캔)"는 영향 없음 |
| P6 | `b33_launch.sh` PRED | 6개 | 그대로 -- 실제 `pre`는 B26-1 판정 기록이 gate에 들어올 때까지 멈춘다(설계대로) |
| P7 | 이전 사전 측정 `b33_at_6c7.md` §4 예상 | backfill test +2, b26pre 과거 V7 쌍 +1 | 실측 backfill test **+5**, b26pre 쌍 **+0**(정규식 사각). 다른 예상(미도달·누수 불변, backfill 쌍 +1)은 맞음 |

## 5. 키트 결함(수정은 안 함 -- 후보)

* K1: `kit-cmds` ④ 두 줄(`run_redteam_variants.py … --only <34/35>`)이 `TMP=… TEMP=…`만 준다. Bash 도구 셸은 APPDATA를 자식에 넘기지 않아(launch_common `lc_push_cmd` 주석과 같은 원인)
  vrepo 기준 실행의 pytest import가 실패 -> 양쪽 모두 exit 2 거짓 FAIL. `env HOME=/c/Users/HSLEE APPDATA='C:\Users\HSLEE\AppData\Roaming' …`를 붙이면 된다(③ `run_attack33.sh`·② `run_headline.sh`는 스크립트 안에서 export해서 괜찮다).
* K2: `m4_records.py` PAT가 `…`로 끝나는 짧은 해시를 못 잡는다(§1). 보고 수치에는 영향 없음(그 쌍은 따로 재어 같음).
* (참고) `conds` 모드 없음(§0).

## 6. B26-1이 움직일 것(추정 -- spec card `20260930-b26-rail-accessor-set` 기준, 병합 뒤 kit-cmds로 다시 잰다)

| 항목 | 예상 |
|---|---|
| src def | +1(`stick_diagram.rail_declaration`). `RailDeclaration`은 메서드 없는 frozen dataclass라 노드가 늘지 않을 가능성이 크다. 지우는 def 0 |
| 미도달 115/39·누수 66 → 0 | `rail_declaration`은 `load_topology` 경유 운영 도달(계약 10) -> 두 도구 모두 도달이면 그대로. 위험: 인계 분기 삭제(계약 13)·20함수 `rails` 배선이 다른 def의 유일한 호출 경로를 지우면 집합이 바뀐다 -- 재측정 대상 |
| test 함수 | +(새 `test_b26_rail_accessor.py`의 test 수 -- 계약 1~7·13·14 기준 대략 15~30). 기존 test의 `rails=` 추가·`test_dup_kcl_edges.py` 시그니처 단언 갱신은 함수 수 불변 |
| V3 쌍·중앙값 | 증가(새 test가 `load_topology`·`compute_metric`·`_metric_kcl_residual`을 부르므로 width_from_id_density·compute_metric·kcl_series_union 쪽 표본이 크게 늘 것). 1.33배 비율은 소폭 변동 |
| 인벤토리 0 82 → 19 | 새 def가 test에서 직접 불리므로(계약 1·3) 개정 쪽 0 증가 없음 예상. base 쪽도 test 직접 호출이면 그대로 |
| 옛 간선 제거 4 | 새 test 파일이 `__init__`을 가진 클래스를 정의하면 그 수만큼 +(dunder 폴백 -- B34 때 +1과 같은 모양). 엔진 쪽 새 `__init__` 없음(interface card) |
| 과거 V7 쌍 | +1(B26-1 판정 기록의 V7 근거가 `reachability.py … --base <전체 또는 7자> --head <…>`를 한 줄에 공백으로 적으면). b26pre처럼 `…`를 붙이면 정규식 밖. 이 쌍은 new_defs `[rail_declaration]`이 있어 new_defs 쌍 4 → 5 |
| 인용 줄 | SR 6452가 B26-1의 SR 2207·4293 수정량만큼 이동 가능. pre의 `super().__` 1건 단정은 pathspec `assets/*.py`가 하위 디렉터리(tests)도 덮으므로 새 test에 `super().__…`가 생기면 **pre가 멈춘다**(확인 필요). mutate·rt·reachability 줄은 불변 |
| 공격 33·34/35 | 엔진 무관 합성 케이스라 그대로일 것(30단계 13 FAIL / 30 PASS, 17단계 차이 0) |

결론: 6c724de 대비 바뀐 것은 test 함수(567 → 591), V3 쌍(37,053 → 48,783 => 39,424 → 52,591, 1.33배), 중앙값(64 → 70 => 65 → 73), 과거 V7 쌍(32 → 33, 기록 33 → 34)뿐이고
미도달·누수·인벤토리 0·옛 간선·공격 33·34/35·인용 줄은 그대로다. 초안 문단은 B26-1 병합 뒤 한 번 다시 쓰면 되고, 그 전에 kit-cmds ④의 APPDATA(K1)만 고쳐 두면 착수 재측정이 한 번에 끝난다.
