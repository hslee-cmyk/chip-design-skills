# U17 후속 항목 (오케스트레이터 기록, 검증에서 나온 범위 밖 결함)

- [2026-10-13, ①-e 감사 F1, 중] folded_cascode 수렴 루프에서 레이아웃 블록마다 recomputes_same_input 56~57(G-10 판정 1 위반, base 동일 기존 결함). 원인: convergence/place_layout.py:36-63·layout/run.py:93-106 `previous` 체인 하나뿐. 대상: U17 ②(S3 색인·graft) 또는 ③. 근거 `_audit_u17_1e/audit_report.md`.
- [2026-10-13, ①-e 감사 F2, 경미 문서] design 40 :151(§2.3)·:894(§3.9 MOD8 요약) 문구 `LayoutResult{W_requests, revalidation}`·`LayoutResult.diffusion` → ly_* 필드·layout_outputs 로 정정. 다음 design 개정 때.
- [2026-10-13, ①-c 감사, 기존] 탐색 층이 같은 θ를 parent 없는 lineage에서 다시 평가해 dc_currents·dc_lengths·dc_columns 재계산(base 동일) -- U17 ② S3 색인 몫.
- [2026-10-13, ①-c 수정 9065d5f] passive_values 블록이 device.dc_gm 열 전체를 투영해 MOS θ만 바뀐 자식에서도 재계산(영점 상쇄 R 규칙이 있는 회로는 two_stage_ota 하나뿐). θ 전체 extras 원인은 제거됨. 남은 부분은 U17 ② §2.4.4 분할(partition) 투영으로 소자별 부분 읽기 -- ② 작업 목록에 넣을 것.
- [2026-10-13, ①-c 재검증 F1] design §2.4.4 분할 대상에 GB5 passive_values 추가, 읽는 레코드 = 영점 상쇄 셀 소자의 dc_gm 으로 명시(② design 보완 때). F2: #17(theta_passive_pairs) 회귀 test 없음 -- test agent 몫. F3: converge_point 비어 있지 않은 passive_value 경로 단언 test 없음(경미).
- [2026-10-13, ①-a 후속 63bce7e] U-68 정리 프로세스당 1회 표시 _CLEANUP_STARTED(core/snapshot_codec.py) = §2.4.1 (d) S0 스냅샷 영속화 범주의 상태로 판단 -> §2.4.10 허용 모듈 목록에 core/snapshot_codec.py 추가하는 design 정정(③ G-8 lint 때 함께). design §2.4.2 Placement 위치 문장(as-built convergence_values / start 사다리 placement 구분) 정정은 ①-b 때. core.engine_code_fp 함수가 모듈을 가리는 패턴 정리(경미).
- [2026-10-13, ①-d 통합 test 7fdd430] design 정정 대상: §2.4.8 소유표에 dc_colour 새 소유자(graph 대칭 블록 s1_symmetry) 행 추가; §6-8 D-1 예시 toy(U11 pass_device 변형, Mx 포함)는 ds_self_swap 정지가 먼저 걸림 -> 예시를 출력 사이 R1 완전차동 toy로 교체. d/s 뒤집기 비트 동일 결함(writer 계획이 표기 source 의존)은 ①-d 구현 수정으로 보냄.
- [2026-10-13, ①-d 감사 중간1] (라) diode 예외: diode 연결 MOS의 d/s를 뒤집으면 gate=source가 되어 S1 gvgs_self_edge로 정지(9회로 중 7) -- 다른 회로 선언이므로 (라)의 fail-closed 취지와 같으나 거부 주체가 봉인 7이 아님. design 40 §6-8 D-3에 "diode 연결 MOS 뒤집기는 S1 gvgs_self_edge가 거부" 문구 추가(다음 design 정정).
- [2026-10-13, ①-d 감사 중간2] G-10 축소탐색 HEAD≤base 7/9: nmcnr 30→122(θ 기저 변경으로 봉인 통과 평가 0→143, 늘어난 것은 parent 없는 재평가 블록 = ② S3 색인 몫), two_stage_ota 56→59(탐색 궤적 차). ② 이월 범주로 기록.
- [2026-10-13, ①-d 감사 경미] design §6-5 1-WL≠정준형 회로 목록 보고, §6-6 folded·two_stage front 회귀 test(42 D-SYd) 미구현; metrics/CONTRACT.md:1052 dc_orbit 낡은 문구; symmetry_marks S0당 2회 호출(stage_a.py:179, kernel_context.py:83).
- [2026-10-13, ①-a] design §2.4.2 Placement 등록 여부(as-built convergence_values) -- ①-b 때 결정.
- [2026-10-13, ①-a 감사 G1 중] U-68 정리 비용: 재현 불가 후보가 있으면 worktree 113개 전부 engine_code_fp 계산 52 s(부하 212 s), core/snapshot_codec.py:272-279. 기본안 후보: worktree별 (경로, HEAD, 엔진 폴더 clean 여부) 키로 지문 판정 결과를 S0 폴더 안 색인에 보존(§2.4.1 (d) 범주) -- 결정 필요 여부 판단 후 후속 card.
- [2026-10-13, ①-a 감사 경미] tests/pipeline/test_stage_a.py:409-414 _S1_BLOCKS 12 하드코딩(s1_symmetry 누락) -> S1_WRITERS에서 유도; pipeline/CONTRACT.md:7, tests/graph/test_s1_build.py:234,247 "12" 문구; snapshot_codec.py:353 손상 시 재읽기 2회; core/__init__.py:7 engine_code_fp 함수가 모듈을 가림; ①-b 때 S0 키에 sky130_lut_rule_decl.json 해시.


