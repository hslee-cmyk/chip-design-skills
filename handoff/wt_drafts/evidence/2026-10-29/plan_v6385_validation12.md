# 계획 v6.38.5 열여섯째 커밋 독립 검증 12 (2026-10-29)

- 대상: worktree `wt/plan-v6385`, 커밋 `74e62d53`(`git diff adb3686a 74e62d53` -- plan 10줄 교체(11·304·1166·1217·1231·2192·2195·2348·2350·2352), history 11줄: H1 1548 경위 1행, 1945 «원문» 정정 1행, «원문» 1948~1956 9행).
- 검증자: 독립(작성자 아님). 문서 수정 0. git은 `git -C`로 읽기만(reset·checkout·stash·commit 0).
- 엔진: `wt/integ-it12`(`b3336452`) 읽기만. python `C:\Python314\python.exe`.
- 기준: O-173(손계산 우선, E-0·E-1·E-2; SPICE 수치 동일성은 지적 기준 아님), graph 단일 정본 1~7(규칙 3 정의 축), O-165 (as-built는 재작성 범위로만 인용), O-169, 만들면 배선, 상수 발명 금지, 회로 이름 0, fail-closed, 원래 취지와 다름 표지.
- 측정 자리: `wt/_drafts/evidence/2026-10-29/plan_v6385_validation12/`

| 파일 | 내용 |
|---|---|
| `plan_<c>.md`·`hist_<c>.md` (c = adb3686a·74e62d53, plan_07964dfe) | 원본 |
| `segdiff.py` → `segdiff_{plan,hist}_adb3686a_74e62d53.txt` | 문장 단위 diff |
| `hist_check.py` → `hist_check.txt` | «원문» 10행이 옛 판 원문 그대로인지(부분 문자열 검사) |
| `residual.txt`·`stale_grep.txt` | 옛 문언 잔존·«원문» 누락 |
| `ctx_lines.txt`·`status_n53.txt`·`grep_search_domain.txt`·`grep_s0.txt` | 본문·Status·N5.3·S0 용어 |
| `refcheck.py` → `refcheck.txt` | 판 전체(07964dfe..74e62d53) 바뀐 52줄의 경로 인용 122개 존재 |

## 판정

**승인 상정 가능.** Critical 0, Major 0, Minor 6(차단 아님 -- 문언 정정, 같은 판 다음 커밋 권고).

- MJ11-1은 실질 해소됐다. 적용 상자 writer가 `search_domain` 자리 하나로 이름이 박혔고, 층·정의 축·소비자 목록·사본 칸 처분·완료 조건이 들어갔다. 엔진 전수 grep에서 둘째 생산자·빠진 소비자 0이다.
- m11-1~m11-5도 반영됐다. 남은 결함은 새 문언의 세부(검사 자리·toy base 서술·줄 인용)와 «원문» 1건이다.

## 1. 검사 1 -- 지적 해소·보존·정합

### 1.1 검증 11 지적

| 지적 | 해소 | 자리 |
|---|---|---|
| MJ11-1 writer 정본 자리 | 해소. '적용 상자 writer = 검색 정의역 S0 블록 하나(as-built `search_domain` -- 재작성 범위로만 인용, O-165)' | 1166 (2), 2195, 1217, 1231, 2348, 2352, 304, 11 |
| MJ11-1 층 | 해소. '층 = `graph.dc_current_basis`·`theta_schema` 뒤'(1166·2195·304) | 같음 |
| MJ11-1 정의 축(규칙 3) | 해소. '선언 상자'(6 (e), spec 추출, S1 앞) 대 '적용 상자'(공통 상자·결합 C 판별·미선언 정지 적용) 두 필드로 나누고 축을 적음. 2192 '같은 필드 writer 본문' → '그 블록 본문이 바뀐다'로 고침 | 1166, 2192 |
| MJ11-1 소비자 | 해소. `iv_context.py:94`(사본 칸 `start_values.py:180` 삭제)·`iv_area.py:85`·`_helpers_area.py:24`·`macro_poles.py:133,141`·`achievability.py:126,248`, `search_context.py:164` = writer 입력(6 (e) 몫) | 1166, 2195 |
| MJ11-1 완료 조건·대안 | 해소. writer 1곳·사본 칸 0·spec 직접 읽기 0·`iv_area` toy. 대안 3개 ⚠ | 1166, 2195 |
| m11-1 «원문» | 해소. 1955·1956 소급 2행, 1945 `129-133` 원문 그대로 | H 1945, 1955, 1956 |
| m11-2 DR-1 결합 C toy | 해소(세 경우) -- 단 base 서술 → m12-6 | 2350 (10) |
| m11-3 U-132 선례 | 해소 | 1166 |
| m11-4 `iv_context.py:94` | 해소 | 1166, 2195 |
| m11-5 `theta_bound_element` 행방 | 해소(검색 정의역 블록 안 거부) -- 단 자리 → m12-1 | 1166, 2195 |

