"""ngspice 로그 -> 오류 코드 대응(op·ac 몫) -- design §7.1 표, '회복된 경고 규칙', 오류 단위. 시뮬레이터 호출 0.

oracle (d): 설계 §7.1 대응표(사용자 승인 대응) -- 줄 머리의 심각도 표지 + 문구 형태로 대응하고 회로 제목 줄·사용자 이름에는 걸리지 않는다
(S-18 거짓 적중 방지). 회복 시도 경고는 결과가 있으면 정보, 없을 때만 코드. 로그 줄은 §7.1 의 '문장 형태' 칸을 손으로 옮긴 입력이다
(기준선 로그 파일을 읽지 않는다 -- 대응표 확정 대조는 OP-1a 보관 텍스트로 판정자가 따로 한다).
기준선 사례가 없는 `sim_timestep_too_small`·`sim_timeout`·pz 반복 한도는 OP-4 몫이라 여기 없다.
해석(interface 에 errors.py 서명이 없다): `adapters.ngspice.errors.classify(log_text, *, result_present) -> (code | None, warnings)`.
"""
import pytest

from adapters.ngspice.errors import classify


def code(log, present):
    return classify(log, result_present=present)[0]


@pytest.mark.parametrize("log,expected", [
    ("Error: Could not find include file /x/y/model.lib", "sim_model_not_found"),
    ("ERROR: fatal error in ngspice, exit(1)", "sim_failed_other"),
    ("Error: no such device or model name xm1", "sim_failed_other"),
    ("Error: no such parameter vdsat", "sim_failed_other"),
], ids=["include", "fatal", "no_such_device", "no_such_parameter"])
def test_error_sentences_map_to_codes_when_no_result(log, expected):
    assert code(log, present=False) == expected


def test_fatal_prefers_the_more_specific_earlier_code():
    log = "Error: Could not find include file /x/y/model.lib\nERROR: fatal error in ngspice, exit(1)"
    assert code(log, present=False) == "sim_model_not_found"          # 앞 줄의 구체 코드 우선(§7.1 비고)


def test_singular_matrix_without_result():
    assert code("Warning: singular matrix: check node out", present=False) == "sim_singular_matrix"


@pytest.mark.parametrize("log", ["Warning: Dynamic gmin stepping failed", "Warning: True gmin stepping failed",
                                 "Warning: source stepping failed"])
def test_recovery_warnings_without_result_are_convergence_failure(log):
    assert code(log, present=False) == "sim_convergence_failed"


def test_recovered_warnings_are_information_only():
    log = ("Warning: Dynamic gmin stepping failed\nWarning: singular matrix: check node out\n"
           "Transient op finished successfully")
    c, warnings = classify(log, result_present=True)
    assert c is None                                                    # 결과가 있으면 오류 코드가 아니다
    assert any("Dynamic gmin stepping failed" in w for w in warnings)  # 문장 그대로 warnings 에 싣는다


@pytest.mark.parametrize("log", [
    "Warning from checkvalid: vector xm1#vdsat is not available",
    "Note: Starting gmin stepping",
    "Note: Dynamic gmin stepping completed",
    "Warning: Source/Drain conductance reset to 1e-12 mho.",
])
def test_information_lines_never_make_an_error(log):
    assert code(log, present=False) is None and code(log, present=True) is None


def test_circuit_title_line_with_error_like_words_is_not_an_error():
    # 시뮬레이터가 다시 찍는 회로 제목 줄 `Circuit: * ... tsingular ...` 은 대응 대상이 아니다(옛 정규식 거짓 적중, S-18)
    assert code("Circuit: * cs_toy tsingular_fatal_error test", present=False) is None


def test_user_name_inside_sentence_is_not_matched():
    # 사용자 이름(넷 이름)에 'singular' 가 있어도 심각도 표지 + 문구 형태가 아니면 걸리지 않는다
    assert code("Note: net singular_node connected to 2 devices", present=False) is None
