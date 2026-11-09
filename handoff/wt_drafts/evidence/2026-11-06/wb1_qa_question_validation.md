verdict: Major 0
gate_sha256: 6a1d646090a37273ebd26b2c6f050cfa6be22fc8169dc356d12718d5bdd8f185

# WB-1 QA1 질문 문서·점검 파일 독립 검증 (2026-11-06)

검증자 = 질문 게이트 독립 검증 agent(질문 문서·점검 파일·권고안·점검 기록의 작성자 아님).
대상: 질문 문서 `wt/_drafts/evidence/2026-11-06/wb1_qa_question.md`(sha256 3a1a24e3…a804, 실측 일치), 점검 파일 `wt/_drafts/ask_gates/2026-11-06_WB1QA.md`(sha256 6a1d6460…f185, 실측 일치).
원 파일 = WB-1 worktree `wt/20261105-wb1-c`(머리 3397b834, 읽기만). 엔진 인용은 원칙 8에 따라 외부 사실(LUT 값)과 재작성 범위(고칠 자리·소비자)로만 쓴다.
실행: grep·sed와 짧은 스크립트 1개(`C:/Users/HSLEE/AppData/Local/Temp/la1s_wb1_val16/check_gate.py`, ask_gate 훅의 `evaluate`를 읽기 전용으로 부름 → `gate_check.txt`). ngspice·pytest·커밋 0. 대상 두 파일 수정 0.

## 결론

Major 0, minor 9. 권고 A는 사실(줄 번호·값)과 맞고, 결정 간 모순과 물리·graph 위반이 남지 않는다. 형식은 훅 기준을 통과한다(검증 파일이 없다는 오류 1건만 남았고, 이 파일로 해소된다). minor는 질문을 내기 전에 문언으로 고치는 것을 권하지만, 게이트를 막지 않고 권고를 바꾸지도 않는다.

## 1. 사실 대조 (질문 문서 §1·§2·§3)