### 1.2 history «원문»(`hist_check.txt`)

- 10행 모두 옛 판 원문의 부분 문자열이다(원문 그대로 10/10).
  - 1945: 6a31bf1c 원문 그대로. `129-133`으로 정정됨.
  - 1948~1954: adb3686a 원문 그대로. 1950 '4곳' = adb3686a의 `SF-1 범위 9의 S0 θ 상자 블록` 4회(1166·1231·2348·2352)와 일치.
  - 1955·1956: 6a31bf1c 원문 그대로.
- **누락 1건** → m12-4. 1217 옛 조각 «범위 9 상자 적용 자리 = S0 θ 상자 블록·소비자 4곳 재배선»의 «원문» 행이 없다(`residual.txt`: history에 그 문자열 False). 1950은 정확한 문자열 `SF-1 범위 9의 S0 θ 상자 블록` 4곳만 덮는다.
- H1 1548 경위 행은 MJ11-1 각 항목과 m11-1~5 반영을 빠짐없이 적었다.

### 1.3 Status·N5.3(7행)

- N5.3 v6.38.5 행 = Q-W1 1161·Q-CF1 1162·Q-ZG1 1163·Q-CA1 1164·Q-KV1 1165·Q-CB1 1166·Q-CB2 1167, 7행이다.
- Status 열린 결정 목록이 이와 1:1이다. Q-CB1 칸이 '적용 상자 writer = 검색 정의역 S0 블록(`search_domain` 자리, SF-1 범위 9 -- 로더 → S0 블록)'으로 본문과 같다.
- Status 원래 취지와 다름 Q-CB1 = '10번'·N13·DEC-105 (10)(a)·적용 자리 로더 → S0 블록·SF-1 → DR-1 순서. 본문 표지(304·1166·2195)와 1:1이다.
- 옛 문언 grep(`stale_grep.txt`): 'S0 θ 상자'·'소비자 4곳'·'상자 소비자'·'상자 적용 자리'·`iv_context.py:32`·'2533 선례'·`129-133`·'같은 필드의 writer 본문' 모두 0이다.

## 2. 검사 2 -- MJ11-1 독립 재판정

### (a) 정의 축(graph 규칙 3) -- 맞음

- 선언 상자 = spec 선언 추출이다(입력 spec, 6 (e) S0 필드, S1 앞).
- 적용 상자 = 원소별 탐색 상자다(선언·공통 상자·결합 C 판별·미선언 정지를 합친 양). as-built로는 `graph/kernel: search_domain`의 `variables` 칸이다.
- 다른 축('적용 규칙을 거쳤는가')이 적혀 있고, 적용 상자는 새 필드가 아니라 기존 필드(`domain.variables`)다. 규칙 3에 맞다.

### (b) 적용 상자 writer 하나 -- 맞음(엔진 전수 grep)

`theta_bounds`·`THETA_BOUNDS`·`_FIELD_BOUNDS`·`capacitance_bounds_f`·`resistance_bounds_ohm`·`.box`·`s.field ==`를 엔진(테스트 제외)에서 전수 grep했다.

