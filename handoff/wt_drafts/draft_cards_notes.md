# P9 / P10(+B22 b) spec card 초안 -- 메모 (base gate `master` 070cf69, 2026-09-30)

초안: `draft_p9.spec.md`(`20260930-p9-kcl-edges`), `draft_p9_design_patch.md`(design 20 정정 문안), `draft_p10_b22.spec.md`(`20260930-p10-df23-inventory`).
추가 scratch 측정(읽기 전용): `p10_phase2_names.py`(+`.out.txt`), `p9_railtwice.py`(+`.out.txt`). 저장소 변경 없음(`git status`는 시작 때와 같음).

## A. 사용자에게만 물을 것 (spec·회로 해석·삭제 승인)

1. **design `20-dead-code-dup` E1·§6.2·§8 P9 정정 승인(`20260930-p9-e1-correction`)** -- 승인된 design의 DoD 판정 기준을 바꾼다:
   (a) `kcl_series_union`은 지우지 않고(KCL 그룹 함수, 운영 호출 2곳) 본문의 중복 엣지 정의만 정본 호출로 바꾼다 -- E1의 "`kcl_series_union` 참조 0"을 없앤다.
   (b) E1의 `_multilinear_interp_point_multi` 참조 0 기준도 없앤다 -- §1이 이 Phase의 DUP 대상을 W 계산·KCL 엣지 둘로 한정했고 이 이름을 다루는 card가 없다(다선형 보간 DUP는 이 Phase에서 하지 않는다는 뜻).
   (c) `_metric_kcl_residual`을 P9 대상에서 뺀다(엣지를 만들지 않는 다른 개념 -- 겹치는 부호 규약·레일 이름 집합은 Phase 3·4).
   문안은 `draft_p9_design_patch.md` 1~4. 승인 방식 선택: 기본안은 정정 커밋 뒤 `target_kind: diff` 승인 기록 하나(`20260930-p9-e1-correction`)를 받아 P9 card에 `approval` 두 줄.
   계획 N3.12.3 "승인 기록이 둘 이상 필요하면 나눈다"가 걸린다고 보면 design v1.3 전체 재승인 하나로 바꿀 수 있다 -- 사용자 선호 확인.
2. **library topology.json 주석 필드의 낡은 이름 정리 여부** -- `current_reuse_telescopic_ota.topology.json` 1250·1281(`suggest_headroom_stack_groups`), 1872(`_metrics_comment`, telescopic family),
   `nmcnr_amplifier.topology.json:74`(`slew_rate()`). topology.json은 쓰기 경로표상 승인 기록 조건이고 E-LIB 입력이다. 기본안: 이번 card들에서 건드리지 않고 두며, 고치려면 별도 승인
   (주석 필드만, connectivity 불변).
   
그 밖에는 사용자 결정이 필요 없다(P9 = 순수 connectivity 규칙의 동작 보존 통합, P10 = 담당 Phase를 계획 DF 표에서 읽음). 픽스처 함수 `folded_cascode_example`·`two_stage_ota_example`의
삭제·이동은 이번 범위가 아니다(목록에서 Phase 3로 표시만) -- 나중에 지우려면 그때 삭제 승인이 필요하다.

## B. prep(`prep_p9_p10.md`)을 다시 재서 틀렸거나 빠진 것

1. **P9 library 회로 수**: prep §4 "8 loadable ... 16/16" → 실제 **9회로 × 2입력 = 18/18**(prep 자신의 회로 목록과 `p9_diff.out.txt`도 9개). `_TEMPLATE`만 로드 실패.
2. **레일 이름 DF가 없다는 주장이 틀림**: prep §8 "§11-1 ... Not yet in plan (no rail-name DF)" → 계획 **DF-19**(929행, 레일 넷 집합이 모듈마다 다름, 담당 4, "위치 열은 전수여야 한다 -- 운영부 29개 함수")와
   **DF-26**(936행, 레일 판정이 넷 이름 집합 하드코딩, 담당 4)이 이미 있다. 따라서 design §11-1의 "DF 번호가 없다 → DF 신설 요청"도 틀렸다. 레일 리터럴 항목은 새 DF가 아니라 DF-19·DF-26에 묶는다(P10 계약 3).
3. **E1의 추가 결함 두 개(prep 미기재)**: (a) `_multilinear_interp_point_multi`는 Phase 2 대상이 아닌데 E1이 참조 0을 요구 (b) E1 명령 경로 `tests/unit -k "dup_"`은 차등 test가 있는 `tests/contracts/`를
   수집하지 않는다(P8 test도 contracts). 또 `-k "dup_"`은 P4의 `test_probe_dup_scan.py`까지 잡는다.
