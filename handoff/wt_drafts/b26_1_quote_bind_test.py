#!/usr/bin/env python3
"""b26_1_quote_bind.check_record self-test -- B26-1 사전 승인 기록 4·5 인용 묶기.

    python b26_1_quote_bind_test.py <작업 디렉터리(/c/g<숫자>/… 아래, 없어야 한다)>

* 입력: 실제 초안 두 개(읽기만), 실제 세션 jsonl(읽기만). 합성 jsonl은 실제 jsonl의 그 toolu tool_use 줄·tool_result 줄 두 줄을 복사해 고친 것(작업 디렉터리 안).
* 기대값은 'b26_1 선례 점검' 지적과 검사 계약(질문·답 전체 일치, 답 자리, 승인 선택지, toolu·tool_result id, is_error)으로 정한다 -- 피검을 불러 만들지 않는다.
  거부 사례는 그 이유 문구(AssertionError 안 문자열)가 맞는지도 본다(다른 이유로 거부돼 통과하는 것을 막는다).
* 정보 열: 옛 fill_u3.check_jsonl(fill_u3.py.pre-qbind.bak)이 기록 5 사례를 어떻게 판정했는지(지적 재현 -- 기대값 아님).
* 결과는 사례마다 <작업 디렉터리>/../qbind_result.tsv가 아니라 _drafts/b26_1_kit_selftest/out/qbind_result.tsv에 append.
"""
import importlib.machinery
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b26_1_quote_bind as qb  # noqa: E402

JDIR_REAL = os.path.join(os.path.expanduser("~"), ".claude", "projects", "C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills")
JREAL = os.path.join(JDIR_REAL, qb.SESSION + ".jsonl")
A4, A5 = "20261001-b26-p9-signature-update", "20261001-b26-v3-equiv-range"
DR4, DR5 = (os.path.join(HERE, "approval_%s.md" % a) for a in (A4, A5))
OLD_FILL = os.path.join(HERE, "b26_1_kit_selftest", "fill_u3.py.pre-qbind.bak")
RES = os.path.join(HERE, "b26_1_kit_selftest", "out", "qbind_result.tsv")
OTHER_TOOLU = "toolu_01UZMV9c7hahwakQs6EiNken"   # 같은 jsonl의 다른 AskUserQuestion


def rd(p):
    return open(p, "rb").read().decode("utf-8")


def sub1(t, a, b):
    assert t.count(a) == 1, ("변형 앵커가 정확히 하나가 아니다", a[:60], t.count(a))
    return t.replace(a, b, 1)


def old_check(text):
    """옛 fill_u3.check_jsonl(정보용) -> PASS|STOP."""
    if not os.path.isfile(OLD_FILL):
        return "-"
    spec = importlib.util.spec_from_file_location("old_fill_u3", OLD_FILL, loader=importlib.machinery.SourceFileLoader("old_fill_u3", OLD_FILL))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            m.check_jsonl(JREAL, text)
        return "PASS"
    except AssertionError:
        return "STOP"


