"""V3 범위 정책 card(20260930-v3-changed-stmt-scope) -- 사용자 결정 A1-b 정정(2026-10-01) 'T6 넓힘' 재측정.

T6 넓힌 판(T6w) = (기존 T6) 삭제 지점 바로 뒤 문장
               ∪ 바뀐 영역(새 문장 / 머리 변경 복합문의 자기 필드 / 지운 문장)이 '바꾸는 이름'을 읽는,
                 같은 블록(head 목록)에서 그 영역 뒤에 오는 문장의 몫.
  * '뒤' = 새·머리 변경 문장은 위치 > j, 지운 문장은 삭제 지점 위치 >= j.
    그 블록이 반복문(for/async for/while)의 body면 위치와 무관하게 그 블록의 다른 모든 문장(다음 회차로 흐름).
  * '바꾸는 이름' = Name(Store/Del) + Attribute/Subscript 대입·삭제 대상의 맨 앞 Name + 메서드 호출 a.b(...)의 맨 앞 Name a
    + except 절 이름.
  * 문장이 '읽는다' = 단순문은 부분 트리 전체의 Name(Load), 복합문은 자기 필드(블록 필드 밖)의 Name(Load). 몫 = 기존 정의.
N2w = N2b(card 기본 N2) ∪ T6w.
도구 함수만 읽기 전용 import(v3_scope_classify 경유), 도구 main은 돌리지 않는다.
결과: C:/g103/out/v3_scope_widen.txt/.json (케이스마다 append)
"""
import ast, difflib, json, re, sys

sys.path.insert(0, "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26_reconcile")
import v3_scope_classify as V   # noqa: E402
S, mc, rch = V.S, V.mc, V.rch

OUTJ = "C:/g103/out/v3_scope_widen.json"
LOOPS = (ast.For, ast.AsyncFor, ast.While)
_JP = re.compile(r"^(?:(.*)\.)?([A-Za-z_]+)\[(\d+)\]$")


def _root(n):
    while isinstance(n, (ast.Attribute, ast.Subscript, ast.Starred)):
        n = n.value
    return n.id if isinstance(n, ast.Name) else None


def _roots(node, own_only):
    if not own_only:
        return [node]
    out = []
    for f, v in ast.iter_fields(node):
        if f in V.BLOCK:
            continue
        if isinstance(v, list):
            out += [x for x in v if isinstance(x, ast.AST)]
        elif isinstance(v, ast.AST):
            out.append(v)
    return out


def mod_names(node, own_only=False):
    out = set()
    for r in _roots(node, own_only):
        for x in ast.walk(r):
            if isinstance(x, ast.Name) and isinstance(x.ctx, (ast.Store, ast.Del)):
                out.add(x.id)
            elif isinstance(x, (ast.Attribute, ast.Subscript)) and isinstance(x.ctx, (ast.Store, ast.Del)):
                r0 = _root(x)
                if r0:
                    out.add(r0)
            elif isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute):
                r0 = _root(x.func)
                if r0:
                    out.add(r0)
    if isinstance(node, ast.ExceptHandler) and node.name:
        out.add(node.name)
    return out


