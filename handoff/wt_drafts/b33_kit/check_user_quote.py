"""승인 기록 초안 '사용자 원문'의 B33 질문·선택지 라벨·선택지 설명·답이 세션 기록(jsonl)의 AskUserQuestion 원문과 같은지 대조(읽기만).
    python -B check_user_quote.py <세션 jsonl> <승인 기록 초안 .md> <출력 .json>"""
import json
import sys

SESSION, DRAFT, OUT = sys.argv[1:4]
qs, answers = [], []
with open(SESSION, encoding="utf-8") as fh:
    for line in fh:
        if "[B33" not in line:
            continue
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = o.get("message") or {}
        for c in msg.get("content") or []:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "tool_use" and c.get("name") == "AskUserQuestion":
                for q in c.get("input", {}).get("questions", []):
                    if "[B33" in q.get("question", ""):
                        qs.append({"ts": o.get("timestamp"), "question": q["question"],
                                   "options": [x.get("label") for x in q.get("options", [])],
                                   "descriptions": [x.get("description") or "" for x in q.get("options", [])]})
            if c.get("type") == "tool_result":
                txt = c.get("content")
                if isinstance(txt, list):
                    txt = "".join(x.get("text", "") for x in txt if isinstance(x, dict))
                if isinstance(txt, str) and "[B33" in txt:
                    answers.append({"ts": o.get("timestamp"), "text": txt})
draft = open(DRAFT, encoding="utf-8").read()
res = {"questions": qs, "answers": answers,
       "question_in_draft": [q["question"] in draft for q in qs],
       "options_in_draft": [all(('"%s"' % x) in draft for x in q["options"]) for q in qs],
       "descriptions_in_draft": [all(('"%s"' % x) in draft for x in q["descriptions"]) for q in qs]}
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in res.items() if k.endswith("in_draft")}, ensure_ascii=False), len(qs), len(answers))
