verdict: (가) -- 조건부. 엔진 필드(`node.dc_writer`·`graph/s1 orbits`) 실측은 시스템 메모리 회수로 중단돼 미완이다. 아래 결론은 netlist 연결 + 계획 DEC-106 규칙 + 앞 실측(`m_s1L.jsonl`)에 근거한 오프라인 판정이다.

# FS-1 짝 정의 -- 'gate·source 같음 = 쓰기 계획 DC 마디 같음' 실측

- 측정자: 앞 판정과 같은 독립 판정자. 읽기·측정만 했고 엔진·test·card 변경 0.
- 기준 코드: role/code/20261107-fs1 head `802b3ed1`. 격리 복제본(`git archive` → scratch `fs1_judge/head802/`)을 썼고 code worktree는 건드리지 않았다.
- 도구는 새로 만들지 않았다. 기존 스크립트에 칸만 더했다.
  - `m_s1.py`: `node.dc_writer`, `device.dc_coord`, `graph/s1 orbits`, 실효 pins·bulk, `port_role` 기록 칸.
  - `m_partner.py`: DC 마디 기준 KVL 짝 갈래.
- scratch 경로: `C:/Users/HSLEE/AppData/Local/Temp/claude/C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills/63c6146a-ab1d-4035-a169-bae810986922/scratchpad/fs1_judge/`

## 실행 상태 (먼저 밝힘)

- 7개 회로 순차 실행(`m_s1D.jsonl`)을 첫 회로(two_stage_ota, 착수 여유 5.8 GB)에서 Claude Code가 끊었다. 사유: '시스템 메모리 위급, 세션 유휴' 회수.
- 결과 줄은 0줄이다. 지시('사용자가 요청할 때만 재시작')대로 다시 띄우지 않았다.
- 그래서 엔진이 쓴 `dc_writer` relation·y 키, `orbits` 값, `dc_coord.partner`는 **미측정**이다. 아래 표에서 그 칸은 '미측정'으로 적는다.
- 재측정 방법: 같은 명령(`m_s1.py <head802 tests> m_s1D.jsonl <회로>`를 회로마다 하나씩) → `m_partner.py`. `dcnode_pairs`·`sym_used`·`sym_to_kvl_dc` 칸이 그대로 나온다.

## 1. 지금 대칭 짝으로 처리되는 쌍 → DC 마디 기준 KVL 짝으로 넘어가는 수

- 대상: 앞 실측(`partnerL.jsonl`, head `7c239bee` 짝 규칙과 같은 정의)에서 대칭 짝으로 메워진 비쓰기 소자. 단계 B 통과 7개 회로 전수에서 **6개**다.
- 6개 모두 role `diff_pair` 묶음의 입력쌍 반쪽이고, gate가 차동 입력 포트 쌍에 물려 있다.

| 회로 | 소자(비쓰기) → 대칭 짝(쓰기) | gate 넷 (종류) | source | kind | 출발 L(같음) | 입력 DC 선언 | DC 마디 같음 (DEC-106) | DEC-97 궤도 |
|---|---|---|---|---|---|---|---|---|
| two_stage_ota | M1 (gate vin_n) → M2 (gate vin_p) | 입력 포트 differential_input_n / _p | CS (공유) | nmos | 1.5e-7 = 1.5e-7 | `pending SP-2`(미선언) | **같음** -- 미선언이면 두 포트가 입력 점 하나(v_cm), relation `input_point` | 미측정 |
| folded_cascode | M1 (vin_n) → M2 (vin_p) | 입력 포트 | tail | nmos | 1.5e-7 | 미선언 | **같음** | 미측정 |
| nmcnr_amplifier | M102 (Vin_n) → M103 (Vin_p) | 입력 포트 | NodeTail | pmos | 1.5e-7 | 미선언 | **같음** | 미측정 |
| current_reuse_telescopic_ota | M1b (Vim) → M1a (Vip) | 입력 포트 | Vx | pmos | 2.5e-6 = 2.5e-6 | 미선언 | **같음** | 미측정 |
| 〃 | M4b (Vim) → M4a (Vip) | 입력 포트 | Vy | nmos | 3.221e-6 = 3.221e-6 | 미선언 | **같음** | 미측정 |
| sf_pushpull_output_opamp | M2 (vin_n) → M1 (vin_p) | 입력 포트 | TAIL | nmos | 1.5e-7 | **선언**(`input_dc.net = agnd`, U-39·U-25) | 값은 같음(두 포트 모두 선언 입력 DC 넷 agnd 값). 다만 DEC-106 `input_point` 갈래가 아니다(선언 갈래). 엔진이 두 포트를 같은 DC 변수로 쓰는지는 **미측정** | 미측정 |

- 결과: 대칭 짝 → DC 마디 KVL 짝으로 넘어가는 수는 **5/6 확정(규칙상)**이고, sf 1개는 미측정이다. 규칙상 확정이란 DEC-106·design 40 1728·1731행 정의상 같은 DC 변수라는 뜻이고, 엔진 필드 값은 미측정이다.
- 그 밖의 비쓰기 소자 37개: gate가 입력 포트가 아닌 내부·바이어스 넷이다. 원래 넷 이름 비교로 KVL 짝이 서던 30개는 DC 마디 비교에서도 같다(같은 넷 = 같은 DC 마디).

