"""극점 노드 목록 (설계 41 §1.7-5, 계획 용어집 '극점 노드 목록').

진입점: `pole_nodes(model, ground, blocks, impedance, drive) -> tuple[PoleNode]`.

그 뷰의 교류접지가 아닌 **모든 노드**를 이름순으로 낸다(신호 경로 밖 바이어스 노드도 용량을 가진 노드다). 노드마다 소속 블록 키(그 넷을 소유한 블록의
출력노드 키. 입력 경계 넷은 앞 블록이 소유하므로 앞 블록 소속이고, 어느 블록도 소유하지 않으면 빈 tuple), 임피던스 등급, 구동 종류(신호가 들어오지
않는 노드는 빈 문자열)를 붙인다. 보상 변수(GB5)·출력 구동 규칙·`parasitic_pm_ss_deg` 가 이 목록을 소비한다. 버퍼 출력노드도 목록에 든다.
"""
from .s1v_values import PoleNode


def pole_nodes(model, ground, blocks, impedance, drive):
    owner = {}
    for block in blocks:
        owner.update({net: block.key for net in block.nodes if net not in block.inputs})
    kind = {d.net: d.kind for d in drive.drive}
    return tuple(PoleNode(net, owner.get(net, ()), impedance[net], kind.get(net, ""))
                 for net in model.nets if net not in ground)
