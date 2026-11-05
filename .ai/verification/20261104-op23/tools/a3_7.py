# -*- coding: utf-8 -*-
"""A3-7 593 변화표. 입력 = OP-1 기준선의 옛 형식 입력 전부, 변환 = op1b_lib.convert_input(§11.5 (i) 기계적 대응 + kinds 값 null).
LUT 경로는 커밋된 npz(같은 폴더 또는 _test_tmp_map 대응)와 5fea301e sample blob 으로 옮긴다. 모델 기록을 넣지 않는다.
오라클 main 을 프로세스 안에서 부른다. 기대: 시뮬레이터 실행 0(모두 실행 전 거부), 입력별 (사유, 단계). 케이스마다 파일에 쓴다.
사용: a3_7.py <iso_v> <work> <exe> <out.jsonl>
"""
import collections, contextlib, glob, hashlib, io, json, os, shutil, subprocess, sys

ISO, WORK, EXE, OUT = sys.argv[1:5]
O = os.path.join(ISO, "skills/analog-gmid-design/tools/spice_oracle")
BL = os.path.join(ISO, ".ai/verification/20261016-op1-baseline/baseline")
sys.path.insert(0, O)
sys.path.insert(0, os.path.join(ISO, ".ai/verification/20261104-op1b/scripts"))
import op1b_lib as L  # noqa: E402
import oracle_run  # noqa: E402

DESC = os.path.join(O, "descriptors/sky130.oracle_descriptor.json")
dsha = hashlib.sha256(open(DESC, "rb").read().replace(b"\r\n", b"\n")).hexdigest()
os.makedirs(WORK, exist_ok=True)
sample = os.path.join(WORK, "sample.npz")
if not os.path.exists(sample):
    b = subprocess.run(["git", "-C", ISO, "cat-file", "blob", "5fea301e:skills/analog-gmid-design/assets/sky130_nfet_pfet_lut_sample.npz"], capture_output=True, check=True).stdout
    open(sample, "wb").write(b)
FILES = os.path.join(BL, "files")
# 입력 찾기
inputs = []
for f in glob.glob(FILES + "/**/*.json", recursive=True):
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    if isinstance(d, dict) and "devices" in d and "rails" in d and ("process" in d):
        inputs.append(f)
inputs.sort()


def locate(f, old):
    p = old["process"].get("lut_npz")
    if p is None:
        return None, "lut_absent"
    base = p.replace("\\", "/").split("/")[-1]
    # (1) 입력 폴더 또는 그 위에서 같은 이름
    d = os.path.dirname(f)
    for _ in range(3):
        c = os.path.join(d, base)
        if os.path.exists(c):
            return c, "committed"
        d = os.path.dirname(d)
    if "sample" in base:
        return sample, "sample_blob"
    q = p.replace("\\", "/")
    if "/pytest/tmp/" in q:                 # 다른 test 폴더의 LUT(모듈 공유 픽스처): 같은 상대 경로의 커밋 npz
        c = os.path.join(FILES, "pytest/tmp", q.split("/pytest/tmp/", 1)[1])
        if os.path.exists(c):
            return c, "committed_other_folder"
    return None, "lut_not_found:" + p[-60:]


out = open(OUT, "w", encoding="utf-8")
cnt = collections.Counter()
for i, f in enumerate(inputs):
    rel = os.path.relpath(f, FILES).replace("\\", "/")
    rec = {"i": i, "input": rel}
    try:
        old = json.load(open(f, encoding="utf-8"))
        lut, how = locate(f, old)
        rec["lut"] = how
        if lut is None:
            rec.update(code="STOP_LUT", stage=None)
        else:
            old2 = L.rewrite_lut_ref(old, lut.replace("\\", "/"))
            sha = hashlib.sha256(open(lut, "rb").read()).hexdigest()
            row = L.lut_files_row(old2, sha, "missing", [])
            new, _ = L.convert_input(old2, lut_files=row, descriptor={"path": DESC.replace("\\", "/"), "sha256": dsha}, adapter="ngspice", exe=EXE)
            d = os.path.join(WORK, f"c{i}")
            shutil.rmtree(d, ignore_errors=True)
            os.makedirs(d)
            ip = os.path.join(d, "t.input.json")
            json.dump(new, open(ip, "w", encoding="utf-8"), ensure_ascii=False)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = oracle_run.main([ip, os.path.join(d, "o"), "--bias", "free"])
            files = sorted(os.listdir(os.path.join(d, "o"))) if os.path.isdir(os.path.join(d, "o")) else []
            rec.update(rc=rc, files=files)
            rej = [x for x in files if x.endswith(".reject.json")]
            if rej and len(files) == 1:
                r = json.load(open(os.path.join(d, "o", rej[0]), encoding="utf-8"))
                rec.update(code=r["code"], stage=r["stage"], detail=r["detail"] if r["code"] != "oracle_input_schema_invalid" or len(str(r["detail"])) < 600 else str(r["detail"])[:600])
            else:
                rec.update(code="NOT_REJECTED", stage=None)
            shutil.rmtree(d, ignore_errors=True)
    except L.Op1bStop as e:
        rec.update(code="STOP_CONVERT:" + str(e.reason), stage=None)
    except Exception as e:  # 측정 도구: 입력별로 적고 계속한다(통과로 세지 않는다)
        rec.update(code="EXC:" + type(e).__name__, stage=None, msg=str(e)[:300])
    cnt[(rec.get("code"), rec.get("stage"))] += 1
    out.write(json.dumps(rec, ensure_ascii=False) + "\n")
    out.flush()
print(len(inputs), {str(k): v for k, v in cnt.items()})
