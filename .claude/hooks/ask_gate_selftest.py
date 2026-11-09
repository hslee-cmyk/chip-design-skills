#!/usr/bin/env python
"""ask_gate.py self-test: 임시 폴더에 가짜 gate/candidate/validation 을 만들어 실제로 거부하는지 확인."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ask_gate.py")
HDR = "H1"
NUMS = "①②③④⑤⑥⑦⑧⑨"
ITEMS = ["지적 사실", "grep", "원칙", "대안", "실현", "열린 결정", "취지", "원문", "물리", "열째"]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def principles(tmp, n=9, broken=False):
    marks = "".join("%s 항목%d " % (NUMS_ALL[i], i + 1) for i in range(n))
    lines = ["앞줄", "25. 아무거나",
             "26. **보고 5묶음** -- 담는다. 표의 칸은 '실측(경로)'·'agent 인용'·'해당 없음(근거)' 중 하나다. **'안 함'이 있으면 먼저 확인.**",
             "    1. **bkit 단계표**: x", "    2. **단계별 점검표**: x", "    3. **원래 취지와 다름**: x",
             "    4. **권고 실측 출처**: x",
             "    5. **권고 확인표 %d항목**(권고마다): %s" % (n, marks), "27. **끝**"]
    if broken:
        lines = ["앞줄", "26. **보고 5묶음** -- 머리만 있고 하위 목록 없음", "27. 끝"]
    path = os.path.join(tmp, "principles.md")
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return path


NUMS_ALL = "①②③④⑤⑥⑦⑧⑨⑩"


def extra_file(tmp, words=(), measured=None):
    path = os.path.join(tmp, "extra.json")
    d = {"forbidden": ["미측정", "상정 전", "확인 필요", "TODO"] + list(words)}
    if measured:
        d["measured_only"] = measured
    json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    return path


def build(tmp, kind="recommend", mutate_row=None, drop_section=None, cand_ok=True, validation="ok",
          post_edit=False, headers=HDR, reason="r", nrows=9):
    gdir = os.path.join(tmp, "gates")
    os.makedirs(gdir, exist_ok=True)
    for f in os.listdir(gdir):
        os.remove(os.path.join(gdir, f))
    ev = os.path.join(tmp, "ev.txt")
    open(ev, "w").write("x")
    cand = os.path.join(tmp, "cand.md")
    open(cand, "wb").write(b"candidate")
    val = os.path.join(tmp, "val.md")
    rows = []
    for i, n in enumerate(NUMS_ALL[:nrows]):
        last = "실측(%s:12)" % ev.replace("\\", "/")
        row = "| %s | %s | 내용 | %s |" % (n, ITEMS[i], last)
        if mutate_row and mutate_row[0] == i:
            row = mutate_row[1].replace("{N}", n).replace("{EV}", ev.replace("\\", "/"))
        rows.append(row)
    secs = ["## bkit 단계표\nx", "## 단계별 점검표\nx", "## 원래 취지와 다름\nx", "## 권고 실측 출처\nx"]
    if drop_section is not None:
        secs.pop(drop_section)
    body = "\n\n".join(secs) + "\n\n## 권고 확인표: %s\n| # | 항목 | 내용 | 근거 칸 |\n|---|---|---|---|\n" % HDR + "\n".join(rows) + "\n"
    csha = sha(b"candidate") if cand_ok else "0" * 64
    if kind == "clarify":
        fm = "---\nkind: clarify\nheaders: %s\nreason: %s\n---\n" % (headers, reason)
    else:
        fm = ("---\nkind: %s\nheaders: %s\ncandidate_doc: %s\ncandidate_sha256: %s\nvalidation: %s\n---\n"
              % (kind, headers, cand.replace("\\", "/"), csha, val.replace("\\", "/")))
    gate = os.path.join(gdir, "g.md")
    data = (fm + body).encode("utf-8")
    open(gate, "wb").write(data)
    if validation == "ok":
        open(val, "w").write("verdict: Major 0\ngate_sha256: %s\n" % sha(data))
    elif validation == "noverdict":
        open(val, "w").write("gate_sha256: %s\n" % sha(data))
    elif validation == "later_major":
        open(val, "w").write("verdict: Major 0\ngate_sha256: old\nverdict: Major 2\ngate_sha256: %s\n" % sha(data))
    elif validation == "detached":
        open(val, "w").write("verdict: Major 0\ngate_sha256: old\n새 판 메모\ngate_sha256: %s\n" % sha(data))
    elif validation == "reverified":
        open(val, "w").write("verdict: Major 2\ngate_sha256: old\nverdict: Major 0\ngate_sha256: %s\n" % sha(data))
    elif validation == "none":
        pass
    if post_edit:
        open(gate, "ab").write("\n수정".encode("utf-8"))
    return gdir


def run(tmp, gdir, cwd=None, questions=None, tool="AskUserQuestion", pr=None, ex=None, enc=None):
    repo = os.path.join(tmp, "repo")
    os.makedirs(repo, exist_ok=True)
    env = dict(os.environ, ASK_GATE_DIR=gdir, ASK_GATE_REPO=repo, ASK_GATE_BASE=tmp,
               ASK_GATE_PRINCIPLES=pr or principles(tmp), ASK_GATE_EXTRA=ex or extra_file(tmp))
    env.pop("PYTHONIOENCODING", None)
    env.pop("PYTHONUTF8", None)
    if enc:
        env["PYTHONIOENCODING"] = enc
    if questions is None:
        questions = [{"question": "q?", "header": HDR, "options": [{"label": "a", "description": "d"}]}]
    inp = json.dumps({"tool_name": tool, "tool_input": {"questions": questions}, "cwd": cwd or repo})
    p = subprocess.run([sys.executable, HOOK], input=inp.encode("utf-8"), capture_output=True, env=env)
    return p.returncode, p.stderr.decode("utf-8", "replace")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        def check(name, want, got):
            ok = want == got[0]
            results.append(ok)
            print("%-4s %s (기대 %d, 실제 %d)" % ("PASS" if ok else "FAIL", name, want, got[0]))
            if not ok:
                print(got[1])

        g = build(tmp)
        check("1 범위 밖 cwd", 0, run(tmp, g, cwd=tempfile.gettempdir()))
        empty = os.path.join(tmp, "empty")
        os.makedirs(empty, exist_ok=True)
        check("2 점검 파일 없음", 2, run(tmp, empty))
        g = build(tmp, mutate_row=(3, "| {N} | 대안 | 안 함 | 실측({EV}) |"))
        check("3 '안 함'", 2, run(tmp, g))
        g = build(tmp, mutate_row=(3, "| {N} | 대안 |  | 실측({EV}) |"))
        check("4 빈 칸", 2, run(tmp, g))
        g = build(tmp, mutate_row=(3, "| {N} | 대안 | 내용 | 그냥 봤음 |"))
        check("5 근거 칸 접두 불허", 2, run(tmp, g))
        g = build(tmp, mutate_row=(3, "| {N} | 대안 | 내용 | 실측(C:/nonexistent_zz/none.py:3) |"))
        check("6 없는 경로", 2, run(tmp, g))
        g = build(tmp, cand_ok=False)
        check("7 candidate sha 불일치", 2, run(tmp, g))
        g = build(tmp, validation="none")
        check("8a validation 없음", 2, run(tmp, g))
        g = build(tmp, validation="noverdict")
        check("8b verdict 없음", 2, run(tmp, g))
        g = build(tmp, post_edit=True)
        check("9 gate_sha256 불일치", 2, run(tmp, g))
        g = build(tmp, validation="later_major")
        check("9a 앞 Major 0 + 마지막 Major 2", 2, run(tmp, g))
        g = build(tmp, validation="detached")
        check("9b 옛 Major 0 + 새 sha 따로", 2, run(tmp, g))
        g = build(tmp, validation="reverified")
        check("9c 앞 Major 2 + 재판정 Major 0", 0, run(tmp, g))
        g = build(tmp, kind="clarify")
        qs = [{"question": "q", "header": HDR, "options": [{"label": "a (Recommended)", "description": "d"}]}]
        check("10 clarify + (Recommended)", 2, run(tmp, g, questions=qs))
        check("11 clarify 정상", 0, run(tmp, g))
        g = build(tmp, kind="clarify", reason="")
        check("11b clarify reason 없음", 2, run(tmp, g))
        g = build(tmp)
        check("12 recommend 정상", 0, run(tmp, g))
        g = build(tmp, drop_section=2)
        check("13 절 하나 빠짐", 2, run(tmp, g))
        g = build(tmp)
        qs = [{"question": "q", "header": "OTHER", "options": [{"label": "a", "description": "d"}]}]
        check("14 header 집합 불일치", 2, run(tmp, g, questions=qs))
        g = build(tmp, mutate_row=(3, "| {N} | 대안 | 내용 | 해당 없음() |"))
        check("15 해당 없음 근거 비어 있음", 2, run(tmp, g))
        g = build(tmp, mutate_row=(3, "| {N} | 대안 | 내용 | 해당 없음(취지와 같음) |"))
        check("16 해당 없음 정상", 0, run(tmp, g))
        # 추가: 원칙 26 에서 유도
        p10 = principles(tmp, n=10)
        g = build(tmp, nrows=9)
        check("17a 원칙에 ⑩ 추가 + ⑩ 없는 점검 파일", 2, run(tmp, g, pr=p10))
        g = build(tmp, nrows=10)
        check("17b 원칙에 ⑩ 추가 + ⑩ 있는 점검 파일", 0, run(tmp, g, pr=p10))
        g = build(tmp)
        check("18 원칙 블록 형식 깨짐", 2, run(tmp, g, pr=principles(tmp, broken=True)))
        r = run(tmp, g, pr=principles(tmp, broken=True))
        ok = r[0] == 2 and "원칙 26 형식" in r[1]
        results.append(ok)
        print("%-4s 18b 거부 메시지에 '원칙 26 형식' 명시" % ("PASS" if ok else "FAIL"))
        for enc in (None, "cp949", "utf-8"):
            r = run(tmp, g, pr=principles(tmp, broken=True), enc=enc)
            ok = r[0] == 2 and "원칙 26 형식" in r[1]
            results.append(ok)
            print("%-4s 18c PYTHONIOENCODING=%s 에서도 한글 사유 정상" % ("PASS" if ok else "FAIL", enc))
        g = build(tmp, mutate_row=(3, "| {N} | 대안 | 새금지어 포함 | 실측({EV}) |"))
        check("19a extra 에 없는 단어는 통과", 0, run(tmp, g))
        check("19b extra.json 에 금지어 추가 -> 거부", 2, run(tmp, g, ex=extra_file(tmp, ["새금지어"])))
        # measured_only: 결정 간 모순 점검처럼 '해당 없음'이 불가한 행
        mo = {"⑩": "점검 기록 필요"}
        g = build(tmp, nrows=10, mutate_row=(9, "| {N} | 열째 | 내용 | 해당 없음(관련 결정 없음) |"))
        check("20a measured_only 행 '해당 없음' -> 거부", 2, run(tmp, g, pr=principles(tmp, n=10), ex=extra_file(tmp, measured=mo)))
        g = build(tmp, nrows=10, mutate_row=(9, "| {N} | 열째 | 내용 | agent 인용 |"))
        check("20b measured_only 행 'agent 인용'만 -> 거부", 2, run(tmp, g, pr=principles(tmp, n=10), ex=extra_file(tmp, measured=mo)))
        g = build(tmp, nrows=10, mutate_row=(9, "| {N} | 열째 | 내용 | 실측(눈으로 봄) |"))
        check("20c measured_only 행 실측이나 경로 없음 -> 거부", 2, run(tmp, g, pr=principles(tmp, n=10), ex=extra_file(tmp, measured=mo)))
        g = build(tmp, nrows=10)
        check("20d measured_only 행 실측(실재 경로) -> 통과", 0, run(tmp, g, pr=principles(tmp, n=10), ex=extra_file(tmp, measured=mo)))
        g = build(tmp, nrows=9)
        check("20e measured_only 항목이 원칙 목록에 없음 -> 거부", 2, run(tmp, g, ex=extra_file(tmp, measured=mo)))
    print("ALL PASS" if all(results) else "SOME FAIL")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
