# design 20 §10 E4 정정 문안 (최종본) + D2 결정 반영

기준: gate `master` cd64170(2026-09-30), 저장소 읽기 전용. 사용자 결정 2026-09-30: "둘다 기본안으로 진행해"(D1 = E4 기본안, D2 = (a) 관찰 기록).
**이 정정은 DoD 판정 기준 변경이다** -- 오케스트레이터 문서 커밋만으로는 안 되고 사용자 승인 기록이 먼저 있어야 한다(E1 정정 선례 `20260930-p9-e1-correction`과 같은 형식).
승인 기록 id: **`20260930-phase2-e4-baseline`**(`target_kind: diff`, `diff_path: docs/02-design/features/gain-budget-gmid-sizing.20-dead-code-dup.design.md`,
`diff_base` = 정정 직전 커밋, `diff_head` = 정정 커밋, `target` = 00-common §8.2 diff 해시). 사용자 원문 칸에는 위 결정 원문을 그대로 옮긴다.

---

## 1. 현재 문안 (design `docs/02-design/features/gain-budget-gmid-sizing.20-dead-code-dup.design.md` **222행**)

```
| E4 | 동작 보존 | `PT` 전체(실패 0)와 E-LIB·E-INST 재측정 | Phase 1 DoD와 같은 값(회로 9/9 로드, instance.json 해시 동일) |
```

잴 수 없는 이유(실측):
* Phase 1 DoD 기록 `docs/03-analysis/gain-budget-gmid-sizing-10-test-separation/phase1-dod.md`(781f405)에 E-LIB·E-INST·instance.json 값이 없다(`grep -c "E-LIB\|E-INST\|instance.json"` → 0).
  비교할 'Phase 1 DoD 값'이 기록에 없다.
* DF-36 `20260930-df36-instance-relpath`(red-green, 판정 기록 148bd6d V2 PASS)가 instance.json `topology_ref`를 절대 경로에서 저장소 루트 기준 `/` 상대 경로로 **의도적으로** 바꿨다.
  raw 해시 동일은 원리상 성립하지 않는다.

## 2. 비교 기준 커밋 확인

* **`da03c0e`** = `da03c0e3084bb0549eb876228296c5a69938d2c1`, "docs: C10 완료 기록, 문서 백로그 B10", `Role: doc`, 부모 0939174(C10 `20260923-caa970b-replay` 판정 기록).
  `phase1-dod.md` 3행 "대상: gate `master` = `da03c0e`(Phase 1 마지막 card C10 완료 기록까지)" -- **Phase 1 DoD를 잰 커밋**이다.
* 엔진 트리: Phase 1 마지막 병합 `e5fa76b`(merge 20260923-v4-decision-exempt)와 da03c0e의 `A/*.py`·`A/library`·`workspaces/run_harness.py` diff 0 -- da03c0e = Phase 1 마지막 병합본의 엔진.
* `da03c0e..cd64170`: 103커밋, 엔진·하네스·library를 바꾼 비병합 커밋 25개(전부 card 역할 커밋 -- prep_phase2_dod §2). library `*.topology.json` diff 0, 하네스는 DF-35 +4/-3뿐.
* da03c0e 하네스는 메인 체크아웃 절대 경로 리터럴 3개(35행 `sys.path.insert`, 42행 `ASSETS_DIR`, 44행 `WORKSPACES_DIR`)를 가진다 -- DF-35 auditor 스크립트 base 모드의
  기대 개수 (ASSETS 2, WORKSPACES 1)와 같다. 그대로 돌리면 메인 저장소 workspaces에 쓰므로 반드시 base 모드(복제본 경로 치환)로 돌린다.
* `stick_diagram.load_topology`·`run_topology_pipeline`·`save_instance_json` 세 def 모두 da03c0e에 있다(8757·8949·9174행; cd64170은 8550·8742·8984행) -- E-LIB 스크립트가 두 판에서 돈다.

## 3. 교체 문안 (최종본 -- 222행을 이 한 행으로 바꾼다)

