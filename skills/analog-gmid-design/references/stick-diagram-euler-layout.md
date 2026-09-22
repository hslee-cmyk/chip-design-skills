# Stick Diagram + Euler Trail 기반 Layout-Sizing 피드백 루프

> 출처: F. Maloberti, *Layout of Analog CMOS IC — Part 2: Transistors and Basic Cells Layout*
> (`vendor/analog/Layout02.pdf`) + 워크드 솔루션(`vendor/analog/Layout02_stacked_layout(update).pptx`).
> gm/ID sizing(§1~§5, `gm-id-methodology.md`)의 출력을 물리적 layout(finger 수·배치·상호연결)으로
> 옮기는 단계에서, sizing이 layout 제약과 충돌할 때 **다시 sizing으로 되먹임**하는 절차를 다룬다.

## 0. 언제 쓰는가

- gm/ID로 회로의 모든 W/L, ID를 결정했고, 이제 물리 layout(finger 수·finger 순서·stack 배치)을
  정해야 할 때.
- 특정 스택(diffusion strip 하나)에 물릴 트랜지스터들의 finger를 어떤 순서로 배치해야
  source/drain diffusion이 끊기지 않고(= 한 번에 이어 그릴 수 있고) metal 배선이 꼬이지 않는지
  판단해야 할 때.
- Cell 전체를 정사각형/직사각형에 가깝게 만들기 위해 critical하지 않은 branch의 W를 조정하려는데,
  **그 조정이 원래 gm/ID 스펙(gain/GBW/noise/matching/distortion)을 깨지 않는지 재확인**해야 할 때.
- Worked example: PDF p.34~p.38(Folded Cascode 전체 예제)이 이 루프를 end-to-end로 보여준다.

## 1. 핵심 전제 — gm/ID sizing은 설계의 끝이 아니다

`gm-id-methodology.md` §1의 6단계(gm 고정 → gm/ID 선택 → ID → W → 기생 수렴 → 스펙 검증)가
끝나면 회로적으로는 완결되지만, **물리 layout 제약은 아직 하나도 반영되지 않은 상태**다. 이
문서가 다루는 것은 그 다음 단계: sizing 결과를 실제로 stick diagram(§4 stack 분할 + §3 Euler
trail 판정)으로 배치해본 **결과**(홀수차수 노드가 ≥4개라 한붓그리기가 안 됨, 특정 stack만
finger가 과도하게 많아 cell이 정사각형이 안 됨 등) — 즉 **layout 배치 결과에서 드러난 제약**
— 를 다시 sizing 쪽으로 되돌리는 반복 루프다. 되먹임되는 "이 결과"는 gm/ID 계산값이 아니라
**stick diagram으로 실제 배치해본 뒤에야 알 수 있는 layout 판정 결과**라는 점이 핵심이다.

```
[gm/ID sizing 완료: 각 소자 W/L, ID]
        │
        ▼
[§2.6 matching 그룹 탐지: 차동쌍/전류거울/캐스코드쌍 — find_matching_candidates()]
        │
        ▼
[§2.5 interdigitation(1D)/common-centroid(2D) 패턴 적용 → unit cell × N으로 W 조립]
        │
        ▼
[§4 Stack 분할] → [§3 Euler trail 판정] → 문제 없음 ─────────┐
        │        (= stick diagram 배치 결과)                  │
     문제 있음(홀수차수 노드 ≥4, 또는 cell이 정사각형이 아님,        │
     또는 §3.5 W가 unit cell 정수배가 아님)                     │
        │                                                    │
        ▼                                                    │
[§5/§5.5 비-critical branch W 조정 후보 생성(finger ±1 또는 unit cell 재탐색)]│
        │                                                    │
        ▼                                                    │
[gm-id-methodology.md §5 검증 체크리스트 재실행]                  │
        │                                                    │
   PASS─┴─────────────────────────────────────────────────→ [Freeze: 이 W로 확정, layout 시작]
        │
       FAIL
        │
        ▼
[다른 branch로 조정 대상 변경 / gm/ID 재선택 / 그래도 안되면
 diffusion break 등 layout 비용 감수] → §4로 복귀
```

이 루프가 수렴해야만(=조정된 사이징이 스펙을 통과해야만) 그 W로 **고정(freeze)**하고 실제
stick-to-layout 변환(interconnect 배치)에 들어간다. 스펙 재검증 없이 layout 편의만으로 W를
바꾸면, layout은 깔끔해지지만 회로 스펙(gain, GBW, phase margin, noise, matching)이 깨질 수
있다 — 이게 이 워크플로우가 존재하는 이유다.

## 2. Stick diagram 기초 — finger 홀짝과 노드 타입 (PDF p.26)

트랜지스터 하나를 여러 finger로 쪼개 diffusion strip 하나로 이으면(S-D-S-D-... 교대):

- **finger 수가 짝수**면 strip의 **양 끝이 같은 타입**(둘 다 source, 또는 둘 다 drain)
- **finger 수가 홀수**면 strip의 **양 끝이 다른 타입**(한쪽 source, 한쪽 drain)

이게 다음 절의 그래프 이론과 만나는 지점이다: finger 수를 짝수↔홀수로 바꾸는 것은 그 스택
양 끝 노드의 그래프 차수(degree)를 짝수↔홀수로 뒤집는 것과 동일하다. 즉 **finger 개수는
설계 자유도이자 그래프 차수를 조작하는 손잡이**다.

> **구현**: 아래 §3·§4의 그래프화·판정·순회 알고리즘은 특정 회로에 종속되지 않는 **일반
> 코드**로 `assets/stick_diagram.py`에 구현되어 있다 — 입력은 트랜지스터 리스트(이름, 극성,
> source/drain net, finger 수)뿐이고 어떤 회로 토폴로지든 그대로 넣을 수 있다. §9에 사용법이
> 있다. 이 절들의 서술은 그 코드가 구현하는 알고리즘의 근거를 설명하는 것이지, 코드를 대체하는
> 별도 수작업 절차가 아니다.

## 2.5 Interdigitation(PDF p.13~16) + Common-Centroid(PDF p.17~19) — Unit Cell 기반 matching의 근본 원리

§3.5(finger 폭 정합성)이 요구하는 "W는 finger 폭의 정수배"라는 제약은 우연한 레이아웃 규칙이
아니다. **matching이 필요한 소자를 어떻게 만드는가**라는, stick diagram보다 한 단계 더
근본적인 방법론에서 필연적으로 나오는 결과다. PDF는 이 방법론을 **두 개의 별개 기법**으로
나눠 다룬다 — 서로 관련되지만 다른 차원의 기법이라는 점이 중요하다:

- **p.13~16 "Interdigitated Devices/Patterns"**: matching되는 2개(이상) 소자를 **finger
  단위로, 한 행(row) 안에서 1차원 교차배열**한다(예: AABBAABB, ABBAABBA).
- **p.17~19 "Common Centroid"**: 소자(또는 위에서 만든 interdigitated 블록) 전체를
  **2차원 사분면(quadrant)**으로 배치한다(예: 왼쪽위=DA, 오른쪽위=DB, 왼쪽아래=DB,
  오른쪽아래=DA) — X축·Y축 양방향 공정 gradient를 동시에 상쇄하기 위한, interdigitation보다
  한 단계 위의 기법이다.

**핵심 원리(두 기법 공통)**:

1. matching되어야 하는 소자 그룹(전류거울, 폴디드 캐스코드의 대칭 브랜치, 차동쌍 등)마다
   **unit cell**(고정 finger 폭 하나)을 정한다.
2. 각 소자의 W는 이 unit cell을 **병렬로 N개** 배열해서 "만든다"(W = N × unit_cell_width) —
   설계식으로 유도하는 게 아니라 **조립 방식 자체가 정의**다. 그래서 N이 정수가 아닌 W는
   애초에 존재할 수 없다 — 이게 §3.5 `check_finger_width_compatibility()`가 잡아내는 문제의
   근본 원인이다.
3. 이 unit cell들을 아래 패턴표의 배열 중 하나로 **교차 배치**해서 공정 gradient(웨이퍼
   위치에 따른 미세한 공정 편차)를 상쇄한다.

> ⚠️ **패턴표는 목적이 아니라 수단이다.** 근본 원리는 딱 하나 — "대칭을 지키면서 최대한
> 잘게 섞는다"(§2.5.4의 "최대한 섞는다" 원칙)이고, §2.5.1/§2.5.2의 패턴표는 이 원리를
> **자주 나오는 소자 개수 조합에 대해 미리 구조화해둔 것**일 뿐이다. 실제 회로에서는 소자
> 개수가 표에 없는 조합(3개짜리 매칭쌍, 서로 다른 3종류 이상의 소자가 뒤섞인 그룹, 개수가
> 안 맞아 표를 그대로 못 쓰는 stack 등)으로 나오는 경우가 흔하다 — 이럴 때 **"표에 맞는
> 패턴이 없으니 대충 나눈다"로 타협하면 안 된다.** 대신 원리로 바로 내려가서 직접 구성한다:
> `build_mirror_symmetric_pattern()`(§2.5.3, 절반만 설계하면 나머지는 자동 생성)과
> `find_interleaved_symmetric_splits()`(§2.5.4, 개수가 안 맞는 매칭쌍도 다른 소자와 섞어
> 대칭 살리기, 결과는 매칭 품질 순 정렬)가 바로 이 "표 없이 원리로 직접 만드는" 범용
> 도구다 — 이 둘은 특정 패턴표 항목에 국한되지 않고 **어떤 소자 개수 조합에도 적용**된다.
> §10 체크리스트에도 이 판단을 명시한다.

### 2.5.1 Interdigitation 패턴표 (PDF p.15, 1D — 한 행 안에서 교차배열)

`*`는 원문이 명시한 "not all the patterns permit a stacked layout" 주의 대상:

| Base | 2× | 3× | 4× |
|---|---|---|---|
| A | AA | AAA | AAAA |
| AB | ABBA | ABBAAB\* | ABABBABA |
| ABC | ABCCBA | ABCBACBCA\* | ABCABCCBACBA |
| ABCD | ABCDDCBA | ABCBCADBCDA\* | ABCDDCBAABCDDCBA |
| ABA | ABAABA | ABAABAABA | ABAABAABAABA |
| ABABA | ABABAABABA | ABABAABABAABABA | ABABAABABAABABAABABA |
| AABA | AABAABAA | AABAAABAAABA\* | AABAABAAAABAABAA |
| AABAA | AABAAAABAA | AABAAAABAAAABAA | AABAAAABAAAABAAAABAA |

**worked example — 433PP443의 정체**: §6.1에서 확정한 folded cascode top 행의 M3/M4
finger 순서(MP를 제외하면 `M4,M3,M3,M4,M4,M3`)는 바로 이 표의 **"AB" 패턴 3× 변형
(`ABBAAB`)**을 A=M4, B=M3로 대입한 것과 정확히 일치한다(코드로 검증: `assets/stick_diagram.py`의
`interdigitate_layout([Transistor("M4",...,n_fingers=3), Transistor("M3",...,n_fingers=3)],
base="AB", repeat=3)`의 `rows[0]["transistor_sequence"]` → `["M4","M3","M3","M4","M4","M3"]`,
`433PP443`에서 MP 2개를 제외한 부분과 100% 일치). 즉 M3/M4는 임의로 나뉜 게 아니라, **서로
matching되어야 하는 한 쌍**이라서 이 표준 interdigitation 패턴 하나를 그대로 적용해 배치한
것이다(1D, 한 행 안에서만 교차배열 — common-centroid의 2D 사분면 배치는 아니다) — `*`가
붙은 3× 변형이라는 점도 원문의 주의사항과 일치한다.

### 2.5.2 Common-Centroid 패턴표 (PDF p.19, 2D — 위/아래 두 행을 사분면처럼 배치)

p.17의 DA/DB 대각선 배치(왼쪽위 DA·오른쪽위 DB / 왼쪽아래 DB·오른쪽아래 DA)와 p.18의
"Cross coupling vs Tiling" 비교를 일반화한 표다. 각 항목은 **(위 행, 아래 행)** 한 쌍으로
읽는다 — interdigitation처럼 한 행 안에서 끝나지 않고, 이 쌍을 상하로 배치해야 사분면 대칭이
완성된다:

| 위 행 | 아래 행 | 2× 반복 시 |
|---|---|---|
| ABBA | BAAB | 위: ABBAABBA / 아래: BAABBAAB |
| ABA | BAB | 위: ABAABA / 아래: BABBAB |
| ABCCBA | CBAABC | 위: ABCCBAABC / 아래: CBAABCCBA |
| AAB | BAA | 위: AABBAA / 아래: BAAAAB |

즉 interdigitation(§2.5.1)으로 "한 행 안에서 A/B를 섞는" 문제를 풀고 나면, common-centroid
(§2.5.2)로 "그 행을 위/아래 어느 쪽에 놓고, 아래 행은 어떻게 뒤집을지"를 한 번 더 결정한다 —
두 기법이 순차적으로 함께 적용되는 경우가 많다(예: folded cascode의 M1/M2가 §6에서 실제로
2개 행으로 나뉜 것이 이 조합의 사례).

### 2.5.3 패턴의 탄생 배경 — 대칭성이 곧 패턴이다 (PDF p.14 "Axis of Symmetries")

§2.5.1의 패턴표가 왜 하필 그 문자열들인지는 우연이 아니다. **interdigitation 패턴은
중앙 수직축을 기준으로 좌우 대칭이 되도록(matching 소자쌍은 서로 맞바꿔서) 구성된
것**이고, **common-centroid 패턴은 중심점을 기준으로 상하좌우 대칭이 되도록 구성된 것**이다
— 패턴표는 이 대칭 조건을 만족하는 문자열들을 미리 나열해둔 결과물일 뿐, 대칭 조건 자체가
1차적이다.

실제로 folded cascode top 행의 원본 finger 순서 `555555344PP334666666`를 중앙(문자열
정중앙, `P`와 `P` 사이)을 기준으로 반으로 나눠 왼쪽(`555555344P`)을 뒤집고 매칭쌍을
맞바꾸면(5↔6, 3↔4, P↔P) 오른쪽 절반(`P334666666`)과 **정확히 일치**한다 — MP(축 정중앙에
걸친 단독 소자)를 기준으로 M5↔M6, M3↔M4가 좌우로 거울처럼 배치된 것이다.

**구현**: `assets/stick_diagram.py`의 `build_mirror_symmetric_pattern(half, pair_map,
center=None)`은 **왼쪽 절반만 설계하면 오른쪽 절반을 자동 생성**한다(위 축대칭 규칙을
그대로 구현) — interdigitation 패턴표를 표에서 찾는 대신, 대칭 규칙으로 직접 만들 수 있다.
`check_mirror_symmetry(sequence, pair_map)`는 반대로 이미 만들어진 순서가 이 축대칭을
만족하는지 검증한다(위 `555555344PP334666666` 예시가 `True`로 검증됨, §9 Test 5).

### 2.5.4 응용 — 홀수 개수 매칭쌍을 다른 소자와 섞어서 대칭을 살린다

지금까지는 소자 개수가 짝수라 좌우로 깔끔하게 반씩 나뉘는 경우만 다뤘다. 그런데 **개수가
홀수인 매칭쌍은 혼자서는 절대 좌우 절반씩 나눌 수 없다**(3개를 1.5+1.5로 쪼갤 수 없으므로).
folded cascode bottom row가 이 경우를 실제로 보여준다: M9=3개, M10=3개(둘 다 홀수) — 원본
finger 순서 `...9xxoo99nno...`를 보면 M9는 **좌1·우2**, M10은 **좌2·우1**로 **불균등하게**
갈라져 있다. 그런데도 전체 시퀀스는 완벽하게 좌우대칭이다 — M9의 "왼쪽에서 부족한 1개"가
정확히 M10의 "오른쪽에서 남는 1개"와 서로의 swap 대응 위치에서 상쇄되기 때문이다.

