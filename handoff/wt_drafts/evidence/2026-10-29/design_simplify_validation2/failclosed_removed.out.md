- 028bea62 41-gain-budget old:704 … '식), `input_status` = 되풀이가 tol 안에서 수렴했으면 `"measured"`, A6 b·c 경로면 `"unsettled"`. **A6 c(`k_max` 소진 뒤 마지막 창 사용)와 fail-closed**: 그 창은 실제 해에서 잰 값이지만 자기를 y 범위로 둔 해와 tol 안에서 맞지 않아, 그 창을 metric 값으로 내면 수렴하지 않은 값을 수렴한 값처럼 쓰는 조용한 대체다. 그래서 y 범위로는 그대로 쓰되'

- 028bea62 41-gain-budget old:728 … "edance`로 분류된 출력의 writer 사슬 뿌리가 출력이 아닌 W3 목표 노드인 경우(아래 OS (f) 꼴) θ 고정 연립에서 어느 고정을 풀어 'V_out = x' 행을 세우는지(그 W3 목표값을 x 미지수로 바꾸는지 등)는 계획 N3.8이 적지 않았다(계획은 '출력이 W3 목표 노드이면'만 적음). 구현 agent는 이 갈래의 창 계산(일반형)을 만들지 않는다. **실행 중 만나면 fail-closed**(v1.12.3 MF-2·gap N1 -- 계획 N3.14 공통 실패 규약의 적용, 계획 개정 불요): `icm_config`가 `config` = None, `IcmConfig.undefined`에 `defin"

- 028bea62 41-gain-budget old:728 … "S2**(v1.12.3 MF-4; v1.12.4 -- 일반형은 계획 v6.24 N3.8 '차동 출력 회로의 측정 구성'(576행, 사용자 결정 O-68 (2): 차동 모드만 닫음 (in+ − in−) = −(Vop − Von), 입력 공통모드 = x, `kvl_sensitivity`에 닫힘 행 둘, margin 대상 = 입력 포트 둘)이 정했고 **후속 card 몫**이다 -- IT-2c는 fail-closed로 시작한다(사용자 결정 O-67 (5)); 이 판은 일반형을 설계하지 않는다): 되먹임 구성이 선언된 차동 출력. 구현 agent는 IT-2에서 이 갈래의 창 계산을 만들지 않고, 실행 중 만나면 `icm_conf"

- 028bea62 41-gain-budget old:728 … 're`**(detail `(("outputs", 출력 넷 tuple),)`)를 `IcmConfig.undefined`에 쓴다(M7 경로, 선언 제약은 unmeasured 경로). card 0이 발동 수를 잰다(4.7-8a). 선언 없는 차동 출력의 `icm_config_differential_output_undeclared`도 O-68 (2) 일반형이 대체할 규칙이지만 IT-2에서는 그대로 fail-closed다(같은 후속 card). IT-2 병합 전 검증자가 이 차동 처리가 13회로 표 Q1(CMFB 감지 차동 출력 4개 KVL 고정, \'추정\', 정확값 oracle `.dc`)과 N3.8 \'차동 출력 회로의 측정 구성'

- 7e57ee63 40-engine old:12 … '획 v6.38 기준, 미검증)을 v6.38.1·v6.38.2와 다시 맞추고(재점검 94건), 계획 넘김 목록(LA-1 후속 정정 표 v6.38.2 행)과 DEC-105 (1)~(12)를 반영했다: DC 블록 재작성 design(40 §3.7-A -- card WB-1, O-165 (a) 비교표·design 입력 측정 표·승인 질문 Q-DC1~Q-DC4), 이득 L 하한 found_db 목표·fail-closed(41 §6.4-1), 매크로 P = 0(41 §6.5-3a), `mirror_vds`(41 §6.7-4·-11), 가드 합 행(41 §6.4-2a), 면적 → gm/ID 하한(41 §6.4-2), CM DC 평형('

- 7e57ee63 40-engine old:12 … '해능 정의 함수 `_transfer_resolution`, 41 §4.7-3b), S-OS2 일반형은 후속 card). 아래는 v1.12.3 머리(대체됨): v1.12.3 검증·gap 반영판(41 v1.12.3과 같은 변경 -- 이 문서는 §2.4.8 `node.dc_output_structure` 행에 권한표·소유표 등록(MF-3), `icm_config` 행에 멈춤 S-OS1·S-OS2 fail-closed code(MF-2·MF-4)). 아래는 v1.12.2 머리(대체됨): v1.12.2 맞춤판(41 v1.12.2와 같은 변경, 사용자 결정 O-63 (4)·O-64 (1)(2) -- 이 문서는 §2.4.8 표: 새 '