## (2026-10-13) supply_current_dc 합산 레일 선언 통로 없음 -- held-out B 등록에서 발견
- `metrics/dc_metrics.py`의 `supply_current_dc`는 `counted_rails`(DEC-78, 기본값 없음)가 있어야 정의된다. 그런데 spec에 선언할 칸이 없고 search 커널은 `()`를 넘긴다 -> 항상 `counted_rails_undeclared`(미측정). library 9회로는 이 metric을 쓰지 않아 드러나지 않았다. held-out A·B가 처음 쓴다.
- design 40·41에 `counted_rails` 선언 위치 문장 없음(grep 0). 분류: design 빈칸 -> ② 결정 자료 후보. A는 원문이 '증폭기 전류만'이라 레일 합산으로 바이어스 회로를 뺄 수 없는 문제도 겹친다.

- (2026-10-14, 사용자 승인 8) BLAS 스레드 결정론 결함(NFR-4): OPENBLAS_NUM_THREADS 미지정 시 two_stage_ota·two_stage_ota_sf·sf_pushpull 의 start.row·rungs·macro·area_est_m2 fp가 base와 비트 단위로 다름, 1 고정 시 일치. 1-b에서는 test 환경 고정만, 엔진 원인 연산 수정은 2 착수 전.


## 2026-10-14 후속 (U17 ①-b 4차·code_hash 판정 비차단)
- design 40: "N-1 반영 예정" 3곳을 "구현 7eb4865"로; 229행 (2) import 시점 RuntimeError, (3) 상수 전 타입 (타입 이름, 값) as-built 반영; 1679행 결정 10 card 상태 "완료(eadb729 위 codehash-integ 병합)".
- graph CONTRACT 10.5·10.6 옛 S1v.key·S1v.views·S1v.facts_applied 표기.
- stage_a.py 모듈 docstring에 진입 거부(SchemaRejectedError) 추가.
- test: N-1 test reason 단언, keeps_other_circuit_snapshots 주석 정정·git worktree 목록 고정(U-68 정리가 다른 worktree 재현 시 보존하므로 메인 저장소에서는 보존 단언이 회귀를 못 잡음).
- compute_block.py 41행 공백, 모듈 전역 _unknown_code_fields 잔존(스타일).
- 관찰: 단계 A s1.snapshot.fp 가 miss 실행과 hit 실행에서 다름(hit끼리 9/9 같음) -- 원인 조사 필요.
- 보류: assets/sky130_pdk_decl.json:89 설명 문자열의 "res_high_po 모델 없음" 옛 사실. decl_sha256 이 파일 전체 바이트라 바꾸면 S0 키 전부 miss + tests/integration/fixtures/u17_1b_s0_baseline.json pdk_decl_sha256 8곳 재측정(test 역할) 필요 -- 기준선 재측정이 필요한 다음 card(library spec 반영 등)와 묶는다. graph/view_analysis.py docstring "극성 판정은 build_s1v" 옛 표기(code card).

- 해소(2026-10-14, NFR-4 측정 3 §7): s1.snapshot.fp hit/miss 차이는 값 결함 아님 -- hit 실행은 디스크의 S0 전체를 읽어 와서 지문 대상이 다르고, hit 쪽 값이 miss 의 탐색 기준 스냅샷 지문과 일치. 하류(context_fp·층0·외층·평가·front) 전부 같음. 남은 일: 같은 이름 지문이 실행 경로마다 다른 대상을 가리키는 것이 문서화돼 있는지만 확인.

- NFR4-F1 (2026-10-15, 사용자 Q-N7 기본안): pushpull_follower_buffer 외층 EP:s1 L:M1 FD 열 실패·재시작(2 대 6) 경로 원인 조사·수정안 제시. 2안(SQP 교체) 재개 안 함. 정의: design 40 §2.4.13 (8)(nfr4-design 482025d), 결함 D-ND4. 근거: 출발점 상대 1.5e-8 차이로 스레드 1끼리 판단 123건 차이(wt/_nfr4_design_scratch).

