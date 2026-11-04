# -*- coding: utf-8 -*-
"""oracle_netlist.py -- [OP-4 소유 잔여] C10 안정성 넷리스트 조각만 남은 파일 (card 20261104-op23, 위임 A-80 D-1).

OP-3 이 입력 -> 넷리스트 텍스트 경로(load_input·validate_input·build_netlist·write_netlists·main 등)를 코어 IR(`core/build_circuit`,
`core/build_benches`)과 어댑터 방언(`adapters/ngspice/dialect`)으로 옮기고 이 파일에서 지웠다. 아래 함수들은 안정성(C10)·pz 벤치 소유 card OP-4 가
`core/stability`·`core/build_benches`·어댑터 방언으로 옮기며 그때 이 파일을 지운다. **지금 호출자는 없다**(oracle_run 이 import 하지 않는다 --
기간 동안 PM 은 stability_unverified). 넷리스트 텍스트를 입력으로 받는 옛 모양 그대로이므로 새 경로에서는 쓸 수 없다.
"""

CHOKE_PREFIXES = ("Lfb_", "Ldc_", "Lhold_")      # 옛 넷리스트 이름 접두사 -- 새 IR 에서는 원소 역할 표(core/ir)가 대신한다


def _num(v):
    return format(float(v), ".10g")


def stability_op_netlist(text, nodes):
    """[신규 C10 안정성] 폐루프 .tran 넷리스트를 만들기 전 동작점 패스: text(오라클 넷리스트)의 .control 앞 본문 그대로에
    `op` 와 print(테스트벤치 choke 전류 i(<choke>), 주어진 SPICE 노드와 choke 회로 쪽 노드의 v(..))를 붙인다.
    반환 (텍스트, choke 이름 목록, 노드 목록). 이 패스의 값이 stability_netlist 의 choke_I·node_V 가 된다(같은 본문의 .op)."""
    body, chokes, nn = [], [], [n for n in nodes if n != "0"]
    for raw in text.splitlines():
        if raw.strip().lower().startswith(".control"):
            break
        body.append(raw)
        tok = raw.split()
        if tok and tok[0].startswith(CHOKE_PREFIXES):
            chokes.append(tok[0])
            if tok[2] not in nn and tok[2] != "0":
                nn.append(tok[2])
        if tok and tok[0].startswith("Vlb_"):    # [U6] 절단 직렬원 양쪽 노드(CM 루프 개루프 .pz 가 소비자 쪽 lbx 를 구동하는 데 쓴다)
            for n_ in (tok[1], tok[2]):
                if n_ not in nn and n_ != "0":
                    nn.append(n_)
    body += [".control", "set noaskquit", "op", "echo OPSTART"]
    body += [f"print i({c.lower()})" for c in chokes] + [f"print v({n.lower()})" for n in nn]
    body += ["echo OPEND", "quit", ".endc", ".end"]
    return "\n".join(body) + "\n", chokes, nn