| # | 문서 주장 | 원 파일·측정 | 판정 |
|---|---|---|---|
| F1 | P:682 셀 = (kind, w_key, L 점, VDS), 앵커 2개 bin은 중점 L 방향 값과 최댓값 | 계획 P:682(WB-1 worktree와 master 같은 문언), design 40:1453 같은 정의 | 맞음 |
| F2 | 중점 표는 kind마다 기준 폭 하나, 다른 폭은 `midpoint_checks.py:72` `width_differs` | `lut/midpoint_checks.py:71-73`. 중점 파일 하나에 `w_ref_m` 하나: `lut/lut_set.py:347-350`. 분석 `wb1_resolution_slice_analysis.md:35`(w_key 1000) | 맞음 |
| F3 | `with_external(value, None)`이 L 항 없이 값을 냄(`_helpers_loo.py:131-135`) | `lut/_helpers_loo.py:131-135`(`ext is None`이면 value 그대로) | 맞음 |
| F4 | WB-1 소자별 슬라이스(`seal_tolerances.py:31`), master는 기준 폭 | WB-1 `sizing/seal_tolerances.py:32`(`op.w_key` 슬라이스 셀, :31은 try 줄). master `sizing/_helpers_lut.py:52` `w_key_of` | 맞음(줄 ±1) |
| F5 | `dc_tol_v` M6 4.49e-3 → 4.25e-6 V(1/1056) | `C:/Users/HSLEE/AppData/Local/Temp/la1s_wb1_ana11/out_master.txt:8` 4.4853e-3, `out_wb1c.txt:8` 4.2477e-6, 비 1055.9 | 값 맞음. **출처 표기 틀림**(m1) |
| F6 | `power_resolution_w` 7.13e-6 → 6.69e-9 W | `la1s_wb1_diag9/dump_132501bd.txt:45` 7.1312e-6(M6 w_key 1000), `dump_7c038c89.txt:45` 6.6908e-9(M6 w_key 110) | 맞음 |
| F7 | gbw 행 c +0.0555 → −330 | `la1s_wb1_ana11/out_master.txt:93` 0.05545, `out_wb1c.txt:207` −330.196 | 맞음 |
| F8 | WB-1 two_stage_ota 실경로 test 4건 red, master 7 passed | `C:/Users/HSLEE/AppData/Local/Temp/la1s_wb1_test6/out_orig.txt` 끝 "4 failed, 15 passed"(converge.py:57 ValueError), scratchpad `master_conv.txt` "7 passed, 48 deselected" | 값은 있음. '같은 test'는 확인하지 못함(m2) |
| F9 | ngspice 중점 nmos 0.42 µm 1.513e-2 대 1.596e-2(0.95~1.44배), pmos 0.55 µm 8.61e-3 대 8.43e-3(0.98~1.09배) | `la1s_wb1_rec13/out/qa_ngspice_mid.txt`(MIDERR·CHECK_REF), `qa_ratio.txt` RATIO_MID min 0.948 max 1.437 / 0.975~1.092 | 맞음 |
| F10 | LOO 폭별 비 0.58~2.25 | `qa_ratio.txt` RATIO_LOO 0.575(nmos 키 104)~2.251(pmos 키 128) | 맞음 |
| F11 | `missing_external` 상태는 `_helpers_loo.py:82`가 냄 | `lut/_helpers_loo.py:81-82`(앵커 2개 bin, 외부 값 없음), 앵커별 `bin_missing_external` :88-90 | 맞음 |
| F12 | computed·single_point bin은 지금처럼 값을 냄 → 기준 폭 경로 거짓 거부 없음 | `_helpers_loo.py:74-77`. 이 두 상태의 행은 `ext_rows`에 없어서 `with_external(v, None)` = v(`lut/tolerance.py:154-158`, `lut/vdsat_tolerance.py:116-120`). 기준 폭 키 1000은 앵커 2개 bin이 모두 `external`(`wb1_resolve_check.md:10`, `qa_lbin_loo.txt` MIDSKIP 비어 있음) | 맞음 |
| F13 | `vdsat_tolerance`도 같은 꼴 | `lut/vdsat_tolerance.py:117` | 맞음. 다만 tol_VDsat는 판정에 쓰지 않는다(m5) |
| F14 | 판정 자리 둘이 실재: 봉인 10행 `seal_undefined`, `block_dc` `tol_v_undefined` | `search/search_values.py:14` `STATUS_UNDEFINED = "seal_undefined"`, `sizing/seal.py:13-15`(undefined → `DcEvaluation(sealed=None)`), `sizing/block_dc.py:497-509`(SCC 셀이 **모두** None이면 `SealViolationError` `tol_v_undefined`), `sizing/s2_values.py:101` | 실재함. 갈래가 더 있음(m4) |
| F15 | 비용: 조합당 0.4~0.5 s, 120조합 ≈ 1분, 기준 생성기 ≈ 90분 | `qa_ngspice_mid.txt` sec 0.5·0.4. 120 = 30 × 4, 90분 = 옛 6분/8조합을 환산한 추정(`wb1_qa_qb_recommendation.md:279-281`) | 대체로 맞음(m6) |
| F16 | B 과소 최대 1.44배(ngspice)·2.25배(LOO) | F9·F10 | 맞음 |
| F17 | C: 층 0 55/60 소자·6/6 회로, 손 봉인 점 7/7 E-0 실패 | `wb1_qa_qb_recommendation.md:74`(보간점만 셈) | 맞음(A 꼴이면 앵커 L 소자도 None이 되므로 하한값이다) |
| F18 | W_min 지문(`lut/fingerprint.py:18-36`)에 `min_finger_w_m` 없음 | `lut/fingerprint.py:18-36`: manifest·생성기·슬라이스·cap·cap_basis·bin_rule + 중점·잡음·mismatch sha뿐, `LutSpec` 없음. W_min 소비자 `lut/widths.py:15`, `lut/finger_slice.py:42` | 맞음 |
| F19 | A-63 Q-DC3 원 근거 (가) '슬라이스별 중점 생성 비용·LUT 적재 순수성', (나) '판정 불변' | D41:1751: (가) = **슬라이스별 tol 표 첫 구성 비용**(7~10분 CPU) + 구성 시점 LUT 적재(순수성). 중점 생성은 **기각된 대안**('비기준 슬라이스 중점 LUT 생성(oracle·LUT card 추가)'). spec :276 "Q-DC3 구성 비용 받아들임" | (나)는 맞음. (가) 서술이 틀림(m3) |
| F20 | 고칠 자리 인용 spec :39·:73·:253·:276, interface :311 | 각 줄이 A-63 Q-DC3·'중점 미검증' 표지 문언이다(직접 sed) | 맞음 |

