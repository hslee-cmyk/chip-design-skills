"""--collect-only -q 출력 두 개의 id 집합 비교. sha256 = sha256(UTF-8('\n'.join(sorted(id, 역슬래시->슬래시))))."""
import hashlib, json, sys
def ids(p):
    out = []
    for ln in open(p, encoding="utf-8", errors="replace"):
        ln = ln.strip().replace("\\", "/")
        if "::" in ln and ln.startswith("skills/"):
            out.append(ln)
    return sorted(set(out))
a, b = ids(sys.argv[1]), ids(sys.argv[2])
sa, sb = set(a), set(b)
by = lambda s: {f: sum(1 for x in s if x.split("::")[0] == f) for f in sorted({x.split("::")[0] for x in s})}
r = {"n_a": len(a), "n_b": len(b), "only_a_by_file": by(sa - sb), "only_b_by_file": by(sb - sa),
     "only_b": sorted(sb - sa),
     "sha_a": hashlib.sha256("\n".join(a).encode()).hexdigest(), "sha_b": hashlib.sha256("\n".join(b).encode()).hexdigest()}
json.dump(r, open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(r, ensure_ascii=False, indent=1))
