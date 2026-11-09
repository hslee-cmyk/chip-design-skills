# B26 결정 자료: D1 레일 극성, D2 MNA 고정 노드

기준: master `cd64170`. 저장소는 읽기만 했다. 실측은 `C:/g26`에 저장소 사본을 떠서 했고 끝난 뒤 지웠다.
선행 조사: `_drafts/prep_b26_supply_nets.md`(아래에서는 "prep"). 이 문서는 그 §4의 D1·D2를 결정하는 데 필요한 것만 담는다.

**한 줄 요약**
- **D1(권고)**: 구조 규칙을 기본으로 쓴다. 그리고 DEC-61 `bulk`와 같은 방식으로 **예외 회로만 적는 선택 필드** `supply_roles`를 둔다. 규칙이 판정하지 못하는 회로는 로드 게이트가 거부한다. 지금 library 9회로는 모두 규칙으로 판정되므로 파일 수정은 0건이다.
- **D2(권고)**: 선언된 레일 전부를 교류접지로 둔다(선택지 (i)). 이상적인 전원을 두고 하는 소신호 해석에서는 이것이 물리적으로 맞다. 지금 값이 바뀌는 것은 current_reuse `cmrr_estimate_db` 하나뿐이다(+0.235 dB, 제약 ≥ 60 dB와의 여유 13 dB, 값이 커지는 쪽이라 제약이 완화된다).
- **prep 정정 1건**: prep §2.4의 "중앙점 theta에서 73.145 → 73.380"은 실제로는 **정본 θ\***(`tests/canonical_theta_star.json`) 값이다. 보조 함수는 회로의 theta 이름이 θ\* 파일에 전부 있으면 θ\*를 쓰는데, current_reuse는 22개가 모두 있다. 진짜 bounds 중앙점은 current_reuse에서 `InfeasibleSizingError`로 거부된다(§3.3).

---

## 1. D1: 레일 극성(높은 레일, 낮은 레일)을 어떻게 정하나

### 1.1 극성이 왜 필요한가

레일 **집합**만 있으면 되는 곳이 대부분이다(prep §3.2 A군). 어느 쪽이 높은 레일이고 어느 쪽이 낮은 레일인지까지 알아야 하는 곳은 아래뿐이다.
- 기둥(가지) 추적의 시작과 끝: `trace_vdd_to_gnd_branches`, `trace_gnd_to_vdd_branches`, 방향 라벨을 비교하는 함수 3개. 이 추적은 topology를 로드할 때 돌고, 그 시점에는 spec이 없어 `supplies_v`를 읽을 수 없다.
- `propagate_node_voltages`(DC 노드전압 시작점), `_metric_supply_current`(높은 레일 전류), `_metric_rail_referenced_voltage`, `_metric_battery_centering_deviation`.
- (계획 DEC-61) bulk 기본값: nmos는 가장 낮은 전위의 레일, pmos는 가장 높은 전위의 레일. 계획은 이것을 `supplies_v`의 **전압 순서**로 정의한다. spec이 있으면 전압이 극성의 정본이라는 뜻이다. D1이 다루는 것은 **spec이 없는 로드 시점**의 극성이다.

### 1.2 library 9회로: 선언과 구조 규칙 결과

구조 규칙은 이렇다. 선언된 레일이 PMOS source로만 나오면 hi, NMOS source로만 나오면 lo, 어느 쪽 source로도 나오지 않으면 mid, 양쪽 source로 모두 나오면 CONFLICT(거부).
bulk는 9회로 모두 선언하지 않았다(`netlist[].bulk` 필드 0건). 그래서 DEC-61 기본 규칙(pmos는 최고 전위, nmos는 최저 전위)이 적용되고, bulk는 규칙의 증거로 쓸 데이터가 없다.

