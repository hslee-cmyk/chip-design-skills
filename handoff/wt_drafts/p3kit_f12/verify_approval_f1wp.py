"""승인 초안 approval_20261002-p3-f1-workspaces-write-path.md 검사 r2(측정 전용):
두 AskUserQuestion 문답([F1] 쓰기 경로 / [F1] 경로 재확인)의 인용 문자열이 세션 jsonl과 바이트 같음, 사용자에게 보인 메시지 id·시각,
머리가 gate merge_gate.parse_approval_header로 파싱됨, 좁힌 두 행으로 해시 재계산·read_plan_tables 불변.

    python -B verify_approval_f1wp.py <gate tools/gates 경로> <복제본 루트>
"""
import json
import re
import subprocess
import sys

GATES, ROOT = sys.argv[1:3]
sys.path.insert(0, GATES)
import merge_gate as mg  # noqa: E402
import role_paths as rp  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
J = r"C:/Users/HSLEE/.claude/projects/C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills/63c6146a-ab1d-4035-a169-bae810986922.jsonl"
DR = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/approval_20261002-p3-f1-workspaces-write-path.md"
raw = open(DR, "rb").read()
doc = raw.decode("utf-8")
L = open(J, encoding="utf-8").read().split("\n")
HEADERS = {"[F1] 쓰기 경로": ("toolu_01PokFaLT31S8ep6tYfPQJmx", "c5b9d12d-5d65-4d05-a940-466ba20d30e2", "2026-10-02T05:30:10.108Z",
                           "fe2c1b04-1a26-4c79-83ee-af5c68933e35", "2026-10-02T05:32:16.443Z"),
           "[F1] 경로 재확인": ("toolu_01QeEYjVgV4ChhaRaJcxgouH", "2dd719f8-7d40-4cfa-aeff-835d8c50cc84", "2026-10-02T08:16:33.022Z",
                            "c2a335c6-b4fc-42a1-bdac-4d834585f82d", "2026-10-02T08:18:56.717Z")}
asks, results, texts, resblocks = {h: [] for h in HEADERS}, {}, {}, {}
for line in L:
    if not line:
        continue
    o = json.loads(line)
    m = o.get("message") or {}
    c = m.get("content")
    if not isinstance(c, list):
        continue
    for b in c:
        if not isinstance(b, dict):
            continue
        if b.get("type") == "tool_use" and b.get("name") == "AskUserQuestion":
            for h in HEADERS:
                if any(q.get("header") == h for q in b["input"]["questions"]):
                    asks[h].append((o["uuid"], o["timestamp"], b["id"], b["input"], o.get("isSidechain")))
        if b.get("type") == "tool_result":
            results[b.get("tool_use_id")] = (o["uuid"], o["timestamp"], o.get("toolUseResult"))
            resblocks[b.get("tool_use_id")] = b.get("content")
        if b.get("type") == "text" and o.get("type") == "assistant" and not o.get("isSidechain"):
            texts[o["uuid"]] = (o["timestamp"], b["text"])
ok = True


def chk(label, cond):
    global ok
    ok &= bool(cond)
    print(("OK  " if cond else "BAD ") + label)


chk("BOM·CRLF 없음", not raw.startswith(b"\xef\xbb\xbf") and b"\r" not in raw)
for h, (tid0, uuid0, ts0, ru0, rts0) in HEADERS.items():
    chk("[%s] AskUserQuestion 정확히 1건, 사이드체인 아님" % h, len(asks[h]) == 1 and not asks[h][0][4])
    uuid, ts, tid, inp, _sc = asks[h][0]
    q = inp["questions"][0]
    chk("[%s] tool_use id/uuid/ts" % h, (tid, uuid, ts) == (tid0, uuid0, ts0) and ("`%s`" % tid0) in doc and ("`%s`" % uuid0) in doc and ("`%s`" % ts0) in doc)
    chk("[%s] 질문 1개·multiSelect false" % h, len(inp["questions"]) == 1 and q["multiSelect"] is False)
    chk("[%s] 질문 원문 인용" % h, ('질문 원문: "%s"' % q["question"]) in doc)
    for op in q["options"]:
        chk("[%s] 선택지 라벨·설명 %s" % (h, op["label"][:8]), ('"%s" -- "%s"' % (op["label"], op["description"])) in doc)
    ru, rts, tur = results[tid]
    ans = list(tur["answers"].values())
    chk("[%s] tool_result uuid/ts" % h, (ru, rts) == (ru0, rts0) and ("`%s`" % ru0) in doc and ("`%s`" % rts0) in doc)
    chk("[%s] tool_result 질문·선택지 = tool_use" % h, tur["questions"][0]["question"] == q["question"] and tur["questions"][0]["options"] == q["options"])
    chk("[%s] 답 1개 = 인용" % h, len(ans) == 1 and ('답: "%s"' % ans[0]) in doc and tur.get("annotations") == {})
    chk("[%s] tool_result 본문에 같은 답" % h, ('"=\\"%s\\"' % ans[0]) in json.dumps(resblocks[tid], ensure_ascii=False))