| 자리 | 역할 | 계획 처분 |
|---|---|---|
| `search/search_domain.py` `_passive_box`(정의 70-75)·미선언 정지(106-116)·Variable(130-134) | 적용 상자 writer(`S0_WRITERS` 표 소속, `search/s0_fields.py:20·27`) | writer 하나로 지정 |
| `search/search_values.py` `SearchSettings.{resistance,capacitance}_bounds_*` | 실행 설정 재정의(writer 입력) | 범위 9 본문 '실행 설정의 수동소자 상자 재정의는 지운다' |
| `pipeline/stage_b.py:155`·`search/search_context.py:165` | 선언 추출(writer 입력, `search_domain` 호출 두 자리 = 같은 writer) | 6 (e)가 지움 |
| `search/iv_context.py:94`(+ 사본 칸 `start_values.py:180`) | spec 직접 읽기 → 사본 | 범위 9 삭제 |
| `search/iv_area.py:85`·`_helpers_area.py:24`·`macro_poles.py:133,141` | 사본(또는 폴백) 읽기 | 범위 9 재배선 |
| `metrics/achievability.py:126,248` | spec 직접 읽기(저항 상자·커패시터 면적) | 범위 9 재배선 |
| `authoring/spec_theta_bounds.py` | 로더 교차 검사·kind 부착 | 블록 안 거부로(→ m12-1) |

- spec_theta_bounds·iv_context·start_values·search_context 가운데 상자를 **적용**(공통 상자·정지)하는 자리는 `search_domain` 밖에 없다. 둘째 생산자 0이다.
- 소비자 재배선 목록은 엔진 소비자 전수와 일치한다(빠짐 0). `achievability`는 이미 `("graph","search_domain")`을 READS한다(`achievability.py:334·342`). 그래서 재배선에 새 READS가 필요 없고, 층(`stage_b.py:169`, `search_domain` 뒤)도 맞다.
- 관찰(지적 아님): `iv_context.py:106` `StartView.box`는 `domain.variables`를 자연 좌표로 바꾼 투영 칸이다. 계획은 이것을 적용 상자 READS 경로로 쓴다. G2 접근자 여부는 기존 StartView 구조 문제라 이번 개정 범위 밖이다.

### (c) 사본 칸 삭제·READS -- 맞음

- `StartView.theta_bounds`(`start_values.py:180`)를 삭제하고, 읽는 쪽은 적용 상자를 READS한다. graph 규칙 2·4에 맞다.

### (d) 완료 조건 측정 가능성 -- 대체로 가능, 2건 보완

- writer 1곳: `@compute_block` writer grep + `_passive_box` 꼴 함수 grep으로 잴 수 있다.
- 사본 칸 0: `StartView` 정의 grep으로 잴 수 있다.
- spec 직접 읽기 0(`git grep`): 엔진의 같은 칸 읽기가 세 철자다(공개 상수 `THETA_BOUNDS`, 지역 상수 `_FIELD_BOUNDS = "theta_bounds"`, 문자열 그대로 `"theta_bounds"` -- `achievability.py:126,248`). 6 (e) 완료 조건의 `git grep THETA_BOUNDS`만으로는 achievability를 못 잡는다 → m12-5.
- `iv_area` toy: base 서술 '그 커패시터 빠짐'이 엔진과 다르다 → m12-2.

### (e) `theta_bound_element` 거부 위치 -- G1과 어긋남(m12-1)

- 이 검사는 '선언 상자'의 유효성 검사다(원소가 topology 수동소자, kind ∈ {R, C}, mode `engine`). 적용 규칙과 무관하다.
- 계획 G1(531)은 계산값을 읽는 검사를 '**그 값의 writer 블록 안 거부**(첫 소비자 앞, 층 순서상 가장 이른 자리)'로 정한다. 그 값 = 선언 상자이므로 자리는 6 (e) 선언 상자 S0 블록(S1 앞)이다. 적용 상자 writer(`search_domain`)가 아니다.
- 지금 안(검색 정의역 블록 안)도 fail-closed는 지킨다. 선언 상자의 소비자가 범위 9 뒤 `search_domain` 하나라서 검증 안 된 값을 읽는 소비자는 0이다.
- 그러나 실패 시점이 로더(`A1_load`, gate `theta_bounds`)에서 단계 B·탐색 문맥(`search_domain` gate)으로 옮겨진다. 단계 A는 `search_domain`을 부르지 않는다(`stage_a.py` 205-235 -- 호출 없음). 그래서 잘못된 선언이 있어도 단계 A가 'ok'로 끝난다.
- 이 변경이 동작 변경·원래 취지와 다름 표지에 없다. G1 꼴(로더 → 단계 A의 그 블록)과도 다르다. 영향받는 자리: `authoring/SPEC_CONTRACT.md:151`, `tests/authoring/test_spec_theta_bounds.py:185·192`(gate `theta_bounds` 기대).

