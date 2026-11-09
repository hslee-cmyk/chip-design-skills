#!/usr/bin/env python3
"""B26-1 사전 승인 기록 4·5의 '## 사용자 원문' 인용을 세션 jsonl AskUserQuestion에 묶는다(t0_quote_check 재사용 얇은 층).

배경(2026-10-06 T0 carry 작성자의 'b26_1 선례 점검'): 기록 4 `20261001-b26-p9-signature-update`(diff)는 jsonl 대조·초안 핀이 없었고,
기록 5 `20261001-b26-v3-equiv-range`(decision)의 fill_u3.py check_jsonl은 답이 본문 **어디든** `> 답` 줄로 있으면 통과했고(답 자리에 묶지 않음,
승인 선택지 대조 없음), 답을 그 toolu가 든 **마지막** toolUseResult 줄에서 tool_result id·is_error 확인 없이 가져왔다.

검사 핵심(질문·답 전체 일치, 블록 = 자기 jsonl·자기 toolu)은 t0_quote_check._check_blocks를 그대로 부른다(두 번째 checker를 만들지 않는다).
B26-1 기록은 T0 블록 양식(머리 줄 -> '> 질문' -> '답:' -> '> 답')이 아니라 아래 양식이라 이 모듈은 **절 파서와 사전 승인 핀**만 더한다:

    ## 사용자 원문
    <빈 줄>
    > <답>                      (1줄 이상 -- 답 자리)
    <빈 줄>
    (질문 <YYYY-MM-DD HH:MM KST>, 답 <YYYY-MM-DD HH:MM KST>(세션 jsonl `<세션 id>` AskUserQuestion `<toolu>`, 질문 <N>개 중 [<header>]). 질문 원문(고치지 않고 그대로): "<질문>"
    선택지: "<label>" -- "<description>" / … .)
    <빈 줄>
    ## …

check_record(text, aid, jsonl_path) -- 절 전체가 위 모양과 정확히 같아야 한다(떠도는 줄·인용 거부). 그 위에:
  * t0_quote_check._check_blocks: 질문 = 그 tool_use input.questions[].question 하나와 전체 일치, 답 자리 = 그 tool_use의 tool_result 줄
    toolUseResult.answers[질문]과 전체 일치, tool_result 문자열에 '"질문"="답"'.
  * 사전 승인 핀(PRE, 이 파일이 정본 -- fill_u3.py도 여기서 읽는다): 기록 id -> 세션 id·toolu·header·승인 선택지 label.
    머리 `id:` = aid, 세션 jsonl 이름·toolu = 핀, jsonl_path basename = '<세션 id>.jsonl', 그 질문의 header = 핀 header = 인용 [header],
    N = 그 tool_use 질문 수, 선택지 줄 = 그 질문 options 전체(label·description, 순서), multiSelect 아님,
    답 = 핀 승인 label이고 그 label이 그 질문 선택지에 있다(거부 선택지를 고른 답으로 승인 기록을 만들 수 없다).
  * tool_result: tool_use_id = toolu인 tool_result 블록이 jsonl에 정확히 하나, is_error가 참이 아니다.
  * 시각: '질문' = tool_use 줄 timestamp의 KST 분, '답' = tool_result 줄 timestamp의 KST 분.

시각 묶기에 대해: 두 기록은 2026-10-01 질문에 대한 **사전 승인**이다(1차 시도 archive보다 먼저 물었다). 그래서 T0 check_record의
'V5 tool_use timestamp > archive 끝 시각' 묶기는 쓰지 않는다 -- 질문이 archive 뒤일 수 없다. target 묶기는 구조적이다: 기록 4 target(diff 해시)·
기록 5 target(변이 id@묶기 해시)은 질문 문안에 없고, b26_1_carry.sh records가 1차 auditor 산출물(base_check.json·attempt1_v3.json)과 따로 계산한 값을
대조해 채운다(기록 4: 3중 diff_hash, 기록 5: fill_u3 --src 묶기 해시·경로 끝 노드). 인용 묶기는 '이 질문에 사용자가 승인 선택지를 골랐다'까지만 증명한다.

    python b26_1_quote_bind.py check <기록 id> <기록 파일> <세션 jsonl>

(dec, 2026-10-07) 절 = 위 블록(답 자리 -> 메타 줄 -> 선택지 줄 -> 빈 줄)의 **나열**로 넓혔다. PRE[기록 id]는 블록 핀 목록(절 안 순서 그대로)이고
블록 수 = 핀 수, 블록 i는 핀 i에 묶는다(위 검사 전부를 블록마다). 기록 4는 U5 + [B26-1 V5](경로 합집합 P9 test + B34 test를 덮는 V5 승인,
card '승인 줄 배치' (6) "두 승인을 함께 인용하는 기록 하나") 두 블록, 기록 5는 U3 한 블록.
같은 toolu의 [B26-1 V4] 질문(V4 면제 decision 기록)은 사용자가 뒤에 바꿨다(2026-10-07 "다로 하자." -- 면제 기록 대신 test-only 강화 card) -- 그 기록은 만들지 않으므로 핀도 없다.
check_record의 반환은 첫 블록 (toolu, jsonl 이름, 답)이다(fill_u3.py 호환). 블록 전부는 check_all.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t0_quote_check as tq  # noqa: E402  (as-is 재사용)

SESSION = "63c6146a-ab1d-4035-a169-bae810986922"
TOOLU = "toolu_01KTtsbRiK7S3cv1coUsAyPw"      # 2026-10-01 AskUserQuestion([U3 등가]·[U5 P9 시그] 등 4개)
TOOLU_D = "toolu_01MGv1L1nfGzLcPrjMTk5A44"    # 2026-10-07 AskUserQuestion([B26-1 V4]·[B26-1 V5]) -- 기록 4가 [B26-1 V5] 블록만 인용한다
# 사전 승인 핀(정본): 기록 id -> '## 사용자 원문' 블록 핀 목록(절 안 순서) -- 블록마다 (세션, toolu, 질문 header, 승인 선택지 label)
PRE = {
    "20261001-b26-p9-signature-update": [
        dict(session=SESSION, toolu=TOOLU, header="U5 P9 시그", approve="갱신 승인 (Recommended)"),
        dict(session=SESSION, toolu=TOOLU_D, header="B26-1 V5", approve="(가) 합친 V5 승인 (Recommended)"),
    ],
    "20261001-b26-v3-equiv-range": [
        dict(session=SESSION, toolu=TOOLU, header="U3 등가", approve="정리 2줄 + 면제 1 (Recommended)"),
    ],
}
_AT = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2} KST"
BLOCK_RE = re.compile(
    r"(?P<a>(?:> [^\n]*\n)+)\n"
    r"\(질문 (?P<qat>" + _AT + r"), 답 (?P<aat>" + _AT + r")\(세션 jsonl `(?P<sid>[0-9a-f-]+)` AskUserQuestion `(?P<tu>toolu_[A-Za-z0-9]+)`, "
    r"질문 (?P<n>[1-9][0-9]*)개 중 \[(?P<hdr>[^\]\n]+)\]\)\. 질문 원문\(고치지 않고 그대로\): \"(?P<q>[^\n]*)\"\n"
    r"선택지: (?P<opts>[^\n]*)\.\)\n\n")
SEC_HEAD = "## 사용자 원문\n\n"


def section(text):
    """'## 사용자 원문' 줄부터 다음 '## ' 줄 앞까지(정확히 한 절)."""
    assert "\r" not in text and not text.startswith("﻿"), "CR·BOM"
    hs = [m.start() for m in re.finditer(r"(?m)^## 사용자 원문$", text)]
    assert len(hs) == 1, ("'## 사용자 원문' 절이 정확히 하나가 아니다", len(hs))
    nxt = re.search(r"(?m)^## ", text[hs[0] + 1:])
    assert nxt, "'## 사용자 원문' 뒤에 다음 절이 없다"
    return text[hs[0]:hs[0] + 1 + nxt.start()]


def parse(text):
    """절 = SEC_HEAD + 블록 1개 이상(빈틈 없이 이어짐, 절 끝까지). 반환 = 블록 dict 목록(절 안 순서)."""
    sec = section(text)
    bad = ("'## 사용자 원문' 절이 B26-1 인용 양식(블록 = 답 자리 -> (질문 시각·답 시각·세션·toolu·N·[header]) 질문 원문 -> 선택지, 블록의 나열)과 정확히 같지 않다", sec[:200])
    assert sec.startswith(SEC_HEAD), bad
    pos, out = len(SEC_HEAD), []
    while pos < len(sec):
        m = BLOCK_RE.match(sec, pos)
        assert m, bad + (pos,)
        d = m.groupdict()
        d["a"] = "\n".join(l[2:] for l in d["a"].rstrip("\n").split("\n"))
        out.append(d)
        pos = m.end()
    assert out, bad
    return out


def _result_meta(jpath, toolu):
    """tool_use_id = toolu인 tool_result 블록 전부: (is_error, 그 줄 timestamp). t0_quote_check._read_ask가 내주지 않는 두 값."""
    out = []
    with open(jpath, encoding="utf-8") as fh:
        for line in fh:
            if toolu not in line:
                continue
            o = json.loads(line)
            c = (o.get("message") or {}).get("content")
            if not isinstance(c, list):
                continue
            for b in c:
                if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id") == toolu:
                    out.append((b.get("is_error"), o.get("timestamp")))
    return out


def _check_one(d, pin, jsonl_path, cache):
    """블록 하나를 핀 하나에 묶는다. 반환 = (toolu, 세션 jsonl 이름, 답)."""
    assert d["sid"] == pin["session"], ("세션 jsonl 이름 != 핀", d["sid"], pin["session"])
    assert d["tu"] == pin["toolu"], ("AskUserQuestion toolu != 핀", d["tu"], pin["toolu"])
    assert os.path.basename(jsonl_path) == d["sid"] + ".jsonl", ("jsonl 경로 이름 != 인용 세션", jsonl_path, d["sid"])
    jdir = os.path.dirname(os.path.abspath(jsonl_path))
    out = tq._check_blocks([{"toolu": d["tu"], "jsonl": d["sid"] + ".jsonl", "q": d["q"], "a": d["a"]}], jdir, cache)
    ub, ts, answers, _rtxt = cache[(os.path.join(jdir, d["sid"] + ".jsonl"), d["tu"])]
    qs = ub["input"]["questions"]
    mine = [q for q in qs if q.get("question") == d["q"]]
    assert len(mine) == 1, ("질문이 tool_use에 정확히 하나가 아니다", d["tu"])
    q = mine[0]
    assert q.get("header") == d["hdr"] == pin["header"], ("질문 header != 인용 [header] != 핀", q.get("header"), d["hdr"], pin["header"])
    assert int(d["n"]) == len(qs), ("'질문 N개' != tool_use 질문 수", d["n"], len(qs))
    assert not q.get("multiSelect"), ("multiSelect 질문", d["hdr"])
    opts = " / ".join('"%s" -- "%s"' % (o["label"], o["description"]) for o in q["options"])
    assert d["opts"] == opts, ("선택지 줄 != 그 질문 options 전체(label·description·순서)", d["opts"][:80])
    labels = [o["label"] for o in q["options"]]
    assert pin["approve"] in labels, ("핀 승인 label이 그 질문 선택지에 없다", pin["approve"], labels)
    assert d["a"] == pin["approve"], ("답 != 그 사전 승인 질문의 승인 선택지 label -- 승인이 아닌 답으로 승인 기록을 만들 수 없다", d["a"][:80], pin["approve"])
    assert answers[d["q"]] == pin["approve"]
    rm = _result_meta(os.path.join(jdir, d["sid"] + ".jsonl"), d["tu"])
    assert len(rm) == 1, ("tool_use_id = toolu인 tool_result가 정확히 하나가 아니다", d["tu"], len(rm))
    assert rm[0][0] is not True, ("tool_result is_error", d["tu"])
    assert ts is not None and rm[0][1] is not None, ("tool_use·tool_result 줄 timestamp 없음", d["tu"])
    assert d["qat"] == tq.asked_at_kst(ts), ("'질문' 시각 != tool_use 줄 timestamp(KST 분)", d["qat"], tq.asked_at_kst(ts))
    assert d["aat"] == tq.asked_at_kst(rm[0][1]), ("'답' 시각 != tool_result 줄 timestamp(KST 분)", d["aat"], tq.asked_at_kst(rm[0][1]))
    return out[0]


def check_all(text, aid, jsonl_path):
    """반환 = 블록마다 (toolu, 세션 jsonl 이름, 답) 목록. 블록 수 = 핀 수, 블록 i = 핀 i. 어긋나면 AssertionError."""
    assert aid in PRE, ("사전 승인 핀이 없는 기록 id", aid)
    pins = PRE[aid]
    fm = re.match(r"---\n(.*?)\n---\n", text, re.S)
    ids = re.findall(r"(?m)^id: (.+)$", fm.group(1)) if fm else []
    assert ids == [aid], ("기록 머리 id != 기록 id", ids, aid)
    ds = parse(text)
    assert len(ds) == len(pins), ("인용 블록 수 != 사전 승인 핀 수", len(ds), len(pins), [d["hdr"] for d in ds])
    cache = {}
    return [_check_one(d, pin, jsonl_path, cache) for d, pin in zip(ds, pins)]


def check_record(text, aid, jsonl_path):
    """check_all 뒤 첫 블록 (toolu, 세션 jsonl 이름, 답)(fill_u3.py 호환 -- 블록 전부는 이미 검사했다)."""
    return check_all(text, aid, jsonl_path)[0]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) == 5 and sys.argv[1] == "check":
        res = check_all(open(sys.argv[3], "rb").read().decode("utf-8"), sys.argv[2], sys.argv[4])
        print("   인용 OK %s %s" % (sys.argv[2], "; ".join("%s (%s) 답 %r = 승인 선택지" % r for r in res)))
    else:
        print("사용: b26_1_quote_bind.py check <기록 id> <기록 파일> <세션 jsonl>", file=sys.stderr)
        sys.exit(2)