## 2. 재점검 v2 고칠 방법 셋의 반영과 새 모순

| 재점검 v2 고칠 방법 | 질문 문서 반영 | 판정 |
|---|---|---|
| R2-1 ①: `with_external` 유지, `missing_external` 앵커 행만 None, toy LUT 영향은 card에 | §2 23행에 그대로 있음 | 옳게 반영됨 |
| R2-1 ②: design에 두 갈래 + **P:663 '하나'가 봉인 항목 범위라는 한 줄** | 두 갈래는 적혀 있음. P:663 한 줄과 계획 개정 항목은 빠짐(점검 파일 bkit 단계표 계획 칸도 'P:682 문언 유지 + card 추가'뿐) | 일부만 반영(m7) |
| R2-1 ④: V2-1.2를 Q-T0 조건부로 표지 | §2 27행 | 옳게 반영됨 |
| R2-3: 지문 근거 정정 + 키 확인을 완료 조건으로 | §3 31행(근거 정정, LM-1e 완료 조건) | 반영됨. 담을 card가 맞는지는 m8 |
| R2-2 (b): QB 재측정·질문을 WB-1 병합 전에 | §3 32행 | 옳게 반영됨 |

반영분과 결정 사이의 모순 직접 대조:

| 결정·규칙 | 반영분과의 관계 | 근거 |
|---|---|---|
| O-200(물리 먼저, 물리 경계를 분해능으로 정하지 않음) | 정합. 정의 항이 없는 셀을 값으로 내지 않고 정의 불능으로 둔다 | `user_decisions.md` O-200, P:682 |
| O-173 E-0 fail-closed | 정합. None 셀은 모두 결국 fail-closed로 끝난다. 봉인 2는 소자마다 `tol_v[m]` 행을 두어(`sizing/seal_vgs_match.py:22-26`) None이면 undefined로 간다(`sizing/_helpers_seal.py:20-22`). 그래서 SCC나 봉인 3·4에서 '정의된 값 중 min/max'로 넘어가도 그 점은 `seal_undefined`로 끝난다 | 같은 파일 |
| O-210 RR-7 / P:663 | 정합. 봉인 항목은 10행 그대로이고 새 사유 이름이 0이다. 봉인 6 띠는 '띠 미정' 기록(RR-7 원문)이다. '하나' 문언은 m7 | `user_decisions.md:1191`, P:663 |
| O-240(tol_V의 남은 자리) | 정합. 순환 수렴이 `tol_v_undefined`를 쓰는 것은 남은 자리 안이다 | `user_decisions.md:1221` |
| O-229 1·2·4 / O-232 | 정합. LM-1e는 엔진 card이고 ngspice가 0이다. LM-1d ngspice는 허용 목록 밖이라 이 질문으로 묻는다. 새 도구 0 | `user_decisions.md:1213`, CLAUDE.md O-229 |
| O-238(원 결정 변경은 근거를 대조한 뒤 질문) | 정합. 질문으로 올린다. 원 근거 (가) 서술은 m3 | `user_decisions.md:1219` |
| A-63 | 정합. Q-DC3 (나) 철회를 묻는다. 원 결정에서 기각된 대안을 되살리는 것이라 m3에 표지가 필요하다 | `la1_auto_decisions.md:69`, D41:1751 |
| A-110 | 정합. O-238로 효력이 없고 무효 표지만 남는다 | `user_decisions.md:1219`, `la1_auto_decisions.md:135`(A-129) |
| P:682 | 정합. 문언 변경 0, 셀 정의 그대로 | P:682 |
| Q-T0(P:1224) | 모순 없음. 'Q-T0 전까지 현행 셀 유지'와 맞는다. 다만 상호작용이 하나 더 있다(m9) | P:1224 |

새 결정 모순: 0.

## 3. 점검 파일 형식 (원칙 26)

