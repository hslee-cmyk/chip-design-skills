# B47 재생성 명령 -- 문서 커밋 D (오케스트레이터, card 20261001-topology-md-sync 순서 1)

측정 기준: gate `master` `a796468`(2026-10-01). 사본(`C:/g95`, 측정 뒤 삭제)에서 아래와 같은 형태로 실행해 확인했다.
경로표: `skills/analog-gmid-design/assets/library/*.topology.md` = 오케스트레이터, 조건 `없음`(계획 N3.12.2 636행) -- 승인 기록 불필요. json은 건드리지 않는다.
전제: 사용자 B47 질문 (1) 답(재생성 진행)을 받았다. 실행 셸은 MSYS2 bash. 같은 bash 호출 안에서 위에서 아래로 실행한다(`set -e`).

```bash
set -euo pipefail
R=/c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
PY=/c/Python314/python.exe
L=skills/analog-gmid-design/assets/library

# 0. 시작 상태: library 작업 트리 깨끗, HEAD = gate master 머리(이 값이 measured_at = D^)
git -C "$R" fetch gate
test -z "$(git -C "$R" status --porcelain -- "$L")"
git -C "$R" rev-parse HEAD gate/master          # 두 값이 같아야 한다. 기록해 둔다(= measured_at)
# 렌더러·json이 a796468 이후 바뀌었으면(아래가 비지 않으면) 이 문서의 기대 blob id는 무효 -- 다시 잰다
git -C "$R" diff --name-only a796468 HEAD -- "$L" skills/analog-gmid-design/assets/topology_to_markdown.py skills/analog-gmid-design/assets/stick_diagram.py

# 1. 낡은 2개만 제자리 재생성 -- cwd = assets, 인자 = library/<n>.topology.json (다른 md 5개의 `소스:` 줄 형식과 같게)
cd "$R/skills/analog-gmid-design/assets"
for n in folded_cascode current_reuse_telescopic_ota; do
  "$PY" -B topology_to_markdown.py "library/$n.topology.json" > /dev/null
done

# 2. 나머지 4개는 추적 파일을 건드리지 않고 임시 경로로 렌더링해 차이 0 확인(둘째 인자 = 출력 경로)
T=$(mktemp -d)
for n in ngcc_3stage_ff pushpull_follower_buffer sf_pushpull_output_opamp two_stage_ota_sf; do
  "$PY" -B topology_to_markdown.py "library/$n.topology.json" "$T/$n.topology.md" > /dev/null
  diff --strip-trailing-cr "library/$n.topology.md" "$T/$n.topology.md"   # 출력 없음 = 차이 0 (차이가 있으면 set -e로 멈춤)
done
rm -rf "$T"

# 3. 바뀐 경로가 정확히 2개, 그 밖(json·다른 md·__pycache__) 0
git -C "$R" status --porcelain                    # library 아래로는 아래 두 줄만(다른 기존 미추적 파일은 무관)
git -C "$R" diff --numstat -- "$L"
#   기대: 5  5  .../folded_cascode.topology.md
#         12 6  .../current_reuse_telescopic_ota.topology.md
git -C "$R" diff -- "$L/folded_cascode.topology.md"   # 기대 내용: `소스:` 줄(skills/analog-gmid-design/assets/library/... -> library/...),
                                                      # Net 표 vin_n·vin_p 행 단자 맞바뀜, 소자 표 M1 Gate vin_p->vin_n, M2 Gate vin_n->vin_p
git -C "$R" diff -- "$L/current_reuse_telescopic_ota.topology.md"  # 기대 내용: Net 표 Vim·Vip·Vom·Vop·gnd 행에 CL/Cf/Cs 단자 추가,
                                                      # 수동 소자 표 CL1·CL2·Cf1·Cf2·Cs1·Cs2 6행 추가, 합계 "6개 수동소자" -> "12개 수동소자"

# 4. 내용 확인: 스테이징한 blob(LF 정규화)이 사본 실측 기대 blob과 같다
git -C "$R" add -- "$L/folded_cascode.topology.md" "$L/current_reuse_telescopic_ota.topology.md"
git -C "$R" ls-files -s -- "$L/folded_cascode.topology.md" "$L/current_reuse_telescopic_ota.topology.md"
#   기대: 711a59108bd53891ea410963e235617a6955b416  folded_cascode.topology.md
#         2a3e67a5ccef1aae8829688bedaa3098b57d74e2  current_reuse_telescopic_ota.topology.md
git -C "$R" diff --cached --name-only            # 정확히 위 두 경로

# 5. 커밋(Role: doc, Change-Id = card id). push는 단독 호출로 하고 전체 출력을 확인한다(병렬·tail 금지)
git -C "$R" commit -F - <<'MSG'
docs: B47 library topology.md 재생성 20261001-topology-md-sync(folded_cascode M1/M2 게이트 넷 -- 7ec8eff 극성 정정 반영, current_reuse_telescopic_ota CL/Cf/Cs 수동 소자 6개 -- 8ae82e7 보상망 connectivity 반영), 나머지 4개 md 차이 0

json connectivity를 고친 두 커밋(8ae82e7 2026-09-10, 7ec8eff 2026-09-17)이 topology_to_markdown.py를 다시 돌리지 않아 md가 낡았다.
assets에서 `python -B topology_to_markdown.py library/<n>.topology.json`으로 두 파일만 다시 만들었다(folded의 `소스:` 줄도 다른 md와 같은
`library/...` 형식이 된다). json·엔진·test 불변. 이 md를 읽는 test·게이트·기준선은 없다(판정 불변, DEC-40 무관).
다음 card 20261001-topology-md-sync(test-only)가 md 표와 json의 일치를 영구 test로 잡는다 -- 이 커밋의 부모가 그 card의 measured_at이다.

Role: doc
Change-Id: 20261001-topology-md-sync
Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
MSG
git -C "$R" log -1 --format='%H %P'               # %P(부모) = 0단계에서 기록한 measured_at
git -C "$R" status --porcelain -- "$L"            # 빈 출력
```

```bash
# 6. push -- 단독 호출, 전체 출력 확인 후에만 다음 단계
git -C /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills push gate master
```

## 주의

* 저장소 루트에서 `python topology_to_markdown.py skills/analog-gmid-design/assets/library/<n>.topology.json`처럼 실행하면 `소스:` 줄이 긴 경로가 된다(옛 folded 형식). 반드시 assets를 cwd로, `library/<n>.topology.json` 인자로 실행한다.
* 둘째 인자 없이 실행하면 추적 md를 덮어쓴다 -- 2단계의 4개는 반드시 임시 출력 경로를 준다.
* `-B`로 실행해 `__pycache__`를 만들지 않는다(3단계 status에 나오면 지운다 -- 추적 대상 아님 확인 후).
* 작업 트리 md는 CRLF로 써지고(`core.autocrlf=true`, `.gitattributes` 속성 없음) 커밋 때 LF로 정규화된다. 4단계 blob id는 LF 정규화 값이다.
* 0단계의 `git diff --name-only a796468 HEAD -- ...`가 비지 않으면(그 사이 library json·렌더러 변경) 기대 numstat·blob id를 다시 재고, card 계약 9의 blob id도 같이 고친다.