| 회로 | `supply_nets` | 규칙 결과 | 근거: PMOS source / NMOS source | 규칙이 보지 않는 그 밖의 레일 단자 | 판정 |
|---|---|---|---|---|---|
| common_gate_amplifier | vdd, gnd | vdd=hi, gnd=lo | vdd: M3 / gnd: M1 | 없음 | 명확 |
| current_reuse_telescopic_ota | vdd, gnd | vdd=hi, gnd=lo | vdd: PMOS 16개(M6, M7, M8, M11a, M15, M13, M22, M20a, M25, M17, M18_bg, M60, M61, M36a, M36b, M39) / gnd: NMOS 12개(M5, M12, M10, M14b, M16, M21, M19, M24b, M26, M66, M68, M38) | gnd: **PMOS M40의 drain·gate**(source=Voc_des, 다이오드 연결), Iref, CL1, CL2, Cs1, Cs2 | 명확. M40은 PMOS가 낮은 레일에 붙은 경우지만 source가 아니라서 규칙이 흔들리지 않는다 |
| folded_cascode | vdd, gnd | vdd=hi, gnd=lo | MP, M3, M4 / M9, M10, M11, MN | 없음 | 명확 |
| ngcc_3stage_ff | vdd, gnd | vdd=hi, gnd=lo | M0, M5, M9, M10, M12 / M3, M4, M6A, M6B, M7, M8, M11, M13, M14 | gnd: CL | 명확 |
| nmcnr_amplifier | vdd, vss | vdd=hi, vss=lo | M101, M108, M109, M201, M202, M302 / M104, M105, M203, M204, M301 | 없음 | 명확. 이름 규칙(`"gnd"` 짝)으로는 lo가 없던 회로다 |
| pushpull_follower_buffer | vdd, vss, agnd | vdd=hi, vss=lo, agnd=mid | M5 / M6 | vdd: **NMOS M1, M4의 drain**(follower), vss: **PMOS M2, M3의 drain**, agnd: CL만 | 명확. follower가 반대 극성 레일에 drain으로 붙어도 규칙은 source만 본다 |
| sf_pushpull_output_opamp | vdd, vss, agnd | vdd=hi, vss=lo, agnd=mid | M6, M8, M11, M9, M17 / M3, M4, M14, M16, M20 | vdd: NMOS M19, M22의 drain, IBias / vss: PMOS M18, M21의 drain / agnd: Cc, CL | 명확 |
| two_stage_ota | vdd, gnd | vdd=hi, gnd=lo | M3, M4, M6 / M5, M7 | 없음 | 명확 |
| two_stage_ota_sf | vdd, gnd | vdd=hi, gnd=lo | M3, M4, M6 / M5, M7, M9 | vdd: NMOS M8의 drain(follower), gnd: CL | 명확 |

결과: **9/9에서 CONFLICT가 0건이고, hi와 lo가 각각 정확히 하나씩 나온다.** mid는 agnd 두 건뿐이며, 둘 다 커패시터 단자에만 나온다. 이 결과는 소자 이름이나 레일 이름을 전혀 보지 않고 얻은 것이다.

### 1.3 규칙이 깨지는 가상 topology 4개

아래 결과는 같은 규칙 코드로 실제로 돌려 얻었다(`C:/g26/hypo.py`, 삭제함).

**H1. NMOS만 있는 저항 부하 CS 증폭기** (vdd가 저항에만 붙음). 교과서에서 흔한 회로다.
```json
"supply_nets": ["vdd", "gnd"],
"netlist": [{"name": "M1", "kind": "nmos", "source": "gnd", "drain": "vout", "gate": "vin"}],
"passive_elements": [{"name": "RD", "kind": "resistor", "terminals": ["vdd", "vout"]}]
```
결과: `vdd = mid`, `gnd = lo`. hi 레일이 없다. "hi와 lo가 각각 하나 이상" 게이트를 두면 **거부로 드러난다**(조용한 오답은 아니다). 모든 소자가 PMOS이고 부하 저항이 gnd에 붙은 회로에서는 반대로 lo가 없다.

