"""base 판 게이트 함수로: 엄격 집합, V1 명령 형식(v1_command_check), 계획서 v_intro·phase_order, red 해시 재계산.
usage: python -P strict7.py <V1 명령 문자열 파일>"""
import json, sys
sys.path.insert(0, "C:/g394/gmid-gate-cache/863a037cc0d774bb984006ea39966c5e4dd741ab")
import merge_gate as mg  # noqa: E402
import role_paths as rp  # noqa: E402

B = "863a037cc0d774bb984006ea39966c5e4dd741ab"
rid = "20261001-b26-backfill-interdig-final-audit"
repo = mg.Repo("C:/g394/iso/.git")
old = mg.TreeView(repo.args, B)
card = rp.parse_spec_card(old.read(rp.spec_card_path(rid)).decode("utf-8"), rid)
s = mg.strict_set(old, card)
plan = mg.read_plan_tables_text(old.read(mg.PLAN_PATH).decode("utf-8"))
v1 = open(sys.argv[1], encoding="utf-8").read().strip()
fails = mg.v1_command_check(v1, python_path="C:/Python314/python.exe", old=B, strict_needed=s, phase=card["phase"])
ids = ["skills/analog-gmid-design/assets/tests/contracts/test_b26_backfill_interdig.py::test_b26bf_in_loop_relaxed_to_layout",
       "skills/analog-gmid-design/assets/tests/contracts/test_b26_backfill_interdig.py::test_b26bf_after_loop_max_rounds_exceeded",
       "skills/analog-gmid-design/assets/tests/contracts/test_b26_backfill_interdig.py::test_b26bf_site_pair_not_found",
       "skills/analog-gmid-design/assets/tests/contracts/test_b26_backfill_interdig.py::test_b26bf_site_no_finger_w",
       "skills/analog-gmid-design/assets/tests/contracts/test_b26_backfill_interdig.py::test_b26bf_site_growth_not_applicable"]
hashes = {i: mg.red_failure_hash(i, AssertionError) for i in ids}
out = {"card": {k: card[k] for k in card if k in ("phase", "evidence_type", "approvals", "activated_ic_case", "gate_change")},
       "strict_set": sorted(s), "v1_command": v1, "v1_command_check": fails,
       "v_intro": plan.v_intro, "phase_order": list(plan.phase_order), "red_failure_hash": hashes}
print(json.dumps(out, ensure_ascii=False, indent=1, default=str))
