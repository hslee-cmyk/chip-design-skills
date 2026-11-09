"""v4 모의 head + '동작 불변 정리'(선택지 (i)) 변형 v4c -- 정리 뒤 V3 대상·생존을 재기 위한 head.

정리(같은 def 안, B26-1이 이미 바꾸는 def만):
  C1 SD _propose_L_roles: 중복 가드 `if candidates is None: return None` 삭제(남는 `gm_id_roles` 가드)
  C2 SD propose_device_roles_gap_fill: `open_net = open_terminals[0]` -> `(open_net,) = open_terminals`
  C3 SD find_differential_pair_candidates: `for i in range(len(chains)): for j in range(i + 1, len(chains)):` -> `for i, j in itertools.combinations(range(len(chains)), 2):`
  C4 SR run_matching_safety_with_finger_growth: _finalize가 다시 하는 `_backfill_interdig_ok(result)` 2곳(루프 안·루프 뒤) 삭제
사용: python -B b26v4c.py classify            -> C:/g103/out/classify_v4c.txt, targets_v4c.json
      python -B b26v4c.py proto <NW>          -> v4c N2w 대상 중 v4에 없던 새 대상 + v4 잔존 대상만 시제품 실행(out/proto_v4c.jsonl)
"""
import ast, sys

R = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26_reconcile/"
sys.path.insert(0, R)
import b26v4_head as H        # noqa: E402
import b26v4_classify as C    # noqa: E402

_orig_build = H.build_head
ONLY = None   # None = C1~C4 전부, 아니면 {"C1",...}


def _dedent_block_after(sd, qual, hdr_i, hdr_j, new_hdr):
    a, b = H._def_span(sd, qual)
    lines = sd.split("\n")
    idx = [k for k in range(a, b - 1) if lines[k] == hdr_i and lines[k + 1] == hdr_j]
    assert len(idx) == 1, idx
    k = idx[0]
    ind_j = len(hdr_j) - len(hdr_j.lstrip())
    out = lines[:k] + [new_hdr]
    m = k + 2
    while m < len(lines):
        l = lines[m]
        if l.strip() and (len(l) - len(l.lstrip())) <= ind_j:
            break
        out.append(l[4:] if l.startswith(" " * (ind_j + 4)) else l)
        m += 1
    return "\n".join(out + lines[m:])


def cleanup(head, rr=", rails=rails"):
    """rr = head에서는 ', rails=rails', b1(정리만 한 모의 base b1c)에서는 ''."""
    S = H.S
    sd, srs = head[S.SD], head[S.SR]
    on = (lambda c: ONLY is None or c in ONLY)
    if on("C1"):
        sd = H._replace_in_def(sd, "_propose_L_roles",
                               "        transistors, base_inputs, outputs, feedbacks, biases, clocks%s)\n    if candidates is None:\n        return None\n" % rr,
                               "        transistors, base_inputs, outputs, feedbacks, biases, clocks%s)\n" % rr)
    if on("C2"):
        sd = H._replace_in_def(sd, "propose_device_roles_gap_fill", "        open_net = open_terminals[0]\n", "        (open_net,) = open_terminals\n")
    if on("C3"):
        sd = _dedent_block_after(sd, "find_differential_pair_candidates",
                                 "            for i in range(len(chains)):", "                for j in range(i + 1, len(chains)):",
                                 "            for i, j in itertools.combinations(range(len(chains)), 2):")
    if on("C4"):
        srs = H._replace_in_def(srs, "run_matching_safety_with_finger_growth",
                                "        _backfill_interdig_ok(result)\n        if result.ok:\n", "        if result.ok:\n")
        srs = H._replace_in_def(srs, "run_matching_safety_with_finger_growth",
                                "    _backfill_interdig_ok(result)\n    current_rows, cur_ctx, result = _finalize(current_rows, cur_ctx)\n    return {\"rows\": current_rows, \"audit\": result, \"ctx\": cur_ctx, \"growth_rounds\": growth_rounds,\n",
                                "    current_rows, cur_ctx, result = _finalize(current_rows, cur_ctx)\n    return {\"rows\": current_rows, \"audit\": result, \"ctx\": cur_ctx, \"growth_rounds\": growth_rounds,\n")
    ast.parse(sd)
    ast.parse(srs)
    head = dict(head)
    head[S.SD], head[S.SR] = sd, srs
    return head


def build_head(mode):
    if mode == "v4c":
        h, o = _orig_build("v4")
        return cleanup(h), o
    return _orig_build(mode)


H.build_head = build_head

if __name__ == "__main__":
    if sys.argv[1] == "classify":
        C.main("v4c")
