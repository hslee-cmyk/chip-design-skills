# card 묶음 b 독립 판정 (2026-11-04)

대상: 브랜치 `docs/cards1104b` head `831db0d4`(master `e33100cc` 대비 전체 diff). 계획 v6.38.9, design v1.16.5, HC-D v0.1.1, card `20261104-eo1r4-sf1l`, card `20261104-hcs`, 위임 A-45~A-48.

방법: 문서 읽기와 `git grep`·`git show`·`sed`. 실행 없음(pytest·LUT·엔진 0). 엔진 인용은 재작성 범위·호출 자리 확인뿐이다(원칙 8). 작성자 설명은 원문과 대조했다.

## card별 판정

| card | 판정 | Major | 비고 |
|---|---|---|---|
| EO-1 범위 4 + SF-1 로더 조각 | V1·V2·V3 정정 뒤 test 가능 | V1, V2, V3 | 표 10행·닫힌 식·E-1·E-2·E-4 식은 맞음 |
| HC-S | V2 정정 뒤 test 가능 | V2 | m3·m4·m8 |
| 계획 v6.38.9 | 표 6행·정본 (3) 문언은 맞음. 소유 card 누락은 V1 | V1 | m6·m7 |

**멈춤(위임 밖) 0.** 세 Major 모두 근본원칙 변경·connectivity·기준 약화가 아니다. V1은 기준을 조이는 쪽이고 card 배정이라 O-226 위임 안이다.

**순서 위반 표지**(오케스트레이터 전달, 원문 확인): design v1.16.5 `77bada20`가 계획 v6.38.9 `831db0d4`보다 먼저 커밋됐다. history에 기록돼 있다. 내용 차이는 없고 이 판정이 묶어서 본다. 위반 사실은 지워지지 않는다.

## Major

**V1. 봉인 6을 경계 0으로 바꾸는 card가 없다** (소유 card 없음, 계획·as-built 불일치 방치)

- **as-built**: `sizing/seal_bulk_reverse.py:20-25`, READS `device.dc_tol_v`, `forward = max(0, −vsb, −(vds + vsb))`, `rows.append((m, forward, tol_v[m], ...))` → 옛 '크기 ≤ tol_V' 판정. `integ/it12`도 같다(:14·:23·:24). `sizing/CONTRACT.md:583`도 같다.
- **계획**: 표 6행·정본 (3)·O-210 RR-7은 경계 0 V를 요구한다. 그러나 `봉인 6` 출현은 P:422(결정), 658·662(표), 1348(WB-1 실측 조건), 1509(E-0), 2138·2142(design 후속 정정), 2555(E-35)뿐이다. N6.1, N6.5, N6.6, N6.20 어디에도 범위로 없다. N6.20 (4) 제목은 '봉인 7·9 맞춤'이다.
- **design**: 41 §4.7-W W8과 40:1163이 규칙을 적지만 파일·card 없음. W8 머리 '재동결 입력'의 대상 IT-2c·IT-2d card(`HEAD`, `integ/it12`, `card/it2c`의 `docs/02-design/specs/20261104-it*`)에 `봉인 6`·`seal_bulk_reverse`·`표 10행`·`RR-7` 0건. 42:98은 `52 vsb | OK | seal_bulk_reverse.py`라 gap 분석도 못 잡는다. 브랜치 `docs/cards1104c`·`docs/cards1104d` 0건.
- **결과**: EO-1 M-6·착수 5는 '옛 tol_V면 멈추고 보고'이고, base는 옛 판정이 거의 확실하므로 그 자리에서 card가 멈춘다. 멈춘 뒤 고칠 card가 없다. 멈추지 않으면 선언 소자는 tol_V까지 순방향을 받고 off 소자는 0 V에서 거부해 A-47이 막으려던 '경계 갈라짐'이 그대로 남는다. 표 6행 '크기 무관 거부'에 fail-open이다. 같은 칸의 표 10행 소유도 spec '표 10행 tol_V 미정(IT·W8)'이라 적혔지만 IT card에 없다.
- **소유 대안 비교**:

| 안 | 물리 정합 | 단순성 | 판단 |
|---|---|---|---|
| EO-1 범위 4에 넣음 | off 절과 같은 병합에서 경계 일치 | 같은 결정(O-210), 바로 다음 병합, 파일 1개 | **권고** |
| IT-2c에 넣음 | 일치 | 재동결·test worktree 진행 중이라 되돌림 | ⚠ 진행 중 card 정지(원칙 19) |
| 새 card | 일치 | card 수 증가, 그 사이 경계 갈라짐 | 이점 없음 |

- **A-47 근거의 귀결**: 'off를 봉인 6과 같은 식으로, 판정식을 둘로 두면 경계가 갈라짐'이 근거인데 card는 식을 두 자리에 따로 적게 한다. 입력이 달라(`dc_op` 대 `off_op`) 둘째 생산자는 아니지만 식 사본이다. 순수 함수 하나로 둔다.

**고칠 문언**

계획 N6.20 범위 (4) 제목: '공용 영역 판정 함수 하나와 **봉인 6 경계 0**·봉인 7·9 맞춤·`off` 선언 처리'. (a) 앞에 다음을 넣는다(N6.1 범위 표기는 그대로).
> (a0) **봉인 6 경계 0**(O-210 RR-7, 정본 (3), 작성자 유도 -- 다른 card에 소유가 없었음): 판정을 '순방향 크기 > 0 = 거부'로 바꾸고 tol_V는 띠 기록에만 쓴다. 식 = 순수 함수 하나, 봉인 6과 `ss_off_op`이 함께 부른다. 동작 변경(변화표 항목).