4. **P10에 레지스트리 기록을 넣으면 doc-only가 아니다**: prep §10 후보 계약 3(레지스트리 DF-23 기록 + `reg_check` exit 0)을 문서 card에 넣었지만 레지스트리는 gmid-code-author 전용 경로(N3.12.2
   -- 오케스트레이터 `docs/03-analysis/**` 행이 레지스트리를 제외)라 code 커밋이 생긴다 → test-only 불가. 초안은 분리했다(별도 red-green card 기본안).
5. **줄 번호 일치를 영구 test로 두면 안 됨**: prep §10 후보 계약 2(항목 줄 = base 소스, 0 stale)를 영구 test로 두면 이후 엔진 card마다 줄이 움직여 전부 막힌다(P2 영구 바이트 대조가 P4에서 폐기된 선례).
   초안은 auditor 측정(P10 계약 7)으로 옮겼다. 같은 이유로 "어휘와 정확히 같은 문자열 상수 전수 포함" 검사도 영구 test로 두지 않았다(새 회로가 `bias`·`out` 같은 넷을 들이면 무관한 card가 깨진다).
6. **B22 (b) 대상 줄 누락**: prep 표 A는 telescopic family 선택 키 언급 `SKILL.md:74`·`known-incidents.md:125`를 빠뜨렸다(P5b가 키를 지웠다). 초안 계약 5의 대상은 19줄.
   반대로 prep 표 A의 `consistency-map.md:207·209`는 맞고, 단어 `fT` 자체는 물리량 표기라 호출형 `.fT(`만 대상이다(단어 대조는 64곳 거짓 양성).
7. **줄 번호 세부**: `_metric_kcl_residual` 부호 규약은 SR 4301-4309가 아니라 **4307·4309**. 나머지 prep 줄 번호(SD 2983·3003·3042·3134·3148·7310, SR 4267·4293·8055, 레지스트리 43·308·428·472~474)는 재측정과 같다.
8. **B22 정의의 출처**: 저장소 문서에서 B22 (a)/(b)/(c) 정의 원문을 찾지 못했다(`.ai/context.md`·docs grep -- `20260929-probe-engine-dup.spec.md`가 "(c)"만 언급, `20260930-restore-plan-functions.spec.md`가 "B22 문서 card" 언급).
   history의 B22는 2026-09-09의 다른 항목(`diode_vds_window`)이다 -- 같은 번호가 두 뜻으로 쓰인다. card 커밋 전에 백로그 원문 위치를 인용하거나 번호를 새로 매기는 것이 안전하다.
9. **레지스트리 누락**: `stick_diagram.folded_cascode_example`·`two_stage_ota_example`(픽스처 넷리스트, test에서만 호출)은 레지스트리 어느 절에도 행이 없다 -- 목록(P10)에는 Phase 3로 적고,
   레지스트리 보강은 분리된 레지스트리 card에서 함께 하는 것이 자연스럽다.
10. prep의 원칙 기본안(P9: `kcl_series_union` 유지·본문만 정본 호출, `_metric_kcl_residual` 제외, 정본 후보 상태 유지, equivalence; P10: 재측정 + phase 필드, 분리 목록)은 재측정으로 맞았다.
    두 엣지 규칙은 줄 단위로 같고 union 순서(내부 넷 → 매칭 쌍)도 같아 결과가 비트 단위로 같다. 레일 이름 넷이 정확히 2회 쓰이는 경우(레일 제외가 결과를 바꾸는 유일한 경우)는 library에 `two_stage_ota`의 `gnd` 하나다.

## C. 오케스트레이터 참고 (결정은 초안 안에 기본안으로 적음)

* P9 판정 유형: equivalence. 계약 1(구조 AST)은 base에서 AssertionError가 나지만 P5b 선례("equivalence는 red 필드에 쓰지 않는다", 새 test 8건 base FAIL·병합본 PASS로 V2 PASS)를 따른다.
  auditor가 이것을 V2 FAIL로 볼 위험이 있으면, 계약 1을 영구 test에서 빼고 auditor AST 측정으로만 두는 대안이 있다(그러면 새 test는 base·병합본 모두 PASS).
* P9 영구 test는 레일 이름 규칙을 계약으로 삼지 않게 했다(레일 이름 넷은 2회 사용 위치에 두지 않음) -- B26(Phase 4)이 `supply_nets`로 바꿀 때 기준 약화(V5) 없이 가도록.
* P10은 순서 1에서 문서 커밋을 먼저 gate에 반영해야 test-only 모양이 된다(새 test가 base에서 통과). auditor는 문서 커밋 직전 커밋에서 새 test가 실패함을 기록한다(계약 8).
* design 20 §8 P10 행·§11-1 정정은 사실 정정(같은 뜻)이라 P7·P8 선례처럼 오케스트레이터 문서 커밋으로 충분하다고 보았다 -- E3 판정 기준은 바뀌지 않는다.