def stability_netlist(text, mode, weights, output_nodes, plan):
    """[신규 C10 안정성] 폐루프 과도(.tran) 넷리스트. text = 오라클이 쓴 넷리스트(.control 앞 본문만 쓴다).
    mode = 'beta_loop': text 는 루프 넷리스트 -- Vlb_<넷>(DC 0) 이 이미 루프 안 직렬 원이고 Vlb = 0 이면 실제 폐루프다.
      끊은 넷마다 Vlb 에 PULSE(0 -> w_k*kick) 를 건다(w_k = weights[넷]).
    mode = 'beta_1': text 는 본 넷리스트 -- 입력 넷마다 그 넷의 테스트벤치 원(Cac_·Vac_·Vdc_·Ldc_·Efb_·Vofs_·Lfb_)을 빼고
      `Ecl_<넷> <넷 노드> ecl_<넷> <출력 노드 쌍> g` + `Vcl_<넷> ecl_<넷> 0 PULSE(V0 -> V0 + w_k*kick)` 로 직접 구동한다:
      V(넷) = V_op(넷) + g*(H - H_op) + w_k*kick(t), g = -sign*w_k, V0 = V_op(넷) - g*H_op(H = 출력 차동/단일 전압).
      입력 AC = -sign*w_k*H 라 루프 이득 = sign*A(β=1, sign = 기준점 A 실수부 부호 -> 기준점에서 음되먹임), 동작점은
      H = H_op 에서 본 동작점과 같다. (결합 C 1 F 를 이상 VCVS 로 구동하면 큰 진동에서 .tran 이 'Timestep too small' --
      2026-10-08 실측 nmcnr_amplifier.)
    나머지 테스트벤치 choke(CHOKE_PREFIXES: Lfb_·Ldc_·Lhold_ <tb 노드> <회로 노드> L)는 `Itb_<이름> <tb 노드> <회로 노드>
    DC <I_op>`(같은 본문의 동작점 패스 stability_op_netlist 가 잰 그 choke 전류) + `.ic v(<회로 노드>) = <V_op>` 로 바꾼다:
    .ic 는 uic 없이 쓰면 과도 시작 전
    바이어스 해에서만 그 노드를 묶고 t > 0 에서 푼다(SPICE .ic 의미) -- 바이어스 = 본 동작점, 과도 중에는 전류가 얼어 있는
    이상적 choke 와 같다(큰 L 을 그대로 두면 ngspice .tran 이 'Timestep too small' 로 멈춘다, 2026-10-08 실측:
    1e20/1e12 H 실패, 1e8 H 성공). plan = {kick_V, td, tr, pw, tstop, tmax, file, sign, choke_I{이름 소문자: A},
    node_V{SPICE 노드 소문자: V}, input_nodes{넷: SPICE 노드}}. 반환 (텍스트, 못 만든 것 목록)."""
    def pulse(v0, a):
        return (f"PULSE({_num(v0)} {_num(v0 + a)} {_num(plan['td'])} {_num(plan['tr'])} {_num(plan['tr'])} "
                f"{_num(plan['pw'])} {_num(2 * plan['tstop'])})")
    body, done, ics, bad = [], set(), [], []
    ci, nv = plan.get("choke_I") or {}, plan.get("node_V") or {}
    drop, h_op = set(), None
    if mode == "beta_1":
        drop = {f"{p}{net}" for net in weights for p in ("Cac_", "Vac_", "Vdc_", "Ldc_", "Efb_", "Vofs_", "Lfb_")}
        vo = [0.0 if n == "0" else nv.get(n.lower()) for n in output_nodes]
        h_op = None if None in vo else vo[0] - vo[1]
    for raw in text.splitlines():
        if raw.strip().lower().startswith(".control"):
            break
        tok = raw.split()
        if tok and tok[0] in drop:
            continue
        if tok and tok[0].startswith(CHOKE_PREFIXES):
            i_op, v_op = ci.get(tok[0].lower()), nv.get(tok[2].lower())
            if i_op is None or v_op is None:
                bad.append(f"{tok[0]}(동작점 전류 {i_op}, 노드 {tok[2]} 전압 {v_op})")
                body.append(raw)
                continue
            body.append(f"Itb_{tok[0]} {tok[1]} {tok[2]} DC {_num(i_op)}")
            ics.append(f".ic v({tok[2]})={_num(v_op)}")
            continue
        if mode == "beta_loop" and tok and tok[0].startswith("Vlb_") and tok[0][4:] in weights:
            net = tok[0][4:]
            body.append(f"{tok[0]} {tok[1]} {tok[2]} DC 0 " + pulse(0.0, weights[net] * plan["kick_V"]))
            done.add(net)
            continue
        body.append(raw)
    if mode == "beta_1":
        for net, w in weights.items():
            node = (plan.get("input_nodes") or {}).get(net)
            v_in = None if node is None else nv.get(node.lower())
            if v_in is None or h_op is None:
                bad.append(f"입력 {net}(동작점 전압 {v_in}, 출력 H_op {h_op})")
                continue
            g = -plan["sign"] * w
            body.append(f"Ecl_{net} {node} ecl_{net} {output_nodes[0]} {output_nodes[1]} {_num(g)}")
            body.append(f"Vcl_{net} ecl_{net} 0 " + pulse(v_in - g * h_op, w * plan["kick_V"]))
            done.add(net)
    body += ics
    body += stability_control(output_nodes, plan)
    return "\n".join(body) + "\n", sorted(set(weights) - done) + bad


