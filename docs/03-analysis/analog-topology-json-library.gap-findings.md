# analog-topology-json-library — Gap Findings (배치 5)

> 목적: `library/_TEMPLATE.topology.json` 스캐폴드 + Design §4.5 절차가 "새 논문에서 처음부터
> topology JSON authoring"을 실제로 감당하는지 독립 검증. 대상: Xie & Chen, "A 126uW
> Current-Reuse Telescopic OTA with Class-AB Output Stage" (2026-07-28 원문 PDF 18페이지
> 직접 재확인 — 이전 background agent 세션의 `sizing_results.json`은 참고만 하고 신뢰하지 않음).
> 산출물: `library/current_reuse_telescopic_ota.topology.json` (41개 소자).

이 문서는 "무엇을 찾았는가"가 산출물이다 — 문제를 못 찾았다면 검증이 부실했다는 신호다(Do
문서 배치 5 게이트). 아래 항목들은 실제로 발견된 것들이다.

---

## 1. 스키마 필드별 실제 커버리지

| 필드 | 결과 | 근거 |
|---|---|---|
| `netlist`(connectivity) | **그대로 채울 수 있었음 — 단, sub-block별 확신도가 크게 다름** | Fig.2(1단, 11개)는 단일 명확한 스키매틱이라 확신도 HIGH. Fig.3(2단 Class-AB, 14개)/Fig.4(bias-gen, 9개)는 소자 밀도가 높고 일부 내부 노드가 원문에 라벨이 없어 확신도 LOW — 아래 §2 참고 |
| `symmetry.matching_pairs` | **부분적으로만 자동화됨 — 중요한 절차 결함 발견** | §3 참고 — `find_matching_candidates()`의 diff_pair 판정이 W를 요구해 사이징 전 단계에서 항상 빈 결과를 반환함 |
| `compensation` | **명확하게 판단 가능했음(null이 정답)** | 1단이 current-reuse(PMOS+NMOS 입력 동시사용, gm1=gmn+gmp)라 `miller_ota_topology()`가 가정하는 표준 1단 구조와 다름 — "구조 일치 여부"로 판단하는 게 정확히 이 경우에도 유효했음(§4 참고) |

---

## 2. netlist 확신도가 sub-block마다 다른 이유 (아예 표현이 안 된 것)

`_TEMPLATE.topology.json`의 인라인 주석("원문을 직접 확인, 상상 금지")은 **"어떻게 확인해야
확신할 수 있는가"에 대한 가이드가 없다** — 이게 실제 한계다. Fig.2처럼 소자 10여개짜리 단일
스키매틱은 이 PDF 렌더링 해상도에서 충분히 읽히지만, Fig.3/Fig.4처럼 소자가 밀집되고 내부
노드에 라벨이 없는 그림은 같은 절차·같은 해상도로는 확신 있게 옮기지 못했다. 구체적으로:

- Fig.3(Class-AB)의 M9a/M9b가 정확히 어떤 방식으로 Vop1(1단 출력)을 읽어 M15 게이트를
  미는지, Vop 레그(M13/M25/M26)가 정확히 어떤 소자로 구성되는지는 원문에 그 부분만 확대한
  별도 그림이 없어 Fig.1(전체 스키매틱)과 대조해도 확신하지 못했다.
- Fig.4(bias-gen)의 M31/M32/M33/M34 사이 정확한 캐스코드 순서는 추정으로 채웠다 — 실제로
  이 추정에 결함이 있었다(§5 참고, `run_topology_pipeline()`이 즉시 잡아냄).
- 스키마 자체(`netlist`/`symmetry`/`compensation` 3개 필드)는 이 정보를 표현하는 데
  부족하지 않았다 — **부족한 건 스키마가 아니라 "이미지에서 밀집된 회로를 정확히 읽는"
  절차/도구**다. 이건 이번 feature의 범위(JSON 스키마 설계)가 아니라 별도 개선 과제로
  남긴다(예: 이미지 확대/OCR 보조 도구, 또는 저자가 직접 회로도를 검증하는 체크포인트 삽입).

**교훈**: `_TEMPLATE.topology.json`과 Design §4.5 절차는 "필드를 어떻게 채우는가"는 잘
안내하지만 "필드를 채운 결과를 얼마나 신뢰할 수 있는가"는 안내하지 않는다 — 향후 스캐폴드에
sub-block별 확신도를 명시적으로 기록하는 필드(`_confidence_note`, 이번에 즉석으로 추가함)를
정식 스키마 요소로 승격하는 게 좋겠다.

---

## 3. 애매해서 판단이 필요했던 것 — `find_matching_candidates()`의 diff_pair 한계 (중요 발견)

Design §4.5 3번 절차는 "`find_matching_candidates()`를 실제로 호출해 나온 후보를 5가지
패턴으로 필터링"하라고 안내한다. 실제로 호출해보니:

```
current_mirror: 9개 그룹 발견(정상 동작)
diff_pair: {} (빈 dict!)
```

원인을 코드에서 직접 확인(`stick_diagram.py` `find_matching_candidates()` 448행):
```python
for (kind, source, w), group in by_source.items():
    if w is None or len(group) != 2:
        continue
```
**diff_pair 판정은 `w`(소자 W)가 같아야 한다는 조건이 있는데, topology JSON 단계의
netlist는 애초에 W가 없다**(사이징 이전이므로). 그래서 이 함수의 diff_pair 경로는 topology
authoring 단계에서 **항상 빈 결과를 반환한다** — current_mirror 경로(게이트 net 공유만
확인, W 불필요)는 정상 동작하지만, diff_pair는 그렇지 않다.

실제로 M1a/M1b, M4a/M4b는 명백한 진짜 차동쌍(같은 source 공유 + 다른 gate)인데도 자동
탐지되지 않았다 — 손으로 판단해 `symmetry.matching_pairs`에 채웠다(같은 구조적 신호:
source 공유+gate 다름을 직접 코드로 재현해 확인, 실제로 정확했다).

**교훈 → 즉시 수정 완료(우회가 아니라 근본 수정)**: 처음엔 "diff_pair는 이 함수에 의존하지
말고 손으로 확인하라"고 Design §4.5를 고쳤으나, 사용자가 더 정확한 지적을 했다 —
`find_matching_candidates()`(이름 그대로 "매칭 **후보** 탐지" 함수)의 존재 이유는 AI가
모든 소자쌍을 수동으로 훑지 않도록 구조적으로 가능한 후보를 미리 좁혀 **토큰을 아끼는 것**이고,
이건 사이징 전/후 상관없이 항상 유효한 이점이다. 진짜 문제는 "이 함수를 사이징 전에 쓰면
안 된다"가 아니라 **diff_pair 경로의 W 요구조건이 하드 게이트로 박혀 있어서 이 함수 본연의
목적을 사이징 전 단계에서 무력화시킨 것**이었다. 그래서 `stick_diagram.py`의
`find_matching_candidates()`를 직접 수정했다 — W가 있으면(사이징 후) 지금처럼 W까지
일치해야 후보로 잡고(대형 회로 오탐 방지), W가 없으면(사이징 전) 구조적 신호만으로 후보를
낸다. 재시험 결과 M1a/M1b, M4a/M4b, M37a/M37b가 즉시 diff_pair 후보로 나왔고(수동 확인과
정확히 일치), 덤으로 bias-gen의 의심스러운 M31/M32 후보(§5에서 확인된 Euler 결함이 있던
바로 그 sub-block)까지 자동으로 표면화됐다 — 기존 self-test 전체 회귀 없음 확인. 이 수정으로
Design §4.5 3번 절차는 다시 "함수를 그대로 호출"로 되돌아갔다(수동 우회 불필요).

---

## 4. `compensation` 판단 — null이 실제로 옳았던 사례