**H2. 적층 전원 도메인(current-reuse 적층, 3레일)**. 가운데 레일이 위 도메인에는 NMOS source, 아래 도메인에는 PMOS source로 쓰인다.
```json
"supply_nets": ["vdd", "vmid", "vss"],
"netlist": [
  {"name": "MP1", "kind": "pmos", "source": "vdd",  "drain": "o1", "gate": "i1"},
  {"name": "MN1", "kind": "nmos", "source": "vmid", "drain": "o1", "gate": "i1"},
  {"name": "MP2", "kind": "pmos", "source": "vmid", "drain": "o2", "gate": "o1"},
  {"name": "MN2", "kind": "nmos", "source": "vss",  "drain": "o2", "gate": "o1"}]
```
결과: `vmid = CONFLICT`. 규칙이 **거부로 드러낸다**. 회로로서는 정상이고, vmid는 가운데 전위다.

**H3. 레벨 시프터(높은 레일 둘)**. vddl(1.8 V) 인버터와 vddh(3.3 V) 교차결합 PMOS 래치.
```json
"supply_nets": ["vddl", "vddh", "gnd"],
"netlist": [
  {"name": "MPi", "kind": "pmos", "source": "vddl", "drain": "inb", "gate": "in"},
  {"name": "MNi", "kind": "nmos", "source": "gnd",  "drain": "inb", "gate": "in"},
  {"name": "MN1", "kind": "nmos", "source": "gnd",  "drain": "x",   "gate": "in"},
  {"name": "MN2", "kind": "nmos", "source": "gnd",  "drain": "y",   "gate": "inb"},
  {"name": "MP1", "kind": "pmos", "source": "vddh", "drain": "x",   "gate": "y"},
  {"name": "MP2", "kind": "pmos", "source": "vddh", "drain": "y",   "gate": "x"}]
```
결과: `vddl = hi`, `vddh = hi`. 규칙은 hi **집합**은 맞게 주지만 둘 중 어느 쪽이 더 높은지는 모른다. 기둥 추적처럼 집합만 필요한 곳에는 문제가 없다. "가장 높은 레일 하나"가 필요한 곳(DEC-61 pmos bulk 기본값, `battery_centering`)은 판정할 수 없다. 전압 순서는 topology에 없고 `supplies_v`에만 있다.

**H4. 가운데 기준 레일이 PMOS source로 쓰이고, vdd는 NMOS drain으로만 나오는 경우**. 조용한 오답이 나는 경우다.
```json
"supply_nets": ["vdd", "vcm", "gnd"],
"netlist": [
  {"name": "M1",   "kind": "nmos", "source": "gnd",  "drain": "a",   "gate": "vin"},
  {"name": "MSF",  "kind": "nmos", "source": "vout", "drain": "vdd", "gate": "a"},
  {"name": "MRST", "kind": "pmos", "source": "vcm",  "drain": "a",   "gate": "rstb"}],
"passive_elements": [{"name": "RL", "kind": "resistor", "terminals": ["vdd", "a"]}, ...]
```
결과: `vcm = hi`, `vdd = mid`, `gnd = lo`. hi와 lo가 각각 정확히 하나라 개수 게이트를 **통과한다**. 그런데 실제로 가장 높은 레일은 vdd(1.8 V)이고 vcm은 0.9 V다. 기둥 추적은 vcm에서 시작하고 vdd는 중간 레일로 취급된다. **topology만 봐서는 이 오류를 잡을 수 없다.** spec의 `supplies_v`가 선언된 뒤 "hi 전압 > mid 전압 > lo 전압" 대조 게이트를 두어야 잡힌다(사이징 대상 회로에서만 가능).

