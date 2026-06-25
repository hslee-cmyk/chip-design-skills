# bkit/workflow/ — RD-PDCA sub-step 프로파일 (swappable)

PDCA phase를 도메인 sub-step으로 세분화하는 **단일 소스**. bkit 9-phase 상태머신은 건드리지 않고,
각 phase 안을 council/swarm sub-step으로 나눈다 (RD-PDCA Team Overlay, `../../docs/04-bkit-customization-guide.md` 참조).

## 파일

- `substeps.<profile>.json` — 프로파일. 기본 제공: `substeps.common.json` (venezia-fpga 기준 digital RTL/FPGA).
- 향후 도메인 추가 = **새 파일만 추가**: 예) `substeps.neural-asic.json` (analog AFE/rectifier/stim sub-step 포함).

## 스키마

```jsonc
{
  "profile": "common",            // 식별자 (== 파일명 substeps.<profile>.json)
  "title": "...", "version": "1.0",
  "phases": {
    "design": {                   // bkit PDCA phase 이름 (design|do|check)
      "pattern": "council",       // council(병렬 검토) | swarm(병렬 구현)
      "doc": "design.template.md",// 생성될 bkit 템플릿 파일명
      "substeps": [
        { "id": "system-arch", "title": "System Architecture",
          "owner": "verilog-rtl-architect-advisor",  // Task 위임 대상 agent
          "skill": "verilog-rtl",                     // sub-agent가 로드할 스킬(선택)
          "gate": true,                               // true면 phase 종료 전 PASS 필수
          "checklist": ["...", "..."] }               // 템플릿/프롬프트에 들어갈 점검 항목
      ]
    }
  }
}
```

## 교체(swap) 절차 — 대규모 업데이트에도 쉬움

sub-step은 **데이터**이고, agent(`chip-cto-lead`)와 템플릿은 그걸 *읽거나 생성*만 한다. 따라서:

1. `substeps.common.json` 을 수정하거나, 새 `substeps.<name>.json` 추가.
2. 재생성:
   ```bash
   python install.py --gen-rd-pdca --project <repo>                 # common 프로파일
   python install.py --gen-rd-pdca --profile neural-asic --project <repo>
   ```
   → `<repo>/.ai/rd-pdca-substeps.json` (agent가 읽는 활성 프로파일) +
     `<repo>/.ai/bkit-templates/{design,do,analysis}.template.md` (프로파일로부터 **생성**) 갱신.
3. `chip-cto-lead` agent와 `install.py` 생성기는 **변경 불필요** — 프로파일만 바뀌면 council/swarm·템플릿이 따라온다.

> 즉 "phase 세분화 내용"은 전부 이 폴더의 JSON 한 곳에 모인다. 도메인이 바뀌어도 JSON 교체 + 재생성이 전부.

## 활성 프로파일은 어디에?

- **소스**(편집): `bkit/workflow/substeps.<profile>.json` (이 repo)
- **배포본**(agent가 런타임에 읽음): `<repo>/.ai/rd-pdca-substeps.json` (생성기가 복사)
- 템플릿은 배포본에서 파생 → bkit은 `.ai/bkit-templates/`를 CLAUDE.md-redirect로 읽음(§ templates 우회, docs/04 §7).
