"""레이아웃 결과 -> 평가 커널 재검증 입력 `RealizedGeometry` (계획 N3.17 LY7·LY8, DEC-89 (2)·(5), DEC-91 (2), 설계 40 §3.9 U14, WB-1).

진입점: `realized_geometry(snapshot, placements) -> sizing.RealizedGeometry`.

`snapshot` = 레이아웃 필드를 쓴 설계점 스냅샷(`LayoutResult.snapshot`) -- 확산 기하는 `ly_diffusion` 필드.

* `layout_ref` = ((소자, `metrics.DiffusionGeometry(finger_w, ad, as, pd, ps, m = n_fingers)`), ...) 이름순 -- `ly_diffusion` 필드 그대로의 참조 값(엔진 접합 용량은 이 확산 면적 비,
  오라클 입력은 같은 기하의 ad·as·pd·ps, LY8). 배치 소자의 입력 손가락 (nf, finger_w) 도 여기서 읽는다(`dc_solve` 가 `slice_of_finger` 로 슬라이스를 정한다). 요청 대기 소자는 뺀다: 레이아웃이 놓은 잠정 기하가 요청한
  (키, nf) 와 다르므로 그 소자의 접합 기하는 그 평가가 쓴 W 의 생성 규칙 기하(요청 대기 소자 포함)에서 읽고, 요청이 실현되면 다음 레이아웃의 기하가 들어온다.
* `w_request` = ((소자, (nf, finger_w)), ...) 이름순 -- **요청 대기 소자만**(WB-1 A-139): 레이아웃 요청(LY3 W_request)이 정한 손가락 행 참조(`effective_placement` 가 마지막 시도에서 읽은
  `Placement.n_fingers`·`finger_w_m`). 배치 소자는 두지 않는다(`layout_ref` 가 입력 손가락의 출처). 요청 W 로 손가락을 다시 고르지 않는다.
* 폭 키(kind 당 슬라이스 하나) 운반은 없다(kind 키 운반 삭제): 슬라이스는 소자마다 `dc_solve` 가 입력 손가락의 폭으로 정한다.
"""
from gmid_engine.layout import F_DIFFUSION, LAYOUT_KEY
from gmid_engine.metrics import DiffusionGeometry
from gmid_engine.sizing import RealizedGeometry


def realized_geometry(snapshot, placements):
    pending = {p.name for p in placements if p.pending}
    diffusion = tuple((d.name, DiffusionGeometry(d.finger_w_m, d.ad_m2, d.as_m2, d.pd_m, d.ps_m, float(d.n_fingers)))
                      for d in sorted(snapshot.value("graph", LAYOUT_KEY, F_DIFFUSION), key=lambda x: x.name)
                      if d.name not in pending)
    return RealizedGeometry(diffusion, tuple((p.name, (p.n_fingers, p.finger_w_m)) for p in sorted(placements, key=lambda x: x.name) if p.pending))