추가 한계(가상 회로가 아니라 규칙의 전제). 규칙은 **source/drain 표기 방향**을 믿는다. 추출기가 대칭 소자(스위치, 전달 게이트)의 D와 S를 바꿔 적으면, 예를 들어 current_reuse M40을 `source=gnd, drain=Voc_des`로 적으면 gnd가 CONFLICT가 된다(거부로 드러난다). 다만 엔진은 이미 vgs 계산을 source 기준으로 하므로 이것은 새로 생기는 전제가 아니다.

정리:

| 실패 유형 | 예 | 규칙의 반응 | 드러나나 |
|---|---|---|---|
| hi 또는 lo 없음(한 종류 트랜지스터만 있는 회로) | H1 | mid로 분류 | 개수 게이트로 거부 |
| 한 레일이 양쪽 source | H2 적층 도메인 | CONFLICT | 거부 |
| 같은 극성 레일이 둘 이상 | H3 레벨 시프터, 음전원·gnd 동시 NMOS source | 집합은 맞음, 순서 모름 | 순서가 필요한 사이트에서만 거부 |
| 극성이 뒤바뀜 | H4 | 틀린 hi/lo | **topology만으로는 못 잡음**. `supplies_v` 대조로만 잡힘 |
| 레일이 bulk에만 나옴(웰 바이어스 넷) | `bulk: "vnw"` 선언 회로 | mid | 극성이 필요한 사이트에 쓰이지 않으면 무해 |

### 1.4 대안: 스키마에 극성을 선언

**모양(기존 관례에 맞춘 안)**. `ports`가 `{넷: {"role": ..., "direction": ...}}`이므로 같은 모양의 형제 필드를 둔다. `supply_nets`는 그대로 둔다(DEC-60 "넷 이름 목록", 테스트 보조 함수 `declared_supply_nets`의 `set(...)`이 그대로 동작한다).
```json
"supply_nets": ["vdd", "vss", "agnd"],
"supply_roles": {
  "_comment": "레일 극성(connectivity 메타데이터, 사용자 확인). 전압 값은 여기 두지 않는다(supplies_v, U-26 (a)).",
  "vdd":  {"role": "rail_high"},
  "vss":  {"role": "rail_low"},
  "agnd": {"role": "rail_mid"}
}
```
`supply_nets`의 원소 자체를 객체로 바꾸는 방법(`[{"net": "vdd", "role": "rail_high"}]`)은 권하지 않는다. DEC-60 문구, 테스트 보조 함수, prep §3.1 접근자가 모두 문자열 목록을 전제하고 있어서 바꿀 곳이 늘어난다.

**검증 규칙(로드 게이트 GB0)**
1. `supply_roles`의 키 집합은 `supply_nets`와 같아야 한다(`_` 접두 키는 제외). role 값은 `rail_high`, `rail_low`, `rail_mid` 중 하나다.
2. `rail_high`와 `rail_low`는 각각 하나 이상 있어야 한다.
3. 구조 증거와 모순되면 거부한다. `rail_high`로 선언된 레일이 NMOS source로만 나오거나, `rail_low`로 선언된 레일이 PMOS source로만 나오는 경우다(H4 같은 선언 실수를 잡는다. 반대로 H2의 vmid는 `rail_mid`로 선언하면 통과한다).
4. `supplies_v`가 있으면(사이징 대상 회로) min(high 전압) > max(mid 전압) > max(low 전압)을 확인한다. 중간 레일이 없으면 min(high) > max(low)만 본다.
5. 거부가 실제로 발동함을 먼저 증명한다(누락 키, 모순 선언, 전압 역순 3건의 red 케이스).