**일반화 조건**: A, B가 서로 matching되는 swap 파트너이고 개수가 각각 `count_a`, `count_b`일
때, 이렇게 "섞어서" 대칭을 만들려면 **count_a == count_b**여야 한다(다르면 잔여 불균형이
남아 다른 소자로 흡수하거나, folded cascode top 행의 MP처럼 축 정중앙에 단독으로 걸쳐 배치해야
한다). 이 조건이 성립하면, A를 왼쪽에 k개(오른쪽에 count_a−k개) 놓을 때 B는 왼쪽에
count_a−k개(오른쪽에 k개) 놓으면 항상 대칭이 성립한다 — k는 0부터 count_a까지 자유롭게
고를 수 있다(k=0이나 count_a면 결국 "각자 한쪽에 통째로" 놓는 단순한 경우로 환원된다).

**"최대한 섞는다"는 원칙 — 대칭 후보가 여러 개면 다 같은 품질이 아니다**: count_a=count_b=3인
경우 대칭이 성립하는 분할은 `(0,3,3,0)`, `(1,2,2,1)`, `(2,1,1,2)`, `(3,0,0,3)` 네 가지 전부다
— 하지만 이 넷이 matching 관점에서 동등하지 않다. `(0,3,3,0)`은 A와 B가 사실상 **안 섞이고**
각자 한쪽 절반을 통째로 차지하는 것이라, 그 방향의 공정 gradient를 전혀 상쇄하지 못한다.
반면 `(1,2,2,1)`은 **양쪽 다 A·B가 섞여 있어** interdigitation의 근본 목적(gradient 상쇄)을
제대로 살린다. 실제로 pptx 원본이 채택한 것도 극단값(`(0,3,3,0)`류)이 아니라 **가장 고르게
섞인 `(1,2,2,1)`**이다.

**개선 동작(swap)으로 보면 더 직관적이다**: `(0,3,3,0)` 분할을 문자로 쓰면 `oxxoo|99nn9`
(M10 3개가 왼쪽에 뭉치고 M9 3개가 오른쪽에 뭉침), `(1,2,2,1)` 분할은 `9xxoo|99nno`다. 이 둘을
**나란히 놓고 비교하면 딱 두 자리, 양 끝(왼쪽 블록의 첫 글자와 오른쪽 블록의 마지막 글자)의
`9`↔`o`만 서로 바꾼 것**이다 — 이 한 번의 맞교환(swap)만으로 "안 섞인" 배치가 "가장 잘 섞인"
배치로 바뀐다(둘 다 대칭은 유지됨 — 어느 쪽이든 전체 시퀀스는 여전히 축대칭이다). 즉 실무에서는
"이미 만든 배치가 있는데 matching을 더 개선하고 싶다"는 상황에서, **양 끝(경계) 위치의 같은
매칭쌍 원소를 서로 바꿔보는 것**이 대칭을 깨지 않으면서 섞임 정도를 높이는 가장 간단한 개선
동작이다. "여러 대칭 후보 중 가능한 한 잘게, 최대한 섞이도록 고른다"는 게
이 기법의 실전 원칙이다.

**구현**: `find_interleaved_symmetric_splits(count_a, count_b)`가 이 조건(count_a==count_b)을
확인하고 가능한 모든 (a_left, a_right, b_left, b_right) 분할을, **"얼마나 고르게 섞였는가"
(`|a_left − a_right|` 오름차순, 즉 매칭 효과가 좋은 순)로 정렬**해서 반환한다. 실제
M9/M10=각 3개 사례를 넣으면 `[(1,2,2,1), (2,1,1,2), (0,3,3,0), (3,0,0,3)]`(가장 잘 섞인
순)이 나오고, pptx 원본이 실제로 채택한 `(1,2,2,1)`이 **정확히 1순위(최선) 추천값과 일치**함을
§9 Test 9에서 확인했다. 어떤 후보를 최종 채택할지는 이 함수가 강제하지 않는다 — 정렬 순서는
matching 품질 기준일 뿐이므로, 앞쪽(더 잘 섞인) 후보부터 실제 stack에 적용해 §3 오일러 조건도
만족하는지 확인하고 골라야 한다(홀수개 매칭쌍의 대칭 조건 자체는 오일러 경로/회로를 자동으로
보장하지 않는다).

**실무 적용**: 이 응용은 "짝수 개수 소자만 대칭 배치할 수 있다"는 제약을 깨준다 — gm/ID
sizing이 준 nominal finger 수가 우연히 홀수라도, 그 소자의 matching 파트너와 함께 **최대한
잘게 섞어** 배치하면 여전히 완전한 축대칭 layout을 만들 수 있고, 그중에서도 가장 고르게 섞인
분할을 고르는 것이 matching 성능(공정 gradient 상쇄)에 가장 유리하다. **DON'T** 이 기법을
모른 채 무조건 짝수 개수로 finger를 반올림하지 말 것 — §3.5(정수배 제약)를 불필요하게 어기거나
W를 억지로 바꾸게 된다.

### 2.5.5 구현 (패턴표 자체)

`assets/stick_diagram.py`의 `INTERDIGITATION_PATTERNS`(§2.5.1 표)와
`interdigitate_layout(transistors, base=..., repeat=...)`(패턴표를 실제 소자로 펼치고 hub-leaf
유효성까지 내부에서 검증·crossover 폴백, §2.7.3 참고), `COMMON_CENTROID_PATTERNS`(§2.5.2 표,
(위,아래) 쌍 구조)가 이 표들을 코드화한 것이다. 이 함수들은 "몇 개로 쪼갤지"(=unit
cell 개수, W로 결정)가 아니라 "이미 정해진 개수를 어떤 순서로 교차 배열할지"만 결정한다 — 즉
§2(finger 홀짝)·§3(Euler trail)·§3.5(정수 배수 검사)의 **입력**을 구성하는 역할이지, 그
판정을 대체하지 않는다.

### 2.5.6 Interdigitation 품질과 Euler feasibility는 다른 질문이다

Euler trail feasibility(한붓그리기가 가능한가)와 interdigitation 품질(finger가 잘 섞였는가)은
서로 다른 질문이다 — 그래프 이론적으로 유효한 trail이라고 해서 자동으로 잘 섞인 배치가
되는 건 아니다(예: `M2 M2 M2 M2 M2b M2b M2b M2b`도 유효한 trail이지만 전혀 안 섞임).
`build_graph()`는 같은 stack 안 트랜지스터들의 finger를 **라운드로빈**(한 개씩 돌아가며)으로
그래프에 추가한다 — Euler 조건(각 node 차수의 짝/홀)은 edge 추가 순서와 무관하므로 판정 결과는
그대로고, `hierholzer()`가 만드는 구체적 trail만 자연스럽게 여러 소자를 번갈아 방문하게 된다.

**hub-leaf 구조(공유 노드 하나 + 서로 안 이어진 leaf, 예: 전류거울·차동쌍)의 한계**: **딱 1개의
metal layer**(오일러 trail 하나로 완결되는 연속 diffusion 1개 행) 안에서는 매 finger를 완전히
1:1로 교대(`ABAB...`)할 수 없다 — 다른 소자로 전환하는 순간은 반드시 공유 노드(hub)를 지나갈
때뿐이고, 그러려면 직전 소자를 **짝수 개** 거쳐야 hub로 되돌아온다(`ABAB...`는 항상 두 번째
finger에서부터 막힌다, 직접 그래프 대입으로 확인). 실제 한계는 "블록 길이가 짝수"라는 것뿐이고
"AABB(2-finger 블록)로 고정된다"는 아니다 — 전체 개수가 홀수거나 두 소자 개수가 다르면
`build_graph()`+`hierholzer()`가 실제로 찾는 순서는 AABB보다 복잡한 형태(예:
`A,B,B,A,A,B,B,A,A,B`처럼 시작/끝에 홀수 finger가 붙는 open path)일 수 있다. **DO** 손으로
패턴을 고르지 말고, 그 finger 개수 조합으로 실제 `build_graph()`+`check_euler_condition()`+
`hierholzer()`를 돌려 나오는 순서를 그대로 채택할 것 — `common_centroid_layout()`이 정확히
이렇게 동작한다(§2.7.3).

**진짜 기준은 diffusion 연속성이 아니라 "1개 metal layer, 비교차"다**: Maloberti PDF p.31
"Use of one Metal Layer"가 명시하듯, 진짜 기준은 딱 1개의 metal layer로 교차 없이 그릴 수
있는가이고, 오일러 trail은 정확히 그 제약을 그래프로 옮긴 것이다(p.27 "Multi-transistor Stick
Diagram"). Lan/Tammineedi/Geiger(ISCAS 2001) Fig.3(b)의 `D1,D2,D2,D1`처럼 AABB보다 촘촘한
패턴이 존재하는 이유는, 공통 source(S)를 1개 층 안에 욱여넣지 않고 **별도의(2번째) metal
layer로 다른 net 위를 건너뛰어(crossover) 배선**했기 때문이다 — S가 그 층의 오일러 제약을
아예 안 받으므로 poly 순서를 자유롭게 고를 수 있다. 즉 그 패턴은 §2.5.1 패턴표를 "연속
diffusion 1개 행"에 그냥 적용한 예가 아니라, **레이어를 하나 더 써서(via로 위/아래 층을
오가며) 오일러 제약 자체를 우회한 결과**다 — 이게 §2.7 기법의 정체다.

**결론**: 딱 1개의 metal layer(오일러 trail, `build_stick_diagram()`/`hierholzer()`가 실제로
찾아내는 walk)만 쓴다면 허브-리프 구조는 여전히 짝수-블록 한계 안에 있다. `build_graph()`의
라운드로빈 기본값이 그 안에서 가능한 최선을 자동으로 찾아준다 — 억지로 더 촘촘한 패턴을
강제하려 하면 1개 층 안에서 walk가 안 된다(실제 칩에서는 그 교차 지점에 추가 layer/via가
필요하다는 뜻). 더 촘촘한(1-finger 단위) 교차가 필요하면 §2.7처럼 **추가 metal layer로 공유
노드를 다른 net들 위로 건너뛰게 배선**해야 한다.

## 2.6 Matching이 필요한 회로 요소 카탈로그 — §2.5 패턴을 "어디에" 적용할지

§2.5의 interdigitation/common-centroid는 아무 소자에나 적용하는 게 아니라, **matching이
회로 성능에 직접 영향을 주는 소자 그룹**에만 적용한다. 대표적인 카탈로그(gm/ID 설계 흐름에서
자주 등장하는 순서로):

| 요소 | 구조적 신호(자동 탐지 단서) | 왜 matching이 중요한가 | 자동 탐지 |
|---|---|---|---|
| **차동쌍**(입력쌍) | 같은 극성 + 같은 source(tail) net + 같은 W, gate net은 서로 다름 | 두 branch의 offset/CMRR이 W·L 불일치에 직접 비례 | ✅ `find_matching_candidates()` |
| **전류거울**(simple/cascode/Wilson) | 같은 극성 + 같은 gate net(대개 diode-connected 쪽 gate=drain) | 미러비 오차가 바로 전류 오차로 전파 | ✅ `find_matching_candidates(transistors)`(gate 공유만으로, cascode/Wilson 여부는 구분 안 함) — **더 엄격하게**: `find_matching_candidates(transistors, idiom_matches=find_idiom_matches(transistors))`(`analog-grammar` skill 연동, 2026-08-06)를 쓰면 gate뿐 아니라 **source까지 같고, diode-connected 레퍼런스가 실제로 있어야만** 후보로 인정한다 — M57/M58 실사고(gate만 같고 source가 달라 VGS 동일 미보장인데 매칭쌍으로 오판됐던 사고) 계기, opt-in(안 넘기면 옛 동작 그대로) |
| **캐스코드 대칭쌍**(folded cascode M5/M6, M7/M8, M9/M10 등) | 같은 극성 + 같은 gate + **서로 다른** source/drain net(각기 다른 folding node) | 두 差동 branch의 출력 임피던스·극점 위치가 어긋나면 CMRR·PSRR 저하 | ✅(옛 gate-only 판정 기준으로는 걸리지만 "캐스코드 역할"이라는 의미까지는 판별 못함) — **`idiom_matches=` 경로로 넘어가면 이 클래스는 더 이상 gate 우연 일치로 안 잡힌다** — 대신 `find_stack_edges()`+`find_stacked_matching_candidates()`(2026-08-06, "복합소자" 개념)가 이미 확정된 매칭쌍(예: M1a/M1b) 위에 직접 stacked된 소자쌍(M2a/M2b)을 재귀적으로 상속해 원인론적으로 탐지한다(gate 일치가 아니라 "확정된 쌍 위에 대칭으로 얹혀 있다"는 구조적 근거) |
| **저항비**(R2/R1, 게인/레퍼런스 설정) | (트랜지스터 아님 — 별도 R 소자) 같은 unit resistor를 직렬/병렬로 비율만큼 배치 | 게인 오차·레퍼런스 오차가 R 비율 오차에 직접 비례 | ❌ (이 모듈은 트랜지스터 전용, R은 범위 밖) |
| **커패시터비**(C2/C1, gain/sampling cap) | (트랜지스터 아님) 같은 unit cap을 배열 | 게인 오차(SC 회로), 샘플링 오차가 C 비율 오차에 비례 | ❌ (범위 밖) |
| **DAC/ADC 단위소자 배열**(thermometer-coded 전류원/커패시터) | 같은 극성 + 같은 gate(전류원 배열이면) + 다수(N개) | 단위소자 불일치가 INL/DNL로 직접 나타남 — 공정 gradient에 가장 민감 | ✅(전류원이면 current_mirror로 걸림, N이 큰 경우가 특징) |
| **Bandgap 코어**(PTAT 미러 + 매칭 BJT/diode) | 전류거울 부분은 위와 동일 + BJT/diode의 emitter 면적비(이 모듈 범위 밖) | 온도계수 오차가 미러비·면적비 오차에 직접 비례 | 부분적(전류거울 부분만) |
| **비교기/래치 cross-coupled 쌍** | 같은 극성 + 서로의 drain이 상대 gate로 교차연결(cross-coupled, gate≠source 그래프 패턴) | 오프셋이 임계전압 결정에 직접 영향 | ❌(현재 탐지기는 diff_pair/current_mirror 패턴만 봄 — cross-coupled 감지는 향후 확장) |
| **Sampling 스위치**(S/C 회로) | 같은 극성 + 같은 W, gate가 clock net | charge injection 불일치가 샘플링 오차로 직접 전파 | 부분적(diff_pair 패턴과 구조가 겹쳐 오탐 가능) |

**탐지의 한계(정직하게)**: `find_matching_candidates()`는 기본값(`idiom_matches=None`)
에서 순수 구조 신호(gate/source net 공유)만 본다 — 실제 self-test(§9 Test 6)에서
`M11`·`MN`(둘 다 source=gnd, 같은 W=16, 서로 다른 gate)이 "diff_pair 후보"로 잘못 잡히는
걸 확인했다: 이 둘은 실제로는 독립된 bias-생성용 diode-connected 소자이지 진짜 차동쌍이
아니다. 즉 이 함수가 찾은 그룹은 **후보**일 뿐이며, 회로가 실제로 그 역할인지는 설계자가
확인해야 한다 — R/C 비율, bandgap의 면적비, cross-coupled 쌍은 아예 구조적으로 탐지
불가능해 `stack_id`로 직접 표시해야 한다.

