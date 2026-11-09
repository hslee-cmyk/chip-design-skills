# P9 / P10 spec card 초안 재검증 -- 변경 기록 (HEAD = gate `master` cd64170, 2026-09-30)

대상: `draft_p9.spec.md`(`20260930-p9-kcl-edges`), `draft_p10_b22.spec.md`(`20260930-p10-df23-inventory`). 초안 base 070cf69.
저장소 변경 없음(`git status`는 시작 때와 같음: `.bkit/state` 두 파일만 M). scratch 재실행 출력은 `_drafts`에만 썼다
(070cf69 판 사본: `p9_diff.out.070cf69.txt`, `p9_railtwice.out.070cf69.txt`, `p10_df23.out.070cf69.txt`, `p10_phase2_names.out.070cf69.txt`, `b22_scan.out.070cf69.txt`).

## 0. 070cf69 -> cd64170 사이에 바뀐 것 (git diff --stat)

* `A/stick_diagram.py`: DF-36 한 곳(8964행 뒤 `save_instance_json` 부근, +17/-1). P9가 인용하는 2983·3003·3023-3048·3134-3154·3206·3291·7304-7310·8550·8643행은 그대로.
* design 20: 6398a28 정정(134 §6.2, 136 차등, 193 §8 P9 -- slug `p9-kcl-edges`, 196 판정 유형 문장, 218 E1). design 05: V3 행 ④(B28).
* 승인 기록 `20260930-p9-e1-correction`(diff 6398a28), `20260930-v3-history-clone`. contracts에 `test_df36_instance_relpath.py` 추가.
* 불변: SR, 레지스트리, library, 계획서, references, SKILL.md, `workspaces/run_harness.py`, unit test.

## 1. 재측정 결과 (움직인 숫자만 고침)

| 항목 | 070cf69 | cd64170 | 초안 반영 |
|---|---|---|---|
| SD `_RAIL_NETS` 참조 줄 | 18 | 18 | 같음 |
| P9 호출 위치 SD 3206·3291·7310, SR 8055, SD 8643 | 같음 | 같음 | 둘러싼 def 줄(3158·3261·7304·7930·8550) 추가 |
| P9 DIFF-DUP 9회로 × 2입력 18/18, 그룹 수 | -- | 바이트 동일 재실행 | 같음 |
| 레일 이름 넷 정확히 2회 사용 | `two_stage_ota` `gnd` | 같음 | 같음 |
| 레지스트리 43·308·428·472·473·474 | -- | 같음, reg_check exit 0 | 8(a)에 43행 '(stick_diagram 3148행)' 병합 뒤 낡음 추가, 8(b)에 472행 SD:3298·3188-3212 명시, 8(c) 낡은 줄 번호 전부 나열(308의 4448 포함) |
| `1e2e243..HEAD` 커밋 수 | 93 | **101** | P10 의도·실측 고침 |
| DF-23 목록 590(324/266), 13/211/42 | -- | 같음 | 같음 |
| references 대상 19줄, Phase 2 이름 23개 | -- | 바이트 동일 | 같음 |
| 분리 표 줄(SR 15·4737·4743·5015, unit 2765·2791·2824, topology 1250·1281·1872, nmcnr 74) | -- | 같음 | 같음 |
| test glob | -- | `test_df36_instance_relpath.py:58` `*.topology.json` 추가(library 전용) | 충돌 없음 명시 |
| DF 표 행(929·933·936·939~944) | -- | 같음 | 같음 |
| design 20 소비자 줄 | 134·193·218(정정 대상) | 88·134·136·193·218(정정 완료) | P9 실측 5 고침 |

## 2. P9 변경

1. 머리: `approval` 두 줄(`20260923-20-dead-code-dup-design`, `20260930-p9-e1-correction`) -- 두 파일 모두 `.ai/approvals/`에 있음. parse_spec_card 통과.
2. 의도: 정정된 design §6.2(134행) 원문 두 단락 인용(통합 방향, `_metric_kcl_residual` 제외). B26 출처(`.ai/context.md` 14963행) 추가.
3. '결정 필요 항목'에서 E1 승인 요청 삭제 -> "없음" + 사용자 원문·승인 기록·커밋(6398a28·ab90ec5). approval 두 줄 관련 N3.12.3(674행)은 선례(`20260929-probe-engine-dup`·`20260930-restore-plan-functions` 각 3줄)로 '결정 아님' 처리. 계획 N6.2 `2` "옛 함수 삭제" 문장은 승인 범위 밖임을 참고로 적음.
4. **계약 1(구조 AST)을 영구 test에서 auditor AST 측정으로 옮김**, 계약 6(b)도(같은 이유 -- base에서 어긋남). 계약 3은 (a) auditor `ast.dump` 불변 / (b) 영구 test 모양으로 나눔.
   근거(판정 유형 근거 절에 인용):
   * 계획 N3.12.3 순서 3(680행) "equivalence면 base에서 통과 확인", 686행 "base와 병합본 모두 통과", N4.2 V2(838행) "base·병합본 모두 PASS".
   * design 05 §10-4(289행)는 모양만 정하고 증거는 V2(§10-6) -- 예외 조항 없음.
   * 선례 P5 `20260923-d-delete-dead`(GONE test base AssertionError, V2 PASS)·P5b `20260923-d-delete-telescopic`(8건 base AssertionError, "equivalence는 red 필드에 쓰지 않는다", V2 PASS)는
     auditor 해석일 뿐 규칙 문장에 없음. 반대 선례 P8 `20260930-dup-w-calc`(AST 판정 base 18개 실패 -> red-green).
   * red-green 전환은 승인된 design §8 P9 행(equivalence)과 어긋나 재정정 필요 -> 택하지 않음.
   * 대가: 재인라인 회귀를 영구 test가 못 잡음 -> 레지스트리 §2·§6 기록과 Phase 3 MOD3 이동 AST 해시가 대신 봄.
   * E1과의 정합: design E1은 P9 기계 판정을 "계약 1"로 가리키고 명령은 `tests/contracts -k "dup_w_calc or dup_kcl_edges"` + 판정 기록 V2 -- 계약 1을 auditor가 V2 basis에 적으면 그대로 성립.
     새 test 파일 이름 `test_dup_kcl_edges.py`가 `-k dup_kcl_edges`에 걸림.
