"""M-TH1c 새 소비자 판정: 두 consumers.jsonl의 (파일, how, name) 키 차. 엔진 import 0.

사용: python m_th1c_diff.py <base consumers.jsonl> <head consumers.jsonl>
출력: 새 키, 없어진 키. 새 키가 있으면 종료 코드 1. `gm_id_field_text`(순방향 칸 텍스트 적중)는 키 밖이다.
"""
import json
import sys


def keys(path):
    with open(path, encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    return {(r["file"], r["how"], r["name"]) for r in rows if r["how"] != "gm_id_field_text"}


base, head = keys(sys.argv[1]), keys(sys.argv[2])
new, gone = sorted(head - base), sorted(base - head)
print("new=%d gone=%d" % (len(new), len(gone)))
for k in new:
    print("NEW", *k)
for k in gone:
    print("GONE", *k)
sys.exit(1 if new else 0)
