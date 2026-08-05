# 세션 컨텍스트 (최종 갱신: 2026-08-05, 세션10 끝 — 다음은 세션11)

## 작업 디렉토리
`C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills`

## 지금 상태 (다음 세션이 가장 먼저 할 일)

1. **L1(스키마 3축 분해)+L2(그룹핑 규칙 분리)는 세션10에서 실제 코드로 구현 완료, 커밋도
   끝났다.** `git log --oneline -5`로 확인 가능한 커밋: `645b8bf`(audit 스크립트+M18_bg
   정정) `00e7ebb`(L1+L2 구현) `8409c0a`(M58/M57 정정) `da1ec7b`(folded_cascode 재구성)
   `5b06ae2`(세션8 마지막). **더 이상 미반영 상태 아님** — 세션9 문서가 "설계만 하고 코드는
   안 건드림"이라고 적어둔 부분은 이제 stale하다, 아래 "세션10 결론"이 최신 상태.
2. **`run_harness.py`는 세션10에서도 아직 재실행 안 함.** 세션10은 `stick_diagram.py`/
   `sizing_recipe.py`의 **내장 self-test**(둘 다 exit 0, toy LUT 기반)만 확인했다 —
   `run_harness.py`는 **실제 sky130 LUT + `grid_points_per_theta=2`로 `current_reuse_
   telescopic_ota`를 처음부터 끝까지 돌리는 별도의 더 무거운 검증**이라 self-test 통과가
   이걸 대체하지 못한다. 세션7·8·9 전부 로그가 0바이트였던 문제(원인 미확정 — 버퍼링보다
   "세션이 끝나며 백그라운드 프로세스가 완료 전에 죽는다"는 가설이 유력, 세션10에서 같은
   세션 안에서 다른 스크립트를 백그라운드 실행해 CPU 사용량으로 "살아있고 실제로 계산 중"임을
   직접 확인한 사례가 있음 — 그 경우는 hang이 아니라 그냥 느린 것이었다, 아래 "세션10 —
   run_harness류 백그라운드 실행 모니터링 교훈" 참고)가 `run_harness.py`에도 여전히 재현될지
   **세션11이 처음부터 다시 확인**해야 한다. 이번엔 세션 안에서 끝까지 지켜볼 것.
3. **다음 설계 단계는 L3(walk 선택)와 L4(사이징→레이아웃 연결)** — 둘 다 세션8부터 "미설계"
   상태 그대로다. 세션10이 L4의 실제 사례(box-shape 갭)를 하나 더 실측으로 노출시켰으니
   (`two_stage_ota`, 아래 참고) 논의 시작할 때 그 사례부터 참고할 것.

## 배경 — 이 기능이 뭐고 왜 하는가 (세션5~10 공통, 참고용)

- **WHY**: topology netlist가 Python 코드 하드코딩이면 재현 불가능, agent마다 해석이
  달라짐 — 그래서 `topology.json`(`skills/analog-gmid-design/assets/library/*.topology.json`)
  하나를 유일한 소스로 둔다.
- **권한 경계(중요, 항상 지킬 것)**: `netlist`/`passive_elements`/`ideal_sources`의
  connectivity는 **사용자만 고친다**. `device_roles`/`symmetry.matching_pairs`/
  `symmetry.dispositions`/`sizing_roles`(theta 포함) 같은 **역할·메타데이터는 Claude가
  분석해서 업데이트해도 된다** — 단, **여러 파일/여러 회로에 영향을 주는 엔진 로직 변경**
  (`stick_diagram.py`/`sizing_recipe.py`의 함수 로직)은 이 경계와 별개로 반드시 사전
  논의·승인이 필요하다(세션7에서 이 규칙을 어겨 즉시 원복 지시받은 사고가 있었음 — 세션10은
  L1/L2 엔진 변경 전에 반드시 설계를 다시 보고하고 "하드컷으로 진행해" 같은 명시 승인을 받은
  뒤에만 코드를 고쳐 이 규칙을 계속 지켰다).
- 논문에 없는 값은 "논문 인용"만으로 확정 짓지 말 것.
- **핵심 파일**: `skills/analog-gmid-design/assets/sizing_recipe.py`(gm/ID 사이징, KCL
  엔진) / `skills/analog-gmid-design/assets/stick_diagram.py`(오일러 trail 기반 레이아웃
  엔진) / `skills/analog-gmid-design/assets/audit_current_forced.py`(세션10 신설, 아래
  참고) / `skills/analog-gmid-design/assets/library/*.topology.json`(4개 회로:
  `current_reuse_telescopic_ota`, `folded_cascode`, `nmcnr_amplifier`, `two_stage_ota`).

---

# 세션10 결론 — L1(스키마 3축 분해)+L2(그룹핑 규칙 분리)를 실제 코드로 구현, self-test
# 전체 통과, 그 과정에서 진짜 버그 3건 발견·수정 + audit 스크립트 신설

세션8/9가 설계만 하고 코드는 건드리지 않았던 L1/L2를, 세션10이 실제로 구현했다. 요약:
**"같은 gate+rail 공유만으로는 매칭 근거가 안 된다"는 세션8~9의 반복 원칙이, L1/L2를
실제 코드로 옮기는 과정에서 스스로를 검증하는 도구(축A 레일 제외, audit 스크립트)가 되어
같은 유형의 실제 버그를 3건 더 잡아냈다** — 이게 이번 세션에서 가장 중요한 결과다.

## A. L1 — 스키마 3축 분해 구현 완료

`kind`(`diff_pair`/`current_mirror`/`branch_symmetric`/`current_matched`) 4종 문자열을
폐지하고, `symmetry.matching_pairs`의 각 항목에 두 필드를 직접 선언하도록 4개
`topology.json`(32건, `_TEMPLATE.topology.json`은 제외) 전부를 마이그레이션했다:
```json
{"names": ["M9a", "M18a"], "current_forced": true, "matching_sensitivity": "ratio"}
```
- **`current_forced`**(bool, 축A) — KCL이 실제로 전류를 강제하는가.
- **`matching_sensitivity`**(`"ratio"`|`"offset"`, 축C) — 레이아웃 민감도(offset이면
  common-centroid 필수).
- **축B(`shares_node`)는 필드로 선언하지 않는다** — `stick_diagram.py`에 새로 만든
  `shares_diffusion_node(ra, rb)`(source/drain 어느 조합이든 공유하면 True, gate는
  제외)가 connectivity에서 항상 자동 계산한다.

마이그레이션 매핑(기계적 룩업, 세션8/9가 이미 확정): `diff_pair`→(true,offset),
`current_mirror`→(false,ratio), `branch_symmetric`→(false,ratio), `current_matched`→
(true,ratio).

### 엔진 변경 (하드컷 — 하위호환 shim 없음, 사용자가 명시 승인)
- `sizing_recipe.py`: `_kcl_pairs`(kind 체크 → `p["current_forced"]`), `auto_mirror_ratios`
  (구 `kind=="current_matched"`만 시드하던 걸 `current_forced` 전체로 확장 — 이 확장이
  `current_reuse_telescopic_ota`의 `N_cmfb_bw_mirror` 같은 수동 보정 theta가 메꾸던 gap을
  구조적으로 없앤다. 그 theta는 이제 중복이지만 `ctx.sized`의 `setdefault`라 해가 없어
  그대로 둠).
- `stick_diagram.py`:
  - `shares_diffusion_node(ra, rb)` 신규(축B 공개 함수).
  - `derive_stack_groups()`를 **`kcl_series_union()`**(축A)/**`geometry_colocation_union()`**
    (축B) 두 함수로 분리 — L2 상세는 아래 B절.
  - `select_layout_tool(kind, area_budget)` → `select_layout_tool(matching_sensitivity,
    shares_node, area_budget)`로 시그니처 하드컷.
  - `audit_row_split(rows, matching_pairs, pair_kinds, max_ratio)` → `audit_row_split(rows,
    matching_pairs, pair_sensitivity, max_ratio, area_budget)`로 하드컷 — 내부 `_kind_of()`
    (connectivity에서 kind 즉석 재추론하던 함수)는 완전히 삭제, 이제 `pair_sensitivity`가
    **필수**(없으면 `ValueError`, 예전처럼 gate/source로 자동 분류하지 않음).
  - `repair_matching_safety(rows, matching_pairs, pair_kinds, max_iter)` → `pair_sensitivity`
    로 동일 하드컷.
  - `run_topology_pipeline()`(3730행 부근) — 프로덕션 호출부, `pair_kinds = {pair:
    p["kind"] ...}` → `pair_sensitivity = {pair: p["matching_sensitivity"] ...}`로 교체.

## B. L2 — 그룹핑 규칙 분리 구현 완료

`kcl_series_union()`(축A)과 `geometry_colocation_union()`(축B)은 union-find 골격은
같지만 **자동 발견 규칙(rule1)이 다르다**:
```
kcl_series_union (축A, sizing_recipe.py의 stack_groups_kcl):
  net이 레일(vdd/gnd/vss)이 아니고 정확히 2단자에만 쓰이면 병합(극성 무관, 세션8 설계 그대로)
  + 선언된 current_forced 쌍 강제 병합.
  ⚠️ 세션10 추가: 레일 제외(세션9 "부수 발견"이 여기서 실제로 구현됨) — 4개 회로 전부
  레일 단자 수 실측(3~16개, 위험한 "정확히 2개"는 two_stage_ota의 gnd뿐이었고 그 원인
  (M5/M7 선언)은 세션9에 이미 삭제)으로 회귀 없음 확인 후 반영.

geometry_colocation_union (축B, sizing_recipe.py의 stack_groups_geometry):
  같은 극성 + non-rail net + drain=source(직렬)만 병합(drain=drain 정션은 제외)
  + 선언된 current_forced 쌍만 강제 병합(current_mirror/branch_symmetric은 완전 제외).
```
`sizing_recipe.py`는 이제 **두 함수에 같은 `_forced_pairs`(current_forced=True만)를
넘긴다** — 차이는 순전히 각 함수의 rule1에 있다(이게 L2의 핵심 아이디어: KCL 사실과
geometry 인접 후보를 서로 다른 자동 발견 규칙으로 완전히 분리).

**실측 확인(folded_cascode, self-test Test 29)**: `geometry_colocation_union()`의
rule1이 선언 없이도 `M9`(diode)-`M7`(캐스코드)를 `Vg9`로, `M10`-`M8`을 `Vg10`으로 자동
발견해 다이오드 레퍼런스 체인 전체(`M7,M8,M9,M10`)를 하나의 물리 그룹으로 묶는다 —
당초 손으로 추정했던 것보다 훨씬 강력하게 동작함을 실행 결과로 확인(선언된 쌍만으로
추정했던 게 틀렸었고, 실제로 rule1이 그 이상을 스스로 찾아낸다).

## C. 구현 중 실제로 발견·수정한 버그 3건 (L1/L2 설계가 스스로 검증 도구가 된 사례)

**1. `current_reuse_telescopic_ota`의 `M58/M57`** — `current_mirror`(축A=false)로
선언돼 있었는데, 사용자 지적으로 재확인하니 `M58.drain=M57.source`(직렬)·
`M58.gate=M57.gate=M57.drain`(공통 다이오드)인 **같은 branch의 stacked diode**였다 —
`current_mirror`의 정의(서로 다른 branch, gate만 공유) 자체를 안 만족. 결정적으로,
**쌍둥이 구조인 `M64/M63`은 이미 올바르게 `matching_pairs`에서 빠져있고
`symmetry.dispositions`에 "매칭 배치 불필요"로 기록돼 있었다** — `M58/M57`만 그 정리가
누락된 채 stale하게 남아있던 것. `matching_pairs`에서 삭제(커밋 `8409c0a`).

**2. `two_stage_ota`의 `M5`(1단 tail) 전류 근거 부재** — 축A 규칙1에 레일 제외를
추가하면서, `M5`가 그동안 `gnd`(우연히 정확히 2번 쓰임)를 통해 `M7`의 전류를 몰래
빌려쓰고 있었다는 게 드러났다(레일 제외 전에는 `gnd` 2단자 병합으로 `M5`가 `M7`(→`M6`
경유)의 KCL 스택에 합류했었음). 이건 세션9가 이미 "`M5/M7`은 같은 gate+rail 공유일 뿐
매칭 근거가 아니다"라며 `matching_pairs` 선언을 지운 것과 **정확히 같은 오류가 엔진
레벨에도 숨어있었던 것**이었다 — 선언만 지우고 엔진의 우연한 의존은 못 잡았던 셈. 해법:
`M5`의 진짜 전류 근거는 매칭이 아니라 `CS` 노드(`M1.source`/`M2.source`/`M5.drain`
3단자 합류)의 순수 KCL 항등식 `ID(M5)=ID(M1)+ID(M2)` — `current_reuse`의
`kcl_tail_M5`/`kcl_tail_M38`과 정확히 같은 패턴이라, `two_stage_ota.topology.json`에
`sizing_roles`(theta 1개 + 최소 metrics/objective/constraints, 이 회로는 폐형식이라
이걸 신설해야 했음)를 새로 추가해 해결(사용자 확인 후 진행).
- **부수 발견(미해결, L4)**: `M5` 전류가 정확해지자(173.9µA→30.1µA, W 1.46µm→1.12µm)
  `M6`(2단, W=199.8µm)과의 크기 격차가 커져 box-shape 비율이 1.5 한도를 넘고
  `repair_matching_safety()`로도 못 고친다 — 이건 L1/L2 범위 밖, context.md가 이미
  "L4 미설계"로 표시해둔 정직한 한계라 self-test에서 정보성 출력으로만 처리(다음 L4
  설계 시 재검토 대상으로 남김).

**3. `current_reuse_telescopic_ota`의 `M18_bg/M60/M61`** — 신설한
`audit_current_forced.py`(아래 D절)가 실행 첫 판에 바로 잡아냄: 7-소자 `current_mirror`
문서용 그룹(`current_forced=false`)에 있는데, `r_biasgen` theta(`root=[M18_bg,M60,M61,
M66]`)가 실제로 셋 다(+`M66`) 같은 값으로 강제하고 있었다 — `M12/M21`(`r_diode_M11a`)과
같은 패턴. 별도 `current_forced=true` 그룹 신설로 정정(7-소자 그룹 자체는 구조적 사실
기록용으로 유지, 겹침 — `M8/M17`·`M13/M22`가 이미 이 패턴).

## D. `audit_current_forced.py` 신설

`current_forced` 선언과 `sizing_roles.theta`를 **양방향** 대조하는 스크립트(설계는
세션10 초반 논의, 구현은 L1/L2 다음에 완료). `python audit_current_forced.py`(인자
없으면 `library/*.topology.json` 전부, `_TEMPLATE.*` 제외):
- **과다선언 방향**(⚠️): `current_forced=true`인데 theta 어디에도 직접 근거(같은 theta의
  `root` 리스트에 공존, 또는 type C의 target/reference 일치)가 없으면 사람 확인 요청.
  `sizing_roles` 자체가 없는 회로(`folded_cascode`/`nmcnr_amplifier`/`two_stage_ota`,
  전부 폐형식 사이징)는 대조 대상이 없어 전 항목이 자동으로 이 표시를 받는 게 **정상**
  (그 회로들의 근거는 `topology_to_markdown.py`로 connectivity를 직접 봐야 함).
- **과소선언 방향**(🔴, 진짜 불일치): `current_forced=false`인데 theta가 실제로 그 쌍을
  강제하면 즉시 잡는다 — 위 M58/M57·M18_bg 유형의 버그를 자동 검출. 다른 항목에 이미
  `current_forced=true`로 선언된 쌍은 "겹침 허용" 패턴이라 오탐에서 제외(M8/M17 등으로
  실제로 오탐 나서 dedup 로직 추가함).
- **정직한 한계**: 간접/연쇄 근거(예: `M10/M19`가 각자 다른 `A_signed` 수식으로 독립
  계산되지만 그 구성요소가 이미 강제된 쌍이라 결과적으로 같아지는 경우)는 못 잡고
  보수적으로 ⚠️ 표시한다 — 이런 건 여전히 사람이 수식을 직접 추적해 판단해야 함
  (`current_reuse_telescopic_ota` 실행 결과 12건이 이 유형으로 ⚠️ 남아있음, M14a/M23a·
  M14b/M24b·M10/M19·M15/M25·M16/M26·M9b/M18b·M1a/M1b·M4a/M4b·M2a/M2b·M3a/M3b·
  M37a/M37b·M36a/M36b — 전부 `sizing_recipe.py`의 기존 `_comment`에 근거가 산문으로
  이미 적혀있는 것들이라 급하지 않음).
- exit code: 🔴 있으면 1, 없으면 0(⚠️는 실패로 안 침).

## E. self-test 회귀 확인 결과

`stick_diagram.py`/`sizing_recipe.py` 둘 다 **exit 0**(예외 없음) — 여러 차례 재실행해
최종 확인. 주요 수정 지점:
- `stick_diagram.py`의 Test 22/23(kind→`pair_sensitivity` 명시 필요, 예전엔 connectivity
  자동추론에 의존했음)/28(`select_layout_tool()` 새 시그니처, `_first_pair_of_kind()`→
  `_first_pair_matching()`)/29(`derive_stack_groups()`→`geometry_colocation_union()`,
  folded_cascode 세션9 재구성 반영해 기대 그룹 재작성)/26(folded_cascode connectivity
  diff=0 비교가 세션9 재구성으로 더 이상 유효한 기준이 아니라 참고 정보로 격하).
- `sizing_recipe.py`의 L-reconcile 합성 픽스처(`"kind": "current_mirror"` → 새 필드),
  `two_stage_ota` 실전 테스트(위 C-2 버그 수정 반영).

## 세션10 — run_harness류 백그라운드 실행 모니터링 교훈

`sizing_recipe.py` self-test가 한 번 180초를 넘겨 백그라운드로 넘어갔을 때, 사용자가
"지난번(`run_harness.py` 3연속 실패)처럼 안 끝날 수 있으니 버퍼링 문제를 추적하며
모니터링하라"고 지시해 실제로 확인한 방법 — **다음에 비슷한 상황에서 재사용할 것**:
1. 로그 파일이 0바이트라고 바로 "죽었다"고 판단하지 말 것 — `tasklist`/`Get-Process`로
   PID가 살아있는지 먼저 확인.
2. PID가 살아있으면 `Get-Process -Id <pid> | Select CPU`를 **두 번, 간격을 두고**
   비교해 CPU 시간이 실제로 늘어나는지 본다(delta≈경과시간이면 거의 풀가동 중 = 진짜
   계산 중, delta≈0이면 진짜로 멈춘 것에 가까움). 이번 사례는 15초 사이 CPU 14.8초
   증가로 "죽지 않고 계산 중"임을 확정했다.
3. 로그가 비어도 프로세스가 살아있다면, 어느 self-test 구간이 원래도 느린지 소스에서
   먼저 찾아본다(이번엔 `current_reuse_telescopic_topology()`의 3단 고정점 반복이
   toy LUT에서 limit cycle에 빠져 `max_iter`까지 도는, **이미 소스 주석에 문서화된
   기존 성능 특성**이었다 — 내가 이번 세션에 만든 버그가 아니었음). 결론이 나면 그냥
   완료를 기다리면 된다 — 죽이고 재시작할 필요 없음.
4. `run_harness.py`가 다음 세션에 또 조용히 안 끝나면, 위 1~3번을 그대로 적용해서
   "죽었다" vs "느리다"부터 구분할 것 — 이게 3세션 연속 미확인이었던 근본 질문이다.

---

## L3. walk 선택 문제 (미설계, 세션8부터 그대로) — `hierholzer()`가 matching_pairs를 모른다

`build_graph()`(edge 삽입 순서)나 `hierholzer()`(trail 구성 시 tie-breaking)가
`matching_pairs`를 인자로 받아 여러 유효 오일러 회로 중 대칭 배치를 만드는 쪽으로
편향된 선택을 하도록 만들어야 한다 — **아직 코드 스케치조차 없음**. 세션8이 확인한 것:
- `interdigitation(3b)`이 원리적으로 불가능한 구조(두 loop가 단일 브리지로만 연결)는
  walk 선택과 무관하게 항상 불가능(참).
- "짝수 finger면 3c(common-centroid)가 항상 완벽히 달성된다"는 이전 결론은 틀렸다 —
  정확히는 "존재는 한다"까지만 참이고, 현재 구현이 그 회로를 실제로 찾아준다는 보장이
  없다(입력 순서 같은 우연에 좌우됨).
- 후보 방향(전부 미검토): edge 삽입 순서를 matching_pairs 인식형으로 바꾸기 / 여러
  유효 trail을 실제로 생성해 dx 최소인 것 선택 / 그래프 자기동형사상으로 팰린드롬
  walk를 구성적으로 만들기.
- 다음 세션 시작점: **논의부터 새로 시작**(그래프 이론적 접근법 후보 검토 → 방향 합의
  → 그 다음에야 구현 논의).

## L4. 사이징→레이아웃 연결 문제 (미설계, 세션8부터 그대로 + 세션10이 실측 사례 추가)

`assign_finger_geometry()`가 축B(`shares_node`) 값을 몰라서, 짝수 finger가 필요한
매칭 쌍(축B=false인 `current_forced` 쌍)에 그 제약을 전달하는 로직이 없다 —
**완전히 새로 설계해야 하는 부분, 코드 스케치 전혀 없음**.
- **세션10 실측 사례 추가**: `two_stage_ota`(위 C-2)에서 `M6`(2단, gm/ID 낮음 → W
  커야 함)과 `M3/M5`(cascode/tail, gm/ID 높음 → W 작아도 됨)의 크기 격차가 box-shape
  비율(≤1.5)을 넘고 `repair_matching_safety()`로도 못 고치는 게 실제로 재현됨 — 스테이지
  간 W 격차가 큰 회로(2단 OTA류 전형적 패턴)에서 이 gap이 실전에 어떻게 나타나는지 보여주는
  구체적 사례로 L4 논의 시작할 때 참고할 것.

---

## 다음 세션 작업 순서 (권장, 각 단계 사용자 승인 필수)

1. `run_harness.py` 재실행, **이번엔 세션 안에서 끝까지 지켜볼 것**(위 "세션10 —
   run_harness류 백그라운드 실행 모니터링 교훈" 방법 그대로 적용 — 죽었는지 느린 건지
   먼저 구분).
2. L3(walk 선택) — 그래프 이론적 접근법 후보들 검토 → 사용자와 방향 합의 → 그 다음에야
   구현 논의.
3. L4(사이징→레이아웃 연결) — L3 방향이 정해진 뒤 설계 착수(축B 값을
   `assign_finger_geometry()`가 소비하는 인터페이스 설계). `two_stage_ota`의 box-shape
   실측 사례(위 C-2)를 구체적 테스트케이스로 활용.
4. L1/L2 잔여 항목(급하지 않음): `audit_current_forced.py`의 ⚠️ 12건(간접 근거,
   `current_reuse_telescopic_ota`) — 필요해지면 사람이 직접 사슬 추적해 확인, 지금은
   방치해도 무방(전부 `sizing_recipe.py` `_comment`에 근거 있음).
5. 전부 반영 후 self-test 전체 재실행(`stick_diagram.py`/`sizing_recipe.py`) +
   `run_harness.py` 재실행으로 최종 회귀 확인.
6. 완주하면 세션4 핸드오프 원래 "다음 단계"(Cc/Rz/Iref 값 채우기, PSRR 폐형식 재유도)로
   이어가기.
7. (미정, 낮은 우선순위, 세션6부터 이월) `find_structural_symmetry_candidates()`의
   `"dual"` transform 오탐 개선 — 손 안 댐.

---

## 작업 파일 위치

- `skills/analog-gmid-design/assets/stick_diagram.py`
  - `shares_diffusion_node(ra, rb)`(1428행 부근) — **세션10 신설**, 축B 공개 함수.
  - `kcl_series_union(netlist, matching_pairs)`(1446행 부근)/
    `geometry_colocation_union(netlist, matching_pairs)`(1505행 부근) — **세션10 신설**,
    구 `derive_stack_groups()`를 대체(그 이름은 더 이상 없음).
  - `select_layout_tool(matching_sensitivity, shares_node, area_budget=None)`(2630행
    부근) — **세션10 시그니처 하드컷**(구 `kind: str` 파라미터 폐지).
  - `audit_row_split(rows, matching_pairs, pair_sensitivity, max_ratio, area_budget=None)`
    (2661행 부근) — **세션10 시그니처 하드컷**(구 `pair_kinds`/내부 `_kind_of()` 폐지).
  - `repair_matching_safety(rows, matching_pairs, pair_sensitivity, max_iter=3)`(2904행
    부근) — **세션10 시그니처 하드컷**.
  - `run_topology_pipeline()`(3690행 부근) — 프로덕션 호출부, `pair_sensitivity` 조립
    하도록 이미 갱신됨.
  - `build_graph()`(1546행 부근 근처, 라인 시프트됨)/`hierholzer()` — **L3 설계·구현
    대상**, 현재 완전히 matching-blind(세션10 미변경).
  - `assign_finger_geometry()`(1932행 부근 근처, 라인 시프트됨) — **L4 설계·구현 대상**
    (세션10 미변경).
- `skills/analog-gmid-design/assets/sizing_recipe.py`
  - `_forced_pairs`/`auto_mirror_ratios`/`stack_groups_kcl`/`stack_groups_geometry`
    (1894~1953행 부근) — **세션10에 `current_forced` 기반으로 전면 교체 완료**.
  - `import` 문(1611행 부근) — `kcl_series_union, geometry_colocation_union`으로 갱신됨.
- `skills/analog-gmid-design/assets/audit_current_forced.py` — **세션10 신규 파일**,
  양방향 근거 대조 스크립트(위 D절).
- `skills/analog-gmid-design/assets/library/*.topology.json` — **4개 전부 세션10에
  마이그레이션 완료**(`kind` 필드 완전 폐지, `current_forced`/`matching_sensitivity`로
  교체). `current_reuse_telescopic_ota.topology.json`은 추가로 M58/M57 삭제(세션10 발견1)
  + M18_bg/M60/M61 재분류(세션10 발견3)까지 반영됨. `two_stage_ota.topology.json`은
  `sizing_roles`(theta 1개 `kcl_tail_M5` + 최소 metrics/objective/constraints) 신규
  섹션이 추가됨(세션10 발견2).
- `skills/analog-gmid-design/references/stick-diagram-euler-layout.md` — L1~L3 재설계
  반영 필요(§2.6/§2.7이 여전히 구 `kind` 문자열 기준으로 서술돼 있을 가능성 — 세션10은
  이 문서를 갱신하지 않음, 코드 docstring에는 새 축 반영 완료). 다음 세션에서 L3/L4
  설계와 함께 갱신할지 판단할 것.
- `workspaces/current-reuse-telescopic-ota-report/run_harness.py` — 다음 세션 최우선
  확인 대상(위 "지금 상태" 2번 참고), 로그 파일명은 세션마다 새로 정할 것(예:
  `run_harness_session11.log`).

## 참고 — 사용자 협업 메모리 (자동 메모리 시스템에 저장됨, 요약만)

- 최종 보고는 항상 한글로.
- 상상으로 채우지 말고 근거·실제 확인 후 진행 — "확정"처럼 보이는 결과도 전제를 다시
  확인하기 전엔 맹신 금지.
- topology.json이 유일한 토폴로지 소스 — connectivity는 사용자 전용, role/matching/theta
  같은 메타데이터는 Claude가 분석해서 업데이트 가능.
- 장시간 실행은 `run_in_background: true` — **세션10 추가**: 백그라운드 실행이 로그
  없이 오래 걸리면 "죽었다"고 바로 판단하지 말고 PID 생존+CPU 사용량 변화로 먼저
  hang 여부를 구분할 것(위 "세션10 — run_harness류 백그라운드 실행 모니터링 교훈" 참고).
- 회로도 이미지/PDF 판독은 신뢰 못 함 — connectivity는 `topology_to_markdown.py`로
  net 기준 표를 뽑아 확인. 논문 본문 텍스트 추출은 신뢰 가능.
- topology 정정은 대기열에 쌓았다가 "한꺼번에 반영해" 지시가 와야 일괄 반영(connectivity
  한정) — **단, role/matching 메타데이터 재분류(kind 재분류, current_forced 정정 등)는
  이 규칙 대상이 아니라 즉시 반영 가능**(세션10에 M58/M57·M18_bg 등 여러 건을 발견 즉시
  개별 반영함, 문제없었음).
- 논문에 없는 컴포넌트 값은 "논문 인용"만으로 확정 짓지 말 것.
- 복잡한 analog 회로 폐형식 재유도는 opus 에이전트(가능하면 git worktree 격리) 위임이
  효과적.
- git commit 시 heredoc-in-`$()`이 bkit 훅에 막힘 — 파일로 메시지 작성 후 `git commit -F`.
- 엔진/스키마 변경은 국소적 메타데이터 정정(파일 하나의 kind 재분류 등)은 바로 실행
  가능하지만, **여러 파일/여러 회로에 영향을 주는 엔진 로직 변경은 반드시 사전 논의·승인
  필요**(세션7에서 이 규칙을 어겨 즉시 원복 지시받은 사고 있었음). 세션10은 이 규칙을
  끝까지 지켜, L1/L2 엔진 변경 전 설계 요약을 두 번(L1/L2 각각) 사용자에게 보고하고
  "미결사항 확정 후 하드컷으로 진행해" 같은 명시 승인을 받은 뒤에만 코드를 고쳤다.
- **세션10 추가**: 엔진 로직을 실제로 구현하다 보면 설계 단계에서 손으로 추정했던
  동작이 실행 결과와 다를 수 있다(예: `geometry_colocation_union()`의 rule1이 예상보다
  훨씬 넓게 병합함, `M18_bg/M60/M61`처럼 감사 스크립트가 예상 못 한 실제 불일치를 찾아냄)
  — 이럴 땐 손으로 정답을 다시 추정하지 말고 격리 스크립트로 직접 실행해 확인할 것
  (`diag_m5.py` 패턴 — 변형 두 개를 나란히 실행해 비교).