def open_loop_parts(text, input_nets, input_nodes, node_V, choke_I, loop_kind=None, break_nets=()):
    """[신규 U6] 개루프 회로 본문 -- `.pz` 와 개루프 과도 확인이 같이 쓴다. text = 오라클이 쓴 넷리스트(본 또는 루프 넷리스트), 동작점
    패스(stability_op_netlist)의 node_V{SPICE 노드 소문자: V}·choke_I{choke 이름 소문자: A} 로 **큰 L·큰 C 없이** 같은 바이어스의 개루프
    회로를 만든다(ngspice `.pz` 근 찾기는 1e12 H·1 F 테스트벤치 소자가 낳는 1e-12 ~ 1e11 rad/s 동적 범위에서 반복 한도에 걸려 실패한다 --
    5T OTA 실측; 이 형태는 같은 회로에서 수렴한다).
      * 입력 넷마다 테스트벤치 사슬(Cac_·Vac_·Vdc_·Ldc_·Efb_·Vofs_·Lfb_·Vlb_·Ilb_)을 빼고 입력 노드를 동작점 전압의 이상 전압원
        `Vpz_<넷> <노드> 0 DC V_op` 로 구동한다(AC 0 = 입력 단락 = 개루프 A 의 자연 주파수).
      * 남은 choke(Lhold_ 등, 강제 바이어스)는 `Itb_<이름> <tb 노드> <회로 노드> DC <I_op>` + 초기 전압 V_op(`ics` 목록).
      * 절단 직렬원: `Vlb_<넷>`/`Ilb_<넷>` 을 빼고 절단 양쪽을 AC 로 나눈다. loop_kind = 'cm'(CM 루프, 절단 넷 = 출력 포트): 소비자 쪽 노드
        lbx_<넷>(루프 순방향 입력)만 동작점 전압의 이상 전압원으로 구동하고 구동자 쪽(출력)은 그대로 둔다. 'dm'(β 루프, 절단 넷 = 입력 포트): 증폭기 쪽 n(위
        입력 사슬 처리)과 되먹임 망 쪽 lbx_<넷> 을 모두 구동한다 -- 닫힌 루프에서 n 은 (높은 이득 때문에) 가상 접지라 되먹임 소자의 반대편 끝이 AC 접지에
        놓이는 부하와 같고, 용량만 물린 lbx 를 띄워 두면 `.pz` 가 'singular matrix' 로 실패한다(smoke 파일럿 실측). RHP 극은 능동 증폭기 내부(국소 양되먹임)에서만
        나오고 수동 β 망은 RHP 극을 만들지 않는다.
    반환 (본문 줄 목록, 초기 전압 사전 {SPICE 노드 소문자: V}). 못 만들면 ValueError."""
    drop_tb = set()
    for net in list(input_nets) + ([] if loop_kind == "cm" else list(break_nets)):
        drop_tb |= {f"{p}{net}" for p in ("Cac_", "Vac_", "Vdc_", "Ldc_", "Efb_", "Vofs_", "Lfb_", "Vlb_", "Ilb_")}
    cm_drop = {f"{p}{net}" for net in break_nets for p in ("Vlb_", "Ilb_")} if loop_kind == "cm" else set()
    body, ics = [], {}
    for raw in text.splitlines():
        if raw.strip().lower().startswith(".control"):
            break
        tok = raw.split()
        if tok and (tok[0] in drop_tb or tok[0] in cm_drop):
            continue
        if tok and tok[0].startswith(CHOKE_PREFIXES):
            i_op, v_op = choke_I.get(tok[0].lower()), node_V.get(tok[2].lower())
            if i_op is None or v_op is None:
                raise ValueError(f"{tok[0]}: 동작점 전류 {i_op} 또는 노드 {tok[2]} 전압 {v_op} 없음")
            body.append(f"Itb_{tok[0]} {tok[1]} {tok[2]} DC {_num(i_op)}")
            ics[tok[2].lower()] = v_op
            continue
        body.append(raw)
    for net, node in zip(input_nets, input_nodes):
        v = node_V.get(node.lower())
        if v is None:
            raise ValueError(f"입력 {net}({node}) 동작점 전압 없음")
        body.append(f"Vpz_{net} {node} 0 DC {_num(v)}")
    if loop_kind in ("cm", "dm"):
        for net in break_nets:
            v = node_V.get(f"lbx_{net}".lower())
            if v is None:
                raise ValueError(f"절단 넷 {net} 의 반대편 노드 lbx_{net} 동작점 전압 없음")
            body.append(f"Vpz_lbx_{net} lbx_{net} 0 DC {_num(v)}")
    return body, ics


