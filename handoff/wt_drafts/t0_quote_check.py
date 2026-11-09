#!/usr/bin/env python3
"""T0 V5 승인 기록 -- 초안 산문 핀(canon)과 '## 사용자 원문' 인용 대조(check_quotes). t0_carry.sh records가 import해서 쓴다.

review_t0_carry S1·m1(2026-10-06). 선례: b26_1_kit_selftest/fill_u3.py check_jsonl(답 = toolUseResult.answers[질문] 전체 일치).

check_quotes(text, jdir):
  '## 사용자 원문' 절 = 인용 블록의 나열. 블록 = 머리 줄(세션 jsonl `<이름>`과 toolu id를 정확히 하나씩) -> '> ' 질문 줄(1개 이상)
  -> '답:' -> '> ' 답 줄(1개 이상). 절 안의 다른 비어 있지 않은 줄은 거부한다(떠도는 인용 금지).
  블록마다 **자기** jsonl(jdir/<이름>)의 **자기** toolu에만 묶는다:
    질문 = 그 tool_use(name AskUserQuestion) input.questions[].question 중 정확히 하나와 전체 일치,
    답   = 그 tool_use의 tool_result 줄 toolUseResult.answers[질문]과 전체 일치(부분 문자열·다른 질문의 답·고르지 않은 선택지 거부),
    덧붙여 tool_result 문자열에 '"질문"="답"'이 있어야 한다(같은 줄 두 표현의 교차 확인).
check_record(text, jdir, v5q, dh, archived_at)  -- review_t0_carry_r1 S1·m1: check_quotes + V5 블록을 **이 target·승인 선택지**에 묶는다:
  V5 블록(canon이 고르는 V5 머리 줄 블록 = 절의 첫 블록) 질문 인용이 보관 질문 재료 v5q($ADIR/v5_question.txt, sums_ok 통과본) 전체를
  부분 문자열로 담고 그 안에 'diff_hash(target) <dh>' 줄이 있다, 답 = V5_APPROVE_LABEL이고 그 질문의 선택지 label에 있다,
  V5 tool_use 줄 timestamp(UTC) > archived_at(archive 끝 시각, UTC ISO), V5_ASKED_AT = 'YYYY-MM-DD HH:MM KST' 형식이고 그 timestamp의 KST 분과 같다.
  V5 선택지 label 두 개(V5_APPROVE_LABEL·V5_REJECT_LABEL)는 이 파일이 정본 -- t0_carry.sh archive가 `labels`로 꺼내 $ADIR/v5_options.txt에 쓴다.
canon(text):
  초안의 오케스트레이터 자리(date·V5 머리 줄 세 자리·V5 질문·V5 답)만 자리표시로 되돌린 텍스트 -- 그 sha256을 t0_carry.sh의
  T0_DRAFT_SHA256 핀과 대조한다(자리 밖 산문 변경 = 핀 불일치). 채우기 전 초안은 canon(t) == t.
"""
import datetime
import json
import os
import re
import sys

# V5 질문 선택지 label 정본(질문 생성 = t0_carry.sh archive의 v5_options.txt, 검사 = check_record가 같은 상수를 쓴다)
V5_APPROVE_LABEL = "승인 -- 이 target으로 운반한다"
V5_REJECT_LABEL = "거부 -- 운반하지 않음"
KST = datetime.timezone(datetime.timedelta(hours=9))
ASKED_AT_RE = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2} KST")

ID_RE = re.compile(r"toolu_[A-Za-z0-9]+")
JN_RE = re.compile(r"세션 jsonl `([A-Za-z0-9][A-Za-z0-9._-]*\.jsonl)`")
V5_BLOCK_RE = re.compile(
    r"(?m)^V5 질문\((?P<at>[^\n]+?), 세션 jsonl `(?P<jn>[^\n`]+)` AskUserQuestion `(?P<tu>[^\n`]+)`\) 원문\(고치지 않고 그대로\):\n"
    r"\n(?P<q>(?:>(?: [^\n]*)?\n)+)\n답:\n\n(?P<a>(?:>(?: [^\n]*)?\n)+)\n(?=\[W-1\]\()")
V5_CANON = ("V5 질문(<V5_ASKED_AT>, 세션 jsonl `<V5_JSONL_NAME>` AskUserQuestion `<V5_TOOLU>`) 원문(고치지 않고 그대로):\n"
            "\n> <V5_QUESTION>\n\n답:\n\n> <V5_ANSWER>\n\n")


def canon(t):
    assert "\r" not in t and not t.startswith("﻿"), "CR·BOM"
    t2, n = re.subn(r"(?m)^date: [^\n]*$", "date: <DATE>", t, count=1)
    assert n == 1, "date: 줄 없음"
    ms = list(V5_BLOCK_RE.finditer(t2))
    assert len(ms) == 1, ("V5 인용 블록 모양(머리 줄·질문·답:·답, 바로 뒤 [W-1])이 정확히 하나가 아니다", len(ms))
    m = ms[0]
    return t2[:m.start()] + V5_CANON + t2[m.end():]


