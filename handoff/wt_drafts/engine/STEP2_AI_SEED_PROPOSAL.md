# 단계 ② 착수 전 결정 자료 -- AI 기능 해석 시작점(design intent seed)을 층 0 시작점 출처로 더하는 안

작성 2026-10-14. 성격: **결정 질문 초안**(저장소·엔진·design·spec 파일은 고치지 않았다. master `34932a9` 읽기 전용).
배경: 사용자 제안(2026-10-14) "AI가 topology를 정성적으로 분석해 기능별로 시작점을 잡고, 전력 기준·면적 기준 두 안을 내서 그것을 기준으로 층 0 값을 찾는 것이 더 나은 시작점이 아니냐". 오케스트레이터 의견(사용자 "그래, 진행해"): 대체가 아니라 **추가 시작점 출처**로 넣고 측정으로 판정한다.
표기: **[사실]** = 파일:줄 인용으로 확인한 것. **[추측]** = 확인하지 않은 판단. **[제안]** = 이 문서의 기본안(사용자 결정 전). 새 상수는 만들지 않았다. 아래 수치는 모두 인용이다.

경로 약어: `P` = `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`, `D40`·`D41` = `docs/02-design/features/gain-budget-gmid-sizing.{40-engine,41-gain-budget}.design.md`, `E` = `skills/analog-gmid-design/gmid_engine`, `M` = `skills/analog-gmid-design/references/gm-id-methodology.md`, `PKG` = `wt/_drafts/engine/STEP2_DESIGN_GAPS_DECISION_PACKAGE.md`.

---

## 0. 먼저 알릴 사실 (결정에 직접 영향)

1. **[사실] A' 손분석은 엔진 입력으로 쓸 수 없다.** P:297 DEC-98 (2) "AI 손분석: ... 결과를 엔진 입력으로 쓰지 않음. 손분석 작성 주체 ≠ 엔진 코드 작성 주체(WP-13)". D40:1603 독립 대조군 행 "결과는 엔진 입력(spec·topology·`structure.json`·출발값)으로 쓰지 않고". → 이번 제안의 AI 시작점은 **A' 손분석과 다른 산출물·다른 작성 주체**여야 하고, A' 손분석을 보고 쓰면 A' 대조군의 독립성이 깨진다(Q-AI3).
2. **[사실] 엔진의 실패는 '출발점 생성'에서 난다는 실측이 이미 있다.** PKG §0.3 "세 회로 모두 커널(DC·봉인·ss 판정)은 유효점을 표현하고 SPICE 와 같은 방향으로 판정한다. 엔진이 못 하는 것은 그 점 근처로 가는 출발점 생성(출발 구간·매크로·자리값·KVL 출발)이다." (current_reuse 손 θ → sealed, 엔진 centre θ0 SEAL_VIOLATION·layer0 Halton 808 점 뒤 실패; sf_pushpull 손 x3 θ → sealed, 엔진 layer0 46 분 미종료). 사용자 제안의 동기와 맞는 증거다. 다만 이 손 θ는 A' 손분석 점이라 그대로 시작점으로 쓰면 1번과 충돌한다.
3. **[사실] master의 층 0은 아직 '최소형'이다.** `E/search/find_front.py:5` "층 0 시작점(`layer0_start`, DEC-71 최소형) -> 시작점(`start_points`: 층 0 점 + S3 이전 front 점 + `given_starts`)"; `E/search/layer0_center.py:641` "[U13] 출발 사다리(`graph/start: rungs` ...)를 칸 순서로 커널에 확인해 처음 받아들일 상태인 칸에서 출발한다". D41 §5 gain 예산 층 0(as-built `26ebfda`·`bd19cc6`)은 master에 없다(`git merge-base --is-ancestor bd19cc6 master` = 아님, 브랜치 design-l0-fix 등에만). D40:1679 U17 ② 행 "층 0 데이터 흐름(41 §5 v1.6 U15 재구현과 한 변경)" -- 즉 측정 대상 '층 0 조립점'은 ②가 만든다.
4. **[사실] U-33 측정 도구는 아직 없다.** D40:1050 `tools/compare_paths.py`는 design에만 있고 저장소에 파일이 없다(`git ls-files | grep compare_paths` 0건). P:1250 U-33 착수 시점 "7b 착수 전(소규모 프로토타입으로 측정한다 -- 세 층을 다 만든 뒤 '안 쓴다'가 나오면 WP-01과 충돌한다)".
5. **[사실] 기능 라벨로 gm/ID를 고정했던 옛 엔진의 실패 기록이 있다.** M §13.7 "`gm_id_role="matching"`이 output-resistance 소자엔 틀린 목적함수였다 ... pm_deg=48.32도 ... 'gain'도 만능은 아니었다(M202 ... 66.61도로 나빠짐)". P:894 IC4 "role 라벨 과신 | 물리·connectivity 판정이 항상 우선 | `test_role_label_removal_invariance`: `headroom_role`/`gm_id_role`/`L_role` 전부 제거해도 결과 동일". 엔진 lint `E/tests/structure/structure_checks.py:975` `TAG_ROLE_KEYS_IC4 = ("gm_id_role", "L_role")`가 이 키 조회를 금지한다. → AI 기능 해석은 **판정·bounds·구조 유도에 들어가면 안 되고 시작점에만** 들어가야 한다(Q-AI1·Q-AI5).
6. **[사실] 원문 보관소 README는 master에 없다.** `assets/library/sources/README.md`는 브랜치 `sources-archive`(커밋 `012273f`)에만 있다(`git merge-base --is-ancestor 012273f master` = 아님). 이 문서의 원문 인용은 그 브랜치 경로와 로컬 원본 PDF 경로를 함께 적는다.

---

## 1. 현재 층 0 seed가 실제로 쓰는 것 (사실 요약)

### 1.1 master as-built (U13 출발 사다리 + 층 0 최소형)