**이관 비용**
- 대상: library 9개 파일 전부(필수 필드로 만들 때).
- 쓰는 주체(계획 N3.12.2 쓰기 경로표): `library/*.topology.json`의 작성자는 오케스트레이터이고 조건은 "승인 기록"이다. U-16에 따르면 사용자가 확인한 표의 항목만 반영하고, `.ai/approvals/<id>.md`와 `Role: doc` 커밋이 필요하며, EL4는 승인 기록 없는 topology diff를 거부한다.
- 파급: topology가 바뀌면 S0 지문이 바뀌어 `ratified` 상태가 `review_needed`로 돌아간다(U-16). 이 때문에 E-LIB 기준 재확인이 필요하다. `supply_nets` 없이 topology dict를 만드는 test 파일이 최대 7개 있다(prep §3.3). 필수 필드로 만들면 이 파일들에도 필드를 넣어야 하고, 이것은 test-author 몫이다.
- 사용자 작업량: 9회로 × 2~3줄 확인. 표로 한 번에 승인할 수 있다(§1.2 표가 그대로 확인표가 된다).

### 1.5 비교

| | (A) 구조 규칙만 | (B) 스키마 필수 선언 | (C) 구조 규칙 기본 + 예외만 선언(권고) |
|---|---|---|---|
| 9회로 이관 | 0개 파일 | 9개 파일, 승인 기록 | 0개 파일 |
| H1·H2·H3 | 거부(선언할 자리가 없어 막힘) | 선언으로 해결 | 거부된 뒤 그 회로만 선언해서 해결 |
| H4(조용한 오답) | 로드 시점에는 못 잡음 | 사람이 틀리게 적으면 못 잡음. 구조 대조(규칙 3)로 일부 잡힘 | 규칙 결과와 `supplies_v` 대조로 사이징 시점에 잡힘. 필요하면 선언으로 확정 |
| 계획 관례 | DEC-60(이름 해석 금지)에 맞음 | WP-07(connectivity는 사용자)에 맞음 | **DEC-61 `bulk`와 같은 구조**(기본 규칙 + 다른 경우만 선언, U-28과 같은 판단) |
| 회로 해석 부담 | 사용자 몫 없음 | 매 회로 사용자 확인 | 예외 회로에서만 사용자 확인 |

---

## 2. D2: 소신호 MNA에서 선언 레일 전부를 교류접지로 둘지

### 2.1 지금 무엇이 일어나나(회로 관점)

`build_ac_network`와 `_full_circuit_response`는 `fixed = {"gnd": 0.0}`에 metric 선언의 `excite`와 `also_fix`만 더해 고정 노드를 만든다. 그 밖의 넷은 **전부 미지수(자유 노드)**다. vdd는 PMOS source에만 붙어 있으므로 MNA에서는 KCL 식 하나를 가진 보통 노드가 된다. 그 식은 "vdd로 들어가는 모든 소자의 소신호 전류 합 = 0"이다.

회로로 말하면 **vdd가 임피던스 무한대인 전원, 즉 이상 전류원으로 급전되는 노드**로 모델링된 것이다. 이상 전압원(교류 임피던스 0)이 아니다. 여기(excitation)에 따라 전체 공급전류가 변하면 vdd 노드가 움직이고, 그 움직임이 PSR 경로를 거쳐 출력에 섞인다.

실측(current_reuse, 정본 θ\*, 사본에서 풀이):

| 여기 | vdd 노드 소신호 전압(현재 코드) | 출력 diff | 출력 common |
|---|---|---|---|
| DM (Vip=+0.5, Vim=−0.5) | 2.04e-5 V | 2410.347 | 3.3e-4 |
| CM (Vip=Vim=1) | **0.0283 V**(1 V CM당 28.3 mV) | 0.05000 → 0.05008 | **0.5307 → 0.5165** |

DM에서는 완전차동 대칭 때문에 전체 공급전류가 거의 변하지 않고, vdd도 거의 움직이지 않는다(그래서 이득과 PM이 바뀌지 않는다). CM에서는 공통모드 입력이 공급전류를 바꾸고 그에 따라 vdd가 28 mV 움직인다. 이것이 CM 이득을 약 2.7% 키우고 CMRR을 0.235 dB 낮춘다.

