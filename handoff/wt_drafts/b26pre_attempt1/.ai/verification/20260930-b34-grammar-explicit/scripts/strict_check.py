"""base 판 게이트 코드로 spec card 파싱·엄격 집합·V1 명령 형식·신규 심볼 목록 확인."""
import sys
import merge_gate as mg, role_paths as rp
root, base, cid, v1 = sys.argv[1:5]
old = mg.TreeView(["-C", root], base)
card = rp.parse_spec_card(old.read(rp.spec_card_path(cid)).decode("utf-8"), cid)
print("card", {k: card[k] for k in ("id", "phase", "evidence_type", "gate_change", "approval", "activated_ic_case")})
ss = mg.strict_set(old, card)
print("strict_set", sorted(ss))
cf = old.read("skills/analog-gmid-design/assets/tests/conftest.py")
print("conftest_has_gmid_phase", mg.conftest_has_gmid_phase(cf) if cf is not None else None)
print("v1_command_check", mg.v1_command_check(v1, python_path="C:/Python314/python.exe", old=base, strict_needed=sorted(ss), phase=card["phase"]))
ic = old.read("docs/02-design/specs/%s.interface.md" % cid)
print("new_symbols", sorted(mg.read_new_symbols(ic.decode("utf-8"))))