완료 (8)에 '(c′) 순방향 크기 < tol_V toy → 봉인 6 거부(옛 판정이면 통과 -- red), 역바이어스 띠 toy → 통과 + 기록, tol_V 미정 → 항목 6은 미정이 아니고 그 점 봉인 불가는 표 10행 toy로 확인'을 더한다.

design 41 §4.8-3 끝 bullet 다음:
> **봉인 6**: `E/sizing/seal_bulk_reverse.py` 재작성. READS `device.dc_op`, `device.dc_tol_v`(띠 기록 전용). 소자마다 `junction_forward(op.vds, op.vsb)`; 값 > 0 ≥ 1건 → fail, devices = 그 소자; 아니면 pass. detail `indistinct` = 순방향 0이고 min(vsb, vds + vsb) < tol_V인 ((소자, 그 값), ...), `band_undefined` = tol_V None 소자. margin·tol None. `E/sizing/junction_forward.py`: `junction_forward(vds, vsb) -> float` = max(0, −vsb, −(vds + vsb)). 부르는 자리 = 봉인 6, `ss_off_op`. **표 10행**: 봉인 6이 tol_V를 판정에 안 쓰므로 tol_V 미정 점의 봉인 불가는 tol_V를 판정에 쓰는 남은 항목이 낸다. T-S8이 잠그고, 잠기지 않으면 멈추고 보고한다.

42 `52 vsb` 행 상태 'OK' → 'MISS(card EO-1 범위 4)', D-EO1에 `봉인 6 경계 0`·`junction_forward` 추가. 40 §11 EO 행 재작성 칸에 `seal_bulk_reverse.py`, 새 파일에 `junction_forward.py`. 41 W8 끝에 '소유 = card EO-1 범위 4'.

spec: 재작성 범위 표에 `sizing/seal_bulk_reverse.py` 행과 `sizing/junction_forward.py`(신규), test 몫에 `tests/sizing/test_seal_bulk_reverse.py`(있는 파일, base에서 확인), `tests/sizing/test_junction_forward.py`. 착수 조건 5행 삭제. '이 card에 없는 것'에서 '표 10행 tol_V 미정(IT·W8)' → '표 10행 판정 자리 신설 없음(T-S8)'. 원래 취지와 다름에 '범위 4에 봉인 6 추가(계획 개정)'.

interface §2 표 다음:
> **봉인 6** `dc_seal_bulk_reverse(snapshot)` READS `device.dc_op`, `device.dc_tol_v`. `junction_forward(vds, vsb) = max(0, −vsb, −(vds + vsb))`(`gmid_engine.sizing`). 값 > 0 소자 ≥ 1 → fail, 아니면 pass. detail `indistinct`, `band_undefined`. `tol`·`margin` 단언 금지.

interface §4 `off_bulk_forward` 행: 'max(0, −vsb, −vdb) > 0' → '`junction_forward(vds, vsb)` > 0'.

interface §6 추가:
| T-S8 | `tests/sizing/test_seal_bulk_reverse.py` | 순방향 크기 = tol_V/2(이진 분수) → fail(옛 판정 통과 -- red). 역바이어스 tol_V/2 → pass + `indistinct`. 경계 vsb = 0·vdb = 0 → pass. tol_V None → 항목 6 pass + `band_undefined`, 보고서 상태 ≠ sealed(다른 항목이 미정) | (손) | red |
| T-S9 | `tests/sizing/test_junction_forward.py` | vsb·vds 조합 손계산 넷(부호 nmos·pmos는 T-O3b), 호출 자리 grep = 둘 | (식) | red(부재) |

interface §7 M-6: '§2 grep 0, `git diff --name-only -- E/graph` 0, `structure.json` 변경 0'만 남기고 'base 봉인 6 확인' 문장을 지운다. M-1 red 목록에 T-S8.

library 영향: 옛 판정 통과 + 새 판정 거부가 있을 수 있다. **미측정**, 변화표(LA-1 측정 시점) 원인 칸 = 이 card.

**V2. 관문이 `triode` 역방향 VDS 소자에서 정의되지 않고, HC-D는 그 칸을 '해당 없음'이라 적었다** (자기 card 표와 모순, 사유 없는 실패)