- 7e57ee63 40-engine old:14 … '), §2.4.14 신설(출처별 처리, ln 좌표 원값 보존 정본 `ThetaCoords`, 재작성 범위, 삭제·변경 목록, card A·B), §2.2·§2.3·§2.4.1·§2.4.10·§7.3·§11 U17 ②·③. 옛 문장·측정은 history. 같은 v1.11에 design 독립 검증(81, 조건부) 반영: 이식 전제를 모든 블록의 의무로(`*` 블록도 이식 대상, 섞인 성공·예외 fail-closed), §2.4.6 계수 창·`LutMemo.counting`·`open_count`·`fix_bound`·n_θ 출처·옮기는 순서·커널 평가 없는 실행·독립 계수 test, card A 판정을 단위 test 기준으로'

- 7e57ee63 40-engine old:14 … 'e_input_failed`(Q13 결정 전 규칙), 레지스트리·`centre_start` docstring 갱신 목록, 줄 번호 f23aec8 기준. 같은 v1.11에 card C 결정 X-15·X-16(사용자 결정 2026-10-15 "1, 2번 둘 다 권고대로 해") 반영: 모든 실행에서 커널 평가 수 ≤ E_total(E_B 유도 실행 포함 -- 유도값은 실행 전체 평가 수, 넘치면 fail-closed), 감도 게이트 예약 R = 2 × 정의역 변수 수를 탐색 예산에서 먼저 떼어 게이트는 항상 돈다, `fd_jacobian` 예산 부족 = 예외 `FdBudgetShortfall`(N-3 오케스트레이터 기본안), '

- 7e57ee63 40-engine old:14 … ', `fd_jacobian` 예산 부족 = 예외 `FdBudgetShortfall`(N-3 오케스트레이터 기본안), 탐색 예산 계산 자리 `search_ceiling`. 같은 v1.11에 card C 검증(84) 반영과 사용자 결정 X-17(2026-10-15 "나로 해"): 선언 E_B = 탐색 예산, E_total = E_B + N_T + R(§2.4.9 정의 갱신), 선언 실행은 예산 fail-closed 없음(선언 40 그대로), 유도 실행은 E_total = D·탐색 예산 = D − N_T − R이고 남는 탐색 예산이 없을 때만 fail-closed(`ValueError`, N-4 오케스트레이터 기본안). 같은 '

- 7e57ee63 40-engine old:14 … '_ceiling`. 같은 v1.11에 card C 검증(84) 반영과 사용자 결정 X-17(2026-10-15 "나로 해"): 선언 E_B = 탐색 예산, E_total = E_B + N_T + R(§2.4.9 정의 갱신), 선언 실행은 예산 fail-closed 없음(선언 40 그대로), 유도 실행은 E_total = D·탐색 예산 = D − N_T − R이고 남는 탐색 예산이 없을 때만 fail-closed(`ValueError`, N-4 오케스트레이터 기본안). 같은 v1.11에 재검증(88) B-4(Q13 결정 전 규칙 엄격안)와 사용자 결정 X-6~X-13(사용자 결정 2026-10-15 "3번 나, 4번 가, '

- 7e57ee63 40-engine old:14 … '(사용자 결정 2026-10-15 "3번 나, 4번 가, 나머지는 8번까지는 권고대로. 9번은 좀더 설명해줘", 원문 `_drafts/user_decisions.md` \'XRUN-F1 design 결정 1~8\') 반영: 감도 게이트 RT 대체 확정(X-6), `donors` 필수 확정(X-7), Q12 닫힘 = 모든 커널 평가를 E_total에 넣고 묶음은 시작 전 확인·색인 상한 등록 때 fail-closed(X-8, 새 card C), Q13 닫힘 = 결정적 도메인 실패를 색인에 등록해 재연(X-9, `recomputes_same_input_failed` 대신 `replays`), evals `snapshot_fp`('

- 7e57ee63 40-engine old:14 … ", 원문 `_drafts/user_decisions.md` '결정 10' 두 항목): §2.4.3 '블록 코드 해시' 행 신설 -- `ComputeBlock.code_hash` = 블록 함수 code 객체(중첩 code 재귀, `__wrapped__` 사슬 포함)의 코드 내용 지문(파일 경로·줄 번호 제외, marshal 미사용, core `fp_of`, 상수 타입 명시 인코딩·미지원 타입 fail-closed `TypeError`), §2.4.3 'checkout 무관' 행의 미결 문구 삭제, §2.4.3 키 (iii) 문장, §2.4.9 판정 2 다른 checkout 단서를 결정 결과로, §11 U17 ② 선행에 결정"

