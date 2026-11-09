#!/usr/bin/env python3
"""t0_quote_check.py 자기 시험(review_t0_carry S1·m1·S2 + review_t0_carry_r1 S1·m1 거부 사례 + 실제 답 수용 전수).

  python t0_quote_check_test.py <모래상자 작업 폴더(/c/g<번호>/...)> <프로젝트 jsonl 폴더(읽기만, 하위 폴더까지)> <결과 파일>
모래상자 폴더 안 j/에 W-1 세션 jsonl 사본 + 가짜 V5 AskUserQuestion jsonl을 만든다(실제 jsonl은 읽기만).
결과는 케이스마다 결과 파일에 append(중간에 죽어도 남는다). 실패 1건이라도 있으면 exit 1.
"""
import glob
import hashlib
import re
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import t0_quote_check as qc  # noqa: E402

SB, JPROJ, OUT = sys.argv[1:4]
assert re.match(r"^(c:|/c)/g\d+(/|$)", os.path.abspath(SB).replace("\\", "/").lower()), SB
W1_JSONL = "63c6146a-ab1d-4035-a169-bae810986922.jsonl"
W1_TOOLU = "toolu_01GVLKut4JY6FMvvZJEvhKS4"
TEMPLATE = os.path.join(HERE, "approval_20260930-p3-tests-location-free.md")
PIN = None
for l in open(os.path.join(HERE, "t0_carry.sh"), encoding="utf-8"):
    if l.startswith("T0_DRAFT_SHA256="):
        PIN = l.split("=", 1)[1].strip()
assert PIN and len(PIN) == 64

fails = []
n_ok = 0


def log(s):
    with open(OUT, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(s + "\n")
    print(s)


def expect(name, fn, should_pass, pat=None):
    global n_ok
    try:
        fn()
        got, msg = True, ""
    except AssertionError as e:
        got, msg = False, repr(e.args[0] if e.args else e)[:200]
    ok = got == should_pass and (should_pass or pat is None or pat in msg)
    n_ok += ok
    if not ok:
        fails.append(name)
    log("%s [%s] %s %s" % ("OK  " if ok else "FAIL", "수용" if should_pass else "거부", name, msg))


# ---- 모래상자 jsonl 폴더: W-1 세션 사본 + 가짜 V5
J = os.path.join(SB, "j")
os.makedirs(J, exist_ok=True)
shutil.copyfile(os.path.join(JPROJ, W1_JSONL), os.path.join(J, W1_JSONL))
V5_TOOLU = "toolu_01FakeV5Sandbox0000000001"
# 보관 V5 질문 재료 대역(archive의 v5_question.txt 모양 -- 끝 줄바꿈 포함), target 해시, archive 끝 시각(UTC)
DH = "0123abcd" * 8
V5Q_ARCH = ("T0 V5 질문 재료 -- 1차 시도 base B1 %s, test 끝 T1 %s\ndiff_hash(target) %s\ndiff_paths:\n  skills/x.py\n"
            "발견(경로 / 단위 / 패턴 / 내용):\n  skills/x.py / u / compare-weaken / a < b\n" % ("b" * 40, "c" * 40, DH))
ARCH_AT = "2026-10-06T11:00:00Z"
V5_Q = "[V5] T0 1차 시도 V5 발견(아래)을 승인 기록 target으로 운반할까요?\n\n" + V5Q_ARCH.rstrip("\n") + "\n\n(card 범위 문장)"
V5_OPTS = [qc.V5_APPROVE_LABEL, qc.V5_REJECT_LABEL]
V5_A = V5_OPTS[0]
V5_TS = "2026-10-06T11:05:30.123Z"                       # KST 2026-10-06 20:05
V5_AT = "2026-10-06 20:05 KST"


def fake_session(name, tu, q, opts, ans, ts):
    with open(os.path.join(J, name), "w", encoding="utf-8", newline="\n") as fh:
        qs = [{"question": q, "header": "V5", "multiSelect": False, "options": [{"label": o, "description": "d"} for o in opts]}]
        fh.write(json.dumps({"type": "assistant", "timestamp": ts, "message": {"role": "assistant", "content": [
            {"type": "tool_use", "id": tu, "name": "AskUserQuestion", "input": {"questions": qs}}]}}, ensure_ascii=False) + "\n")
        fh.write(json.dumps({"type": "user", "timestamp": ts, "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": tu,
             "content": 'Your questions have been answered: "%s"="%s". You can now continue with these answers in mind.' % (q, ans)}]},
            "toolUseResult": {"questions": qs, "answers": {q: ans}}}, ensure_ascii=False) + "\n")


