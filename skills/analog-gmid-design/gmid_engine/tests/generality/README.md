# 일반성(metamorphic) test (`tests/generality/`)

사용자 대원칙(2026-10-07): "topology 에 종속된 엔진은 만들지 않는다. 임의의 topology 에 적용할 수 있어야 한다."
구조 규칙 I(`tests/structure/`)가 소스에서 회로별 분기를 막는다면, 이 폴더는 **동작**으로 확인한다: library 밖 합성 회로를
만들고 이름·순서·극성·크기를 바꿔도 엔진 결과가 기대대로 움직이는지 본다. 지금은 공개 API `gmid_engine.authoring.load_topology`
에 건다. S1 그래프·구조 유도가 master 에 들어오면 같은 생성기·변형기로 test 파일을 더한다(아래 '확장').

```bash
C:/Python314/python.exe -m pytest gmid_engine/tests/generality -q      # skill 디렉터리에서
```

## 생성기·변형기 (`topogen/`, 엔진을 import 하지 않는 순수 dict 조작, test 는 `topogen.__all__` 만 쓴다)

| 파일 | 공개 이름 | 하는 일 |
|---|---|---|
| `circuits.py` | `synthetic_topologies()` | 합성 회로 4종 `{이름: doc}`(부를 때마다 새 객체): `syn_cs_load`(CS + PMOS 전류원 부하), `syn_diffpair5`(5T OTA), `syn_follower`(소스 팔로워 + R·C 부하), `syn_cascode`(텔레스코픽 캐스코드 CS + 전압원 바이어스). 레일 `qp_hi`·`qp_lo` 2개, library 이름과 겹치지 않음 |
| `random_renaming.py` | `random_renaming(doc, seed)` | 모든 원소·넷 이름과 topology_name 을 무작위 새 이름으로 보내는 전단사 표(결정론, casefold 충돌 없음, 글자로 시작) |
| `rename.py` | `rename(doc, mapping)` | 표대로 이름 치환(역표로 되돌아옴) |
| `shuffle.py` | `shuffle_order(doc, seed)` | 원소 목록·supply_nets·포트·JSON 키 순서 섞기(terminals 순서는 내용이라 그대로) |
| `polarity.py` | `flip_polarity(doc)` | nmos<->pmos + 두 레일 맞바꾸기 -> (doc, 레일 치환표). 두 번 = 원래 |
| `duplicate.py` | `duplicate_stage(doc, suffix)` | 회로를 한 벌 더 만들어 직렬 연결(앞 단 출력 -> 뒷 단 이름순 첫 입력, 레일 공유) -> (doc, 이어진 넷) |
| `tag_noise.py` | `add_tag_noise(doc, seed)` | 읽지 않는 태그 키 4개(역할 키 무작위 값 포함)와 `_` 주석 키 잡음 |
| `inject.py` | `inject_violation(doc, kind)`, `VIOLATION_KINDS` | 위반 하나 주입 + 계약이 정한 기대 hit(rule, elements, 정확 일치 여부). 원소는 이름이 아니라 문서 위치로 고른다 |
| `_doc_walk.py` | `map_nets`·`map_element_names`·`collect_names` | 넷·원소 이름 자리 순회(공용 helper, 각 함수 2파일 이상 사용). `map_nets` 는 `bias_inputs` 원소도 옮긴다(CONTRACT 9절) |
| `spec_rename.py` | `rename_spec(spec, mapping, topology_fp)` | 사이징 spec JSON 의 이름 자리(meta.circuit·supplies 레일·input_dc net·원소 값 키·feedback)를 같은 표로 치환 + topology_fp 교체(지문은 호출자가 공개 API 로 재서 준다). 옮기지 못하는 자리(선언 view·노드 목표·영역)는 `ValueError` |
| `spec_template.py` | `synthetic_spec(doc, topology_fp, supplies_v, constraints=())` | 합성 회로용 최소 spec(원소 값 = topology 옛 값, 입력 DC engine, feedback [], 유도 뷰 제약) |

helper 도 구조 규칙 A(파일당 진입점 1개)·B(다른 파일 `_` 이름 import 금지)를 지킨다 -- `tests/` 는 구조 test 대상 밖이라
`test_generator_sanity.py` 가 같은 검사기를 `topogen/` 에 직접 건다. 규칙 H(1:1 test)는 엔진 하위 패키지에만 적용되며
`generality` 는 하위 패키지 이름이 아니다(고아 검사 대상 아님).