### (f) 층 순서·순환 -- 0

- 선언 상자(S0, S1 앞) → `search_domain`(`dc_current_basis`·`theta_schema` 뒤, `kernel_context.py:84-90` → `search_context.py:173`/`stage_b.py:158`) → `achievability`(`stage_b.py:169`)·StartView 소비자 순서다. 역방향 READS는 0이다.
- DR-1 결합 C 갈래가 READS하는 `graph.dc_current_basis`는 이미 `search_domain` READS에 있다(as-built 85-86). 층 역전이 없다.
- 판별 술어('C 한 끝 넷에 닿는 소자')는 소자 단자 연결 READS를 더해야 한다(지금 READS에는 `device.pins` 없음). S1 이전 필드라 층 문제는 없고, design 몫이다(관찰).
- 카드 순서 SF-1 → DR-1 순환 0(검증 11 (d) 그대로, 변경 없음).

### (g) 대안 ⚠ 비교 -- 정확

- 새 S0 블록 ⚠ `_passive_box`·미선언 정지가 둘째 생산자로 남음: 맞다(지우면 같은 결론이고, 지우는 범위가 따로 생긴다).
- 6 (e) S1 앞 블록 ⚠ `dc_current_basis` READS 층 역전: 맞다.
- '결합 C만 S0, 나머지 로더' ⚠ 소자 집합 분할·로더 판별 불가: 맞다.

### (h) DR-1 완료 (10) toy 세 경우 -- 들어감, base 서술 보완(m12-6)

- 미선언 결합 C → 정지, 선언 결합 C → 선언 상자, 0 전류 MOS 없는 θ 커패시터 → 공통 상자. 경우는 셋 다 맞다.
- base 서술 '공통 상자 적용 -- red'는 블록 수준 toy(빈 항 행을 가진 `dc_current_basis`를 합성)에서만 성립한다. 파이프라인 수준 toy에서 base(SF-1 병합 뒤, DR-1 전)는 `current_basis.py:130-133` `mos_zero_current_structural`에서 먼저 정지한다. `search_domain`에 닿지 않는다.
- 둘째·셋째 경우는 base에서도 같은 결과라 회귀 보호(red 아님)다. 표지가 없다.

## 3. 검사 3 -- 판 전체(07964dfe..74e62d53) 최종 표본

- 경로 인용: 판 전체에서 바뀐 plan 52줄의 `wt/_drafts/...`·엔진 경로 122개가 모두 존재한다(MISS 0, `refcheck.txt`).
- 옛 문언: `stale_grep.txt` 남은 hit는 모두 다른 맥락이다. '같은 통합 병합으로만 master' 368(O-149)·2189(DE-1 범위 3), 'f_low 칸' 1163·2348(철회 문장), 'f_low 선언 자리' 2352(철회 문장).
- **끊긴 줄 인용**(as-built, 이번 커밋 새 인용) → m12-3:
  - `search_domain.py:76-80` = 빈 줄 + `_budget_i_max`. `_passive_box`는 70-75다.
  - `:89-90` = 데코레이터·def. READS 튜플(`dc_current_basis`·`theta_schema`)은 85-86이다.
  - `106-112`는 저항 정지 + 커패시터 누락 계산까지다. 커패시터 정지 raise는 113-116이다.
  - 이 줄 번호는 검증 11 표(검증자 기인)를 옮긴 것이다.