def _unquote(lines):
    return "\n".join(l[2:] if l.startswith("> ") else "" for l in lines)


def parse_blocks(text):
    sec = re.search(r"(?ms)^## 사용자 원문\n(.*?)(?=^## |\Z)", text)
    assert sec, "## 사용자 원문 절이 없다"
    blocks, cur, state = [], None, None
    for l in sec.group(1).split("\n"):
        if not l.strip():
            continue
        isq = l == ">" or l.startswith("> ")
        if not isq and l != "답:":
            ids = ID_RE.findall(l)
            jns = JN_RE.findall(l)
            assert len(ids) == 1 and len(jns) == 1, ("인용 블록 머리 줄이 아니다(toolu id·세션 jsonl 이름이 정확히 하나씩)", l[:100])
            assert state in (None, "a"), ("앞 블록이 '답:'·답 인용 없이 끝났다", l[:100])
            cur = {"toolu": ids[0], "jsonl": jns[0], "q": [], "a": []}
            blocks.append(cur)
            state = "head"
        elif l == "답:":
            assert state == "q", ("'답:' 앞에 질문 인용이 없다", cur and cur["toolu"])
            state = "ans"
        elif state in ("head", "q"):
            cur["q"].append(l); state = "q"
        elif state in ("ans", "a"):
            cur["a"].append(l); state = "a"
        else:
            raise AssertionError(("블록에 묶이지 않은 인용 줄", l[:100]))
    assert blocks, "인용 블록이 없다"
    assert state == "a", "마지막 블록에 답 인용이 없다"
    for b in blocks:
        b["q"] = _unquote(b["q"]); b["a"] = _unquote(b["a"])
    return blocks


def _content_text(c):
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "\n".join(x.get("text", "") for x in c if isinstance(x, dict))
    return ""


def _read_ask(jpath, toolu):
    """jsonl에서 그 toolu의 AskUserQuestion tool_use 블록·그 줄 timestamp, answers, tool_result 문자열(각각 정확히 하나)."""
    uses, results = [], []
    with open(jpath, encoding="utf-8") as fh:
        for line in fh:
            if toolu not in line:
                continue
            o = json.loads(line)
            c = (o.get("message") or {}).get("content")
            if not isinstance(c, list):
                continue
            for b in c:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "tool_use" and b.get("id") == toolu:
                    uses.append((b, o.get("timestamp")))
                if b.get("type") == "tool_result" and b.get("tool_use_id") == toolu:
                    results.append((b, o.get("toolUseResult")))
    assert len(uses) == 1, ("jsonl에 그 tool_use가 정확히 하나가 아니다", os.path.basename(jpath), toolu, len(uses))
    ub, ts = uses[0]
    assert ub.get("name") == "AskUserQuestion", ("AskUserQuestion이 아니다", toolu, ub.get("name"))
    assert len(results) == 1, ("jsonl에 그 tool_result가 정확히 하나가 아니다", toolu, len(results))
    rb, tur = results[0]
    assert isinstance(tur, dict) and isinstance(tur.get("answers"), dict), ("tool_result 줄에 toolUseResult.answers가 없다", toolu)
    return ub, ts, tur["answers"], _content_text(rb.get("content"))


def load_ask(jpath, toolu):
    """jsonl에서 그 toolu의 AskUserQuestion 입력 질문 목록, answers, tool_result 문자열(각각 정확히 하나)."""
    ub, _ts, answers, rtxt = _read_ask(jpath, toolu)
    return [q["question"] for q in ub["input"]["questions"]], answers, rtxt


def utc_ts(s):
    """jsonl timestamp('2026-10-02T04:35:31.525Z') 또는 archived_at('2026-10-06T12:00:00Z') -> aware UTC datetime."""
    assert isinstance(s, str) and s.endswith("Z"), ("UTC ISO 시각(끝 Z)이 아니다", s)
    return datetime.datetime.fromisoformat(s[:-1] + "+00:00")


def asked_at_kst(ts):
    """tool_use 줄 timestamp -> 'YYYY-MM-DD HH:MM KST'(V5_ASKED_AT 자리 값)."""
    return utc_ts(ts).astimezone(KST).strftime("%Y-%m-%d %H:%M KST")


def check_quotes(text, jdir):
    return _check_blocks(parse_blocks(text), jdir, {})