5. V3 주의 추가: 바뀐 def `kcl_series_union`이 변이 대상 -- 합성 입력이 변이를 죽이도록.
6. '작성 전 실측' 전체를 cd64170 기준으로 다시 씀(쓰기 경로표 줄 번호 599·603·618·621-622 포함).

## 3. P10(+문서 백로그 B22 (b)) 변경

1. topology.json 주석: 사용자 결정 원문 인용, **보류(범위 밖, 백로그)**로 확정 -- 분리 표·결정 절 반영. '결정 필요 항목' = 없음.
2. **B22 두 뜻 해소**: 정의 원문 = `.ai/context.md` 14943행(2026-09-23 P5 기록, (a)(b)(c)) + 합류 14950·14966·14977행. 다른 뜻 = history §10.3 B22(4002행, `diode_vds_window` mirror_members, 2026-09-09 해소)
   -- 엔진 주석 SR 567·3425·7412, 레지스트리 77행이 이 뜻. 원인: context 백로그 번호(B6~B28)가 history B 번호(§10.3 B1~B25, 규칙표 B10~B21)와 따로 매겨져 겹침.
   card 본문은 항상 '문서 백로그 B22'로 쓰고 두 출처를 명시, id·test 이름에 `b22` 안 씀. 제안: 이후 context 백로그를 `BL-` 접두사로(옛 기록 불변, 대응 한 줄).
   (c)는 P4 `20260929-probe-engine-dup` 계약 4에서 처리됨. (a)와 14950 합류 test 주석이 남으므로 card 뒤에도 문서 백로그 B22는 열림.
   계약 5가 B22 (b)의 원래 5줄(+99행)보다 넓은(19줄) 이유를 '원칙은 계약에 전 범위로'로 명시.
3. 판정 유형 test-only 근거 보강: design 05 §10-4 표 290행(코드 커밋 없으면 test-only 모양만 EL4 통과), design 05 §18 557행(`10-test-separation` R2: code 커밋 없는 게이트 데이터 변경 = test-only),
   design 20 §8 P10 행. 계획 687·838행의 test-only 증거 문장은 TS용(섹션 매핑표)이라 이 card의 V2 해석을 적음(기존 test 전부 + 새 test base PASS, 순서 4·5 없음) + 계약 7·8.
4. 쓰기 주체를 계획 N3.12.2 표 줄 번호로 대조: 목록 626(레지스트리 제외), design 624, references 640, SKILL.md 638, skill-validation-prompt 639, test 618, auditor 621·622, 레지스트리 603(code-author -> 분리),
   topology.json 634(승인 기록 -> 분리·보류). 모두 초안 배정과 일치.
5. 문서 커밋의 위치 문장 정정: '역할 밖 경로'가 아니라 역할 커밋이 아닌 오케스트레이터 커밋이 card push 전에 gate에 들어감(선례 6398a28·ab90ec5).
6. 레지스트리 기록 분리가 잊히지 않게 design §8에 P10b 행(`df23-registry-record`, red-green)을 같은 문서 커밋에서 더하는 기본안 추가.
7. 계약 7의 '선례 `20260930-p4-relocate-test-retire`'는 spec card가 아니라 승인 기록 -> 경로와 spec card(`20260929-probe-engine-dup`) 명시.
8. 계약 6 문장: 문서 커밋은 card base에 포함되므로 "070cf69 이후 이 card가 바꾼 경로"와 "test 커밋만 보면 contracts 새 파일뿐"으로 나눔.

## 4. 머리 검증 (tools/gates/role_paths.py parse_spec_card, PYTHONPATH=tools/gates, 읽기 전용)

* P9: id `20260930-p9-kcl-edges`(expect_id 일치), phase `2`, evidence_type `equivalence`, gate_change `no`, approval 2개 -- 통과, 본문 절 11개.
* P10: id `20260930-p10-df23-inventory`, phase `2`, evidence_type `test-only`, gate_change `no`, approval 1개 -- 통과, 본문 절 11개.

## 5. 남은 사용자 결정

없음(두 card 모두 착수 조건 충족). 참고로 사용자에게 알릴 만한 것:
* P9 계약 1을 auditor 측정으로 옮겨 재인라인 회귀의 영구 test 가드가 없다 -- 영구 가드를 원하면 red-green 전환 + design §8 P9 행 재정정(새 승인)이 필요하다. 기본안은 규칙 문장 준수(현 초안).
* 백로그 번호 체계(`BL-` 접두사) 도입은 오케스트레이터 기록 관례 변경 제안일 뿐 승인 사안 아님.
* 새 백로그 등록 필요: topology.json 주석 정리(사용자 보류), Phase 2 전부터 낡은 이름(b22_scan).
