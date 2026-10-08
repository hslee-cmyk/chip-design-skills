"""단계 A 보고서 쓰기 (pipeline CONTRACT 단계 A 절).

진입점: `write_stage_a_report(report, output_dir, stem) -> tuple`  ((json 경로, md 경로)).

`report` = JSON 으로 쓸 수 있는 dict. `<stem>.stage_a.json`(전체, 키 정렬) 과 `<stem>.stage_a.md`(사람이 읽는 요약: 상태·정지 사유·review_needed·뷰별
블록·루프 요약·적용한 ratified 사실·feedforward 비율 후보·루프 역할)를 `output_dir` 에 쓴다. 디렉터리는 없으면 만든다. 기존 파일은 덮어쓴다(실행 산출물, .gitignore 대상 폴더에 둘 것).
"""
import json
from pathlib import Path


def _markdown(report):
    lines = ["# 단계 A 보고서: " + report["circuit"], "", "- 상태: " + report["status"] + " (exit " + str(report["exit_code"]) + ")",
             "- N_S(계수 예산): " + str(report["count_budget"]), "- declared 대조: " + report["declared_comparison"], ""]
    if report["stop_reasons"]:
        lines += ["## 정지 사유"] + ["- " + r for r in report["stop_reasons"]] + [""]
    if report["review_needed"]:
        lines += ["## review_needed"] + ["- " + r for r in report["review_needed"]] + [""]
    if report.get("applied_facts"):
        lines += ["## 적용한 ratified 사실"] + ["- " + concept + " " + subject for concept, subject in report["applied_facts"]] + [""]
    if report.get("ff_ratio_candidates"):
        lines += ["## feedforward 비율 제약 후보 (값은 spec 이 선언할 때만 제약)"]
        lines += ["- " + c["view"] + " " + c["ff"] + ": " + c["relation"] + " (우회 블록 " + str(c["bypassed_block"]) + ", 출처 " + c["source"] + ")"
                  for c in report["ff_ratio_candidates"]] + [""]
    for view in report["views"]:
        lines.append("## 뷰 " + view["id"] + " (" + view["kind"] + ")")
        lines += ["- 블록: " + ", ".join(b["kind"] + str(b["key"]) + "@s" + str(b["stage"]) for b in view["blocks"]),
                  "- 루프: " + str(view["loop_count"]) + ", 끊는 점: " + str(view["cuts"]) + ", 극성: " + str(view.get("polarity", 0))]
        if view.get("feedforward"):
            lines += ["- feedforward: " + ", ".join(f["id"] + str(f["cells"]) + " 부호 " + str(f["sign"]) for f in view["feedforward"])]
        if view.get("loop_roles"):
            lines += ["- 루프 역할: " + ", ".join(r["loop_id"] + "=" + r["role"] for r in view["loop_roles"])]
        lines.append("")
    return "\n".join(lines) + "\n"


def write_stage_a_report(report, output_dir, stem):
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)
    json_path = folder / (stem + ".stage_a.json")
    md_path = folder / (stem + ".stage_a.md")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    md_path.write_text(_markdown(report), encoding="utf-8")
    return str(json_path), str(md_path)