- 7e57ee63 40-engine old:14 … 'decl=` "그대로 둠"): §2.4.3 \'무효화\' 행 -- PDK 선언·LUT 생성 규칙 선언이 U-68 정리 대상 입력 파일, `run_stage_a` 키워드 전용 필수 인자 `pdk_decl_path`·`lut_rule_decl_path`(경로는 키 메타 위치에만, S0 값·스냅샷 `fp`·`context_fp` 밖), 진입에서 경로 파일 sha ≠ `decl_sha256`이면 거부(fail-closed, 구현 7eb4865). 같은 v1.9.3에 as-built 문서 정정(판정 u17-1b-r4 988eef4·codehash ecda471의 경미 지적, 버전 번호 불변): \'블록 코드 해시\' 행 (2) impor'

- 7e57ee63 40-engine old:14 … '0-14 "3~9 모두 권고대로" 중 4~9 반영(원문 `_drafts/user_decisions.md` 마지막 항목: "4 run_stage_b settings 필수 인자(기본값 제거). 5 as-built b(context_fp)·c(SearchContext 옛 이름 읽기 속성) 수용, design 정정 v1.9.2 기록. 6 D6로 단계 A non-ok 회로 S0 24블록 재계산 수용(fail-closed), 정정 기록. 7 checkout 경로를 S0 값에서도 제거(로딩 시 해석) ... 8 test 환경 OPENBLAS 스레드 1 고정 + 엔진 결정론 원인 수정은 2 착수 전(백로그). 9 sizing CONTR'

- 7e57ee63 40-engine old:14 … 'peError\'로 정정(v1.9.2)."): §2.4.3 `run_stage_b`의 `settings` 필수 인자(결정 4), §2.4.7 `context_fp` 문언을 as-built(평가 커널의 S0 입력 지문)로 정정·`SearchContext` 옛 칸 이름 읽기 속성 과도기 주석(결정 5), §2.4.3·§2.4.9 D6 저장 시점의 결과(단계 A가 ok가 아닌 회로는 스냅샷 없음, fail-closed 수용)와 G-10 판정 2 적용 범위 = 단계 A ok 회로(결정 6), §2.4.3 S0 값에 checkout 경로 없음(결정 7), §11 U17 ② 선행에 NFR-4 결정론 원인 수정(결정 8), sizing'

- 7e57ee63 41-gain-budget old:17 … '획 v6.38 기준, 미검증)을 v6.38.1·v6.38.2와 다시 맞추고(재점검 94건), 계획 넘김 목록(LA-1 후속 정정 표 v6.38.2 행)과 DEC-105 (1)~(12)를 반영했다: DC 블록 재작성 design(40 §3.7-A -- card WB-1, O-165 (a) 비교표·design 입력 측정 표·승인 질문 Q-DC1~Q-DC4), 이득 L 하한 found_db 목표·fail-closed(41 §6.4-1), 매크로 P'

- 7e57ee63 41-gain-budget old:17 … '`graph.ss_circuit`(writer 블록 `ss_circuit_field`, writer 이름 `ss_circuit`, `ss_circuit.py` 층 1)으로 대체, `metrics_ss`·`metrics_aux`·`ss_nodal` READS, 조립 사본 둘 삭제, `CODE_PASSIVE_MISSING` 한 자리(`ss_circuit.py`), DC 전도 소자(저항) 결측만 fail-closed(`graph.ss_nodal` = `Undefined`, `icm_config` `passive_value_undeclared`; 용량만 결측이면 노달 계·측정 구성 섬), G-10 ss 단계 graft +1·`s'

- 7e57ee63 41-gain-budget old:17 … 'c 착수 조건 (iv) 범위 -- 근거 `wt/_drafts/evidence/2026-10-21/design41_v1126_validation.md` MF-A·R1~R8): (1) 4.7-3b (1) 차동 출력 결합(두 출력 판정이 같을 때만, 갈리면 새 code `icm_config_feedback_outputs_split`)과 이 card의 갈래 순서(① 지원 밖 ② 갈림 ③ S-OS2 fail-closed) (2) 지원 밖 원소 = S1 `device.unsupported` READS(kind 목록 대조 삭제 -- 둘째 계산 제거), code 이름 `icm_config_feedback_element_unsupport'