```
| E4 | 동작 보존 | `PT` 전체. 그리고 **같은 격리 복제본 `<iso>`(같은 체크아웃 경로)** 에서 `git -C <iso> checkout --detach da03c0e`(Phase 1 DoD 대상 커밋, `phase1-dod.md` 3행) 판과 Phase 2 마지막 card 병합본 판을 차례로 떠 E-LIB·E-INST를 잰다(판을 바꿀 때마다 `git -C <iso> checkout -- workspaces`·`git -C <iso> clean -fdx` 로 산출을 지운다). E-LIB = `.ai/verification/20260930-df36-instance-relpath/scripts/e_lib.py <iso> <out>`(두 판 같은 스크립트). E-INST(회로 `current_reuse_telescopic_ota`·`folded_cascode`) = da03c0e 판은 `.ai/verification/20260930-df35-harness-paths/scripts/e_inst_df35.py <iso> <회로> base <out>`(하네스의 메인 체크아웃 경로 리터럴 ASSETS 2·WORKSPACES 1개를 같은 표기의 `<iso>` 경로로 치환), 병합본 판은 `.ai/verification/20260930-df36-instance-relpath/scripts/e_inst_df36.py <iso> <회로> <out>`(치환 없음, 리터럴 0개 요구) | `PT` 실패 0(수집 수는 Phase 1과 다르므로 비교하지 않는다). E-LIB: 두 판 모두 library 9/9 로드(`_TEMPLATE` 제외), `e_lib.py` 결과 해시(`hash`)가 두 판에서 같다. E-INST: 두 회로 모두 (a) `without_topology_ref_sha256`(`topology_ref`를 뺀 instance.json의 키 정렬 compact JSON sha256)이 두 판에서 같다 (b) 병합본 판 `topology_ref` = DF-36 계약 1 기대값 `skills/analog-gmid-design/assets/library/<topology 파일>`(`topology_ref_equals_expected_contract1` true), 경로 문자열 잎 0 (c) da03c0e 판 `topology_ref`는 `<iso>`의 ASSETS 경로와 `library/<topology 파일>`을 이은 절대 경로(`topology_ref_is_join_of_ASSETS_DIR` true -- 같은 파일). (2026-09-30 정정, 승인 `20260930-phase2-e4-baseline`: 옛 기준 'Phase 1 DoD와 같은 값(회로 9/9 로드, instance.json 해시 동일)'은 (1) Phase 1 DoD 기록에 E-LIB·E-INST 값이 없고 (2) DF-36(`20260930-df36-instance-relpath`, red-green)이 `topology_ref`를 절대 경로에서 저장소 상대 경로로 의도적으로 바꿔 raw 해시 동일이 원리상 성립하지 않아 잴 수 없었다. 비교 기준을 Phase 1 DoD 대상 커밋 da03c0e의 같은 경로 실측으로 바꾸고, 의도적으로 바뀐 `topology_ref` 하나만 DF-36 계약값으로 따로 판정한다) |
```

### 3.1 측정 절차 (auditor 브리핑용 -- design 행에는 넣지 않는다)

1. 격리 복제본 하나 `<iso>`(`--no-hardlinks --no-local`, origin 제거, `core.longpaths=true`), 가드 4줄(격리 경로·`git -C`·`set -e`·끝나면 reflog/status). 다른 E 행과 같은 `<iso>`를 쓴다.
2. 스크립트 사본: 위 세 파일을 scratch로 복사해 쓴다. 드라이버 `einst.sh`(두 폴더에 있음)는 출력 경로(`C:/g14`·`C:/g16` 하드코딩)만 바꿔 쓴다. 스크립트 본문은 고치지 않는다
   (고치면 그 diff를 판정 기록 basis에 적는다).
3. `git -C <iso> checkout --detach da03c0e` → 산출 정리 → E-LIB → E-INST base(두 회로) → 산출 정리.
4. `git -C <iso> checkout --detach <Phase 2 마지막 card 병합본>` → 산출 정리 → E-LIB → E-INST(두 회로) → 산출 정리. `PT` 전체도 이 판에서.
5. 비교: E-LIB `hash` 한 쌍, E-INST 회로마다 `without_topology_ref_sha256` 한 쌍과 (b)(c) 플래그. 판정은 auditor 보고 그대로 `phase2-dod.md`에 옮긴다(오케스트레이터 재계산 없음).
6. 시간 참고(DF-35 판정 기록): 파일럿 E-INST 1회 131~178 s, folded 15~19 s -- 두 판 합쳐 약 7분.
7. 불일치가 나오면 E4 FAIL로 보고하고, 어느 card에서 달라졌는지는 card별 판정 기록 V2 사슬로 좁힌다(아래 4의 대안 문안이 그 사슬이다).