class MatchW(V.Match):
    """V.Match.block과 같은 알고리즘 + 사이트(블록, 위치, 바뀐 이름) 기록."""

    def __init__(self):
        super().__init__()
        self.sites = []   # (owner, field, j, strict, names)

    def block(self, bl, hl, owner, field):
        sm = difflib.SequenceMatcher(None, [V.fp(x) for x in bl], [V.fp(x) for x in hl], autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            if tag == "insert":
                for j in range(j1, j2):
                    self.new.append(V.jp(owner, field, j))
                    self.sites.append((owner, field, j, True, mod_names(hl[j])))
                continue
            if tag == "delete":
                self.dels.append((owner, field, j1))
                self.del_nodes += bl[i1:i2]
                self.sites.append((owner, field, j1, False, set().union(*[mod_names(n) for n in bl[i1:i2]])))
                continue
            free = list(range(i1, i2))
            for j in range(j1, j2):
                h = hl[j]
                pick = None
                if V.is_compound(h):
                    for i in free:
                        if type(bl[i]) is type(h) and V.is_compound(bl[i]) and V.hfp(bl[i]) == V.hfp(h):
                            pick = i
                            break
                    if pick is None:
                        for i in free:
                            if type(bl[i]) is type(h) and V.is_compound(bl[i]):
                                pick = i
                                break
                if pick is None:
                    self.new.append(V.jp(owner, field, j))
                    self.sites.append((owner, field, j, True, mod_names(h)))
                    continue
                free.remove(pick)
                b = bl[pick]
                hp = V.jp(owner, field, j)
                if V.hfp(b) != V.hfp(h):
                    self.hdr.append(hp)
                    self.sites.append((owner, field, j, True, mod_names(h, own_only=True) | mod_names(b, own_only=True)))
                for f in V.BLOCK:
                    bv, hv = getattr(b, f, None), getattr(h, f, None)
                    if isinstance(hv, list) or isinstance(bv, list):
                        self.block(bv or [], hv or [], hp, f)
            if free:
                self.dels.append((owner, field, j2))
                self.del_nodes += [bl[i] for i in free]
                self.sites.append((owner, field, j2, False, set().union(*[mod_names(bl[i]) for i in free])))


def t6w(bfn, hfn):
    """넓힌 T6 대상 문장 경로 (단순문 목록, 복합문 목록) -- 이름 규칙 몫만(기존 T6 '바로 뒤'는 classify의 T6)."""
    M = MatchW()
    M.block(bfn.body, hfn.body, "", "body")
    pn = {p: n for n, p in mc._path_nodes(hfn)}
    simple, comp = set(), set()
    for owner, field, j, strict, names in M.sites:
        if not names:
            continue
        own_node = pn[owner] if owner else hfn
        lst = getattr(own_node, field, None) or []
        loop = field == "body" and isinstance(own_node, LOOPS)
        for k, s in enumerate(lst):
            if loop:
                if strict and k == j:
                    continue
            elif (k <= j) if strict else (k < j):
                continue
            if not isinstance(s, (ast.stmt, ast.ExceptHandler, ast.match_case)):
                continue
            c = V.is_compound(s)
            _st, ld = V.names(s, own_only=c)
            if ld & names:
                (comp if c else simple).add(V.jp(owner, field, k))
    # 검증: MatchW가 V.Match와 같은 new/hdr/dels를 만든다
    M0 = V.Match()
    M0.block(bfn.body, hfn.body, "", "body")
    assert (M0.new, M0.hdr, M0.dels) == (M.new, M.hdr, M.dels), "MatchW != Match"
    return sorted(simple), sorted(comp)


_classify_orig = V.classify


def classify_w(bfn, hfn, src, hmap=None, executed=None):
    rows, info = _classify_orig(bfn, hfn, src, hmap, executed)
    ts, tc = t6w(bfn, hfn)
    for t in rows:
        op, mpath = t["op"], t["path"]
        if op == "early_return":
            t["T6w"] = False
            continue
        np_ = V.node_path(op, mpath)
        hd = op in ("stmt_delete", "except_body_delete")
        t["T6w"] = any(V.under(np_, q) for q in ts) or any(V.own(np_, q) or (hd and np_ == q) for q in tc)
    info["t6w"] = len(ts) + len(tc)
    return rows, info


V.DEFS["N2w"] = lambda t: V.DEFS["N2b"](t) or t.get("T6w", False)


if __name__ == "__main__":
    V.OUTT = "C:/g103/out/v3_scope_widen.txt"
    open(V.OUTT, "w").close()
    with open("C:/g103/out/executed_lines.json", encoding="utf-8") as fh:
        V.EXEC = json.load(fh)
    V.classify = classify_w          # measure()가 부르는 모듈 전역 교체
    res = {}
    p9b = dict(S.BASEF); p9b[S.SD] = V.git_show("7535799", S.SD)
    p9h = dict(p9b); p9h[S.SD] = V.git_show("b7765b0", S.SD)
    res["p9_real"] = V.measure("P9 실제(7535799 -> b7765b0)", p9b, p9h)
    b26, _ = S.build_b26(S.BASEF)
    res["b26_1_sim"] = V.measure("B26-1 시뮬레이션(build_b26)", S.BASEF, b26)
    res["b34_v2"] = V.measure("B34 좁힌 초안(사이트 1·2·3·11·11b)", S.BASEF, V.build_b34(S.BASEF))
    for k, r in res.items():
        V.log("== 요약 %s: all=%d N2b=%d N2w=%d D1b=%d | 하한 N2w %.1f min, 상한 N2w %.2f h, 현실 하한 N2b=%.2f h N2w=%.2f h | 미실행 줄 대상 변이 N2b=%d N2w=%d" % (
            k, r["totals"]["all"], r["totals"]["N2b"], r["totals"]["N2w"], r["totals"]["D1b"], r["low_min"]["N2w"], r["high_h"]["N2w"],
            r["realistic_low_h"]["N2b"], r["realistic_low_h"]["N2w"], r["unexec"]["N2b"], r["unexec"]["N2w"]))
        for row in r["rows"]:
            if row.get("N2w") != row.get("N2b"):
                V.log("   %s::%s all=%d N2b=%d N2w=%d D1b=%d (t6w 문장 %s)" % (row["path"].split("/")[-1], row["def_"], row["all"], row["N2b"],
                                                                     row["N2w"], row["D1b"], row.get("t6w")))
    with open(OUTJ, "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