- 7e57ee63 41-gain-budget old:17 … "ransfer_resolution`(δV_out = |z_u|ᵀ|r|, `icm_config.py` 비공개 -- 실현 가능성 근거·DE-1 이동 인계), 기록 = `IcmConfig.transfer` resolution 칸 = δA_num (2) 멈춤 S-OS2 -- 일반형은 계획 v6.24 N3.8 '차동 출력 회로의 측정 구성'(O-68 (2))이 정했고 후속 card 몫, IT-2c는 fail-closed로 시작(O-67 (5)) (3) 13회로 출력 구조 분류표 승인 = IT-1·IT-2 통합 병합 조건(O-66 (3), 충족 -- O-66 (1)) (4) 정의 불능 code 목록 보완, 깨지는 기존 test 넷 "

- 7e57ee63 41-gain-budget old:17 … '*(design 검증 MF-1~MF-4·N-1~N-3, gap 분석 `_drafts/evidence/2026-10-21/design_it12_v1122_plan_gap.md` N1~N3): MF-1 OS (e) 단단한 경로 = MOS 엣지(저항만 경로는 기존 `dc_resistor_cycle` 정지가 먼저) -- 4.7-1a·4.7-8a; MF-2(= gap N1) 멈춤 S-OS1 실행 중 fail-closed code `icm_config_output_root_w3`(N3.14 적용) -- 4.7-1a·4.7-3b (1)·L8 (d); MF-3 권한표 `DC_WRITES`·sizing CONTRACT 소유표 등록, 깨지'

- 7e57ee63 41-gain-budget old:17 … '1 실행 중 fail-closed code `icm_config_output_root_w3`(N3.14 적용) -- 4.7-1a·4.7-3b (1)·L8 (d); MF-3 권한표 `DC_WRITES`·sizing CONTRACT 소유표 등록, 깨지는 기존 test 둘은 test 작성 주체 몫, OS (j) grep 꼴 -- 4.7-1a; MF-4 멈춤 S-OS2(차동 출력 + 되먹임 선언) fail-closed code -- 4.7-1a; N-1 분류 걷기에 `_TIE` 엣지 없음(계획 N6.5)·toy OS (k); N-2 동작 변경 목록 기준선 둘로 나눔·(6) 넓힘 -- 4.7-8; N-3 S-OS 발동 측정에 he'

- 7e57ee63 41-gain-budget old:17 … ' J-E 입력 DC 정책을 IT-1(W4 입력 뿌리 y 키 = 뿌리 넷, 입력 뿌리 최대 하나·둘 이상이면 정지)과 IT-2(커널 = 선형 감도 끝, 끝 풀이는 수락 반복·front)로 개정, §4.7 신설(입력 포트 창 정본 하나 -- 필드 셋 `node.dc_window`·`node.dc_window_def`(DE-1 예약)·`node.dc_window_def_refined`, 끝 풀이 fail-closed 사유, metric 읽기, card IT-1·IT-2 interface), §6.7-1 v1 문장·§6.7-1a 개정 후 문언(O-13 (1)·IT-Q1 (나), as-built 문단은 history)·§6.7-1'

- c7a51e41 40-engine old:877 … '연(블록 함수 호출 0, `replays` 1), 입력과 무관한 예외(예: 블록 안 `ValueError`·`KeyboardInterrupt` 흉내)는 등록 안 함, 같은 키 성공·실패 섞임 `ValueError`, `from_record`, `Donors` 하위 아닌 객체 거부, `test_graft_equals_compute`(`*`), `test_index_single_source`, fail-closed (1)~(4)·(6)(§2.4.5 표, (5)는 card C) / `test_compute_block.py` 다시 쓰기: 인자 없으면 `TypeError`, 같은 lineage `reuse`·다른 lineage `'

- c7a51e41 41-gain-budget old:1236 … "5.2) | DEC-72 |\n| 4 블록 범위(버퍼 상수항, 바이어스 의사 블록, GB3 기둥 매핑, 고정 입력, 강결합 그룹) | 바이어스 의사 블록·기둥 매핑·고정 입력은 유지. 버퍼 상수항은 섞인 회로에서 버퍼 DP 단계로 바뀐다(P-15, §5.6). 강결합 그룹 좌표 훑기는 폐기(P-1, §5.3.11) | DEC-71 (2)(3)(7), DEC-76 |\n| 5 bin 격자 게이트·fail-closed | 유지(§5.4·§5.6) | DEC-80 |\n| 6 평가 예산 | 몫 규칙·벽시계·계수 유지. '후보 수'의 정의만 n_i로 바꾼다(§5.8). 국소 봉인 memo는 폐기하고 S3 메모리 색인으로 바꾼다(§5."

