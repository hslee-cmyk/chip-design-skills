### N6.41 card LG-1 -- LUT 생성기의 모델 변수 대응을 PDK 선언으로, VTH 열 삭제(사용자 결정 O-246 D1·D3)

**근거**: 사용자 결정 O-246 D1·D3(2026-11-06, `_drafts/user_decisions.md` O-246 행). 정의 자리 = N3.16 'LUT 열 정의·모델 변수 대응' 행(이 절은 card 범위·완료 조건만). 원본 방식 = gm/ID 원본 Jespers & Murmann 2017 부록 2 305~307쪽(공정마다 설정 파일의 '시뮬레이터 출력 변수 → 표 변수' 대응 행렬, 부호 −1 -- 로컬 `skills/analog-gmid-design/references/gmid_sources/jespers_murmann_2017/extracted/lookup-table-generation-and-usage.pdf`, 책 쪽 = PDF 쪽 + 302).

**LA-1 차단 판정**: **비차단 -- LA-1 뒤 착수**(O-229 4 '새 검증 도구·인프라는 LA-1을 실제로 막을 때만'). 근거: (i) 이 card는 지금 생성기가 쓰는 같은 출력 식을 선언에서 읽게 옮기는 것이라 LUT 열 값·정의가 바뀌지 않는다(LA-1이 읽는 데이터 불변) (ii) VTH는 엔진 소비자 0이다(비 test `\.vth\b` 읽기 0 -- 재작성 범위 사실, 계획 작성 때 실측; `lut/lut_set.py`·`lut/point_query.py`는 적재·운반만) (iii) LA-1은 sky130 한 공정으로 잰다 -- 공정 교체는 LA-1 측정 경로 밖. 이 판정이 틀렸다는 사실(예: LA-1이 대응 선언을 읽어야 하는 자리)이 나오면 멈추고 보고한다.

**임시 규칙 O-229**: 물리 정합(E-0 fail-closed)과 graph 단일 정본은 완화하지 않는다. 생성기 몫의 값 불변 확인은 ngspice 없이 한다(완료 (2)); ngspice는 그 확인이 바이트 대조로 닫히지 않을 때만이며 그 실행은 O-232 허용 목록 밖이라 그때 사용자에게 묻는다(위임 밖). 엔진 몫(VTH 적재·`OpPoint.vth` 삭제)은 ngspice 0. test 범위 = O-229 2, card 뒤 = 독립 판정 1회. LA-1 뒤 착수라 그때 O-229가 풀려 있으면 그 시점 규칙을 따른다.

**graph 규칙**: 대응은 LUT 입력의 출처(PDK 선언)이지 graph 필드가 아니다. 엔진은 논리 열 이름만 읽고(엔진 쪽 대응 사본 0), 새 cache·memo·sctx 슬롯·결과 칸·값 사본 0. 선언 파일의 sha256은 기존 PDK 선언 출처 기록(`decl_sha256`) 경로로 생성 기록에 든다(새 지문 칸 0 -- 필요하면 design에서 멈추고 보고, 규칙 6).

