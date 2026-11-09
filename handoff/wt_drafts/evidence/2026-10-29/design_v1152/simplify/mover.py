"""design 40·41 2차 단순화 이동 도구(2026-10-29, 검증 design_simplify_validation.md §4.2).
jobs 모듈(JOBS 목록)을 받아 design 본문의 줄 구간 또는 부분 문자열을 새 문장으로 바꾸고, 바뀐 원문을 그대로
design 이력 파일(docs/02-design/features/gain-budget-gmid-sizing.design.history.md)에 H 번호 절로 옮긴다.
job = dict(id, file('40'|'41'|'42'), title, 그리고
  mode 'lines': start(줄 머리, 유일), end(줄 머리, 배타; None = 한 줄), new(대체 문단; '' = 줄 삭제)
  mode 'sub'  : old(유일 부분 문자열), new)
모든 job을 먼저 검사하고(유일성 실패 = 아무것도 쓰지 않음 -- fail-closed), 통과하면 쓴다. CRLF/LF 유지."""
import importlib.util, os, sys

W = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/docs/02-design/features/"
DOCS = {"40": "gain-budget-gmid-sizing.40-engine.design.md",
        "41": "gain-budget-gmid-sizing.41-gain-budget.design.md",
        "42": "gain-budget-gmid-sizing.42-gap-checklist.design.md"}
HIST = W + "gain-budget-gmid-sizing.design.history.md"
HEAD = ("---\ntitle: gain-budget-gmid-sizing -- design 이력(40·41·42)\n"
        "design: gain-budget-gmid-sizing.40-engine.design.md, gain-budget-gmid-sizing.41-gain-budget.design.md, gain-budget-gmid-sizing.42-gap-checklist.design.md\n"
        "date: 2026-10-29\n---\n\n# gain-budget-gmid-sizing design 이력\n\n"
        "> design 본문에서 옮긴 판 경위·측정 서술·폐지·대체된 옛 문언을 원문 그대로 둔다. 현행 규칙·정의·인터페이스·완료 조건은 본문이 정본이다. "
        "본문은 각 자리에서 이 파일의 H 번호를 가리킨다. 근거: 사용자 2026-10-29 '같은 기준으로 과도하게 복잡한 부분 고쳐'(gm/ID 손계산 우선), "
        "독립 검증 `wt/_drafts/evidence/2026-10-29/design_simplify_validation.md` §4.2. 1차 단순화 원문(S1~S12)은 `wt/_drafts/evidence/2026-10-29/design_v1152/simplify/moved_text.md`.\n")


def load(path):
    raw = open(path, "rb").read().decode("utf-8")
    nl = "\r\n" if "\r\n" in raw else "\n"
    return raw, nl


def run(jobfile):
    spec = importlib.util.spec_from_file_location("jobs", jobfile)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    texts, nls = {}, {}
    for k in {j["file"] for j in mod.JOBS}:
        texts[k], nls[k] = load(W + DOCS[k])
    out = []
    for j in mod.JOBS:
        k, nl = j["file"], nls[j["file"]]
        t = texts[k]
        if j["mode"] == "table_after":
            # anchor(유일 줄 머리) 뒤 첫 header(줄 머리) 표를 통째로 note 한 줄로 바꾼다(다음 heading 전에 있어야 함)
            lines = t.split(nl)
            ai = [i for i, l in enumerate(lines) if l.startswith(j["anchor"])]
            if len(ai) != 1:
                sys.exit("%s: anchor occurs %d times" % (j["id"], len(ai)))
            si = None
            for i in range(ai[0] + 1, len(lines)):
                if lines[i].startswith(j["header"]):
                    si = i
                    break
                if lines[i].startswith("#"):
                    break
            if si is None:
                sys.exit("%s: header not found before next heading" % j["id"])
            ei = si
            while ei < len(lines) and lines[ei].startswith("|"):
                ei += 1
            old = "\n".join(lines[si:ei])
            lines[si:ei] = [j["new"]]
            t = nl.join(lines)
        elif j["mode"] == "filter":
            # start/end 줄 머리로 구간(end 배타)을 정하고 pred(line)이 참인 줄을 지운다; note가 있으면 구간 끝(빈 줄 앞)에 넣는다
            lines = t.split(nl)
            si = [i for i, l in enumerate(lines) if l.startswith(j["start"])]
            if len(si) != 1:
                sys.exit("%s: start occurs %d times" % (j["id"], len(si)))
            si = si[0]
            ei = [i for i in range(si + 1, len(lines)) if lines[i].startswith(j["end"])][0]
            rm = [i for i in range(si, ei) if j["pred"](lines[i])]
            if not rm or len(rm) != j.get("expect", len(rm)):
                sys.exit("%s: filter removed %d (expect %s)" % (j["id"], len(rm), j.get("expect")))
            old = "\n".join(lines[i] for i in rm)
            keep = [lines[i] for i in range(si, ei) if i not in set(rm)]
            if j.get("note"):
                k2 = len(keep)
                while k2 > 0 and keep[k2 - 1].strip() == "":
                    k2 -= 1
                keep[k2:k2] = ["", j["note"]]
            lines[si:ei] = keep
            t = nl.join(lines)
        elif j["mode"] == "sub":
            c = t.count(j["old"])
            if c != 1:
                sys.exit("%s: old occurs %d times" % (j["id"], c))
            old, t = j["old"], t.replace(j["old"], j["new"])
        else:
            lines = t.split(nl)
            si = [i for i, l in enumerate(lines) if l.startswith(j["start"])]
            if len(si) != 1:
                sys.exit("%s: start occurs %d times" % (j["id"], len(si)))
            si = si[0]
            if j.get("end") is None:
                ei = si + 1
            else:
                ei = [i for i in range(si + 1, len(lines)) if lines[i].startswith(j["end"])]
                if not ei:
                    sys.exit("%s: end not found" % j["id"])
                ei = ei[0]
            old = "\n".join(lines[si:ei])
            new = [] if j["new"] == "" else j["new"].split("\n")
            lines[si:ei] = new
            t = nl.join(lines)
        texts[k] = t
        out.append("\n## %s -- design %s %s\n\n%s\n" % (j["id"], k, j["title"], old))
    for k, t in texts.items():
        open(W + DOCS[k], "wb").write(t.encode("utf-8"))
    if os.path.exists(HIST):
        h = open(HIST, "rb").read().decode("utf-8")
    else:
        h = HEAD
    h += "".join(out)
    open(HIST, "wb").write(h.encode("utf-8"))
    print("applied", len(mod.JOBS), "jobs")


if __name__ == "__main__":
    run(sys.argv[1])