## 2. KVL로 넘어가지 않는 대칭 짝 사용

| 쌍 | gate 넷 | 궤도 | 판단 |
|---|---|---|---|
| sf_pushpull_output_opamp M2 → M1 | 입력 포트(선언 입력 DC = agnd) | 미측정 | DEC-106 문언은 '입력 DC 미선언'의 갈래다. 선언 회로에서 두 포트는 각자 선언 값(같은 agnd)으로 고정된다. 물리적으로 VG1 = VG2 = V(agnd), source 공유(TAIL), 같은 kind·bulk·L이므로 같은 VGS·VSB·L이다. 따라서 '같은 DC 값을 같은 정의 자리(선언 입력 DC 넷 하나)에서 읽는 두 마디'를 DC 마디 같음에 넣으면 KVL 짝이다. 그 정의는 쓰기 계획이 이미 갖고 있을 것으로 보이며(두 포트의 writer = 선언 넷 W0/W1 꼴), 엔진 필드로 확인해야 한다. |

- 내부 차동 마디에 gate가 물린 대칭 짝 사용은 **0건**이다. 내부 차동 마디 쌍(예: current_reuse M37a·M37b, gate Voc·Voc_des)은 두 소자가 모두 쓰기 소자라 짝이 필요 없다(앞 실측 r-1 표).
- branch_symmetric 묶음의 대칭 짝 사용도 **0건**이다. 그 묶음 멤버는 모두 쓰기 소자이거나 KVL 짝을 가진다.

## 3. 결론

- **(가) 성립(조건부)**: 지금 대칭 짝 규칙이 메우는 경우는 library 전수에서 '차동 입력 포트 쌍에 gate가 물린 입력쌍 반쪽' 하나뿐이다. 이 경우는 쓰기 계획 DC 마디로 gate를 비교하면 KVL 짝이 된다.
  - 5/6은 DEC-106 `input_point`로 같은 DC 변수다.
  - 1/6(sf, 선언 입력 DC)은 같은 선언 값을 읽는 두 마디다.
  - 그러므로 '짝 = DC 마디 기준 KVL 짝 하나(+ 출발 L 같음)'로 대칭 짝 규칙과 `matching_groups` 의존을 없앨 수 있다. 이것은 graph 규칙 3('같은 DC 마디인가'의 정의를 둘 두지 않음)에도 맞다. `start_partner`의 넷 이름 비교 + diff_pair 메우기는 그 정의의 둘째 판정이므로, 쓰기 계획 필드(`node.dc_writer` → 같은 y 키 / input_point / 선언 넷) READS 하나로 바꾸는 것이 정본 자리다.
- **(나)는 필요 없다**: 궤도 짝이 KVL로 메울 수 없는 경우를 메우는 사례가 library 전수에 0건이다. 궤도는 미측정이지만 결론에 쓰이지 않는다.
- **조건**: 이 판정을 확정하려면 아래 둘을 엔진 필드로 확인해야 한다.
  1. 5개 회로에서 두 입력 포트 `node.dc_writer`의 relation이 `input_point`이거나 같은 y 키다.
  2. sf에서 두 입력 포트가 같은 DC 정의 자리(선언 입력 DC)를 쓴다.
  - 2가 서지 않으면 sf M2는 짝을 잃는다. 단일 멤버 칸이 아니라 diff_pair 칸 (M1, M2)의 멤버이므로 그 칸이 출발 불능(`no_member_density`)이 되고, 그것이 (다)이다. 그 경우 DC 마디 같음 정의에 '선언 입력 DC 넷 공유'를 넣도록 계획 DEC-106 범위를 개정해야 한다.
- 함께 볼 정본 후보: `device.dc_coord`의 `relation = parallel_vgs`·`partner`('같은 (gate, source)의 쓰기 소자' -- s2_values.py:374-381)가 이미 쓰기 계획이 정한 KVL 짝이다. 입력쌍 반쪽의 dc_coord가 `parallel_vgs` + partner = 다른 반쪽이면, `start_partner`가 그 필드를 READS하는 것이 가장 단순한 단일 정본이다(L 같음 조건만 더함). 이 값도 미측정이다(재측정 칸 `dcnode_pairs[*].coord`).

## 4. 출발 불능 n/N 변화

- **변화 없음(오프라인 판정)**: 앞 실측은 출발 불능 0/82, 기준 폭 출발 7/82였다.
- DC 마디 기준 KVL 짝으로 바꾸면 대칭 짝 6개가 KVL 짝으로 같은 쓰기 소자(같은 상대)를 얻는다. 짝의 상대가 바뀌지 않으므로 출발 W·칸 키도 같다.
- 기준 폭 출발 7개(M23a·M14a·M20b·M11b·M40·M2·M21)는 gate가 내부 바이어스·출력 팔로워 마디라 입력 점 병합의 영향을 받지 않는다. 그래서 7/82 그대로다.
- 조건 2가 서지 않는 경우에만 sf diff_pair 칸 1개가 출발 불능이 된다(1/82).

## 실행 기록

- 착수 전 여유 5.83 GB(≥ 3.7 GB). 회수 뒤 여유 5.75 GB, 판정자 python 프로세스 0개를 확인했다.
- 금지 명령 0.
- 원인 규명된 미완: 엔진 필드 실측 1건(시스템 메모리 회수). 재시작은 요청이 있을 때만 한다.
