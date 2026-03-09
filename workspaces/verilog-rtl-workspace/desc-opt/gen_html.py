import json

template_path = "C:/Users/HSLEE/.claude/skills/skill-creator/assets/eval_review.html"
with open(template_path, encoding='utf-8') as f:
    template = f.read()

skills = [
    {
        "name": "verilog-rtl",
        "desc": "Verilog/SystemVerilog RTL 설계 및 분석 skill. RTL 코드 작성, 사이클 분석, 합성 가능성 검토, 코드 리뷰, 모듈 통합, SV Coverage 설계, Verilator lint",
        "eval": "C:/Users/HSLEE/.claude/skills/verilog-rtl-workspace/desc-opt/trigger-eval.json",
        "out": "C:/Users/HSLEE/.claude/skills/verilog-rtl-workspace/desc-opt/eval_review.html"
    },
    {
        "name": "verilog-a",
        "desc": "Verilog-A 아날로그 behavioral 모델링 skill. 수렴 최적화, transition 필터, 피드백 시스템, Mixed-signal 인터페이스",
        "eval": "C:/Users/HSLEE/.claude/skills/verilog-a-workspace/desc-opt/trigger-eval.json",
        "out": "C:/Users/HSLEE/.claude/skills/verilog-a-workspace/desc-opt/eval_review.html"
    },
    {
        "name": "lattice-fpga",
        "desc": "Lattice FPGA 합성/구현/검증 workflow. iCEcube2/Radiant/Diamond 환경, RTL 합성, 타이밍 분석, 비트스트림 생성, 하드웨어 검증",
        "eval": "C:/Users/HSLEE/.claude/skills/lattice-fpga-workspace/desc-opt/trigger-eval.json",
        "out": "C:/Users/HSLEE/.claude/skills/lattice-fpga-workspace/desc-opt/eval_review.html"
    },
    {
        "name": "uvm-verification",
        "desc": "UVM 검증환경 설계 skill. agent/env/test 계층, driver/monitor/sequencer, RAL, Factory/Config DB, Coverage, Package Organization",
        "eval": "C:/Users/HSLEE/.claude/skills/uvm-verification-workspace/desc-opt/trigger-eval.json",
        "out": "C:/Users/HSLEE/.claude/skills/uvm-verification-workspace/desc-opt/eval_review.html"
    },
    {
        "name": "chip-verification",
        "desc": "RTL-UVM 통합 검증환경 skill. 듀얼탑 구조, RTL-TB 인터페이스, Reference Model, Scoreboard, AMS 검증환경, 회귀 테스트 전략",
        "eval": "C:/Users/HSLEE/.claude/skills/chip-verification-workspace/desc-opt/trigger-eval.json",
        "out": "C:/Users/HSLEE/.claude/skills/chip-verification-workspace/desc-opt/eval_review.html"
    }
]

for s in skills:
    with open(s["eval"], encoding='utf-8') as f:
        eval_data = json.load(f)
    html = template
    html = html.replace("__SKILL_NAME_PLACEHOLDER__", s["name"])
    html = html.replace("__SKILL_DESCRIPTION_PLACEHOLDER__", s["desc"])
    html = html.replace("__EVAL_DATA_PLACEHOLDER__", json.dumps(eval_data, ensure_ascii=False))
    with open(s["out"], "w", encoding='utf-8') as f:
        f.write(html)
    print(f"Created: {s['out']}")
print("All done!")