- EO-1 §1 행 4: `triode`, current > 0, VDS < 0 → `triode`, mismatch False. T-S6: 'triode → 통과'. 이 소자는 봉인을 통과해 관문 대상(§4 '선언 없음 + `triode`')으로 온다.
- EO-1 §4: VDSAT′ = VDSAT + Σ. 봉인 쪽은 'VDS < 0이면 LUT 조회 없이 `None`'인데 관문의 **기준** VDSAT은 규칙이 없다. '보정 조회 축 밖 = `OUT_OF_DOMAIN`'은 보정점 문장이다.
- HC-S §2: 기준 VDSAT = 필드 `vdsat_v`. 이 소자는 `reverse_vds`라 None이다. `None + Σ` = `TypeError`(후보 실패 부류 밖, 실행 전체가 사유 없이 끝남). HC-D §3.4 관문 행 `reverse_vds` 칸은 '해당 없음(봉인 통과 점)'이라 사실과 다르다.
- 다른 칸은 맞다: 열 없음은 `STATUS_PENDING_SEAL7`이고 `search/kernel.py`가 `STATUS_SEALED`일 때만 `ss_evaluate`를 불러 관문에 오지 않는다. `lut_domain`은 봉인 9 미정이라 역시 오지 않는다.
- 물리: VDS < 0에서 LUT VDSAT은 없다. VDS′ < 0이면 행 4(vdsat 값 안 봄)로 통과가 맞고, VDS′ ≥ 0이면 VDSAT′을 모르므로 행 5 거부가 fail-closed다. 실제 경로 도달 여부는 미측정이나 표가 통과시키는 입력이므로 정의가 있어야 한다.

**고칠 문언**

EO-1 interface §4 관문 VDSAT′ 줄 뒤(41 §4.8-7 보정값 끝에도 같은 뜻):
> VDS < 0 소자(`triode`만 봉인을 통과해 온다): 기준 VDSAT 조회 0, vdsat 입력 = `OUT_OF_DOMAIN`, 보정 조회 0. VDS′ < 0이면 표 행 4 통과, VDS′ ≥ 0이면 행 5 거부. 수치 문턱 없음.

EO-1 interface §6 T-G5 뒤:
| T-G6 | 같은 파일 | `triode` VDS < 0: ΔV로 VDS′ < 0 → 통과, VDS′ = 0 → `off_gate`, VDS′ > 0 → `off_gate`. 그 소자 `vdsat` 호출 0 | (손) | -- |

HC-S interface §2 관문 행 끝: '`vdsat_v` None(사유 `reverse_vds`, `triode`만 도달) = EO-1 §4 그대로 `OUT_OF_DOMAIN`, `sat_threshold` 호출 0.' §4 S11에 '`reverse_vds` 주입 → T-G6과 같은 결과, 예외 0'.

HC-D §3.4 관문 행 `reverse_vds` 칸: '해당 없음(봉인 통과 점)' → '`triode`만 도달: `OUT_OF_DOMAIN`, 조회 0(41 §4.8-7)'.

**V3. LUT 축 끝 공개 함수에 이름·파일·test 자리가 없다** (구조 규칙 A·H, 소스 없는 test 불가)

- 41 §4.8-3 '축 끝 읽기는 LUT 공개 함수 하나를 더한다', spec '`lut/` 공개 함수 하나'. interface에 이름이 없고 §6에 test 행이 없다.
- 규칙 A(`structure_checks.py:233` `entry_points`, `check_a` '정확히 1개'): 기존 파일에 더하면 새 뿌리라 그 파일이 위반이다(예: `axis_guard.py`의 `check_axes`와 뿌리 둘). 그래서 새 파일이다.
- 규칙 H(`check_h`): 새 파일 `lut/<x>.py`는 `tests/lut/test_<x>.py`가 있어야 한다. 그 test는 test 역할 몫인데 interface만 보는 test 작성자가 이름을 모른다. 그대로면 M-2 구조 위반으로 돌아온다. 앞 판정 V2와 같은 부류다.

**고칠 문언**

interface §1 뒤 또는 §2 `domain_edge` 줄 앞:
```text
lut_axis_bounds(memo, kind, w_key) -> ((축, 첫 값, 끝 값), ...)   # gmid_engine.lut, 축 = AXES 순서, 값 사본 필드 없음
```
§2 `domain_edge` 끝의 '축 이름·판정식은 작성자 판단.' 삭제. spec 재작성 범위 행: '`lut/axis_bounds.py` | 신규: `lut_axis_bounds` | D41:870'. §6:
| T-S10 | `tests/lut/test_axis_bounds.py` | r4 격자 전 축 첫·끝 값 손으로, 없는 슬라이스 `KeyError` | (손) | red(부재) |

41 §4.8-3 '축 끝 읽기는 `E/lut/axis_bounds.py` `lut_axis_bounds` 하나'.

## 항목별 판정