**2026-08-06 갱신**: `idiom_matches=find_idiom_matches(transistors)`를 넘기면(`analog-
grammar` skill 연동, `analog-gmid-design/references/analog-grammar-integration.md` 참고)
위 M11/MN 오탐은 해소된다 — `analog-grammar`가 두 소자 다 role=DIODE_CONNECTED로 판정해
diff_pair가 요구하는 role=AMPLIFYING 조건을 애초에 통과 못하기 때문이다(self-test 30에서
동일 fixture로 재확인). 단 이 경로는 **opt-in**이다 — `idiom_matches`를 실제로 넘기지
않으면 이 문단 첫 단락의 한계가 그대로 남는다. 캐스코드 대칭쌍(M2a/M2b류)은 이 opt-in
경로로 넘어가면 gate 우연 일치로는 더 이상 안 잡히므로, `find_stacked_matching_
candidates()`(복합소자 기반 상속, 위 표 참고)를 별도로 함께 써야 한다.

### 2.6.1 `find_verified_differential_and_mirror_relations()`의 fan-in 오판정 — 방향 인식 상류 슬라이스로 해결

**증상(세션25)**: 병렬 tail(예: `Vx`가 `M6`/`M7` 둘로부터 병렬 공급되는 구조)에서, 진짜
파트너(`M57`)가 아니라 `M7`이 `M58`과 잘못 묶이는 버그가 발생했다.

**근본원인**: 이 함수가 `(M1a,M1b)` 차동쌍 관계를 `M6`쪽 조합에서만 찾고, `M7`쪽에서
독립적으로도 같은 관계가 성립한다는 걸 "소자쌍 dedup" 로직이 조용히 버려 `M7`이 "차동쌍
소속 아님"으로 오판됨.

**시행착오(3라운드)**: (1) 전체 체인을 누적해서 봤더니 다른 무관한 관계까지 오염됨. (2)
"mirror 당사자면 무조건 배제"로 바꿨더니 이번엔 진짜 mirror-겸-differential 관계까지 배제됨.
(3) **방향 인식 상류 슬라이스**(`vdd_to_gnd` 방향이면 앞쪽이 상류, `gnd_to_vdd` 방향이면
반대로 뒤쪽이 상류 — 방향별로 "상류"의 정의 자체가 다름)로 해결.

**일반 교훈**: differential branch와 symmetric branch를 동시에 보고 각각의 branch에 실제로
속한 소자를 구별해야 한다 — "mirror 당사자라는 이유만으로 배제"하면 안 되고, 그 특정 비교에
실제로 (전류 방향상) 도달하는 상류 경로인지가 판정 기준이어야 한다.

## 2.7 Unit 소자 복제 — 1D interdigitation과 2D common-centroid 중 언제 무엇을 쓰는가

**실무 원칙**: matching이 중요한 소자 그룹은 **동일한 크기의 unit 소자를 N개 반복**해서
만들고(총 W를 임의로 나누는 게 아니라, 두 소자가 정확히 같은 unit geometry·같은 orientation을
갖도록), 그 unit들을 대칭 패턴(§2.5 interdigitation 또는 common-centroid)으로 배치해야
matching 특성이 좋아진다.

**§2.5.6과 연결되는 핵심 전제**: hub-leaf 구조(공유 노드 하나 + 서로 안 이어진 leaf, 예:
전류거울·차동쌍)는 딱 1개의 metal layer(오일러 trail 하나로 완결되는 연속 diffusion 1개 행)
안에서는 매 finger를 완전히 1:1로 교대(`ABAB...`)할 수 없다 — 다른 소자로 전환하려면 반드시
공유 노드(hub)를 지나야 하고, 그러려면 직전 소자를 짝수 개 거쳐야 hub로 되돌아온다. 실제
한계는 "블록 길이가 짝수"라는 것뿐이다 — 전체 개수가 홀수거나 두 소자 개수가 다르면
`build_graph()`+`hierholzer()`가 실제로 찾는 순서는 AABB보다 복잡한 형태(예:
`A,B,B,A,A,B,B,A,A,B`처럼 시작/끝에 홀수 finger가 붙는 open path)일 수도 있다. **DO** 손으로
패턴을 고르지 말고, 그 finger 개수 조합으로 실제 `build_graph()`+`check_euler_condition()`+
`hierholzer()`를 돌려 나오는 순서를 그대로 채택할 것(§2.5.6). `common_centroid_layout()`이
정확히 이렇게 동작한다(§2.7.3).

**패턴표 항목별로 1개 layer 실현 가능 여부가 다르다**: `ABABBABA`(§2.5.1 `AB` 패턴 4배 반복)
처럼 블록이 아닌 촘촘한 패턴은 1개 layer로 못 만든다(§2.5.6에서 직접 검증됨). 반면
`COMMON_CENTROID_PATTERNS` 표의 `ABBA`/`AAB`는 겉보기와 달리 실제로는 **AABB와 같은 부류
(짝수 블록 경계)**라서 추가 layer 없이 1개 layer로 이미 실현 가능하다(직접 그래프 검증:
`ABBA` → `leafA-tail-leafB-tail-leafA`, `AAB` → `tail-leafA-tail-leafB`, 둘 다 유효한 오일러
경로). 반면 같은 표의 `ABA`는 **1개 layer로 불가능**(어느 방향으로 시작해도 두 번째
finger에서 막힘)하다. 즉 **"1D는 1개 layer, 2D는 추가 layer"라는 이분법은 성립하지 않는다**
— 실현 가능 여부는 패턴별로 직접 `check_euler_condition()`으로 검증해야 알 수 있는 것이지,
1D냐 2D냐(행이 1개냐 2개냐)와는 무관하다. 2D(2행) 배치의 실제 의미는 "1개 layer로 실현
가능한 행을 하나 더 만들어서, 두 행을 swap-대칭으로 배치해 y방향/잔여 gradient까지 추가로
상쇄하는 것"이지, "AABB 한계를 우회하는 것"이 아니다.

### 2.7.1 실제 근거 — 왜 "unit 반복 + 2행 배치"가 matching을 개선하는가

