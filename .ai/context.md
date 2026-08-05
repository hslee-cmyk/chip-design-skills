# 세션 컨텍스트 (최종 갱신: 2026-08-05, 세션 9 끝 — 다음은 세션 10)

## 작업 디렉토리
`C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills`

## 지금 상태 (다음 세션이 가장 먼저 할 일)

1. **`run_harness.py`는 세션9도 실패했다 — 재실행부터.** `run_in_background: true`로
   실행했으나 세션 종료 시점 확인 결과 `run_harness_session9.log`가 **세션7·8과 똑같이
   0바이트**(2026-08-05 13:35 생성, 내용 없음) — 프로세스가 완료를 못 보고 죽은 것으로
   보인다(3개 세션 연속 같은 증상, Python 버퍼링 의심). 세션10은 처음부터 다시 실행하고
   **이번엔 끝까지 지켜볼 것** — 필요하면 `python -u`(unbuffered) 옵션이나
   `PYTHONUNBUFFERED=1` 환경변수로 버퍼링 자체를 의심해볼 것(3연속 실패라 근본 원인 조사
   가치 있음).
2. **git 상태 확인 필요.** 세션9는 세션8과 달리 **`.ai/context.md` 외에 실제 코드/JSON도
   수정했다** — `skills/analog-gmid-design/assets/library/two_stage_ota.topology.json`
   (`M5/M7` 삭제)과 `folded_cascode.topology.json`(netlist 전면 재구성 + `ideal_sources`
   신규 + `matching_pairs` 재분류) 둘 다 **사용자 명시 승인/정정지시로 반영 완료됐다**
   (엔진 파일 `stick_diagram.py`/`sizing_recipe.py`는 여전히 미변경 — L1/L2 설계는 전부
   미구현 상태 그대로). `git status`/`git diff`로 이 두 파일이 실제로 반영됐는지, 커밋이
   필요한지부터 확인할 것(세션9는 커밋 여부를 사용자에게 묻지 않았다).
3. 아래 "세션9 총정리"(새 스키마/원칙)와 "세션9 — folded_cascode netlist 전면 정정"을
   사용자에게 다시 요약 보고하고, "다음 세션 작업 순서"에 따라 **L1(스키마)부터 승인받아**
   순서대로 진행할지 확인받을 것. L1 마이그레이션 시 `folded_cascode`의 `M7/M8`이
   `branch_symmetric`→`current_matched`로 이미 바뀐 것도 34건 기계적 룩업 표에 반영해야
   함(세션8 시점 표는 이 재분류 이전 상태 — 아래 L1 절 참고, 최신 kind는 JSON이 정본).

## 배경 — 이 기능이 뭐고 왜 하는가 (세션5~8 공통, 참고용)

- **WHY**: topology netlist가 Python 코드 하드코딩이면 재현 불가능, agent마다 해석이
  달라짐 — 그래서 `topology.json`(`skills/analog-gmid-design/assets/library/*.topology.json`)
  하나를 유일한 소스로 둔다.
- **권한 경계(중요, 항상 지킬 것)**: `netlist`/`passive_elements`/`ideal_sources`의
  connectivity는 **사용자만 고친다**. `device_roles`/`symmetry.matching_pairs`/
  `symmetry.dispositions`/`sizing_roles`(theta 포함) 같은 **역할·메타데이터는 Claude가
  분석해서 업데이트해도 된다** — 단, **여러 파일/여러 회로에 영향을 주는 엔진 로직 변경**
  (`stick_diagram.py`/`sizing_recipe.py`의 함수 로직)은 이 경계와 별개로 반드시 사전
  논의·승인이 필요하다(세션7에서 이 규칙을 어겨 즉시 원복 지시받은 사고가 있었음).
- 논문에 없는 값은 "논문 인용"만으로 확정 짓지 말 것.
- **핵심 파일**: `skills/analog-gmid-design/assets/sizing_recipe.py`(gm/ID 사이징, KCL
  엔진) / `skills/analog-gmid-design/assets/stick_diagram.py`(오일러 trail 기반 레이아웃
  엔진) / `skills/analog-gmid-design/assets/library/*.topology.json`(4개 회로: 
  `current_reuse_telescopic_ota`, `folded_cascode`, `nmcnr_amplifier`, `two_stage_ota`).

---

# 세션8 결론 — "사이징(KCL) harness"와 "레이아웃(오일러) harness"가 모순 없이 최적 결과를
# 내려면 4개 층이 전부 맞아야 한다

## 질문의 출발점
세션7 끝에 사용자가 던진 질문("KCL 축과 레이아웃 축을 완전히 분리해야 한다"는 "정정3" 원칙을
실제로 어떻게 구현하나)을 세션8 내내 실제 코드 실행으로 검증했다. 결론적으로, **스키마 하나만
고쳐서는 안 되고, 서로 독립적인 4개 층이 전부 맞아야 두 harness가 모순 없이 동작한다**는
게 밝혀졌다:

| 층 | 질문 | 담당 코드 | 설계 상태 |
|---|---|---|---|
| **L1. 스키마** | `matching_pairs` 하나가 KCL 의도·레이아웃 위상·전기적 민감도 세 질문에 동시에 답하려 한 게 문제의 뿌리 | `topology.json`의 `symmetry.matching_pairs` | **거의 완료**(마이그레이션표까지 있음) |
| **L2. 그룹핑 규칙** | 어떤 소자들을 같은 물리 행 후보로 묶을지 | `stick_diagram.py`의 `derive_stack_groups()` | **상당히 진행**(기능블럭 자동분리까지 확인) |
| **L3. walk 선택** | 그 행 안에서 오일러 trail을 어떤 순서로 고를지 | `stick_diagram.py`의 `build_graph()`/`hierholzer()` | **미설계**(문제만 발견) |
| **L4. 사이징→레이아웃 연결** | 사이징 단계가 L2/L3이 필요로 하는 조건(예: 짝수 finger)을 미리 배정해주는가 | `sizing_recipe.py`/`stick_diagram.py`의 `assign_finger_geometry()` | **미설계**(문제만 발견) |

L1/L2가 옳아도 L3/L4가 없으면 harness는 "우연히 맞으면 통과, 아니면 실패"하는 신뢰 불가능한
상태로 남는다(L3에서 실측으로 확인됨, 아래 참고).

---

## L1. 스키마 재설계 — `kind`를 축A/B/C로 분해

### 세 개의 독립 축
- **축A(`current_forced: bool`)**: KCL이 실제로 전류를 강제하는가. `sizing_recipe.py`의
  `_kcl_pairs` 병합 여부를 결정. 선언 필수.
- **축B(`shares_node`, **선언 불필요** — 항상 자동 계산)**: source/drain을 직접 공유해
  물리적으로 같은 diffusion을 연장할 수 있는가(interdigitation=3b의 위상적 가능 여부).
  ```python
  def shares_diffusion_node(ra, rb):
      # gate는 포함하지 않는다 -- gate 공유는 "같은 바이어스"일 뿐 diffusion 연장과 무관
      # (M106/M107이 gate=VB3를 공유해서 이걸 착각한 적이 한 번 있었음, 실측 중 발견해 고침)
      na = {ra.source, ra.drain} - {None}
      nb = {rb.source, rb.drain} - {None}
      return bool(na & nb)
  ```