| # | 항목 | 판정 | 근거 |
|---|---|---|---|
| 1 | 소스 없이 기대값 | V2·V3 외 가능 | 닫힌 식 s′ = s + (1 − a2)ΔVDS − a1ΔVGS − a3ΔVSB 직접 유도 일치. T-O1 ΔV_x = −ΔI/G_xx, 주입 nmos d −ΔI·s +ΔI, pmos 반대: KCL 일치. T-S3 tol = 0.25·(1/8)²/4 = 1/1024 이진 분수. `r4_*`·`seal_item`·`tamper`는 `tests/sizing/conftest.py`에 있고 `from sizing.conftest import`가 선례(`test_passive_values.py:136`). `R4_VS` 음수 포함, `R4_VDS`·`R4_VGS` 0 포함이라 T-O3b `vsb = 0, vds = 0` 축 안 |
| 2 | 계획↔design↔card | V1 외 맞음 | §1 10행 = D41 표. P:1361~1366 줄 인용 맞음. `커널 = 봉인 전 항목`(P:664)은 7행 G2-a 선례와 같은 꼴이라 실효 모순 아님(m6) |
| 3 | graph 정본 | V1의 식 사본 외 위반 없음 | writer 넷 D40:477~480, `dc_sat_v` D40:455. E-3 관문 READS + 보정점 호출은 다른 입력이라 둘째 생산자 아님. E-4 off 판정은 `dc_op`에 없는 소자라 둘째 생산자 아님. `vds_floor`: 같은 LUT memo의 derived 영역, 슬라이스당 1값이고 as-built `block_columns:118`을 옮기는 것뿐이라 **승인 예외(LUT memo) 범위 안**, 새 cache 아님(m3) |
| 4 | E-1 | 맞음 | `constraint_classes.py`: 값 None → notes, 목적 축 → judged, 레지스트리 → ss(index), 그 밖 notes. 합집합이 '판정 제약'과 정확히 같다. `declared`는 같은 extras 참조, 사본 아님. `SchemaRejectedError`는 `CANDIDATE_FAILURE_CLASSES` 밖(`test_failure_classes.py:93`)이라 후보 실패로 삼켜지지 않음: fail-closed. `verified_by`는 레지스트리 밖 `KeyError`, 규칙이 사유로 바꿈(m5) |
| 5 | E-2 | 분할 맞음, V3·m4 남음 | 손 대입 아래 |
| 6 | E-4 | 식 동치, 정지 순서 맞음, **소유 card 없음 = V1** | 아래 |
| 7 | 물리·배선 | V2 외 맞음 | 삭제 대상 소비자 grep = spec 목록과 일치(코드 16파일 + test 15파일). `dc_off_current` 소비자 `tools/` 0, 엔진 오라클 `off_current_A`는 주석뿐. 상수·회로 이름·PDK 값 0(회로 이름은 audit 연기 시험 대상만). DC·AC: 관문은 ss G로 DC 보정만 |
| 8 | base·착수·A-34·GL-1 | 맞음(V1로 착수 5 삭제) | `S1V_RULE_FILES`·`STRUCTURE_RULE_EXTRA_FILES`는 `graph/`뿐이고 두 card 범위 밖, `linear_devices`의 `graph/` 소비자 0. 래칫: 모듈 수준 값 타입 없음, `_vds_floor` `stale` |
| 9 | 원칙 8 | 맞음 | 엔진 인용은 재작성 범위 + 소비자. D41 §4.8-6 '`.judged`는 목적 축뿐' 이유는 as-built 칸 사실이지만 SF-1 범위 8이 인자를 지운다고 적어 재작성 범위로 읽힌다 |

**E-2 손 대입**(`entry_points`: 공개 def 중 같은 파일 다른 최상위 문이 이름을 안 읽는 것 = 뿌리, `len(concepts) == 1`):

| 파일 | 공개 정의 | 뿌리 | 결과 |
|---|---|---|---|
| `sizing/region_judge.py` | `judge_region`, `RegionJudgment` | `judge_region`(본문이 클래스를 읽음) | 통과 |
| `sizing/region_mismatch.py` | `region_mismatch` | 1 | 통과. 한 파일이면 뿌리 둘 위반이었다: A-46 인용 맞음 |
| `lut/sat_threshold.py` | `sat_threshold`, `SatBound` | `sat_threshold` | 통과 |
| `lut/sat_threshold_grid.py` | `sat_threshold_grid` | 1 | 통과 |
| `lut/derived_fns.py` | `derived`(`_vds_floor`는 비공개) | 1 | 통과 |
| `metrics/ss_off_op.py`, `ss_off_delta.py` | 블록 + 값 클래스 | 블록 | 통과 |
| `metrics/ss_off_gate.py`, `search/off_judged.py`, `sizing/seal_region.py`, `region_decl.py` | 1 | 1 | 통과 |
| HC-1 뒤 `lut/sat_threshold.py` + `stack_unsat` | `sat_threshold`, `SatBound`, `stack_unsat`, `StackJudge` | `sat_threshold`, `stack_unsat`(`stack_unsat`은 `sat_threshold_grid`를 읽어 `sat_threshold`를 안 읽음, HC-D §7.2) | **뿌리 둘 위반**: m4 |

**E-4 대입**: nmos p = +1: vsb = Vs − Vb, vdb = Vd − Vb, 표 6행 Vs·Vd ≥ Vb ⇔ vsb·vdb ≥ 0. pmos p = −1: vsb = Vb − Vs, vdb = Vb − Vd, Vs·Vd ≤ Vb ⇔ vsb·vdb ≥ 0. max(0, −vsb, −vdb) > 0 ⇔ 순방향. 동치. 순서: 세 사유 모두 그 점 E-0이라 결과는 같고 사유만 갈린다. 벌크 → 축 밖이 맞다(벌크는 물리, 축은 표본 범위. VS 축이 음수를 포함해도 잡힘). VGS 먼저는 O-212 정지와 일치하고, 함께 있을 때 벌크 사유가 안 적히는 손실은 판정을 안 바꾼다. vds < 0 ∧ vdb ≥ 0 = `off_outside_lut`은 정본 (5) (다)와 일치.

## Minor (막지 않음)