| 단계 | 쓰는 입력 | 근거 |
|---|---|---|
| 출발 구간(§6) | S1/S1v, spec, LUT 곡선, A6 상한표. gm/ID 하한 = 헤드룸(§6.2), 상한 = 속도(§6.3), L 구간(§6.4), 전류 = S1v 매크로(§6.5) | D41:1233 "입력은 S1/S1v, spec, LUT 곡선, A6 상한표다" |
| 출발 사다리 | 칸 0 = 실행 가능한 최대 t*(gm/ID = lo + t·(hi − lo)), 칸 k = t*/2^k | D41:1259-1262 |
| 층 0 최소형 | 칸 0부터 커널 확인 → 상자 중심·전류 Chebyshev 중심 → 봉인 여유 최대-최소, 실패 시 Halton 시험 | `E/search/layer0_center.py:1-30`, `:641` |
| 시작점 목록 | ① 층 0 점 ② 같은 S0·스키마·코드 지문의 S3 이전 front 점 ③ `given`(선언 x0) | `E/search/start_points.py:5-8` |

### 1.2 design 41 §5 v1.6 (② 재구현 대상) 층 0 seed

| 항목 | 내용 | 근거 |
|---|---|---|
| 역할 분류 S | gain 제약 전달 뷰 주경로 이득 블록에서 S1v AC 역할 `input`, 매크로 활성일 때. gm/ID는 §6 구간 안 LUT gm/ID 점 위 **자유 축**, ID = gm_req/(gm/ID) | D41:724 |
| 역할 분류 B | `load`·`mirror`·`diode_load`·`tail_source`, 바이어스 기둥, FF 셀. **"축이 아니다. §6 출발값 ... 을 쓰고, 외층 SLSQP가 다듬는다"** | D41:725 |
| 역할 분류 F | `cascode`·`pass`·`follower`, 매크로 비활성 회로의 `input` → 격자 폴백 | D41:726 |
| (a) gm/ID 역산 | 실측 9회로 블록 MOS 102개 중 ID가 KCL·선언으로 정해진 소자 0개 → ID 기지 역산은 발동하지 않음 | D41:733 |
| (c) VDS 배분 | VDsat + tol 하한으로 채운 뒤 `∂(gm/gds)/∂VDS` 큰 소자부터 LUT VDS 격자 간격 걸음 | D41:740-741 |
| (b) L 역산 | 블록 국소 gain(L_c) = T_b, PDK bin마다, bin 안 bisection | D41:750-751 |
| L 초기 목표 | 미러 = knee, 레플리카 = window 하한, 신호 = 역산, 그 밖 = §6 출발 L | D41:817-820 |
| 후보 집합 | 역산 → 검증(감싸는 LUT L 점 2) → 자유·폴백 격자 → 넓히기 | D41:850-854 |
| 고정 입력 첫 회차 | §6 출발값 + knee·LR5 종류 앵커 합집합을 **추가 후보**로 | D41:883 (R29 수용, 사용자 2026-10-08) |
| 외층 인계 | 조립점에서 SLSQP, 근방 반경 r_j = max(|θ_local − θ_assembled|, h_j), 2배 확장, **층 0은 전역 bounds를 줄이지 않는다** | D41:1035-1040 |
| 시작점 출처 순서 | 1 층 0 조립점 2 출발 구간 후보(41 §6.6) 3 S3 feasible 상위 `n_starts` 4 선언 x0 5 `layer0_center`(t_eval 첫 측정·다른 출처 없을 때만) | D40:792-797 |
| 계획 시작점 | "층 0 조립점(DEC-71 ..., U-33 확정 시) -> 지문이 일치하는 S3 feasible 점 상위 `n_starts`개(선언값) -> 부족하면 선언 x0. '지난 해 ± 창'은 추가 시작점으로만 쓴다(전역 bounds를 줄이지 않는다)" | P:453 |
| 보존 소유자 | '외층 시작점 대기열' = "대기 중인 시작점(층 0 조립점, 출발 구간 후보 등)의 스냅샷 / 그 시작점의 풀이가 끝날 때" | D40:308 |
| 평가 예산 | N_T = floor((B − T_used − T_reserve)/t_eval), 예산 상한 계산 용도 | D41:961, P:233 DEC-34 |

### 1.3 seed에 없는 것 (빈칸) -- AI 시작점이 채울 수 있는 자리

- **[사실]** B 소자(미러·부하·꼬리·바이어스)는 층 0 축이 아니고 §6 출발값 하나에 고정된다(D41:725). §6 출발값은 "7. gm/ID 선택: 구간 안의 최댓값"(D41:1254)과 사다리 t*/2^k(D41:1262)뿐이라 **모든 소자를 같은 t로 함께 움직인다**(소자마다 다른 위치를 고르지 않는다).
- **[사실]** S 자유 축의 정의역은 §6 구간 격자다(D41:724). 축을 구간 밖으로 넓히지 않는다.
- **[추측]** 그래서 "미러는 구간 하한(강반전) 쪽, 입력쌍은 상한 쪽"처럼 **기능에 따라 소자마다 다른 방향**을 고르는 시작점은 현재 어느 출처에도 없다. 이것이 AI 시작점이 추가로 줄 수 있는 정보다. 반대로 S 소자의 gm/ID 위치만 바꾸는 시작점은 층 0 자유 축 격자가 이미 덮을 수 있어 추가 가치가 작을 것이다(측정으로 확인, §4).

---

## 2. 제안: 선언 파일 + 엔진 배선

### 2.1 원칙 -- 무엇을 AI가 쓰고 무엇을 코드가 계산하는가