fake_session("fakev5-session.jsonl", V5_TOOLU, V5_Q, V5_OPTS, V5_A, V5_TS)
# X2: 사용자가 실제로 '거부'를 고른 세션 / 선택지 label이 정본 상수와 다른 세션(사용자는 그 '승인' 모양을 고름) / archive 전에 물은 세션
fake_session("fakev5-reject.jsonl", "toolu_01FakeV5Reject00000000001", V5_Q, V5_OPTS, qc.V5_REJECT_LABEL, V5_TS)
fake_session("fakev5-label.jsonl", "toolu_01FakeV5Label000000000001", V5_Q, ["승인 (Recommended)", qc.V5_REJECT_LABEL], "승인 (Recommended)", V5_TS)
fake_session("fakev5-early.jsonl", "toolu_01FakeV5Early000000000001", V5_Q, V5_OPTS, V5_A, "2026-10-06T10:59:59.999Z")

# W-1 batch의 실제 질문·답(같은 tool_use 안 D-11 포함)
w1_qs, w1_ans, _ = qc.load_ask(os.path.join(J, W1_JSONL), W1_TOOLU)
W1_Q = [q for q in w1_qs if q.startswith("[W-1]")][0]
D11_Q = [q for q in w1_qs if q.startswith("[D-11]")][0]
W1_A, D11_A = w1_ans[W1_Q], w1_ans[D11_Q]
assert W1_A == "(가) T0에서 test import 수정 (Recommended)", W1_A

tmpl = open(TEMPLATE, "rb").read().decode("utf-8")


def quote(s):
    return "\n".join("> " + l if l else ">" for l in s.split("\n"))


def fill(v5_q=V5_Q, v5_a=V5_A, v5_tu=V5_TOOLU, v5_jn="fakev5-session.jsonl", w1_a=None, w1_q=None, t=None, v5_at=V5_AT):
    t = tmpl if t is None else t
    for k, v in (("<DATE>", "2026-10-06"), ("<V5_ASKED_AT>", v5_at), ("<V5_JSONL_NAME>", v5_jn), ("<V5_TOOLU>", v5_tu)):
        assert t.count(k) == 1
        t = t.replace(k, v)
    t = t.replace("> <V5_QUESTION>", quote(v5_q)).replace("> <V5_ANSWER>", quote(v5_a))
    if w1_a is not None:
        assert t.count("\n> " + W1_A + "\n") == 1
        t = t.replace("\n> " + W1_A + "\n", "\n" + quote(w1_a) + "\n")
    if w1_q is not None:
        assert t.count("\n> " + W1_Q + "\n") == 1
        t = t.replace("\n> " + W1_Q + "\n", "\n" + quote(w1_q) + "\n")
    return t


def chk(t):
    return lambda: qc.check_quotes(t, J)


def rec(t, v5q=V5Q_ARCH, dh=DH, aat=ARCH_AT):
    return lambda: qc.check_record(t, J, v5q, dh, aat)


def pin_ok(t):
    def f():
        h = hashlib.sha256(qc.canon(t).encode("utf-8")).hexdigest()
        assert h == PIN, ("핀 불일치", h)
    return f


