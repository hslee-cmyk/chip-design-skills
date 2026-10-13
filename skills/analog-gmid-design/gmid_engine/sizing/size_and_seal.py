"""GB7 공개 API -- 후보 θ 하나를 DC 정본(노드전압·가지전류·소자 op)으로 풀고 봉인한다 (설계 3.2·5절 `size_and_seal`,
계획 N3.5 평가 커널 ②③④⑤ -> 봉인, 요구 3.2).

진입점: `size_and_seal(ctx, theta, parent=None, w_request=()) -> DcEvaluation`.

* `ctx` = `build_kernel_context` 결과(S0 당 1회). `theta` = `check_theta` 가 받는 {(kind, key): 값} 또는 `Theta`.
* `parent` = 같은 ctx 에서 나온 이전 `DcEvaluation`(FD 스텝의 기준점·SLSQP 직전 반복 등) 또는 None(ctx.base 에서 시작).
  블록은 입력 버전이 같으면 계산하지 않고 parent 스냅샷의 필드를 그대로 쓴다(필드가 곧 캐시, 구조 공유).
  계획 블록 버전이 ctx 와 다른 parent 는 `ValueError`(다른 S0 의 스냅샷을 섞지 않는다).
* 블록 순서와 추가 인자(블록이 실제로 읽는 θ 성분만 -- 한 성분을 움직이면 그 성분을 읽는 블록과 하류만 다시 계산):
  `dc_currents`(θ current) -> `dc_lengths`(θ L) -> `dc_columns`(θ ln_idu·y·resistance, 고정 노드값, 선언 저항, LUT) ->
  `dc_widths`(LUT) -> `seal_dc`.
  [DEC-92] θ `capacitance`·`ss_resistance`(DC 전류가 흐르지 않는 수동소자)는 어느 DC 블록에도 넘기지 않는다 -- 그 성분만
  바꾼 θ 는 parent 에서 DC·봉인 블록 계산 0(소신호 값은 metrics `ss_evaluate` 가 θ 에서 읽는다).
* **L 동치류**(설계 40 §3.2-1): θ 의 L 성분은 동치류당 주인 하나이고(`ctx.schema`), `ctx.l_ties` = ((멤버, 주인), ...) 의 멤버 L = 주인 θ L.
* **tol_I**(설계 40 §3.7-3, 계획 N3.6 v6.4): 봉인 3 의 gm 은 후보 자기 동작점의 `device.dc_gm`(`dc_tolerances` 가 쓴 ID × LUT gm/ID) 하나다.
  parent 에 의존하지 않으므로 같은 θ 는 parent 와 무관하게 같은 봉인 결과를 낸다. 수동소자 θ 만 바뀐 자식의 DC 재사용은 입력 버전 일치로 성립한다.
* **W_request**(설계 40 §3.7, 계획 N3.17 LY3): `w_request` = {MOS: W(m)} 또는 ((MOS, W), ...) -- 그 소자의 W 는 고정 입력이다. 쓰기 소자의 θ
  ln IDu 는 무시되고 ln(ID·L/W) 로 대체되며(ID·L 은 ②③ 이 정한 값), 종속 소자는 요청 W 로 `dc_widths` 가 쓰고 봉인 3 이 어긋남을 판정한다.
* 실패: 후보 실패 = `SealViolationError`·`NonconvergentError`(core `CANDIDATE_FAILURE_CLASSES`) -- 탐색 층이 이름으로 잡아 S3
  실패 레코드로 남긴다. 그 밖(ValueError·TypeError = 호출 계약 위반)은 잡지 않는다.
"""
from .kernel_run import run_kernel


def size_and_seal(ctx, theta, parent=None, w_request=()):
    return run_kernel(ctx, theta, parent, w_request, True)