- **[사실]** P:325 WP-21: "결과가 **판정·기준값·보고 수치·다음 단계의 입력**이 되는 일은 **코드**로만 한다 ... 결과가 **회로 해석**(구조로 가를 수 없는 것)인 일은 **AI가 근거와 기본안을 내고 사람이 ratify**하며, 결과는 데이터(`structure.json`, 승인 기록)로 고정해 그 뒤로는 코드가 읽는다."
- **[제안]** 그래서 선언 파일에는 **해석(기능·방향)만** 적고, 숫자(θ)는 엔진 코드가 기존 구간·LUT·매크로로 계산한다. AI가 gm/ID·L·ID 숫자를 직접 적는 형식(=손 설계점)은 쓰지 않는다. 이유: (1) 숫자 시작점은 '다음 단계의 입력'이라 WP-21 첫째 부류(코드) 몫이다. (2) 숫자를 쓰려면 AI가 LUT 조회로 값을 만들어야 하는데 그것이 A' 손분석과 같은 일이 되어 §0-1 독립성 문제가 커진다. (3) 방향만 적으면 값의 근거가 엔진이 이미 가진 선언값(spec·LUT·PDK)이라 새 상수가 생기지 않는다(WP-03, P:307).
- 대안(숫자 직접 기입)은 Q-AI2 선택지로 둔다.

### 2.2 선언 파일 스키마 초안 `<회로>.design_intent.json`

위치: `assets/library/<회로>.design_intent.json`, `assets/heldout/<회로>.design_intent.json`([제안], structure.json과 같은 폴더 관례 -- `assets/library/nmcnr_amplifier.structure.json`).

선례: `structure.json`(`assets/library/nmcnr_amplifier.structure.json`): `topology_hash`·`rule_hash`·`facts[{concept, subject, value, status, evidence, approval_id}]`. D40:604 "`topology_hash`·`rule_hash`가 S0와 맞을 때만 ratified 사실을 적용하고, 다르면 해당 사실을 `review_needed`로 되돌린다".

```jsonc
{
  "schema_version": "1",
  "circuit": "<회로>",
  "topology_hash": "<connectivity_fp, structure.json과 같은 정의>",
  "spec_hash": "<sizing_spec.json 정규화 지문>",           // spec이 바뀌면 의도가 무효일 수 있으므로
  "vocab_hash": "<엔진 어휘 표(아래 anchor 목록) 코드 지문>",  // structure.json rule_hash와 같은 역할
  "authoring": {
    "author": "AI",                     // 작성 주체 식별(세션·agent 이름)
    "model": "<모델 ID>",
    "inputs_seen": ["topology.json sha", "sizing_spec.json sha", "원문 paper.md sha", "M sha"],  // 무엇을 보고 썼는지
    "inputs_not_seen": ["engine 출력", "A' 손분석 docs/03-analysis/aprime/<회로>.md", "엔진 코드"],
    "frozen_at": "<날짜>", "frozen_sha256": "<이 파일 본문 지문>"
  },
  "review": { "reviewer": "user", "status": "proposed|ratified|review_needed", "approval_id": "<user_decisions 항목>" },
  "groups": [
    {
      "id": "G_in",
      "devices": ["M1", "M2"],               // matching 그룹·궤도와 같은 묶음이어야 한다(아래 검사)
      "function": "1단 입력 차동쌍, GBW를 정하는 gm1",   // 자유 문장(사람용). 엔진은 읽지 않는다
      "expected_s1v_role": "input",          // 교차 확인용. 엔진 S1v AC 역할과 다르면 review_needed
      "plans": {
        "power": { "gm_id_anchor": "hi",  "L_anchor": "inverse" },
        "area":  { "gm_id_anchor": "lo",  "L_anchor": "inverse" }
      },
      "evidence": [
        { "claim": "gm/ID 큰 쪽 = 전류 최소, 작은 쪽 = W 최소", "source": "M §5.1 표",
          "pdf": "G:/내 드라이브/work/Todoc/기술문서/Gm_over_Id/(E-book) The gm_ID Methodology, a sizing tool for low-voltage analog CMOS Circuits.pdf", "page": "PDF p.115 (Fig. 6.11 문단)" }
      ]
    }
  ],
  "passives": [ { "name": "Cc", "function": "Miller 보상", "plans": {"power": "engine_rule", "area": "engine_rule"} } ]
}
```

**anchor 어휘(닫힌 목록, [제안])** -- 모두 엔진이 이미 계산하는 값의 이름이다. 새 숫자는 없다.

| 칸 | 값 | 엔진이 계산하는 값(근거) |
|---|---|---|
| `gm_id_anchor` | `hi` | 그 소자 §6 구간 [gm/ID_lo, gm/ID_hi]의 실행 가능 위쪽 끝 = 사다리 칸 0의 t*(D41:1261) |
| | `lo` | 같은 구간의 아래 끝 = 헤드룸 하한 gm/ID_lo(D41:1281). 구간이 비면 §6.6 충돌 레코드(D41:1407) 그대로 |
| | `chosen` | §6 선택점(현재 출발값과 같다 -- 그 소자는 바꾸지 않는다) |
| `L_anchor` | `inverse` | 층 0 (b) L 역산 결과(D41:750). 층 0이 꺼진 회로는 §6.4-6 선택 L(D41:1341) |
| | `knee` | §5.3.7 knee 앵커(D41:822-829) |
| | `window_lo` | `feasible_L_window` 하한(D41:831-836) |
| | `start` | §6 출발 L(D41:819) |
| passive | `engine_rule` | §6.5 보상 수동소자 규칙(D41:1360-1363). 수동소자 값은 AI가 정하지 않는다 |