**물리적으로 맞는 쪽**: 이상적인 DC 전원을 가정한 소신호 해석(SPICE `.ac`와 같음)에서는 DC 전압원이 교류 단락이다. 따라서 모든 레일은 교류접지다. 전원 임피던스를 모델링하고 싶으면 레일에 명시적 임피던스를 선언해야 하고, 그것은 "레일을 자유 노드로 두는 것", 즉 무한 임피던스와는 다른 모델이다. 계획 DEC-60("선언이 없으면 그 넷이 신호 넷으로 남아 … 교류접지 집합이 어긋난다")과 two_stage_ota 선언 주석이 이미 이 현상을 "심각한 버그"로 적어 두었고, two_stage_ota는 `excite`에 `vdd: 0.0`을 넣어 우회하고 있다. current_reuse CMRR 선언에는 그 우회가 없다.

추가 논거:
- PSRR은 `excite_den={"vdd": 1}`로 vdd를 여기한다. `fixed.update(excite)`가 마지막에 적용되므로 선택지 (i)에서도 여기 값이 이긴다. 결과가 변하지 않음을 실측으로 확인했다(차 0).
- 앞으로 vss-PSRR(`excite: {"vss": 1}`)을 선언하면, 현재 코드에서는 vdd가 자유 노드로 남는다. 두 레일이 동시에 틀린 상태가 된다. (i)에서는 자동으로 맞다.
- 선택지 (ii) "낮은 레일만 고정"은 vdd·gnd 회로에서 현재와 같다(CMRR 오차가 그대로 남는다). agnd 회로에서는 부하 CL과 보상 Cc가 자유 노드에 붙는다. 이것은 DEC-60 (iii)이 막으려던 상태 그대로다.
- nmcnr(vdd/vss)에는 `gnd` 넷이 없다. 현재 코드로 MNA metric을 선언하면 **어떤 레일도 고정되지 않는다.** 지금은 nmcnr에 MNA metric이 없어서 드러나지 않을 뿐이다.

### 2.2 9회로 전수: 선언 레일을 전부 교류접지로 두면 바뀌는 metric

방법: 저장소 사본(`C:/g26`)의 두 `fixed = {"gnd": 0.0}`을 환경변수로 바꾸는 패치를 넣었다(`gnd_only`는 원본과 같고, `all_rails`는 `{r: 0 for r in supply_nets}` 다음에 also_fix와 excite 순서로 덮어쓴다). `tests/unit/_library_sized_contexts._evaluate_once`로 `run_harness.SPECS` 4회로를 두 모드에서 한 번씩 평가했다. 회로마다 선언된 **모든 metric**(평가기가 돌려주는 전체)을 비교했다. 이 경로는 `skills/analog-grammar/assets`도 import한다(§4 부수 발견).