log("== t0_quote_check 자기 시험 (%s)" % OUT)
# ---- 수용
expect("정상: V5(가짜 세션, 여러 줄 질문) + W-1 실제 답 -- check_quotes", chk(fill()), True)
expect("정상: V5 = 이 target·승인 label·archive 뒤·V5_ASKED_AT 일치 -- check_record", rec(fill()), True)
expect("정상: 보관 재료 끝 줄바꿈 없이 넘겨도 같은 판정", rec(fill(), v5q=V5Q_ARCH.rstrip("\n")), True)
# ---- review_t0_carry_r1 S1·m1 거부(V5 블록을 이 target·승인 선택지에 묶기). 옛 115행 '정상: V5 자리에 실제 D-11' 수용 -> X1 거부로 바꿈
X1 = fill(v5_q=D11_Q, v5_a=D11_A, v5_tu=W1_TOOLU, v5_jn=W1_JSONL, v5_at="2026-10-02 13:35 KST")
expect("X1 V5 자리에 실제 D-11(같은 batch, W-1 세션) 질문·답 -- 인용 자체는 원문과 같다(check_quotes 통과)", chk(X1), True)
expect("X1 V5 자리에 실제 D-11 질문·답 -- check_record 거부(보관 질문 재료 없음)", rec(X1), False, "v5_question.txt")
expect("X2 사용자가 실제로 '거부 -- 운반하지 않음'을 고름(인용은 원문 그대로)", rec(fill(v5_a=qc.V5_REJECT_LABEL, v5_tu="toolu_01FakeV5Reject00000000001", v5_jn="fakev5-reject.jsonl")), False, "승인 선택지 label")
expect("X3 V5_ASKED_AT 자리에 산문 한 줄", rec(fill(v5_at="질문은 오늘 저녁에 했다")), False, "형식")
expect("m1 V5_ASKED_AT 형식은 맞지만 timestamp KST 분과 다름(UTC 그대로 적음)", rec(fill(v5_at="2026-10-06 11:05 KST")), False, "timestamp(KST 분)")
expect("선택지 label이 정본 상수와 다름('승인 (Recommended)')", rec(fill(v5_a="승인 (Recommended)", v5_tu="toolu_01FakeV5Label000000000001", v5_jn="fakev5-label.jsonl")), False, "V5_APPROVE_LABEL")
expect("V5 질문이 archive 끝 시각 전", rec(fill(v5_tu="toolu_01FakeV5Early000000000001", v5_jn="fakev5-early.jsonl", v5_at="2026-10-06 19:59 KST")), False, "archive 끝 시각")
expect("다른 target 해시(보관 재료 diff_hash 줄과 다름)", rec(fill(), dh="f" * 64), False, "diff_hash(target)")
expect("보관 재료가 질문과 한 바이트 다름(발견 한 줄 변조)", rec(fill(), v5q=V5Q_ARCH.replace("a < b", "a <= b")), False, "v5_question.txt")
# ---- 거부(review_t0_carry S1 네 사례 + 보강)
expect("S1-a V5 답 = 고르지 않은 선택지 '거부 -- 운반하지 않음'", chk(fill(v5_a=V5_OPTS[1])), False, "사용자가 고른 답")
expect("S1-b V5 답 = 잘린 '승인'", chk(fill(v5_a="승인")), False, "사용자가 고른 답")
expect("S1-c W-1 답 = 같은 batch D-11의 답", chk(fill(w1_a=D11_A)), False, "사용자가 고른 답")
expect("S1-d W-1 답 = 고르지 않은 '(나) shim에 기존 import 허용'", chk(fill(w1_a="(나) shim에 기존 import 허용")), False, "사용자가 고른 답")
expect("지어낸 V5 답", chk(fill(v5_a="승인 (Recommended) -- 꾸민 답")), False, "사용자가 고른 답")
expect("W-1 질문 한 글자 변조", chk(fill(w1_q=W1_Q.replace("어떻게", "어떡게"))), False, "질문 인용")
expect("V5 블록을 W-1 toolu에 묶고 V5 질문 인용(다른 toolu의 질문)", chk(fill(v5_tu=W1_TOOLU, v5_jn=W1_JSONL)), False, "질문 인용")
expect("V5 블록이 적은 jsonl 이름이 없는 파일", chk(fill(v5_jn="nosuch.jsonl")), False, "세션 jsonl이 없다")
expect("V5 질문 인용 앞부분만(여러 줄 중 첫 줄)", chk(fill(v5_q=V5_Q.split("\n")[0])), False, "질문 인용")
t_stray = fill().replace("\n## 범위 설명", "\n> (가) T0에서 test import 수정 (Recommended)\n\n## 범위 설명")
expect("절 끝 떠도는 인용 줄 = W-1 답 반복(마지막 블록 답에 붙음 -> 불일치)", chk(t_stray), False, "사용자가 고른 답")
t_noans = fill().replace("답:\n\n> " + W1_A + "\n", "")
expect("W-1 블록 '답:'·답 인용 없음", chk(t_noans), False, "답")
# ---- m1 산문 핀
expect("핀: 채우기 전 초안 canon = 핀", pin_ok(tmpl), True)
expect("핀: 채운 초안 canon = 핀", pin_ok(fill()), True)
expect("핀: 여러 줄 V5 답도 canon = 핀", pin_ok(fill(v5_a="첫 줄\n둘째 줄")), True)
expect("핀: '기대값 불변(계약 5)' -> '기대값 변경 허용'", pin_ok(fill(t=tmpl.replace("기대값 불변(계약 5)", "기대값 변경 허용"))), False, "핀 불일치")
expect("핀: W-1 답 인용 변조(산문 쪽)", pin_ok(fill(w1_a="(나) shim에 기존 import 허용")), False, "핀 불일치")
expect("핀: 끝에 </content> 줄 덧붙임", pin_ok(fill() + "</content>\n"), False, "핀 불일치")
expect("핀: V5 머리 줄 산문 변조('고치지 않고 그대로' 삭제)", pin_ok(fill().replace("원문(고치지 않고 그대로):", "원문:")), False, "V5 인용 블록")