- 전류는 칸이 없다. **[제안]** 전류는 선택한 gm/ID로 매크로 확정 풀이(D41:1261 칸 0과 같은 설정)와 KCL 전파(D41:1379-1382)로 엔진이 정한다.
- KVL 고리(§6.7 7a)는 소자별 anchor 선택 뒤 같은 규칙으로 다시 적용한다(D41:1255 "위반이 있으면 그 행에 묶인 소자들만 각자 구간 안(올림 포함)에서 다시 고른다"). 고리를 풀지 못하면 그 안(plan)은 §6.6 충돌 레코드와 함께 시작점 후보에서 빠진다.
- **검사(엔진, 실패하면 그 파일 전체 `review_needed`, 무동작 보고)**: (1) `topology_hash`·`spec_hash`·`vocab_hash`가 현재와 같다. (2) `devices`가 topology에 있다. (3) 한 그룹이 S1 matching 그룹·자기동형 궤도·같은 VGS 묶음을 가르지 않는다(가르면 축 하나 규칙 D41:732와 충돌). (4) `expected_s1v_role`이 S1v AC 역할과 같다. (5) anchor가 어휘 안에 있다. (6) 금지 키(`gm_id_role`·`L_role`·`headroom_role`, `structure_checks.py:975`)를 쓰지 않는다.

### 2.3 엔진 배선 위치 ([제안])

| 무엇 | 위치 | 근거·이유 |
|---|---|---|
| 파일 로드·검사 | authoring 로더 하나(`structure.json` 로더와 같은 층, `E/graph/structure_load.py` 선례 D40:597) | 회로별 데이터는 파일에, 엔진 코드는 회로 이름 없음(topology 무관) |
| S0 키 | D40:220 키에 **(iv) design_intent 파일 지문** 추가(structure.json 사실 지문 (ii)와 같은 방식). 파일이 없으면 '없음' 표지를 키에 넣는다 | D40:226 저장 시점 규칙: 키가 이미 있으면 다시 쓰지 않는다. 의도 파일이 키 밖이면 같은 키로 읽은 스냅샷의 시작점 필드가 매번 다시 계산되어 G-10 판정 2(두 번째 실행 S0 블록 computes = 0, D40 §2.4.9)를 깬다 **[추측: 구현 전이라 실측 아님]** |
| 시작점 값 | S0 수준 블록 신규 `intent_seeds` → 필드 `graph/start: intent_seeds`(plan마다 θ, 충돌 레코드, 검사 결과). 입력 버전 = (의도 파일 지문, `start.row`, `rungs`, `kvl_model`) | DEC-83 graph 단일 정본(P:282). D40:205-208 "S0 수준 값은 계산 블록으로 만들고 S0 수준 스냅샷에 쓴다". 기존 `graph/start` 행(D40:414, §2.4.8)에 칸 추가 |
| 외층 시작점 대기열 | D40 §3.6-6 출처 목록에 **'1a 의도 시작점(전력안·면적안)'**을 층 0 조립점 다음, 출발 구간 후보 앞에 넣는다. 보존 소유자 = '외층 시작점 대기열'(D40:308) 그대로 | 전역 bounds를 줄이지 않는다(D41:1036·1040, P:453). 근방 반경 규칙은 조립점에만 있으므로 의도 시작점은 일반 시작점처럼 전체 bounds에서 SLSQP |
| S3 origin | 평가 기록 origin에 `source = intent:<plan>` | D40:282 origin 칸(단계·시작점·...). 측정 귀속(§4)에 필요 |
| 결과 JSON | 시작점마다 출처·검사 결과·받아들임 여부·front 기여 수 | P:274 DEC-75 "꺼진 기능은 ... 보고서에 '비활성'" |

**층 0 후보로도 넣을지**(사용자 원문 "그것을 기준으로 층 0 값을 찾는")는 Q-AI4로 분리했다. 선례: D41:883 "고정 입력 동치류 전부에 knee + LR5 종류 앵커 합집합을 **추가 후보**로" -- 의도 anchor를 같은 방식으로 B 소자의 추가 후보로 넣을 수 있다.

### 2.4 실패·부재 시 동작 ([제안])

| 경우 | 동작 | 근거 |
|---|---|---|
| 파일 없음 | 무동작. 결과 JSON `intent_seeds: {status: "absent"}`, 다른 출처는 그대로 | WP-01 '조용히 넘어가지 않는다'(P:270 DEC-71 문언 "조용히 자명해를 내지 않는다, WP-01") |
| 지문 불일치·검사 실패 | 그 파일 전체 `review_needed`, 시작점 0, 사유 기록. 정지하지 않는다 | structure.json 선례 D40:604 |
| `review.status != ratified` | 시작점으로 쓰지 않는다(측정 실행에서만 선언으로 켬, Q-AI2) | WP-21 '사람이 ratify' |
| 한 plan이 구간 충돌·KVL 미해결·봉인 실패 | 그 plan만 빠짐, 기록 | `E/search/start_points.py:7-8` "받아들일 상태 ... 가 아닌 시작점은 목록에서 빼고 기록에 사유를 남긴다" |
| 기능 켜짐 여부 | spec `optional_stages`의 선언 불리언([제안] 이름 `intent_seeds`). 기본값은 U-33 확장 측정 뒤 결정(Q-AI6) | DEC-75(P:274) |

---

## 3. 예시 -- two_stage_ota (값은 '예시', 사용자 확인 전, 회로 해석은 공동분석 대상)

**입력 확인([사실])**
- topology: `assets/library/two_stage_ota.topology.json` netlist -- M1/M2 nmos(gate vin_n/vin_p, source CS, drain D3/O1), M3 pmos diode(D3), M4 pmos(gate D3, drain O1), M5 nmos(gate bias, D=CS), M6 pmos(gate O1, drain OUT), M7 nmos(gate bias, drain OUT), Rz(O1–N_cc_rz)·Cc(N_cc_rz–OUT) 직렬 보상, CL 3 pF(OUT–gnd).
- spec: `assets/library/two_stage_ota.sizing_spec.json` -- `gain_ss_db >= 57`, `gbw_ss_hz >= 7e6`, `offset_excess <= √2`, `noise_excess_th <= 2`, `area_search_m2 <= 1.5e-8`, PM 미정(SP-3), `wall_clock_budget_s` 300.
- 원문: Maloberti 2004 p.28 "Example 1 (2 stages OTA) ... Width only are shown; Compensation network and bias are missing (!)" -- 원문은 폭만 주고 gm/ID 근거가 없다. 경로 `assets/library/sources/two_stage_ota+folded_cascode__maloberti_2004/paper.md` p.28(브랜치 `sources-archive` `012273f`), 원본 `G:/내 드라이브/work/Todoc/논문모음/analog layout/(Bible - Euler Path) Layout of Analog CMOS Integrated Circuit Part2.pdf` p.28, 웹 재게시 slideshare.net/slideshow/layout02-1/58842369(저자 게시처 찾지 못함).
- 엔진 실측(D41:1008, 2026-10-12): O1 블록 S 축 15·B 축 18, OUT 블록 S 축 44, L 동치류 3/1.
- 그래서 이 회로의 의도는 원문이 아니라 **방법론 문헌의 기능 관례**로 쓴다(아래 근거 칸).