- **축C(`matching_sensitivity: "ratio"|"offset"`)**: 오차가 offset/CMRR급(centroid 강제)
  인지 미러비 오차급(interdig로 충분)인지. 기본값 `"ratio"`, `diff_pair`류만 `"offset"`.
  선언 필요(회로 역할 판단이라 connectivity로 자동 도출 불가).

### 기존 4개 kind가 실제로 이 축들의 어떤 고정 조합이었는지 (전 라이브러리 34건 전수조사:
diff_pair 6 + current_mirror 4그룹 + branch_symmetric 3 + current_matched 21)

| 구 kind | 축A | 축C | 축B(실측) |
|---|---|---|---|
| `diff_pair` | true | offset | 항상 공유(source가 diff_pair 정의 자체) |
| `current_mirror` | false | ratio | 항상 공유(정의 자체가 "같은 gate+source") |
| `branch_symmetric` | false | ratio | **항상 비공유**(정의 자체가 "공유 노드 없음") |
| `current_matched` | true | ratio | **혼재** — 21건 중 6건이 비공유 ← **유일한 문제** |

`diff_pair`/`current_mirror`/`branch_symmetric`은 축B가 정의에 내장돼 있어 지금까지 문제가
없었다. **`current_matched`만 축A(KCL)만 의미하고 축B가 검증된 적 없어서** 세션8의 모든
역설이 여기서만 나왔다.

### 축B 역설 6건 (current_matched인데 실제로 공유 노드 없음, 전부
`current_reuse_telescopic_ota`)

| 쌍 | 비고 |
|---|---|
| `M2a/M2b` | 세션7 "정정1"이 이미 diff_pair로 되돌리자고 회로 역할 논증으로 지적한 바로 그 쌍 — 순수 connectivity 계산이 독립적으로 같은 결론에 도달, 교차검증됨 |
| `M3a/M3b` | 위와 동일(정정1 대상) |
| `M9a/M18a` | 세션8 핵심 반복 사례(아래 L2/L3에서 계속 등장) |
| `M9b/M18b` | 위와 동일 계열 |
| `M11b/M20b` | 세션8 전수조사에서 새로 발견 |
| `M14a/M23a` | 세션8 전수조사에서 새로 발견 |

(참고: 7-member `current_mirror` 문서용 그룹 `{M18_bg,M8,M13,M17,M22,M60,M61}`도 확인함 —
C(7,2)=21개 조합 전부 `shares_node=True`(전부 `vdd` 공유 1단 PMOS라 정상). **레일(vdd/gnd)
공유가 축B에서 유효한 근거로 인정된 사례** — 단 이건 `derive_stack_groups()` 규칙1이 레일을
의도적으로 제외하는 것(L2, 아래)과는 **다른 목적의 다른 판단**이니 헷갈리지 말 것.)

### 제안 스키마
```json
{"names": ["M9a", "M18a"], "current_forced": true, "matching_sensitivity": "ratio"}
```
`kind` 필드 폐지, 옛 `kind` 문자열은 리포트/`_comment`용 파생 표시값으로만 남김(엔진 판단에
안 씀). 마이그레이션은 34건 전부 **기계적 룩업**(위 표 그대로, 개별 판단 불필요).

### 엔진 변경 지점 (설계 완료, 코드만 안 넣음)
- `sizing_recipe.py`의 `_kcl_pairs`(1947행 부근): `kind not in (...)` → `p["current_forced"]`
  로 교체(4개 kind 전부 회귀 없음, 표로 확인됨).
- `stick_diagram.py`의 `_kind_of()`/`audit_row_split()`(2669행, 2779-2780행 부근): kind
  기반 정책 분기를 폐지하고
  ```python
  if matching_sensitivity == "offset":
      interdig_required, centroid_required = False, True
  elif shares_diffusion_node(ra, rb):
      interdig_required, centroid_required = True, (area_budget == "generous")
  else:
      interdig_required, centroid_required = False, True
  ```
  로 교체. 4개 대표 케이스(M9a/M18a류, M106/M107류, M12/M21류, M1a/M1b)로 정책 로직 자체는
  회귀 없이 검증됨(단, "M9a/M18a가 실제로 ok=True를 낸다"는 구체적 통과 여부는 L3가 없으면
  재현 안 됨 — 아래 참고, 정책 판단과 실제 통과 여부를 혼동하지 말 것).

---

## L2. 그룹핑 규칙 재설계 — `derive_stack_groups()`를 축A용/축B용 두 함수로 분리

### 배경 — 왜 하나의 함수로는 안 되는가
`derive_stack_groups()`는 지금 `sizing_recipe.py`에서 **두 용도**로 쓰인다:
`stack_groups_kcl`(축A, `_kcl_pairs`로 호출)과 `stack_groups_geometry`(축B, 전체
`matching_pairs`로 호출). 둘 다 **같은 규칙1**("정확히 2단자에만 쓰이는 net → 병합")을
쓰는데, 이 규칙이 두 용도에 다른 의미를 가진다는 게 세션8에서 드러났다.

### 규칙1 — 축A(KCL)용은 "정확히 2단자"가 물리 법칙, 극성과 무관해야 옳다
2단자 net은 전하보존으로 두 소자 전류가 반드시 같다 — **극성 무관, 이건 물리 법칙이지 임의
기준이 아니다.** 실측 근거: `M106`(nmos)과 `M108`(pmos)이 `NodeM1`(정확히 2단자, 폴디드
캐스코드 폴딩 노드)을 공유하면 KCL로 두 전류가 반드시 같다 — 극성이 달라도. **그래서
`stack_groups_kcl` 호출의 규칙1은 극성 체크를 추가하면 안 된다(그대로 유지).**

⚠️ **세션8 중반의 실수(정정됨)**: 처음엔 "규칙1에 극성 체크를 추가"하는 걸
`derive_stack_groups()` 전체(즉 `stack_groups_kcl` 포함)에 일괄 적용하려 했다. 이러면
`stack_groups_kcl`이 M106=M108 같은 진짜 KCL 등식을 놓치게 된다 — **극성 체크는 반드시
`stack_groups_geometry` 호출에만 적용해야 한다.**

### 규칙1 — 축B(geometry)용은 "정확히 2단자"가 아니라 "명시적 rail 제외" + "같은 극성" +
"drain=source(직렬)만"
사용자 제안("규칙1의 2단자 노드를 좀더 합리적으로")을 계기로 재설계:

1. **"정확히 2단자"가 아니라 "명시적 rail(vdd/gnd)이 아닌가"가 기준**이어야 한다. 실측
   근거: `current_reuse_telescopic_ota`에서 source/drain 사용 횟수가 `vdd`(16회)/
   `gnd`(13회)만 압도적으로 높고 나머지 net은 전부 5회 이하로 뚝 떨어진다(자연스러운
   컷오프, 임의 아님). 또한 vdd/gnd는 거의 항상 `source`로만 쓰이고 `drain`으로는 거의
   안 쓰인다(28건 vs 1건).
2. **같은 극성끼리만 병합**(발견1 원래 취지, PMOS/NMOS는 다른 well이라 같은 diffusion
   행에 못 들어감).
