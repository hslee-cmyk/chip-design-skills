"""IT-2b 감사: 431d2e7b 순수 리팩터링 비트 동일 확인 -- out/run/HEAD(엔진 615ef68b) 대 HEAD2(엔진 431d2e7b), 그리고 HEAD2 대 HEAD2_rep2(결정성).
칸 전부를 비교하되 시간 칸(wall_s·perf 의 *_s)과 커널 기록의 n_solve(재계산 제거로 줄어드는 것이 목적)는 빼고, n_solve 는 따로 센다.
usage: python -I compare_refactor.py <run dir> <out json>
"""
import json
import sys
from pathlib import Path

RUN = Path(sys.argv[1])
LIB = ["common_gate_amplifier", "current_reuse_telescopic_ota", "folded_cascode", "nmcnr_amplifier", "pushpull_follower_buffer",
       "sf_pushpull_output_opamp", "two_stage_ota", "two_stage_ota_sf", "ngcc_3stage_ff"]


def load(side, c):
    p = RUN / side / (c + ".json")
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def strip(d, drop_solve):
    d = dict(d)
    for k in ("wall_s", "repo", "side"):
        d.pop(k, None)
    if "front" in d:
        fr = dict(d["front"])
        fr["perf"] = {k: v for k, v in fr.get("perf", {}).items() if not (k.endswith("_s") or "time" in k)}
        d["front"] = fr
    if drop_solve and "kernel" in d:
        d["kernel"] = [{k: v for k, v in r.items() if k != "n_solve"} for r in d["kernel"]]
    return d


def diffcols(a, b, drop_solve):
    sa, sb = strip(a, drop_solve), strip(b, drop_solve)
    return sorted(k for k in set(sa) | set(sb) if json.dumps(sa.get(k), sort_keys=True) != json.dumps(sb.get(k), sort_keys=True))


def main():
    out = {}
    for c in LIB:
        h, h2, r2 = load("HEAD", c), load("HEAD2", c), load("HEAD2_rep2", c)
        row = {}
        if h is not None and h2 is not None:
            row["refactor_diff_columns"] = diffcols(h, h2, True)
            if "kernel" in h:
                ks = lambda d: sum(r["n_solve"] for r in d["kernel"])
                row["n_solve"] = [ks(h), ks(h2)]
                row["kernel_calls_with_fewer_solves"] = sum(1 for a, b in zip(h["kernel"], h2["kernel"]) if b["n_solve"] < a["n_solve"])
                row["kernel_calls_with_more_solves"] = sum(1 for a, b in zip(h["kernel"], h2["kernel"]) if b["n_solve"] > a["n_solve"])
        if h2 is not None and r2 is not None:
            row["determinism_diff_columns"] = diffcols(h2, r2, False)
        out[c] = row
        print(c, row)
    Path(sys.argv[2]).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
