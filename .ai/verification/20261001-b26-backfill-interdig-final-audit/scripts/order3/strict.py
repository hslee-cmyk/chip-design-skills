import sys
sys.path.insert(0, "C:/g393/gmid-gate-cache/863a037cc0d774bb984006ea39966c5e4dd741ab")
import merge_gate as mg
import role_paths as rp
repo = mg.Repo("C:/g393/iso/.git")
old = mg.TreeView(repo.args, "863a037cc0d774bb984006ea39966c5e4dd741ab")
rid = "20261001-b26-backfill-interdig-final-audit"
card = rp.parse_spec_card(old.read(rp.spec_card_path(rid)).decode("utf-8"), rid)
print("card phase", card["phase"], "aic", card["activated_ic_case"])
s = mg.strict_set(old, card)
print("STRICT=" + ",".join(sorted(s)))