3. **`drain=source`(진짜 직렬/캐스코드)만 병합, `drain=drain`(합류/정션)은 제외.** 실측
   근거: `M8.drain=Vg15=M9a.source`(진짜 stacked series, 병합 타당) vs
   `M2a.drain=Vom1=M18a.drain`(diff-pair core 캐스코드 출력과 class-AB 출력이 우연히
   합류하는 정션 노드일 뿐 — 이 회로의 "current-reuse" 메커니즘 자체이긴 하지만 레이아웃
   인접의 근거는 아님).

### 규칙2(선언된 matching_pairs 강제 병합)도 축A를 반영해야 함
`current_mirror`(비강제, 순수 문서용) 선언을 geometry 병합에서 **완전히 제외**해야 한다 —
안 그러면 Vbias1의 7-소자 문서용 그룹이 class-AB 출력단(`M8,M9a,M17,M18a`)을 다시 끌고 들어와
매칭 품질을 악화시킨다(실측: 섞인 9-member 그룹 dx=6.00 vs 제외한 4-member 그룹 dx=3~4).

### 최종 규칙 (L2, 설계 완료 — 코드만 안 넣음)
```
축A(_kcl_series_union, 기존 그대로 유지, 극성체크 절대 추가 금지):
  net이 정확히 2개 소자 단자(source/drain)에만 쓰이면 병합(극성 무관)

축B(_geometry_colocation_union, 신규):
  규칙1: 같은 극성 + rail(vdd/gnd)이 아닌 net + 한쪽 drain=다른쪽 source(직렬)면 병합
  규칙2: current_forced=True(구 diff_pair/current_matched)로 선언된 pair만 강제 병합
         (current_mirror/branch_symmetric은 geometry 병합에서 완전히 제외)
```

### 검증된 효과 — 기능블럭 자동 분리 (사용자 가설 확인됨)
위 규칙으로 `current_reuse_telescopic_ota`를 재그룹핑하니 **사람이 수동으로 curated
override를 고를 필요 없이 diff-pair core와 class-AB 출력단이 자동으로 분리됐다**:
- diff-pair core: `{M6,M7,M1a,M1b,M2a,M2b,M58,M57}` (8개)
- class-AB 출력단(PMOS만): `{M8,M9a,M18a,M17}` (4개)

**이전 계획(세션8 초반의 "vdd/gnd 매개 curated override를 수동 선언"하는 발견4 방향)은
이 규칙으로 대체된다 — 더 이상 필요 없음.**

⚠️ **아직 검증 안 됨**: 이 규칙을 `folded_cascode`/`nmcnr_amplifier`/`two_stage_ota`
전체에 적용했을 때도 정상적인 그룹 수·구조가 나오는지는 `current_reuse_telescopic_ota`
한 회로에서만 확인했다 — 다음 세션에서 4개 회로 전부 재검증 필요.

---

## L3. walk 선택 문제 — `hierholzer()`가 matching_pairs를 모른다 (새로 발견, 미설계)

### 발단 — 자기 수정 경위 (다음 세션이 반드시 알아야 할 실수)
L2 검증 중 "M9a/M18a가 class-AB 그룹에서 dx=3~4로 안 좋다"는 결과가 나와서, 한때 "이 정도가
한계"라고 결론지었다. 사용자가 "아까 말한 finger 늘린 solution이 안 먹힌다고?"라고 반문해서
재검증했고, **두 가지가 밝혀졌다**:

1. **세션8 초반(L2 이전)의 "완벽한 dx=0.00" 성공 사례 중 2건이 실은 극성이 섞인 무효 행
   이었다.** 즉 실제로 만들 수 없는 행에 대한 결과였다:

   | curated 그룹 | 실제 극성 구성 | 유효한가 |
   |---|---|---|
   | `{M8,M9a,M9b,M17,M18a,M18b}`(vdd 매개) | pmos 4개 + nmos 2개 | ❌ 무효 |
   | `{M106,M107,M108,M109}`(nmcnr) | nmos 2개 + pmos 2개 | ❌ 무효 |
   | `{M9b,M10,M19,M18b}`(gnd 매개) | nmos 4개 | ✅ 유효 |

2. **극성을 올바르게 지킨 재검증**(`{M8,M9a,M17,M18a}` pmos만, `{M104,M106,M105,M107}`
   nmos만 — 후자는 무효했던 M108/M109 pmos 다리 대신 `vss`를 매개로 한 nmos 다리)에서
   `build_stick_diagram()`이 실제로 반환한 시퀀스는 **비대칭**이었다:
   ```
   M9a 케이스(nf=2): M9a,M9a,M8,M17,M18a,M18a,M17,M8   -> dx=4.00
   M106 케이스(nf=2): M106,M106,M104,M105,M107,M107,M105,M104 -> dx=4.00
   ```
   그런데 **같은 그래프에 대해 손으로 구성한 아래 시퀀스는 유효한 오일러 회로이면서
   완벽히 대칭이다**(직접 검증함, dx=0.00):
   ```
   M9a,M8,M17,M18a,M18a,M17,M8,M9a   <- 팰린드롬, dx=0.00, 유효한 오일러 회로
   M106,M104,M105,M107,M107,M105,M104,M106 <- 팰린드롬, dx=0.00, 유효한 오일러 회로
   ```
   반면 유일하게 유효했던 gnd 케이스의 실제 반환 시퀀스
   (`M9b,M10,M19,M18b,M18b,M19,M10,M9b`)는 **우연히 팰린드롬**이었다 — 그래서 그때만
   3c가 진짜로 완벽했다(운이 좋았을 뿐).

### 정정된 결론 (다음 세션이 이 버전을 신뢰할 것)
- **3b(interdigitation)가 이런 "두 loop가 단일 브리지로만 연결된" 구조에서 원리적으로
  불가능하다는 결론은 그대로 유지된다.** M9a는 그래프상 M18a와 절대 직접 이웃할 수 없다
  (위상 자체의 성질 — 최적 팰린드롬 시퀀스에서도 M9a/M18a는 서로 안 붙어있다, 확인함).
  walk 선택과 무관하게 항상 참.
- **"짝수 finger면 3c가 항상 완벽히 달성된다"는 이전 결론은 틀렸다.** 정확히는: "짝수
  finger면 3c를 완벽히 달성하는 오일러 회로가 **존재는 한다**"까지만 참이고,
  `build_stick_diagram()`/`hierholzer()`가 **그 회로를 실제로 찾아준다는 보장이 없다.**
  지금 구현은 `matching_pairs`를 전혀 모른 채 그래프 구조·입력 순서만으로 결정론적으로
  하나의 유효한 trail을 고르는데, 그게 우연히 대칭이면 3c가 통과하고 우연히 비대칭이면
  실패한다 — **입력 리스트 순서 같은 우연에 좌우되는, 신뢰할 수 없는 동작이다.**

### 필요한 것 (미설계, 코드 스케치 전혀 없음 — 다음 세션 새 논의 시작점)
`build_graph()`(edge 삽입 순서)나 `hierholzer()`(trail 구성 시 tie-breaking)가
`matching_pairs`를 인자로 받아, **여러 유효 오일러 회로 중 선언된 쌍들의 무게중심 거리를
최소화하는 쪽으로 편향된 선택**을 하도록 만들어야 한다. 후보 방향(전부 미검토):
- edge 삽입 순서를 matching_pairs 인식형으로 바꿔서 애초에 대칭 walk가 나오게 유도.
- 여러 유효 trail을 실제로 몇 개 생성해보고(같은 그래프, 다른 시작점/tie-break) 그중
  dx가 최소인 것을 선택(작은 그룹이면 계산량 감당 가능할 것).