- 겹침: 6 (e)는 `iv_context.py:93`을 '선언 상자 READS로 재배선'할 둘째 생산자로 둔다. 범위 9(승인 시)는 같은 자리를 적용 상자 READS + 사본 삭제로 바꾼다. 승인 시 6 (e) 재배선 대상에서 빠진다는 조건 문언이 없다(같은 card 안 '넣었다가 옮김' 위험, O-153) → m12-5.

### 질문 표(6 + Q-CB2)

| 질문 | 권고 | 대안·⚠ | 시점 | 판정 |
|---|---|---|---|---|
| Q-W1 | 이번 판은 표지·되돌릴 목록뿐 | (가)·순서 (i) 되돌릴 목록 | WB-1 착수 실측 → 결정 → 일괄 반영 | 상정 가능(변경 없음) |
| Q-CF1 | 안 A | B ⚠ IT-2c 재개정 | WB-1 범위 3a 착수 전 | 상정 가능 |
| Q-CA1 | (가) 삭제 | (나)(다) ⚠ | SF-1 spec data 커밋 전 또는 metric 등록 card 착수 전 | 상정 가능 |
| Q-ZG1 | (나) W_min·L_min, writer 하나, (i) fail-closed 기록 유지 | (가)~(마)·(i)~(iii) ⚠ | DR-1 design 착수 전 | 상정 가능 |
| Q-KV1 | (다) + (A) | (가)(나)(라)·(B)(C) ⚠ | TB-1 design 착수 전, E-0·I_Q 실측 뒤 | 상정 가능 |
| Q-CB1 | (나) 역할별 분리 + (α) + (Q) DR-1 이관, 적용 상자 writer = `search_domain` 자리 | (가)(다)(라)(마)(바)·(β)·(P)·새 블록·S1 앞 블록·로더 분할 ⚠ -- 정확 | SF-1 design(범위 9) 착수 전 | **상정 가능**(m12-1·2·5·6은 design 전 문언 정정 권고) |
| Q-CB2 | 결정하지 않음(열린 질문) | 후보 2개, ⚠ 관례를 정의로 | LA-1·ME-1 변화표 뒤 | 상정 대상 아님(기록 맞음) |

## 4. 지적

Critical 0, Major 0.

### Minor

- **m12-1** `theta_bound_element` 자리(1166·2195)
  - 문제: G1(531) '그 값의 writer 블록 안(가장 이른 자리)'에 따르면 자리는 선언 상자 writer인 6 (e) S0 블록이다. 그런데 계획은 적용 상자 writer(`search_domain`)에 두었다.
  - 결과: 실패 시점이 로더 → 단계 B·탐색 문맥으로 바뀌고, 단계 A가 잘못된 선언으로 'ok'가 된다. 이 변경에 동작 변경·원래 취지와 다름 표지가 없다.
  - 권고: 자리를 '선언 상자 S0 블록 안 거부(6 (e) 블록, G1 -- 실패 시점 로더 → 단계 A의 그 블록)'로 고친다. 영향 자리 `SPEC_CONTRACT.md:151`·`test_spec_theta_bounds.py:185·192`를 적는다. fail-closed는 지금 안도 지켜지므로 차단은 아니다.
- **m12-2** `iv_area` toy base 서술(1166 '공통 상자 커패시터가 최소 면적 하한에서 빠지고', '(base = 그 커패시터 빠짐 -- red)')
  - 엔진 base에서 회로별 선언 없는 θ 커패시터는 `search_domain`이 `theta_capacitance_bounds_undeclared`로 정지한다. 실행 설정 재정의가 있으면 `_passive_value`가 `ctx.box` 기하 **중점**을 쓴다(`_helpers_area.py:17-25`). 어느 경우도 '빠짐'이 아니다.
  - '빠짐'은 `achievability._area`(248-255, `c_min None` → 합에서 빠짐)의 동작이다.
  - 권고: iv_area toy base = '정지(또는 실행 재정의 시 중점) -- red'로 고친다. 재배선 소비자 `achievability` 면적 하한에도 toy(공통 상자 커패시터가 상자 하한으로 들어감, base 빠짐 -- red)를 더하거나, N6.35 E-12 toy가 덮는다고 적는다.
