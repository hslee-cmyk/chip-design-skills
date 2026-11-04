"""Adds measured circuit entries to the baseline fixture by byte insertion (existing bytes untouched).
usage: add_entries.py <fixture> <measure jsonl> <circuit> [<circuit> ...]
Verifies: raw format round trip before, parsed old entries identical after, every old line still present in order."""
import json
import sys

F, M, wanted = sys.argv[1], sys.argv[2], sys.argv[3:]
raw = open(F, "rb").read()
old = json.loads(raw.decode("utf-8"))
NL = b"\r\n"


def dump(obj):
    return json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False).encode("utf-8").replace(b"\n", NL)


assert dump(old) + NL == raw, "fixture format is not indent=1 sort_keys CRLF"
measured = {}
for line in open(M, encoding="utf-8"):
    r = json.loads(line)
    measured[r["circuit"]] = r
assert not set(wanted) & set(old)
new = dict(old)
for c in wanted:
    r = measured[c]
    assert r["second_run_identical"] == [True, True, True], c
    new[c] = r["entry"]
new["_source_o227"] = ("[O-227 (2) 2026-11-04] r2r_opamp, rfc_ota 항목: 판정자(audit)가 master 5671a6c7 + test 커밋 ede4f440 격리 복제본에서 잰 값. 재는 법 = 이 파일 ngcc_3stage_ff 항목과 같은 "
                       "꼴(status != [ok, ok] 회로: stage_a_sha = 단계 A 보고서에서 env_fp 뺀 키, stage_b_sha = 단계 B 보고서에서 achievability 뺀 키, achievability_sha = achievability 키, "
                       "sha = test_s0_layer_9circuits._sha, 사슬 두 번 비트 동일 확인, OPENBLAS_NUM_THREADS=1). 같은 도구가 ngcc_3stage_ff·common_gate_amplifier·two_stage_ota 항목을 그대로 재현함을 대조했다. "
                       "두 회로의 status 는 [ok, ok] 가 아니다(r2r = stopped: 단계 A 정지 3건, rfc = review_needed) -- 회귀 기준선이지 '회로 정상' 표지가 아니다. "
                       "cnr_ota, erfc_ota 는 단계 B 정지(achievability 없음)라 넣지 않았다. 판정 기록 .ai/verification/20261104-o227/verdict.json.")
out = dump(new) + NL
open(F, "wb").write(out)
back = json.loads(out.decode("utf-8"))
for k in old:
    assert back[k] == old[k], k
# order-preserving subsequence check on lines: no old line removed or changed
oi = iter(out.split(NL))
missing = [ln for ln in raw.split(NL) if not any(ln == x for x in oi)]
print("old lines missing:", len(missing), "new keys:", sorted(set(back) - set(old)), "old entries unchanged:", len(old))
assert not missing