- 그래프의 대칭성(예: 자기동형사상)을 미리 찾아서 팰린드롬 walk를 구성적으로 만드는 방법.

---

## L4. 사이징→레이아웃 연결 — `assign_finger_geometry()`가 축B를 모른다 (미설계)

L3가 해결돼도, 애초에 축B=false인 `current_forced` 쌍(`M9a/M18a` 등)이 3c를 통과하려면
**짝수 개의 finger**가 필요하다(L3 실측: nf=1은 항상 실패, nf=2 이상부터 가능성이 열림).
그런데 `assign_finger_geometry()`(`stick_diagram.py`, 사이징 결과 W와 stack 후보를 이어
`n_fingers`를 정하는 함수)는 지금 이 사실을 전혀 모르고 W와 target_row_fingers만 보고
finger 수를 정한다. **L1(축B 계산)의 결과를 L4가 소비해서 "이 쌍은 짝수 finger가 필요하다"는
제약을 사이징 단계에 전달하는 로직이 없다** — 완전히 새로 설계해야 하는 부분, 코드 스케치
전혀 없음.

---

## 세션9 — 재검증 2건 완료 결과 (격리 스크립트로 확인, repo 파일 미변경)

- **`folded_cascode`의 `M5/M6`, `M7/M8` 극성 확인 — 문제 없음.** `M5/M6`는 둘 다 pmos,
  `M7/M8`은 둘 다 nmos, 각 선언 쌍 내부 극성 혼재 없음. L3에서 발견됐던 "curated 그룹이
  실제로 무효한 극성 조합"인 문제 패턴은 여기 해당 안 됨.
  - 부수 확인: **현행(미변경) `derive_stack_groups()`는 4개 회로 전부에서 이미 극성 혼재
    그룹을 만들고 있었다** — `folded_cascode`:`{M5,M6,M7,M8}`, `nmcnr_amplifier`:
    `{M106,M107,M108,M109}`/`{M201..M204}`/`{M301,M302}`, `two_stage_ota`:
    `{M3,M4,M1,M2}`/`{M6,M5,M7}`. `current_reuse_telescopic_ota`만의 특이 사례가 아니라
    L1/L2가 고치려는 문제가 라이브러리 전체에 일반적으로 존재함이 확인됨 (L1/L2 필요성
    뒷받침).
- **L2 새 규칙(rail 제외 + drain=source + 축A 제한 규칙2)을 나머지 3개 회로에 적용 —
  `folded_cascode`/`nmcnr_amplifier`는 깨끗함(전 그룹 단일 극성, `current_mirror`류
  비강제 쌍은 geometry 병합에서 정상적으로 제외됨).**