하류 단계 공용 `pipeline.py`(엔진 공개 API 만 import -- topogen 밖): 실 LUT v2(`assets/lut_v2_location.json`, 없거나 sha 불일치면
fixture `pipe` 가 skip 이 아니라 FAIL)·sky130 PDK/LUT 규칙 선언으로 회로 변형("orig"·("ren", seed)·("shuf", seed)·"pol") 마다
topology+spec -> S1 -> sizing ctx -> search ctx 를 만들고(캐시), 고정 θ = 원래 회로의 search `layer0_start` 시작점(평가 예산 40,
결정론)을 준다. library spec 에는 소신호 metric 판정 제약을 (metric, op) 가 없는 것만 유도 뷰로 더한다(같은 입력이면 충분).

## test

| 파일 | 불변량 |
|---|---|
| `test_generator_sanity.py` | 입력이 의도대로인가: 4종·레일 2·극성 둘, library 이름과 서로소, 로드 통과·JSON 집계 일치, 치환 전단사·역치환, 극성 두 번 = 원래, 섞기는 내용 보존(실제로 섞임), 복제는 원소 2배, 태그 잡음은 무시 키만 |
| `test_metamorphic_load.py` | 변형한 doc 의 로드 투영 = 원래 투영에 같은 변형을 적용한 것(이름 치환·레일/kind 치환), 섞기·태그 잡음은 투영·정렬 결과 동일, 복제는 앞 단 포함 + 2배, 변형 합성도 통과 |
| `test_metamorphic_fingerprint.py` | `connectivity_fp`(authoring CONTRACT 2절): 섞기·태그/주석 잡음·topology_name 변경 -> 같음(파일 해시는 다름), 이름 치환·넷 하나·원소 하나·극성 -> 다름, 역치환·극성 두 번 -> 원래, 같은 치환표면 입력 순서 무관 같음, 복제는 극성·섞기와 교환 |
| `test_metamorphic_violations.py` | 7가지 위반 x 7가지 변형(그대로·이름 2벌·섞기·극성·복제·태그 잡음)에서 그 위반 하나만 검출, 주입 뒤 이름 치환하면 elements 가 같은 표로 옮겨지고 rejected_gates·not_evaluated 동일 |
| `test_metamorphic_s1.py` | S1 구조 유도(graph `build_s1`, U2~U4): 이름 치환 -> 이름 무관 정준형(segment·가지·기둥·gs 묶음·DC 역할·관계 엣지·G_vgs 개수)이 치환표로 옮겨짐(합성 3종 + library 5회로), 섞기·태그 잡음 -> `snapshot.fp` 동일, 극성 뒤집기 -> kind·레일 맞바꾼 같은 구조, 지원 밖 원소(syn_cascode 전압원) 정지가 변형을 따라감 |
| `test_metamorphic_bias_inputs.py` | `bias_inputs`(authoring CONTRACT 9절): 이름 치환 -> 결과가 치환표로 옮겨짐(합성 syn_cs_load+외부 바이어스 gate, library 7회로), 넷만 치환하고 선언은 옛 이름 -> 새 이름 `gate_only_undeclared` + 옛 이름 `bias_input_not_gate_only`, 섞기·선언 순서 뒤집기 -> 같은 결과·같은 fp |
| `test_spec_generators.py` | `synthetic_spec` 은 hit 없이 로드·원소 값 = topology 값, `rename_spec` 은 치환 topology 와 hit 없이 로드·이름 자리가 표로 옮겨짐·이름 없는 섹션 지문 동일·입력 불변, 옮기지 못하는 자리는 `ValueError` |
| `test_metamorphic_matching.py` | 레이아웃 matching 분류(graph 4.5a `matching_groups`·`matching_dispositions`): 이름 치환 3벌 -> 정준형(다중집합, 정렬 꼬리는 집합)이 표로 옮겨짐, 섞기+태그 잡음 3벌 -> tuple 동일, 극성 -> 레일 표로 옮겨짐, 복제 -> kind 수 2배 (합성 3 + library 9, 84 경우) |
| `test_metamorphic_sizing.py` | sizing 3.0 구조 색이 표로 옮겨짐, 쓰기 계획·θ 스키마·zero_cancel 이 표로(차이는 기록된 동률 후보 안만), 고정 θ 평가의 노드전압·원소 전류·소자 op 비트 동일(다변수 반복 SCC 노드만 SccLog.tol 안), 섞기+잡음 -> 스냅샷 지문 동일, 극성 -> kind 무관 개수(writer·dependent·W4·θ 종류별·free) 동일 |
| `test_metamorphic_metrics.py` | 고정 θ 봉인 점의 `ss_evaluate`: 전력·면적·레일 전류는 합 재배열 상계 n·eps·Σ|항| 안, 소신호 metric(gain·UGF·GBW·PM·rout)은 그 metric 분해능(9절 resolution) 안·정의 불가는 같은 code, 섞기+잡음 -> 스냅샷 지문 동일 |
| `test_metamorphic_search.py` | `search_domain` 변수·L 칸·전류 상자가 표로, 고정 θ `evaluate` 상태·목적(재배열 상계)·소자별 제약 행 비트 동일, 층 0 중심 평가 결과가 표로, 층 0 시작점이 표로(**이름 치환에서 실패 -- 아래 발견**), 섞기+잡음 -> 층 0 시작점 동일 |
| `test_metamorphic_layout.py` | 봉인 점에서 만든 `LayoutInput`(W 로그 압축 -- 층 0 점의 m 급 W 는 MemoryError)의 `run_layout`: 외곽 면적·bbox·소자별 배치·그룹 결과·W 요청이 표로, 섞기+잡음 -> 결과 동일 |

