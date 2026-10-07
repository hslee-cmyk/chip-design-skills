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
| `_doc_walk.py` | `map_nets`·`map_element_names`·`collect_names` | 넷·원소 이름 자리 순회(공용 helper, 각 함수 2파일 이상 사용) |

helper 도 구조 규칙 A(파일당 진입점 1개)·B(다른 파일 `_` 이름 import 금지)를 지킨다 -- `tests/` 는 구조 test 대상 밖이라
`test_generator_sanity.py` 가 같은 검사기를 `topogen/` 에 직접 건다. 규칙 H(1:1 test)는 엔진 하위 패키지에만 적용되며
`generality` 는 하위 패키지 이름이 아니다(고아 검사 대상 아님).

## test

| 파일 | 불변량 |
|---|---|
| `test_generator_sanity.py` | 입력이 의도대로인가: 4종·레일 2·극성 둘, library 이름과 서로소, 로드 통과·JSON 집계 일치, 치환 전단사·역치환, 극성 두 번 = 원래, 섞기는 내용 보존(실제로 섞임), 복제는 원소 2배, 태그 잡음은 무시 키만 |
| `test_metamorphic_load.py` | 변형한 doc 의 로드 투영 = 원래 투영에 같은 변형을 적용한 것(이름 치환·레일/kind 치환), 섞기·태그 잡음은 투영·정렬 결과 동일, 복제는 앞 단 포함 + 2배, 변형 합성도 통과 |
| `test_metamorphic_fingerprint.py` | `connectivity_fp`(authoring CONTRACT 2절): 섞기·태그/주석 잡음·topology_name 변경 -> 같음(파일 해시는 다름), 이름 치환·넷 하나·원소 하나·극성 -> 다름, 역치환·극성 두 번 -> 원래, 같은 치환표면 입력 순서 무관 같음, 복제는 극성·섞기와 교환 |
| `test_metamorphic_violations.py` | 7가지 위반 x 7가지 변형(그대로·이름 2벌·섞기·극성·복제·태그 잡음)에서 그 위반 하나만 검출, 주입 뒤 이름 치환하면 elements 가 같은 표로 옮겨지고 rejected_gates·not_evaluated 동일 |

`connectivity_fp` 는 이름을 투영에 담으므로 이름 치환에 **불변이 아니다**(CONTRACT 2절 "넷 이름 하나 ... 바뀌면 다르다").
이름에 무관한 것은 fp 값이 아니라 '같은 치환표면 같은 fp, 되돌리면 원래 fp'라는 함수성이다.

## 확장 (S1 그래프·구조 유도가 master 에 들어오면)

새 공개 API(예: S1 그래프 빌더, 구조 유도)마다 `test_metamorphic_<대상>.py` 를 더하고 같은 `synthetic_topologies()` 와
변형기를 쓴다. 기대 불변량 예: 이름 치환 뒤 유도 결과(기둥·미러·차동쌍 등)가 같은 치환표로 옮겨진다, 극성 뒤집기 뒤 n/p 가
맞바뀐 같은 구조, 단 복제 뒤 구조가 두 벌(+ 연결부), 섞기·태그 잡음 뒤 동일. 회로를 더할 때는 `circuits.py` 에
`_<회로>()` 를 만들고 `synthetic_topologies` 의 tuple 에 넣는다(이름은 library 와 겹치지 않게 -- sanity test 가 확인).