- **`two_stage_ota`의 `M5/M7` — 처음엔 edge case로 오판했다가 사용자 반문으로 정정됨
  (같은 세션 내 왕복, 코드 미반영 상태라 실제 손해는 없었음).**
  1. **최초 판단(오판)**: `M5/M7`이 `current_matched`(축A=강제)인데 `device_roles`상
     `M5.vertical_stack_id="stage1"`, `M7.vertical_stack_id="stage2"`로 다르다는 이유로
     "스테이지를 넘나드는 강제 병합은 문제"라고 결론짓고, "규칙2에 축B 조건(vertical_stack_id
     같을 때만 강제병합) 추가"를 제안 → 사용자가 일단 승인.
  2. **사용자의 반문**(`M12/M21`은 gnd 경유·`M13/M22`는 vdd 경유로 같은 row 아니냐)으로
     이 축B 조건을 `current_reuse_telescopic_ota`에 실제로 적용해보니, 같은 이유로 정말
     매칭이 필요한 `M12/M21`·`M13/M22`(current_matched, `current_mirror` 문서용 그룹의
     멤버이기도 함)까지 강제병합이 끊겨 그룹이 쪼개지는 **부작용을 실측으로 확인**.
  3. **재검토 결과 — 최초 판단 자체가 틀렸었다는 게 밝혀짐**: `M5/M7`
     (`source=gnd,gate=bias` 동일)과 `M12/M21`(`source=gnd,gate=Vbias4` 동일)·`M13/M22`
     (`source=vdd,gate=Vbias1` 동일)는 전부 **"레일에 소스가 직접 물리는 1단 소자가 같은
     게이트로 매칭되는" 동일 패턴**이다. 이건 세션8이 이미 검증한 전례(7-member vdd 그룹
     `{M18_bg,M8,M13,M17,M22,M60,M61}` — "전부 vdd 공유 1단 PMOS라 정상")와 정확히 같은
     구조라, **stage/vertical_stack_id가 달라도 강제병합을 막을 이유가 없다.**
     `vertical_stack_id`는 `allocate_stack_headroom()`의 전압 헤드룸 예산 배정용 라벨일
     뿐, "물리적으로 같은 행에 놓일 수 있는가"와는 별개 축이라 이 판단 기준으로 못 쓴다.
  4. **왜 이게 "레일 경유 = 매칭 어려움"이라는 이전 세션 결론과 모순이 아닌지(사용자 질문에
     대한 답)**: 그 결론은 **규칙1**(순수 connectivity로 기능블럭을 *자동 발견*하는 규칙)에
     한정된다 — 레일/정션(`drain=drain`)을 자동 병합 트리거에서 뺀 이유는, 회로 전체가
     결국 레일에 닿기 때문에 레일 공유를 병합 근거로 쓰면 **서로 무관한 기능블럭이 뭉개지기**
     때문(nmcnr의 "vdd 공유 6-PMOS hub" false-positive가 실측 사례). 반면 **규칙2**는 이미
     선언된 `current_forced=true`를 *적용*하는 것뿐이라 "레일로만 연결"이 병합의 근거가
     아니다.

  ⚠️ **4번 설명 자체에 있었던 2차 오류(사용자가 다시 지적, 정정)**: 위 4번을 처음 쓸 때
     "매칭 관계는 회로 설계 의도(Vbias4/Vbias1로 같은 바이어스를 미러링)로 이미 확정됐다"고
     썼는데, **이건 정확히 `sizing_recipe.py` 1901-1914행이 이미 실패를 겪고 폐기한 옛 판단
     기준이다.** 그 주석: "이전엔 `current_mirror`가 '같은 gate net을 공유'(구조적 사실)와
     '같은 전류로 강제 병합'(설계 의도)을 동시에 의미했는데... '같은 gate=같은 전류'라고
     가정한 옛 매핑이 M8/M13을 한 `current_mirror` 쌍으로 잘못 묶어 **KCL 크래시**를 낸 뒤
     발견됨." 즉 "같은 게이트(바이어스)를 공유하는 설계 의도"는 **`current_mirror`(축A=false)
     의 정의 그 자체**이지 `current_matched`(축A=true)의 근거가 아니다.
     **`M12/M21`이 실제로 축A=true인 진짜 근거**(topology.json 자체 주석)는 "같은 바이어스
     공유"가 아니라 **`sizing_roles`에서 `r_diode_M11a`라는 같은 θ(theta)를 쓰도록 사이징
     단계가 이미 강제하는 구체적 사실**이다(`M10/M19`는 `kcl_sink` theta로 동일 매커니즘).
     ⚠️ **`M13/M22`는 재정정됨(2차) — 실은 근거 있었음.** `matching_pairs`의 `M13/M22`
     항목 자체엔 `_comment`가 없어서 "근거 없음"이라고 판단했었는데, `sizing_roles.theta`를
     직접 열어보니 **진짜 근거가 있다**:
     ```json
     {"name": "r_classab_diode_src", "root": ["M13","M22"], "reference": ["M1a","M1b"], ...}
     ```
     즉 `M12/M21`(`r_diode_M11a`)과 완전히 같은 메커니즘 — θ의 `root` 리스트가 두 소자를
     같은 값으로 강제한다. `matching_pairs`의 `_comment` 유무로만 근거를 판단한 게 이번
     오류였다 — **진짜 근거 소스는 `sizing_roles.theta[].feeds.root`이지 `matching_pairs`의
     `_comment`가 아니다.**

  5. **`M5/M7`(two_stage_ota)만 정말로 근거가 없다 — 구조적으로 대조 대상 자체가 없음**:
     `two_stage_ota.topology.json`엔 `sizing_roles`/θ 그리드서치 필드가 **아예 없다**
     (`compensation.function="miller_ota_topology"`, 폐형식 gm1/gm2 계산이라
     `optimize_full_circuit_budget()`의 θ 탐색을 안 씀 — `current_reuse_telescopic_ota`류와
     사이징 방법론 자체가 다르다). 그래서 `M12/M21`·`M13/M22`처럼 대조할 θ-forcing 근거가
     이 회로엔 **원천적으로 존재할 수 없다.** 게다가 `sizing_recipe.py` 1915-1917행
     (`auto_mirror_ratios`)은 `kind=="current_matched"`인 쌍에 **자동으로 1:1 전류 비율을
     강제**하는데, `M5`(1단 tail)/`M7`(2단 bias)이 정말 1:1인지는 검증된 적이 없고
     `compensation.parameters`의 별도 `"NDP"`(단간 비율로 추정)가 있는 걸 보면 오히려
     스테이지별로 전류가 다를 가능성이 있다.
     **`M5/M7`의 `current_matched` 선언 자체가 옳은지 다음 세션에서 재검토할 것** —
     θ-forcing 대조가 원천적으로 불가능하므로 사용자에게 회로 의도(1단/2단이 실제로 같은
     전류인지)를 직접 물어야 한다(connectivity/sizing_roles 어느 쪽으로도 못 정함).

  6. **"이를 위한 새 스키마 필드가 필요한가?"(사용자 질문) — 불필요, 대신 audit 스크립트가
     필요하다.** θ-탐색 회로(`current_reuse_telescopic_ota` 등)는 근거가 이미
     `sizing_roles.theta[].feeds.root`에 존재한다 — `matching_pairs`에 같은 정보를 중복
     기록하는 새 필드를 만들면 두 곳이 어긋날 위험만 커진다. 대신 **검증 스크립트 하나**가
     필요: `current_forced=true`인 모든 `matching_pairs` 쌍에 대해 `sizing_roles.theta`의
     `root`/`reference`에 두 이름이 함께 있는지 자동 대조 — 있으면 통과(`M12/M21`,
     `M13/M22`), 대조 대상 자체가 없으면(`two_stage_ota`처럼 `sizing_roles` 없는 회로)
     자동으로 "사람 확인 필요" 플래그. 아직 스크립트 작성 안 함 — L1 승인 시 같이 논의.

  7. **`M5/M7` 문제 해결됨 — 최종적으론 `matching_pairs`에서 아예 뺐다(JSON 정정 완료,
     2단계 정정).** 사용자가 회로 역할(M1/M2=diff_pair, M3/M4=current_mirror load,
     M5=tail, **M6/M7=output buffer**)을 직접 알려준 게 결정적 단서였다.
     - **1단계**: `net_uses`를 실측하니 `OUT` net이 `M6.drain`/`M7.drain` **정확히
       2단자뿐** — 축A 규칙1("정확히 2단자면 병합, 극성 무관")이 그대로 적용되는 **진짜
       KCL 사실**(`I(M6)=I(M7)`, current_reuse의 `NodeM1=M106/M108` 사례와 동일 패턴).
       옛 `M5/M7` 선언은 `gate=bias, source=gnd` 공유라는 **구조적 유사성만으로 매칭을
       가정**한 것(이 세션 내내 반복 확인한 "같은 gate+rail 공유는 current_mirror급
       사실일 뿐 current_matched 근거가 아니다" 오류의 또 다른 사례) — 사용자가 "M5는
       매칭 의도 없음, 비율 달라도 됨"으로 확정. 처음엔 `M5/M7`→`M6/M7`로 고쳐 넣었다.
     - **2단계(사용자 재질문으로 정정)**: "branch 분석하면 바로 나오는데 왜 명시해야
       하나"는 사용자 질문에 재검토한 결과, `M6/M7`의 전류 동일성은 **소자 미스매치와
       무관한 순수 위상적(KCL) 사실**이라 진짜 `current_mirror`/`diff_pair`처럼 레이아웃
       interdig로 개선될 매칭 오차가 애초에 없다는 게 드러남. `derive_stack_groups()`가
       선언 없이도 "정확히 2단자면 병합" 규칙으로 이미 자동 처리하므로(사이징 쪽은
       선언이 완전히 중복), **`matching_pairs`엔 아예 넣지 않기로 최종 결정** — "매칭
       필요"라는 잘못된 신호를 주는 것보다 낫다. 별도의 새 카테고리(예: 파라시틱
       최소화용 인접 배치)도 검토했으나, 그걸 소비하는 엔진 로직이 없어 죽은 메타데이터가
       될 뿐이라 기각(YAGN, 필요해지면 그때 별도 축으로).
     **최종 상태**: `two_stage_ota.topology.json`의 `matching_pairs`엔 `M3/M4`,`M1/M2`만
     남음. `compensation.notes`에 M6/M7의 KCL 관계와 왜 선언 안 하는지 산문으로 기록.
     단일 파일의 role/matching 메타데이터 재분류라 즉시 반영(엔진 코드 미변경).

  8. **부수 발견 — 축A 규칙1도 레일 제외가 필요할 수 있다(L1/L2 구현 시 논의 필요, 아직
     미반영).** `M5/M7`이 잘못 선언된 배경을 추적하다 발견: `two_stage_ota`처럼 소자 수가
     적은 회로에서는 `gnd`/`vdd` 같은 레일이 **우연히 정확히 2번만 쓰일 수 있다**(이번
     경우 `gnd`: `M5`,`M7` 딱 2건). 축A 규칙1("정확히 2단자면 병합, 극성 무관")은 지금
     레일을 제외하지 않는데, 레일은 외부 전원으로 무한히 전류를 흘릴 수 있어 "2단자=닫힌
     계=전하보존" 논리가 성립하지 않는다 — `current_reuse`처럼 큰 회로(vdd 16회/gnd
     13회)에선 이 함정이 안 드러났을 뿐, **작은 회로에선 축A 규칙1이 레일에서 거짓
     KCL 관계를 만들어낼 수 있다.** 축B 규칙1(geometry)은 이미 레일을 제외하는데, 축A
     규칙1(KCL)은 아직 안 그렇다 — L1/L2 구현 시 축A 규칙1에도 레일 제외를 추가할지
     검토할 것(단, 195행 "극성체크는 축B에만" 원칙처럼, 레일 제외도 축B만의 것인지
     축A에도 필요한지는 별도 판단 필요 — current_reuse의 M106/M108(NodeM1, non-rail
     2단자)류 진짜 KCL 사실은 계속 잡아야 하므로 "레일이 아닌 2단자"로 조건을 좁히는
     정도면 충분해 보임, 코드는 아직 안 건드림).

  **최종 결정(정정, 2026-08-05 세션9): 축B 조건 추가는 폐기, 규칙2는 원래 설계대로
  (current_forced=True 쌍이면 조건 없이 강제 병합) 유지 — 이건 그대로 유효하다.** `M12/M21`·
  `M13/M22`는 둘 다 `sizing_roles.theta`의 θ-forcing 근거로 검증 완료. **`M5/M7` 문제는
  해결 완료**(위 7번) — 옛 `M5/M7` 선언은 삭제, `M6/M7`의 진짜 KCL 관계는 선언 없이
  자동 검출에 맡기기로 확정(JSON 반영됨) — 더 이상 미해결 항목 아님. 남은 건 8번의
  일반화된 엔진 이슈(축A 규칙1 레일 제외)뿐, L1/L2 구현 시 같이 논의.

  **부가 확인(사용자 질문, 2026-08-05)**: 규칙1(자동발견, drain=source만)과 규칙2(선언된
  `current_forced` 쌍만 강제병합)를 실제 설계대로 **같이** 적용하면 "Vbias1 7-소자 hub"
  문제는 발생하지 않는다 — 그 7개는 그 자체로 `kind="current_mirror"`(축A=false)라
  규칙2가 그룹째로 건드리지 않고, 개별 선언된 2-소자 쌍(`M8/M17`,`M13/M22`)만 규칙2로
  병합된다. 이 문제는 세션9 도중 검토했던 **가상의 대안 규칙**("같은 source+같은 gate면
  자동 병합", 실제 L2 설계엔 없음)에서만 재현됐다 — 실제 L2 설계는 이 문제가 없음을
  재확인, 오히려 설계 견고성 확인.

---

## 세션9 — `folded_cascode.topology.json` netlist 전면 정정 (사용자 정정지시, connectivity, **최종 확정**)

`current_matched` 감사(위 §의 4개 회로 전수조사) 중 `folded_cascode`의 `M3/M4`·`M9/M10`이
"같은 gate+rail뿐, 근거 없음"으로 flag됐다가, 사용자가 **10여 차례에 걸친 정정지시로 실제
connectivity를 직접 알려줘서** 원래 netlist(외부 bias1~bias5로 단순화된 버전)가 **다이오드
연결 레퍼런스 구조를 잘못 생략한 것**이었음이 드러났다. 중간에 Claude가 `M11`을 임의로
삭제하는 실수를 했다가 사용자에게 즉시 지적받고 원복한 사고가 있었음(⚠️ **교훈**: connectivity
정정 지시를 "구현 아이디어"로 확장 해석해서 명시 안 된 소자를 건드리면 안 된다 — 정확히
지시된 것만 반영할 것). **최종 확정 netlist**(사용자 확인 완료, `topology_to_markdown.py`로
재검증):

| Name | Source | Drain | Gate | 역할 |
|---|---|---|---|---|
| `MP` | vdd | `vb1` | `vb1` | PMOS 다이오드(vb1 레퍼런스) |
| `M3`/`M4` | vdd | X/Y | `vb1` | MP 미러(폴딩 전류원) |
| `M1`/`M2` | `tail` | X/Y | vin_p/vin_n | diff pair(실제 tail 전류원 소비) |
| `M11` | gnd | `tail` | `vb2` | MN 미러 — diff pair의 진짜 tail 전류원 |
| `MN` | gnd | `vb2` | `vb2` | 독립 레퍼런스 다이오드 |
| `M9` | gnd | `Vg9` | `Vg9` | NMOS 다이오드(X-branch 캐스코드 레퍼런스) |
| `M10` | gnd | `Vg10` | `Vg9` | M9 미러 |
| `M5` | **Y**(교차) | `Vg7` | bias3(외부, 다이오드 아님) | 캐스코드 |
| `M7` | `Vg9` | `Vg7` | `Vg7` | NMOS 다이오드(레퍼런스) |
| `M6` | **X**(교차) | `out` | bias3(외부, 다이오드 아님) | 캐스코드 |
| `M8` | `Vg10` | `out` | `Vg7` | M7 미러(출력 노드에서 상쇄) |

`ideal_sources`: `Ibg`(current_source, terminals=`vb1`,`vb2`, value 미상 TBD) — `vb1`(MP측)과
`vb2`(MN측) 두 독립 다이오드 레퍼런스 사이의 전류 관계를 트랜지스터 대신 이상적 소자로 모델링.

**핵심 구조 3가지**(전부 사용자 정정으로 확정):
1. 단일 출력(`out`) — 옛 `outA`/`outB`(fully-differential처럼 보였던 두 출력)는 존재하지 않음.
   X-branch 신호전류를 `M7`(다이오드)+`M8`(미러)로 반전해 `out`에서 Y-branch(`M6`) 소싱 전류와
   상쇄하는 전형적 differential-to-single-ended 폴디드 캐스코드. `Vg7`(M7 다이오드 노드)과
   `out`(진짜 출력)은 분리된 별개 net.
2. `M5`/`M6`이 **교차(cross-coupled)** — `M5.source=Y`(=`M4.drain`=`M2.drain`),
   `M6.source=X`(=`M3.drain`=`M1.drain`), 처음엔 자기 branch(비교차)로 잘못 넣었다가 정정.
3. `X`/`Y`는 순수 폴딩 노드(3단자씩)로, `M9`/`M10`의 다이오드+미러 캐스코드 스택은 별도
   `Vg9`/`Vg10` net으로 분리 — 처음엔 `X`/`Y`에 얹었다가 과부하(7/5단자)로 잘못 판정.
4. `vb1`(MP/M3/M4 레퍼런스)과 `tail`(M1/M2 diff pair 실제 전류원, M11이 공급)은 **서로 다른
   두 노드** — 처음엔 하나로 합쳤다가 사용자가 "새로운 별도 node로 분리" 지시로 확정.

**matching_pairs**: `M3/M4`·`M9/M10`(기존 `current_matched`)에 다이오드 근거 `_comment` 추가,
`M7/M8`은 `branch_symmetric`→`current_matched`로 재분류(다이오드+미러 확인). `M5/M6`은
다이오드 없이 외부 `bias3`만 공유해 `branch_symmetric` 유지 — 이 회로의 "근거 없음" 감사 항목
전부 해소.

✅ **사용자 최종 확인 완료**(2026-08-05) — 더 이상 미해결 항목 아님. `run_harness.py`류
self-test가 `folded_cascode`를 다루면 이 정정이 회귀 없이 반영됐는지 확인 필요(사이징 엔진
코드는 아직 안 건드림 — 이번 세션은 connectivity/matching_pairs/ideal_sources만 수정).

---

## 세션9 총정리 — 이번 세션에 다듬은 새 스키마와 원칙 (사용자 요청으로 종합)

**A. L1 스키마**(세션8 설계, 이번 세션 개념 명확화) — `kind` 폐지, `current_forced`(축A,
선언 필수)/`matching_sensitivity`(축C, 선언 필수)/`shares_node`(축B, 자동계산) 3축으로 분해.
`current_mirror`/`branch_symmetric`은 (축A,축C) 선언값이 완전히 같아(`false`,`ratio`) 축B로만
갈리므로 새 스키마에서는 사실상 하나로 합쳐짐(사람이 둘을 구분해 선언할 필요 없음).

**B. L2 그룹핑 규칙** — 규칙1(자동발견, `_kcl_series_union`/`_geometry_colocation_union`) vs
규칙2(선언된 `current_forced` 쌍 강제병합). 이번 세션에 확립된 핵심 원칙:
1. 규칙1(자동발견)과 규칙2(선언적용)는 답하는 질문이 다르다 — "레일 경유=매칭 어려움"
   원칙은 규칙1 한정, 규칙2엔 적용 안 됨.
2. **"같은 gate+rail 공유"만으로는 `current_forced=true`의 근거가 안 된다** — 이건
   `current_mirror`(축A=false)의 정의 자체다(`sizing_recipe.py`의 M8/M13 KCL 크래시 전례).
   진짜 근거는 (a) 진짜 2단자 KCL 노드 또는 (b) `sizing_roles.theta`의 명시적 forcing.
3. **순수 위상적(KCL) 사실은 `matching_pairs`에 선언하지 않는다** — 소자 미스매치가 아니라
   순수 KCL로 강제되면 interdig로 개선될 매칭 오차가 없으므로(`two_stage_ota` M6/M7 사례),
   선언 대신 축A 규칙1의 자동 검출에 맡긴다.
4. 폐기된 아이디어 — 규칙2에 `vertical_stack_id` 기반 조건 추가(다른 처리 단과 대칭 좌우
   절반을 구분 못 해서 폐기, 원래 설계 유지).
5. 새 스키마 필드 대신 audit 스크립트 — `current_forced=true` 근거를 `matching_pairs`에
   중복 기록하지 말고 `sizing_roles.theta[].feeds.root/reference`와 자동 대조(아직 미작성).
6. 부수 발견(미반영) — 축A 규칙1도 레일 제외가 필요할 수 있다(작은 회로에서 거짓 KCL
   관계 생성 가능, `two_stage_ota` M5/M7 오류의 근본 원인으로 추정).

**C. 실전 검증** — `folded_cascode` netlist 전면 재구성(위 절)으로 "같은 gate+rail은 근거
부족" 원칙이 실전에서 정확히 맞아떨어짐을 재확인. `ideal_sources`(정정: 처음 쓴 게 아니라
`current_reuse_telescopic_ota.topology.json`에 이미 `Iref`(current_source) 예시로 쓰이고
있었음 — `passive_elements`도 `R1`/`R2`/`Cc1`/`Rz1`/`Cc2`/`Rz2` 등으로 이미 사용 중. 이번
세션은 기존 스키마를 `folded_cascode`에 동일하게 적용한 것뿐)를 `folded_cascode`에도
동일 스키마로 적용.

