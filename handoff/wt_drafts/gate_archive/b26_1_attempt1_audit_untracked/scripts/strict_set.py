# base 판 merge_gate.strict_set(B1 트리, card) 값 -- 캐시를 sys.path 맨 앞에 두고 부른다.
import sys
cache, iso, b1, cid = sys.argv[1:5]
sys.path.insert(0, cache)
import merge_gate as mg
import role_paths as rp
repo = mg.Repo(iso + "/.git") if hasattr(mg, "Repo") else None
view = mg.TreeView(["-C", iso], b1)
card_b = view.read(rp.spec_card_path(cid))
card = rp.parse_spec_card(card_b.decode("utf-8"), cid)
ks = mg.strict_set(view, card)
print("phase=%s" % card["phase"])
print("activated_ic_case=%r" % (card["activated_ic_case"],))
print("strict=%s" % ",".join(sorted(ks)))