**방법론 근거([사실], 원문 PDF·쪽)**
- R1 효율·속도·면적 절충: gm/ID 큰 쪽 = 전류 최소·W 큼, 작은 쪽 = W 작음·전류 큼. M §5.1 표(Jespers 2010 요약). 원본 `G:/내 드라이브/work/Todoc/기술문서/Gm_over_Id/(E-book) The gm_ID Methodology, a sizing tool for low-voltage analog CMOS Circuits.pdf` PDF p.115 "the optimum lies ... in the middle of the moderate inversion region"(Fig. 6.11 문단). 웹: doi.org/10.1007/978-0-387-47101-3(Springer, 확인은 서지만 -- 링크 접속 미확인).
- R2 미러는 강반전 쪽(매칭·잡음): Cortes & Bampi PDF p.3 §3.1 "the current mirror transistors (M3-M4) are operated in strong inversion to guarantee good matching and noise properties"; 원본 `G:/내 드라이브/work/Todoc/기술문서/Gm_over_Id/(Bible) MILLER OTA DESIGN USING A DESIGN METHODOLOGY BASED ON THE GMID AND EARLY-VOLTAGE CHARACTERISTICS.pdf` p.3. 같은 쪽 "considering the GBW specification, the gm/ID ratio of the NMOS differential pair (M1-M2) can be determined". 웹 링크 찾지 못함. **논문의 숫자(gm/ID 10, 7, 10.47, AMS 0.35 µm)는 쓰지 않는다**(공정이 다르고, 논문 값 인용 금지 원칙).
- R3 약반전 mismatch 민감: Jespers PDF p.169(Annex A3, Fig. A3.4 문단) "The high mismatch sensitivity of MOS transistors in weak inversion is corroborated by a large spread"; M §7.1.
- R4 diode 미러 L 과대 금지(doublet): M §6.3 "Q3 길이는 과도 확대 금지"(Jespers 8장 요약, 원본 같은 PDF 8.3절 PDF p.140~152 -- 정확한 문단 쪽은 미확인).
- R5 이득 → L 역산: Cortes & Bampi PDF p.3 §3.2 "considering the gm/ID vs. VA curve, now the correspondent L can be found"; M §6.7. 엔진 (b) 역산(D41:750)과 같은 원리라 `inverse`로 둔다.
- R6 Miller 2D 사이징 공간(전력·면적이 attribute): Jespers 8.3절 PDF p.142 "Sizing is performed now in a 2D sizing space, one axis per stage", PDF p.132 "Specifications determine the dimensions ... attributes delineate optimization areas"; M §6.4.

**예시 선언(요약표, 값은 anchor 이름뿐)**

| 그룹 | 소자 | 기능(AI 해석) | 기대 S1v 역할 | 전력안 gm/ID / L | 면적안 gm/ID / L | 근거 |
|---|---|---|---|---|---|---|
| G_in | M1, M2 | 1단 입력 차동쌍, gm1이 GBW·Cc로 정해짐 | `input` | `hi` / `inverse` | `lo` / `inverse` | R1, R2(입력쌍은 GBW로), R5 |
| G_mir | M3, M4 | 1단 능동 부하 미러(M3 diode) -- offset·잡음 가드 대상 부하 | `diode_load`, `mirror`/`load` | `lo` / `knee` | `lo` / `window_lo` | R2, R3, R4. 전류는 KCL이 정하므로 gm/ID `lo`는 전력 중립이고 W·면적을 줄임(R1) [추측: 2a 가드 상한(D41:1325)과 같은 방향이라 충돌 없을 것] |
| G_tail | M5 | 1단 꼬리 전류원(gate = 외부 bias) | `tail_source` | `lo` / `knee` | `lo` / `window_lo` | R2·R3(전류원 매칭). M5·M7은 매칭 의도 없음(topology `symmetry.dispositions` "M5/M7 ... 매칭이 아니다") → 그룹을 묶지 않는다 |
| G_cs2 | M6 | 2단 공통소스, gm2(비주극점·RHP 영점) | `input`(2번째 블록) | `hi` / `inverse` | `lo` / `inverse` | R1, R6 |
| G_ld2 | M7 | 2단 전류원 부하, ro가 2단 이득에 직접 들어감 | `load`/`tail_source` | `lo` / `inverse` | `lo` / `window_lo` | M §13.7 교훈("비캐스코드 단순 전류원 → ro 자체"): 이득에 들어가므로 전력안은 역산에 맡김 |
| passive | Cc, Rz | Miller 보상·RHP 영점 이동 | -- | `engine_rule` | `engine_rule` | D41:1360-1363. PM 미정(SP-3)이라 매크로는 `pm_floor_pole_at_ugf` 경로(D41:1394) |

- 이 예시는 **소자마다 다른 방향**(입력 `hi`, 부하·꼬리 `lo`)을 주는 점에서만 §6 사다리(모든 소자 같은 t)와 다르다. S 소자(M1/M2, M6)의 `hi`는 사다리 칸 0과 같은 값이다. → 전력안의 새 정보는 B 소자 3그룹의 `lo`·`knee`뿐이다. 측정에서 이 차이가 front에 기여하는지가 판정 대상이다.
- **AI 해석 오류 가능 지점**(공동분석): M4가 미러 출력이자 1단 출력노드 부하라 'ratio 매칭'과 '이득 부하' 중 어느 기능이 우선인지(M §13.3 "current mirror 다리가 ratio-matching인지 gain-stage load인지 -- 5개 구조 신호"). 예시는 매칭 우선으로 적었다.

