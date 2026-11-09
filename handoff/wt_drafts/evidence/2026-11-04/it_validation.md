# IT card 독립 판정 (2026-11-04)

대상: `wt/_drafts/evidence/2026-11-04/it/`의 `00_scope_base_briefs.md`, card 넷(`20261104-it1`·`it2c`·`it2d`·`it2e`) spec·interface. 기준: design master `0d99a813` 41 §4.7-V·§4.7-W·§4.7-5, 계획 N6.5·N6.6·N3.6·N3.8, 위임 A-33.

방법: 문서 읽기와 `git show`·`grep`. 실행 없음. 엔진 인용은 재작성 범위 확인뿐이다(`integ/it12` `block_columns.py`, 원칙 8). interface 넷은 전문을, spec은 IT-1·IT-2c만 읽었고 IT-2d·IT-2e spec은 열지 않았다.

## 결론

interface 넷은 구현 없이 기대값을 유도할 수 있고, 판정 규칙은 맞다. 다만 card 경계 하나와 GL-1 뒤 lint 하나가 빠져 코드 단계에서 막힌다. 두 건 모두 문언으로 닫힌다.

| 점검 | 판정 |
|---|---|
| 낡은 O-204~O-215 이전 문언 | 0. +tol은 T-L8a′ 구별 전제로만, R0·`off` 행·정의 창은 '없음' 목록으로만 나옴 |
| RR-6 | 맞음. 꺼짐 분류·정지 0, T-G가 `off_device_on_signal_path` 0 단언, 술어 필드 안 만듦(표 #19) |
| DEC-106 종속 수 | 맞음. 같은 꼬리 toy 1 손계산과 일치, F 닿는 경우·이중 차감 toy 있음 |
| servo 식 | 손으로 확인. c·s = 0, 구동 넷 1 − e_p(c·vx)/a_e, 차동 s̄ = 1, 예시 수치 맞음 |
| `region_rows` 부호 | 손으로 확인. nmos VDS, pmos VSD, `triode` 부호 반전 맞음 |
| 갈래 5 `icm_capacitive_only_node` | 계획과 맞음. O-211 조건 (3)이 영역 행 창에도 걸림(P:742 부근 '조건 넷', '같은 조건 R0 영역 행 창에도'). G 행 전부 0 판정은 gate·용량만 닿는 넷에 맞음 |
| V_cm·세 metric | design 4.7-5와 일치 |
| 계획 조건 (4) 필드 둘 상태 축 | 대상 없음. 점별 이득 필드를 안 만듦(O-215 임시) |

## Major

**I1. IT-1 head에서 `_windows` 재작성 범위가 빠져 T-1h가 맞을 수 없다** (재작성 범위 누락, 틀린 기대값)

- IT-1 interface는 'n 포트 항목은 없다'고 적고 T-1h가 이를 단언한다. 순서는 IT-1 → IT-2c이고, 커널 비뿌리 항목 삭제는 IT-2c 범위다.
- `integ/it12` `block_columns.py` `_windows`는 입력 포트 가운데 relation이 `REL_WINDOW`·`REL_INPUT_DC`가 아닌 것을 모두 처리한다(`:800-801`). 새 relation `input_point`는 이 거르기를 지나 n 포트 항목을 쓰거나 `writer_head` 사슬을 탄다. IT-1 spec 재작성 범위에 `_windows`가 없어, 코드 주체는 범위를 넘거나 T-1h red로 멈춘다.
- **고칠 문언**(IT-1 spec 재작성 범위 표, `block_columns.py` 행): '`E/sizing/block_columns.py` `input_roots`·`_solve_input_window`·writer 식·`_windows`의 뿌리 아닌 포트 거르기 | 읽는 키만 입력 점 y로. `_windows` 거르기에 `input_point` 포함(입력 점 두 항목 중 p는 뿌리 갈래, n은 항목 없음). 그 밖 비뿌리·F 성분 갈래는 IT-2c가 지운다. 루프·예외 추가 0, 덧대기가 필요해지면 멈춤'.
- interface는 바꾸지 않는다.

**I2. `Circuit` 이동이 GL-1 래칫을 깬다** (구현하면 병합 정지, 재작성 범위 누락)

- IT 병합은 GL-1 코드 뒤다(A-33). GL-1 래칫 키는 (kind, 경로, 안정 이름)이고 행 추가는 기준 약화다(40 §2.4.10 GL-1 절).
- `_Circuit` 생성자는 `self.writers = dict(...)`·`self.pins = {…}` 꼴 속성을 여럿 둔다(`integ/it12` `block_columns.py:165-175`). 이것을 `E/sizing/_helpers_dc_solve.py` `Circuit`으로 그대로 옮기면 `g8_attr_container` 새 키가 생겨 `test_rule_g8_baseline_ratchet`이 red가 된다. IT card 어디에도 이 처리가 없다(card에 G-8·래칫 언급 0, 판정 측정 A3은 IT-1이 구조 규칙 A~I, IT-2c가 G1~G7만 적음).
- **고칠 문언**
  - IT-2c spec '재작성 범위' 표에 행 추가: '`Circuit` 생성자 속성 | 읽기 전용 값으로 둔다(`types.MappingProxyType(dict(...))`·tuple). G-8 새 키 0. 40 §2.4.10 "그런 클래스는 구조로 고친다". 값·쓰임 불변. 쓰기가 필요한 `override`는 `block_columns._Circuit`에 남긴다.'
  - IT-2c interface '`Circuit` 계약' 끝: '속성은 호출자가 바꿀 수 없다. `check_g8`·`check_value_types`가 이 모듈에 위반을 내지 않는다.'
  - IT-2c interface 판정 측정 A3: '+ GL-1 병합 뒤 base에서 `ratchet.new` 0(새 키·수 증가 0). `block_columns.py` 쪽 줄어든 키는 판정자가 줄임. 행 추가로 통과시키면 `criteria_weakened`.'
  - IT-1 판정 측정 A3 끝에 같은 `ratchet.new` 0 문장을 더한다. IT-2d·IT-2e의 A3도 같다.

## Minor (막지 않음, 문언 포함)

- m1. **A2 합격 문언**: '새 실패 0 + 나열'은 N6.3·N6.5 완료 6 '0 failed'보다 약하고, 위임 O-226 밖이다. spec D-1이 '약화면 멈춤'이라 지금은 안전하다. IT-1 A2를 '전체 0 failed. base에 실패가 남으면 그 목록을 오케스트레이터에 올리고 판정을 멈춘다(A-31 병합 여부 확인, master에 아직 없음)'로 고친다.
- m2. **빈 창이 정렬로 숨음**: 끝을 min·max로 정렬하므로 Δlo > Δhi인 빈 창이 양수 폭이 된다. 기울기 ≤ eps로 건너뛴 행의 slack < 0도 창을 좁히지 않는다. 봉인점 slack ≥ 0이면 도달하지 않고, IT~EO-1 기간 `triode` 불일치만 해당하며 library `triode` 선언은 0/13(41 §4.8-12)이라 Minor다. IT-2c '창' 문단 끝에: 'Δlo > Δhi이거나 건너뛴 행의 slack < 0이면 모든 입력 포트 `"unmeasured"`.' T-K에 한 사례.
- m3. **`input_dc` 값**: `"declared"`·`"pending"`뿐인데 spec `engine`도 미선언이다(DEC-106). IT-2d 정의 줄에: '`input_dc` = 입력 DC 미선언(spec `engine`·`pending`)이면 `"pending"`.' T-M1 미선언 toy에 `engine` 변형.
- m4. **단언 금지와 고칠 test 충돌**: IT-2c '`node.dc_window` 수치 단언 금지'와 '`test_block_columns.py` tol 5건 여유 0 재유도'가 겹친다. 고칠 표에 '이 card 안 재유도는 기존 test 한정. 새 test는 `node.dc_window` 수치를 단언하지 않는다'를 더한다.
- m5. **IT-2c spec 범위 표**: `E/sizing/__init__.py` `__all__`, `E/_module_map.py` 새 모듈 행, `s2_values.py` `SS_WRITES`·`DC_WRITES`, metrics·sizing CONTRACT 소유표가 없다(interface에는 있음). 한 행 추가.
- m6. **T-1g red 표기**: 이름 전단사는 base에서 이미 같을 수 있어 red가 보장되지 않는다. red 목록에서 빼고 '입력 점 y 키 이름 추종만 red'로 적는다.
- m7. **T-L12 전제**: `k_max` 소진을 만드는 공개 이름이 interface에 없다. 기존 하네스(`test_block_columns.py`의 `SccLog.k_max` 사례)를 쓰라고 한 줄 적는다.
- m8. **O-211 조건 (3)과 NL-1**: 조건 근거가 '전하 보존 극한 정본 자리 없음'인데 card NL-1이 그 자리를 만든다. 재점검 입력으로 표지한다(지금 동작 불변).
- m9. 계획 잔재(P:1764 범위, N6.6 (14) E-22, P:1341)는 `00_scope` 표지대로 후속이다.

## 미확인

- IT-2d·IT-2e spec 본문, `scope_grep.txt` 건수 재대조, 레지스트리 문언.
- `Circuit` 속성 중 실제로 옮길 집합(design '행 부분'), 읽기 전용 교체의 값 불변은 card 착수 때 test로 본다. `MappingProxyType` 호출이 lint를 지나는지는 GL-1 interface의 가변 값 목록 기준 판단이다.
- ⑩ 결정 간 모순 점검은 O-225로 하지 않았다.

쓰기: 이 파일 하나.

verdict: Major 2