# ---- 실제 답 전수 수용: 프로젝트 폴더 모든 jsonl의 AskUserQuestion 질문마다 블록 하나를 만들어 check_quotes(jsonl은 읽기만)
sweep = 0
sweep_fail = []
n_ts = 0
for jp in sorted(glob.glob(os.path.join(JPROJ, "**", "*.jsonl"), recursive=True)):
    ids = []
    with open(jp, encoding="utf-8") as fh:
        for line in fh:
            if '"AskUserQuestion"' not in line:
                continue
            o = json.loads(line)
            c = (o.get("message") or {}).get("content")
            if isinstance(c, list):
                ids += [b["id"] for b in c if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "AskUserQuestion"]
    for tu in ids:
        try:
            ub, ts, ans, _ = qc._read_ask(jp, tu)
        except AssertionError as e:
            log("     (전수 건너뜀: %s %s -- 답 없음/중단된 질문: %r)" % (os.path.basename(jp)[:8], tu, e.args[0][0] if e.args else e))
            continue
        qs = [q["question"] for q in ub["input"]["questions"]]
        try:                                   # m1: 실제 tool_use 줄 timestamp가 모두 V5_ASKED_AT 형식으로 바뀌는가
            assert qc.ASKED_AT_RE.fullmatch(qc.asked_at_kst(ts)), ts
            n_ts += 1
        except (AssertionError, ValueError, TypeError) as e:
            sweep_fail.append((os.path.basename(jp)[:8], tu, "timestamp", repr(e)[:160]))
        for q in qs:
            if q not in ans:
                continue
            sec = "## 사용자 원문\n\n질문(세션 jsonl `%s` AskUserQuestion `%s`):\n\n%s\n\n답:\n\n%s\n\n## 끝\n" % (os.path.basename(jp), tu, quote(q), quote(ans[q]))
            sweep += 1
            try:
                qc.check_quotes(sec, os.path.dirname(jp))
            except AssertionError as e:
                sweep_fail.append((os.path.basename(jp)[:8], tu, q[:40], repr(e)[:160]))
log("== 실제 답 전수 수용: 질문 %d개(tool_use timestamp -> KST %d개), 거부 %d개" % (sweep, n_ts, len(sweep_fail)))
for f in sweep_fail:
    log("FAIL 전수 %r" % (f,))
if sweep_fail or sweep == 0:
    fails.append("전수")
log("== 결과: 사례 %d/%d OK, 전수 %d/%d 수용 -> %s" % (n_ok, n_ok + len([f for f in fails if f != "전수"]), sweep - len(sweep_fail), sweep, "PASS" if not fails else "FAIL %s" % fails))
sys.exit(1 if fails else 0)