| 회로 | 평가점 | MNA metric(선언) | 바뀌는 metric(전→후) | 안 바뀌는 metric |
|---|---|---|---|---|
| current_reuse_telescopic_ota | 정본 θ\*(22/22) | cmrr_estimate_db, psrr_estimate_db, gain_full_circuit_db, parasitic_pm_deg | **cmrr_estimate_db 73.14488 → 73.38009(+0.23521 dB)**, parasitic_pm_deg 75.901400 → 75.901405(+5.7e-6°), gain_full_circuit_db +2.2e-10 dB(수치 잡음 수준) | power_uA, area_um2, gain_db, noise_v_rthz, mismatch_sigma_mV, psrr_estimate_db, vg15_level_v, vop1_level_v, rz1_ohm, rz2_ohm, classab_centering_dev_v, mirror_ratio_error_pct, supply_current_uA, kcl_residual_uA, stack_headroom_slack_v, mirror_ratio_error_mV. 16개, 차 정확히 0 |
| two_stage_ota | bounds 중앙점 거부(`InfeasibleSizingError`, stage1_ref 예산 초과). 시드 고정 무작위 300점도 전부 거부(Infeasible 259, ValueError 41) | gain_db(`smallsignal_gain_db`) | **없음(구성상 0)**. 선언 `excite`에 이미 `vdd: 0.0`이 있어 고정 집합이 전 {gnd, vin_p, vin_n, bias, vdd} = 후 {같음}이다 | power_uA, area_um2, mismatch_sigma_mV(MNA 무관) |
| folded_cascode | bounds 중앙점(평가 성공) | 없음 | 없음 | power_uA, gain_db, pm_deg, cmrr_db, psrr_db. 5개, 차 0(폐형식) |
| nmcnr_amplifier | 중앙점 거부(stage2_diode_ref), 무작위 300점 전부 거부 | 없음 | 없음(구성상. metric 5개 모두 폐형식: sum_current, nmcnr_gain_db, nmcnr_pm_deg, cmrr_estimate, psrr_estimate) | |
| common_gate_amplifier, ngcc_3stage_ff, pushpull_follower_buffer, sf_pushpull_output_opamp, two_stage_ota_sf | 사이징 spec 없음(SPECS 밖), `sizing_roles.metrics` 0개 | 없음 | 없음 | 해당 없음 |

**결론: 현재 9회로에서 값이 의미 있게 바뀌는 metric은 current_reuse `cmrr_estimate_db` 하나다.**
- 제약 `cmrr_estimate_db ≥ 60`(user_spec)과의 여유: 73.1 dB 기준 13 dB. 변화 방향은 +(제약 완화)라서 θ\*가 새로 불가능해질 수는 없다. 목적함수는 `minimize power_uA`이고 CMRR이 활성 제약이 아니므로 θ\*도 바뀌지 않을 가능성이 높다. 다만 이것은 추정이고, 확정은 auditor가 병합본에서 최적화를 다시 돌려 E-INST로 확인해야 한다.
- 진짜 bounds 중앙점에서는 current_reuse가 거부된다(M15 gm_id 후보 없음). 그래서 이 표의 current_reuse 행은 θ\* 기준이다.
- 앞으로 영향: agnd 두 회로와 nmcnr에 MNA metric이 선언되는 순간 (i)이 없으면 결과가 틀린다(§2.1). 지금은 값이 없어 차이도 없다.

### 2.3 승인 범위

(i)을 고르면 파일럿 기준선(current_reuse `cmrr_estimate_db`)이 바뀐다. 계획 DEC-40(기준 변경은 매 건 사용자 승인)에 따라 승인 기록이 함께 필요하다. 변화 방향은 기준 약화가 아니라 모델 정정이지만, 기준값이 바뀌므로 승인 대상으로 둔다. B26-3 card의 판정은 red-green(합성 회로에서 vdd 자유 노드 때문에 CM 응답이 달라짐)과 E-INST 차이표다.

---

## 3. 권고 (권고일 뿐이고 결정은 사용자가 한다)

### 권고 D1: (C) 구조 규칙 기본 + 선택 필드 `supply_roles`(예외 회로만)