- m1. **`detail["reason"]`**: `FailureRecord.detail`은 정렬 tuple이다(`failure_record.py`). 관례 = `dict(exc.record.detail)["reason"]`. EO-1 interface §4·§5 문언을 그렇게.
- m2. **EO-1 spec 계약 7**에 `off_bulk_forward` 없음. 'VGS < 0 = `off_vgs_negative`, 벌크 접합 순방향 = `off_bulk_forward`, 그 밖 LUT 축 밖 = `off_outside_lut`, 모두 그 점 E-0'.
- m3. **`vds_floor` 메모 상한**: `lut_memo.py:114` derived 상한 = 슬라이스 수 × `DERIVED_TABLES` 길이('퇴출이 없도록 개수 그대로'). as-built `sizing_vds_floor`도 목록에 없어 이미 하나 모자란다. HC-S 재작성 범위에 '`lut/lut_memo.py` `DERIVED_TABLES`에 `vds_floor`', test 몫에 `tests/lut/test_lut_memo.py:28`.
- m4. **`stack_unsat` 자리**: HC-D :253·:297을 '`E/lut/stack_unsat.py`(`stack_unsat`·`StackJudge`, 구조 규칙 A, test `tests/lut/test_stack_unsat.py`)'로. HC-S spec '규칙 A 다시 확인' 문장은 '자리는 HC-D §7.2'로. 이번 판에 같이 고치면 HC-1 card 재작업이 준다. HC-S 판정은 막지 않는다.
- m5. **슬루 문장**: 41 §4.8-6 '레지스트리 밖 oracle 전용 항목(슬루)은 `unverified`로 정지'. 실제 경로에서 그 metric은 notes로 가 표 둘째 행 `off_judged_by_not_judged`가 먼저다. 둘 다 정지. '`not_judged`로 정지(레지스트리 밖 + 판정 칸 직접 구성은 T-J1에서만 `unverified`)'.
- m6. **계획 문언**: P:664 끝에 '표 6행 off 절·7행 G2-a 보정 판정은 첫 ss 층에서 재며 봉인 보고서 항목이 아니다.' (5) (다) 'VGS < 0·LUT 축 밖 E-0 검사', (라) 같은 문구를 'VGS < 0·벌크 접합·LUT 축 밖'으로. (마) 평가 순서 '봉인 전 항목 통과 → ss 층 `device.off_op` → `graph.ss_nodal`'.
- m7. **판 표기**: 40·41·42 `plan_version`·Status '계획 기준', 두 spec 머리 `P:`가 v6.38.8이다(인용 줄은 안 밀림). 6.38.9로. v6.38.9 history 절이 문서 끝 별도 절이라 `## Version History` 표에 행이 없다.
- m8. **HC-S §3 '전도·기존 분지 마스크'**: test가 정의를 모른다. '분지 = on_mask ∧ VGS ≥ 같은 (L, VDS, VS)에서 gm/ID 최대인 VGS 마디'. S7은 gm/ID 단조 LUT로 잡으면 마스크가 전 칸 참이라 단언 금지와 양립한다.
- m9. **`edge_costs` 전도 조건**: HC-S '전도·`id_equivalent` 조건은 그대로'. as-built `_conduction_ok`는 gm·tol_V ≥ I_off 꼴이고 정본 (1)은 전도 수치 문턱을 지웠다. EO-1 '`conduction_mask`(GC-7)'와 같은 card인지 이 판정에서 대조하지 않았다. 소유 확인을 HC-S '이 card에 없는 것'에 한 줄로.
- m10. **spec `region_decl.py` '파일 이름은 작성자 판단'**: T-D1이 `test_region_decl.py`로 정해 규칙 H상 이름이 정해졌다. 문구 삭제.
- m11. **T-R2 위치** '같은 파일'이 `test_region_mismatch.py`인데 내용은 `judge_region`이다. `test_region_judge.py`로.
- m12. **A-48에 off 띠 없음**: 표 6행은 'LA-1 완료 13 재점검'이라 적었는데 재점검 입력 A-48에 그 항목이 없다. 오케스트레이터 기록에 한 줄.
- m13. **VDS = 0 열**: conftest 주석상 LUT v2 VDS = 0 열은 전류 0이다. 양 단자가 같은 off 소자(vds = 0)는 벌크·축 검사를 지나 `op_point`에서 다른 사유로 끝날 수 있다. fail-closed이고 **미측정**. T-O3b에 `off_cols=1` 변형을 더하면 사유가 드러난다.

## 미측정·미확인

- 전부 실행 안 함: pytest, LUT, 13회로, 연기 시험, `ratchet.new`, scan_shared_calls, 결정성.
- 실제 경로에서 VDS < 0이 `device.dc_op`에 도달하는지(`dc_widths`가 먼저 끝날 수 있음). V2는 표가 통과시키는 입력이라 도달과 무관하게 적었다.
- 봉인 6 경계 변경의 library 영향(V1), 표 10행이 남은 항목으로 잠기는지(T-S8로 잰다).
- `search/search_context.py` 호출자가 `SchemaRejectedError`를 어디서 보고하는지(스테이지별 except는 stop 경로로 grep만).
- `test_seal_bulk_reverse.py`는 있다(`git ls-files`). 그 안의 옛 tol_V 기대값은 읽지 않았다. T-S8 작성 때 `broken_tests` 이유 'O-210 RR-7'로 교체한다. `junction_forward.py`·`axis_bounds.py` 이름은 비어 있다.
- ⑩ 결정 간 모순 점검은 O-225로 하지 않았다. 원문 PDF 해당 없음.

쓰기: 이 파일 하나.