def pz_netlist(text, input_nets, input_nodes, output_node, node_V, choke_I, loop_kind=None, break_nets=()):
    """[신규 U6] 개루프 `.pz` 넷리스트(open_loop_parts 본문 + `.nodeset` + `op` + `pz`). `.pz` 는 입력 포트가 이미 전압원에 묶인 노드에 못 건다
    ('input signal is shorted') -- 극점은 포트와 무관한 자연 주파수라 포트는 출력 노드의 전류 입력(`pz <출력> 0 <출력> 0 cur pol`)으로 둔다
    (회로를 바꾸지 않는다). 못 만들면 ValueError."""
    body, ics = open_loop_parts(text, input_nets, input_nodes, node_V, choke_I, loop_kind, break_nets)
    body += [f".nodeset v({n})={_num(v)}" for n, v in ics.items()]
    body += [".control", "set noaskquit", "op", "echo PZSTART", f"pz {output_node} 0 {output_node} 0 cur pol", "print all",
             "echo PZEND", "quit", ".endc", ".end"]
    return "\n".join(body) + "\n"


def openloop_tran_netlist(text, input_nets, input_nodes, output_nodes, node_V, choke_I, loop_kind, break_nets, plan, kick_V):
    """[신규 U6] 개루프 과도 확인 넷리스트: `.pz` 가 낸 RHP 극이 진짜인지 SPICE 시간 영역으로 확인한다(ngspice `.pz` 는 큰 BSIM4 회로에서 근을
    놓치거나 가짜 근을 낸다 -- smoke 파일럿 실측: 개루프 forced 에서 RHP 극 23 개를 냈지만 400 ns 개루프 과도는 증가가 없다). open_loop_parts 본문
    (`.nodeset` 대신 `.ic`) + 출력 노드 하나에 초기 변위 `.ic v(<출력>) = V_op + kick`(킥 = V_T, 폐루프 과도와 같은 크기; `.ic` 는 uic 없이 바이어스 해에서만
    그 노드를 묶고 t > 0 에서 풀어 준다 = 초기 변위가 풀려 나가는 과도) + stability_control 의 창 단위 실행(plan.t_kick_end = 0, 기준 H_ref = 동작점 H 값).
    RHP 극이 있으면 변위가 지수로 자라거나(포화 한계 사이클) 아니면 창마다 감쇠한다 -- 폐루프 과도와 같은 판정 규칙(transient_decision)을 쓴다.
    반환 (텍스트). 못 만들면 ValueError."""
    body, ics = open_loop_parts(text, input_nets, input_nodes, node_V, choke_I, loop_kind, break_nets)
    o1 = output_nodes[0]
    v_o1 = node_V.get(o1.lower())
    if v_o1 is None:
        raise ValueError(f"출력 {o1} 동작점 전압 없음")
    ics[o1.lower()] = v_o1 + kick_V
    body += [f".ic v({n})={_num(v)}" for n, v in ics.items()]
    body += stability_control(output_nodes, plan)
    return "\n".join(body) + "\n"


# wrdata 가 찍는 가수 자릿수 = numdgt + 1 (ngspice-46 실측: numdgt 4 -> 5 자리, 8 -> 9 자리, 12 -> 13 자리).
# 파일 반올림 반 단위 u = 0.5 * 10^-numdgt 를 .control 과 파이썬 판정(data_rel_resolution)이 같은 값으로 쓰도록 numdgt 를 명시한다.
WRDATA_NUMDGT = 8