이유:
1. 현재 9/9 회로가 규칙만으로 모순 없이 판정된다. 이관 파일 0개, 승인 기록 0건으로 B26-2를 바로 시작할 수 있다.
2. 계획에 이미 같은 모양의 선례가 있다. DEC-61 `bulk`는 "기본 규칙 + 기본과 다른 연결만 선언"이고, U-28이 같은 판단으로 확정됐다. 극성도 같은 구조로 두면 스키마 관례가 하나로 유지된다.
3. 규칙이 틀리는 경우(H1, H2, H3의 순서 필요 사이트)는 모두 **거부로 드러나게** 만들 수 있다. 조용한 오답(H4)은 topology만으로는 어느 방법으로도 막을 수 없다. 사람이 선언해도 잘못 적을 수 있기 때문이다. 이 경우는 `supplies_v` 전압 순서 대조 게이트가 막는다. 극성의 최종 정본은 계획 DEC-61대로 `supplies_v` 전압이다.
4. 게이트는 셋이다. (a) CONFLICT, hi 없음, lo 없음이면 거부하고, 선언이 있으면 선언을 쓴다. (b) 선언은 구조 증거와 모순되면 거부한다. (c) `supplies_v`가 있으면 전압 순서와 대조한다. 각 게이트가 실제로 거부함을 H1·H2·H4 합성 topology로 먼저 증명한다.
5. `supply_roles` 필드 자체는 필요한 회로가 생길 때 만든다(만들면 배선한다는 원칙). B26-2에서는 스키마 자리와 게이트 규칙만 계획서에 적고, 코드는 "선언이 없으면 규칙"만 구현한다. 선언을 읽는 코드는 첫 예외 회로와 함께 넣는다.

(B)를 고를 경우의 조건: 사용자가 "극성은 회로 해석이므로 항상 사람이 확정한다"는 원칙을 우선하면 (B)가 맞다. 이때 §1.2 표를 확인표로 써서 9회로를 한 번에 승인하고, 규칙 3(구조 대조)을 반드시 함께 둔다.

### 권고 D2: (i) 선언 레일 전부를 교류접지로 고정, 그다음 also_fix와 excite로 덮어쓰기

이유:
1. 이상적인 전원을 둔 소신호 해석의 정의와 맞는다. 레일을 자유 노드로 두는 것은 "무한 임피던스 전원"이라는 의도하지 않은 모델이다. 실측으로 vdd가 CM 1 V당 28 mV 움직였다.
2. 현재 바뀌는 기준값은 1개(+0.235 dB, 제약 완화 방향, 여유 13 dB)이고, 나머지 metric은 모든 회로에서 0이다(§2.2).
3. (ii)는 지금의 오차(current_reuse CMRR)를 그대로 두고, agnd 회로의 CL·Cc와 nmcnr의 vdd를 자유 노드로 남긴다. 사이징 대상이 늘어날수록 틀린 값이 늘어난다.
4. two_stage_ota 선언의 `excite: {"vdd": 0.0}` 같은 회로별 우회가 필요 없어진다. 우회를 남겨도 결과는 같으므로 지우는 것은 선택이다(지우면 topology 변경이라 승인 기록이 필요하므로 이번 card에서는 남기는 것이 싸다).
5. 필요한 승인: DEC-40 기준선 변경 승인 1건(current_reuse `cmrr_estimate_db`, θ\*에서 auditor가 다시 잰 값으로).

---

## 4. 부수 발견(B26 범위 밖, 기록만)

- **prep 정정**: prep §2.4와 §4 D2의 "중앙점 theta"는 current_reuse에서는 **정본 θ\*** 값이다(`_library_sized_contexts._theta_point` 규칙). 수치(73.1449 → 73.3801)는 맞다. two_stage_ota와 nmcnr은 중앙점에서 거부된다는 prep의 서술도 맞다. current_reuse는 진짜 중앙점에서도 거부된다(M15, gm_id 후보 없음).
- **다른 skill의 유무가 사이징 결과를 조용히 바꾼다**: `stick_diagram._import_analog_grammar`는 `skills/analog-grammar`가 없으면 조용히 폴백한다(설계상 의도, 1025~1031행 주석). 저장소 사본에서 이 skill을 빼고 돌리자 current_reuse θ\* 평가가 성공이 아니라 `ValueError`(vertical_stack_id 그룹 biasgen_vop_a / biasgen_vop_floatsrc_sink 순환)로 바뀌었다. 즉 이 폴백은 무해한 보강이 아니라 결과를 바꾸는 경로다. 우회·skip 타당성 검토 대상으로 백로그에 올릴 만하다(인프라 결함이라 gmid 엔진을 막을 때만 처리).