1차 판정(head `831db0d4`): Major 3

## 재판정 (head `dd33c964`)

대상: `831db0d4..dd33c964`. 계획 v6.38.10 `17f0126f`, design v1.16.6·HC-D v0.1.2 `391aa9c4`, card `dd33c964`. 방법은 위와 같다(실행 없음). 작성자 보고가 아니라 diff와 원문으로 확인했다.

### 반영 확인

| 항목 | 판정 | 확인 자리 |
|---|---|---|
| V1 | 반영 | 계획 (a0)·(c′)·제목, 41 §4.8-3·W8·T-S8·T-S9, 42 `52 vsb` MISS·D-EO1, 40 §11, spec 범위·착수 5 삭제·계약 14, interface §2·§4·T-S8·T-S9·M-6 |
| V2 | 기준점은 반영, **보정점 칸 누락 = R1** | EO-1 §4·T-G6, 41 §4.8-7, HC-S §2·S11, HC-D §3.4 |
| V3 | 반영 | interface §2 `lut_axis_bounds`·T-S10, spec `lut/axis_bounds.py`, 41 §4.8-3 |
| m1, m2, m3, m4, m5, m8, m10, m11 | 반영 | 문언대로 |
| m7 | 반영, 잔여 하나 | `plan_version`·Status·`P:`·Version History 행 맞음. 40:14 `Planning Doc ... v6.38.5`가 남음(r3) |
| m13 | 반영, 문언 과함 | r1 |
| m6 | 미반영(전달대로) | 그대로 minor. 아래 r4와 같이 처리 권고 |

**m9 판단**: 'GC-7 소유로 읽힘'은 **맞다.** P:673 '`conduction_mask` 칸 전도 술어(graph-consumption GC-7 -- 술어 = ID > 0으로 줄어듦)', graph-consumption plan:687 '`cell_floor`·`edge_costs`·`current_box` 셋 다 그 함수를 부르고', 같은 history:333 '네 번째 자리 `derived_fns.py:36-47` `_conduction_ok`(`edge_costs`)'. 다만 GC-7은 LA-1 공통 선행 15 card에 없다. 그래서 LA-1 측정 때도 `edge_costs` VGS 비용에는 gm·tol_V ≥ I_off 조건이 남는다. 봉인 판정이 아니라 탐색 하한이므로 fail-open은 아니다(거짓 거름 쪽). HC-S '이 card에 없는 것'에 '`edge_costs` 전도 조건 = GC-7, LA-1 측정 시점 변화표에 잔존 표지' 한 줄을 권한다(r5).

### Major

**R1. HC-S 관문: 보정점 VDS + ΔVDS < 0에서 `vdsat_v` None, 사유 사상이 없다** (V2의 나머지 칸, 1차 판정에서 내가 놓침)

- HC-S §1 행 1: vds < 0 → `sat_threshold`는 `vdsat_v` None, `reverse_vds`. 관문은 X = VDS 항에서 vds + ΔVDS로 이 함수를 부른다.
- HC-S §2 관문 행과 HC-D §3.4는 보정점 사유로 `lut_domain` → `OUT_OF_DOMAIN`만 적었다. `reverse_vds`는 없다. 기준 VDS ≥ 0, VDS + ΔVDS < 0이면 항이 `None − vdsat(X)`로 `TypeError`다. 후보 실패 부류 밖이라 실행이 사유 없이 끝난다.
- 도달 입력: `triode` 스위치의 VDS ≈ 0(ΔVDS < 0 하나면 된다), 또는 선언 없는 소자의 작은 VDS. 표가 막지 않는 입력이다.
- EO-1 판에서는 `vdsat`이 축 밖 → `OUT_OF_DOMAIN`이라 정의돼 있다. 즉 HC-S 재배선이 동작을 바꾼다. 물리: 이 입력은 VDS′ = VDS + ΔVDS < 0이고, 행 3·4가 vdsat 값을 안 보므로 `OUT_OF_DOMAIN`이어도 선언 없음 = 거부, `triode` = 통과로 맞다.

**고칠 문언**

HC-S interface §2 관문 행: '보정점 vdsat(X + ΔX) = `sat_threshold(...).vdsat_v`, 사유 `lut_domain` → `OUT_OF_DOMAIN`.' → '보정점 vdsat(X + ΔX) = `sat_threshold(...).vdsat_v`, 사유 `lut_domain`·`reverse_vds` → `OUT_OF_DOMAIN`(`reverse_vds`는 LUT 조회 0).' HC-D §3.4 관문 행 괄호를 같은 뜻으로. 41 §4.8-7 **HC-S 뒤** 문장 끝에도 같은 괄호.

HC-S interface §4 S11 끝: '기준 VDS ≥ 0, VDS + ΔVDS < 0 주입: 선언 없음 → `off_gate`, `triode` → 통과, 둘 다 예외 0.'

EO-1 interface §6 T-G6 끝(이 card에서도 같은 입력을 잠가 HC-S와 비교 기준으로 쓴다): '기준 VDS ≥ 0, VDS′ < 0: 선언 없음 → `off_gate`(행 3), `triode` → 통과(행 4), 보정 조회 축 밖은 `OUT_OF_DOMAIN`.' 41 T-G6에도 같은 줄.

### 새 모순 점검