def main(work):
    assert re.fullmatch(r"[A-Za-z]:/g\d+/[a-z0-9_]+|/c/g\d+/[a-z0-9_]+", work.replace("\\", "/")), ("작업 디렉터리는 /c/g<숫자>/<이름>", work)
    assert not os.path.exists(work), ("작업 디렉터리가 이미 있다", work)
    os.makedirs(work)
    os.makedirs(os.path.dirname(RES), exist_ok=True)
    t4, t5 = rd(DR4), rd(DR5)
    # 합성 jsonl 원재료: 실제 jsonl의 그 toolu tool_use 줄·tool_result 줄(읽기만)
    use_line = res_line = None
    with open(JREAL, encoding="utf-8") as fh:
        for line in fh:
            if qb.TOOLU not in line:
                continue
            o = json.loads(line)
            c = (o.get("message") or {}).get("content")
            if not isinstance(c, list):
                continue
            for b in c:
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("id") == qb.TOOLU:
                    assert use_line is None; use_line = o
                if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id") == qb.TOOLU:
                    assert res_line is None; res_line = o
    assert use_line and res_line
    # (dec) 기록 4 둘째 블록 [B26-1 V5] = 2026-10-07 toolu(qb.TOOLU_D)의 tool_use·tool_result 두 줄도 합성 jsonl에 싣는다(mut_d로 고칠 수 있다)
    use_d = res_d = None
    with open(JREAL, encoding="utf-8") as fh:
        for line in fh:
            if qb.TOOLU_D not in line:
                continue
            o = json.loads(line)
            c = (o.get("message") or {}).get("content")
            if not isinstance(c, list):
                continue
            for b in c:
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("id") == qb.TOOLU_D:
                    assert use_d is None; use_d = o
                if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id") == qb.TOOLU_D:
                    assert res_d is None; res_d = o
    assert use_d and res_d

    def mkj(name, mut_res=None, extra=(), fname=qb.SESSION + ".jsonl", mut_d=None):
        d = os.path.join(work, name)
        os.makedirs(d)
        u = json.loads(json.dumps(use_line)); r = json.loads(json.dumps(res_line))
        ud = json.loads(json.dumps(use_d)); rd_ = json.loads(json.dumps(res_d))
        if mut_res:
            mut_res(r)
        if mut_d:
            mut_d(rd_)
        with open(os.path.join(d, fname), "w", encoding="utf-8", newline="\n") as fh:
            for o in (u, r, ud, rd_) + tuple(extra):
                fh.write(json.dumps(o, ensure_ascii=False) + "\n")
        return os.path.join(d, fname)

    def rblock(r):
        return [b for b in r["message"]["content"] if b.get("type") == "tool_result"][0]

    def set_err(r):
        rblock(r)["is_error"] = True

    def wrong_id(r):
        rblock(r)["tool_use_id"] = "toolu_01XXXXXXXXXXXXXXXXXXXXXX"

    q5 = [q for q in use_line["message"]["content"][0]["input"]["questions"] if q["header"] == "U5 P9 시그"][0]["question"]
    q3 = [q for q in use_line["message"]["content"][0]["input"]["questions"] if q["header"] == "U3 등가"][0]["question"]

    def user_rejected(r):   # 사용자가 실제로 거부 선택지를 고른 jsonl(답·문자열 둘 다)
        r["toolUseResult"]["answers"][q5] = "P9 시그니처 유지"
        b = rblock(r)
        b["content"] = b["content"].replace('"%s"="갱신 승인 (Recommended)"' % q5, '"%s"="P9 시그니처 유지"' % q5)
        assert '"%s"="P9 시그니처 유지"' % q5 in b["content"]

    def user_rejected3(r):
        r["toolUseResult"]["answers"][q3] = "등가 4개 모두 면제"
        b = rblock(r)
        b["content"] = b["content"].replace('"%s"="정리 2줄 + 면제 1 (Recommended)"' % q3, '"%s"="등가 4개 모두 면제"' % q3)

    J_OK = mkj("ok")
    J_ERR = mkj("err", set_err)
    J_WID = mkj("wid", wrong_id)
    J_DUP = mkj("dup", extra=(json.loads(json.dumps(res_line)),))
    J_REJ = mkj("rej", user_rejected)
    J_REJ3 = mkj("rej3", user_rejected3)
    J_NAME = mkj("name", fname="other-session.jsonl")
    qv5 = [q for q in use_d["message"]["content"][0]["input"]["questions"] if q["header"] == "B26-1 V5"][0]["question"]
    qv4 = [q for q in use_d["message"]["content"][0]["input"]["questions"] if q["header"] == "B26-1 V4"][0]["question"]

    def v5_rejected(r):   # 사용자가 [B26-1 V5]에서 '(나) card 계약 12 개정'을 고른 jsonl
        r["toolUseResult"]["answers"][qv5] = "(나) card 계약 12 개정"
        b = rblock(r)
        old = '"%s"="(가) 합친 V5 승인 (Recommended)"' % qv5
        assert b["content"].count(old) == 1
        b["content"] = b["content"].replace(old, '"%s"="(나) card 계약 12 개정"' % qv5)

    def v5_err(r):
        rblock(r)["is_error"] = True
    J_REJV5 = mkj("rejv5", mut_d=v5_rejected)
    J_ERRV5 = mkj("errv5", mut_d=v5_err)
    okv5 = "\n> (가) 합친 V5 승인 (Recommended)\n"
    i5 = t4.index(okv5)
    blk_u5 = t4[t4.index("## 사용자 원문\n\n") + len("## 사용자 원문\n\n"):i5 + 1]
    blk_v5 = t4[i5 + 1:t4.index("## 범위 설명")]
    assert blk_u5.startswith("> 갱신 승인") and blk_v5.startswith("> (가) 합친 V5") and blk_v5.endswith(".)\n\n")

    ok4, ok5 = "\n> 갱신 승인 (Recommended)\n", "\n> 정리 2줄 + 면제 1 (Recommended)\n"
    cases = [
        # (이름, 기대, 기록 id, 텍스트, jsonl, 이유 문구, 설명)
        ("real4", "PASS", A4, t4, JREAL, "", "기록 4 실제 초안 + 실제 jsonl(실제 답 수용)"),
        ("real5", "PASS", A5, t5, JREAL, "", "기록 5 실제 초안 + 실제 jsonl(실제 답 수용)"),
        ("syn4", "PASS", A4, t4, J_OK, "", "기록 4 + 합성 jsonl(실제 두 줄 그대로)"),
        ("syn5", "PASS", A5, t5, J_OK, "", "기록 5 + 합성 jsonl(실제 두 줄 그대로)"),
        ("swap_reject4", "STOP", A4, sub1(t4, ok4, "\n> P9 시그니처 유지\n"), JREAL, "답 인용 != 사용자가 고른 답", "기록 4 답 자리를 거부 선택지로"),
        ("swap_reject5", "STOP", A5, sub1(t5, ok5, "\n> 등가 4개 모두 면제\n"), JREAL, "답 인용 != 사용자가 고른 답", "기록 5 답 자리를 다른(비승인) 선택지로"),
        ("elsewhere4", "STOP", A4, sub1(sub1(t4, ok4, "\n> P9 시그니처 유지\n"), "\n덮지 않는 것:", "\n> 갱신 승인 (Recommended)\n덮지 않는 것:"), JREAL,
         "답 인용 != 사용자가 고른 답", "기록 4 답 자리 변조 + 실제 답을 범위 설명에 인용"),
        ("elsewhere5", "STOP", A5, sub1(sub1(t5, ok5, "\n> 등가 4개 모두 면제\n"), "\n덮지 않는 것:", "\n> 정리 2줄 + 면제 1 (Recommended)\n덮지 않는 것:"), JREAL,
         "답 인용 != 사용자가 고른 답", "기록 5 답 자리 변조 + 실제 답을 범위 설명에 인용(옛 check_jsonl 통과 사례)"),
        ("user_rejected4", "STOP", A4, sub1(t4, ok4, "\n> P9 시그니처 유지\n"), J_REJ, "승인 선택지 label", "jsonl에서 사용자가 거부 선택지를 골랐고 기록이 그대로 인용"),
        ("user_rejected5", "STOP", A5, sub1(t5, ok5, "\n> 등가 4개 모두 면제\n"), J_REJ3, "승인 선택지 label", "jsonl에서 사용자가 비승인 선택지를 골랐고 기록이 그대로 인용"),
        ("wrong_toolu4", "STOP", A4, t4.replace(qb.TOOLU, OTHER_TOOLU), JREAL, "toolu != 핀", "기록 4 toolu를 같은 jsonl의 다른 AskUserQuestion으로"),
        ("wrong_toolu5", "STOP", A5, t5.replace(qb.TOOLU, OTHER_TOOLU), JREAL, "toolu != 핀", "기록 5 toolu를 다른 AskUserQuestion으로"),
        ("is_error4", "STOP", A4, t4, J_ERR, "is_error", "tool_result is_error = true"),
        ("is_error5", "STOP", A5, t5, J_ERR, "is_error", "tool_result is_error = true"),
        ("result_id", "STOP", A4, t4, J_WID, "tool_result가 정확히 하나가 아니다", "tool_result tool_use_id가 다른 id"),
        ("result_dup", "STOP", A4, t4, J_DUP, "tool_result가 정확히 하나가 아니다", "같은 toolu tool_result 두 줄"),
        ("jsonl_name", "STOP", A4, t4, J_NAME, "jsonl 경로 이름 != 인용 세션", "jsonl 파일 이름이 인용 세션과 다름"),
        ("header", "STOP", A4, sub1(t4, "[U5 P9 시그]", "[U4 B40]"), JREAL, "header", "인용 [header]를 다른 질문 header로"),
        ("question", "STOP", A4, sub1(t4, "갱신해도 될까요?", "갱신해도 될까요"), JREAL, "질문 인용이 그 tool_use의 질문 하나와 전체 일치하지 않는다", "질문 원문 한 글자 변조"),
        ("question_other", "STOP", A4, sub1(sub1(t4, q5, q3), ok4, ok5), JREAL, "header", "기록 4 질문·답 자리에 같은 toolu의 U3 질문·답"),
        ("options", "STOP", A4, sub1(t4, "약화가 아닙니다(승인 기록 diff 1건)", "약화가 아닙니다"), JREAL, "선택지 줄", "선택지 description 변조"),
        ("q_time", "STOP", A4, sub1(t4, "(질문 2026-10-01 21:10 KST", "(질문 2026-10-01 21:09 KST"), JREAL, "'질문' 시각", "질문 시각 1분 변조"),
        ("a_time", "STOP", A5, sub1(t5, "답 2026-10-01 21:14 KST(", "답 2026-10-01 21:15 KST("), JREAL, "'답' 시각", "답 시각 1분 변조"),
        ("n_questions", "STOP", A4, sub1(t4, "질문 4개 중", "질문 3개 중"), JREAL, "질문 N개", "질문 수 변조"),
        ("stray_line", "STOP", A4, sub1(t4, ok4, ok4 + "> 덧붙인 인용\n"), JREAL, "답 인용 != 사용자가 고른 답", "답 자리에 인용 줄 하나 더(두 줄 답 != 실제 답)"),
        ("stray_para", "STOP", A5, sub1(t5, "\n\n## 범위 설명", "\n\n떠도는 문단.\n\n## 범위 설명"), JREAL, "인용 양식", "절 안 떠도는 문단"),
        ("wrong_aid", "STOP", A5, t4, JREAL, "기록 머리 id", "기록 4 본문을 기록 5 id로 검사"),
        # (dec) 기록 4 = U5 + [B26-1 V5] 두 블록
        ("v5blk_missing", "STOP", A4, sub1(t4, blk_v5, ""), JREAL, "인용 블록 수 != 사전 승인 핀 수", "기록 4에서 [B26-1 V5] 블록 삭제(U5만 -- 옛 한 경로 기록 모양)"),
        ("v5blk_order", "STOP", A4, sub1(t4, blk_u5 + blk_v5, blk_v5 + blk_u5), JREAL, "toolu != 핀", "두 블록 순서 바꿈"),
        ("v5blk_dup", "STOP", A4, sub1(t4, blk_v5, blk_v5 + blk_v5), JREAL, "인용 블록 수 != 사전 승인 핀 수", "[B26-1 V5] 블록 두 번"),
        ("v5blk_answer", "STOP", A4, sub1(t4, okv5, "\n> (나) card 계약 12 개정\n"), JREAL, "답 인용 != 사용자가 고른 답", "[B26-1 V5] 답 자리를 거부 선택지로"),
        ("v5blk_user_rej", "STOP", A4, sub1(t4, okv5, "\n> (나) card 계약 12 개정\n"), J_REJV5, "승인 선택지 label", "jsonl에서 사용자가 [B26-1 V5] 거부 선택지를 골랐고 기록이 그대로 인용"),
        ("v5blk_is_error", "STOP", A4, t4, J_ERRV5, "is_error", "[B26-1 V5] tool_result is_error = true"),
        ("v5blk_v4_quoted", "STOP", A4, sub1(sub1(sub1(t4, qv5, qv4), okv5, "\n> (가′) 면제 + 재검토 줄 (Recommended)\n"), "질문 2개 중 [B26-1 V5]", "질문 2개 중 [B26-1 V4]"), JREAL, "header", "[B26-1 V5] 자리에 같은 toolu의 [B26-1 V4] 질문·답(철회된 V4 면제)"),
        ("v5blk_syn", "PASS", A4, t4, J_OK, "", "기록 4 두 블록 + 합성 jsonl(두 toolu 네 줄 그대로)"),
    ]
    hdr = "case\texpected\tgot\tmatch\tdesc\tdetail\told_check_jsonl\n"
    open(RES, "w", encoding="utf-8", newline="\n").write(hdr)
    nbad = 0
    for name, exp, aid, text, jp, why, desc in cases:
        try:
            qb.check_record(text, aid, jp)
            got, msg = "PASS", ""
        except AssertionError as e:
            got, msg = "STOP", repr(e.args)
        detail = ""
        if got == "STOP" and why and why not in msg:
            got, detail = "STOP_OTHER_REASON", "이유 문구 없음[%s] " % why
        old = old_check(text) if aid == A5 and jp == JREAL else "-"
        m = "ok" if got == exp else "MISMATCH"
        nbad += m != "ok"
        line = "\t".join([name, exp, got, m, desc, (detail + msg).replace("\t", " ").replace("\n", " ")[:200], old])
        with open(RES, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(line + "\n")
        print("  %-15s 기대 %-4s 결과 %-17s %-8s 옛 %-4s %s" % (name, exp, got, m, old, desc))
    print("결과 %s -- 사례 %d, 불일치 %d" % (RES, len(cases), nbad))
    shutil.rmtree(work)
    return 1 if nbad else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1]))
