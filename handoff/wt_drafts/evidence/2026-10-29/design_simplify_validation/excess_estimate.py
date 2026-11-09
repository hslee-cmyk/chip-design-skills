# 남은 과잉 분량 추정(휴리스틱 -- 상한·하한 범위로만 읽는다). design/v115 fc874bd6 작업 트리.
# 범주:
#  H  머리(첫 '## ' 앞, Summary 줄 제외) -- 판 이력(라)
#  P  괄호 경위: '(' 로 시작해 짝 ')'까지 중 판·검증·결정 경위 단서를 가진 것(라). 중첩은 바깥만.
#  S  취소선 ~~...~~ (폐지 기록 본문)
#  O  '옛 문장/옛 문언/옛 정의' 가 든 문장(마침표 단위)(라)
#  R  'v1.x 대체 -- ' 표지가 붙은 본문 줄(대체 표가 정본, 본문은 기록이라 스스로 밝힌 줄)(O-169)
#  A  as-built 파일:줄 인용 수(`E/...py:N`) -- 분량 아님, 수
#  M  측정 수치 꼴(실측·ms·µW·% 와 숫자 범위)이 든 문장 바이트(라 후보)
import re, json
D = r'C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/docs/02-design/features/'
F = {'40': 'gain-budget-gmid-sizing.40-engine.design.md', '41': 'gain-budget-gmid-sizing.41-gain-budget.design.md',
     '42': 'gain-budget-gmid-sizing.42-gap-checklist.design.md'}
HIST = re.compile(r'v1\.\d|검증|재판정|재검증|gap |커밋|사용자 결정|승인 O-|옛 |철회|대체|정정|경위|history|판\b|원래 취지')
def parens(s):
    out = []; i = 0; n = len(s)
    while i < n:
        if s[i] == '(':
            d = 0; j = i
            while j < n:
                if s[j] == '(': d += 1
                elif s[j] == ')':
                    d -= 1
                    if d == 0: break
                j += 1
            seg = s[i:j + 1]
            out.append(seg); i = j + 1
        else:
            i += 1
    return out
res = {}
for k, fn in F.items():
    txt = open(D + fn, encoding='utf-8').read()
    b = lambda s: len(s.encode('utf-8'))
    first = txt.find('\n## ')
    head = txt[:first]
    summ = ''.join(l for l in head.split('\n') if l.startswith('> **Summary**'))
    H = b(head) - b(summ)
    body = txt[first:]
    P = 0; Pn = 0
    for line in body.split('\n'):
        for seg in parens(line):
            # 짝이 맞지 않는 괄호(줄 끝까지 삼킴)·과대 구간은 제외 -- 하한 쪽 추정
            if not seg.endswith(')') or len(seg) > 2500:
                continue
            if len(seg) >= 40 and HIST.search(seg):
                P += b(seg); Pn += 1
    S = sum(b(m) for m in re.findall(r'~~.*?~~', body, flags=re.S))
    sents = re.split(r'(?<=[.;])\s', body)
    O = sum(b(s) for s in sents if re.search(r'옛 (문장|문언|정의|본문|규칙|초안)', s))
    R = sum(b(l) for l in body.split('\n') if re.search(r'v1\.\d+(\.\d+)? 대체 --', l))
    A = len(re.findall(r'`?E/[\w/]+\.py:\d', body))
    M = sum(b(s) for s in sents if re.search(r'실측|측정', s) and re.search(r'\d+(\.\d+)?\s?(ms|µW|s\b|%|/\d+)', s))
    res[k] = dict(total_KB=round(b(txt) / 1024, 1), H_head_KB=round(H / 1024, 1), P_hist_paren_KB=round(P / 1024, 1), P_count=Pn,
                  S_strike_KB=round(S / 1024, 1), O_old_sentence_KB=round(O / 1024, 1), R_superseded_line_KB=round(R / 1024, 1),
                  A_asbuilt_line_refs=A, M_measure_sentence_KB=round(M / 1024, 1))
json.dump(res, open('excess_estimate.out.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