| 질문 | 판정 | 근거 |
|---|---|---|
| `junction_forward` 규칙 A | 통과 | 공개 def 하나, 뿌리 1 |
| 규칙 H | 통과 | `tests/sizing/test_junction_forward.py`, `tests/lut/test_axis_bounds.py` 명시. `test_seal_bulk_reverse.py`는 이미 있음 |
| 층 순서 | 통과 | `LAYER_ORDER` sizing < metrics라 `ss_off_op` → `gmid_engine.sizing` 가능. sizing 안 층은 `seal_bulk_reverse.py`가 셋째 층(`_module_map.py:114`)이고 이 함수는 import가 없어 아래 층에 둘 수 있다. spec이 `_module_map.py`를 범위에 포함 |
| graph | 통과 | 값 저장 없음, 입력이 달라 둘째 생산자 아님. `lut_axis_bounds`는 축 읽기, 사본 필드 없음 |
| 봉인 6 ↔ 띠 기록 | 맞음 | 표 6행·정본 (3) '역바이어스 크기 tol_V 미만 = 기록만', 'tol_V 미정 = 띠 미정'과 `indistinct`·`band_undefined` 일치. 경계 0은 min = 0 < tol_V라 pass + `indistinct` |
| 봉인 6 ↔ 표 10행 | 맞음, 근거 문장 낡음 | 봉인 2(`seal_vgs_match.py`)가 `dc_op` 모든 MOS 행에 `tol_v[m]`을 쓰고 `judge`가 None → undefined, `dc_seal_report`가 undefined → `sealed=None`. 그래서 T-S8 '보고서 ≠ sealed'가 봉인 6·9 없이도 성립한다. 단 P:1806은 그 기제를 '봉인 9 행의 tol None(`seal_conduction.py:43-46`)'으로 적었고 이 파일은 EO-1이 지운다(r2) |
| P:1348 WB-1 '봉인 6 tol_V' | 새 모순 아님 | 착수 전 고칠 문언 표의 행이고 '착수 조건(문언)'으로 살아 있다. Q-T0(P:1223)는 tol_V 셀 구성 질문이라 남는다. 다만 EO-1 병합 뒤 봉인 9 ε·봉인 6 tol_V는 Q-T0의 판정 입력이 아니다(r2) |
| 봉인 6 margin None | 표지 누락 | 41 '`margin·tol` None'이면 `layer0_center.py:271` 여유 행에서 항목 6도 빠진다(r6) |

### test 작성자 대입

| test | interface만으로 | 비고 |
|---|---|---|
| T-S8 | 가능, 마지막 절만 경로가 흐림 | 앞 셋: `tamper`로 `dc_op`·`dc_tol_v` 주입 후 블록 호출, 기존 `run` 꼴. '보고서 상태'는 `seal_dc`가 `dc_tolerances`를 다시 돌려 주입을 덮을 수 있다(r7) |
| T-S9 | 가능 | 식 명시 |
| T-S10 | 가능 | `R4_GRIDS` 첫·끝 값, `KeyError` 명시 |
| T-G6 | 가능 | `dc_op`·`graph.ss_off_delta` 주입으로 VDS′ = 0 정확값. 기대 행이 §1 표에서 나온다. `s_prime` 값만 미정(r8) |
| S11 | 기준점 가능, 보정점은 R1 뒤 | EO-1 T-G6 참조 |

### Minor (막지 않음, 번호는 재판정 안)

- r1. **T-O3b `off_cols=1` 문언**: '정지 사유를 기록하고 fail-closed임만 단언'은 정지를 전제한다. VDS = 0에서 전류 0은 물리적으로 맞아 정지 없이 ΔI_off = 0일 수 있고, 그러면 test가 틀린 이유로 red다. → '정지하면 사유 있음, 정지하지 않으면 ΔI_off = 0. 사유 없는 예외 0(어느 쪽인지는 **미측정**이라 단언하지 않음)'.
- r2. **계획 문언**: P:1806 '봉인 9 행의 tol이 None(`seal_conduction.py:43-46`)' → '봉인 2 행의 tol이 None'. P:1348 칸 끝에 'EO-1 범위 4 뒤 봉인 9 ε 삭제, 봉인 6 tol_V = 띠 기록 입력만'.
- r3. 40:14 `Planning Doc` v6.38.5 → v6.38.10(41 §4.8 판 표기와 맞춤).
- r4. m6 미반영분: P:664 한 문장, (5) (다)(라) '벌크 접합', (마) `device.off_op` 순서.
- r5. HC-S '이 card에 없는 것'에 `edge_costs` 전도 조건 = GC-7 한 줄(위 m9).
- r6. EO-1 spec '원래 취지와 다름' 1: '봉인 7·9 ... 이 두 항목' → '봉인 6·7·9 ... 이 세 항목'.
- r7. T-S8 마지막 절: '보고서 상태 ≠ sealed(다른 항목이 미정)' → '같은 주입 스냅샷의 `dc_seal_vgs_match` 항목 2 = undefined(보고서 sealed 불가의 근거)'.
- r8. EO-1 §4 `off_gate` 행: 'detail `s_prime` = ((소자, s′), ...), `OUT_OF_DOMAIN`이면 s′ = None'.
- r9. M-5 출력 전용 목록에 `dc_seal_6` `indistinct`·`band_undefined`, `dc_seal_7` `indistinct_undefined` 추가.