## 4. 대안 문안 (참고 -- 채택하지 않음)

```
| E4 | 동작 보존 | `PT` 전체와, Phase 2 card 판정 기록 전부의 `checks.V2` basis | `PT` 실패 0, 엔진·하네스·library를 바꾼 da03c0e 이후 비병합 커밋이 전부 card 역할 커밋이고 그 card 판정 기록마다 E-LIB·E-INST base = 병합본(DF-36은 `topology_ref`를 뺀 값) |
```
새 측정이 없어 싸지만 E4가 따로 재는 것이 없어지고(card 기록을 다시 읽을 뿐), card 사이의 base 공백·기록 누락을 잡지 못한다 -- 기본안은 Phase 양 끝을 한 번 직접 대조한다.

---

## 5. D2 결정 반영 -- P3c 보류분 `A/tests/probe_physical_consistency.py`

**결정(사용자 2026-09-30, 기본안 (a))**: Phase 2 DoD는 E2 문구(`tests/probes/**`)대로 판정하고, `phase2-dod.md` '남긴 관찰'에 다음을 적는다. 추가 card 없음.

> P3c 보류(백로그 B21, Phase 4 -- 2026-09-29 사용자 "보류, P5로 진행"). `A/tests/probe_physical_consistency.py`는 tests 루트에 남아 `engine_dup_scan.py`(범위 `tests/probes/**`) 밖에 있다.
> 같은 스캐너를 이 파일에 적용하면 발견 1건: 40행 `rail-set`(`RAIL_HI, RAIL_LO = {"vdd", "VDD"}, {"gnd", "GND", "vss", "VSS"}`). 메인 체크아웃 절대 경로 리터럴 2개(33행 `ASSETS`, 38행 `INST`)도 있다.
> 처리는 B21(Phase 4)에서 -- 레일 집합의 topology 무관 정본(`supply_nets` 선언에서 읽는 경로)이 B26으로 먼저 생겨야 한다.

비용 비교(짧게, 기록용 -- (b) 작은 card를 택하지 않은 이유):
* **대체할 정본이 아직 없다**: 스캐너가 제시하는 교체 대상은 `sizing_recipe._DEFAULT_RAIL_HI/_DEFAULT_RAIL_LO`(engine_dup_scan.py 35행)인데, 레지스트리 §2 '레일 넷 집합' 행은 이를
  "정본 없음 -- 이름 기반 상수는 정본이 아니다 … 상수 하나로 합치는 것은 해결이 아니다(B26)"로 적는다. 그 상수를 import하게 바꾸면 스캐너 발견은 0이 되지만 이름 리터럴 종속을 다른 곳으로
  옮길 뿐이고(B26 영역), `supply_nets`를 probe가 직접 읽게 하면 엔진에 없는 레일 해석을 probe가 새로 구현하는 것이라 E2가 막으려는 것 자체가 된다.
* **영구 test가 움직인다**: `tests/probes/`로 옮기면 `contracts/test_ts6_probe_relocate.py:419-423`(probes/ 집합 = 32개 고정)이 깨진다 -- 기대값 변경이라 test-author 수정 + V5 승인이 필요하고,
  P3c spec card `20260923-probe-promote-consistency` 계약 1(`unit/test_probe_physical_consistency.py`가 생기고 원본이 없어진다)과도 어긋나 spec card 개정이 같이 필요하다.
* 경로 리터럴 2개 상대화, 읽는 `workspaces/current-reuse-telescopic-ota-report/current_reuse_telescopic_ota.instance.json`(추적 파일)의 경로 유도도 함께 바뀐다(P2의 깊이 보정·상대화와 같은 작업).
* 합계: test-only card 1건 + V5 승인 1건 + spec card 개정 1건, 그리고 B26 전이라 결과가 정본 호출이 아니다 -- Phase 2 DoD의 판정값(E2)은 바뀌지 않는다.