이 회로는 2단이고 Miller 보상(Cc/Rz)을 쓰지만, `miller_ota_topology()`는 **표준 1단**(간단한
차동쌍+미러 부하)을 가정한다. 이 회로의 1단은 current-reuse telescopic(PMOS 입력 M1a/b +
NMOS 입력 M4a/b가 같은 branch에 직렬로 있어 gm1 = gmn + gmp, 논문 자체 Eq.3~5로 유도)이라
`miller_ota_topology()`의 gm1 계산식과 구조적으로 다르다. **"구조가 일치하는가"를 판단
기준으로 삼는 원칙(배치 3에서 정립)이 여기서도 정확히 작동했다** — this time null이
정확한 결과였다(이전 두 example에서는 있음/null 각각 한 번씩 나왔었는데, 이번 사례는 "구조가
안 맞으면 억지로 끼워 맞추지 않는다"는 원칙의 첫 실전 확인이다.

> **2026-07-29 추가 참고**: 이 회로의 topology.json은 이후 세션에서 사용자와 함께 논문을
> 처음부터 끝까지 재확인하며 오류 3건(가상 bias-gen 소자, Class-AB Vop측 12개 소자 누락,
> M9a/M18a 극성 오류)을 발견·수정했다 — 전체 소자 매핑표와 근거는
> `references/sky130-worked-example.md` §13 참고. 이 섹션(§4)의 compensation=null 결론
> 자체는 그 수정과 무관하게 여전히 유효하다.
>
> **2026-07-30 추가 참고(중요)**: 위 결론("null이 정확한 결과")은 **"기존 3개 등록 함수
> 대비"** null이 맞다는 뜻이지, 이 회로가 영구히 보상 없이 설계돼도 된다는 뜻이 아니다 —
> 이 회로는 실제로 Cc/Rz Miller 보상을 쓰는 다단 구조라 보상 자체는 필요하다. 이 구분을
> 명확히 하려고 `_compensation_status` 필드(`not_applicable`\|`pending_topology_fn`\|
> `resolved`)를 topology.json 스키마에 추가했다 — 이 회로는 `pending_topology_fn`(새
> `topology_fn` 유도·등록 대기 중, do.md 배치 7-3)이지 `not_applicable`(보상 자체가
> 불필요한 단일 스테이지)이 아니다.

---

## 5. `run_topology_pipeline()`이 실제 authoring 오류를 잡아낸 사례 (검증 게이트의 실제 가치)

더미 `sizing_overrides`(모든 소자 n_fingers=2, finger_w=5, w=10, sub-block별 stack_id)로
파이프라인을 실행한 결과:

```
box_shape.ok=False (row_widths: stage1=22, stage2=28, biasgen=18, cmfb=14, 비율 2.0>1.5)
audit_row_split.ok=False (24개 체크 실패)
  1. euler[biasgen] FAIL -- status=blocked, odd_nodes=[]
floorplan bbox=28x7, density=0.42
coverage.ok=True, missing=set()
```

- **box_shape FAIL과 대부분의 audit_row_split FAIL은 "예상된" 결과다** — 모든 소자에
  동일한 더미 finger 값을 줬으니 sub-block별 폭이 불균등한 것과, row 분할을 전혀 안 했으니
  matching-safety가 깨지는 것은 배치 2에서 이미 확인한 알려진 한계(row 분할 미자동화)의
  재현일 뿐이다.
- **`1. euler[biasgen] FAIL`은 진짜 발견이다.** `status=blocked`(홀수차수가 아니라
  그래프 자체가 끊긴 상태)는 §2에서 이미 LOW 확신도로 표시한 bias-gen(Fig.4) 재구성에
  실제 연결 결함이 있었다는 증거다(구체적으로 M32를 `source=drain=gate=N31_32`인 자기
  자신에게 닫힌 노드로 잘못 구성함 — 실제 회로에서 있을 수 없는 축약형 diode-loop를 만든
  것으로 보인다). **이 배치에서 이 결함을 손으로 다시 고치지 않았다** — 그 자체가
  검증 게이트(Design §4.5 5번)가 의도한 대로 작동했다는 증거이기 때문이다: 확신도가
  낮다고 스스로 표시한 sub-block에서 실제로 결함이 나왔고, 파이프라인이 그걸 즉시 잡았다.
  **결론: 검증 게이트는 실제로 가치가 있다** — "확신도 LOW"라는 자기평가와 "파이프라인이
  실제로 잡아낸 결함"이 정확히 일치했다.
- `coverage.ok=True`는 41개 소자 전부가 stick-diagram row에 등장한다는 뜻 — 이건 PRE-FLIGHT
  사고27(원래 사고: CMFB/bias-gen/Class-AB 22개 소자 통째 누락)이 이 도구 체계에서는
  재발하지 않았다는 직접 증거다. 모든 소자에 `stack_id`를 부여하는 게 `sizing_overrides`의
  필수 항목이라는 스키마 설계 자체가, "일부 sub-block을 빼먹고 넘어가는" 실수를 구조적으로
  차단한다(빼먹으면 `run_topology_pipeline()`을 아예 호출할 수 없다 — 그 소자의 override가
  없으면 connectivity만 있고 layout 필드가 없는 상태로 계산이 진행되어 즉시 에러가 난다).

---

## 6. 종합 평가

| 질문 | 답 |
|---|---|
| topology JSON 스키마(connectivity+symmetry+compensation)가 새 회로를 표현하기에 충분한가? | **그렇다** — 41개 소자, 15개 matching pair, compensation 판단까지 3개 필드로 전부 표현 가능했다. 부족했던 건 스키마가 아니라 원문을 정확히 읽는 절차(§2) |
| Design §4.5 절차가 실제로 안내가 되는가? | **그렇다(수정 후)** — symmetry 단계(3번)가 처음엔 `find_matching_candidates()`의 diff_pair 경로(W 필수)와 어긋났지만, 우회가 아니라 그 함수 자체를 수정해 근본적으로 해결했다(§3) — 함수를 그대로 호출하는 원래 절차가 그대로 유효하다 |
| 검증 게이트(`run_topology_pipeline()`)가 실제로 유용한가? | **그렇다** — 확신도 LOW로 자체 표시한 sub-block에서 정확히 그 지점의 구조적 결함(Euler 불가)을 잡아냈고, `find_matching_candidates()` 수정 후에는 같은 결함을 매칭 후보 단계에서도 한 번 더 표면화했다(M31/M32) |
| PRE-FLIGHT 사고27(sub-block 통째 누락)이 이 도구 체계로 재발하는가? | **재발하지 않았다** — `sizing_overrides`가 모든 소자에 대해 필수이므로 빠뜨리는 게 구조적으로 어렵고, `check_stick_diagram_coverage()`가 실제로 missing=set()을 확인해줬다 |

## 7. 후속 조치 제안 (이번 배치 범위 밖, 기록만)

1. ~~Design §4.5 3번 절차 문구 수정~~ — **완료**: `find_matching_candidates()`의 diff_pair
   경로에서 W를 필수→선택적 필터로 수정, 절차 문구도 원래대로("함수를 그대로 호출")
   되돌림(§3 참고)
2. `_TEMPLATE.topology.json`에 `_confidence_note` 필드를 정식 스키마 요소로 승격 검토
3. bias-gen(M31/M32) 재구성 결함은 이번 배치에서 의도적으로 고치지 않았다 — 실제 telescopic
   OTA 리포트를 완성하려면(배치 6) 원문을 다시 확인해 이 부분을 먼저 바로잡아야 한다

## 8. `verify_symmetry_dispositions()` 신설 — 후보 누락을 구조적으로 차단 (사용자 요청, 완료)

§3의 W 필터 수정 이후, 실제 `current_reuse_telescopic_ota.topology.json`을 재검증하니
`find_matching_candidates()`가 찾은 9개 후보 그룹 중 상당수가 `matching_pairs`에 조용히
빠져 있었다(예: M6/M8/M13이 전부 같은 Vbias1을 공유하는데 M8/M13만 기록돼 있었음, M27/M28/M29
같은 3-leg 미러를 pairwise 2개 항목으로 쪼개 기록해서 "그룹 전체가 한 항목에 있는지" 검사에
실패함). 사용자가 "이 함수는 후보만 추출해주니, AI가 실제로 후보를 검증해서 확정한 후 JSON에
기록하는 걸 강제하라"고 요구 — `run_full_circuit_audit()`의 "every candidate has a recorded
disposition" 체크와 동일한 원리를 `verify_symmetry_dispositions(transistors, matching_pairs,
dispositions)`로 topology-authoring 단계에 이식했다.

- `matching_pairs`에 없는 후보는 반드시 `symmetry.dispositions`(설계-report-spec §1.5의
  5가지 패턴 category + reason)로 기각 사유를 남겨야 `ok=True`.
- 9개 후보 전부 처리(6개는 `false_positive_consumer_reads_bias`/`diode_chain`, 1개는 아직
  검증 안 된 저확신도 sub-block이라 `needs_reverification`으로 명시 — M31/M32, §5와 연결).
- self-test(Test 21.5)로 "빠뜨리면 FAIL, 채우면 PASS" 회귀 확인 + 실제 telescopic OTA
  전체 재검증 통과.
- `folded_cascode`/`two_stage_ota` 기존 topology JSON도 이 새 게이트로 재검증 — 둘 다
  이미 완전했음(`ok=True`, dispositions 불필요).

## 9. `linked_topology_files` + net 이름 대소문자 재검증 — 사고8/사고9 재발 방지 완결 (사용자 요청, 완료)

§8 이후 두 가지를 사용자가 연달아 짚었다:

1. **"다단계 회로면 모든 단계로 확장해서 매칭관계를 따지고 있냐"** — 실제로는 이번 시연이
   회로 하나=파일 하나였기 때문에(41개 소자 전부 한 리스트) `find_matching_candidates()`가
   항상 전체를 봤을 뿐, **강제된 게 아니었다**. 향후 회로를 stage별로 여러 topology JSON
   파일로 쪼개면 사고8(sub-block별로 나눠 돌려 cross-block 매칭을 놓침)이 재발할 수 있는
   구조였다. → `load_topology()`에 `linked_topology_files`(형제 파일 목록, 방사형) 지원을
   추가 — 이 필드가 있으면 어느 형제 파일을 진입점으로 읽든 자동으로 전부 병합한다. 합성
   2-파일 테스트(Test 21.6)로 cross-file matching 후보가 실제로 발견되는지 확인.
2. **"예전에 겪었던 대소문자 문제(사고9)가 이번에도 반영됐냐"** — 확인해보니 **반영 안 돼
   있었다**. `run_full_circuit_audit()`에는 이 검사(net-name case consistency)가 있지만,
   새 topology-JSON 파이프라인(`load_topology()`/`find_matching_candidates()`/
   `verify_symmetry_dispositions()`)엔 이 검사가 아예 없었다 — 지금까지 예제 3개가 우연히
   표기를 일관되게 써서 드러나지 않았을 뿐이다. `linked_topology_files`(서로 다른 시점/
   작성자가 만들 파일들을 병합)를 만든 직후라 이 위험이 특히 커진 상태였다. →
   `verify_symmetry_dispositions()`의 0번 단계로 net 이름 대소문자 스캔을 추가(자동 통일
   하지 않고 FAIL만 시킴 — 사람이 원본을 고치게 함). self-test로 `Vbias1`/`vbias1` 같은
   불일치를 실제로 잡아내는지 확인.

**교훈**: 이번 세션 초반(다른 예제 회로 작업)에서 이미 겪고 고친 사고(8, 9)라도, **새로
만든 오케스트레이션 레이어에 그 교훈이 자동으로 이식되지 않는다** — 각 신설 함수마다
"이 사고가 여기서도 재발할 수 있는가"를 별도로 재확인해야 한다는 게 이번 배치 전체를
관통하는 가장 중요한 메타 교훈이다.

## 10. `run_topology_pipeline()` sizing_overrides 누락 검사 — 사고27 재발, 자체 발견 (완료)

§9 직후 "나머지 중요 사고 방지 로직도 확인해보라"는 요구에 따라 점검하다가 자체적으로
발견: `run_topology_pipeline()`에 소자 하나를 `sizing_overrides`에서 빠뜨려도 에러 없이
`n_fingers=1`/`stack_id=None` 기본값으로 조용히 처리됐다. 게다가 `split_into_stacks()`가
`stack_id=None`인 소자를 `(kind, "unspecified")` 폴백 그룹으로 자동 흡수해버려서,
`check_stick_diagram_coverage()`("사이징된 소자 전부가 어떤 물리 행에든 있는가")조차 이
소자가 "존재는 한다"고 통과시켰다 — 사이징 자체가 안 된 소자가 `coverage.ok=True`인 채로
조용히 넘어갈 뻔했다. M11을 실제로 빠뜨려 재현 확인.

**사고27과 같은 근본 유형**: "부분만 처리하고도 커버리지 체크가 그걸 못 잡는다"는 실패
패턴이 사이징-이후 오케스트레이션 레이어 안에서 또 재발할 뻔한 것 — §9의 메타 교훈("이미
고친 사고라도 새 레이어에 자동으로 이식되지 않는다")이 이번에도 그대로 적용된다.

**해결**: 함수 시작에 `missing_overrides = {t.name for t in transistors} -
set(sizing_overrides.keys())`를 계산해 비어있지 않으면 즉시 `ValueError`(어떤 소자가
빠졌는지 이름까지 명시). Test 26.5로 회귀 확인. function-selection-map.md §10 반영.

## 11. 함수 중복 감사 — 전수 조사 + 27건 사고 교차검증 (사용자 요청, 완료)

사용자가 "모든 함수를 전수로 살펴 중복/불필요 함수를 찾고, 27건 PRE-FLIGHT 사고와
교차검증해서 승인 후 고치라"고 요구 — stick_diagram.py 46개/sizing_recipe.py 13개/
topology_library.py 5개 전 함수의 실제 코드 바디를 읽어 대조했다.

**확인된 진짜 중복 2건(리팩터 완료)**:
1. net 대소문자 스캔 로직이 `run_full_circuit_audit()` 2번 체크와
   `verify_symmetry_dispositions()`(§9) 0단계에 복붙돼 있었다 — `_scan_case_collisions()`
   헬퍼로 추출.
2. `skyline_pack_best_width()`/`pack_to_height()`가 "폭 후보를 스윕하며 `skyline_pack()`을
   반복 호출"하는 루프를 복붙 — `_sweep_widths()` 헬퍼로 추출, 각 함수는 선택 기준만 그
   위에 적용.

둘 다 순수 리팩터(동작 변화 없음), self-test 전체 재확인(exit 0, 기존 출력 패턴 동일).

**검증 후 기각된 후보 3건**: `search_unit_cell_sizing`/`search_stack_finger_w`/
`search_shared_finger_w`(unit-cell/Case A/Case B — 서로 다른 제약을 가진 의도된 자매
함수들, 통합 시 오히려 나빠짐), `unit_cell_common_centroid_layout` vs
`common_centroid_2row`(후자가 임의 개수까지 처리하는 상위호환이지만, 전자는 논문 리터럴
패턴(ABBA/BAAB) 대조·추적용으로 별도 존재 이유가 있음 — docstring 관계 명시만 남겨둠,
미착수), missing-names set-difference 패턴(`check_stick_diagram_coverage()` vs
`run_topology_pipeline()` 인라인 체크 — 각 1줄이라 헬퍼 추출 실익 낮음, 보류).

**27건 PRE-FLIGHT 사고 전체 교차검증**: net 대소문자 스캔(위 1번, 사고9 계열)을 제외하면,
나머지 사고가 만든 함수는 전부 그 시점에 없던 새 능력이었다 — "이미 있는 함수로 풀 수
있었는데 새로 만든" 경우는 발견되지 않았다. 함수 삭제 대상 없음.

**교훈**: 중복 후보를 "이름이 비슷해 보인다"만으로 판단하지 않고 실제 코드 바디를 읽어
대조하니, 처음 지목했던 5개 후보 중 2개만 진짜 중복이었고 3개는 문서화된 의도적 분리였다 —
겉보기 유사성과 실제 중복은 다르다는 걸 이번 감사로 재확인.

## 12. §11 이후 — "병합"의 의미 정정과 실제 함수 병합 2건 + hub_merge 누락 발견 (사용자 요청, 완료)

§11에서 `unit_cell_common_centroid_layout()` vs `common_centroid_2row()`를 "상위호환 아닌
지원범위가 다른 관계"로 결론짓고 "포팅 후 삭제"는 위험하다고 판단했었다. 사용자가 의도를
정정: "병합"은 포팅+삭제가 아니라 **하나의 함수가 파라미터로 분기해 두 기능을 다 수행**하는
것 — 이러면 두 알고리즘을 그대로 둔 채 진입점만 합치는 낮은 리스크 리팩터가 된다.

**실제 병합 1 — `common_centroid_layout(pattern_key=None)`**: `pattern_key` 지정 시 표 기반,
미지정 시 그래프 기반으로 분기. 병합 코드를 짜면서 두 가지를 실측으로 새로 발견했다:
(a) count_a==count_b인 대칭 케이스에서 **두 경로가 문자 그대로 같은 패턴을 낸다**(n=4, n=8
둘 다 확인 — 행 순서만 다름). 이전 턴에서 "서로 다른 결과를 낸다"고 답한 건 손으로 추론한
틀린 결론이었고, 사용자가 "common_centroid_2row가 ABBA/BAAB와 같은 패턴을 가지고 있지
않나?"라고 반문한 뒤 실제로 두 함수를 나란히 실행해보고서야 정정됐다 — **직접 실행 없이
추론만으로 "다르다"고 답한 것 자체가 이번 세션 내내 지켜온 "근거 없이 확신하지 말 것" 원칙의
위반이었다.** (b) 표에는 3-소자 패턴(`ABCCBA`/`CBAABC`)도 있는데, 옛
`unit_cell_common_centroid_layout()`은 letter_to_name에 A/B만 등록해 이런 pattern_key가
실제로 매치되면(`n_per_device=6`처럼) `KeyError`로 불명확하게 죽는 잠재 버그였다(직접
재현 확인) — 병합하며 명확한 `ValueError`로 교체.

**실제 병합 2 — `interdigitate_layout(names, base=, repeat=, counts=)`**: 사용자가 "나머지 함수들도
이 관점에서 다시 확인해보라"고 요구해 재검토 중, `expand_interdigitation_pattern()`/
`interleave_counts()` 쌍이 common_centroid 쌍과 정확히 같은 구조(표 기반 비율·다소자 vs
표 없는 round-robin 임의개수)임을 새로 찾았다. 병합 전 grep으로 확인한 결과 **둘 다 이 파일
안에서 실제 호출된 적이 없었다**(`interleave_counts()`는 `common_centroid_2row()`의 그래프
기반 계산으로 이미 대체됐고, `expand_interdigitation_pattern()`은 function-selection-map.md에
등재만 되고 self-test가 아예 없었다) — 병합하며 두 경로 모두에 self-test를 처음으로 추가.

**병합과 무관한 발견 — `verify_symmetry_dispositions()`의 hub_merge 체크 누락**: 병합 작업
중 `run_full_circuit_audit()`의 3번 체크(hub_merge/current_mirror/diff_pair 세 tag 전부
검사)와 대조하다가, `verify_symmetry_dispositions()`가 `find_hub_merge_candidates()`를 아예
호출하지 않는다는 걸 발견 — 사고1(find_hub_merge_candidates를 stage 경계 넘어 안 돌림)과
같은 종류의 gap이 새 오케스트레이션 레이어에 남아있던 것. 세 tag 전부 검사하도록 수정 후
`current_reuse_telescopic_ota.topology.json`에 재적용하니 **6개 hub_merge 후보가 미처리로
드러났다**: vdd/gnd 공급 레일 공유(PMOS 12개/NMOS 9개, `false_positive_shared_supply_rail`),
캐스코드 스택 중간 노드 공유(M3a/M4a, M3b/M4b, `false_positive_cascode_stack_node`), 이미
current_mirror/diff_pair tag로 처리된 것과 같은 소자쌍이 hub_merge tag로도 별도로 잡힌 경우
(M31/M34→Vbias3, M31/M32→N31_32 — tag를 섞지 않는다는 `run_full_circuit_audit()` 원칙 그대로
각각 별도 disposition 기록). 전부 근거와 함께 dispositions에 추가, self-test 재확인(exit 0).

**교훈**: (1) "병합"이라는 단어의 의미(포팅+삭제 vs 분기 통합)를 사용자와 다르게 해석하면
같은 코드를 보고도 정반대 리스크 판단이 나온다 — 애매하면 재확인. (2) "이 함수의 실제 출력이
뭔지 몰라서 추론으로 답했다"는 상황 자체를 만들지 말 것 — 이번에도 결국 사용자가 반문한 뒤에야
직접 실행해 정정했다. (3) 새 검사 로직(hub_merge tag 추가)을 실 데이터에 처음 적용하면 그
데이터의 기존 숨은 gap이 드러난다 — 코드 수정 후 반드시 실제 라이브러리 파일로 재검증할 것,
합성 self-test만으로는 이런 gap을 못 잡는다.

## 13. `common_centroid_layout()` 신설 — 3-소자 확장 요청이 실제로는 N행 구조였음 (완료)

§12에서 `common_centroid_layout()`이 2-소자 전용임을 확인한 뒤, 사용자가 "3-소자 지원을
추가해달라"고 요청했다. 코드를 짜기 전에 표의 3-소자 패턴(`ABCCBA`/`CBAABC`)을
`_hubleaf_sequence_node_path()`로 먼저 검증했더니 **모든 repeat에서 실현 불가능**(`None`)
했다 — hub-leaf 구조에서 서로 다른 leaf로 전환하려면 반드시 hub를 거쳐야 하는데, leaf가
3개면 "A→B 전환 직후 위치가 hub가 아니라 leafB"인 상태로는 그 다음(B→C) 전환이 항상
막힌다(2-소자의 `ABA`/`BAB` 불가능이 leaf가 늘수록 더 강하게 나타나는 것).

사용자에게 "3-소자 hub-leaf 자체를 재조사"하도록 확인받아 추가로 검증한 결과: (a) 블록
형태(`AABBCC`)는 hub-leaf로 유효한 walk임을 확인, 하지만 (b) 기존 함수처럼 **2행**(swap
기반)만으로는 3개 소자의 열평균을 절대 맞출 수 없음을 실측으로 확인(`AABBCC`+1회 회전
`BBCCAA`: A=2.5, B=1.5, C=3.5로 불일치). (c) **3행**(2회 추가 회전, `AABBCC`/`BBCCAA`/
`CCAABB`)을 시도하니 A=B=C=2.5로 완전 일치 — **N개 소자는 N개 행이 필요**하다는 결론.

일반화된 원리(코드로 검증): N개 leaf가 전부 hub 하나에만 연결되므로 이름을 순환 회전해도
그래프 automorphism이 항상 성립하고(2-소자 swap의 N-소자 일반화), 회전이 매 열마다 정확히
한 소자만 배정하므로 row_0의 블록 배분이 불균등해도 N개 행 전체에서 모든 소자가 모든 열을
정확히 1번씩 지나간다 — 이 성질이 열평균 완전 일치를 자동으로 보장한다.

`common_centroid_layout(names, leafs, hub_net, count)` 신설: row_0을
`build_graph()`+`check_euler_condition()`+`hierholzer()`로 계산 후 나머지 N-1개 행은 회전만으로
생성(재계산 불필요, automorphism으로 보장됨). self-test(Test 12.7)에 N=3 실측(열평균/개수
검증) + 각 행을 `_hubleaf_sequence_node_path()`로 독립 재검증(구성 로직을 안 믿고 재확인)
+ 3-소자 표 패턴이 실제로 무효라는 대조군 + N=2가 기존 swap과 동등함을 보이는 회귀 + 실패
케이스(오일러 불가능/길이 불일치/중복 이름) 전부 추가. 전체 self-test exit 0 확인.

**교훈**: "함수를 확장해달라"는 요청을 받으면 파라미터를 어떻게 늘릴지부터 설계하지 말고,
그 확장이 실제로 의미 있는 결과를 낼 수 있는지(표의 3-소자 패턴 자체가 hub-leaf 구조에
안 맞았다)를 먼저 코드로 검증할 것 — "호출은 되지만 항상 실패하는 기능"은 지원이 아니다.
이번에도 사용자가 "그거 확실해?"라고 반문하기 전엔 제자리에서 멈추지 않았다는 패턴이
반복됐다(§12와 동일 교훈) — 확신이 서지 않으면 사용자가 묻기 전에 스스로 먼저 실행해
검증하는 습관이 필요하다.

## 14. `common_centroid_layout()` 일반화 — 소자 개수/`n_rows` 자유 지정 (완료)

§13 직후 사용자가 "이 함수를 일반화해서 소자 개수와 row 개수 제약도 인자로 받고, 안
정해주면 최적안을, 정해주면 그 제약 안에서 최적안을 내도록" 요청했다.

**입력 인터페이스 변경**: `names/leafs/hub_net/count`(개별 인자)에서 `transistors: list`
(Transistor 리스트, `n_rows=None` 선택)로 바꿔 hub_net/leaf_of/counts를 직접 추론하도록
했다 — 이 함수가 §13에서 막 신설돼 self-test 1개 외엔 의존하는 곳이 없었기 때문에 이
시점에 시그니처를 고치는 게 나중보다 쌌다.

**두 경로로 분기**: (1) 소자 개수가 전부 같고 `n_rows` 미지정 — 기존 회전 경로
(`_common_centroid_nway_exact()`로 이름 정리, 잔차 0, 증명된 최적) 그대로 사용. (2) 그
외(개수가 다르거나 `n_rows`를 N과 다르게 지정) — 새로 만든 휴리스틱 탐색 경로
(`_common_centroid_nway_search()`).

**탐색 경로 설계 과정에서 실측으로 발견한 문제**: 소자를 비율에 맞게 최대한 고르게 섞은
순서(`_proportional_round_robin()`)를 만들어 `n_rows`개로 균등 분할하는 것만으로는, A=6/
B=4/C=2를 4행으로 나누는 경우처럼 **모든 절단 지점(phase)에서 홀수차수 leaf가 3개
이상**(hub-leaf 오일러 조건 위반) 되는 조합만 나와 하나도 실현 불가능한 걸 실측으로
확인했다(전체 phase 전수 탐색으로 확정). 원인을 분석해 손으로 A=6/B=4/C=2를 다른 배분
({A:2,B:1,C:2},{A:1,B:1,C:0}...)으로 재구성하니 실제로 실현 가능함을 확인 — 즉 균등
분할 자체가 아니라 "패리티(홀짝)를 고려하지 않은 균등 분할"이 문제였다. **해결**: 인접
행끼리 소자 1개씩 주고받아 패리티를 맞추는 보정(`_repair_row_parity()`)을 추가 — 같은
예제에서 target_rows=4의 잔차가 (탐색 실패)에서 0.17로 개선됨을 확인.

self-test(Test 12.7을 새 시그니처로 갱신, Test 12.8 신설 — 개수 다름/`n_rows`<N/
`n_rows`>N/`n_rows`=N 명시 4가지 케이스) 전부 통과, 각 행을 `_hubleaf_sequence_node_
path()`로 독립 재검증(구성 로직을 그냥 믿지 않음).

**정직하게 남긴 한계**: 이 탐색 경로는 증명된 최적이 아니라 candidate 생성 + 잔차
(objective)로 정렬하는 휴리스틱(이 파일의 `search_stack_finger_w()`/`skyline_pack_
best_width()`와 같은 철학)이고, 잔차 지표 자체가 각 행 내부의 x(열) 위치만 정규화해서
비교하므로 소자 총 개수 편차가 크면(예: 어떤 소자가 극소수 행에만 존재) y방향(어느
행에 있는지) 비대칭까지는 잡지 못한다 — 모든 (n_rows, 개수) 조합에서 낮은 잔차를
보장하지 않는다는 것을 반환값(`residual`/`method`)과 docstring에 명시했다.

**교훈**: 코드를 짜기 전 프로토타입으로 알고리즘 아이디어(비례 라운드로빈, 균등 분할)를
먼저 검증한 게 실제로 실패 사례(target_rows=4)를 조기에 발견하게 해줬다 — 실패를 발견한
뒤 "왜 실패했는지"를 손으로 재구성해 원인(패리티 미고려)을 찾고 나서야 올바른 보정
로직을 설계할 수 있었다. 알고리즘을 파일에 바로 쓰기 전에 작은 스크립트로 먼저 돌려보는
것이 이번 세션 전체에서 반복적으로 검증된 습관이다.

## 15. `common_centroid_layout()` dispatch 버그 — n_rows를 N과 같게 명시해도 탐색
경로로 새던 문제 (사용자 발견, 완료)

§14 직후 사용자가 "2행/2소자처럼 swap으로 해결되는 경우, finger를 늘려가며 실제로 최적이
출력되는지 확인해보라"고 요구했다. 직접 스윕(`n_fingers`=2,4,6,8,10,20,50,101)해보니
**`n_rows=2`를 명시하면(N=2와 정확히 같은 값인데도) 탐색 경로로 가서, `n_fingers=2`일 때
residual=1.0(완전 실패)까지 나오는 실제 버그**를 발견했다 — n_fingers=6/10/50에서도
각각 0.067/0.022/0.0008로 0이 아니었다.

**근본 원인**: dispatch 조건이 `if n_rows is None and all_equal`이라 "사용자가 명시한
`n_rows`가 우연히 N과 같은" 경우를 걸러내지 못했다. 더 근본적으로는, 탐색 경로
(`_proportional_round_robin()`+`_slice_into_rows()`)가 **하나의 선형(주기적) 시퀀스를
자르는 방식**이라 "두 행이 서로 swap된 관계"인 후보를 애초에 만들어낼 수 없다 — 실측:
`M2,M2b,M2,M2b`(N=2, 균등)를 2등분하면 phase를 0~3 어느 값으로 바꿔도 항상 두 조각이
**똑같다**(`AB|AB` 또는 `BA|BA`뿐, `AB|BA`는 이 candidate 공간에 없음). 주기적 시퀀스를
등분하면 구조적으로 항상 같은 위상의 조각만 나오기 때문이다.

**해결**: dispatch 조건을 `target_rows`(사용자가 준 `n_rows` 또는 기본값 N)를 먼저 정한
뒤 `if target_rows == n and all_equal`로 검사하도록 변경 — `n_rows`를 사용자가 명시했든
기본값이든, 소자 수와 같고 개수가 균등하면 항상 증명된 최적(회전 경로, 잔차 0)을 쓴다.
self-test에 이 버그를 정확히 재현하는 회귀(finger 수 8가지 값 스윕, 전부
`method=rotation_exact`+`residual=0.0` 확인) 추가.

**교훈**: "행 개수를 자유롭게 지정할 수 있게 해달라"는 요청을 구현할 때, "사용자가 명시한
값이 우연히 기존 특수 케이스(N)와 같을 수도 있다"는 경계 조건을 실제로 스윕해서 확인하지
않으면 이런 회귀가 조용히 남는다 — §14를 만들 때 Test 12.8에 "n_rows=3(=N) 명시" 케이스가
있었는데도(residual=0.036으로 통과) 그때는 "탐색 경로치고 낮다" 정도로만 넘기고 왜 정확히
0이 아닌지 캐묻지 않았다 — 사용자가 finger 수를 늘려가며 직접 확인해보라고 요구한 덕분에
비로소 드러났다. 통과하는 테스트도 "왜 정확히 최적이 아닌가"를 스스로 물었어야 했다.

## 16. `common_centroid_layout()` — 전수 스윕으로 발견한 2차 버그: 균등분배가 우연히
전부 홀수면 대안을 안 찾고 포기 (사용자 요청, 완료)

§15 수정 직후 사용자가 "다른 n_rows 값(3,4,5)에서도 같은 버그 없는지 다 스윕해봐"라고
요구 — N=2~6, count 11가지(각 N에 대해 N,N+1,N+2,N+3,4,6,8,10,20,50,101 중 count>=N인
것)로 `n_rows=N` 총 53개 조합을 전수 실행했다.

**결과**: §15 버그(dispatch 오류)의 재발은 0건이었지만, 스윕 도중 **다른 문제**를
발견했다 — N=4,count=20을 4개 소자에 "최대한 균등하게" 나누면 `divmod(20,4)=(5,0)` →
전부 5(홀수)가 되는데, 이러면 4개 leaf가 전부 홀수차수라 오일러 조건이 깨져 즉시
`ValueError`가 났다. 그런데 `_common_centroid_nway_exact()`의 회전 원리는 row_0의 블록
배분이 무엇이든(균등하든 아니든) 항상 잔차 0을 보장한다고 이미 증명해뒀는데, 그 사실을
활용해 "조금 덜 균등하지만 홀짝은 맞는" 대안 배분(`[6,6,4,4]`)을 시도해보지도 않고
포기한 것이었다 — 실제로 `[6,6,4,4]`는 `check_euler_condition()`으로 직접 확인하니 유효했다
(N=4/count=20,101, N=6/count=20,101 총 4건에서 같은 패턴 확인).

**해결**: `_fix_block_parity()` 신설 — 홀수 항목이 2개보다 많으면 두 개씩 짝지어(단,
1을 빼면 0이 되는 항목은 제외) 1개씩 주고받아(합계 불변) 짝수로 만든다. 홀수 항목 개수의
홀짝(mod 2)은 이 연산의 불변량(=총합의 홀짝과 같음)이라, 총합이 짝수면 0개까지, 홀수면
1개가 남을 때까지 줄인다. 오일러 조건 실패 시 이 보정을 먼저 시도하고, 그래도 안 되면
그제서야 `ValueError`.

**남은 10건은 진짜 불가능임을 확인**: 스윕에서 여전히 실패로 남은 조합(N=3/count=3,
N=4/count=4·5, N=5/count=5·6·7, N=6/count=6·7·8·9)은 재확인 결과 count가 n에 매우
가까워 **다른 분할 자체가 수학적으로 존재하지 않는** 경우였다(예: 4개 양의 정수의 합이
5면 `{2,1,1,1}`이 유일한 분할 — 대안이 없으니 보정도 무력하다). 버그가 아니라 물리적
한계.

**부수 발견**: 스윕 중 `count < n`(소자별 개수가 소자 수보다 작음, 예: N=4에 각 2개씩)
조합에서 `Transistor.__post_init__`의 "n_fingers>=1" 체크가 균등분배로 생긴 0을 잡아내며
불명확한 에러로 죽는 것도 발견 — `_common_centroid_nway_exact()` 진입부에 명확한 사전
`ValueError`로 교체.

self-test(Test 12.9)에 N=2~6 전수 스윕(회귀 없음 확인) + N=4/count=20 보정 성공 회귀 +
`count<n` 명확한 에러 확인 전부 추가. 전체 self-test(`stick_diagram.py`/`sizing_recipe.py`)
exit 0 재확인.

**교훈**: 버그를 하나 고친 뒤 "이 수정이 다른 파라미터 범위에서도 성립하는가"를 실제로
스윕해서 재확인하는 습관이 이번에 다시 값어치를 증명했다 — 발견된 건 원래 버그(§15)의
재발이 아니라, 그걸 고치는 과정에서 처음으로 실제 실행되기 시작한 코드 경로(회전 경로가
큰 count/여러 N 조합에서 실제로 얼마나 자주 호출되는지) 안에 있던 **별도의** 결함이었다.
"이 수정으로 다 됐다"고 여기지 않고 인접 파라미터 공간을 전수 스윕하는 것이 계속 새로운
발견으로 이어졌다(§13→§14→§15→§16 전부 사용자의 재확인 요구에서 시작됨).

## 17. `common_centroid_layout()` — `n_rows != N` 전수 스윕에서 잔차 지표의 두 가지
결함 발견/수정 (사용자 요청, 완료)

§16 직후 사용자가 "나머지 n_rows도 스윕해봐(N보다 크거나 작은 경우)"라고 요구 — N=2~6,
`n_rows`=1~2N+1(N==n_rows인 조합은 §16에서 이미 전수 확인해 제외), finger 다양(11가지
후보 중 유효값)으로 총 260개 조합을 전수 실행했다.

**크래시/구조 오류는 0건**: 모든 결과가 유효한 hub-leaf walk(`_hubleaf_sequence_node_
path()`로 재확인)였고, 소자별 총 개수/행 개수도 전부 정확했다.

**하지만 잔차 지표(`_common_centroid_residual()`) 자체에서 두 가지 결함을 발견**:

1. **길이 1인 행에 있는 소자가 완전히 안 보임**: 기존 구현은 길이 1인 행을 통째로
   건너뛰었는데, 어떤 소자가 그런 행에만 등장하고 길이 2 이상인 행엔 전혀 없으면 그
   소자가 잔차 계산 대상에서 아예 빠졌다 — 실측(A만 있는 길이2 비대칭 행 + B만 있는
   길이1 행 2개)으로 residual=0.0이 나옴을 확인, B가 통째로 안 보이는데 "완벽"으로
   잘못 보고된 것이다. **해결**: 길이 1인 행에 중립값 0.5(왼쪽·오른쪽 어느 쪽으로도
   치우치지 않은 값)를 부여해 그 소자가 반드시 `positions`에 기록되도록 수정.

2. **더 근본적인 한계 — 소자 격리는 residual만으로 못 잡음**: 소자 하나가 통째로 자기
   행에만 격리돼(다른 소자와 단 한 번도 같은 행에 있어본 적 없음) 있어도, 각자 행
   내부에서는 대칭적으로 보이기 때문에 (1)을 고친 뒤에도 residual=0.0이 나올 수 있다
   — 실측(N=2,count=2,n_rows=4 -> 모든 행이 길이 1일 수밖에 없어 rows=
   `['A'],['B'],['A'],['B']`)으로 확인. n_rows가 총 finger 수 대비 너무 많으면
   구조적으로 피할 수 없는 상황이다. **해결**: `_count_isolated_pairs()`(모든 소자쌍이
   적어도 한 행에서 공존했는지 세는 함수) 신설 — 탐색의 정렬 기준을 `residual` 단독에서
   `(isolated_pairs, residual)` 튜플(사전식, 격리 적은 쪽 우선)로 바꾸고, 반환값에
   `"isolated_pairs"` 필드를 추가해 이 상황을 호출자가 확인할 수 있게 했다(회전 경로는
   항상 N개 소자 전부가 매 행에 있어 `isolated_pairs=0`이 보장됨을 함께 명시).

self-test(Test 12.10)에 260개 조합 전수 스윕(크래시/구조 오류 0건 확인) + 잔차 은닉 사례
재현·수정 확인 + 격리 사례가 `isolated_pairs`로 정직하게 드러남을 보이는 회귀 + 회전
경로는 항상 `isolated_pairs=0`임을 확인하는 회귀 전부 추가. 전체 self-test
(`stick_diagram.py`/`sizing_recipe.py`) exit 0 재확인.

**정직하게 남긴 한계**: `isolated_pairs`를 1순위 정렬 기준으로 넣어도, `n_rows` 자체가
격리를 구조적으로 강제하는 경우(모든 행 길이가 1일 수밖에 없는 경우)는 어떤 phase를
골라도 피할 수 없다 — 이건 탐색 알고리즘의 결함이 아니라 그 `n_rows` 값 자체가 주어진
finger 총량 대비 물리적으로 무리한 요구라는 신호로 해석해야 한다. 이 사실 자체를
docstring/문서에 명시했다.

**교훈**: "지표가 0이다"를 곧이곧대로 "완벽하다"로 믿지 말고, 그 지표가 측정하지 못하는
실패 양상이 따로 있는지 스스로 의심하는 습관이 필요하다 — §15(swap 못 찾음)에 이어
§17(격리를 못 잡음)까지, 이 함수의 잔차 계산 관련 결함은 전부 사용자가 "실제로 스윕해서
확인해보라"고 요구한 뒤에야 발견됐다. 통과하는 self-test/낮은 잔차 수치를 봤다고 그
자체로 안심하지 말고, "이 지표가 놓칠 수 있는 실패가 뭘까"를 스스로 먼저 물었어야 하는
패턴이 §14~§17에 걸쳐 반복됐다 — 다음에 유사한 objective(잔차, 점수 등) 기반 탐색
함수를 만들 때는 처음부터 "이 objective가 완전히 놓치는 실패 사례가 있는가"를 코드
작성과 함께 점검할 것.

## 18. `INTERDIGITATION_PATTERNS` 표 hub-leaf 유효성 전수 스윕 + 외부 문헌 조사 —
"무효"의 의미 정정 (사용자 요청, 완료)

§17 직후 사용자가 "n_rows=1인 경우는 interdigitate_layout()가 되는 것 아니냐"고 질문 — 실측
비교 결과 다름을 확인했다: `interdigitate_layout()`의 round-robin 경로(`base=None`)는
`ABAB...`(완전 1:1 교대)를 내는데 `_hubleaf_sequence_node_path()`로 검증하니 **무효**
(hub-leaf 구조상 완전 교대는 그래프상 불가능, §2.5.6에서 이미 확립된 사실). 반면
`common_centroid_layout(transistors, n_rows=1)`은 `build_graph()`+`hierholzer()`로
실제 유효한 `ABBA`형 블록을 계산한다 — 같은 함수가 아니다.

이어서 사용자가 "interdigitate_layout도 패턴이 있잖아(`base=...`), 그건 오일러 trail이 되는
것 아니냐"고 재질문 — `base="AB"`만 repeat 1~3에서 우연히 유효하고 repeat=4
(`ABABBABA`)와 `base="ABA"`는 무효임을 실측 확인. 사용자가 "이것도 n-way로 확장해서
검증해봐"라고 요구해 `INTERDIGITATION_PATTERNS`의 **모든** (base,repeat) 32개 조합을
`_hubleaf_sequence_node_path()`로 전수 검증했다.

**결과**: 32개 중 **7개만 유효**(`base="A"`(1-소자, 자명) 4개 + `base="AB"`의
repeat=1,2,3). `ABC`/`ABCD`(3~4소자, 전체 repeat)와 `ABA`/`ABABA`/`AABA`/`AABAA`
(2소자, 전체 repeat)는 **전부 무효** — 3개 이상의 leaf가 있으면 서로 다른 소자로 hub를
안 거치고 바로 전환하는 구조가 그래프상 항상 불가능하기 때문(§16의 `ABCCBA` 2D 패턴
불가능 발견과 같은 근본 원인).

**외부 문헌 조사(사용자 요청)**: 이 결과를 "이 표의 3소자 이상 패턴은 못 쓴다"로 오해할
위험이 있어 WebSearch로 실제 업계 관행을 조사했다. [AnalogHub의 "Matching patterns in
layout"](https://analoghub.ie/category/Layout/article/layoutMatchingPatterns)은
8A-4B-4C류 다중소자 interdigitation을 실제 예시로 제시하고, current mirror layout
문헌들은 이런 다중소자 패턴을 **crossover routing**(열 사이를 metal+via로 건너뛰어
연결하는 배선)으로 구현하는 걸 표준 기법으로 다룬다. 즉:

- 이 codebase의 hub-leaf 검증(`_hubleaf_sequence_node_path()`)이 확인하는 건 **"crossover
  없이 단일 연속 diffusion(1개 metal layer) 하나로 이어지는가"**라는 좁은 질문이다.
- 표의 3소자 이상 패턴이 "무효"인 건 이 좁은 질문에서만 그렇다 — crossover(추가 배선)를
  감수하면 실무에서 실제로 쓰이는 정당한 패턴이다.
- `INTERDIGITATION_PATTERNS`는 hub-leaf 전용 표가 아니라 **범용 layout matching
  패턴표**이고, 이 codebase의 stick-diagram 파이프라인이 처음부터 "crossover 없는 단일
  연속 diffusion" 전제로 설계된 것일 뿐이다.

**반영**: `interdigitate_layout()` docstring에 이 구분(무효=crossover 필요, 실무 사용 불가가
아님)을 명시적으로 추가하고, hub-leaf crossover-free 배치가 필요하면
`common_centroid_layout(transistors, n_rows=1)`을 쓰라고 안내. self-test(Test
12.11)에 32개 조합 전수 스윕 + 예상 유효/무효 집합과 정확히 일치하는지 확인하는 회귀
추가(표가 나중에 바뀌면 이 회귀가 잡아낸다). function-selection-map.md/consistency-map.md
동기화.

**교훈**: "무효"라는 한 단어짜리 판정 결과를 볼 때 "이 특정 검증 기준에서 무효"인지
"실무에서 못 쓴다"인지 스스로 구분하지 않으면 오해를 낳는다 — 이번엔 사용자가 직접
외부 문헌 조사를 요구한 덕분에 전자(좁은 기준에서만 무효)임이 밝혀졌다. 코드 내부
검증만으로 결론을 내리지 않고 실제 업계 관행까지 대조하는 것이, 자체 구축한 모델(이
경우 hub-leaf 단일 diffusion 모델)의 한계와 실제 물리적 가능성을 혼동하지 않는 데
필요했다 — §13~§17이 전부 "코드로 검증"이었다면 §18은 처음으로 "코드 밖(업계 표준)과
대조"한 사례다.

## 19. `find_min_crossover_layout()` 신설 — 최소 crossover routing 배치 계산 (사용자
요청, 완료)

§18에서 "무효"가 실무 사용 불가가 아니라 crossover 필요를 뜻한다는 걸 확인한 직후,
사용자가 "그럼 이 함수에서 최소한의 crossover routing이 생기는 조합을 찾아 결과로 내는
것으로 만들어달라, crossover 개수도 표시, 우선순위는 crossover가 안 생기는 연속 diffusion
조합"이라고 요구했다.

**적용한 원리**: 이건 그래프 이론에 이미 알려진 정리(route inspection/Chinese postman
문제의 T-join 표준 결과)로 정확히 풀리는 문제다 — 연결된 그래프에서 홀수차수 노드가
2m개면, 전체 edge를 **정확히 m개의 trail**로 쪼갤 수 있고 그보다 적은 개수로는 불가능
하다(m<=1이면 기존 `check_euler_condition()`이 이미 처리하는 circuit/path 경우 — 0
crossover). m개의 trail을 하나로 이어붙이려면 **m-1번의 crossover**가 필요하다.

**구현 방법**: 홀수차수 노드 2m개를 2개씩 짝지어 m개의 가상 edge(실제 배선이 아니라
계산상 도구)를 그래프에 추가하면 모든 노드가 짝수차수가 돼(짝짓기 방법과 무관하게 이
성질은 항상 성립) 전체가 하나의 오일러 회로가 된다. 기존 `hierholzer()`로 이 회로
전체를 계산한 뒤, 가상 edge가 나온 지점마다 실제로 끊어서(가상 edge 자체는 버림) m개의
진짜 trail로 분해한다.

**검증 순서(코드부터 짜지 않고 프로토타입으로 먼저 확인)**:
1. ABC(3소자 1개씩, 4개 홀수차수 노드 — 3 leaf + hub, m=2) → 프로토타입 실행 결과
   `[C,A]`+`[B]`, crossover=1 확인.
2. ABCD(4소자 1개씩, 4개 홀수 leaf, hub는 짝수라 4개, m=2) → crossover=1.
3. 6소자 1개씩(6개 홀수 leaf, m=3) → crossover=2.
4. 이미 가능한 경우(A=2,B=2) → crossover=0(회귀 없음 확인).
모두 이론값과 정확히 일치함을 확인한 뒤 실제 `stick_diagram.py`에
`find_min_crossover_layout()`으로 구현.

**추가 검증**: 균등 개수(N=1~6, count=1~5) 30개 조합 + 무작위 불균등 개수(N=2~6, 15회씩)
75개 조합, 총 105개 조합을 별도 스크립트로 전수 스윕 — `crossover_count ==
max(0, odd_nodes//2 - 1)` 공식과 전부 정확히 일치, 소자 총 개수가 항상 보존됨, 각
segment가 `_hubleaf_sequence_node_path()`로 독립적으로 유효한 walk임을 확인. 실패 0건.

self-test(Test 12.12)에 위 4가지 핵심 사례 + segment 유효성 재확인 + 입력 검증(빈 리스트,
hub 불일치) 추가. 전체 self-test(`stick_diagram.py`/`sizing_recipe.py`) exit 0 확인.
function-selection-map.md 반영.

**교훈**: 문제가 이미 알려진 그래프 이론 정리에 정확히 대응된다는 걸 알아보면, 손으로
휴리스틱을 고안하지 말고 그 정리를 그대로 구현하는 게 가장 안전하고 확실하다(§14~§17의
휴리스틱 탐색과 대조적으로, 이번엔 "증명된 최적"을 얻을 수 있었다 — 짝짓기 방법과
무관하게 m 값 자체는 항상 같다는 정리 덕분에). 다만 이론을 안다고 바로 코드에 반영하지
않고, 작은 프로토타입으로 여러 구체적 사례(3,4,6소자)에서 실제로 공식이 들어맞는지
먼저 확인한 뒤에야 파일에 반영한 것 — 이 세션 내내 반복된 "실행해서 확인 후 반영" 원칙이
여기서도 그대로 적용됐다.

## 20. `common_centroid_layout()` 회전 경로에 `find_min_crossover_layout()` 통합 —
"진짜 불가능" 사례 전부 해결 (사용자 요청, 완료)

§19 직후 사용자가 "common_centroid도 이 최소 crossover routing 조건을 추가하면 어떻게
되지?"라고 질문했다. 코드부터 바로 짜지 않고 프로토타입으로 먼저 확인: §17에서 "진짜
불가능"으로 확정했던 N=3,count=3 사례를 `find_min_crossover_layout()`으로 만든
row_0(crossover=1개, segments=`[B]`+`[C,A]`)에 기존 회전(이름/leaf relabeling)을 그대로
적용해봤다.

**핵심 발견**: 회전 3회를 다 돌려도 **잔차가 여전히 정확히 0**이었다(`row0=[B,C,A],
row1=[C,A,B], row2=[A,B,C]`, 열평균 전부 일치). 이건 우연이 아니라 필연이다 — 회전
증명("N개 행 전체에서 모든 소자가 모든 열을 정확히 1번씩 방문한다")은 row_0가 **어떻게
계산됐는지와 무관하게** 성립한다(그래프로 직접 계산했든, crossover를 섞어 만들었든,
순수 relabeling이라는 사실 하나로 증명이 성립하기 때문). §17에서 "진짜 불가능"으로
확정했던 10개 조합(N=3~6, count가 N에 매우 가까운 경우) 전부를 재확인한 결과 crossover
1~2개로 전부 해결됨을 실측 확인 후 사용자 승인을 받아 실제 통합했다.

**구현**: `_common_centroid_nway_exact()`의 우선순위를 (1) 균등 분배로 0-crossover 시도
→ (2) `_fix_block_parity()`(§16) 홀짝 보정으로 0-crossover 재시도 → (3) 그래도 안 되면
`find_min_crossover_layout()`(§19)으로 최소 crossover 배치 폴백 — 순으로 재구성했다.
(3)까지 왔다는 건 홀수차수 노드가 4개 이상이라는 뜻이고, `find_min_crossover_layout()`은
그래프 이론(T-join)상 이런 경우 항상 성공하므로, **결과적으로 `count>=N`이기만 하면 이
경로는 이제 절대 실패하지 않는다** — §16/§17에서 발견했던 "진짜 불가능" 카테고리 자체가
소멸했다.

반환 스키마도 확장: 각 행에 `"segments"`(crossover 경계로 나뉜 조각들, 독립적으로 각각
유효한 walk)와 `"crossover_after"`(그 인덱스 바로 다음에 crossover routing 접합이
필요하다는 표시)를 추가하고, 최상위에 `"crossover_count"`를 추가했다. 탐색 경로
(`method="search"`)에도 스키마 일관성을 위해 `crossover_count=0`/`segments`=행 전체
1개짜리를 채웠다 — 단, 탐색 경로 자체엔 아직 crossover 폴백을 붙이지 않았다(부분 개선,
아래 후속 과제).

**검증**: self-test(Test 12.9b)에 §17의 "진짜 불가능" 10개 조합 전부 재확인(crossover_
count>0, residual=0.0, 각 segment `_hubleaf_sequence_node_path()`로 독립 유효성 확인)
+ 기존 0-crossover 성공 케이스(N=2,count=4) 무회귀 확인 추가. 별도 스크립트로 N=2~8 ×
count=N~N+14(105개 조합) 전수 스윕 — 실패 0건. 전체 self-test(`stick_diagram.py`/
`sizing_recipe.py`) exit 0 재확인. function-selection-map.md 반영.

**후속 과제(이번 배치 범위 밖, 기록만)**: 탐색 경로(`_common_centroid_nway_search()`)는
소자 개수가 다르거나 `n_rows!=N`일 때 쓰이는데, 여기서도 `_repair_row_parity()`가 실패한
후보를 그냥 버리는 대신 `find_min_crossover_layout()`으로 crossover 폴백을 시도하면
Test 12.10에서 관찰됐던 고잔차/`isolated_pairs>0` 사례 일부를 추가로 구제할 수 있을지도
모른다 — 다만 그 경로는 애초에 잔차 0을 증명하지 못하는 휴리스틱이라, crossover까지
더하면 무엇을 최적화 기준으로 삼을지(잔차 vs crossover 개수 트레이드오프)를 먼저
정해야 해서 이번 요청 범위 밖으로 남겼다.

**교훈**: "A에서 발견한 걸 B에도 적용하면 어떻게 되나"라는 질문을 받으면, 두 메커니즘이
독립적으로 호환되는지 가정하지 말고 실제로 프로토타입 코드를 돌려 확인한 뒤 통합할 것 —
이번엔 "회전 증명이 row_0의 계산 방식에 의존하지 않는다"는 성질을 직접 실행으로 확인했기
때문에 안심하고 기존 self-test(Test 12.9의 "진짜 불가능" 목록)를 뒤집는 변경을 할 수
있었다. 가정만으로 이런 큰 변경을 했다면 근거 없이 기존 동작을 바꾸는 셈이었을 것이다.

## 21. 탐색 경로(`method="search"`)에도 crossover 폴백 통합 (사용자 요청, 완료)

§20(회전 경로 통합) 직후 사용자가 "탐색 경로에도 crossover 폴백 추가해줘"라고 요구했다.

**구현**: `_build_rows_from_shares_with_crossover()`를 신설 — 행 하나가 `_repair_row_
parity()`(인접 행끼리 소자 1개씩 재배정, 물리적 비용 없음)로도 0-crossover가 안 되면
`find_min_crossover_layout()`(§19)으로 최소 crossover 배치로 폴백한다. 기존
`_build_rows_from_shares()`(0-crossover 전용, 실패 시 `None`)는 그대로 두고, `None`이면
crossover-허용판으로 넘어가는 구조를 유지했다 — 우선순위(0-crossover 먼저, 진짜 안 될
때만 crossover)를 그대로 보존하기 위해서다.

`_common_centroid_nway_search()`의 candidate 정렬 기준을 `(isolated_pairs, residual)`
에서 **`(crossover_count, isolated_pairs, residual)`**로 확장했다(사전식 정렬 — crossover
가 하나라도 더 필요한 후보는 잔차/격리가 아무리 좋아도 항상 후순위). `find_min_crossover_
layout()`이 그래프 이론상 항상 성공하므로, 결과적으로 **탐색 경로도 이제 사실상 실패하지
않는다**(모든 phase가 crossover까지 동원해도 안 되는 경우만 `ValueError` — 실전에서
관측되지 않음).

**self-test 수정 중 발견한 부수 문제**: Test 12.10(n_rows!=N 260개 조합 전수 스윕)을
그대로 재실행하니 107건이 "무효 walk"로 실패했다 — 원인을 보니 버그가 아니라 **테스트
자체가 옛 스키마를 가정**하고 있었다: crossover가 있으면 행의 flat `transistor_
sequence`는 더 이상 단일 연속 walk가 아닌 게 정상인데, 테스트가 여전히 flat 시퀀스
전체를 `_hubleaf_sequence_node_path()`로 검증하고 있었다. 검증 로직을 `row["segments"]`
의 각 조각을 독립적으로 확인하는 방식으로 수정하니(§19/§20에서 이미 쓴 패턴과 동일)
전부 통과 — 크래시 0건, 구조 오류 0건, ValueError 0건, 성공한 조합의 crossover 총합=926
(폴백이 실제로 광범위하게 쓰였음을 확인).

추가로 별도 스크립트로 N=2~6 무작위 100개 조합(임의 개수 조합 + 임의 `n_rows`) 전수
스윕 — ValueError 0건, 실패 0건. 전체 self-test(`stick_diagram.py`/`sizing_recipe.py`)
exit 0 재확인. function-selection-map.md 반영.

**교훈**: 한 경로(회전)에 적용한 변경을 다른 경로(탐색)에 그대로 옮길 때, 그 경로의 자체
검증 테스트가 옛 스키마(단일 flat walk라는 암묵적 가정)에 의존하고 있을 수 있다는 걸
뒤늦게 발견했다 — 새 기능을 기존 코드에 통합할 때는 그 코드가 의존하는 다른 곳(이번엔
같은 파일의 self-test)의 암묵적 가정까지 함께 점검해야 한다. §14~§21에 걸쳐 이
`common_centroid_layout()` 하나를 반복적으로 사용자가 재검증 요구 → 발견 → 수정
→ 재검증 요구의 사이클로 다듬어왔다는 것 자체가, 처음부터 "다 됐다"고 여기지 않고
계속 파고드는 태도의 가치를 보여준다.

## 22. `common_centroid_layout()` 완전 제거 — `common_centroid_layout()`로 흡수 통합 (사용자 요청, 완료)

§21까지 `common_centroid_layout()`를 N-소자·임의 row·crossover-tolerant로 완전히
일반화한 뒤, 사용자가 "common_centroid_layout은 이제 필요없지 않아?"라고 물었다.

**검증 없이 답하지 않고 직접 실행 비교**: `common_centroid_layout()`에는 두 경로가
있었다 — `pattern_key=None`(회전/그래프 기반, N=2 대칭 전용)과 `pattern_key=...`
(`COMMON_CENTROID_PATTERNS` 문헌 표 기반, 1:1이 아닌 비율도 지원). 실측 비교 결과
`pattern_key=None` 경로는 nway와 **완전히 동일한 출력**(중복 확인)이었지만,
`pattern_key=...` 경로는 **중복이 아니었다** — 2:1 비율(예: `AAB`/`BAA`) 케이스에서 nway
탐색 경로는 잔차 0.75까지 나오는데, 표 경로는 잔차 정확히 0을 낸다. 이 비대칭을 실측으로
확인하지 않고 "겉보기에 비슷하니 둘 다 필요 없다"고 답했다면 표 경로의 진짜 이점(문헌
검증된 비율 패턴의 잔차-0 보장)을 놓쳤을 것이다.

이 발견을 바탕으로 AskUserQuestion("중복 경로만 제거 vs 둘 다 유지")을 제시했으나
사용자가 거부하고 명확화를 요구 — 이어서 "기능을 흡수해서 common_centroid_layout만
남기면 안 되나?"로 최종 방향이 확정됐다: 표 경로의 가치까지 nway 안으로 흡수하고 옛
함수는 완전히 삭제.

**구현**: `_try_pattern_table_match(names, leafs, hub_net, counts)` 신설 — N=2 전용,
`COMMON_CENTROID_PATTERNS`의 2-소자 항목만(3-소자 `ABCCBA`류는 명시적으로 skip) 개수에
맞는 repeat를 찾아 두 가지 이름 순서로 각각 `_common_centroid_from_pattern_table()`
(기존 헬퍼, 그대로 유지)을 시도, 성공하면 반환, 전부 실패(`ValueError`)하면 `None`
(호출자가 탐색 경로로 폴백). `common_centroid_layout()`의 dispatch를 3단계로
재구성: ①`target_rows==n and all_equal` → 회전 정확 경로(`method="rotation_exact"`,
잔차 0 보장) ②`n==2 and target_rows==2` → `_try_pattern_table_match()`
(`method="pattern_table"`, 실패 시 ③으로 폴백) ③그 외 전부 → 탐색 경로
(`method="search"`). `common_centroid_layout()`과 `_common_centroid_from_graph()`
(2-소자 전용 그래프 경로, `_common_centroid_nway_exact()`에 이미 superseded된 상태였음)
둘 다 파일에서 완전히 삭제 — 이제 common-centroid 배치 API는 `common_centroid_layout_
nway()` 하나뿐이다.

self-test 재작성: Test 11을 `_common_centroid_from_pattern_table()` 직접 호출로
재작성(ABBA/BAAB 유효성, ABA/BAB 거부, ABCCBA 3-소자 거부 확인), Test 12를 `Transistor`
리스트 기반 `common_centroid_layout()` 호출(9:9 홀수 케이스,
`method=="rotation_exact"` 단언)로 재작성, Test 12.5를 표 경로 vs nway 비교 + 2:1
비율 케이스에서 `method="pattern_table"`/잔차 0.0 확인(구 탐색 경로의 잘못된 잔차 0.75와
대조)으로 재작성. branch_symmetric 테스트 구간의 옛 `common_centroid_layout()` 호출
2곳도 `common_centroid_layout([Transistor(...), Transistor(...)])` +
`rows[i]["transistor_sequence"].count(name)` 패턴으로 재작성. 전체 self-test
(`stick_diagram.py`/`sizing_recipe.py`) exit 0 재확인. `function-selection-map.md`의
옛 `common_centroid_layout()` 단독 행을 삭제하고 nway 행에 3단계 dispatch 설명으로
통합, `interdigitate_layout`/`run_topology_pipeline` 행의 잔여 참조도 `common_centroid_layout_
nway()`로 수정. `consistency-map.md`에 37차 항목 추가.

**교훈**: "이 함수 이제 필요없지 않아?"라는 질문에 코드를 안 열어보고 겉보기 유사성만으로
"네, 중복이니 삭제"라고 답했다면 표 경로의 잔차-0 이점을 잃을 뻔했다 — 표면적으로 비슷해
보이는 두 함수도 실측 비교 전에는 "중복"이라 단정하지 말 것(이 세션 전체의 "근거 없이
가정하지 말 것" 원칙과 동일선상). 또한 사용자가 AskUserQuestion의 선택지들을 거부하고
명확화를 요구했을 때, 그건 제시한 선택지 자체가 사용자가 원하는 답(완전 흡수)을 포함하지
않았다는 신호였다 — 선택지 설계가 실제 요구를 못 담으면 사용자는 고르지 않고 재질문한다.

## 23. `interdigitate_layout()`를 `common_centroid_layout()`와 동급으로 재설계 (사용자 요청, 완료)

§22 직후 사용자가 naming 일관성을 지적했다: "common_centroid는 layout이라는 용어가
붙었는데 interdigitate_layout는 없어 — 일관성이 떨어진다고 생각하는데 어떻게 생각해?" 처음엔
"반환값 성격이 달라서(전자는 검증된 완성 layout, 후자는 순수 패턴 생성기)"라고 답했으나,
사용자가 "interdigitate_layout도 이번에 기능을 확장했잖아. 검증 기능도 있어"라고 반박 — 코드를
다시 열어 확인한 결과 실제로는 `interdigitate_layout()`가 결과를 내부에서 검증하지 않는다는
게 맞았다(docstring에 "이 경로는 결과가 1개 layer로 실현 가능한지 검증하지 않는다"고
명시돼 있었음, 재확인으로 뒷받침). 사용자가 다시 "interdigitate_layout도 fallback이 있잖아"라고
묻자 함수 본문(`if base is not None: ... return; ...round-robin...; return`)을 직접
읽어 **자동 fallback이 없다**(호출자가 선택하는 두 갈래일 뿐, 실패 시 자동 재시도 없음)를
확인·보고했다. 마지막으로 사용자가 "아까 검증했던 것은 어떻게 된거야, crossover routing을
써서 fail을 없애라고 한 것"이라고 묻자, `find_min_crossover_layout()` 도입 요청(§19)이
실제로는 `common_centroid_layout()`에만 통합됐고(§20/§21) `interdigitate_layout()`에는
적용된 적이 없었음을 재확인 — 이 함수는 self-test 외 어디서도 호출되지 않는 유틸이었고,
docstring도 "hub-leaf 무효면 `common_centroid_layout(n_rows=1)`을 대신 쓸 것"이라고
한 단계 위로 리다이렉트만 해뒀을 뿐 자체적으로 개선되지는 않았었다.

사용자의 최종 요청: "interdigitate_layout를 common_centroid_layout과 동급으로 만들어. 쓸데없는
주석은 지워버리고, crossover없이 할 수있는 패턴을 최적패턴으로 return하되 필요하다면
최소한의 crossover routing이 되는 패턴을 common_centroid_layout과 동일한 형식으로
return하고 검증하는 로직도 추가해."

**구현**: `interdigitate_layout(transistors, base=None, repeat=None) -> dict`로 시그니처를
`common_centroid_layout()`와 동일한 스타일(`Transistor` 리스트 입력)로 바꾸고,
반환도 동일 스키마(`rows`/`method`/`crossover_count`/`residual`/`isolated_pairs`)로
통일했다. `_try_interdigitation_table_match()`(`_try_pattern_table_match()`와 대칭
구조) 신설 — `repeat`을 생략하면 표 전체를 자동 탐색해 소자의 실제 `n_fingers`와 정확히
맞고 hub-leaf로도 유효한 항목을 찾는다(`method="pattern_table"`). 안 맞으면(또는 `base`
자체가 없으면) `common_centroid_layout()`의 탐색 경로가 이미 쓰던 헬퍼
(`_repair_row_parity()`/`_build_rows_from_shares()`/`_build_rows_from_shares_with_
crossover()`)를 새 코드 추가 없이 그대로 재사용해 단일 행을 직접 구성·검증하고, 필요하면
crossover 폴백까지 쓴다(`method="search"`). 부수 효과로 옛 "base 없이는 정확히 2소자만"
제약도 자연히 사라졌다 — 재사용한 헬퍼가 애초에 임의 개수(N>=1) 소자를 지원하는 Counter
기반이기 때문이다. 실측 확인: base="ABC"(3소자, hub-leaf 무효로 알려진 표)와 base 없이
같은 3소자를 넣은 결과가 **문자 그대로 동일**했다 — 둘 다 같은 `Counter({M3:1,M4:1,M5:1})`
로 귀결되어 같은 crossover 폴백 경로를 타기 때문(우연이 아니라 구조적 필연임을 코드로
확인).

self-test 재작성: Test 12.6을 새 스키마로 전면 재작성, Test 12.11(32개 base×repeat 전수
스윕)을 `_hubleaf_sequence_node_path()` 외부 호출 방식에서 `interdigitate_layout()` 직접 호출로
재작성 — 7개는 `method="pattern_table"`, 나머지 25개는 `method="search"`로 자동 폴백해
**32개 전부 예외 없이 성공**함을 확인(이전엔 유효성 판정만 하고 실제 배치는 안 만들어줬다).
`len(transistors)<1`로 최소 조건을 완화(옛 `len<2`였으면 base="A"의 1-소자 자명 케이스가
깨짐 — 실행해보고서야 발견, 미리 예측하지 않았다). 전체 self-test(`stick_diagram.py`/
`sizing_recipe.py`) exit 0 재확인. `function-selection-map.md`/`stick-diagram-euler-
layout.md`(§2.5.5/§2.7.2/§2.7.3/Test 요약)의 옛 시그니처·"검증은 호출자 책임" 서술을
전부 갱신, `consistency-map.md`에 38차 항목 추가.

**교훈**: naming 비일관성 지적이 스타일 문제가 아니라 실제 기능 격차(한쪽만 crossover
폴백+내부 검증을 갖춤)를 가리키는 신호였다. 더 중요하게는, 사용자가 "fallback 있잖아"/
"crossover로 fail 없애라고 했잖아"라고 되물었을 때 바로 동의하거나 방어하지 않고 매번
코드를 다시 열어 확인했다 — 첫 반박("검증 기능도 있어")은 사실이 아니었고, 두 번째
질문("crossover로 fail 없애라 한 것")은 사실이었다(다만 그 요청이 적용된 범위가
`interdigitate_layout()`가 아니라 `common_centroid_layout()`였을 뿐). 사용자의 기억과
코드의 실제 상태가 부분적으로만 일치할 수 있다는 것, 그리고 그 어긋남을 찾아내려면
"그렇습니다"도 "아닙니다"도 아니라 매번 직접 읽고 답해야 한다는 것을 재확인한 사례다.

## 24. 함수 naming 비일관성 정리 1건 — `verify_*`를 `check_*`로 통일 (사용자 요청, 완료)

§23 직후 사용자가 "이제 함수 이름을 살펴보자. 일관성이 없는 이름들을 list up해봐"라고
요청했다. `stick_diagram.py`의 함수 정의 60개 전체를 훑어 6가지 비일관성을 정리해 보고했다:

1. **`detect_`/`find_`**: `find_matching_candidates()` vs `find_hub_merge_candidates()` —
   둘 다 "확정 아닌 구조적 후보만 찾는다"는 동일한 역할인데 동사가 다르다.
2. **`check_`/`verify_`(+반환 타입 흔들림)**: `check_box_shape`/`check_finger_width_
   compatibility`/`check_stick_diagram_coverage`/`check_multi_leaf_hub_parity` vs
   `verify_mirror_symmetry`/`verify_symmetry_dispositions`/`verify_walk_sequence` — "이미
   만들어진 구조가 어떤 속성을 만족하는지 판정"이라는 동일 패턴에 두 동사가 근거 없이
   섞여 있고, 반환 타입도 `BoxShapeVerdict`/`list`/`dict`/`WalkVerdict`/`bool`로 같은
   동사 계열 안에서도 제각각이었다.
3. **`audit_`**: `audit_row_split`/`run_full_circuit_audit` — 여러 하위 체크를 묶은 종합
   판정이라 "audit"은 말이 되지만, 결과 dataclass가 `AuditResult`로 2번의 `*Verdict`들과
   또 다른 suffix.
4. **`build_`/`generate_`**: `build_graph`/`build_mirror_symmetric_pattern`/`_build_rows_
   from_shares*` vs `build_stick_diagram` — 전부 "입력을 받아 새 구조를 구성해 반환"인데
   `build_stick_diagram`만 다른 동사.
5. **동사 없음**: `check_euler_condition`/`hierholzer` — 알고리즘/개념 이름 그대로(명사), 나머지
   전부가 동사로 시작하는 것과 다름(의도적 예외로 볼 여지는 있음).
6. **`interdigitate_layout()` vs `common_centroid_layout()`**: §23으로 기능은 동급이 됐지만
   이름 구조 자체는 여전히 비대칭(맨 동사 vs 동사+명사+`_layout`+`_nway`).

사용자가 2번(`check_`/`verify_` 혼용)부터 정리하도록 지시했다.

**구현**: 순수 개명(동작/시그니처/반환 타입은 전혀 안 건드림 — 반환 타입 통일은 훨씬 큰
별도 작업이라 이번 스코프에서 의도적으로 제외) — 이미 다수였던 `check_` 계열로 통일:
`verify_mirror_symmetry`→`check_mirror_symmetry`, `verify_symmetry_dispositions`→
`check_symmetry_dispositions`, `verify_walk_sequence`→`check_walk_sequence`.
`stick_diagram.py` 전체(정의+내부 호출+self-test 16곳)와 이 함수들을 참조하는 모든
operational 문서(`function-selection-map.md`, `SKILL.md`, `stick-diagram-euler-
layout.md`, `design-report-spec.md`, `skill-validation-prompt.md`, 이 프로젝트의
`analog-topology-json-library.design.md`, `library/_TEMPLATE.topology.json`,
`library/current_reuse_telescopic_ota.topology.json`)을 함께 개명했다. 이 문서(gap-
findings.md)와 `consistency-map.md`의 **날짜/번호가 박힌 과거 항목(§8/§17/§18, 17~25차)은
옛 이름 그대로 보존**했다 — 그 항목들의 주제 자체가 "그 시점에 이 이름으로 만들어졌다"는
API 이력이라, 최신 이름으로 바꿔 쓰면 실제 개명 사실이 사라진다(반면 design-report-
spec.md/stick-diagram-euler-layout.md의 PRE-FLIGHT 사고 서술은 이름이 아니라 프로세스
실수가 주제라 최신 이름으로 갱신해도 정보 손실이 없어 그대로 갱신했다).

self-test: 개명 후 `stick_diagram.py`/`sizing_recipe.py` 전체 self-test exit 0 재확인.

**교훈**: naming 정리 요청이라도 전부 같은 방식(찾아서 다 바꾸기)으로 처리하면 안 된다 —
"이 이름 언급이 API 역사 그 자체를 기록하는 문서"인지 "이름이 우연히 등장하는 인시던트
서술"인지를 파일(그리고 파일 안 문단)별로 구분해서 적용해야, 정리하면서 오히려 과거
기록의 정확성을 해치는 실수를 피할 수 있다.

## 25. 함수 naming 비일관성 정리 나머지 5건 — `stick_diagram.py` API 표면 전체 재정리 (사용자 요청, 완료)

§24 직후 사용자가 "반환타입은 다른 함수 모두 바꾸고 진행하자. 나머지 함수 비일관성도
순서대로 정리해"라고 요청했다. §24에서 보고한 나머지 항목을 순서대로 처리:

1. **`check_*` 반환 타입 통일 완결**: `check_finger_width_compatibility`(list),
   `check_multi_leaf_hub_parity`(dict), `check_stick_diagram_coverage`(dict),
   `check_symmetry_dispositions`(dict), `check_mirror_symmetry`(bool)를 각각
   `FingerWidthVerdict`/`MultiLeafHubParityVerdict`/`CoverageVerdict`/
   `SymmetryDispositionsVerdict`/`MirrorSymmetryVerdict` dataclass로 감쌌고,
   기존 `WalkVerdict.valid`도 `.ok`로 개명해 전 `check_*` 함수가 `.ok`로 통일된
   pass/fail 접근을 갖도록 만들었다. 이 작업은 순수 rename이 아니라 실제 구조
   변경이라 self-test 16곳 + `save_instance_json()`의 `coverage` 직렬화 지점을
   먼저 grep으로 전부 찾아 접근 패턴(`["ok"]`형)을 확인한 뒤 하나씩 attribute
   access로 고치고 즉시 self-test로 확인하는 순서로 진행했다 — `save_instance_
   json()`이 이미 `box_shape`/`audit_row_split`(기존 dataclass)을 수동으로 dict로
   평탄화(flatten)해서 JSON 직렬화하던 기존 패턴을 그대로 재사용했을 뿐, 새 직렬화
   방식을 도입하지는 않았다. 부수 발견: `stick-diagram-euler-layout.md` §8
   docstring에 `_nway` 개명 후에도 갱신 안 된 `common_centroid_layout` 잔여
   참조 3곳이 남아있던 걸 이번에 함께 바로잡았다.
2. **`detect_matching_candidates()` → `find_matching_candidates()`**: `find_`가
   이미 4개 함수의 다수 관례였으므로 그쪽으로 순수 rename.
3. **`AuditResult` vs `*Verdict`**: 검토 결과 실제로는 비일관성이 아니었다 —
   `AuditResult`는 두 `audit_*` 함수가 이미 공유하는, `checks` 리스트+`.add()`
   축적 메서드를 가진 **구조적으로 다른** 타입(여러 sub-check을 모으는 용도)이라
   "`*Verdict`=단일 속성 판정, `*Result`=종합 판정"이라는 2단 관례로 문서화만
   하고 코드는 그대로 뒀다.
4. **`generate_stick_diagram()` → `build_stick_diagram()`**: `build_graph`/
   `build_mirror_symmetric_pattern`/`_build_rows_from_shares*`와 같은 패턴인데
   이 함수만 다른 동사였다 — 순수 rename.
5. **`interdigitate()` → `interdigitate_layout()`, `common_centroid_layout_nway()`
   → `common_centroid_layout()`**: §23으로 기능은 동급이 됐지만 이름 구조는 여전히
   비대칭이었다. `common_centroid_layout()`이 완전히 제거된 지금(§22) `_nway`
   suffix는 더 이상 다른 함수와 구분할 필요가 없어 vestigial이었으므로 제거하고,
   `interdigitate()`에 `_layout` suffix를 붙여 대칭을 맞췄다. 단순 문자열 치환은
   "interdigitated"/"interdigitation" 같은 영어 단어를 오염시킬 위험이 있어(실제로
   grep으로 이 위험을 사전에 확인함), 단어 경계를 명시한 치환으로 안전하게 처리했다.
6. **`euler_condition()` → `check_euler_condition()`, `hierholzer()`는 유지**:
   `euler_condition(g) -> EulerVerdict`는 1번에서 통일한 `check_*`→`*Verdict`
   패턴과 정확히 같은 모양이라 그 계열로 편입(rename). `hierholzer()`는 그래프
   이론의 표준 알고리즘 이름 그대로라 의도적으로 유지 — 도메인 전문가에게 이미
   통하는 표준 용어를 억지로 동사형으로 바꾸면 오히려 인식 가능성을 잃는다고
   판단했다.

각 항목마다 `stick_diagram.py`(정의+내부 호출+self-test)와 모든 operational 참조
문서를 함께 갱신하고, 매번 `stick_diagram.py`/`sizing_recipe.py` self-test exit 0을
재확인하며 하나씩 순서대로 진행했다 — 한 번에 다 바꾸고 마지막에 몰아서 디버깅하지
않았다.

**교훈**: "반환 타입까지 바꾸자"는 지시는 이름만 바꾸는 것보다 훨씬 큰 blast
radius(모든 호출부의 접근 패턴 변경)를 가진 작업이었지만, 미리 전 호출부를 grep으로
찾아 정확한 접근 패턴을 확인한 뒤 함수 하나씩 고치고 즉시 self-test로 검증하는 방식
으로 쪼개서 진행하니 실제로는 위험이 통제 가능했다 — 크고 모호해 보이는 지시일수록
실행 가능한 최소 단위(함수 하나, grep 확인, self-test 1회)로 쪼개는 것이 핵심이다.
동사 없는 이름(`hierholzer`)이나 구조가 다른 타입(`AuditResult`)처럼, 비일관성으로
보이는 모든 항목이 실제로 "고쳐야 할 결함"인 것은 아니다 — 도메인 표준 용어나
의도적으로 다른 구조를 반영한 이름은 그대로 유지하고 그 판단 근거를 문서화하는 것도
"정리"의 정당한 결과다.