ans2 = list(results["toolu_01QeEYjVgV4ChhaRaJcxgouH"][2]["answers"].values())[0]
chk("사용자 원문 블록 = 둘째 답", ("## 사용자 원문\n\n> %s\n" % ans2) in doc)
# 사용자에게 보인 메시지
t = texts["b7855051-7ee7-42a9-be08-2aec3e6f2792"]
line = "- **workspaces 스크립트 16개**: 역할 커밋의 쓰기 경로 밖에 있습니다. 초안의 기본안은 F1 전에 제가 역할 밖 커밋으로 고치는 것입니다."
chk("04:56 메시지 줄 = jsonl", t[0] == "2026-10-02T04:56:52.742Z" and (line + "\n") in t[1] and ("```text\n" + line + "\n```") in doc)
prev1 = [u for u, (tt, _x) in texts.items() if "2026-10-02T05:18:43" <= tt < HEADERS["[F1] 쓰기 경로"][2]]
chk("첫 질문 앞 마지막 텍스트 = f3a5cc43 하나", prev1 == ["f3a5cc43-a112-4a70-923b-c49c3f095691"])
prev2 = [u for u, (tt, _x) in texts.items() if "2026-10-02T08:15:38" <= tt < HEADERS["[F1] 경로 재확인"][2]]
chk("둘째 질문 앞 마지막 텍스트 = d9afd326 하나", prev2 == ["d9afd326-85fd-479c-9bfa-de5f086e90d1"] and texts[prev2[0]][0] == "2026-10-02T08:15:38.969Z")
after = texts.get("f3c7a869-c255-4455-951e-53a98aad33a0")
chk("답 뒤 대체 알림 08:19:58 = jsonl", after and after[0] == "2026-10-02T08:19:58.614Z"
    and "앞서 고르신 \"(가) 쓰기 경로표에 행 추가\"를 이 답으로 대체합니다" in after[1])
between = [u for u, (tt, _x) in texts.items() if HEADERS["[F1] 경로 재확인"][2] < tt < "2026-10-02T08:19:58.614Z"]
chk("둘째 질문~답 알림 사이 다른 텍스트 0", between == [])
# 머리 파싱 + 해시
hdr = mg.parse_approval_header(raw, ".ai/approvals/20261002-p3-f1-workspaces-write-path.md")
chk("머리 파싱 plan_tables", hdr["target_kind"] == "plan_tables")
P = "docs/01-plan/features/gain-budget-gmid-sizing.plan.md"
base = subprocess.run(["git", "-C", ROOT, "show", "4a286f0:" + P], capture_output=True).stdout.decode("utf-8")
row = "| gmid-code-author | `workspaces/run_harness.py` | -- | 없음 |\n"
new = ("| gmid-code-author | `workspaces/current-reuse-telescopic-ota-report/*.py` | -- | 없음 |\n"
       "| gmid-code-author | `workspaces/two-stage-ota-report/*.py` | -- | 없음 |\n")
chk("앵커 행 1개, 602행", base.count(row) == 1 and base.split("\n").index(row.rstrip("\n")) + 1 == 602)
aft = base.replace(row, row + new)
chk("해시 전 7167e028…", mg.plan_tables_hash(base) == "7167e02839f86c4ecbcd91a63a9833c4d83a8aab8008bfe2d8cfc36206d2596d")
chk("해시 뒤 = target", mg.plan_tables_hash(aft) == hdr["target"] == "16b899d1c745ddd0d305b2a977eecc74b0c830d89507d7eb3476b7323a08aec1")
chk("read_plan_tables 불변", mg.read_plan_tables_text(aft) == mg.read_plan_tables_text(base))
chk("쓰기 경로표 68 → 70", (len(rp.read_write_paths(base)), len(rp.read_write_paths(aft))) == (68, 70))
for r in new.rstrip("\n").split("\n"):
    chk("새 행 원문 인용 %s" % r[22:60], ("`` " + r + " ``") in doc)
chk("넓은 행(`workspaces/*/**/*.py`)을 새 행으로 쓰지 않음", "`` | gmid-code-author | `workspaces/*/**/*.py`" not in doc)
print("ALL OK" if ok else "SOME BAD")
