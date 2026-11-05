"""IT-0 SIM(§6.7-1a 모사, IT-1 범위 1·2·5만) 측정 전용 패치를 iso-sim 복제본에 적용한다. 판정 기록 폴더 밖에 쓰지 않는다."""
import sys, pathlib
root = pathlib.Path(sys.argv[1]) / "skills/analog-gmid-design/gmid_engine/sizing"
def sub(path, old, new, count=1):
    p = root / path; t = p.read_text(encoding="utf-8")
    assert t.count(old) == count, (path, old[:60], t.count(old)); p.write_text(t.replace(old, new), encoding="utf-8")
# 범위 1: 같은 DC 엣지(_TIE)와 input_tie_order 기록 없음
sub("writer_plan.py", """    for group in _same_colour_groups(ncolour, free_inputs):
        ties.append(TieBreak(TIE_INPUT_ORDER, group, group))
""", "")
sub("writer_plan.py", "_edges(classes, kinds, pins, diode, dcolour, free_inputs, hints)", "_edges(classes, kinds, pins, diode, dcolour, (), hints)")
# 범위 2: 입력 포트 W4 뿌리 y 키 = 뿌리 넷 (members = 자기 자신은 REL_TIE 가 없어 그대로 따라온다)
sub("writer_plan.py", "plan.put(root, TIER_W4, REL_WINDOW, None, None, INPUT_GROUP_KEY if ports else root)", "plan.put(root, TIER_W4, REL_WINDOW, None, None, root)")
# 범위 5 측 커널: 입력 뿌리 = 입력 포트인 W4 뿌리(y 키 = 넷), 뿌리마다 자기 y. 다중 입력 뿌리 정지(범위 4)는 넣지 않는다.
sub("block_columns.py", """    ("node", "dc_writer"), ("node", "dc_rail_v"), ("node", "dc_column_nbrs"),""",
    """    ("node", "dc_writer"), ("node", "dc_rail_v"), ("node", "dc_column_nbrs"), ("node", "port_direction"),""")
sub("block_columns.py", """        self.writers = dict(projection.column("node", "dc_writer"))
""", """        self.writers = dict(projection.column("node", "dc_writer"))
        self.input_ports = frozenset(n for n, d in projection.column("node", "port_direction") if d == "input")   # [IT0-SIM]
""")
sub("block_columns.py", """                     if w.relation == REL_WINDOW and w.y_key == INPUT_GROUP_KEY)""",
    """                     if w.relation == REL_WINDOW and net in self.input_ports and w.y_key == net)   # [IT0-SIM]""")
sub("block_columns.py", """    key = (THETA_Y, INPUT_GROUP_KEY)
    requested = c.theta[key]
    c.theta[key] = _MID
    try:
        values, logs = _solve(c)
        windows = c.input_windows(values, roots)
    except _FAILURES:
        windows = None
        found = None
    finally:
        c.theta[key] = requested""", """    key = tuple((THETA_Y, r) for r in roots)          # [IT0-SIM] 뿌리마다 자기 y
    requested = {k: c.theta[k] for k in key}
    for k in key:
        c.theta[k] = _MID
    try:
        values, logs = _solve(c)
        windows = c.input_windows(values, roots)
    except _FAILURES:
        windows = None
        found = None
    finally:
        c.theta.update(requested)""")
sub("block_columns.py", """    for y in _dyadic_ys(budget):
        c.theta[key] = y
        try:
            values, logs = _solve(c)
        except _FAILURES:
            continue
        finally:
            c.theta[key] = requested""", """    for y in _dyadic_ys(budget):
        for k in key:                                   # [IT0-SIM] 모든 입력 뿌리 y 를 같이 훑는다
            c.theta[k] = y
        try:
            values, logs = _solve(c)
        except _FAILURES:
            continue
        finally:
            c.theta.update(requested)""")
print("ok")
