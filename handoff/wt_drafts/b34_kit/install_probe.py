"""사용자 선행 작업(install.py SKILLS에 analog-grammar) 확인용 -- '설치본' 모양 사본(skills/<name>만 있는 디렉터리)을
base(0f23786)와 모의 head(B34 코드 사이트 적용) 두 판에서 analog-grammar 없음/있음으로 만들어 library 9회로 load_topology를 부른다.
설치본 경로 관계(~/.claude/skills/analog-gmid-design/assets -> ../../analog-grammar/assets)와 같은 상대 위치다.

  C:/Python314/python.exe -B install_probe.py --clone C:/g123/repo --head sim-b34 --work C:/g123/inst --out <KIT>/out/install_probe.json
"""
import argparse, io, json, os, subprocess, sys, tarfile

PROBE = r'''
import sys, os, json, hashlib
root = sys.argv[1]
A = os.path.join(root, "skills", "analog-gmid-design", "assets")
sys.path.insert(0, A)
import stick_diagram as sd
res = {}
for f in sorted(os.listdir(os.path.join(A, "library"))):
    if not f.endswith(".topology.json") or f.startswith("_"):
        continue
    try:
        ts, meta = sd.load_topology(os.path.join(A, "library", f))
        res[f] = {"ok": True, "device_roles": len(meta.get("device_roles") or {}),
                  "gap_fill_review": len(meta.get("_device_roles_gap_fill_review_needed") or []),
                  "meta_sha": hashlib.sha256(json.dumps(meta, sort_keys=True, default=repr).encode()).hexdigest()[:16]}
    except Exception as e:
        res[f] = {"ok": False, "exc": type(e).__name__, "msg": str(e)[:200],
                  "cause": type(e.__cause__).__name__ if e.__cause__ else None}
print(json.dumps(res, ensure_ascii=False))
'''


def main(argv):
    ap = argparse.ArgumentParser()
    for k in ("--clone", "--head", "--work", "--out"):
        ap.add_argument(k, required=True)
    ns = ap.parse_args(argv)
    os.makedirs(ns.work, exist_ok=True)
    pp = os.path.join(ns.work, "probe.py")
    open(pp, "w", encoding="utf-8").write(PROBE)
    out = {}
    for rev in ("0f23786", ns.head):
        for mode in ("without", "with"):
            d = os.path.join(ns.work, "%s_%s" % (rev.replace("/", "_"), mode))
            assert not os.path.exists(d), d
            os.makedirs(d)
            names = ["skills/analog-gmid-design"] + (["skills/analog-grammar"] if mode == "with" else [])
            data = subprocess.run(["git", "-C", ns.clone, "archive", rev] + names, capture_output=True, check=True).stdout
            tarfile.open(fileobj=io.BytesIO(data)).extractall(d, filter="data")
            r = subprocess.run([sys.executable, "-B", "-P", pp, d], capture_output=True,
                               env=dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONHASHSEED="1"))
            try:
                res = json.loads(r.stdout.decode("utf-8"))
            except ValueError:
                res = {"_error": (r.stdout + r.stderr).decode("utf-8", "replace")[-800:]}
            out["%s|%s" % (rev, mode)] = res
            okn = sum(1 for v in res.values() if isinstance(v, dict) and v.get("ok"))
            print("%-10s %-8s ok %d/%d  exc %s" % (rev, mode, okn, len(res),
                  sorted({v.get("exc") for v in res.values() if isinstance(v, dict) and not v.get("ok")})))
    json.dump(out, open(ns.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # 요약 비교
    b_with, h_with = out["0f23786|with"], out["%s|with" % ns.head]
    b_wo, h_wo = out["0f23786|without"], out["%s|without" % ns.head]
    print("base with == head with (meta_sha 9/9):", all(b_with[k]["meta_sha"] == h_with[k]["meta_sha"] for k in b_with))
    print("base without vs base with meta_sha 같은 회로 수:", sum(b_wo[k].get("meta_sha") == b_with[k]["meta_sha"] for k in b_with))
    print("base without gap_fill_review:", [b_wo[k].get("gap_fill_review") for k in b_wo])
    print("base with    gap_fill_review:", [b_with[k].get("gap_fill_review") for k in b_with])
    print("head without 메시지 예:", list(h_wo.values())[0])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