---

## 4. 측정 계획 -- U-33 확장

### 4.1 비교군 (같은 spec·같은 `wall_clock_budget_s`·같은 E_B 식, 회로마다)

| 군 | 시작점 출처 | 비고 |
|---|---|---|
| P0 | §6 출발 사다리만(층 0 끔) | U-33 (i) '콜드 스타트'를 사다리 기준으로. **[제안]** 이 군을 넣는 이유: 의도 시작점의 B 소자 방향이 사다리의 공통 t와 얼마나 다른지 분리하려고 |
| P1 | 층 0 조립점 → §6 후보 → S3 → x0 (D40:792-797 그대로) | U-33 (ii) |
| P2 | 의도 시작점(전력안·면적안) → §6 후보 → S3 → x0 | 층 0 끔 |
| P3 | 층 0 조립점 → 의도 시작점 → §6 후보 → S3 → x0 | 제안 배선 |

- **[제안]** 모든 군은 **빈 S3 폴더**로 돌린다(시작점 출처 ③ S3 이전 front 점이 군 사이에 섞이지 않게 -- `E/search/start_points.py:5` ②가 같은 S0·스키마·코드 지문이면 이전 실행 front를 시작점으로 읽는다). S0 스냅샷 폴더는 공유해도 된다(시작점 필드만 다름 -- 의도 파일 지문이 S0 키에 들어가므로 P2·P3과 P0·P1은 다른 스냅샷 키).
- `OPENBLAS_NUM_THREADS=1`(D40:1679 NFR-4 결정론 원인 수정이 ② 착수 조건으로 남아 있다 -- 수정 전이면 고정 필요).
- 정밀 경로는 측정 대상이 아니다(D40:1050 "U-66 (가): 미구현 정지").

### 4.2 지표

| 지표 | 정의 | 출처 |
|---|---|---|
| (a) front 질 -- 지배 포함 | 군 X의 front가 군 Y를 **약지배 포함**: Y의 모든 front 점 y에 대해 X의 어떤 점 x가 두 축에서 x ≤ y + 허용 폭. 허용 폭 = 전력 max(b_P, 전력 모델 오차), 면적 = 면적 축 bin 폭 max(레이아웃 격자 분해능, 면적 모델 오차) | DEC-71 (6) 같은 점 접기 규칙(P:270), DEC-80(P:279), D40 §3.6-5 ε 간격. 새 상수 없음 |
| (b) front 질 -- hypervolume | 회로마다 네 군 front 점 합집합(봉인 통과·c ≥ 0)의 축별 최댓값에 각 축 허용 폭 한 칸을 더한 점을 기준점 r로 두고, 군별 (전력, 면적) 지배 면적 HV_X. 보고는 HV_X / HV_합집합. 면적 예산이 선언된 회로(`area_search_m2`)는 r_면적 = 예산 값([제안]: 선언값이 있으면 선언값, 없으면 합집합 최댓값 + 한 칸) | 저장소에 hypervolume 정의 없음(`grep hypervolume` 0건) -- **이 문서가 새로 정의하는 지표**. 기준점은 측정 데이터·선언값·기존 분해능에서만 유도 |
| (c) 평가 수 | 층 0 몫·의도 시작점 생성(커널 0이면 0)·외층 포함 전체 커널 호출 수, 그리고 **첫 받아들일 시작점까지 평가 수** | U-33 (i)(P:1250) |
| (d) 시간 | wall-clock 전체, 첫 front 점까지 | U-33 (iv) |
| (e) 출처 귀속 | 출처별 받아들인 시작점 수, 최종 front 점의 출처(`sweep_front` `roots`, D41:1038) | §2.3 S3 origin |
| (f) 활성 제약 여유 | 제약마다 활성/비활성·여유(D40 §3.10.6) | U-33 (iii) |
| (g) A' 연결 | 시작점의 ngspice T4-pre 통과 여부(출처별) | D40:1604·1624. 의도 시작점 통과는 **따로 기록**하고 ② 완료 판정에 넣지 않는다(Q-AI5) |

### 4.3 회로 집합

- library 9회로(회귀 지표, D40:1626 "9회로 도달률 ... 회귀 지표로만") + held-out 4회로 `assets/heldout/{rfc_ota, erfc_ota, r2r_opamp, cnr_ota}`(일반성 근거, P:297 DEC-98 (4)).
- **[사실]** 2026-10-12 시점 단계 A·B를 넘지 못한 회로: current_reuse 정지, ngcc·nmcnr `review_needed`(D41:1013). 그 뒤 spec 변경(PKG Q1-2 nmcnr·ngcc gain 제약 선언)이 있어 ② 시점 상태는 다시 재야 한다. 층 0이 돌지 않는 회로는 P1 = P0이고 P3 = P2 + 사다리이므로 의도 시작점의 효과가 가장 잘 드러난다 **[추측]**.

### 4.4 판정 규칙 ([제안], 새 상수 없음)