`connectivity_fp` 는 이름을 투영에 담으므로 이름 치환에 **불변이 아니다**(CONTRACT 2절 "넷 이름 하나 ... 바뀌면 다르다").
이름에 무관한 것은 fp 값이 아니라 '같은 치환표면 같은 fp, 되돌리면 원래 fp'라는 함수성이다.

## 확장 (S1 그래프·구조 유도가 master 에 들어오면)

새 공개 API(예: S1 그래프 빌더, 구조 유도)마다 `test_metamorphic_<대상>.py` 를 더하고 같은 `synthetic_topologies()` 와
변형기를 쓴다. 기대 불변량 예: 이름 치환 뒤 유도 결과(기둥·미러·차동쌍 등)가 같은 치환표로 옮겨진다, 극성 뒤집기 뒤 n/p 가
맞바뀐 같은 구조, 단 복제 뒤 구조가 두 벌(+ 연결부), 섞기·태그 잡음 뒤 동일. 회로를 더할 때는 `circuits.py` 에
`_<회로>()` 를 만들고 `synthetic_topologies` 의 tuple 에 넣는다(이름은 library 와 겹치지 않게 -- sanity test 가 확인).

## 하류 단계 발견 (2026-10-08, 실 LUT v2, test_metamorphic_search)

- **층 0 시작점이 이름에 따라 바뀐다**(`test_layer0_start_follows_renaming`, 6회로 중 4회로 실패: syn_diffpair5·two_stage_ota·
  folded_cascode·ngcc_3stage_ff). 상자 중심·전류 중심 출발 평가는 치환표를 따라가지만(`test_layer0_centre_follows_renaming` 통과),
  search CONTRACT 3.21 3 단계 Halton 시험이 "변수 i(1 의 순서)에 i 번째 소수 기저"이고 변수 순서 = θ 스키마 성분 순서(이름 정렬)라
  이름 치환이 소수 기저 배정을 바꾼다 -> 다른 시험 점 열 -> 다른 시작점(예 two_stage_ota seed 1: origin halton:11 대 halton:13,
  t 0.578 대 0.778). 순서 섞기·태그 잡음으로는 같다(이름이 같으므로). 엔진·계약 결정 대상(이 폴더는 test 만 둔다).
- 그 밖 하류 단계(쓰기 계획·θ 스키마·DC 해·소신호/DC metric·탐색 정의역·고정 θ 평가·레이아웃 면적)는 이름 치환·섞기·태그 잡음을
  계약이 정한 수준(비트 동일 또는 계약 허용오차)으로 따라갔다.