def stability_control(output_nodes, plan):
    """[신규 C10 조기 종결 계약 (b)(d)] 폐루프 과도 `.save` 카드 + `.control` 블록 줄 목록.
    * H(관측) = plan.observe 가 있으면 그 노드들(루프 끊는 점)의 부호 합, 없으면 출력 노드 차(개루프 과도 확인).
    * `.save`: H 식의 피연산자 v(..) 와 time 만 저장(메모리 오류 완화; 전체 벡터 저장 안 함).
    * 창 단위 실행: ngspice 가 `stop when time > <창 j 끝>` / `resume` 으로 창 j = 1..K 를 차례로 끝내며(마지막 창은 tstop 에서
      저절로 끝난다), 창마다 로그에 `STABWIN j M_j`(M_j = 창 [t_end+(j-1)W, t_end+jW] 안 max|H - H(0)|) 한 줄을 쓴다. 경계 조건이
      `>` 인 것은 ngspice 의 `stop when` 이 `>=` 를 받지 않아서다(경계를 처음 넘은 표본에서 멈춘다 -- 그 표본은 창 j 밖).
      멈출 때마다 `delete all`(끝난 조건을 지우지 않으면 resume 이 같은 조건에서 곧바로 다시 멈춘다 -- 실측).
    * 조기 종결: 파이썬 oracle_simulate.early_window 와 같은 식을 창마다 스크립트로 평가한다.
        growth      : j >= 3, g↑(M_{j-2}, M_{j-1}), g↑(M_{j-1}, M_j), g↑(M_1, M_j)
        limit_cycle : j >= 3, 창 j-1 과 j 에서 flat 이다(설계 40 §4 C10 8 '감쇠하지 않음'). flat(j) := M_j(1-reltol) > floor' 이고 g↓(M_{j-1},M_j) 아님
      g↑(a,b) := b(1-reltol) > a(1+reltol) + floor', g↓(a,b) := a(1-reltol) > b(1+reltol) + floor'.
      (ngspice 명령 줄의 `>`·`<` 는 출력/입력 리다이렉션으로 읽혀 `let x = (a > b)` 가 조용히 틀리거나 실패한다 -- 실측. 비교는 `>=`·`<=`
      만 쓰고(`>=` 는 정상 비교), 한 줄에 하나씩 `let x = (a >= b)` 로 계산해 곱은 그 변수로 한다. 엄격 부등식(`>`)과 `>=` 는 값이
      정확히 같을 때만 다르고 floor' > 0 이라 실제로 같을 수 없다.)
      floor' = plan.floor_V + u·max|H|(지금까지 표본; u = 0.5·10^-numdgt). 충족하면 즉시 데이터 파일을 쓰고 끝낸다
      (파이썬은 파일에서 같은 기준을 다시 계산해 증명한다 -- ngspice 는 멈출 시점만 정한다).
    * 마지막 시각이 창 끝에 못 닿으면(ngspice 가 중간에 죽음) 더 돌리지 않고 파일만 쓴다(파이썬이 failed 로 판정)."""
    obs = plan.get("observe")
    if obs:   # 폐루프 과도: 관측 = 루프 끊는 점의 노드 전압(설계 40 §4 C10 8 '자극 위치') -- [[노드, 부호], ...]; 전체 부호는 abs() 라 무관
        s0 = 1 if obs[0][1] >= 0 else -1
        hst = f"v({obs[0][0]})" + "".join(f" {'+' if s0 * sg >= 0 else '-'} v({nd})" for nd, sg in obs[1:])
        save = ".save " + " ".join(f"v({nd})" for nd, _ in obs)
    else:     # 개루프 과도 확인(pz_validate): 관측 = 출력 노드(입력이 전압원에 묶여 끊는 점 신호가 없다)
        a, b = output_nodes[0], output_nodes[1]
        hst = f"v({a})" + ("" if b == "0" else f" - v({b})")
        save = f".save v({a})" + ("" if b == "0" else f" v({b})")
    u = 0.5 * 10.0 ** (-WRDATA_NUMDGT)
    tke, W, K = plan["t_kick_end"], plan["window_s"], int(plan["windows"])
    c = [save, ".control", "set noaskquit", f"set numdgt={WRDATA_NUMDGT}", "set wr_singlescale",
         f"let sw_tke = {_num(tke)}", f"let sw_w = {_num(W)}", f"let sw_k = {K}",
         f"let sw_rt = {_num(plan['reltol'])}", f"let sw_fl0 = {_num(plan['floor_V'])}", f"let sw_u = {_num(u)}",
         "let sw_j = 0", "let sw_m1 = 0", "let sw_p1 = 0", "let sw_p2 = 0", "let sw_fin = 0", "let sw_kind = 0"]
    if K > 1:
        c.append(f"stop when time > {_num(tke + W)}")
    c.append(f"tran {_num(plan['tmax'])} {_num(plan['tstop'])} 0 {_num(plan['tmax'])}")
    c += ["while sw_fin = 0",
          "  let sw_j = sw_j + 1",
          f"  let hst = {hst}",
          "  let sw_lo = sw_tke + (sw_j - 1) * sw_w",
          "  let sw_hi = sw_tke + sw_j * sw_w",
          "  let sw_tl = time[length(time) - 1]",
          "  if sw_tl >= sw_hi * (1 - 2 * sw_u)",
          f"    let sw_m = maximum(abs(hst - ({_num(plan['h_ref']) if plan.get('h_ref') is not None else 'hst[0]'})) * (time >= sw_lo) * (time <= sw_hi))",
          "    echo STABWIN $&sw_j $&sw_m",
          "    if sw_j = 1",
          "      let sw_m1 = sw_m",
          "    end",
          "    let sw_fl = sw_fl0 + sw_u * maximum(abs(hst))",
          "    let sw_up = (sw_m * (1 - sw_rt) >= sw_p1 * (1 + sw_rt) + sw_fl)",
          "    let sw_dn = (sw_p1 * (1 - sw_rt) >= sw_m * (1 + sw_rt) + sw_fl)",
          "    let sw_up0 = (sw_p1 * (1 - sw_rt) >= sw_p2 * (1 + sw_rt) + sw_fl)",
          "    let sw_dn0 = (sw_p2 * (1 - sw_rt) >= sw_p1 * (1 + sw_rt) + sw_fl)",
          "    let sw_upf = (sw_m * (1 - sw_rt) >= sw_m1 * (1 + sw_rt) + sw_fl)",
          "    let sw_ab1 = (sw_m * (1 - sw_rt) >= sw_fl)",
          "    let sw_ab0 = (sw_p1 * (1 - sw_rt) >= sw_fl)",
          "    let sw_fl1 = sw_ab1 * (1 - sw_dn)",
          "    let sw_fl0f = sw_ab0 * (1 - sw_dn0)",
          "    let sw_gr = sw_up0 * sw_up * sw_upf",
          "    let sw_lc = sw_fl0f * sw_fl1",
          "    if sw_j >= 3",
          "      if sw_gr >= 1",
          "        let sw_fin = 1",
          "        let sw_kind = 1",
          "      end",
          "      if sw_lc >= 1",
          "        let sw_fin = 1",
          "        let sw_kind = 2",
          "      end",
          "    end",
          "    if sw_fin = 0",
          "      if sw_j >= sw_k",
          "        let sw_fin = 2",
          "      else",
          "        let sw_p2 = sw_p1",
          "        let sw_p1 = sw_m",
          "        let sw_nb = sw_tke + (sw_j + 1) * sw_w",
          "        delete all",
          "        if sw_k >= sw_j + 2",
          "          stop when time > $&sw_nb",
          "        end",
          "        resume",
          "      end",
          "    end",
          "  else",
          "    let sw_fin = 3",
          "  end",
          "end",
          "echo STABEND $&sw_j $&sw_fin $&sw_kind",
          f"let hst = {hst}",
          f"wrdata {plan['file']} hst",
          "quit", ".endc", ".end"]
    return c
