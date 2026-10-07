"""authoring 공용 helper -- 단자에 나타나는 넷 집합. `hidden_rails.py`·`topology_load.py` 가 같이 쓴다.

* `mos_terminal_nets(devices)`: MOS 소자의 drain·gate·source 와 선언 bulk 넷 frozenset.
* `two_terminal_nets(elements)`: 수동소자·이상원 terminals 넷 frozenset.
"""


def mos_terminal_nets(devices):
    nets = set()
    for x in devices:
        nets.update((x.d, x.g, x.s))
        if x.bulk is not None:
            nets.add(x.bulk)
    return frozenset(nets)


def two_terminal_nets(elements):
    nets = set()
    for x in elements:
        nets.update(x.terminals)
    return frozenset(nets)