def _check_blocks(blocks, jdir, cache):
    out = []
    for b in blocks:
        jp = os.path.join(jdir, b["jsonl"])
        assert os.path.isfile(jp), ("블록이 적은 세션 jsonl이 없다", jp)
        key = (jp, b["toolu"])
        if key not in cache:
            cache[key] = _read_ask(jp, b["toolu"])
        ub, _ts, answers, rtxt = cache[key]
        qs = [q["question"] for q in ub["input"]["questions"]]
        assert qs.count(b["q"]) == 1, ("질문 인용이 그 tool_use의 질문 하나와 전체 일치하지 않는다", b["toolu"], b["q"][:80])
        assert b["q"] in answers, ("그 질문의 답이 toolUseResult.answers에 없다", b["toolu"], b["q"][:80])
        assert b["a"] == answers[b["q"]], ("답 인용 != 사용자가 고른 답(toolUseResult.answers[질문] 전체 일치)", b["toolu"], b["a"][:80], answers[b["q"]][:80])
        assert '"%s"="%s"' % (b["q"], b["a"]) in rtxt, ("tool_result 문자열에 '\"질문\"=\"답\"'이 없다", b["toolu"])
        out.append((b["toolu"], b["jsonl"], b["a"]))
    return out


def check_record(text, jdir, v5q, dh, archived_at):
    """check_quotes + V5 블록을 이 target(v5q·dh)·승인 선택지·archive 뒤 질문에 묶는다(review_t0_carry_r1 S1·m1). 반환 = check_quotes와 같다."""
    blocks = parse_blocks(text)
    cache = {}
    out = _check_blocks(blocks, jdir, cache)
    ms = list(V5_BLOCK_RE.finditer(text))
    assert len(ms) == 1, ("V5 인용 블록 모양이 정확히 하나가 아니다", len(ms))
    m = ms[0]
    b = blocks[0]
    assert (b["jsonl"], b["toolu"]) == (m.group("jn"), m.group("tu")), ("V5 머리 줄 블록이 '## 사용자 원문' 첫 블록이 아니다", b["toolu"], m.group("tu"))
    assert re.fullmatch(r"[0-9a-f]{64}", dh), ("target 해시 모양", dh)
    v5q = v5q[:-1] if v5q.endswith("\n") else v5q
    assert "diff_hash(target) %s" % dh in v5q.split("\n"), ("보관 V5 질문 재료에 'diff_hash(target) <이 target>' 줄이 없다", dh[:16])
    assert v5q in b["q"], ("V5 질문 인용이 보관 V5 질문 재료(v5_question.txt) 전체를 담지 않는다 -- 이 target에 대한 질문이 아니다", b["toolu"], b["q"][:80])
    ub, ts, _answers, _rtxt = cache[(os.path.join(jdir, b["jsonl"]), b["toolu"])]
    labels = [[o.get("label") for o in q.get("options", [])] for q in ub["input"]["questions"] if q.get("question") == b["q"]]
    assert len(labels) == 1, ("V5 질문이 tool_use에 정확히 하나가 아니다", b["toolu"])
    assert V5_APPROVE_LABEL in labels[0], ("V5 질문 선택지에 승인 label(V5_APPROVE_LABEL)이 없다", b["toolu"], labels[0])
    assert b["a"] == V5_APPROVE_LABEL, ("V5 답 != 승인 선택지 label(V5_APPROVE_LABEL) -- 승인이 아닌 답으로 승인 기록을 만들 수 없다", b["a"][:80])
    assert ts is not None, ("V5 tool_use 줄에 timestamp가 없다", b["toolu"])
    assert utc_ts(ts) > utc_ts(archived_at), ("V5 질문 시각이 archive 끝 시각 뒤가 아니다(이 1차 시도 보관 전에 물은 질문)", ts, archived_at)
    at = m.group("at")
    assert ASKED_AT_RE.fullmatch(at), ("V5_ASKED_AT 형식 'YYYY-MM-DD HH:MM KST'가 아니다", at[:80])
    assert at == asked_at_kst(ts), ("V5_ASKED_AT != V5 tool_use 줄 timestamp(KST 분)", at, asked_at_kst(ts))
    return out


if __name__ == "__main__":
    # python t0_quote_check.py canon-sha <초안>  |  check <기록> <jsonl 폴더>  |  labels(승인·거부 label 두 줄 -- archive가 v5_options.txt에)
    import hashlib
    if sys.argv[1] == "canon-sha":
        print(hashlib.sha256(canon(open(sys.argv[2], "rb").read().decode("utf-8")).encode("utf-8")).hexdigest())
    elif sys.argv[1] == "check":
        for tu, jn, a in check_quotes(open(sys.argv[2], "rb").read().decode("utf-8"), sys.argv[3]):
            print("   인용 OK %s (%s) 답 %r" % (tu, jn, a))
    elif sys.argv[1] == "labels":
        sys.stdout.buffer.write(("%s\n%s\n" % (V5_APPROVE_LABEL, V5_REJECT_LABEL)).encode("utf-8"))
    else:
        sys.exit(2)