- **m12-3** as-built 줄 인용(1166): `search_domain.py:76-80` → 70-75, `:89-90` → 85-86, `106-112` → 106-116. 검증 11 표의 검증자 기인 오류가 옮겨진 것이다.
- **m12-4** history «원문» 누락 1건: 1217 옛 조각 «범위 9 상자 적용 자리 = S0 θ 상자 블록·소비자 4곳 재배선».
- **m12-5** 측정·겹침
  - (a) '`spec 설정 직접 읽기 0(git grep)`'에 grep 패턴을 적는다. 엔진 철자 셋(`THETA_BOUNDS`·`_FIELD_BOUNDS`·문자열 `"theta_bounds"`)이고, 6 (e)의 `git grep THETA_BOUNDS`는 achievability를 못 잡는다.
  - (b) 6 (e) `iv_context.py:93` 재배선에 '(→ Q-CB1 승인 시 범위 9가 적용 상자 READS로 -- 6 (e) 대상에서 빠짐)'을 단다.
- **m12-6** DR-1 완료 (10) toy
  - toy 수준(블록/파이프라인)을 정한다. 파이프라인 수준이면 base = `mos_zero_current_structural` 정지다.
  - 둘째·셋째 경우는 '회귀 보호(red 아님)'로 표지한다.

## 5. 검사 4 -- 승인 상정

**가능.** Critical 0, Major 0. Minor 6은 문언 정정이고 새 실측은 필요 없다. m12-1·m12-2·m12-6은 test 작성자 기대값과 실패 시점에 닿으므로, 상정 전 같은 판 커밋으로 고치기를 권고한다. 다른 질문(Q-W1·Q-CF1·Q-CA1·Q-ZG1·Q-KV1)은 변경이 없고 상정 가능하다.

## 6. 원칙 점검표(실측/읽기/안 함)

| 항목 | 결과 | 방법 |
|---|---|---|
| graph 규칙 1(writer 하나) | 적용 상자 writer `search_domain` 하나, 둘째 생산자 0 | 실측(엔진 전수 grep, §2 (b) 표) |
| graph 규칙 2·4(사본) | `StartView.theta_bounds` 삭제 지정. `StartView.box`는 기존 투영(범위 밖 관찰) | 실측(`iv_context.py:94·106`, `start_values.py:180·184`) |
| graph 규칙 3(정의 축) | 선언 상자/적용 상자 축 기재 -- 맞음 | 읽기 + 실측 |
| graph 규칙 5·6 | 정본 자리 지정됨, 새 슬롯 0 | 읽기 |
| 소비자 전수 | 빠짐 0 | 실측(grep `theta_bounds`·`.box`·`s.field ==`) |
| 층·순환 | 역전 0, 순환 0. achievability READS search_domain 확인 | 실측(`achievability.py:334·342`, `stage_b.py:158·169`, `search_context.py:173`) |
| 만들면 배선 | 재배선 목록·toy 있음(base 서술 m12-2) | 실측 |
| fail-closed | 유지. 실패 시점 이동 미표지 → m12-1 | 실측(`stage_a.py`, `spec_load.py:122-127`, `spec_theta_bounds.py`) |
| O-165 | as-built 자리는 '재작성 범위로만 인용' 표지. 줄 번호 3곳 틀림 → m12-3 | 실측 |
| O-153 | 6 (e)·9 겹침 조건 문언 없음 → m12-5 | 읽기 |
| 상수 발명 | 0 | 읽기 |
| 회로 이름 | 규칙 문언 0(사실 칸 erfc만) | 읽기 |
| E-0·E-1·E-2·O-169·O-171 | 물리 판정 변경 없음 | 읽기 |
| 원래 취지와 다름 1:1 | Status·304·1166·2195 1:1(m12-1 미표지 1건 별도) | 읽기 |
| SPICE 수치 동일성 | 지적 기준으로 쓰지 않음 | -- |
| history «원문» | 10/10 원문 그대로, 누락 1 → m12-4 | 실측(`hist_check.py`) |
| 끊긴 경로 | 판 전체 122/122 존재 | 실측(`refcheck.py`) |