**범위**(재작성 범위 -- 원칙 8; 줄은 계획 작성 때 실측, 착수 때 base에서 다시):
1. **PDK 선언 항목**: 'LUT 열 ↔ 모델 op 변수 대응'(논리 열마다 op 변수 표현식·부호, 소자 인스턴스 접두 꼴) -- 소비자 = 생성기(만들면 배선; 소비자 없는 선언 필드를 먼저 만들지 않음, O-177).
2. **생성기 배선**: 기준 폭 생성기 `assets/sky130_lut_sweep.py`(`OP_PARAMS` :92, `_fields` :240-243 인스턴스 접두 `@m.xdut.msky130_fd_pr__<cell>`, bin 경계 진단 `_dc_run` :491-511의 `.save` 식)와 슬라이스 생성기(LUT 생성 규칙 선언의 생성기 항목, LM-1d 중점 생성기 포함)가 1의 선언을 읽는다 -- 생성기 안 모델 변수 이름·인스턴스 접두 0. 생성기 저장소 이관은 범위 밖(O-229 4와 같은 이유 -- LM-1d 2).
3. **VTH 열 삭제**(D3): 생성기 열 목록(`COLUMNS` :319·`OP_PARAMS`·`units` :714), 엔진 적재(`lut/lut_set.py:188-215`, `lut/lut_types.py:25` `CAP_TABLE_COLUMNS`·슬라이스 선택 열), `OpPoint.vth`(`lut/lut_types.py:285-294`, `lut/point_query.py:54-61`), `_module_map.py:329` 문언, 그 test; oracle 기록 칸 `VTH_spice`·`vov_spice`·`below_vth_spice`(`tools/spice_oracle/core/compare.py:248-272` -- 판정 소비자 0, 엔진 짝 0이라 정의 동일성 대조 대상도 아님)는 **삭제**한다(출력 전용으로 남길 소비자 없음 -- VTH는 물리 의미 없는 양); oracle 쪽 삭제는 oracle-portability 계획 문언 대조 뒤(지금 그 계획에 이 칸 문언 0 -- `git grep` 실측). 기존 LUT 데이터 파일은 고치지 않는다(VTH 열이 남아도 적재가 읽지 않음 -- 데이터 sha256 불변; 다음 재생성부터 생성기가 내지 않음). bin 경계 진단(`_dc_run` 마스크 `vg >= vth`·`dvth` 통계)은 LUT 열이 아니다 -- 그 진단의 VTH 조건을 남길지(남기면 1의 선언에 진단 전용 항목)·지울지(지우면 진단 기록 재측정)는 spec card가 그 진단의 소비자(bin 규칙 선언 근거 -- oracle OP-7)와 대조해 정하고, 이 계획 개정 없이 정할 수 없으면 멈추고 보고한다.
4. **oracle 대응**: oracle 어댑터 모델 계열 op 이름 표(`tools/spice_oracle/adapters/ngspice/dialect.py:18` `OP_PARAM_TABLES`)가 1의 선언을 읽게 할지는 oracle-portability 계획 개정이 정한다(착수 조건) -- 목표는 엔진 LUT와 oracle 측정량의 대응 출처 하나(원칙 2·O-197).

**완료 조건**: (1) 생성기 안 모델 변수 이름·인스턴스 접두 `git grep` 0, 대응은 PDK 선언에서만 (2) **데이터 값 불변** -- (a) 새 생성기가 같은 입력에서 내는 넷리스트·제어 블록·출력 식 문자열이 옛 생성기와 바이트 같다 (b) **후처리 동등**: 새 파싱·변환 단계(대응 선언의 부호 규약 적용 포함)가 같은 원시 출력에서 옛 단계와 비트 같은 배열을 낸다 -- 입력 = 보관된 원시 출력·체크포인트 재생, 또는 부호가 섞인 합성 원시 출력 toy(ngspice 0); 선언의 부호 규약이 옛 후처리(`np.abs` 절댓값)와 같은 뜻인지는 design에서 정하고, 다르면 멈추고 보고한다. (a)·(b) 가운데 하나라도 다르면 멈추고 보고 (3) 배선 증거 -- 대응만 다른 toy 선언(다른 op 변수 이름)에서 생성기가 다른 출력 식을 내고 엔진 코드는 바뀌지 않는다(실행 없이 문자열 대조) (4) VTH 정의·소비 `git grep` 0(생성기 열 목록·엔진 적재·`OpPoint`·oracle 기록 칸), 기존 LUT 데이터 sha256 불변 (5) O-229 2 test 범위 + N6.3 공통(새 cache 0·회로 이름 0·상수 발명 0) (6) 작성자 ≠ 판정자.

**순서**: card LA-1 병합 뒤(LA-1 비차단) → 이 계획의 LG-1 범위 승인 → oracle-portability 계획 개정(범위 3 oracle 칸·범위 4) → design(S-7) → spec/interface card. base = WB-1 + LM-1e 통합 병합 뒤 master(`lut/lut_set.py`·`lut/lut_types.py` 겹침).

