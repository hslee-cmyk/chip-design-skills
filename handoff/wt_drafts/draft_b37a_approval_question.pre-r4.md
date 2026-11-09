# B37a 승인 질문·기록 초안 -- `20260930-b37a-ports-roles`(target_kind: decision)

대상 card: `_drafts/draft_b37a.spec.md`(id `20260930-b37a-ports-roles`). 측정 출처: card '작성 전 실측'(v2: gate `master` `7535799`, scratch `C:/g68`. **v3: 항목 단위 삭제 목록·`ports` oracle = gate `master` `dd60db6`, scratch `C:/g174` -- card '작성 전 실측' 8**).
(v3 -- Phase 4 design v0.9.5 §6 D47·§5.4 #47 조건 (나): Q1이 승인하는 대상은 산문 표가 아니라 **항목 단위 삭제 목록**이고, 그 목록이 승인 기록 본문에 그대로 실린다. v2 원본은 `draft_b37a_approval_question.pre-p4v095.md`.)
이 파일은 오케스트레이터가 사용자에게 묻는 문안과, 답을 받은 뒤 쓰는 승인 기록 범위 설명 초안이다. card 안에 두면 코드 블록 안의 `## ` 줄이 card 절로 파싱되므로 따로 둔다(B34 선례).

## 1. 사용자에게 묻는 것(세 가지, 각각 답이 필요)

### Q1. 동작 변경을 받아들이는가

B37a는 `load_topology`가 topology `ports` 선언을 analog-grammar에 넘기게 한다. 지금은 넷 이름 정규식이 입력을 추정하고, `vin_p`·`Vinn`류 입력을 BIAS로 분류한다.
그 분류에서 **유도된** 자동 채움 값이 있다. B37a 뒤에는 그 유도가 없어진다. 그 결과는 **삭제뿐**이다(값 추가·변경 0, 사람이 선언한 값 변화 0 -- 실측). 승인 대상은 아래 **항목 단위 삭제 목록 전체**다(gate `master` `dd60db6`에서 잰 값 -- v2의 `7535799` 측정과 항목까지 같다. 착수 시 실제 base에서 다시 재고, 한 항목이라도 다르면 멈추고 새 목록으로 다시 묻는다).

요약(읽기용 -- 승인·판정의 출처는 아래 데이터 블록이다):

| 회로 | 키 | 지워지는 항목 |
|---|---|---|
| `ngcc_3stage_ff` | `device_roles`, `_device_roles_autofilled`(두 키 같음) | 필드 `headroom_role` 4건: M1 `cascode`, M4 `mirror`, M6B `mirror`, M7 `mirror`(소자 항목은 남음 -- `gm_id_role` 등 유지) |
| `sf_pushpull_output_opamp` | 〃 | 필드 `headroom_role` 20건: M1 `cascode`, M2 `cascode`, M5 `cascode`, M6 `mirror`, M7 `cascode`, M8 `mirror`, M9 `mirror`, M10 `cascode`, M11 `mirror`, M12 `cascode`, M13 `cascode`, M14 `mirror`, M15 `cascode`, M16 `mirror`, M17 `mirror`, M18 `cascode`, M19 `cascode`, M20 `mirror`, M21 `cascode`, M22 `cascode`. 그중 M5~M22 18개는 남는 필드가 없어 **소자 항목째** 사라진다(M1·M2는 `L_role`·`gm_id_role` 유지) |
| `two_stage_ota_sf` | 〃 | 필드 `headroom_role` 5건: M1 `cascode`, M2 `cascode`, M4 `mirror`, M6 `mirror`, M8 `cascode`. M6·M8은 **소자 항목째** 사라진다 |
| `nmcnr_amplifier` | `_device_roles_gap_fill_review_needed` | 2항목(12 → 10): M201, M301의 'compensation.stage_devices 소속 -- gm_id_role 제안은 … 가드로 무시' 안내 |
| `two_stage_ota` | 〃 | 2항목(9 → 7): M4 `field_conflicts` `headroom_role` [`cascode`, `mirror`] 안내, M6 'compensation.stage_devices 소속' 안내 |

레이아웃 1차 그룹(E3, `resolve_stack_layout` 경로 3 -- `dd60db6` 재측정에서 v2와 같다): `ngcc_3stage_ff` `[M0, M1, M2]` → `[M0]`, `[M1, M2]` / `sf_pushpull_output_opamp` `[M17, M18]`·`[M19, M20]` → 넷으로 분리(전체: `[M5,M6]`·`[M7,M8]`·`[M9,M10]`·`[M11,M12]`·`[M15,M16]` + 단독 `M17`~`M22`) / `two_stage_ota_sf` `[M8, M9]` → `[M8]`, `[M9]`.

바뀌지 않는 것(실측): 9회로 `transistors`, V1·V2 파이프라인 결과, 위 8쌍과 `ports` 밖의 meta 키 전부(`_vertical_stack_id_autofilled` 포함), `input_referred_offset_pairs` 9/9, audit 9/9.

**항목 단위 삭제 목록(데이터 블록 -- 승인 기록 본문에 이대로 싣는다).** 적용(판정 python이 base 값에 적용한 값이 병합본 기대값): (1) `field_removed` `[회로, 키, 소자, 필드, 옛 값]`마다 그 필드를 지운다(옛 값이 다르거나 없으면 INVALID) (2) `entry_removed` `[회로, 키, 소자]`는 (1) 뒤 `{}`가 된 소자 항목을 키째 지운다(`{}`가 아니면 INVALID) (3) `review_needed_removed` `[회로, 항목]`은 리스트에서 dict 전체가 같은 항목 하나를 지운다(없으면 INVALID) (4) 목록 밖은 base 값 그대로. `dd60db6`에서 (1)~(3) 적용 값 = 모의 병합본 값(9회로 × 3키 불일치 0). 블록 sha256(펜스 안 줄을 LF로 잇고 끝에 LF 1개) `7c1871a6977a21fe0b7583540362816d721eb5435da754cb38042f3e585de58f`.

```json
{"list_id": "b37a-deletion-list-v1",
 "base_commit": "dd60db6515b6fe80ab16349835c19aa75d4f292f",
 "pairs": [
  ["ngcc_3stage_ff", "_device_roles_autofilled"],
  ["ngcc_3stage_ff", "device_roles"],
  ["nmcnr_amplifier", "_device_roles_gap_fill_review_needed"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled"],
  ["sf_pushpull_output_opamp", "device_roles"],
  ["two_stage_ota", "_device_roles_gap_fill_review_needed"],
  ["two_stage_ota_sf", "_device_roles_autofilled"],
  ["two_stage_ota_sf", "device_roles"]
 ],
 "field_removed": [
  ["ngcc_3stage_ff", "_device_roles_autofilled", "M1", "headroom_role", "cascode"],
  ["ngcc_3stage_ff", "_device_roles_autofilled", "M4", "headroom_role", "mirror"],
  ["ngcc_3stage_ff", "_device_roles_autofilled", "M6B", "headroom_role", "mirror"],
  ["ngcc_3stage_ff", "_device_roles_autofilled", "M7", "headroom_role", "mirror"],
  ["ngcc_3stage_ff", "device_roles", "M1", "headroom_role", "cascode"],
  ["ngcc_3stage_ff", "device_roles", "M4", "headroom_role", "mirror"],
  ["ngcc_3stage_ff", "device_roles", "M6B", "headroom_role", "mirror"],
  ["ngcc_3stage_ff", "device_roles", "M7", "headroom_role", "mirror"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M1", "headroom_role", "cascode"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M10", "headroom_role", "cascode"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M11", "headroom_role", "mirror"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M12", "headroom_role", "cascode"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M13", "headroom_role", "cascode"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M14", "headroom_role", "mirror"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M15", "headroom_role", "cascode"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M16", "headroom_role", "mirror"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M17", "headroom_role", "mirror"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M18", "headroom_role", "cascode"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M19", "headroom_role", "cascode"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M2", "headroom_role", "cascode"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M20", "headroom_role", "mirror"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M21", "headroom_role", "cascode"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M22", "headroom_role", "cascode"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M5", "headroom_role", "cascode"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M6", "headroom_role", "mirror"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M7", "headroom_role", "cascode"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M8", "headroom_role", "mirror"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M9", "headroom_role", "mirror"],
  ["sf_pushpull_output_opamp", "device_roles", "M1", "headroom_role", "cascode"],
  ["sf_pushpull_output_opamp", "device_roles", "M10", "headroom_role", "cascode"],
  ["sf_pushpull_output_opamp", "device_roles", "M11", "headroom_role", "mirror"],
  ["sf_pushpull_output_opamp", "device_roles", "M12", "headroom_role", "cascode"],
  ["sf_pushpull_output_opamp", "device_roles", "M13", "headroom_role", "cascode"],
  ["sf_pushpull_output_opamp", "device_roles", "M14", "headroom_role", "mirror"],
  ["sf_pushpull_output_opamp", "device_roles", "M15", "headroom_role", "cascode"],
  ["sf_pushpull_output_opamp", "device_roles", "M16", "headroom_role", "mirror"],
  ["sf_pushpull_output_opamp", "device_roles", "M17", "headroom_role", "mirror"],
  ["sf_pushpull_output_opamp", "device_roles", "M18", "headroom_role", "cascode"],
  ["sf_pushpull_output_opamp", "device_roles", "M19", "headroom_role", "cascode"],
  ["sf_pushpull_output_opamp", "device_roles", "M2", "headroom_role", "cascode"],
  ["sf_pushpull_output_opamp", "device_roles", "M20", "headroom_role", "mirror"],
  ["sf_pushpull_output_opamp", "device_roles", "M21", "headroom_role", "cascode"],
  ["sf_pushpull_output_opamp", "device_roles", "M22", "headroom_role", "cascode"],
  ["sf_pushpull_output_opamp", "device_roles", "M5", "headroom_role", "cascode"],
  ["sf_pushpull_output_opamp", "device_roles", "M6", "headroom_role", "mirror"],
  ["sf_pushpull_output_opamp", "device_roles", "M7", "headroom_role", "cascode"],
  ["sf_pushpull_output_opamp", "device_roles", "M8", "headroom_role", "mirror"],
  ["sf_pushpull_output_opamp", "device_roles", "M9", "headroom_role", "mirror"],
  ["two_stage_ota_sf", "_device_roles_autofilled", "M1", "headroom_role", "cascode"],
  ["two_stage_ota_sf", "_device_roles_autofilled", "M2", "headroom_role", "cascode"],
  ["two_stage_ota_sf", "_device_roles_autofilled", "M4", "headroom_role", "mirror"],
  ["two_stage_ota_sf", "_device_roles_autofilled", "M6", "headroom_role", "mirror"],
  ["two_stage_ota_sf", "_device_roles_autofilled", "M8", "headroom_role", "cascode"],
  ["two_stage_ota_sf", "device_roles", "M1", "headroom_role", "cascode"],
  ["two_stage_ota_sf", "device_roles", "M2", "headroom_role", "cascode"],
  ["two_stage_ota_sf", "device_roles", "M4", "headroom_role", "mirror"],
  ["two_stage_ota_sf", "device_roles", "M6", "headroom_role", "mirror"],
  ["two_stage_ota_sf", "device_roles", "M8", "headroom_role", "cascode"]
 ],
 "entry_removed": [
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M10"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M11"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M12"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M13"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M14"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M15"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M16"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M17"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M18"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M19"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M20"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M21"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M22"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M5"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M6"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M7"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M8"],
  ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M9"],
  ["sf_pushpull_output_opamp", "device_roles", "M10"],
  ["sf_pushpull_output_opamp", "device_roles", "M11"],
  ["sf_pushpull_output_opamp", "device_roles", "M12"],
  ["sf_pushpull_output_opamp", "device_roles", "M13"],
  ["sf_pushpull_output_opamp", "device_roles", "M14"],
  ["sf_pushpull_output_opamp", "device_roles", "M15"],
  ["sf_pushpull_output_opamp", "device_roles", "M16"],
  ["sf_pushpull_output_opamp", "device_roles", "M17"],
  ["sf_pushpull_output_opamp", "device_roles", "M18"],
  ["sf_pushpull_output_opamp", "device_roles", "M19"],
  ["sf_pushpull_output_opamp", "device_roles", "M20"],
  ["sf_pushpull_output_opamp", "device_roles", "M21"],
  ["sf_pushpull_output_opamp", "device_roles", "M22"],
  ["sf_pushpull_output_opamp", "device_roles", "M5"],
  ["sf_pushpull_output_opamp", "device_roles", "M6"],
  ["sf_pushpull_output_opamp", "device_roles", "M7"],
  ["sf_pushpull_output_opamp", "device_roles", "M8"],
  ["sf_pushpull_output_opamp", "device_roles", "M9"],
  ["two_stage_ota_sf", "_device_roles_autofilled", "M6"],
  ["two_stage_ota_sf", "_device_roles_autofilled", "M8"],
  ["two_stage_ota_sf", "device_roles", "M6"],
  ["two_stage_ota_sf", "device_roles", "M8"]
 ],
 "review_needed_removed": [
  ["nmcnr_amplifier", {"device": "M201", "note": "compensation.stage_devices 소속 -- gm_id_role 제안은 sizing_recipe.py의 _AUTHORITATIVE_GM_ID_SOURCES 가드(2026-08-14 신설)로 무시되므로 충돌 없이 안전하게 적용된다(사람이 참고용으로만 확인할 것, 자동 반영 자체를 막을 필요는 없음)."}],
  ["nmcnr_amplifier", {"device": "M301", "note": "compensation.stage_devices 소속 -- gm_id_role 제안은 sizing_recipe.py의 _AUTHORITATIVE_GM_ID_SOURCES 가드(2026-08-14 신설)로 무시되므로 충돌 없이 안전하게 적용된다(사람이 참고용으로만 확인할 것, 자동 반영 자체를 막을 필요는 없음)."}],
  ["two_stage_ota", {"device": "M4", "field_conflicts": {"headroom_role": ["cascode", "mirror"]}, "note": "이미 선언된 값과 제안이 달라 그 필드만 자동 반영하지 않음(다른 무관한 필드는 그대로 제안)"}],
  ["two_stage_ota", {"device": "M6", "note": "compensation.stage_devices 소속 -- gm_id_role 제안은 sizing_recipe.py의 _AUTHORITATIVE_GM_ID_SOURCES 가드(2026-08-14 신설)로 무시되므로 충돌 없이 안전하게 적용된다(사람이 참고용으로만 확인할 것, 자동 반영 자체를 막을 필요는 없음)."}]
 ]
}
```

* 질문 문안(제안): "B37a 뒤 위 데이터 블록의 항목(필드 58·소자 항목 40·review 항목 4)이 정확히 지워지고 그 밖은 그대로인 동작을 받아들이는가? 착수 시 다시 잰 목록이 이 목록과 한 항목이라도 다르면 이 승인은 적용되지 않는다."
* 원칙으로 말할 수 있는 것: 사라지는 값은 **이름 정규식이 입력을 BIAS로 분류한 유도**에서 나왔다. 그 유도는 넷 이름이 바뀌면 달라지므로(실측: 레일 밖 넷 이름만 바꾸면 3회로의 meta가 바뀐다) 근거로 쓸 수 없다. 그래서 자동 채움을 비운다.
* 원칙으로 말할 수 없는 것: 사라지는 값 하나하나가 **맞았는지 틀렸는지**. 예를 들어 사람이 선언한 4회로에서 입력쌍 `headroom_role`은 `cascode`라서, 세 회로 입력쌍의 base `cascode`는 사람 관례와 같은 값이었다. 값의 옳고 그름과 세 회로의 `headroom_role`·수직 그룹을 무엇으로 볼지는 회로 해석이므로 6a(DEC-35 ports·역할 제안표, J ratify)에서 공동분석한다. 이 승인은 그 판단을 하지 않는다.
* 세 회로 모두 SPECS 밖이라 지금 평가 수치(4회로 metric·sized 해시·거부 문구)는 그대로다(실측).
* 기존 test 기대값 변경은 0이다. selftest 17곳은 입력 픽스처에 `ports`(신호 입력이 없는 합성 픽스처는 `{}`)를 더하고, `test_s013` 두 호출에 `ports=`를 더한다(실측: 그렇게 보강한 사본에서 새 실패 0).

### Q2. 이 card의 입력으로 쓰는 `ports` 선언을 확인하는가(회로별)

B37a 뒤 아래 회로의 자동 채움·레이아웃 1차 그룹은 `ports` 선언으로 정해진다. 파일 안에 '사용자 확정' 주석이 있는 것은 folded_cascode·nmcnr_amplifier(그리고 '사용자 확인'의 current_reuse)뿐이다.
나머지는 추가 커밋 메시지의 "사용자 확정 넷 표"가 있으나, 그 표에 `ports` role(입력·출력 지정)이 들어 있었는지는 메시지만으로 확인되지 않는다. DEC-35 '확인' 단계를 건너뛰지 않으려고 묻는다.

| 회로 | `ports` 선언(role) | 파일 안 기록 | 추가 커밋 | B37a로 동작이 바뀌는가 |
|---|---|---|---|---|
| `ngcc_3stage_ff` | 입력 `Vinp`(differential_input_p)·`Vinn`(differential_input_n), 출력 `Vout`(single_ended_output) | 주석 없음 | `5459a44`(2026-09-16) "사용자 확정 넷 표: 소자 16, Cm1·Cm2·CL, 레일 선언 supply_nets" | **예** |
| `sf_pushpull_output_opamp` | 입력 `vin_p`·`vin_n`, 출력 `vout` | 주석 없음 | `4ea001f`(2026-09-15) "Allen L26 p.26-6 Fig. 7.1-1 전체 회로 …, 사용자 확정 넷 표" | **예** |
| `two_stage_ota_sf` | 입력 `vin_p`·`vin_n`, 출력 `vout` | 주석 없음 | `ad85c2c`(2026-09-15) "사용자 확정 넷 표 기준 connectivity만(스펙·symmetry 판정·sizing 필드 미정)" | **예** |
| `pushpull_follower_buffer` | 입력 `vin`(single_ended_input), 출력 `vout` | 주석 없음 | `ad85c2c`(위와 같음) | 아니오(실측 같음). 다만 B37a 뒤 선언이 판정 입력이 된다 |
| `common_gate_amplifier` | 입력 `vin`(single_ended_input), 출력 `vout` | 목적 설명(`vin`을 입력 전압원이 구동, 바이어스 넷은 포트 아님) | `31f9ad1`(2026-09-17) "판독한 넷 표를 사용자가 확정" | 아니오(실측 같음). 위와 같음 |
| `two_stage_ota` | 입력 `vin_p`·`vin_n`, 출력 `OUT` | 목적 설명 + 출력 포트 `OUT` '사용자 확정' | -- | review 목록만(Q1 표) |
| `current_reuse_telescopic_ota` | 입력 `Vip`·`Vim`, 출력 `Vop`·`Vom` | '사용자 확인' | -- | 아니오 |
| `folded_cascode`, `nmcnr_amplifier` | (각 파일) | '사용자 확정' | -- | 아니오 / review 목록만 |

질문 문안(제안): "B37a는 위 표의 `ports` 선언을 사실로 쓴다. ngcc_3stage_ff·sf_pushpull_output_opamp·two_stage_ota_sf(동작이 바뀌는 3회로)와 pushpull_follower_buffer·common_gate_amplifier의 입력·출력 포트 지정이 맞는가? 틀린 회로가 있으면 그 회로의 `ports`를 먼저 고친다(library 데이터 -- 사용자 수정)."

### Q3. sf_pushpull 레이아웃 1차 그룹(B37a 뒤 값)을 계약 test 기대값으로 고정하는가

V3(승인된 N2 범위)의 대상 변이 81개 중 하나 -- `resolve_stack_layout` 경로 3 분기를 통째로 지우는 변이 -- 는 계약 test(모의)와 기존 test 전체로 죽지 않는다(실측). 경로 3과 레거시 폴백 결과가 갈리는 입력이 library `sf_pushpull_output_opamp` 하나뿐이기 때문이다. 등가 변이가 아니다.
* 기본안: 고정한다. 계약 5(b)가 sf_pushpull의 B37a 뒤 그룹(`[M5,M6]`·`[M7,M8]`·`[M9,M10]`·`[M11,M12]`·`[M15,M16]` + 단독 `M17`~`M22`)을 단언한다. 이것은 Q1에서 받아들인 **동작을 고정**하는 것이지, 그 값이 회로상 맞다는 판정이 아니다. 6a(J ratify)가 이 값을 바꾸면 그때 기대값 변경이라 V5·DEC-40 승인을 받는다.
* 대안: 고정하지 않는다. 그 변이를 해시 묶음 면제로 통과시킨다(비등가 변이 면제 = 판정 약화, 사용자 승인).

## 2. 기록에 원칙 기본안으로 적기만 하는 것(질문 아님)

* `ports` 키 없음·`null`·dict 아님·항목 형식 오류(항목이 dict 아님, `role` 없음, 6어휘 밖, 빈 넷 이름)·`direction`과 role 모순은 거부한다. 명시적 `ports: {}`(입력·출력 0)는 받는다(B26-1 `supply_nets: []` 선례 -- '포트 없음'이라는 명시 선언).
* 포트 넷이 netlist·`passive_elements`·`ideal_sources` 단자 어디에도 없으면 거부, 포트 넷이 레일(`meta["rails"]`)이면 거부(선언은 사실이어야 하고 조용히 무시하지 않는다).
* `input_referred_offset_pairs`는 offset 쌍이 있는데 입력 넷이 0이면 거부한다(지금 `ports` 없음 거부의 취지를 유지).
* 연결 파일 `ports`는 진입 파일과 같아야 한다. 출력 role 0개는 받는다. role 어휘 6개는 닫힌 표다.
* 순서: B34 → B26-1 → (Phase 3) → CC-4a → B37a. 착수 조건: V3 게이트 card 둘(`20260930-v3-exempt-binding`, `20260930-v3-changed-stmt-scope` -- A1 승인) 병합.
* '출력은 포트만'(B37b 뒤 비포트 SIGNAL 넷을 출력으로 보지 않음)은 **이 기록에 넣지 않는다** -- `m_cascode` 방향 판정의 회로 해석이라 B37b card의 결정 항목이다.

## 3. 승인 기록 초안(답을 받은 뒤)

```
id: 20260930-b37a-ports-roles
target_kind: decision
target: 20260930-b37a-ports-roles
user_quote: <Q1 답 원문> / <Q2 답 원문> / <Q3 답 원문>
scope: B37a 동작 변경 수용 -- 아래 '항목 단위 삭제 목록'의 항목이 정확히 지워지고 그 밖은 base 그대로(이름 의존 유도라 무효인 자동 채움 삭제.
       값의 옳고 그름은 6a J ratify로 넘김)와 E3 레이아웃 1차 그룹 변화(Q1 E3 줄), Q2 표의 ports 선언을 B37a 입력으로 확인,
       Q3(sf_pushpull E3 값 test 고정 또는 면제), §2 원칙 기본안. 목록을 잰 base 커밋: <착수 시 재측정 커밋>.
       재검토: 착수 시 재측정 목록이 이 기록의 목록과 한 항목이라도 다르면 이 기록은 적용되지 않는다(새 목록으로 다시 묻는다).
```

승인 기록 본문(위 머리 아래)에 반드시 넣는 것 -- Phase 4 design v0.9.5 §6 D47의 기대값 출처:
* 제목 `## 항목 단위 삭제 목록(D47)` 아래에 **착수 시 재측정한** 데이터 블록(Q1 json 블록과 같은 형식 -- `list_id`·`base_commit`·`pairs`·`field_removed`·`entry_removed`·`review_needed_removed`)을 ```json 펜스로 그대로 싣는다. `base_commit`은 그 재측정 판. 'N개 사라짐' 같은 산문으로 바꾸지 않는다.
* 그 블록 원문(LF)의 sha256과 적용 규칙 (1)~(4)(Q1 '항목 단위 삭제 목록' 문단) 한 줄씩.
* 재측정 목록이 이 파일 Q1 블록(`dd60db6`)과 같으면 sha256이 `7c1871a6977a21fe…`와 같다(같은 원문일 때). 다르면 사용자에게 새 목록으로 다시 묻는다.
