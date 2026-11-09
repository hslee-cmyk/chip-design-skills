"""D0b 작성 전 실측(측정 전용): D0a `plan` 시제품(_drafts/p3kit_d0a/move_plan_proto.py)에 '결정 필요 항목'의 규칙 후보를
환경 변수로 켜는 변형을 만들어 스크래치에 쓴다. 역할 산출물·기대값 근거가 아니다(작성자 != 검증자).

    python -B mk_variant.py <move_plan_proto.py> <출력 .py>

환경 변수(실행 때):
  V_KEEP=1  -- `--keep` 파일의 단위 중 A-0~A-5로 정해지지 않은 것은 그 파일에 남긴다(rule "A-K"). MOD 번호는 모든 MOD보다 큰 가짜 번호
              (도구 파일이라 MOD가 그것을 참조하면 upward로 잡힌다).
  V_A6=1    -- 참조자가 없어 A-5로 정해지지 않은 단위를 R(u)의 가장 큰 배정 MOD로(rule "A-6": 계층상 둘 수 있는 가장 낮은 자리).
              R(u)도 비면 unassigned 그대로. 고정점 반복과 번갈아 돈다.
  V_LIFT=1  -- A-4(셀 MOD 하나)를 A-3처럼 max(셀 MOD, R(u) 배정 MOD 최댓값)로(rule "A-4L").
출력 JSON에 `unassigned_refs`({단위: [R(u) 단위·MOD]})를 더한다.
"""
import sys

src, dst = sys.argv[1], sys.argv[2]
t = open(src, encoding="utf-8").read()


def sub(old, new, label):
    global t
    if t.count(old) != 1:
        raise SystemExit("anchor %s: %d" % (label, t.count(old)))
    t = t.replace(old, new)


sub("""        elif ms and any(len(m) == 1 for m in ms):
            m = [x for x in ms if len(x) == 1][0]
            assign[uid], rule[uid] = next(iter(m)), "A-4"
""", """        elif ms and any(len(m) == 1 for m in ms):
            m = [x for x in ms if len(x) == 1][0]
            if os.environ.get("V_LIFT") == "1":
                cat[uid] = ("A-4L", next(iter(m)))
            else:
                assign[uid], rule[uid] = next(iter(m)), "A-4"
""", "lift")
sub("""    for it in range(200):
        moved = False
""", """    KEEPNUM = {}
    for i_, f_ in enumerate(ns.keep):
        KEEPNUM[f_] = 1000 + i_
        modfile[1000 + i_] = f_
    for outer in range(50):
      before = dict(assign)
      for it in range(200):
        moved = False
""", "outer")
sub("""            if assign.get(uid) != k:
                assign[uid], rule[uid] = k, r_
                moved = True
        if not moved:
            break
""", """            if assign.get(uid) != k:
                assign[uid], rule[uid] = k, r_
                moved = True
        if not moved:
            break
      if os.environ.get("V_A6") == "1":
        for uid, (r_, lo) in cat.items():
            if uid in assign or r_ not in ("A-2", "A-5"):
                continue
            if [v for v in referencers[uid] if v != uid]:
                continue
            refs_k = [assign[v] for v in R[uid] if v in assign and v != uid]
            if refs_k:
                assign[uid], rule[uid] = max(refs_k), "A-6"
      if os.environ.get("V_KEEP") == "1":
        for uid in targets:
            if uid not in assign and U[uid]["file"] in KEEPNUM:
                assign[uid], rule[uid] = KEEPNUM[U[uid]["file"]], "A-K"
      if assign == before:
        break
""", "a6keep")
sub("""    res = {"tool": "move_plan", "command": "plan", "verdict": None,""",
    """    unassigned_refs = {u_: sorted("%s@%s" % (v, modfile[assign[v]] if v in assign else "?") for v in R[u_]) for u_ in unassigned}
    res = {"tool": "move_plan", "command": "plan", "verdict": None, "unassigned_refs": unassigned_refs,""", "res")
open(dst, "w", encoding="utf-8").write(t)
print("variant written", dst)
