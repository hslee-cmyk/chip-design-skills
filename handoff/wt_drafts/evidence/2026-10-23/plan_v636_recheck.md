# 계획 v6.36 재검증 (plan/v636 `b0e7ef7c`, 부모 `ca9092e2`)

- 2026-10-23, 읽기 전용 검증 agent. 쓴 파일은 이 파일 하나다.
- 확인한 것
  - `b0e7ef7c`의 plan 전문(273·618·1532·1644행 등)
  - integ-it12 `4fc0ca1d` `authoring/spec_constraints.py` `_view`(:177-204)
  - integ-it12 `1fa7b1e5` `graph/views.py:51-81`
  - current_reuse spec

## 점수: 92 / 100 -- 새 G 0, 새 S 1

## 1. 해소 확인

| 지적 | 판정 |
|---|---|
| S-1 | 해소. 273행 괄호가 '값(V_id*) = DEC-23 (나′) 세 성분 합 …; **판정 자리만** U-108 승인 전까지 옛 문언(front 전용)'으로 좁혀졌다. 본문도 'V_id* = DEC-23 (나′) 세 성분 합(성분 (3) = −ΔV_out(ΔW)/A_dc …)'이고, '옛 ΔW = 0이면 통과와 단독식은 삭제'로 적혀 있다. grep 결과 'ΔW = 0이면 통과'가 남은 자리는 Status·273·317·618의 삭제·대체 표지 안뿐이다. |
| N-1 | 해소(618행 마지막 칸에 '**v6.36 O-118로 근거 오류**, DEC-23 (나′)', `offset_systematic`은 DE-1 (c)가 대체) |
| N-2 | 해소(U-107 (a) 스윙 창 정의 불능 → V_id* 정의 불능, (b) V_ref = V_out0이면 점검 불요 -- Status 요약) |
| N-3 | 반영. 다만 추정의 근거 문장이 코드와 다르다(2절). |
| N-4~N-6 | 해소(Status 요약과 해당 자리) |

## 2. N-3 작성자 추정 코드 확인

- **추정**: 'current_reuse의 선언 view도 모두 결정 대기라 `_declared`(`views.py:51-63`)가 씨앗을 내지 않아 지금도 기본 뷰로 떨어진다.'
- **코드 사실**
  - current_reuse의 선언 view 넷(gain, ratio 둘, parasitic_pm)은 모두 `{"pending":"MOD5"}`다. 로더 `_view`(`spec_constraints.py:179-180`)가 이를 `ViewDecl(pending)`으로 만들고, `_declared`는 pending 모드를 건너뛴다. 여기까지는 맞다.
  - 그러나 같은 회로의 view 미선언 제약에는 로더가 기본 뷰를 붙인다(`_view` :198-204 → `views.port`·`views.loop` 유도). `offset_in_sigma_mv`·`offset_sys_mv`·`noise_out_int_vrms`(transfer → port 뷰)와 `pm_ss_deg`(loop 뷰)가 그렇다.
  - 그래서 `_declared`는 씨앗을 **낸다**. `_declared(spec) or _default(model)`의 `or` 대체는 일어나지 않는다.
- **결론**
  - '씨앗을 내지 않아 기본 뷰로 떨어진다'는 사실과 다르다.
  - 다만 로더가 유도한 port 씨앗의 (excite, sense)가 `_default`와 같은 유도라 `setdefault`가 같은 키로 합친다. 그래서 '변화 0'이라는 결론은 그대로 성립한다(loop 씨앗은 변경 전후 모두 있음).
  - 문장만 '로더가 view 미선언 제약에 붙인 기본 port 뷰 씨앗이 있어 기본 키가 이미 목록에 있다'로 고치면 된다(N-1). 착수 실측으로 확인한다는 표시는 유지한다.

## 3. 새 발견

### S-1 손계산 오라클(1644행)의 'ΔW ≠ 0 손 회로 toy' 기대값이 (나′)와 맞지 않는다

- **위치**: 1644행 '계통 offset은 **ΔW ≠ 0 손 회로 toy**(… 부호 있는 V_id* = −ΔV_out / A_dc(ΔV_out = −G⁻¹·ΔI …) 손계산과 부호까지 일치 …'
- **근거**
  - (나′)에서 V_id* = 성분 (1)(V_id,seal − V_id,0) + 성분 (2)((V_ref − V_out0)/A_dc) + 성분 (3)(−ΔV_out(ΔW)/A_dc)이다(DEC-23·DE-1 (c)).
  - 같은 문단의 ΔW = 0 toy는 '값 = 성분 (1)(2) 손계산'이라 (1)(2)가 0이 아닌 toy를 전제한다.
  - 그런데 ΔW ≠ 0 toy는 V_id* 전체를 성분 (3) 단독식과 비교한다. 성분 (1)(2)가 0이 아닌 toy라면 맞는 구현이 red가 되고, (3)만 내는 옛 구현이 green이 된다(판정 뒤집힘).
- **수정 제안**: 기대값을 '(나′) 세 성분 합 손계산(성분 (3) = −ΔV_out/A_dc)'으로 바꾼다. 또는 toy 전제로 '입력 DC 선언(V_id,seal = V_id,0)·V_ref = V_out0 → 성분 (1)(2) = 0'을 단언하고 성분 (3)만 대조한다. 223행 A_dc 갈래 문장의 '계통 offset V_id* = −ΔV_out / A_dc(아래 계산)'도 'V_id*(A_dc로 나누는 성분 (2)(3))'로 맞춘다.
- **원칙 점검**: 사용자 결정 O-118 반영 정확성, 판정 가능성(red가 뒤집히지 않음), 정의 자리 하나 → 맞음

### N (참고)

- **N-1** 2절. 1532행 '(d)' 괄호의 current_reuse 문장을 코드 사실(로더 기본 port 씨앗 존재, `or` 대체 미발생, 같은 키로 합쳐져 변화 0)로 고친다.

## 4. 새 원칙 위반

S-1 밖에는 없다. 점검한 항목은 graph 정본, fail-closed, DC/AC, DEC-103, 상수 0, 회로 이름 0, 만들면 배선, 계획 먼저다.