1. **기본 경로로 승격(의도 시작점 기본 켬)**: held-out 4회로 **전부**에서 P3가 P1을 (a) 약지배 포함하고, held-out 중 **한 회로 이상**에서 P1을 넘는 개선(P1 front에 없는 비지배 점이 허용 폭 밖에 생김, 또는 P1 front 0 → P3 front ≥ 1). 같은 예산이라 평가 수 증가 허용치는 따로 두지 않는다(예산 식이 상한).
2. **선언 선택지로 유지(기본 끔)**: held-out 어느 회로에서도 P3가 P1보다 나쁘지 않지만 개선이 없을 때. WP-01 관점: 만든 기능이 기본 경로에 안 쓰이게 되므로 **사용자 승인 필요**(Q-AI6).
3. **폐기**: held-out 한 회로에서라도 P3가 P1을 약지배 포함하지 못할 때(의도 시작점이 예산을 빼앗아 front를 잃음). 코드는 같은 변경에서 삭제(WP-01, 사용자 승인).
4. **대체 질문으로 올림**: P2가 held-out 전부에서 P1을 약지배 포함하고 평가 수가 적으면 사용자에게 '층 0 대체' 여부를 묻는다(오케스트레이터 의견은 추가이고, 대체는 DEC-73·U-33 문언 변경이라 사용자 결정).
5. library 9회로 결과는 회귀 표로만 낸다. held-out 실패를 고치려고 의도 파일이나 엔진을 바꾸면 그 회로는 개발 회로로 옮긴다(D40:1627 U-76 (5)와 같은 규칙).

### 4.5 비용 추정

