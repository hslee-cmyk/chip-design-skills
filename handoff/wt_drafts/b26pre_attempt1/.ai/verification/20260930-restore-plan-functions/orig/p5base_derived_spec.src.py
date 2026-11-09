def derived_spec(circuit_key: str, why: str, **overrides) -> dict:
    """정본에서 **명시한 항목만** 바꾼 spec(2026-09-10).

    ## 왜 있나 (2026-09-10 사고)

    조사 스크립트들이 spec을 손으로 복붙해 쓰다가 정본과 갈렸고, 한 세션치 측정이
    전부 비정본 기준이 됐다(`gm_id_grid` 57점 vs 21점, `L_candidates` 41점 vs 12점,
    `stage_power_tolerance` 누락 등). 복붙의 문제는 **바꿀 의도가 없던 항목까지 같이
    갈린다**는 것이다 -- 그리고 그게 조용하다.

    이 함수는 그 두 가지를 동시에 막는다:

      * 덮어쓴 키만 갈린다. 나머지는 정본이 바뀌면 같이 따라간다.
      * `_spec_source`에 **무엇을 왜 바꿨는지**가 자동으로 박혀 산출물에 남는다.
        `sizing_recipe.require_declared_spec_source()`가 이 선언을 강제한다.

    조사에서 해상도를 일부러 낮추는 것은 정당하다 -- 말없이 낮추는 것이 문제였다.

        spec = H.derived_spec("current_reuse_telescopic_ota",
                              "L만 훑는 조사라 gm_id는 성기게",
                              gm_id_grid=[float(4 + i) for i in range(21)])

    `why`는 필수이고 비어 있으면 거부한다 -- 이유를 안 적을 거면 정본을 쓰라는 뜻이다.
    """
    if not (why or "").strip():
        raise ValueError(
            "derived_spec()은 `why`(왜 정본과 다르게 쓰는지)를 반드시 받는다 -- "
            "이유를 적을 게 없으면 canonical_spec()을 쓸 것. "
            "이 요구는 2026-09-10 사고(복붙 spec이 정본과 조용히 갈림) 재발 방지용이다.")
    spec = canonical_spec(circuit_key)
    if not overrides:
        return spec
    changed = []
    for k, v in overrides.items():
        before = spec.get(k, "(없음)")
        if isinstance(before, (list, tuple)) and before:
            before = f"n{len(before)}"
        if isinstance(v, (list, tuple)) and v:
            after = f"n{len(v)}"
        else:
            after = v
        changed.append(f"{k}:{before}->{after}")
        spec[k] = v
    spec["_spec_source"] = (f"run_harness.derived_spec({circuit_key!r}) "
                            f"[{', '.join(changed)}] -- {why.strip()}")
    return spec
