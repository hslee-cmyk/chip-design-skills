"""B37a 정직한 픽스처 보강 사본(head_fx): head 사본을 복사한 뒤 selftest 두 파일의 **입력 픽스처만** 고친다.
규칙(card '작성 전 실측' 7과 같음 -- test-author가 소스 없이 따를 수 있는 규칙):
  * 합성 toy topology(신호 입력이 없는 바이어스·미러·단일 소자 픽스처): `"ports": {}`(명시적 '포트 없음').
  * 라이브러리 회로의 부분 netlist를 옮긴 픽스처(l4c = current_reuse M3a 행): 그 회로의 `ports` 선언 중
    이 netlist에 나오는 넷만 같은 role로(`Vip` differential_input_p, `Vim` differential_input_n). 출력 포트(Vop/Vom)는
    이 부분 netlist에 없으므로 넣지 않는다. `direction`은 넣지 않는다(S6).
  * 연결 파일(linked)에는 넣지 않는다(진입 파일에만 -- s071 stick partA).
  * `resolve_stack_layout` 직접 호출(test_s013 두 곳)에는 `ports=_rsl_meta["ports"]`(같은 test 첫 호출의 meta 선언).
기대값·assert·메시지 문자열은 바꾸지 않는다. 치환 대상은 정확한 횟수를 assert한다.
사용: python -B make_fx.py <head 사본> <dst>
"""
import os, shutil, sys

SRC, DST = sys.argv[1], sys.argv[2]
U = "skills/analog-gmid-design/assets/tests/unit"


def sub(s, old, new, count):
    n = s.count(old)
    assert n == count, (n, count, old[:100])
    return s.replace(old, new)


def edit(rel, fn):
    p = os.path.join(DST, rel)
    with open(p, encoding="utf-8", newline="") as fh:
        s = fh.read()
    crlf = "\r\n" in s
    s = fn(s.replace("\r\n", "\n"))
    compile(s, p, "exec")
    if crlf:
        s = s.replace("\n", "\r\n")
    with open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write(s)


def sizing(s):
    s = sub(s, '"linked_topology_files": [], "compensation": None, "_compensation_status": "not_applicable",',
            '"linked_topology_files": [], "compensation": None, "_compensation_status": "not_applicable", "ports": {},', 10)
    s = sub(s, '"linked_topology_files": [], "_compensation_status": "resolved",',
            '"linked_topology_files": [], "_compensation_status": "resolved", "ports": {},', 2)
    s = sub(s, '"topology_name": "bad_fixture", "schema_version": "2.0",',
            '"topology_name": "bad_fixture", "schema_version": "2.0", "ports": {},', 1)
    l4c = '"ports": {"Vip": {"role": "differential_input_p"}, "Vim": {"role": "differential_input_n"}},'
    s = sub(s, '"topology_name": "m3a_row_selftest",', '"topology_name": "m3a_row_selftest", ' + l4c, 1)
    s = sub(s, '"topology_name": "m3a_row_ofcb_selftest",', '"topology_name": "m3a_row_ofcb_selftest", ' + l4c, 1)
    s = sub(s, "resolve_stack_layout(_rsl_trs, _rsl_forced, _rsl_device_roles)",
            'resolve_stack_layout(_rsl_trs, _rsl_forced, _rsl_device_roles, ports=_rsl_meta["ports"])', 1)
    s = sub(s, "resolve_stack_layout(_rsl_bad_trs, [], _rsl_bad_roles)",
            'resolve_stack_layout(_rsl_bad_trs, [], _rsl_bad_roles, ports=_rsl_meta["ports"])', 1)
    return s


def stick(s):
    return sub(s, '"topology_name": "demo_partA", "source": "self-test synthetic",',
               '"topology_name": "demo_partA", "source": "self-test synthetic", "ports": {},', 1)


if os.path.exists(DST):
    shutil.rmtree(DST)
shutil.copytree(SRC, DST)
edit(U + "/test_selftest_sizing_recipe.py", sizing)
edit(U + "/test_selftest_stick_diagram.py", stick)
print("fx built", DST)