- 실행: 13회로 × 4군 × `wall_clock_budget_s` 300 s(13개 spec 전부 300, 확인) = 상한 15,600 s ≈ 4.3 시간(직렬, 스레드 1). 예산을 다 쓰지 않는 회로는 더 짧다. 결정론이라 회차 반복은 필요 없다.
- AI 작성: 13회로 × (기능 해석 1 + 두 안) 파일, 사용자 확인 13건(held-out 4건은 엔진 실행 전 동결).
- 코드: 로더·검사, S0 키 항목, `intent_seeds` 블록(§6 사다리·7a·매크로 재사용 -- 새 풀이기 없음), 시작점 출처 한 칸, `tools/compare_paths.py`(U-33에 원래 필요, 이 측정 전용 아님).
- ngspice: 출처별 시작점 T4-pre(②의 A' 실행에 얹음).
- **선행 조건**: ②의 층 0 재구현(P1 정의에 필요)과 compare_paths.py. 둘 다 없으면 이 측정은 P0 대 P2만 가능하다.

---

## 5. 결정 질문 (② design 착수 전)

### Q-AI1 대체인가 추가인가
- (가) **추가 시작점 출처**(층 0·§6 사다리 유지, 의도 시작점은 대기열 한 칸) (나) 층 0 seed 대체 (다) §6 출발값 대체
- **기본안 (가)**. 근거: DEC-71 (4) "역산은 후보를 만드는 수단이고 격자를 대체하지 않는다"(P:270)와 같은 원칙, 층 0은 전역 bounds를 줄이지 않는다(D41:1040), IC4(P:894)·M §13.7 기능 라벨 실패 기록, 오케스트레이터 의견·사용자 동의(2026-10-14). 대체는 §4.4-4 측정 결과가 있을 때 별도 결정.

### Q-AI2 선언 파일에 무엇을 쓰나
- (가) **해석만**(기능 문장 + anchor 이름, 숫자는 엔진 계산) (나) AI가 gm/ID·L·ID 숫자(LUT 조회 근거 포함)까지 기입 (다) (가) + 선택적으로 숫자 칸 허용
- **기본안 (가)**. 근거: WP-21(P:325) '다음 단계의 입력'은 코드, '회로 해석'은 AI 제안·사람 ratify; WP-03(P:307) 새 상수 금지 -- anchor는 엔진이 계산하는 값의 이름이라 근거가 바뀌면 따라간다; (나)는 A' 손분석과 같은 작업이 되어 Q-AI3 문제가 커진다.

### Q-AI3 작성·확인 절차와 A' 독립성
- (가) **작성 주체 = A' 손분석·엔진 코드와 다른 AI 세션**, 입력은 topology·spec·원문·방법론 문서만, A' 문서·엔진 출력·엔진 코드를 보지 않음(`authoring.inputs_not_seen`에 기록). 사용자는 기능 해석을 확인(ratify)하고 `approval_id`를 남김 (나) A' 손분석 작성자가 같이 작성 (다) 사용자 확인 없이 AI 작성본 그대로 사용
- **기본안 (가)**. 근거: DEC-98 (2)(P:297) 손분석 결과를 엔진 입력으로 쓰지 않음 -- 같은 작성자가 쓰면 손분석 결론이 의도 파일로 새어 들어가 A' 대조군이 엔진 입력에 섞인다; WP-13(P:317); WP-21 '사람이 ratify'; structure.json 선례(`approval_id`). 기능 해석은 회로 해석이라 공동분석 대상(메모리 원칙 '회로위상 해석은 항상 공동분석').

### Q-AI4 엔진 어디로 들어가나
- (가) **외층 시작점 대기열만**(층 0 조립점 다음 칸) (나) 층 0 후보 집합에도(§5.3.10 knee 앵커처럼 B 소자의 추가 후보) (다) 둘 다
- **기본안 (가) 먼저, (나)는 측정 뒤**. 근거: (가)는 출처 귀속(§4.2 (e))이 깨끗해 U-33 판정이 가능하다; (나)는 사용자 원문("그것을 기준으로 층 0 값을 찾는")에 더 가깝고 선례(D41:883 R29 추가 후보)도 있으나 층 0 후보 수 n_i(D41:977)를 늘려 절단·'추정'(D41:893) 위험이 있다. (가)에서 B 소자 방향이 front에 기여하면 (나)를 별도 card로 묻는다.

### Q-AI5 held-out 적용과 A' 완료 판정
- (가) **held-out 4회로도 의도 파일을 쓰되, 엔진 실행 전 AI 단독 작성 → 사용자는 사실 오류(소자 이름·연결)만 확인, 기능 해석 수정 없이 동결(`frozen_sha256`)**. 엔진 결과를 본 뒤 고치면 그 회로는 개발 회로로 이동. ② 완료(A')는 기존대로 층 0·출발 구간 시작점으로 판정하고 의도 시작점 통과는 별도 기록 (나) held-out에는 의도 파일을 쓰지 않음(측정은 library만) (다) 의도 시작점도 A' '엔진 시작점'으로 인정
- **기본안 (가)**. 근거: DEC-98 (4)·U-75(P:1292) held-out = "엔진 개발(코드·test 픽스처·`structure.json` 사실·spec 값 조정·발동표 측정)에 쓰지 않은 회로" -- 결과를 보고 고친 의도 파일은 개발 데이터가 된다(U-76 (5), D40:1627과 같은 논리); (나)는 일반성 근거가 없어진다(D40:1626 "일반성의 근거는 held-out 회로"); (다)는 완료 기준 변경이라 사용자 승인 사안(N6.3 `criteria_weakened`, P U-76 (1) 근거 문장) -- 기본안에서 바꾸지 않는다. 사용자 확인을 '사실 오류만'으로 좁히는 이유: 사람이 해석을 고치면 held-out 비교가 'AI 해석'이 아니라 '사람 해석' 측정이 된다.

### Q-AI6 측정 판정 기준
- (가) **§4.4 규칙**(held-out 전부 약지배 포함 + 1회로 이상 개선 → 기본 켬 / 개선 없음 → 선언 선택지(사용자 승인) / 악화 → 폐기) (나) U-33 원문 그대로(평가 수 감소 + 목적값·여유가 허용 폭 안) (다) hypervolume 비율만
- **기본안 (가)**. 근거: 같은 예산(DEC-34 식) 아래 비교라 '평가 수 감소'보다 front 질이 직접 지표; 허용 폭은 기존 분해능·모델 오차(DEC-71 (6)·DEC-80)라 새 상수가 없다; hypervolume은 저장소에 정의가 없어 보조 지표로만 둔다. 기본 끔으로 남는 경우는 WP-01(P:305) 때문에 사용자 승인 사안으로 명시.

### Q-AI7 ② 일정과의 관계
- (가) **② design에는 자리만 정한다**(S0 키 항목 (iv)·`graph/start: intent_seeds` 필드 행·대기열 출처 1a·보존 소유자) -- 구현은 ② 층 0 재구현과 `compare_paths.py`가 들어온 뒤 **별도 card**(U-33 측정 card와 묶음) (나) ②와 함께 구현 (다) ② 완료 뒤 따로 design부터
- **기본안 (가)**. 근거: P1 비교군이 ② 층 0을 필요로 한다(§0-3); ② 범위는 이미 '전체 재작성' 규모(D40:1679); 측정 전에 구현해 두면 '만들고 안 쓰는' 위험(WP-01) -- 자리만 design에 두고 구현·측정을 한 card로 묶으면 그 위험이 없다. 단 ②가 held-out에서 시작점 실패로 막히면(PKG §0.3 패턴) 이 card를 앞당길지 다시 묻는다.

### Q-AI8 IC4·S0 키 정합 (기술 결정, 기본안 확인만)
- (가) **의도 파일은 topology 밖 별도 파일, 구조 유도·봉인·제약·bounds는 읽지 않고 `intent_seeds` 블록 하나만 읽는다(G-8 위치 검사로 고정), 지문은 S0 키 (iv)** (나) spec `human`에 칸 추가(`intended_region` 선례, `E/authoring/SPEC_CONTRACT.md:94` 어휘 = triode만)
- **기본안 (가)**. 근거: IC4 lint(`structure_checks.py:975-980`)는 topology 태그 조회를 금지한다 -- 의도 정보가 topology에 들어가면 lint 위반; spec은 사용자 선언 값(출처 필수)이고 의도는 AI 해석·ratify라 structure.json과 같은 부류(WP-21 둘째); S0 키에 없으면 저장 규칙(D40:226)상 매 실행 재계산 **[추측: 구현 전]**. IC4 문언 "제거해도 결과 동일"은 topology 라벨 대상이라 별도 파일은 해당하지 않지만, 의도 파일이 있으면 시작점이 달라 결과가 달라질 수 있다는 사실을 IC4 표 비고로 적을지는 사용자 확인.

---

## 6. 원칙 충돌 점검 요약

| 원칙 | 충돌 여부 | 처리 |
|---|---|---|
| 임의 상수 금지(WP-03) | anchor 어휘는 엔진 계산값의 이름이라 숫자 없음. 측정 허용 폭·기준점도 기존 분해능·선언값·측정 데이터에서 유도 | Q-AI2 (가), §4.2 |
| topology 무관 코드 | 회로 이름은 선언 파일에만, 엔진 코드는 anchor 어휘만 안다 | §2.3 |
| 결정성 NFR-4(P:188) | AI 출력은 비결정적이지만 파일로 동결되면 그 뒤는 결정론. 파일 지문이 S0 키에 들어감 | §2.3, Q-AI8 |
| graph 단일 정본(DEC-83) | 선언 파일 = S0 입력, 계산된 θ = `graph/start: intent_seeds` 필드(writer 하나), sctx 사본 없음 | §2.3 |
| 회로 해석 공동 결정 | 기능 해석은 AI 제안 → 사용자 ratify, held-out은 사실 확인만 + 동결 | Q-AI3·Q-AI5 |
| held-out 공정성 DEC-98 (4) | 엔진 실행 전 동결, 결과 보고 수정 시 개발 회로 이동 | Q-AI5 |
| A' 독립성 DEC-98 (2) | 작성 주체 분리, A' 문서 미열람 기록 | Q-AI3 |
| IC4 라벨 과신 | 판정·bounds·구조에 안 들어감, 시작점만, 금지 키 미사용 | Q-AI8, §0-5 |
| 만들면 배선(WP-01) | 자리만 design, 구현은 측정과 한 card, 기본 끔 결과면 사용자 승인 | Q-AI6·Q-AI7 |
| 전역 bounds 불축소(P:453, D41:1040) | 의도 시작점은 대기열 한 칸, bounds 무변경 | §2.3 |
| 논문 값 인용 금지 | Cortes & Bampi gm/ID 10·7 등 숫자 미사용, 기능 방향만 인용 | §3 |
