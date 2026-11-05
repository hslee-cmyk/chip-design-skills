"""θ 분류 필드 계산 블록 (card 20261104-tb1-theta-class, 설계 41 §5.3.3 표, 설계 40 §2.4.8 소유표 `device.theta_class`, 계획 N6.29 범위 1~2, R13).

진입점: `theta_class`(`@compute_block`) -- `theta_class(snapshot, has_gbw_target, has_rout_limit, has_settling)`. S0 블록, `dc_writer_plan` 앞. θ 무관(S0 당 1회).

* extras = `DcInputs` 의 유무 칸 셋(bool). **값은 읽지 않는다** -- 선언 값이 바뀌어도 결과는 같다.
* writes `device.theta_class` = {MOS: `ThetaClass(kind)`} (MOS 전수). reads = S1 소자 열·핀 + S1v `graph.views`(블록 AC 역할·feedforward 묶음). 위치 좌표
  `device.dc_coord`·topology 태그는 읽지 않는다.
* 분류(41 §5.3.3 표):
  - 매크로 활성 = GBW 목표 선언, 또는 정착 선언 있음 + GBW 미선언 (= 둘 중 하나라도 선언).
  - **S** = 매크로 활성 회로에서 gain 제약 전달 뷰 전부(없으면 전달 뷰 전부; 정의는 `l_classes.gain_transfer_views` 와 공용, 합집합)의 이득·복합 블록의 AC 역할 `input`, 그리고 출력 저항(rout)이 선언된 회로에서 전달 뷰 버퍼 블록의
    출력 노드에 source 가 닿는 follower.
  - **F** = AC 역할 `cascode`·`pass`·`follower`, 그리고 S 가 아닌 `input`(매크로 비활성 회로의 입력).
  - **B** = 그 밖 전부(`load`·`mirror`·`diode_load`·`tail_source`, 어느 블록에도 들지 않는 MOS, feedforward 묶음 셀). S1v 가 없는 S1(블록 없음)이면 전부 B.
* `off` 선언 MOS 도 값은 B 로 낸다(블록 밖 정의) -- 거르는 것은 소비자(`region_decl` READS).
"""
from gmid_engine.core import compute_block
from gmid_engine.graph import (BLOCK_BUFFER, BLOCK_COMPOSITE, BLOCK_GAIN, ELEMENT_MOS, ROLE_CASCODE, ROLE_FOLLOWER, ROLE_INPUT, ROLE_PASS,
                               S1V_KEY, VIEW_TRANSFER, gain_transfer_views)

from .s2_values import THETA_CLASS_B, THETA_CLASS_F, THETA_CLASS_S, THETA_CLASS_WRITER, ThetaClass

READS = (("device", "element_class"), ("device", "pins"), ("graph", "views"))
WRITES = (("device", "theta_class"),)
_SIGNAL_ROLES = (ROLE_CASCODE, ROLE_PASS, ROLE_FOLLOWER, ROLE_INPUT)        # F 가 되는 AC 역할(입력은 S 가 아닐 때)
_GAIN_BLOCKS = (BLOCK_GAIN, BLOCK_COMPOSITE)


@compute_block(THETA_CLASS_WRITER, reads=READS, writes=WRITES)
def theta_class(projection):
    has_gbw_target, has_rout_limit, has_settling = projection.extras
    classes = dict(projection.column("device", "element_class"))
    pins = {name: dict(p) for name, p in projection.column("device", "pins")}
    views = tuple(v for v in dict(projection.column("graph", "views")).get(S1V_KEY, ()) if v.kind == VIEW_TRANSFER)
    macro = has_gbw_target or has_settling
    # gain 제약 전달 뷰 전부(`l_classes.gain_transfer_views`, 합집합), 없으면 전달 뷰 전부 -- 첫 뷰 하나로 줄이지 않는다.
    # 입력 `DcInputs` 는 유무 bool 뿐이라 gain 제약 뷰 id 집합이 이 블록에 없다 -> 빈 집합을 넘기고 전달 뷰 전부로 떨어진다(보고: 뷰 id 정본 필드 없음).
    gain_views = (gain_transfer_views(views, ()) or views) if macro else ()
    strong = {name for v in gain_views for block in v.blocks if block.kind in _GAIN_BLOCKS for name, role in block.roles if role == ROLE_INPUT}
    if has_rout_limit:
        strong |= {name for v in views for block in v.blocks if block.kind == BLOCK_BUFFER for name, role in block.roles
                   if role == ROLE_FOLLOWER and pins[name]["s"] in block.outputs}
    signal = {name for v in views for block in v.blocks for name, role in block.roles if role in _SIGNAL_ROLES}
    cells = {name for v in views for ff in v.feedforward for name in ff.cells + ff.bias_cells + ff.load_cells}
    return {("device", "theta_class"): {name: ThetaClass(THETA_CLASS_B if name in cells else THETA_CLASS_S if name in strong
                                                         else THETA_CLASS_F if name in signal else THETA_CLASS_B)
                                        for name, cls in classes.items() if cls == ELEMENT_MOS}}
