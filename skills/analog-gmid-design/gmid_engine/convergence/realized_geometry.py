"""레이아웃 결과 -> 평가 커널 재검증 입력 `RealizedGeometry` (계획 N3.17 LY7·LY8, DEC-89 (2)·(5), DEC-91 (2), 설계 40 §3.9 U14).

진입점: `realized_geometry(snapshot, placements, keys) -> RealizedGeometry`.

`snapshot` = 레이아웃 필드를 쓴 설계점 스냅샷(`LayoutResult.snapshot`) -- 확산 기하는 `ly_diffusion` 필드.

* `w_request` = ((소자, 실현 W), ...) 이름순 -- 놓인 소자는 `nf x finger_w`, W_request 응답 대기 소자는 요청한 W(`effective_placement`). 모든 배치 소자를 넣는다: LY7 은
  W_request 유무와 관계없이 실현 기하로 재평가하고 LY1 허용오차 안의 실현 오차도 재평가 없이 freeze 하지 않는다.
* `w_keys` = `kernel_keys` 가 고른 ((kind, 폭 키), ...) -- 실현 폭 슬라이스(소자의 폭 키가 바뀌면 그 키를 읽는 계산 블록이 다시 계산된다).
* `diffusion` = ((소자, `metrics.DiffusionGeometry(finger_w, ad, as, pd, ps, m = n_fingers)`), ...) 이름순 -- `ly_diffusion` 필드 그대로(엔진 접합 용량과
  오라클 입력이 같은 값, LY8). 요청 대기 소자는 뺀다: 레이아웃이 놓은 잠정 기하가 요청한 (키, nf) 와 다르므로 그 소자는 LUT 생성 규칙 기하(요청한 폭 슬라이스·W 와 일관)를
  쓰고, 요청이 실현되면 다음 레이아웃의 기하가 들어온다.
"""
from gmid_engine.layout import F_DIFFUSION, LAYOUT_KEY
from gmid_engine.metrics import DiffusionGeometry
from gmid_engine.search import RealizedGeometry


def realized_geometry(snapshot, placements, keys):
    pending = {p.name for p in placements if p.pending}
    diffusion = tuple((d.name, DiffusionGeometry(d.finger_w_m, d.ad_m2, d.as_m2, d.pd_m, d.ps_m, float(d.n_fingers)))
                      for d in sorted(snapshot.value("graph", LAYOUT_KEY, F_DIFFUSION), key=lambda x: x.name)
                      if d.name not in pending)
    return RealizedGeometry(tuple((p.name, p.W_m) for p in placements), tuple(keys), diffusion)