- 훅 `evaluate` 실측(`la1s_wb1_val16/gate_check.txt`): 절 4개(bkit 단계표·단계별 점검표·원래 취지와 다름·권고 실측 출처)와 '## 권고 확인표: QA1'이 있다. ①~⑩ 근거 칸 접두는 '실측('·'해당 없음('이고, ⑩은 실측 + 점검 기록 경로다. 금지어 0. 인용 경로가 모두 있다. 오류는 'validation 파일이 없음' 1건뿐이고 이 파일로 해소된다.
- frontmatter: kind recommend, headers QA1, candidate_sha256이 현재 질문 문서와 같다(실측).
- 전체 grep: 금지어 5개('안 함'·'미측정'·'상정 전'·'확인 필요'·'TODO')가 두 파일 어디에도 없다.
- 인용 경로 실재: `dump_7c038c89.txt`, `dump_132501bd.txt`, scratchpad `master_conv.txt`, `qa_ngspice_mid.txt`, `qa_lbin_loo.txt`, evidence 3파일 모두 있다.
- 5묶음 내용 칸은 지켜졌다. ① 근거 칸의 dump 경로는 dc_tol_v 값을 담고 있지 않다(m1과 같은 원인, 형식 문제는 아님).

## 4. 권고 A의 물리·graph 점검

- 물리(원칙 1·2·10): A는 P:682 정의를 그대로 채운다. 실측으로 L 보간 오차가 폭과 무관하게 mV 자릿수다(F9·F10). 중점이 없는 칸은 fail-closed다(§2 O-173 행). 위반 0.
- graph(규칙 1~6): tol 셀 writer는 `DC_TOLERANCES_WRITER` 하나다(`sizing/seal_tolerances.py:25`). tol 표는 기존 memo derived 영역이다(`lut/tolerance.py:164`). 중점 데이터는 LUT 입력이고, 위치 선언 하나(O-180)와 지문 `midpoints_sha256`(`lut/fingerprint.py:31-32`)에 들어간다. 새 cache·사본·슬롯 0. 위반 0.
- 만들면 배선: LM-1d 데이터는 기존 소비자(`midpoint_l_bin_checks` → `tol_v_table`·`tol_vdsat_table`)가 읽는다. 위반 0.

## Major

없음.

## minor (질문을 내기 전에 문언으로 고치기를 권함, 게이트는 막지 않음)

- **m1 (출처)**: §1 10행과 점검 파일 ①은 `dc_tol_v` M6 값의 출처를 덤프 `dump_7c038c89.txt`라고 적었다. 그 덤프에는 dc_tol_v가 없고 `power_resolution_w`와 OP만 있다. 값은 `C:/Users/HSLEE/AppData/Local/Temp/la1s_wb1_ana11/out_master.txt:8`·`out_wb1c.txt:8`(분석 agent 측정)에 있고 맞다. 출처를 바꾸거나 'agent 측정 인용'으로 표지할 것.
- **m2 (확인 범위)**: 'two_stage_ota 실경로 test 4건 red; master 같은 test 7 passed'에서 WB-1 쪽은 `la1s_wb1_test6/out_orig.txt`(test 19개 중 4 failed)이다. master 쪽 `master_conv.txt`는 128바이트로 명령줄이 없다. 그래서 '같은 test'인지 확인하지 못했다. 권고 근거는 gbw 행 c(F7)로 따로 서므로 결론은 바뀌지 않는다. 명령줄을 붙이거나 '같은'을 빼기를 권한다.
- **m3 (원 결정 근거 서술)**: §1 11행의 (가)는 '슬라이스별 중점 생성 비용'이 아니다. D41:1751의 (가)는 '슬라이스별 tol 표 첫 구성 비용(7~10분) + LUT 적재 시점 순수성'이다(spec :276 '구성 비용 받아들임'). 비기준 슬라이스 중점 생성은 Q-DC3가 **기각한 대안**이다(기각 사유 'oracle·LUT card 추가'). 지금 문언대로면 "(가) 중점 생성 비용이 유지된다"와 "A = 중점 생성"이 서로 어긋나 읽힌다. O-238의 '원 결정 근거 대조'를 정확히 하려면 이렇게 고친다: "(가) tol 표 구성 비용·순수성 -- 유지. A는 Q-DC3가 기각한 대안(중점 생성)을 되살리며, 기각 사유(card 추가)는 LM-1d·LM-1e 두 card의 비용으로 받아들인다."
- **m4 (판정 자리 서술의 정밀도)**: 'None 셀은 기존 판정 자리 둘로 간다'는 결과로는 맞다(모두 fail-closed). 그러나 갈래가 더 있다.
  - SCC는 셀이 **모두** None일 때만 `tol_v_undefined`이고, 일부만 None이면 정의된 값의 min을 쓴다(`block_dc.py:505-509`).
  - 봉인 3·4는 노드마다 정의된 값의 max를 쓴다(`seal_kcl.py:58-59`, `seal_node_conflict.py:31`).
  - 이런 점은 결국 봉인 2 소자 행(`seal_vgs_match.py:26`)의 None으로 `seal_undefined`가 된다.
  - 이 밖의 tol_v_table 소비자: `layout/slice_density.py:29-35`(None → 그 폭 후보 제외, 사유 `tol_v_undefined`), `lut/derived_fns.py:57-67`(edge_costs, None 행 제외), `lut/slice_tables.py:21-24`(U-87 디스크 표 캐시).

  LM-1e design에서 갈래를 적을 때와 '고칠 자리' 목록에 이 셋을 넣을 것. 그러면 toy LUT의 edge_costs·layout 영향이 card 범위에 들어간다.
