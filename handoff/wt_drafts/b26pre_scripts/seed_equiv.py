"""b26pre -- 씨앗 한 방향 삭제 변이(_propose_gm_id_roles·_propose_L_roles·propose_device_roles_gap_fill의
`seeds[ga] = gb` / `seeds[gb] = ga`)가 library 회로에서 load_topology meta를 바꾸는지 잰다(등가 후보 근거).
방법: find_structural_symmetry_candidates를 감싸, 씨앗에서 자기 자신이 아닌 쌍(x->y, y->x)의 한쪽 방향만 남긴다
(fwd = x<y인 x->y만, rev = x>y인 x->y만). b1(HEAD + B34) 사본에서 실행. 결과 C:/g87/out/seed_equiv.txt."""
import glob, json, os, sys
A = "C:/g87/b1/skills/analog-gmid-design/assets"
sys.path.insert(0, A)
import stick_diagram as sd  # noqa

OUT = open("C:/g87/out/seed_equiv.txt", "w", encoding="utf-8")
orig = sd.find_structural_symmetry_candidates


def norm(meta):
    keys = ("device_roles", "_device_roles_autofilled", "_matching_pairs_autofilled", "_matching_pairs_needs_review",
            "_device_roles_gap_fill_review_needed", "_vertical_stack_id_autofilled", "symmetry")
    return json.dumps({k: meta.get(k) for k in keys}, sort_keys=True, default=lambda o: sorted(o) if isinstance(o, set) else repr(o))


def make(mode):
    def f(transistors, seed_net_pairs, transform="mirror"):
        s = {}
        for k, v in seed_net_pairs.items():
            if k == v or transform != "mirror":
                s[k] = v
            elif (mode == "fwd" and k < v) or (mode == "rev" and k > v):
                s[k] = v
            elif seed_net_pairs.get(v) != k:   # 짝이 없는 단방향 씨앗은 그대로
                s[k] = v
        return orig(transistors, s, transform=transform)
    return f


files = sorted(glob.glob(A + "/library/*.topology.json"))
files = [p for p in files if not os.path.basename(p).startswith("_")]
diff = 0
for p in files:
    sd.find_structural_symmetry_candidates = orig
    _t, m0 = sd.load_topology(p)
    ref = norm(m0)
    for mode in ("fwd", "rev"):
        sd.find_structural_symmetry_candidates = make(mode)
        _t, m1 = sd.load_topology(p)
        same = norm(m1) == ref
        diff += not same
        OUT.write("%s %s %s\n" % (os.path.basename(p), mode, "same" if same else "DIFF"))
sd.find_structural_symmetry_candidates = orig
OUT.write("circuits %d, diffs %d\n" % (len(files), diff))
OUT.close()
print(open("C:/g87/out/seed_equiv.txt", encoding="utf-8").read())
