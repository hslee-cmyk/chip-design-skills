# trimfx_fd_rcmfb -- connectivity 표 (후보 C, 초안·사용자 확인용)

* 출처 파일: `wt/_drafts/trim_fixture/C_trimfx_fd_rcmfb/trimfx_fd_rcmfb.topology.json`
* 만든 방법: 새 엔진 로더 `load_topology`(master 944020f, 격리 worktree)로 읽어 직접 뽑았다.
* connectivity_fp = `5a5eb324b010091ebbd7139f59f6e65cc30cb402edf05481fe95c2b43bbf2441`
* 회로(새로 씀, 해석 공동 확인 필요): 완전 차동 1단. NMOS 차동쌍 M1·M2 + 꼬리 M5 + PMOS 전류원 부하 M3·M4. 부하 게이트 cms = 두 출력을 Rcm1·Rcm2 로 평균한 공통모드 감지점(저항 감지 CMFB 를 부하 게이트에 직접). 차동 신호에서 cms 는 교류 접지, 공통모드에서는 부하가 다이오드처럼 동작.
* **단계 A 실측 결과: 정지(exit 2)** -- 아래 '엔진 유도' 참조. 지금 엔진으로는 structure.json 사실 없이 쓸 수 없다.

## Net별 연결 표

| Net | 구분 | 연결된 단자 | 단자 수 |
|---|---|---|---|
| `bias` | 외부 바이어스(bias_inputs) | M5.gate | 1 |
| `cms` | 내부 | M3.gate, M4.gate, Rcm1.t1, Rcm2.t1 | 4 |
| `gnd` | 레일 | CL1.t1, CL2.t1, M5.source | 3 |
| `tail` | 내부 | M1.source, M2.source, M5.drain | 3 |
| `vdd` | 레일 | M3.source, M4.source | 2 |
| `vim` | 포트 differential_input_n | M2.gate | 1 |
| `vip` | 포트 differential_input_p | M1.gate | 1 |
| `vom` | 포트 differential_output_n | CL2.t0, M1.drain, M3.drain, Rcm2.t0 | 4 |
| `vop` | 포트 differential_output_p | CL1.t0, M2.drain, M4.drain, Rcm1.t0 | 4 |

## 소자별 단자

| 소자 | kind | drain | gate | source | bulk |
|---|---|---|---|---|---|
| M1 | nmos | vom | vip | tail | (생략 -- 엔진 기본 규칙) |
| M2 | nmos | vop | vim | tail | (생략 -- 엔진 기본 규칙) |
| M3 | pmos | vom | cms | vdd | (생략 -- 엔진 기본 규칙) |
| M4 | pmos | vop | cms | vdd | (생략 -- 엔진 기본 규칙) |
| M5 | nmos | tail | bias | gnd | (생략 -- 엔진 기본 규칙) |

| 2단자 소자 | kind | t0 | t1 |
|---|---|---|---|
| CL1 | capacitor | vop | gnd |
| CL2 | capacitor | vom | gnd |
| Rcm1 | resistor | vop | cms |
| Rcm2 | resistor | vom | cms |

## 극성 확인

vip 상승 -> M1 전류 증가 -> vom 하강, M2 전류 감소 -> vop 상승. 따라서 vip -> (vop - vom) 비반전.

## trim에 관계된 엔진 유도(실측)

* S1 matching group: `diff_pair (M1, M2) derived`, `mirror (M3, M4) derived`(엔진은 gate 공유 쌍을 mirror 로 분류).
* 주입 쌍(design §9.1 예상): n_p = M1.drain = **vom**, n_n = M2.drain = **vop**. 차동 출력이라 기준 선언 불필요.
* 단계 A(`run_stage_a`, 실 LUT) **stopped, exit 2**:
  - `unsupported_rule_branch | loop_record_only | transfer:0 | cms,vom | global_feedback_or_cross_coupled` (vop 쪽도 같음) -- 저항 감지 CM 루프를 엔진 규칙이 '기록만'으로 둔다.
  - `review_needed | dc_role_unresolved_group | M3,M4` -- gate 가 신호 넷(cms)이라 DC 역할을 구조로 못 가른다(dc_role 사실 필요).
  - `review_needed | l_owner_name_order | M3,M4`.
* 풀려면 structure.json ratified 사실(dc_role, ac_ground_exception 등 -- current_reuse 의 `ac_ground_exception Vbias2` 와 같은 종류)이 필요하고, 그것은 사용자 승인·rule_hash 절차(T-11·T-16) 대상이다.