- XRUN-F1 (2026-10-15, 사용자 J-2 권고): search_context._wire_sweep_memo 가 LUT memo 상한을 정하려고 첫 평가를 임시 컨텍스트에서 계산하고 버린 뒤 층 0이 같은 점을 다시 평가 -- 실행 안 같은 입력 중복 계산(원래 취지와 다를 수 있음), 임시 계수라 G-10 에 안 잡힘. 측정부터.


## 2026-10-15 백로그: 단계 B 헤드룸 창 엣지 비용 |VGS| 최솟값 0
- TD-3 조사(wt/_drafts/engine/td3_probe/)에서 단일 출력 6회로 모두 단계 B 헤드룸 창이 레일 거의 끝까지 열림 -- 엣지 비용 |VGS| 최솟값이 0으로 나옴. design 41 §4.6 창 추정과 크게 다름. 결함인지 정의대로인지 미판정 -- 측정·원인 card 필요.


## 2026-10-16 추가 백로그
- [조사 card 후보] current_reuse_telescopic_ota: master 기준 층 0 40점 전부 SEAL_VIOLATION, front 0, 정지 start_no_root_in_window+probe_eval_budget (card A 판정 측정 base·head 동일, M2 _scratch_m2/results/followup.md). gm/ID 엔진이 이 회로를 못 푸는 원인 조사 -- 사용자 F-1 (a) 결정으로 별도 card.
- [백로그] context_fp가 DcInputs.pending(결정 대기 표지 (경로, 결정 ID))을 담고 경로에 제약 목록 배열 색인이 들어감(dc_inputs.py:39, spec_schema.py:50) -- 의미 무관 순서 변화로 키 무효화. 정확성 문제 아님.
- [design 개선 후보] _wire_sweep_memo가 n_θ 하나를 위해 centre_start 전체 호출, 층 0이 다시 호출(XRUN-F1 card A gap 분석 D-4).
- [card C] two_stage_ota_sf kernel_calls 43 > E_B 40 (FD 묶음 예산 밖).


## 2026-10-16 current_reuse 층 0 조사 요약 (읽기 전용 조사, 원자료 _scratch_m2)
- 40점 모두 봉인 7 no_root_in_window(1변수 노드 풀이 solve_self): Vy/M4a 33점(창 빔, hi = V(N3a4a) − 0.0375 = −0.0375 → V(N3a4a)=0), Vg25/M18a 4, Ncmfb_tail/M37b 2, Vom1/M18b 1 -- 모두 source 추종 writer.
- 가설 H-A: SCC {Vy, Vbias3, N64_63, N3a4a}에서 GS 비엄격 투영이 N3a4a를 0 V 창 끝에 고정(block_columns.py:397-399) 뒤 _strict_recheck가 Vy를 보고. H-B: V(N3a4a)−V(Vy) = VGS(M63)−VGS(M3a) ≥ 0.0375 필요, 40점 모두 ln_idu(M63) < ln_idu(M3a). 출발 구간 규칙이 gate 공유·diode 적층/추종 쌍의 KVL 결합을 묶지 않음(start_intervals.py:22-23, 276), 보정은 빈 창 대상 아님(layer0_center.py:445-457), Halton 27점이 상자 하단 직선(스크램블 없음). search/CONTRACT.md:834-860 [r5c] '적층 diode ln_idu 상한 규칙 미정의'와 같은 결.
- 확인 측정 M-1~M-5(무거운 측정 뒤). 사용자 공동분석 질문: M63·M64 복제 바이어스 의도, M20a/b→M18a·M23a/M24b→M18b class-AB 관계, M39·M40·M37b 역할, SP-2·CI-15 미선언 의도.
- [백로그 2026-10-16 O-6 D-c] 차동 이득 실수 판정 상수 1e-3 유도식: ac 파일 data_rel만으로는 기준선 174개 중 170개 판정이 뒤집힘(_scratch_op1/results/m7_gain_imag.json). 첫 점 주파수와 극점 위상을 고려한 식으로 유도 후 교체.
- [백로그 2026-10-16 O-10 KCL] 종속(차) 전류에 W_min·밀도 하한 l_m과 면적 상한 u_m 구간 결합, L 칸마다 상자∩원뿔 LP 공집합 판정(Hoffman 컷 충돌 기록) -- 실패 사례 0이라 백로그, 근거 wt/_scratch_kcl/. 별도: DC 저항이 θ 전류 기저일 때 ln 좌표라 t0→t1 양수만 표현(r2r RL, rfc RB, nmcnr RL, cnr x37/x40/x9, sf_pushpull R1a~c, current_reuse R1) -- agnd 부하의 반대 방향 전류 표현 불가 여부 공동분석 필요.
- [백로그 2026-10-16 X-22] structure_rule_fp/s1v_rule_fp가 S1V_RULE_FILES 파일 바이트 전체를 해시해 서명·주석 변경에도 ratified structure.json 사실이 stale이 됨(card B s1v_build.py 서명 변경 실례) -- 판정 로직에만 묶도록(core _code_hash AST 정규화 재사용 등) 개선 후보, 계획 필요.