---

## 다음 세션 작업 순서 (권장, 각 단계 사용자 승인 필수)

1. `run_harness.py` 재실행(위 "지금 상태" 1번), 끝까지 확인. **(세션9: 실행함, 완료 대기
   중이었음 — 세션10은 로그부터 확인할 것, `run_harness_session9.log`)**
2. ~~위 "아직 재검증 안 된 것" 2건 먼저 마무리~~ **(세션9 완료, 결과는 위 "세션9 — 재검증
   2건 완료 결과" 참고)**
2.5. ~~`M5/M7`(two_stage_ota) 재검토~~ **(세션9 완료 — 사용자가 회로 역할 확인,
   `M6/M7`로 정정해 JSON 반영 완료. 위 "세션9 — 재검증 2건 완료 결과" §7 참고.)**
   `M13/M22`도 `sizing_roles.theta`의 `r_classab_diode_src`로 근거 확인 완료(§4).
   **남은 항목**: L1 구현 시 (a) `current_forced=true` 선언을 `sizing_roles.theta`의
   root/reference와 자동 대조하는 audit 스크립트(§6), (b) 축A 규칙1에도 레일 제외를
   추가할지(§8, `M5/M7` 오류의 근본 원인으로 추정되는 일반화된 이슈) 같이 논의할 것.
3. L1(스키마) 설계를 사용자에게 다시 요약 보고 → 승인 시: 4개 JSON 파일의 `matching_pairs`
   마이그레이션(34건, 기계적 룩업) + `sizing_recipe.py`/`stick_diagram.py` 두 엔진 파일
   수정 + self-test 전체 회귀 확인.
4. L2(그룹핑 규칙) 설계를 사용자에게 요약 보고 → 승인 시: `derive_stack_groups()`를
   `_kcl_series_union()`/`_geometry_colocation_union()` 두 함수로 분리 구현 +
   `sizing_recipe.py`의 두 호출부(`stack_groups_kcl`/`stack_groups_geometry`) 업데이트 +
   self-test 회귀 확인. **(세션9: 규칙2에 축B 조건 추가를 검토했다가 부작용 확인 후 폐기함
   — 원래 설계대로 조건 없이 구현할 것, 위 "세션9 — 재검증 2건 완료 결과" §M5/M7 참고)**
5. L3(walk 선택) — 아직 설계 자체가 없으므로, 다음 세션에서 **논의부터 새로 시작**(그래프
   이론적 접근법 후보들 검토 → 사용자와 방향 합의 → 그 다음에야 구현 논의).
6. L4(사이징→레이아웃 연결) — L1/L2/L3 방향이 정해진 뒤에 설계 착수(축B 값을
   `assign_finger_geometry()`가 소비하는 인터페이스 설계).
7. 전부 반영 후 self-test 전체 재실행 + `run_harness.py` 재실행으로 최종 회귀 확인.
8. 완주하면 세션4 핸드오프 원래 "다음 단계"(Cc/Rz/Iref 값 채우기, PSRR 폐형식 재유도)로
   이어가기.
9. (미정, 낮은 우선순위, 세션6부터 이월) `find_structural_symmetry_candidates()`의
   `"dual"` transform 오탐 개선 — 손 안 댐.

---

## 세션7 이전 배경 (압축 요약 — 세션8이 "정정4"를 실측으로 훨씬 더 발전시켰으므로 세부는
## 위 L1~L4를 우선 참고할 것)

세션7은 `current_reuse_telescopic_ota.topology.json`의 몇몇 `matching_pairs`(`M2a/M2b`를
`diff_pair`로 되돌릴지 등, "정정1/2")를 논의하다가 "정정3"(KCL축과 레이아웃축 분리 원칙)에
도달했고, "정정4"에서 축1(row 배정)/축2(매칭 기법) 프레임을 제안하며 끝났다. 세션8은 이
프레임을 실측으로 검증해 L1~L4의 4계층 모델로 발전시켰다 — "정정1/2"의 개별 재분류
(`M2a/M2b`→`diff_pair` 등)는 L1의 축B 전수조사가 **독립적으로 같은 결론에 도달**했으므로
(위 L1 "축B 역설 6건" 표 참고), L1 마이그레이션에 자동으로 포함된다(별도로 다시 다룰
필요 없음).

## 세션7의 핵심 교훈 (계속 지킬 것, 세션8이 실제로 준수하며 진행함)

- **엔진/스키마 변경은 이유가 아무리 명확해 보여도 절대 먼저 구현하지 말 것** — 반드시
  논의하고 명시적 승인을 받은 뒤에만 코드/JSON을 고칠 것.
- `branch_symmetric`(또는 그 성질을 가진 `current_matched`)은 겉보기엔 "전류가 확인 안 된
  pending 상태"처럼 보여도, 전체 회로의 KCL을 끝까지 추적하기 전엔 "electrically
  independent"라고 단정하면 안 된다.
- KCL(전류가 강제되는가)과 레이아웃(어떤 배치 기법이 필요한가)은 **서로 다른 질문**이고
  같은 `kind` 문자열 하나로 두 질문에 동시에 답하려 하면 꼬인다 — L1이 이걸 구체적으로
  해결하는 설계다.
- **세션8이 추가로 배운 것**: "그럴듯한 성공 결과"(dx=0.00 같은)도 전제 조건(극성 유효성
  등)을 다시 확인하기 전엔 믿지 말 것 — 실제로 두 번이나 무효한 전제 위의 결과를 "성공"
  이라고 잘못 보고했었다(L3 참고). 사용자의 반문("그거 정말 안 되는 거 맞아?")이 두 번 다
  올바른 재검토로 이어졌다 — 결론에 도달했다고 검증을 멈추지 말 것.

## 작업 파일 위치

- `skills/analog-gmid-design/assets/stick_diagram.py`
  - `derive_stack_groups()`(1425행 부근) — L2 재설계 대상(두 함수로 분리).
  - `_kind_of()`/`audit_row_split()`(2669행, 2580-2790행 부근) — L1 게이트 정책 교체 대상.
  - `select_layout_tool()`(2545행)/`repair_matching_safety()`(2835행) — L1 반영 후
    재검토 필요(특히 `repair_matching_safety()`의 "공유 hub 없으면 skip" 로직이 L1 이후에도
    필요한지).
  - `build_graph()`(1546행 부근)/`hierholzer()`(1636행 부근) — **L3 설계·구현 대상**,
    현재 완전히 matching-blind.
  - `assign_finger_geometry()`(1932행 부근) — **L4 설계·구현 대상**.
- `skills/analog-gmid-design/assets/sizing_recipe.py`
  - `_kcl_pairs`(1947행 부근) — L1 반영 대상(`kind` 체크 → `current_forced` 체크).
  - `stack_groups_kcl`/`stack_groups_geometry` 호출부(1919-1952행 부근) — L2 반영 대상
    (두 함수로 분리된 `derive_stack_groups()` 호출로 교체, 극성 체크는 geometry만).
- `skills/analog-gmid-design/assets/library/current_reuse_telescopic_ota.topology.json`
  — L1 마이그레이션 1순위 대상(축B 역설 6건 전부 이 파일).
- `skills/analog-gmid-design/assets/library/nmcnr_amplifier.topology.json` — L1 마이그레이션
  대상(`M104/M105`→current_mirror, `M106/M107`→branch_symmetric 등 이미 올바른 kind라
  기계적 변환만 필요).
- `skills/analog-gmid-design/assets/library/folded_cascode.topology.json` — **세션9에
  netlist/ideal_sources/matching_pairs 전면 재구성 완료**(위 "세션9 — folded_cascode
  netlist 전면 정정" 절 참고, 사용자 최종 확인됨). L1 마이그레이션 시 최신 `matching_pairs`
  (`M3/M4`,`M9/M10`,`M7/M8`=current_matched, `M1/M2`=diff_pair, `M5/M6`=branch_symmetric)
  기준으로 진행할 것 — 세션8 시점 34건 표는 `M7/M8` 재분류 이전이라 그 표만 보고
  마이그레이션하면 안 됨.
- `skills/analog-gmid-design/assets/library/two_stage_ota.topology.json` — **세션9에
  `matching_pairs`에서 `M5/M7` 삭제 완료**(위 "세션9 — 재검증 2건 완료 결과" §7 참고).
  최신 `matching_pairs`는 `M3/M4`(current_matched), `M1/M2`(diff_pair)뿐 — `M6/M7`은
  의도적으로 미선언(축A 규칙1 자동검출에 위임).
- `skills/analog-gmid-design/references/stick-diagram-euler-layout.md` — §2.6/§2.7이
  L1~L3 재설계 후 갱신 필요(특히 "swap-분배로 dx=0.00/dy=0.20" 실측 인용이 L3의 "존재는
  하지만 알고리즘이 못 찾는다"는 정정된 이해와 어떻게 정합되는지 정리 필요).
- `workspaces/current-reuse-telescopic-ota-report/run_harness.py` — 다음 세션 최우선
  확인 대상, 로그는 `run_harness_session9.log`(세션9가 실행, 완료 확인 못 함 — 위 "지금
  상태" 1번 참고).

## 참고 — 사용자 협업 메모리 (자동 메모리 시스템에 저장됨, 요약만)

- 최종 보고는 항상 한글로.
- 상상으로 채우지 말고 근거·실제 확인 후 진행 — "확정"처럼 보이는 결과도 전제(예: 극성
  유효성)를 다시 확인하기 전엔 맹신 금지(세션8에서 두 번 위반했다가 자체 수정한 사례 있음).
- topology.json이 유일한 토폴로지 소스 — connectivity는 사용자 전용, role/matching/theta
  같은 메타데이터는 Claude가 분석해서 업데이트 가능.
- 장시간 실행은 `run_in_background: true`.
- 회로도 이미지/PDF 판독은 신뢰 못 함 — connectivity는 `topology_to_markdown.py`로
  net 기준 표를 뽑아 확인. 논문 본문 텍스트 추출은 신뢰 가능.
- topology 정정은 대기열에 쌓았다가 "한꺼번에 반영해" 지시가 와야 일괄 반영(connectivity
  한정).
- 논문에 없는 컴포넌트 값은 "논문 인용"만으로 확정 짓지 말 것.
- 복잡한 analog 회로 폐형식 재유도는 opus 에이전트(가능하면 git worktree 격리) 위임이
  효과적.
- git commit 시 heredoc-in-`$()`이 bkit 훅에 막힘 — 파일로 메시지 작성 후 `git commit -F`.
- 엔진/스키마 변경은 국소적 메타데이터 정정(파일 하나의 kind 재분류 등)은 바로 실행
  가능하지만, **여러 파일/여러 회로에 영향을 주는 엔진 로직 변경은 반드시 사전 논의·승인
  필요**(세션7에서 이 규칙을 어겨 즉시 원복 지시받은 사고 있었음). 세션8은 이 규칙을 끝까지
  지켜 모든 실측을 격리된 1회성 스크립트로만 수행하고 실제 파일은 전혀 안 건드렸다.