- **m5 (vdsat)**: tol_VDsat는 '구별 불가' 띠 기록 전용이다(P:682, `lut/sat_threshold.py:4`). 그래서 `vdsat_tolerance`의 None은 판정 자리가 아니라 기록 미정으로 간다. §2의 '판정 자리 둘'에 vdsat이 포함되지 않음을 한 줄로 밝힐 것.
- **m6 (비용 수치)**: 순서상 W_min 정정(3397b834)이 LM-1d보다 먼저다. 권고 v2 기준으로 조합 수는 112다(`wb1_qa_qb_recommendation.md:279`). '기준 생성기 ≈ 90분'은 옛 6분 기록을 환산한 추정이다(권고 v2 V2-6에서 불확실로 표지). '120(W_min 뒤 112)', '≈ 90분(환산 추정)'으로 적기를 권한다. 선택지 순위는 바뀌지 않는다.
- **m7 (R2-1 ② 일부 반영)**: 재점검 v2가 요구한 'P:663 문언의 "하나"가 봉인 항목 범위라는 한 줄'이 §2와 점검 파일 bkit 단계표(계획 칸)에 없다. 결정 모순은 아니다(P:663은 '봉인 항목이 쓰는 셀'을 범위로 한다). 다만 고칠 방법을 하나 빠뜨렸으므로 §2 끝과 계획 개정 항목에 넣을 것.
- **m8 (W_min 완료 조건이 들어갈 card)**: W_min 캐시 키 확인을 LM-1e(중점 적재 card)의 완료 조건에 두었다. 이 위험은 A-129(이미 커밋)와 WB-1 병합에 걸린 것이고 중점과는 관계가 없다. WB-1 병합 전 판정 항목에 두는 것이 범위상 맞다. 덧붙여 실측: W_min 소비자 `lut/widths.py:15`·`lut/finger_slice.py:42`는 `lut.spec`에서 바로 읽는다. tol 표 memo 키(`lut/tolerance.py:164` (kind, w_key, checks))는 W_min과 관계가 없다. 그래서 위험은 `widths` 집합에 기대는 파생값에 한정된다.
- **m9 (Q-T0 상호작용 하나 더)**: A 꼴은 `missing_external` bin의 **앵커 행 전체**를 None으로 만든다. 그래서 L이 앵커와 정확히 같은 조회도 None이 된다. 이것은 Q-T0(P:1224)의 후보 '앵커 조회 L 성분 0'이 채택되면 다시 볼 자리다. 지금은 'Q-T0 전까지 현행 셀 유지'와 맞으므로 모순은 아니다. LM-1d 뒤에는 발동이 0이다. §2 조건부 표지에 이 한 줄을 덧붙이기를 권한다.

## 돌린 범위

grep·sed로 원 파일을 읽었고, 훅 `evaluate`를 1회 불렀다. ngspice·pytest는 돌리지 않았다. 재지 않은 것은 이 범위 밖으로 남긴다(통과로 세지 않음): m2의 master 명령줄, m4 갈래들의 toy LUT 실측 영향.