1. **기하학적 동일성(identical geometry)**: 두 matched 소자를 "같은 unit을 N번 반복"으로
   만들면 W/L 반올림, contact 배치, edge 효과가 두 소자 사이에서 완전히 동일해진다 — 총 W만
   전기적으로 같게 잡고 서로 다른 형태(예: 한쪽은 finger 3개, 다른 쪽은 finger 5개)로
   구현하면 그 자체로 이미 기하학적 불일치가 생긴다.
   ([analoghub.ie](https://analoghub.ie/category/Layout/article/layoutMatchingPatterns):
   "Both patterns demand unit-sized elements... ensuring consistent geometry and
   orientation across the array.")
2. **고차(비선형) gradient 잔여 mismatch 감소**: unit을 더 잘게, 더 많이 나눠서 대칭 배치할수록
   1차(선형) gradient뿐 아니라 2차 이상의 gradient 성분까지 더 정밀하게 상쇄된다 — 실측
   데이터([Lan/Tammineedi/Geiger, ISCAS 2001](https://class.ece.iastate.edu/vlsi2/docs/papers%20done/2001-07-aicsp-ml.pdf)
   Fig.4): 단순 배치(뭉침) 대비 1D interdigitation(ABBA류)이 잔여 mismatch를 크게 줄이고,
   2D common-centroid(사분면 배치)가 거기서 다시 **약 절반**(그 논문 조건에서 Interdigitized
   ≈0.04% → Common-Centroid ≈0.02%)으로 줄인다.
3. **국소 공정 효과(WPE/LOD)의 균일 노출**: unit 하나하나를 독립적으로 guard-ring/dummy로
   감싸면, 큰 다중-finger 블록 하나로 만들 때 생기는 "블록 끝 finger vs 중간 finger가 다른
   주변 환경에 노출되는" 문제를 unit 단위로 세밀하게 완화할 수 있다.

### 2.7.2 결정 기준 — row(행) 개수를 언제 얼마로 정하는가

[analoghub.ie](https://analoghub.ie/category/Layout/article/layoutMatchingPatterns)의
실무 기준을 그대로 따르되, `common_centroid_layout()`의 일반화(§2.7.3)를 반영해 정확히
표현하면: 1D냐 2D냐는 "추가 layer를 쓰느냐"의 문제가 아니라 "몇 개의 물리 행에 나눠 배치해
몇 차원의 gradient를 상쇄하느냐"의 문제이고, 몇 개 물리 행에 나눌지는 그 자체로 별도의
최적화 대상이다.

**기본 원칙 — row 개수는 기본적으로 제약하지 않는다**: `common_centroid_layout(transistors)`를
`n_rows` 없이 그대로 호출하면 내부적으로 `target_rows=N`(매칭 그룹의 소자 개수)을 택해
**잔차 정확히 0(증명된 최적)**을 낸다(§2.7.3 경로①). 이 기본값이 항상 2행보다 낫거나 같다 —
소자가 정확히 2개인 단순 매칭쌍(전류거울, 차동쌍)에서는 N이 우연히 2라서 "2행"으로 보일
뿐이고, 소자가 3개 이상인 매칭 그룹(DAC/ADC 다수 unit, bandgap 다수 BJT 배열 등)이면
N행(N>2)이 2행보다 더 정밀한 매칭을 준다.

**DO** `n_rows`를 지정하지 말고 기본값(N행)을 쓸 것. **DON'T** floorplan 단계의 실제
면적/aspect-ratio 제약이 없는데 `n_rows=2`처럼 row 개수를 임의로 줄이지 말 것 — layout
분석 단계 자체에는 그런 제약이 없으므로, floorplan이 실제로 요구하지 않는 한 소자가 3개
이상인 그룹에서 row 수를 줄이면 잔차가 0보다 커져 매칭 품질이 불필요하게 나빠진다.

| 상황 | 기법 | 이유 |
|---|---|---|
| 단순 전류거울, 바이어스 회로(예: Example 1의 M2/M2b) | **1행, 진짜 오일러 trail 그대로**(`build_stick_diagram()`이 찾는 순서, 추가 조치 없음) | 면적 효율적이고 배선이 간단하다 — 1행 수준의 matching으로 충분 |
| 차동쌍, DAC/ADC 단위소자 배열, bandgap BJT 배열 등 정밀도가 특히 중요한 경우 | `n_rows` 미지정으로 `common_centroid_layout()` 호출 → **N행**(소자가 정확히 2개인 차동쌍/미러쌍이면 자연히 2행, 3개 이상이면 N행)으로 자동 배치, 각 행은 여전히 실제 오일러 trail(`build_graph()`+`hierholzer()`로 직접 계산), 회전(§2.7.3 경로①)으로 point-symmetric하게 배치 | 1행만으로는 못 잡는 y방향/잔여 gradient까지 상쇄 — **추가 metal layer는 필요 없다**. floorplan이 물리 행 수를 실제로 제한할 때만 `n_rows`로 명시적으로 줄인다 |

**패턴표 항목별 실현 가능 여부**: `INTERDIGITATION_PATTERNS`/`COMMON_CENTROID_PATTERNS` 두
문헌 표 모두, 표 안의 패턴이 **정말로 1개 layer로 실현 가능한지는 패턴마다 다르다** —
`ABBA`/`AAB`는 실제로 1개 layer로 가능하지만(직접 그래프 검증됨), `ABA`는 불가능하다
(마찬가지로 직접 검증됨). "1D/2D니까 자동으로 되거나 안 된다"고 짐작할 문제가 아니다 —
`interdigitate_layout()`와 `common_centroid_layout()` **둘 다** 그 정확한 순서를 내부에서
`build_graph()`+`check_euler_condition()`으로 직접 재검증하고, 실패하면 각자 crossover
폴백(§2.7.3)으로 자동 전환한다 — 호출자가 별도로 재검증하거나 대체 패턴을 고를 필요가 없다.

### 2.7.3 코드

전체 함수 시그니처·3단계 우선순위 로직·반환 필드는 `function-selection-map.md` §6
(Interdigitation/Common-centroid 배치)에 정리되어 있다 — 여기서는 이 문서의 다른 절이
참조하는 핵심 동작만 요약한다.

- `interdigitate_layout(transistors, base=None, repeat=None) -> dict`(§2.5.1) — hub-leaf
  소자를 1행 interdigitation으로 배치한다. `base`(+`repeat`) 지정 시 `INTERDIGITATION_PATTERNS`
  표에서 각 소자의 실제 `n_fingers`와 정확히 맞고 hub-leaf로도 유효한 조합을 찾아
  우선 쓴다(`method="pattern_table"`, crossover 0, `repeat` 생략 시 표 전체를 자동 탐색).
  표에 안 맞거나 표가 hub-leaf 무효(예: `ABA`, 3소자 이상 패턴 전부)면 소자 개수 비율에 맞춘
  배치를 직접 구성해 검증하고(`method="search"`), 그것도 0-crossover로 안 되면
  `find_min_crossover_layout()`으로 최소 crossover 배치로 폴백한다 — 호출자가 별도로
  `build_graph()`+`check_euler_condition()`을 다시 불러 재검증할 필요가 없다.
- `common_centroid_layout(transistors, n_rows=None, max_candidates=24)` — hub-leaf
  N개(N>=2) 소자의 connectivity(`Transistor` 리스트 — 전부 같은 `source`=hub 공유, `drain`은
  서로 다름)를 그대로 받아 common-centroid 배치를 찾는다. **① `target_rows`(=`n_rows` 명시값
  또는 미지정 시 N)가 소자 수와 같고 개수 전부 같음** — 회전 경로(`method="rotation_exact"`,
  잔차 정확히 0, 증명된 최적): N개 leaf에 이름을 순환 회전(`name_i -> name_{i+1 mod N}`)해
  N개 행에 배치한다(N=2면 전통적인 swap과 동일). **② N=2 + `target_rows==2` + 개수가
  다름(비율)** — `COMMON_CENTROID_PATTERNS`의 2-소자 문헌 패턴(`AAB`/`BAA` 등)에서 정확히
  맞는 조합을 찾아 검증된 결과(잔차 0)를 반환한다(`method="pattern_table"`, 표에 안 맞거나
  hub-leaf로 무효(`ABA`/`BAB`류)면 ③으로 폴백). **③ 그 외**(개수가 다르거나 `n_rows` 명시,
  표에도 안 맞음) — 휴리스틱 탐색 경로(`method="search"`, 증명된 최적 아님 — 비례
  라운드로빈으로 섞은 뒤 `n_rows`개로 균등 분할, 오일러 조건이 깨지면 인접 행끼리 1개씩
  주고받는 보정을 시도, 여러 절단 지점 중 `(crossover_count, isolated_pairs, residual)`
  사전식 정렬로 최선을 채택). ①②③ 경로 전부 0-crossover가 안 되면 `find_min_crossover_layout()`
  으로 최소 crossover 배치로 폴백한다. 반환값의 `"residual"`/`"isolated_pairs"`/
  `"crossover_count"`/`"method"`로 어느 경로였는지 항상 확인할 것 — 소자 개수 편차가 크면
  잔차가 0이 아닐 수 있고(잔차는 행 내부 x위치만 비교하므로 y방향 비대칭까지는 못 잡는 한계도
  있음), `isolated_pairs`가 0이 아니면 소자가 실제로 격리 배치된 것이다. 각 행의
  `"segments"`/`"crossover_after"` 필드로 crossover 위치를 확인할 것.

**실제 적용 사례(Intrinsic Gain Stage, sky130)**: M2/M2b 전류거울(4:4)은 단순 전류거울이고,
1행 수준의 matching으로 충분하다고 판단해 **1행, 진짜 오일러 trail
그대로**(`build_stick_diagram()`이 실제로 찾아낸 `M2,M2,M2b,M2b,M2,M2,M2b,M2b`)를
채택했다. §9 Test 11은 (정밀도가 더 필요하다고 가정할 때) `ABBA`/`BAAB` 2행 버전도 검증해
두었다 — 이 패턴은 직접 확인 결과 추가 layer 없이 1개 layer로도 실현 가능하다(위 표 참고).
§8 box-shape는 어느 쪽을 택하든 별도로 만족시켜야 한다(1행 버전은 N/P 두 stack이 각각
1행×8개로 맞추면 box가 되고, 2행 버전은 M1도 같은 폭의 2행으로 나눠야 box가 된다).

**실제 적용 사례 2(Walker CS/차동쌍, 5T OTA 입력단, sky130)**: 3개 매칭 그룹(M1/M2 차동쌍,
M3/M3b tail 미러, M4/M5 부하 미러) 전부 허브-리프 구조다. §2.7.2 기준대로 M3/M3b·M4/M5는
단순 미러라 1행으로 채택하고, M1/M2(차동쌍)만 오프셋 정밀도 때문에 2행(`common_centroid_layout`)을
적용했다 — 두 행 모두 여전히 1개 metal layer, 진짜 오일러 trail이다(추가 layer 없음).
§8 box-shape까지 함께
맞추려면 diffpair(2행)·tailstack(1행)·loadstack(1행) — 총 4개 물리 행의 폭을 전부
일치시켜야 한다: `search_stack_finger_w()`로 tailstack·loadstack의 finger_w를 각각
재탐색해 둘 다 정확히 폭 10(5+5)에 맞추고, M1/M2는 처음부터 소자당 finger 10개(짝수)로
잡아 `find_interleaved_symmetric_splits(10,10)`의 최선 분할 `(5,5,5,5)`로 diffpair의
2행도 폭 10에 맞췄다 — 세 finger_w 전부 원래 gm/ID sizing과 스냅 오차 0%로 딱 맞아떨어져
4개 행이 전부 폭 10인 완전한 box가 됐다. box-shape로 finger_w를 바꾼 뒤에도 SPICE 전류
매칭은 85.6%로 이전(87.3%)과 비슷한 수준을 유지했다 — diode-connected 미러(M3b, M4)는
SPICE가 자동 재보정하므로 box-shape와 스펙을 동시에 만족시킬 수 있었다.

## 3. Euler trail 그래프화와 3가지 존재 조건 (PDF p.27, pptx slide 1~2)

한 스택(하나의 연속된 diffusion strip으로 만들 대상 트랜지스터 그룹)을 그래프로 본다:

- **node = net**(그 스택에 물리는 서로 다른 전기적 노드 — source/drain 공유점)
- **edge = transistor 1개(또는 finger 1개)** — 두 노드(자신의 S, D)를 잇는다
- **MOS는 source/drain이 대칭**이므로 이 edge는 방향이 없다(무방향 그래프) — 이게 한붓그리기가
  성립하는 근본 이유다("MOS가 대칭이기 때문에 한붓그리기가 가능함", pptx slide 2 원문).

**오일러 경로 존재 조건 (pptx slide 2 원문 그대로):**

1. **모든 꼭짓점의 차수가 짝수** → 시작점=도착점, 오일러 **회로**(닫힌 한붓그리기) 가능.
2. **홀수 차수 꼭짓점이 정확히 2개** → 그 둘 중 하나에서 시작, 다른 하나에서 끝나는 오일러
   **경로**(열린 한붓그리기) 가능.
3. **홀수 차수 꼭짓점이 4개 이상** → 한붓그리기 **불가능**.

**worked example (pptx slide 2)**: M1(node1↔2), M2(node2↔3), M3(node3↔4)의 직렬 체인 —
node1 차수=1(홀), node2=2(짝), node3=2(짝), node4=1(홀) → 홀수 노드 정확히 2개(1, 4) → 경로
존재. 실제 배치 `3 4 3 2 1 2 1 2 3 4 3`가 이 조건을 만족하는 순서 중 하나다(M3가 양끝 2회씩,
M1이 가운데서 4회 왕복, M2가 그 사이 1회씩 — 이는 각 트랜지스터를 finger 여러 개로 쪼개
node1~4 사이에 필요한 만큼 반복 배치했다는 뜻).

**설계 레버**: 조건 3(홀수 노드 ≥4)에 걸리면 다음 중 하나를 선택한다:

- (a) **finger 수 조정으로 parity 전환** — 문제 되는 노드에 물린 트랜지스터의 finger 수를
  홀↔짝 전환해 그 노드 차수의 parity를 뒤집는다(§2). **비-critical branch에서 이 조정을
  우선 시도** — critical 노드(신호 경로/matching 민감 노드)의 finger 수를 함부로 바꾸면
  gm/ID 스펙이 깨질 위험이 크다. `assets/stick_diagram.py`의 `suggest_finger_adjustments()`가
  이 탐색을 자동으로 수행한다(모든 트랜지스터의 ±1 finger 조정을 전수 탐색해 홀수 노드가
  가장 많이 줄어드는 후보 순으로 반환) — 손으로 어느 소자를 조정할지 추측하지 않아도 된다.
- (b) **diffusion break** — 스택을 2개 이상의 분리된 strip으로 나눈다. 면적/기생 비용 증가.
- (c) **stack 재구성** — 애초에 어느 트랜지스터를 같은 stack(행)에 묶을지 재배정한다(§4로
  복귀).

⚠️ **오일러 조건은 두 번째 게이트다** — 그 앞에 §3.5의 finger 폭 정합성 검사를 먼저 통과해야
한다. W가 finger 폭의 정수배가 아니면 애초에 finger 개수 자체가 정의되지 않으므로, 오일러
분석은 그 다음 문제다.

## 3.5 Finger 폭 정합성 — 오일러 조건보다 먼저 확인할 더 기초적인 제약

같은 stack의 모든 트랜지스터는 finger 폭이 같아야 한다(§4). 이때 **W가 그 finger 폭의 정확한
정수배인지**는 오일러 그래프를 그리기도 전에 먼저 확인해야 하는 문제다 — "4.75개 finger"는
물리적으로 존재할 수 없다. 이건 단순한 층수 규칙이 아니라 §2.5의 unit-cell 조립 방식 자체에서
나오는 필연이다: W가 finger 폭(=unit cell)의 정수배여야 하는 이유는 "그렇게 만들어야 layout이
깔끔해서"가 아니라 **애초에 W = N×unit_cell로 조립하는 것이 matching 방법론의 정의**이기
때문이다. `assets/stick_diagram.py`의 `check_finger_width_compatibility()`가 이 검사를
담당한다. §6.1의 Folded Cascode 검증이 이 문제의 실제 사례다: PDF가 준 M7/M8=38µm,
M9/M10=25µm은 그 stack의 finger 폭(8µm)으로 나누어떨어지지 않아서(38/8=4.75, 25/8=3.125)
40µm/24µm로 조정됐다 — **이 조정의 실제 동기는 오일러 패리티가 아니라 이 정수-배수 제약이었다**
(§6.1에서 자세히 검증).

## 3.6 `vertical_stack_id`(전기적 VDD~GND 컬럼)와 물리 레이아웃 행(kind 동질)은 다른 두 축이다

**발견 경위(2026-08, 세션28)**: 사용자 질문("`resolve_stack_layout()`에서 왜 PMOS/NMOS가
같은 stack에 있는데 오일러 패스에 문제가 없지?")으로 촉발됐다. `vertical_stack_id`(전기적으로
VDD~GND 한 컬럼을 이루는 소자 그룹, 예: class-AB 출력단의 M15(PMOS)+M16(NMOS))를 그대로
§3~§4의 물리 레이아웃 행(diffusion strip)으로 취급하면, PMOS와 NMOS를 같은 물리적 행에
놓으라는 잘못된 결과가 나올 수 있다.

**근본원인**: `build_graph()`/`check_euler_condition()`은 순수 net-connectivity 그래프
알고리즘이라 `Transistor.kind`(pmos/nmos)를 전혀 참조하지 않는다 — 무방향 그래프이므로
PMOS/NMOS를 섞어도 수학적으로는 차이가 없어 보인다. 실측 결과 이 회로의 declared
`vertical_stack_id` 26개 중 **8개**가 실제로 kind-mixed(PMOS+NMOS 혼재)였는데도 오일러
조건 검사를 통과하고 있었다(예: `vbias2_stack`의 hierholzer 결과가 `M57`(PMOS)과
`M68`(NMOS)이 diffusion을 공유하며 바로 이어붙는, 물리적으로 불가능한 trail을 "path"(정상)로
확정한 사례). "게이트를 통과했다"는 관찰이 실제로는 "게이트가 그 조건을 볼 수 없어서 그냥
통과한 것"이었다는 뜻 — 검증 함수가 실제로 무엇을 체크하는지(무엇을 체크 **안** 하는지)를
코드로 직접 확인하지 않은 채 "통과했다"를 근거로 삼으면 안 된다는 일반 교훈이기도 하다
(related: `known-incidents.md`에 이 발견의 서사가 별도로 기록됨 — 여기서는 기술적 해법만
다룬다).

**해법 — 두 축을 명시적으로 분리**:
1. `build_graph()`에 **kind 동질성 하드 게이트**를 신설 — 다른 kind는 애초에 같은 그래프에
   넣지 않는다.
2. `derive_horizontal_stack_groups()` 신설 — `vertical_stack_id`(전기적 KVL 그룹) 안에서
   kind로 먼저 쪼갠 뒤, 기존 `merge_layout_groups_by_matching_pairs()`(재사용, 재발명 안 함)로
   declared `matching_pairs` 기준 대칭 branch를 재병합해 **물리 레이아웃 행**을 만든다.

이후 `resolve_stack_layout()`은 electrical 질문(KVL, `vertical_stack_id`)과 physical 질문
(오일러 trail/대칭 배치, 물리 레이아웃 행)을 각각 별도 축에서 파생해 참조한다 — "이 두 값이
같은 축의 다른 표현"이라고 가정하지 말 것.

### 3.6.1 `vertical_stack_id` 자체를 connectivity로 자동 유도하기 — naive 시도 3개 실패, 1개 성공

`vertical_stack_id`(전기적 VDD~GND 컬럼) 선언 자체를 connectivity(KCL)만으로 자동 재구성하는
시도(세션23)에서, 직관적인 규칙 4가지 중 3개가 실패했다:

1. **엄격 2단자 KCL union** — matching_pairs와 KCL 경계가 거의 서로소라 결과가 항상 공집합에
   가까움.
2. **rail 제외 전체 연결성분** — 51개 소자 중 25개가 declared 11개 그룹을 전부 섞은 한 덩어리로
   붕괴(너무 성김).
3. **소자 단위 분기별 경로 나열** — 병렬 형제(예: `M1a`/`M1b`)를 다음 hop으로 잘못 인식해
   조합이 446개까지 폭발.

**성공한 규칙**: PMOS는 source(레일쪽)→drain(부하쪽), NMOS는 drain(부하쪽)→source(레일쪽)
순으로 **kind별로 "실제 전류 방향"을 고정**해 추적한다(`trace_vdd_to_gnd_branches()`) — 병렬
형제는 구조적으로 다음 hop이 될 수 없고, PMOS/NMOS의 drain끼리 만나는 지점만 진짜 캐스코드
접합으로 인식된다. 사용자가 제시한 5개 정답 branch와 정확히 일치했고, 조합 폭발 없이 29개
branch로 수렴했다.

**한계**: 이 branch 골격만으로는 `vertical_stack_id`를 완전 자동 확정하지 못한다 — "허브
공유형"(예: M5/M6/M7처럼 여러 branch가 tail 하나를 공유)과 "인접쌍 분할형"(사람이 하나의
branch를 기능 이름 경계로 둘로 쪼갬)이라는 두 어긋남 패턴이 남는다. 이건 branch tracing 결과에
analog-grammar idiom matching을 결합(`suggest_vertical_stack_composites()`)해야 최종
해소된다(실측 62/63 일치).

## 3.7 오일러 게이트는 필요조건이지 충분조건이 아니다 — `n_fingers=1` 기준 검증의 한계

병합 전 오일러 실현가능성 게이트(§4.1)는 기본적으로 `n_fingers=1`(topology.json 원본,
아직 실제로 사이징되지 않은 상태)만 보고 병합을 승인한다. 하지만 실제 파이프라인은 이후
`assign_finger_geometry()`가 실측 W로 계산한 **전혀 다른 finger 수**로 오일러를 다시
판정한다 — 이 둘의 홀짝 결과가 항상 같다는 보장은 없다.

**정직한 한계로 기록**: 이 게이트는 필요조건(베이스라인에서 최소한의 가능성이 있는지)만
걸러내는 것이지, 충분조건(실제 사이징 이후에도 계속 풀린다는 것)까지는 보장하지 못한다.
`assign_finger_geometry()` 이후 단계(euler 자동수정, `run_topology_pipeline_with_finger_
fixup()`)가 이 gap을 실제로 흡수하는 하류 안전망이다 — `n_fingers=1` 게이트 통과를 "이 그룹은
완전히 안전하다"는 뜻으로 오독하지 말 것.

## 4. Stack 분할 절차 (PDF p.25)

**핵심 전제(Maloberti PDF p.29 "Layout Oriented Design")**: stack(물리
행) 배정의 기준은 **"같은 stage인가"가 아니라 "같은 극성 + 하나의 공유 net(hub)을 갖는가
+ 그 병합이 실제로 한붓그리기 되는가"**다. p.29 슬라이드는 1단 PMOS 부하(M3/M4)와 2단
PMOS gain 소자(M6)를 stage가 다름에도 불구하고 "같은 극성 + vdd 공유"라는 이유만으로 한
물리 행에 합친다(§4.1). 즉 stage 경계는 stack 배정의 결과일 뿐 입력 전제가 아니다 —
아래 절차의 3번 단계("트랜지스터끼리 묶는다")를 stage별로 미리 나눠놓고 시작하면 이런
병합 기회 자체를 놓친다.

1. 회로의 모든 트랜지스터 W/L을 확인한다(gm/ID sizing 결과).
2. Layout 관점에서 finger로 쪼갠다(단위 finger 폭 결정 — 공정 룰 + matching 요구사항).
3. **같은 finger 폭을 쓸 수 있는 트랜지스터끼리** 같은 stack(행)으로 묶는다 — stack 하나 =
   같은 finger width, (길이는 달라도 됨) diffusion strip 하나. **stage 경계는 무시하고
   먼저 `find_hub_merge_candidates()`(§4.1)로 병합 후보부터 찾을 것** — 그중 실제로 합칠
   그룹만 최종적으로 `stack_id`를 부여한다(합치지 않기로 한 그룹은 그대로 stage별로 분리).
4. 이 시점에 W가 딱 안 맞으면(=stack 내 다른 트랜지스터들과 finger 폭이 안 맞으면) **비-critical
   트랜지스터의 W를 조정**할 후보를 만든다 — 이게 §5 피드백 루프로 들어가는 입구다.
5. 모든 stack의 finger 개수를 되도록 비슷하게 맞춘다(cell 전체 shape가 정사각형에 가까워짐,
   §8).
6. Stack들을 배치하고 상호연결(interconnect)한다.

단계 3(같은 폭끼리 자동 그룹핑)과 이후의 그래프화·판정·순회(§3)는 `split_into_stacks()` +
`build_stick_diagram()`이 기계적으로 수행한다. 단계 1(어떤 트랜지스터를 같이 stack으로
묶을지의 회로적 판단, 예: folded cascode에서 왜 MP,M3,M4,M5,M6이 한 그룹인지, 또는 p.29처럼
stage가 다른 소자를 합칠지)은 코드가 대신 결정하지 않는다 — `Transistor.stack_id`로 명시해서
그 판단을 코드에 전달한다. 다만 **그 판단 자체를 위한 후보 탐색과 유효성 검증**은 아래 §4.1의
두 함수가 기계적으로 도와준다.

### 4.1 Stage 경계를 넘는 stack 병합 — 언제, 어떻게 판단하는가

**왜 병합하는가**: 매 stage마다 별도 행을 만들면 stage 수만큼 행이 늘어나 cell이 세로로
길어진다. 같은 극성 소자를 여러 stage에 걸쳐 한 행으로 합치면 행 개수 자체가 줄어 더
compact한 cell이 나온다 — p.29 예제가 정확히 이 효율성 때문에 M3/M4(1단)+M6(2단)를
합친다.

**탐지**: `find_hub_merge_candidates(transistors)`가 `stack_id`/stage 배정을 완전히
무시하고, 극성 + 공유 단자(source 또는 drain)만으로 회로 전체에서 병합 **후보**를 찾는다
— `find_matching_candidates()`가 "matching이 필요한 쌍"을 찾는 것과 달리, 이 함수는
matching과 무관하게 "같은 diffusion에 물릴 수 있는 후보"를 찾는다(서로 다른 stage,
matching 관계도 아닌 소자끼리도 hub만 같으면 잡힌다).

**검증(반드시 필요 — 후보 발견 ≠ 실제로 가능)**: hub 하나에 leaf(서로 다른 소자)가 2개뿐인
구조(전류거울/차동쌍)는 finger 개수가 몇이든 항상 한붓그리기가 됐다(§2.5.6). 하지만 **leaf가
3개 이상**인 병합(p.29의 M3/M4/M6가 정확히 이 경우 — hub=vdd, leaf=bias/out1/out2 3개)은
조건이 다르다 — 직접 `build_graph()`+`check_euler_condition()`으로 확인한 결과(§9 Test 14,
3-leaf 조합 64개 전수 대조):

| 홀수 finger를 가진 leaf 개수(m) | 결과 |
|---|---|
| m = 0 (전부 짝수) | 항상 가능 (closed circuit) |
| m = 1 또는 2 | 항상 가능 (open path) |
| m ≥ 3 | **항상 불가능** — leaf 개수나 구체적 값과 무관 |

**실무 규칙**: 병합한 stack의 모든 소자가 같은 finger 수 k(§8 box-shape처럼 "공통 finger
수"를 원하는 상황)를 쓴다면, **leaf(=병합된 소자 수)가 3개 이상일 때 k는 반드시 짝수여야
한다** — k가 홀수면 m=(leaf 개수)가 그대로 3 이상이 되어 항상 실패한다. p.29 슬라이드가
"same number of fingers per stack (k)"를 요구하면서 실제로 짝수 k를 쓰는 이유가 취향이
아니라 이 그래프 이론적 필연이었다는 뜻이다. `check_multi_leaf_hub_parity(n_fingers_by_leaf)`
가 이 판정을 그래프를 만들지 않고 공식으로 빠르게 해준다(여러 k 후보를 탐색할 때 스크리닝
용도 — 최종 채택 전에는 `build_graph()`+`check_euler_condition()`으로 반드시 재확인할 것).

**결정 순서**: (1) `find_hub_merge_candidates()`로 후보 발견 → (2) 후보의 leaf 개수가
3개 이상이면 `check_multi_leaf_hub_parity()`로 스크리닝(2개 이하면 항상 가능하니 생략
가능) → (3) `search_stack_finger_w()`류로 공통 k(leaf≥3이면 짝수)에서 각 소자의 finger_w를
구함 → (4) 병합 시 행 개수 감소가 실제로 이득인지(별도 stage별 행으로 뒀을 때와 면적
비교) 판단해 최종적으로 `stack_id`를 부여한다 — 병합 가능하다고 항상 병합이 이득은 아니다.

**음성 사례 — 병합 후보가 없는 게 정상인 경우**: `find_hub_merge_candidates()`를
모든 회로에 돌리면 뭔가는 항상 나올 거라고 기대하면 안 된다. Example 1(IGS)과 Example 2(Walker
5T OTA)에 §4.1/§4.2 도구를 적용한 결과:

- **Example 1**: stage가 1개뿐이라 "stage 경계를 넘는 병합" 자체가 성립할 여지가 없다.
  `find_hub_merge_candidates()`는 M2/M2b(PMOS, source=vdd 공유) 하나만 찾는데, 이건 이미
  기존 pstack 그 자체다. M1(NMOS)은 겹치는 소자가 없어 병합 후보에서 원천 제외된다. 이미
  2-stack(nstack/pstack)으로 최소 구조라 새 프레임워크로 바뀌는 게 없다.
- **Example 2**: PMOS 쪽(M4/M5=loadstack)은 Ex1과 마찬가지로 유일 후보=기존 구조. NMOS 쪽은
  겉보기엔 흥미로운 case다 — diffpair(M1/M2, source=tail 공유)와 tailstack(M3/M3b, source=gnd
  공유)이 "tail"이라는 같은 물리 net을 사이에 두고 있다(M1/M2의 source이자 M3의 drain).
  하지만 `find_hub_merge_candidates()`는 source/drain을 별개 키로 취급하므로 (nmos,'drain','tail')=[M3]는
  크기 1이라 후보에서 빠진다 — 이건 함수의 사각지대가 아니라 **실제로 병합이 안 맞기 때문**이다:
  diffpair 쪽은 tail이 hub, tailstack 쪽은 tail이 leaf라 역할이 반대다(Ex3의 stage1+stage2
  병합은 두 그룹 다 vdd/gnd를 **같은 역할**(hub)로 공유했기 때문에 성립했던 것과 대비).
  실제로 M1/M2/M3(9,9,5핑거)를 억지로 하나의 tail-hub로 강제 구성해 `check_multi_leaf_hub_parity()`에
  넣어봐도 `m_odd_leaves=3 -> impossible`이 나와, 역할 불일치를 무시하더라도 어차피 그래프상
  불가능함이 이중으로 확인된다. 따라서 Example 2도 기존 3-stack(diffpair/tailstack/loadstack)
  구조가 이미 최선이며 바뀌는 게 없다. → **다단 캐스케이드(Ex3)에서만 stage-crossing 병합이
  실제로 이득이 되고, 단일 stage 회로(Ex1/Ex2)에서는 새 프레임워크를 적용해도 자연스럽게
  "병합 없음"으로 수렴한다** — 이게 프레임워크가 과적합되지 않았다는 근거다.

### 4.2 세로로 쌓을까, 가로로 놓을까 — Case A vs Case B

지금까지(§8) 다룬 방식은 **세로 스택(Case A)**: 여러 stack을 위아래로 쌓아 하나의 cell을
만들 때, 쌓이는 행들의 **폭(n_fingers)을 통일**하고 **높이(finger_w)는 stack마다 자유롭게**
둔다(`search_stack_finger_w()`). 이건 회로도(schematic)에서 stage 간 연결이 **세로로
흐를 때**(1단 출력이 아래 2단 입력으로 이어지는 배치) 맞는 선택이다.

schematic이 **가로로 흐르는 경우**(다단 캐스케이드가 좌→우로 나란히 그려지는, 흔한 교과서
표기)라면 정반대가 맞다 — **가로 배치(Case B)**: stage들을 좌우로 나란히 놓고, 이번엔
**높이(finger_w)를 stage 전체에서 통일**하고 **폭(n_fingers)은 stage마다 자유롭게** 둔다
(책 두께는 달라도 높이가 같으면 책장에 나란히 꽂히는 것과 같은 원리). `search_shared_finger_w()`
가 Case A `search_stack_finger_w()`의 정반대 방향 자매 함수로 이 탐색을 담당한다.

**Case A와 근본적으로 다른 점**: Case A는 matching pair처럼 W가 서로 같은 소자끼리 정확히
나누어떨어지는 finger_w를 찾는다(존재하면 오차 0). 하지만 서로 다른 stage의 W는 대개
무관한 실수값이라, **모든 소자에 정확히 맞는 finger_w는 일반적으로 없다** — `search_shared_finger_w()`
는 대신 "가장 스냅 오차가 적은" 후보를 찾고, 그 오차(`max_snap_error`)를 보고 채택 여부를
판단하게 한다.

**schematic 방향은 출발 가설일 뿐, 반드시 숫자로 재확인할 것(Example 3, NGCC 3단, §9 Test 15)**:
NGCC의 schematic은 좌→우로 흐르는 전형적인 3단
캐스케이드다(gm1→gm2→gm3 순서, 실제로 이 스킬의 Example 3 schematic도 이렇게 그렸다).
"schematic이 가로면 Case B"라는 원칙만 따르면 9개 소자 전부에 finger_w 하나를 적용해야
할 것 같지만, 실제로 `search_shared_finger_w()`를 돌려보면:

- **스냅 오차만 최소화**(제약 없음): finger_w≈0.60µm, 최대 스냅오차 0.61%(아주 정확함) —
  하지만 M1b/M1c(4핑거) vs M3b/M3c(523핑거)로 **행 폭 비율이 131:1**이 되어 한쪽 stage가
  실무에서 못 쓸 만큼 가늘고 길어진다.
- **행 폭 비율을 25:1로 강제 제한**: finger_w≈12.5µm까지 커지지만, 이번엔 M1b/M1c의
  스냅 오차가 **426%**까지 뛴다(2.384µm짜리 소자를 1개 finger·12.5µm로밖에 못 만드니 당연한
  결과) — 도저히 쓸 수 없는 수준.

**원인**: NGCC는 gm3/gm1≈24배 차이 때문에 소자 W 자체가 최대 130배(M1b 2.384µm ~ M3b
313.626µm)까지 벌어져 있다 — 이 정도로 큰 소자 크기 스펙트럼에서는 Case B(공통 finger_w
하나)가 수학적으로 성립하지 않는다. Example 3에 실제로 채택한 건 Case A
(§8, box-shape target=8 + load3만 4개 물리 행으로 쪼갬)였고, 이 검증 결과가 그 선택이
옳았음을 사후적으로 확인해준다.

**결론 — 결정 기준의 정확한 위치**: "schematic의 캐스케이드 방향"은 Case A/B 중 **어느 걸
먼저 시도해볼지 정하는 출발 가설**이지, 최종 결정 기준이 아니다. 최종 결정은 반드시
`search_shared_finger_w()`(Case B) 또는 `search_stack_finger_w()`(Case A)를 실제로 돌려서
나오는 **스냅 오차·행 폭(또는 행 높이) 비율의 트레이드오프가 실무적으로 받아들일 만한지**로
내린다 — 두 tool 모두 "받아들일 만한 후보가 없다"고 나오면(Example 3의 Case B가 그랬듯),
schematic 방향과 무관하게 다른 방식(세로 스택, 또는 §4.1의 stage 병합, 또는 §4의 물리 행
분할)으로 넘어가야 한다는 신호다. 소자 크기 스펙트럼이 넓은 다단 회로(단마다 gm이 크게
다른 경우)일수록 이 재확인이 특히 중요하다 — "schematic이 가로니까 무조건 Case B"라고
가정하고 넘어가면 안 된다.

## 5. Sizing 피드백 루프 — 무엇을 조정하고 무엇으로 재검증하는가

**조정 대상 판단**: "이 branch를 조정해도 회로 스펙에 영향이 작은가?"를 먼저 판단한다 —
전형적으로 **미러 비율만 문제인 전류원, cascode 상단의 캐스코드 소자(자체 gm은 이득에
직접 기여하지 않고 출력 임피던스만 높임), 바이어스 전용 branch** 등이 조정 여지가 크다.
반대로 입력 差동쌍, dominant pole을 결정하는 소자, 노이즈 dominant 소자는 최후의 수단으로만
건드린다.

**재검증은 `gm-id-methodology.md` §5(또는 이 skill 개요서 SKILL.md §5) 체크리스트를 그대로
재실행**한다 — 새 문서를 만들지 않는다:

- [ ] W 변경 후에도 목표 gm/ID(qF)가 여전히 그 소자의 동작점을 대표하는가, 아니면 ID/W
      비율이 바뀌어 다른 inversion 영역으로 밀렸는가?
- [ ] 이득(A = (gm/ID)·VA) 스펙을 여전히 만족하는가 — cascode/미러 소자 W 변경은 대개 VA에
      영향, gm에는 무영향이라 이득 여유가 있는 편이다.
- [ ] GBW/phase margin(다단이면 §10 topology_fn 재실행) 스펙을 만족하는가 — 기생 Cgg/Cgd가
      W에 비례해 변하므로 극점 위치가 미세하게 이동할 수 있다.
- [ ] Matching(전류거울/차동쌍 관련이면) 여전히 충분한가 — W 축소가 mismatch(σ∝1/√(WL))를
      악화시키지 않는가?
- [ ] Slew-rate/noise가 W 변경으로 악화되지 않았는가?

**판정**:

- **PASS** → 이 W로 **고정(freeze)**한다. 이 시점 이후로는 sizing을 재론하지 않고 물리 layout
  (finger 배치·상호연결)만 진행한다 — freeze 없이 layout에 들어가면 나중에 사이징이 또
  바뀌어 배치를 다시 해야 하는 재작업이 발생한다.
- **FAIL** → (i) 같은 조건을 만족하는 다른 비-critical branch로 조정 대상을 바꿔 다시 시도,
  (ii) 그 branch 내에서 gm/ID(qF)를 재선택해 W 변경 폭을 줄이는 방향 시도, (iii) 그래도 스펙을
  못 맞추면 §3(c)의 diffusion break(면적 비용 감수)로 후퇴한다. 무한정 반복하지 말고, 스펙
  마진이 이미 타이트한 소자는 초기 후보에서 제외하는 편이 빠르다.

## 5.5 Unit Cell 사이징 후보 탐색 — nominal W에서 거꾸로 시작하기

§5의 루프는 "이미 stack을 나눠봤더니 문제가 생겼다"는 반응형 흐름이다. 반대로 **처음부터**
gm/ID가 준 nominal W를 특정 unit cell 폭들의 정수배 후보로 바꿔서 시작할 수도 있다 —
`assets/stick_diagram.py`의 `search_unit_cell_sizing(nominal_w, candidate_unit_widths)`가
이 역할이다: nominal_w 근방에서 `unit_w × N`(N=정수) 형태의 후보를 전부 만들어 상대오차
오름차순으로 반환한다. 예를 들어 gm/ID가 37µm을 요구했는데 그 stack의 unit cell 후보가
8µm/10µm뿐이면 40µm(8×5 또는 10×4, 오차 8.1%)가 가장 가까운 후보다.

⚠️ 이 함수는 §3.5(정수배)만 만족하는 후보를 **생성**할 뿐, §5의 스펙 재검증이나 §8의
shape 판단을 대신하지 않는다 — 오차가 가장 작은 후보부터 순서대로 §5 체크리스트를 돌려
채택 여부를 판단해야 한다.

## 6. Worked example — Folded Cascode (PDF p.34~p.38)

이 예제가 §5 루프의 완전한 end-to-end 사례다. 아래 수치는 PDF p.34~p.38 원본 이미지를
직접 렌더링해 확인한 값이다(과거 텍스트 추출본은 슬라이드 5의 finger 순서 정렬이 깨져 있어
신뢰할 수 없었다).

- **p.34 "Example 2 (Folded Cascode)" — 원 회로 W(µm), 확인됨**:
  `MP=20, M3=30, M4=30, M5=60, M6=60, M1=80, M2=80, M7=38, M8=38, M9=25, M10=25, M11=16, MN=16`
  (13개 소자, "Only Ws are shown" 명시).
- **p.35 "Split of Transistors" — stack별 finger 폭·개수, 확인됨**:
  - top stack(MP, M3, M4, M5, M6): finger 폭 **10µm**, finger 수 = 2, 3, 3, 6, 6
    (20/10, 30/10, 30/10, 60/10, 60/10 — 전부 정수, 조정 불필요).
  - bottom stack(M7, M8, M9, M10, M11, MN): finger 폭 **8µm**. M11=16µm(2개), MN=16µm(2개)는
    그대로지만, **M7·M8(38µm)과 M9·M10(25µm)은 8로 나누어떨어지지 않는다**(38/8=4.75,
    25/8=3.125) — 슬라이드에 38과 25가 빨간 취소선으로 그어져 있고 옆에 **40, 24**로 다시
    적혀 있다. 즉 M7/M8: 38→40µm(=5×8), M9/M10: 25→24µm(=3×8)로 조정.
  - mid(M1, M2): p.36에 "10x2"로 표기 — 각 10개 finger(80/10=8µm/finger로 bottom과 동일 폭).
- **p.36 "Stack Design"**: 조정된 W로 각 stack의 finger **배치 순서**(어느 트랜지스터의
  finger가 몇 번째 자리에 오는지)를 압축 표기로 제시한다. 이 문서 §3의 "node 순서" 표기와
  달리, 이 슬라이드의 문자열은 "그 자리에 어느 **트랜지스터**의 finger가 있는가"를 나열한
  것이다(예: top 행 문자열은 M5 finger 6개가 연속, 이어서 M3/M4/MP/M3/M4, 마지막에 M6 finger
  6개 — 각 문자의 등장 횟수를 세면 P=2, 3=3, 4=3, 5=6, 6=6으로 p.35의 finger 수와 정확히
  일치한다). M1/M2 행은 `1,1,2,2,...` 반복 패턴 2개 행으로 나뉘어 있어 interdigitation
  (PDF p.13~16)과 common-centroid(PDF p.17~19)가 결합돼 있음을 보여준다(§2.5).
- **p.37 "Interconnection: Exercise"**: 위에서 정한 finger 배치 위에 metal로 실제
  source/drain 배선을 긋는 연습문제(4개 행, 행마다 약 20개 finger 자리 — 정답은 이 슬라이드에는
  없고 학생이 직접 풀어야 하는 빈 칸으로 남아 있다).
- **p.38 "Basic Cell Design: check-list"**: 이 전체 절차의 종료 조건 — 회로도 그리기 →
  critical element/node 식별 → matching 소자 표시 → 대칭축 표시 → W 분석 → **"Possibly,
  change transistor size for a layout oriented strategy"**(= §5 피드백 루프 그 자체) →
  stack 그룹화 → cell height 정의 → stick diagram 스케치("transistors of the same type in
  the same region") → substrate/well bias 공간 확보 → I/O 연결 레이어 정의 →
  **"Begin the layout now!!"**.

### 6.1 코드 검증 결과 (`assets/stick_diagram.py` 실제 실행, PDF 재확인 후)

**결과 0 — pptx 원본(zip 안 XML, `ppt/slides/slide6.xml`)의 각 텍스트 상자 좌표를 직접 파싱해
`check_euler_condition()`으로 재검증한 결과, p.37 연습문제의 실제 정답과 완전히 일치했다.**
4개 행의 실제 node 시퀀스:

```
top(MP/M3/M4/M5/M6):  2 3 2 3 2 3 2 1 5 1 4 1 5 1 5 6 5 6 5 6 5
mid 행A(M1/M2):        7 5 7 2 7 5 7 2 7 5 7 2 7 5 7 2 7 5 7 2 7
mid 행B(M1/M2):        7 2 7 5 7 2 7 5 7 2 7 5 7 2 7 5 7 2 7 5 7
bottom(M7~M11,MN):     3 8 3 8 3 8 0 7 0 10 0 8 0 9 0 10 6 10 6 10 6
```

이 4개 시퀀스를 트랜지스터 이름과 무관하게(각 hop을 그냥 익명 edge로 취급) 그대로
`build_graph()` + `check_euler_condition()`에 넣은 결과:

```
top   : 홀수 노드=['2','5'], kind=path   → 실제 시퀀스도 2에서 시작해 5에서 끝남 (일치)
mid A : 홀수 노드=[],        kind=circuit → 실제 시퀀스도 7에서 시작해 7에서 끝남 (일치)
mid B : 홀수 노드=[],        kind=circuit → 실제 시퀀스도 7에서 시작해 7에서 끝남 (일치)
bottom: 홀수 노드=['3','6'], kind=path   → 실제 시퀀스도 3에서 시작해 6에서 끝남 (일치)
```

4개 행 전부, 코드가 예측한 시작/끝 노드가 Maloberti 원문이 실제로 채택한 시작/끝 노드와
정확히 일치했다 — 원저자가 실제로 출판한 해답과 코드의 독립적 계산이 정확히 맞아떨어진 것이다.

**트랜지스터별 정확한 source/drain도 확정했다.** `ppt/slides/slide5.xml`의 텍스트 도형을
좌표까지 파싱해보니, top 행의 M3/M4/MP 구간 finger 순서는 슬라이드에 실제로 존재하는 별도
텍스트 도형 **`433PP443`**(4,3,3,P,P,4,4,3 — M4=3, M3=3, MP=2와 정확히 일치)였다. 이
finger-순서 문자열과 p.37 정답 node 시퀀스를 위치별로 대조해 13개 소자 전부의 net-pair를
역산했고, `assets/stick_diagram.py`의 **`folded_cascode_example()`**로 코드화했다:

| 소자 | source | drain | 비고 |
|---|---|---|---|
| MP | vdd | tail | 확정(2 finger, {vdd,tail} 100% 일관) |
| M3 | vdd | X | finger 하나가 net-pair 불일치를 보였으나(원본 오탈자로 추정), M3.drain≠M4.drain(별개 folding node로 가야 함)이라는 회로이론 제약으로 확정 |
| M4 | vdd | Y | 위와 동일 |
| M5 | X | outA | 확정(6 finger, {X,outA} 100% 일관) |
| M6 | Y | outB | 확정(6 finger, {Y,outB} 100% 일관) |
| M1 | tail | X | 확정(10 finger) |
| M2 | tail | Y | 확정(10 finger) |
| M9 | gnd | X | 확정(3 finger, {gnd,X} 100% 일관) — 이름과 달리 M9가 전류원, M7이 cascode임에 주의 |
| M10 | gnd | Y | 확정(3 finger, {gnd,Y} 100% 일관) |
| M7 | X | outA | 확정(5 finger, {X,outA} 100% 일관) |
| M8 | Y | outB | 확정(5 finger, {Y,outB} 100% 일관) |
| M11 | gnd | vb1 | 확정(2 finger, bias 생성용) |
| MN | gnd | vb2 | 확정(2 finger, bias 생성용) |

`stick_diagram.py`의 self-test **Test 4**가 이 넷리스트를 실제로 돌려 top/mid/bottom 3개
stack 전부의 홀수차수 노드 집합이 pptx 정답과 정확히 일치하는지 자동 검증한다(현재 3/3 일치).

**결과 1 — finger 폭 정합성 검사(`check_finger_width_compatibility()`)가 PDF의 실제 조정
이유를 정확히 재현했다**:

```
BEFORE: M7 W=38.0um / finger_w=8.0um -> ratio=4.7500 (정수 아님). 가능한 값: 32.0um 또는 40.0um
BEFORE: M9 W=25.0um / finger_w=8.0um -> ratio=3.1250 (정수 아님). 가능한 값: 24.0um 또는 32.0um
AFTER : 모든 소자의 W가 finger_w의 정수배 (OK)
```

PDF가 실제로 선택한 값(40, 24)이 코드가 제시한 두 후보 중 하나와 정확히 일치한다 — "40µm
또는 32µm 중 하나를 고르라"는 후보 자체가 "8µm finger 폭에서 정수 개수가 되는 가장 가까운
두 값"이라는 같은 산수에서 나오기 때문이다.

**결과 2 — 이 사례의 진짜 원인은 Euler 패리티가 아니라 "finger 수가 정수여야 한다"는 더
근본적인 제약이었다**: `n_fingers`를 `round(W/finger_w)`로 대충 반올림해서 오일러 분석만
돌리면, `round(38/8)=5`와 `round(40/8)=5`가 **똑같아서** 조정 전후 그래프가 구분되지 않는다
(M9/M10도 `round(25/8)=round(24/8)=3`으로 동일). 실제로 top/mid/bottom 세 stack 모두 조정
전후 상관없이 정상적인 오일러 경로/회로였다(top: pA↔pB 경로, mid: 닫힌 회로, bottom: outA↔outB
경로 — M11=MN=2개(짝수)라 vb1/vb2도 짝수차수라 홀수 노드에 걸리지 않는다). 즉 **이 PDF
예제가 실제로 보여주는 것은 "finger 폭의 정수배 여부"라는, 오일러 조건보다 먼저 통과해야 하는
더 기초적인 검사(§3.5)**였다 — Euler 패리티 문제(§3의 M1/M2/M3 예제, `stick_diagram.py`의
Test 2 홀수노드-4개 시나리오)는 별도로 실재하는 실패 모드이지만, 이 특정 수치 예제가 실제로
부딪힌 문제는 아니었다. 두 검사는 서로 다른 계층의 제약이라 `build_stick_diagram()` 이전에
`check_finger_width_compatibility()`를 먼저 통과시키는 순서로 쓴다(§9).

## 7. Worked example — 2-Stage OTA (PDF p.28~p.33)

같은 루프를 더 단순한 회로로 보여주는 예제. p.28~p.33을 원본 이미지로 직접 확인했다 —
folded cascode 때와 달리 이 예제는 스키매틱에 **모든 net 이름
(VDD, D3, O1, CS, OUT, GND)이 명시적으로 라벨링**돼 있어 node 연결 추론이 전혀 필요 없었다.

- **p.28 "Example 1 (2 stages OTA)" — 원 회로 W(µm), 확인됨**: `M3=30, M4=30, M1=60, M2=60,
  M6=108, M7=72, M5=40` (Miller 2단 OTA: M1/M2 NMOS 입력쌍 + M3/M4 PMOS 미러 부하(1단),
  M6 PMOS 공통소스 + M7 NMOS 부하(2단), M5=tail, M5·M7 게이트 공유).
- **p.29 "Layout Oriented Design" — stack 그룹핑, 확인됨**: top(M3,M4,M6) / mid(M1,M2) /
  bottom(M5,M7) 3-stack, "for M3 and M4 use 2 fingers"(명시) + "같은 stack당 같은 finger
  수(k)"라는 지침.
- **p.30/p.31(pptx slide 3) — 실제 finger 수, 확인됨**: `M3=2, M4=2, M6=8, M1=6, M2=6,
  M5=4, M7=8` — 세 stack 모두 총 12 finger로 균등(k=12).

⚠️ **p.29 본문("change the size of M6 and M7 to 80 and 120 respectively")을 문자 그대로
읽으면 M6→80, M7→120이지만, 이는 finger 수와 모순된다.** M3/M4가 2 fingers로 고정되어
top stack의 unit cell 폭은 30µm/2=**15µm/finger**로 확정된다 — 이 폭에서 M6가 그림대로
8 fingers이려면 8×15=**120µm**이어야 한다(80µm이면 80/15=5.33으로 §3.5 정수배 조건을
어긴다). 마찬가지로 M5=40µm/4finger=**10µm/finger**로 bottom stack 폭이 확정되고, M7이
8 fingers이려면 8×10=**80µm**이어야 한다(120µm이면 120/10=12로 그림의 8과 안 맞는다).
즉 **실제로는 M6→120µm, M7→80µm이 맞다** — 본문 문장의 "80과 120" 순서가 M6/M7과 반대로
적힌 것으로 보인다(§6.1에서 발견한 M3/M4 사례와 같은 종류의 원문 오탈자로 추정).

**코드 검증**(`assets/stick_diagram.py`의 `two_stage_ota_example()`, self-test Test 8):
위 확정값(net 이름·W·finger 수 전부 원본에서 직접 읽음)을 그대로 넣어 돌리면 **top/mid/bottom
3개 stack 전부 홀수차수 노드 0개 — 완전한 닫힌 회로**로 나온다. 이는 p.31 "Use of one Metal
Layer"(단일 metal layer로 교차 없이 배선 완성)이 성공한 이유를 정확히 설명한다 — 애초에
한붓그리기가 막힘없이 가능한 구조였기 때문에 단일 layer로도 충분했던 것이다(p.30의 "First
attempt... not completed"는 finger 순서/배선 시도가 미완성이었을 뿐, 그래프 자체는 처음부터
문제가 없었다).

**연습문제(p.32)**가 §5 피드백을 직접 요구한다 — 3가지 대안을 비교시킨다: (a) M6/M7의 finger
그룹 방식만 바꾸는 안, (b) **M6=90, M7=60**으로 재조정하는 안(주의: 이것도 unit cell
15µm/10µm 기준으로는 90/15=6, 60/10=6 fingers가 되어 원래의 k=12 균등 배분이 깨진다 —
"여러 조정 후보 중 스펙을 지키면서 stack이 가장 잘 맞는 조합을 고른다"는 §5의 판단이 실제로
필요해지는 지점이다), (c) M1·M2를 common-centroid로 묶는 안(§2.5.2).

## 8. Cell shape(정사각형) 판단 기준

> **역사적 배경(2026-08 세션31 "CR" 재설계)**: `check_box_shape()`는 원래 각 행의
> `n_fingers`(finger **개수**)만 비교했다 — `finger_w`(finger 폭)와 `l`(채널 길이)는 전혀
> 안 봤다. 실측(2단 Miller OTA, W가 94배 벌어지는 스펙트럼)으로 이 함정이 드러났다: 6개 행
> 전부 finger 개수가 6~12로 균일해 `max_ratio=1.00 PASS`였는데, 실제 물리적 행 길이는
> `n_fingers*finger_w`로 직접 계산하면 2.63µm~246.24µm로 **94배** 차이가 났다 — PASS 자체가
> 물리적으로 무의미했던 것이다. 세션31이 `Transistor.l` 필드 + `PROCESS_GEOMETRY`/`pitch(l)`/
> `RowGeometry`/`compute_row_geometry(rows)`(`assets/stick_diagram.py:6389-6457`)를 신설해
> 이 함정을 엔진 레벨에서 근본적으로 없앴다 — 아래 §8.1~§8.5, 그리고 현재
> `check_box_shape(rows, row_width_tol=1.5, max_elongation=None, orientation="either")`
> (`assets/stick_diagram.py:6475`)의 시그니처와 서술은 전부 이 **재설계 이후** 상태를
> 반영한다. `rectangular`(행 폭 일치, 옛 `max_ratio`의 실질적 역할)와 `elongation_ok`(전체
> 길이 제한, opt-in)를 명시적으로 분리한 것도 이 재설계의 일부다 — 부수 효과로, PMOS/NMOS를
> 2개 super-block으로 묶는 well-merging 그룹핑(문헌 근거: Xiao/Young/He/Pun, CUHK,
> "Practical Placement and Routing Techniques for Analog Circuit Designs" §IV.C)만으로
> `aspect_ratio` 1.008→1.223/`packing_density`=0.775로 즉시 개선된 사례도 이 세션에서 확인됨
> (row_split 추가 조정 없이).

- 목표: 모든 stack의 finger 개수를 비슷하게 맞춰 **stack 높이 × stack 폭이 1:1에 가깝게**
  만든다(극단적으로 긴 직사각형은 실제 칩 floorplan에서 배치 효율이 떨어지고 배선도 길어짐,
  더 심한 경우 stack별 폭이 너무 다르면 여러 stack을 쌓았을 때 사각형이 아니라 계단/'ㄱ'자
  모양의 셀이 나와 실무에서 아예 쓸 수 없다 — 특수한 경우가 아니면 항상 피해야 한다).

### 8.1 핵심 자유도 — "finger_w(unit cell)는 stack마다 달라도 된다"

§3.5/§4가 요구하는 finger_w 균일성은 **같은 stack(같은 물리적 행) 안에서만** 성립한다.
서로 다른 stack(예: NMOS 단 vs PMOS 단, 또는 folded cascode의 top/mid/bot tier)은 **서로 다른
unit cell(finger_w)을 써도 무방하다** — 오히려 이 자유도가 §8의 실제 실행 수단이다. 실제
PDF의 folded cascode 예제도 tier마다 다른 finger_w(top: M3/M4/MP=10µm, M5/M6도 top 안에
있지만 같은 10µm 계열, mid: M1/M2=8µm, bot: M7~MN=8µm — tier 간 폭이 다름)를 쓰고 있고,
folded cascode의 "555555344PP334666666 / 433PP443 / 1122... / 777779xxoo99nno88888" 같은
숫자·문자 라벨 그리드 자체가 **"어떻게 나누면 각 행이 서로 맞아떨어지는가"를 숫자로 먼저
탐색해본 결과물**이다 — 이 탐색 과정 없이 그냥 사이징된 대로 한 행씩 그리면(총 W가 크게
다른 stack일수록) box가 안 나온다는 게 실전 관찰이다.

### 8.2 탐색 절차 (코드화됨 — `search_stack_finger_w()`)

1. 각 stack의 총 W(gm/ID sizing 결과, 소자별)를 모은다.
2. 기준이 될 stack(보통 finger 개수가 가장 적어 문제가 되는 쪽, 혹은 이미 확정된 다른
   제약이 있는 쪽)의 실제 finger 개수를 `target_row_fingers`로 잡는다.
3. 나머지 stack마다 `search_stack_finger_w(devices, target_row_fingers)`를 호출해 그
   stack의 총 finger 수가 target에 가장 가까워지는 finger_w 후보를 탐색한다 — 반환되는
   `BoxLayoutCandidate.finger_w`가 그 stack에 쓸 unit cell 폭, `total_row_fingers`가 실제
   행 길이다.
4. 여러 stack의 `total_row_fingers`가 서로 충분히 가까우면(이상적으로는 정확히 같으면)
   채택 — 아니면 2)의 기준을 바꿔 다시 탐색하거나, 그래도 안 맞으면 pptx slide 5의 차동쌍
   예처럼 **큰 stack을 2개 이상의 물리적 행으로 쪼개는** 방법(§4)으로 넘어간다.
5. **`check_box_shape({행_이름: 실제_finger_개수, ...})`를 호출해 PASS를 확인한다** —
   이 호출을 건너뛰고 "충분히 가까운 것 같다"고 눈대중으로 넘어가지 말 것. `check_euler_condition()`
   과 동급의 필수 게이트이며, §10 Definition of Done의 순서(box-shape → §5 재검증 → freeze
   → SPICE)를 실제로 강제하는 지점이다.
6. **이 조정도 반드시 §5 스펙 재검증을 통과해야 확정된다** — "정사각형으로 만들기 위한
   조정"이 스펙 위반의 면죄부가 되지 않는다. **DON'T** 재검증과 freeze가 끝나기 전에는
   SPICE로 넘어가지 말 것 — 순서를 어기면 finger_w를 나중에 또 바꿔야 할 때 SPICE도 다시
   돌려야 하는 재작업이 생긴다.

### 8.3 함정 — finger_w가 LUT 기준폭에서 벗어나면 실측 전류가 어긋난다

gm/ID LUT는 보통 특정 기준폭(`W_ref`, 예: 5µm)에서 캘리브레이션되어 있다. §8.2의 탐색으로
box-shape에 맞는 finger_w(예: 20µm, 1.9µm)를 골랐다면, **그 finger_w에서 실제로 SPICE를
돌려 전류가 LUT 예측과 맞는지 반드시 재확인해야 한다** — 실측으로 확인된 사례(sky130,
Intrinsic Gain Stage 예제): 같은 총 W=80µm라도 finger_w=5µm에서는 46.2µA, finger_w=20µm
에서는 38.7µA로 **~16% 차이**가 났다(공정 모델의 폭 의존 항으로 추정, §12.3의 `nf=` 파라미터
버그와는 무관한 별개 현상). 대응 원칙:
- **Diode-connected 소자**(자기 게이트=드레인)는 SPICE가 스스로 그 finger_w에서 target
  전류를 내는 VSG를 재계산해주므로 별도 보정이 필요 없다.
- **독립적으로 바이어스되는 소자**(예: 차동단 게이트, gain 소자)는 LUT가 준 VGS를 그대로
  쓰면 전류가 어긋난다 — 실제 finger_w에서 target ID를 내는 VGS(혹은 필요하면 총 W)를
  SPICE로 다시 찾아야 한다(이분탐색 등). 이것도 §5 "sizing↔layout은 피드백 루프다"의 실제
  적용 사례다 — 박스 모양을 위해 finger_w를 바꿨다면 그 finger_w에서 다시 검증하라.

**실제 개선 사례(Intrinsic Gain Stage, sky130)**: 처음엔 두 stack 모두 finger_w=W_ref(5µm)로
고정해서 N단(M1)=3핑거, P단(M2+M2b)=32핑거로 10.7:1 불균형이 나왔다(스택을 쌓으면 'ㄱ'자
비정상 셀). `search_stack_finger_w()`로 P단 finger_w≈19.6µm(4+4=8핑거), N단
finger_w≈1.9µm(8핑거)를 탐색해 8:8 완전한 box로 바꿨고, M1의 게이트 바이어스를 SPICE
이분탐색으로 재보정한 뒤 다시 시뮬레이션한 결과 fT 스펙 오차는 0.44%→0.52%로 사실상 그대로
유지됐다 — box 모양과 스펙 충족을 동시에 만족시킬 수 있었다.

### 8.4 함정 — `check_box_shape()` PASS는 finger_w가 실제로 만들 수 있다는 뜻이 아니다

§8.2의 `search_stack_finger_w()`/`check_box_shape()`는 순수 **비율**(행 길이의 최대/최소)만
본다 — 그 비율을 만족시키기 위해 골라진 finger_w가 **PDK가 실제로 받아주는 폭인지는 전혀
검사하지 않는다.** 이 둘은 서로 다른 조건이고, 하나를 통과했다고 다른 하나가 자동으로
보장되지 않는다.

**실측으로 확인된 사례(Example 3, NGCC 3-stage, sky130)**: 3단 OTA의 gain 소자 3개 +
전류거울 부하쌍 3개, 총 6개 stack의 총 W가 4.2µm(M2)~627µm(load3, M3b/M3c 합)까지
150배 차이 났다. 공통 목표 행폭을 4로 잡으면 6개 stack 전부 `check_box_shape()` PASS
(비율 1.00)였지만, load3(M3b/M3c)의 finger_w가 156.8µm까지 커졌고 — **sky130 PMOS
서브서킷이 이 폭을 그냥 거부했다**(SPICE 시뮬레이터 인스턴스화 시점 실측 에러:
`could not find a valid modelname`). box-shape는 완벽했지만 그 layout은 애초에
만들 수 없는 것이었다.

**대응 원칙**:
- `check_box_shape()` PASS는 §10 체크리스트를 넘어가도 된다는 필요조건이지, **충분조건이
  아니다.** PASS 직후 반드시 그 finger_w로 SPICE 인스턴스화가 실제로 되는지 확인할 것
  (모델 로드 에러 여부 — §8.3의 "전류값이 맞는지" 확인보다 선행하는, 더 기초적인 체크다).
- 안전한 finger_w 상한은 공정/모델마다 다르므로 매 프로젝트 초반에 실측으로 확인해 두는 게
  좋다(sky130 실측 관찰로는 대략 수십 µm 이내가 안전했고, 150µm대는 실패했다 — 정확한
  경계값은 확인하지 않았으니 절대치로 인용하지 말 것).
- finger_w가 이 안전 범위를 넘는 stack이 나오면, §4에서 이미 쓰던 "큰 stack을 여러 물리
  행으로 쪼개는" 방법을 **box-shape 게이트 자체에도 그대로 적용**한다: 오일러 trail(배선
  순서)은 하나의 연속 그래프로 그대로 두고, 그 순서를 물리적으로 N등분해 N개 행에 나눠
  놓는다 — 재배선이 필요 없다(§2.5.6에서 확인한 대로 하나의 metal layer 배선 유효성은
  diffusion 연속성이 아니라 그래프의 오일러 조건에서 나오므로, 물리적으로 몇 개 행에
  나눠 그리든 그래프 자체는 바뀌지 않는다). 목표 행폭을 낮추는(예: 4→8) 동시에 큰 stack의
  분할 행 수를 늘리면(예: 1행→4행) 그 stack의 finger_w가 낮아진다.
  - Example 3의 실제 조정: 목표 행폭을 4→8로 올리고, load3(총 32핑거/소자)만 4개 물리
    행(행당 8)으로 분할 → finger_w 156.8µm → 19.6µm(안전 범위)로 낮아지고, 9개 물리 행
    전부 폭 8로 `check_box_shape()` PASS(비율 1.00) — 이번엔 SPICE 인스턴스화도 성공.

### 8.5 `check_box_shape()` FAIL을 최종으로 받아들이기 전에 — 분할 비용을 숫자로 보일 것

§8.2 step 4가 이미 "비율이 안 맞으면 큰 stack을 여러 물리 행으로 쪼개라"고 말하지만, 실전에서는
그 분할을 실제로 검토하지 않고 **"공정 특성(mobility 차이 등) 때문에 원래 이렇다"는 정성적
설명만으로 FAIL을 최종 결론으로 받아들이는** 일이 생긴다 — 이것도 "뒷부분 remedy를 건너뛰는"
익숙한 실패 패턴의 변종이다.

**실제 사례(telescopic OTA 재현)**: PMOS 물리 행(94~90핑거)과 NMOS 물리 행
(4~8핑거)의 비율이 23.5:1로 FAIL이 나왔고, 리포트는 "sky130 PMOS/NMOS mobility 차이로 W가
18~23배 벌어지는 게 진짜 원인"이라고 정확히 설명했다 — 여기까지는 맞다. 하지만 §8.2 step 4가
말하는 "물리 행을 더 쪼개면 비율이 내려간다"는 remedy를 실제로 계산해보지 않고 넘어갔다.
사후 확인해보니: 비율 1.5 이내로 맞추려면 NMOS 최대 행폭(8핑거)의 1.5배인 12핑거 이하로
PMOS 각 행을 쪼개야 하고, PMOS 그룹(90/94/94/40핑거)을 전부 이 기준으로 나누면 **PMOS만 최소
28개 물리 행**이 필요하다(현재 5개 대비). 이 정도 행 개수 폭증은 셀을 정사각형으로 만드는
원래 목적(§8 도입부: floorplan 효율)에 오히려 역행한다 — 그래서 FAIL을 받아들이는 게 맞는
결론이었지만, **그 결론에 도달하는 계산 자체는 리포트에 없었다.**

**규칙**: `check_box_shape()`가 FAIL을 반환했을 때, §8.2 step 4의 분할 remedy를 실제로 적용하지
않고 FAIL을 최종으로 받아들이기로 판단했다면, 그 판단의 근거로 **"비율 임계값(보통 1.5)을
만족시키려면 몇 개의 물리 행이 필요한지"를 실제로 계산해서 리포트/결정 추적에 남길 것** —
정성적 설명("공정 특성 때문")만으로 끝내지 않는다. 계산은 단순하다: `ceil(문제_stack의_총_핑거수
/ (다른_극성_최대_행폭 × max_ratio))`로 필요한 행 수를 구하고, 그 행 수가 실무적으로 감당 가능한
범위(대략 한 자릿수)인지 판단한다 — Example 3(NGCC)처럼 4행 정도로 해결되면 반드시 분할을
적용하고, 이번 사례처럼 20행 이상이 필요하면 그 숫자 자체가 "분할이 실익보다 비용이 크다"는
근거가 되어 FAIL을 받아들이는 결정을 정당화한다. 어느 쪽이든 **그 계산 결과 숫자를 결정
추적에 남겨야** 사후에 "왜 이 FAIL을 그냥 받아들였는가"를 재구성할 수 있다.

## 9. 코드 사용법 — `assets/stick_diagram.py`

이 스킬의 layout-단계 "결과물"은 이 코드를 실행해 얻는 stack별 stick diagram이다. 어떤 회로든
`Transistor` 리스트로 표현해 넘기면 된다:

```python
from stick_diagram import (
    Transistor, build_stick_diagram, render_stick_diagram,
    check_finger_width_compatibility, split_into_stacks,
    find_matching_candidates, search_unit_cell_sizing,
    find_hub_merge_candidates, check_multi_leaf_hub_parity,  # §4.1 — stage 경계 넘는 stack 병합 판단
    search_stack_finger_w,   # §8.2/Case A — stack별 box-shape finger_w 탐색(n_fingers 고정, 세로 스택)
    search_shared_finger_w,  # §4.2/Case B — 공통 finger_w 탐색(finger_w 고정, 가로 배치)
    check_box_shape,         # §8 게이트 — SPICE 검증 전 필수 PASS/FAIL 체크포인트
    common_centroid_layout,  # §2.7 — matching-critical 2D 배치(pattern_key로 표/그래프 경로 분기)
)

# gm/ID sizing이 끝난 상태의 트랜지스터를 그대로 옮겨 적는다.
# stack_id를 명시하지 않으면 (극성, finger_w)로 자동 그룹핑된다.
# w(전체 W)를 finger_w와 함께 주면 §3.5 divisibility 검사를 쓸 수 있다.
# gate를 채우면 §2.6 matching 그룹 자동 탐지를 쓸 수 있다(선택, Euler 분석엔 안 씀).
circuit = [
    Transistor("M1", "nmos", source="vin_p", drain="tail", gate="in_p", w=32, finger_w=2.0, n_fingers=4),
    Transistor("M2", "nmos", source="vin_n", drain="tail", gate="in_n", w=32, finger_w=2.0, n_fingers=4),
    Transistor("M3", "pmos", source="vdd",   drain="vin_p", gate="bias", w=18, finger_w=3.0, n_fingers=6),
    # ...
]

# 0단계(선택): matching이 필요한 그룹부터 찾는다(§2.6) — 차동쌍/전류거울 후보.
# 캐스코드 대칭쌍·R/C 비율은 구조적으로 탐지 안 되니 stack_id로 직접 표시할 것.
found = find_matching_candidates(circuit)

# 0.5단계(선택): nominal W가 unit cell 정수배가 아니면 후보부터 탐색(§5.5).
candidates = search_unit_cell_sizing(nominal_w=32.0, candidate_unit_widths=[2.0, 4.0])

# 1단계: finger 폭이 정수인지 먼저 확인 (§3.5) — 오일러 분석보다 선행해야 하는 게이트
for stack_id, group in split_into_stacks(circuit).items():
    verdict = check_finger_width_compatibility(group)
    for iss in verdict.issues:
        print(f"{iss.transistor}: W={iss.w} / finger_w={iss.finger_w} "
              f"-> 정수 아님, 후보: {iss.nearest_valid_w}")

# 2단계: 정합성 문제 없는 stack만 오일러 분석
for stack_id, result in build_stick_diagram(circuit).items():
    print(render_stick_diagram(result))
    if result.status == "blocked":
        # result.suggestions[0]이 가장 유력한 finger 조정 후보 —
        # 반드시 §5 체크리스트로 재검증한 뒤에만 채택할 것.
        ...
```

`build_stick_diagram()`은 stack마다 `StickResult`를 반환한다: `status="ok"`면
`node_sequence`/`transistor_sequence`가 실제 stick diagram(오일러 경로/회로)이고,
`status="blocked"`면 `odd_nodes`(원인 노드)와 `suggestions`(finger 조정 후보, §3(a))가 채워진다.
`check_finger_width_compatibility()`는 `w`/`finger_w`를 둘 다 지정한 소자 중 W가 finger_w의
정수배가 아닌 것을 찾아 `FingerWidthIssue`(정확한 비율, 가장 가까운 두 정수배 후보)로 반환한다
— §6.1에서 실제 PDF 예제(M7/M8, M9/M10)로 검증됨. `find_matching_candidates()`는 §2.6
카탈로그 중 구조적으로 탐지 가능한 전류거울/차동쌍 후보를 찾는다(오탐 가능성 있음 — §2.6
참고). `search_unit_cell_sizing()`은 §5.5의 unit cell 정수배 후보 생성기다.
self-test(2026-09-22 TS1 뒤로는 `assets/tests/legacy/selftest_stick_diagram.py` -- 실행법은 `assets/tests/README.md`) 15종(Test 1a/1b: 직렬 체인의 open path/closed circuit
차이, Test 2: 홀수 노드 4개 detection+조정 제안, Test 3: 극성별 자동 stack 분리, Test 4:
folded cascode 실제 넷리스트 검증(§6.1), Test 5: 축대칭 검증(§2.5.3), Test 6: matching 그룹
탐지(§2.6), Test 7: unit cell 후보 탐색(§5.5), Test 8: 2-stage OTA 실제 넷리스트 검증(§7),
Test 9: 홀수개 매칭쌍 교차대칭(§2.5.4), Test 10: box-shape finger_w 탐색 —
Intrinsic Gain Stage 예제로 3:32 불균형을 8:8로 맞추는 실제 사례(§8), Test 11: 2D
common-centroid(짝수 개수) — 같은 예제의 M2/M2b 전류거울을 1-unit point-symmetric 배치로
개선하는 사례(§2.7), Test 12: `common_centroid_layout()`(홀수 개수 지원, `Transistor`
리스트 입력, `method=="rotation_exact"` 단언) — Walker 차동쌍(M1/M2, 9:9)을 각 행에 대해
`build_graph()`+`hierholzer()`로 실제 계산하고(손으로 섞은 패턴이 아님), 두 행이 서로
다른지·1차 원리로 인접 finger가 공유 net을 갖는 유효한 경로인지·M1/M2 열 평균이 상쇄되는지를
모두 재확인하는 사례, Test 12.5: 대칭(1:1) 케이스에서 표 경로(`method="pattern_table"`)와
회전 경로(`method="rotation_exact"`)가 실제로 같은 패턴을 내는지, 2:1 비율 케이스에서
표 경로 흡수 후 잔차가 정확히 0(구 탐색 경로의 잘못된 잔차 0.75와 대조)인지 검증, Test
12.6/12.11: `interdigitate_layout()`(표 기반/탐색+crossover 경로 모두 반환 스키마·예외
없음까지 self-test로 확인) 검증, Test 13:
`check_box_shape()` 게이트 — Example 1/2의 실제 최초 실수(10.7:1, 4.2:1
불균형)를 FAIL로, §8로 고친 뒤(1:1)를 PASS로 정확히 구분하는 사례, Test 14: stage 경계를
넘는 stack 병합(§4.1) — `check_multi_leaf_hub_parity()` 공식이 3-leaf 조합 64개 전수에서
`build_graph()`+`check_euler_condition()`과 항상 일치함을 확인, `find_hub_merge_candidates()`가
stack_id로 이미 다른 stage에 분리해 둔 M3/M4/M6를 hub=vdd 공유만으로 다시 찾아내는지 확인,
Maloberti p.29 예제를 짝수 k=8(가능)/홀수 k=7(불가능)로 실제 재현, Test 15:
`search_shared_finger_w()`(§4.2, Case B) — Example 3의 실제 9개 소자로 정직하게 검증한
결과 schematic이 가로로 흐르는데도 Case B가 수학적으로 안 맞음(131:1 행폭 비율 또는
426% 스냅 오차)을 확인, 실제로 채택한 Case A가 옳았음을 사후 검증)을 바로 확인할 수 있다.

## 9.5 row_split 재시도는 gm/ID 그리드서치와 분리된 별도 루프여야 한다 — 재계산 효율

**사용자 원문(세션31→32 전환 계기)**: "sizing하는 것과 layout shape 맞추는 것은 별개의
작업이잖아... 오로지 전기적 특성에 영향을 줄 수 있을 때만 optimize로 다시 최적화하고 layout
iteration을 돌려야 해."

**증상**: `current_reuse_telescopic_ota`(51소자, 자유 theta 13개)가 §8 box-shape 자동조정을
위해 `optimize_full_circuit_budget()`(gm/ID 그리드서치 전체 — 이 파이프라인에서 가장 비싼
부분)을 row_split 재시도 매 라운드마다 처음부터 다시 호출해, 10분+ 무응답이 발생했다.

**해법**: euler-fixup/matching-safety repair(핑거증가가 실제 gm/ID 재검증을 요구하는,
전기적으로 유의미한 루프)는 그대로 안쪽에 두되, **row_split 적용만** baseline 결과에서 매번
새로 시작하는 얇은 클로저(`_evaluate_row_split()`)로 분리한다 — theta 그리드서치는 전혀
재실행하지 않는다. `floorplan_target`이 있으면:
- `_pick_split_target()` — `floorplan.row_split_candidates` 중 diffusion-safe(`splittable=True`)
  하면서 가장 지배적인(`value/bbox` 비율이 큰) 후보를 고른다.
- `_score_floorplan()` — `floorplan_target`(`max_aspect_ratio`/`min_packing_density`) 대비
  얼마나 못 미치는지를 상대오차 합산으로 스칼라화해, 라운드끼리 "개선됐는지"를 비교한다.
- 한 stack을 골랐으면 `max_split_per_stack`까지 계속 밀어붙이다, 그래도 개선이 없으면
  그때만 포기(`excluded`)하고 다음 후보로 넘어가는 **backtracking** 루프.

**일반 원칙**: 재시도 루프를 설계할 때는 "이번 재시도가 정말 비용이 큰 부분(여기서는 gm/ID
그리드서치)까지 다시 계산해야 하는가"를 항상 먼저 물을 것 — 전기적 재계산이 필요 없는 순수
기하학적 조정(row_split)은 baseline 결과 위에서 독립적으로 반복해야 한다.

## 10. Definition of Done (Layout 단계 체크리스트)

**순서가 중요하다** — 아래 체크리스트는 위에서부터 순서대로 통과해야 한다. 특히
**box-shape 게이트(§8)는 SPICE 재검증보다 먼저** 와야 한다 — 순서를 어기고 SPICE부터
돌리면, box-shape 문제가 나중에 발견될 때마다 finger_w를 다시 잡고 SPICE도 다시 돌려야
하는 재작업이 생긴다.

⚠️⚠️ **DO** 아래 항목을 전부 예외 없이, 순서대로, 각 항목의 실제 검증 근거(함수 호출 결과)를
남기며 통과할 것. **DON'T** 일부 항목(예: Euler trail·box-shape)만 통과시키고 나머지(예:
§4.1 stage-merge 확인, matching-symmetry 검증)를 생략한 채 충분하다고 넘어가지 말 것 —
앞쪽 항목 통과가 뒤쪽 항목의 필요성을 줄이지 않는다. 매 항목에 대해 "이 항목을 검증한 실제
함수 호출과 그 결과"를 리포트/작업 기록에 명시적으로 남길 것 — "이미 다른 걸 확인했으니 이건
괜찮을 것"이라는 추정으로 항목을 비워두지 말 것.

- [ ] Matching이 필요한 소자 그룹(차동쌍/전류거울/캐스코드쌍/R·C비율 등, §2.6 카탈로그)을
      전부 식별했는가? `find_matching_candidates()`가 찾은 후보를 그대로 믿지 않고 오탐
      (§2.6의 M11/MN 사례)을 걸러냈는가?
- [ ] **stack_id를 배정하기 전에 `find_hub_merge_candidates()`(§4.1)를 회로 전체(여러
      stage/circuit을 합친 전체 소자 목록)에 대해 먼저 돌렸는가?** — stage별로 먼저 나눠
      생각하고 시작하면 이 탐지 자체가 성립하지 않는다(§4.1 도입부). 후보가 나오면
      `check_multi_leaf_hub_parity()`(leaf≥3일 때)와 `search_shared_finger_w()`로 실제
      실현 가능성과 스냅 오차를 확인했는가? 실현 가능해도 "병합 가능 ≠ 병합해야 함"(§4.1
      결정 순서 4번) — 행 개수 감소의 이득과 stage 간 diffusion 공유가 만드는 노이즈 커플링
      우려를 저울질해 채택/거부 근거를 남겼는가? **DON'T** 병합 후보 탐색 자체를 생략하지
      말 것 — 최종적으로 isolation 우려로 거부하더라도, "후보가 있는지조차 확인 안 함"과
      "확인 후 근거 있게 거부함"은 전혀 다르다.
- [ ] 모든 트랜지스터가 stack(행)에 배정되었는가(§4, 위 병합 판단을 반영해서)?
- [ ] W가 그 stack의 finger 폭의 정수배인가(§3.5)? 아니면 오일러 분석 이전에 먼저 조정했는가?
- [ ] 각 stack의 그래프 차수 분석 결과 홀수 노드가 0개 또는 2개인가(§3, `check_euler_condition()`)?
      아니라면 §3(a/b/c) 중 하나로 해소했는가?
- [ ] **`check_box_shape()` 게이트를 호출해 PASS를 받았는가(§8)?** — row_widths에 실제
      물리적 행(common-centroid로 나눴다면 행별로 각각) 폭을 넣어 확인한다. FAIL이면
      `search_stack_finger_w()`(§8)나 `common_centroid_layout()`
      (§2.7, matching-critical 그룹만)로 finger_w·행 구성을 다시 정하고, **이 항목을
      다시 통과할 때까지 아래 항목으로 넘어가지 않는다.**
- [ ] **FAIL을 정성적 설명("공정 특성 때문")만으로 최종 결론 삼지 않았는가(§8.5)?** —
      §8.2 step 4의 물리 행 분할 remedy를 실제로 적용하지 않기로 했다면, 비율 임계값을
      만족시키는 데 필요한 물리 행 개수를 계산해서(`ceil(총_핑거수 / (다른 극성 최대 행폭 ×
      max_ratio))`) 결정 추적에 남겼는가 — 이 숫자가 실무적으로 감당 가능한 범위(대략 한
      자릿수)면 실제로 분할을 적용하고, 그렇지 않다면(예: 20행 이상) 그 숫자 자체를 FAIL을
      받아들이는 근거로 제시했는가?
- [ ] **그 PASS를 만든 finger_w가 PDK에서 실제로 인스턴스화되는가(§8.4)?** — 비율만 맞고
      finger_w가 PDK 유효범위를 벗어나면(sky130 실측 사례: 156.8µm 폭에서 모델 로드 자체가
      실패) `check_box_shape()` PASS는 무의미하다. 큰 stack이 있다면 SPICE로 그 finger_w를
      실제로 인스턴스화해 에러가 없는지 먼저 확인하고, 실패하면 목표 행폭을 낮추고/분할 행
      수를 늘려(§8.4) finger_w를 안전 범위로 내린 뒤 위 항목부터 다시 통과시킨다.
- [ ] 그 그룹마다 interdigitation(§2.5.1) 또는 common-centroid(§2.5.2/§2.7) 패턴을
      적용했는가 — 임의 배치가 아니라 축대칭(§2.5.3) 규칙을 만족하는가? 1행으로 충분한
      그룹(단순 미러)과 다행(多行) 배치가 필요한 그룹(차동쌍/DAC·ADC 다수 unit 등, §2.7.2
      결정 기준)을 구분했는가? **후자는 floorplan 제약이 없다면 `n_rows`를 지정하지 말고
      `common_centroid_layout()`의 기본값(N행, 잔차 0)을 그대로 쓸 것** — row 개수를
      2 등으로 임의로 제한하지 않는다(§2.7.2 기본 원칙). (§2.7.2: 다행 배치도 각 행이
      여전히 1개 metal layer, 진짜 오일러 trail이다 — 추가 layer가 필요한 게 아니다.)
- [ ] **표준 패턴표(§2.5.1/§2.5.2)가 이 소자 개수 조합에 맞지 않는다면**(홀수 등), 대충
      나누고 넘어가지 않고 원리(대칭 + 최대한 섞기, §2.5 도입부 경고문 + §2.5.4)로 직접
      구성했는가 — `build_mirror_symmetric_pattern()`/`find_interleaved_symmetric_splits()`
      /`common_centroid_layout()`로 만든 배치가 실제로 대칭(`check_mirror_symmetry()`)과
      매칭 품질(가장 고르게 섞인 후보)을 둘 다 만족하는지 확인했는가?
- [ ] finger 수/W 조정(box-shape 게이트 통과를 위한 것 포함)이 있었다면, **조정 후 W로
      gm/ID 검증 체크리스트를 재실행**했는가(§5)? finger_w가 LUT 기준폭(W_ref)에서
      벗어났다면 §8.3처럼 SPICE 실측으로 전류 편차를 재확인했는가? 재검증 없이 사이즈만
      바꾸고 넘어간 항목이 있는가 — 있다면 안 된다.
- [ ] 재검증을 통과한 W를 **freeze**하고 그 이후 사이징을 재론하지 않았는가(§1의 루프 종료
      조건)?
- [ ] **리포트/문서에 stick diagram을 옮겨 적을 때, `build_stick_diagram()`이 실제로
      반환한 `transistor_sequence`/`node_sequence`/`odd_nodes`/`status`를 그대로 썼는가 —
      손으로 축약하거나 "대표 패턴"으로 재구성하지 않았는가?** 실제 사고 사례는
      known-incidents.md 사고1 참고(SKILL.md §6도 참조) — 함수 호출 결과를 그대로
      직렬화할 것, 길다는 이유로 축약하지 말 것.
- [ ] 각 stack의 finger 순서(stick sequence)가 실제로 오일러 경로/회로 조건을 만족하는가?
- [ ] Metal interconnection이 같은 one-stroke 원칙으로 교차 최소화되었는가(§6 p.37 예제
      방식)?
- [ ] Well/substrate bias, I/O 연결 레이어 공간을 stick diagram 단계에서 미리 확보했는가
      (PDF p.33, p.38 체크리스트)?