### 미측정

pytest·LUT·13회로 전부. 봉인 6 경계 0의 library 새 거부 수. 특히 소스가 풀이로 레일과 같아지는 넷에서 −1e-16 꼴 순방향이 거부되는지(O-210 '크기 무관'이라 규칙상 거부, 변화표에서 확인). VDS′ 항의 실제 도달. ⑩ 결정 간 모순 점검은 O-225로 하지 않았다.

쓰기: 이 파일 하나.

재판정(head `dd33c964`): Major 1

## 최종 재판정 (head `185190c7`)

대상: `dd33c964..185190c7`만. 계획 v6.38.11 `71d33224`, design v1.16.7·HC-D v0.1.3 `21e1936c`, card `185190c7`. 방법은 위와 같다(실행 없음). diff와 head 원문으로 확인했다.

### 반영 확인

| 항목 | 판정 | 확인 자리 |
|---|---|---|
| R1 | 문언대로 | HC-S §2 '`lut_domain`·`reverse_vds` → `OUT_OF_DOMAIN`(`reverse_vds`는 LUT 조회 0)', HC-D §3.4, 41 §4.8-7, HC-S S11 끝, EO-1 T-G6 끝, 41 T-G6, HC-S spec 재작성 행 |
| r1 | 문언대로 | EO-1 T-O3b |
| r2 | 작성자 문언이 **맞음** | P:1806 실제 문장은 '봉인 9 행의 tol이 None이라'였고 '봉인 2 행의 tol이 None이라 undefined로 판정되어'가 됐다. 지워질 파일 인용 삭제도 맞다(head에 `seal_conduction.py:43-46` 0건, 옛 문언은 history에 있음). 뒤 `E/sizing/seal.py:13` 인용은 그대로 유효한 재작성 범위 사실이다. P:1348 보강도 문언대로 |
| r3 | 작성자 문언이 **맞음** | 40:14 v6.38.11. 내 문언 v6.38.10은 판이 오르기 전 값이다 |
| r4 | P:664·(다)·(라) 문언대로, (마)는 자리가 다름(f1). '규칙 변경 없음' 보고는 **맞음** | 벌크 접합 = v6.38.9, `device.off_op` 첫 ss 블록 = A-12, off 절 자리 = v6.38.9. 새 조건·문턱·자리 없음 |
| r5 | 뜻대로 | HC-S spec '이 card에 없는 것' 바로 아래 표지. 내용 충분 |
| r6 | 문언대로 | EO-1 spec 원래 취지와 다름 1 |
| r7 | 문언대로 | EO-1 T-S8, 41 T-S8 |
| r8 | 문언대로 | EO-1 §4 `off_gate` 행 |
| r9 | 문언대로 | EO-1 M-5 |

### M-6 표지

**잡음 흡수 상수 없음.** '−1e-16 꼴'은 표지 문장의 예시이고 판정식·허용값이 아니다. '판정식에 문턱을 넣지 않는다(O-210 RR-7, 원칙 1)'가 명시돼 있고, 41에는 그 값이 0건이다. `junction_forward` 식과 '값 > 0 = fail'은 이 diff에서 그대로다.

### 새 모순

없음(Major 기준). 대조: 인라인 수정이라 `P:`·D40·D41 줄 인용이 안 밀린다. T-G6 새 줄은 §1 표 행 3·4와 맞고 EO-1 §4 '보정 조회 축 밖 = `OUT_OF_DOMAIN`'과 맞다. S11 새 줄은 T-G6 새 줄과 같은 결과라 재배선 전후 동작이 같다. P:1806 새 근거는 앞 판정에서 읽은 봉인 2 행 구조와 맞다. 판 표기 40·41·42·HC-D·두 card 모두 v6.38.11·v1.16.7·v0.1.3.

### Minor (막지 않음)

- f1. **r4 (마) 평가 순서가 두 문장이다.** 머리 괄호에 '봉인 전 항목 통과 → ss 층 `device.off_op` → `graph.ss_nodal`'을 더했는데, 같은 (마) 뒤쪽 원문 '평가 순서 = 봉인 전 항목 통과 → ss 층 `graph.ss_nodal` → (라) ΔV 기록 블록 → 이 관문 → ...'이 남았다. 앞부분 생략이라 뒤집히지는 않지만 정의 자리가 둘이다. 머리 괄호를 지우고 뒤 문장을 '봉인 전 항목 통과 → ss 층 `device.off_op` → `graph.ss_nodal` → (라) ΔV 기록 블록 → 이 관문 → ...'으로.
- f2. **M-6 '거부가 나면 멈추고 보고한다'의 대상이 흐리다.** 탐색 중 봉인 6 거부는 옛 판정에서도 있고, library 변화표는 보류라 M-6에서 잴 자리가 없다. fail-open은 아니다(멈추는 쪽). → 'M-8 연기 시험에서 순방향 크기 < tol_V로 봉인 6에 거부된 점이 있으면 소자·크기를 판정 기록에 적고 멈추고 보고한다.'

### 미측정

pytest·LUT·13회로 전부, 봉인 6 경계 0의 library 새 거부 수. ⑩ 결정 간 모순 점검은 O-225로 하지 않았다. 이 판정은 위 diff 범위만 봤다.

쓰기: 이 파일 하나.

verdict: Major 0
