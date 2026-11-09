"""df23_recount.py 자기 점검: base 레지스트리 + 기대 행으로 만든 §8 -> same(exit 0), 변형마다 -> differs(exit 1).
사용: python -P df23_recount_selftest.py <base 복제본> <작업 디렉터리> <out.jsonl>"""
import json, os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import df23_recount as R

base, work, out = sys.argv[1:4]
inv_src = os.path.join(base, R.INV_REL)
reg_src = os.path.join(base, R.REG_REL)
inv = json.load(open(inv_src, encoding="utf-8"))
e81, e82, _ = R.expected(inv)


def sec8(rows81, rows82, path=R.INV_REL, measured=None, hdr82=R.HDR82, usage=True):
    m = inv["measured_at"] if measured is None else measured
    L = ["## 8. DF-23 -- 엔진 이름 리터럴 종속 (전수 목록 기록)", "", "목록: `%s`" % path, "measured_at: `%s`" % m, ""]
    if usage:
        L += ["목록을 다시 재면 이 절을 같은 Phase 안에서 갱신한다(대조: `reg_check.py --df23-inventory`).", ""]
    L += ["### 8.1 총계", "", "| " + " | ".join(R.HDR81) + " |", "|---|---|---|"]
    L += ["| " + " | ".join(r) + " |" for r in rows81]
    L += ["", "### 8.2 함수별 (role = 동작을 정함)", "", "| " + " | ".join(hdr82) + " |", "|---|---|---|---|---|"]
    L += ["| " + " | ".join(r) + " |" for r in rows82]
    L += [""]
    return "\r\n".join(L) + "\r\n"


r82 = [list(x) for x in e82]
bump = [list(x) for x in e82]; bump[0][2] = str(int(bump[0][2]) + 1)
cases = [
    ("clean", sec8(e81, e82), 0),
    ("clean_reversed", sec8(list(reversed(e81)), list(reversed(e82))), 0),
    ("no_section", "", 1),
    ("row81_missing", sec8(e81[1:], e82), 1),
    ("row81_dup", sec8(e81 + [e81[0]], e82), 1),
    ("row82_missing", sec8(e81, e82[1:]), 1),
    ("row82_count_off", sec8(e81, [tuple(x) for x in bump]), 1),
    ("row82_dup", sec8(e81, e82 + [e82[-1]]), 1),
    ("path_off", sec8(e81, e82, path=R.INV_REL + "x"), 1),
    ("measured_off", sec8(e81, e82, measured=inv["measured_at"][:-1] + "0"), 1),
    ("hdr82_off", sec8(e81, e82, hdr82=["함수", "파일", "수", "DF", "담당 Phase"]), 1),
    ("usage_missing", sec8(e81, e82, usage=False), 1),
]
with open(out, "w", encoding="utf-8") as fo:
    for tag, s8, want in cases:
        d = os.path.join(work, tag)
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(os.path.dirname(os.path.join(d, R.REG_REL)), exist_ok=True)
        os.makedirs(os.path.dirname(os.path.join(d, R.INV_REL)), exist_ok=True)
        shutil.copyfile(inv_src, os.path.join(d, R.INV_REL))
        open(os.path.join(d, R.REG_REL), "wb").write(open(reg_src, "rb").read() + s8.encode("utf-8"))
        p = subprocess.run([sys.executable, "-P", os.path.join(os.path.dirname(os.path.abspath(__file__)), "df23_recount.py"),
                            d, os.path.join(d, "res.json")], capture_output=True)
        fo.write(json.dumps({"case": tag, "exit": p.returncode, "want": want, "ok": p.returncode == want}, ensure_ascii=False) + "\n")
        fo.flush()
print(open(out, encoding="utf-8").read())
