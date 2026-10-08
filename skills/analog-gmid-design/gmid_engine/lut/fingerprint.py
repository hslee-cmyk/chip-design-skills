"""LUT 묶음 지문 -- S0 입력·LUT memo 키 (설계 MOD1 2.5).

진입점: `lut_fingerprint`.

지문 = `core.fp_of`(정준 직렬화 sha256) of {manifest sha256, 생성기 sha256, 슬라이스별 (kind, w_key, 파일 sha256,
측정 조건, 모델 파일 sha256), 기준 LUT sha256·측정 조건, 용량 기준 폭 채택 근거}. 파일 경로는 넣지 않는다(같은
내용을 다른 폴더에 두어도 같은 지문). 코드 해시는 넣지 않는다(S0 의 '유도 규칙 코드 해시' 항목이 맡는다, P N3.3).
[r6] 검증 중점 파일이 출처에 있으면(`midpoints_sha256` 이 None 아님) 그 sha256 을 끝에 더한다 -- 중점 값이 tol 표의 외부
bin 값으로 들어가므로 다른 중점 파일은 다른 지문이다. 없으면 r5 와 같은 지문(같은 6항목).
[r7] 잡음 r1 파일·mismatch 감도 r1 파일이 출처에 있으면 그 sha256 을 차례로 더한다(없으면 같은 지문).
"""
from gmid_engine.core import fp_of


def lut_fingerprint(provenance, cap_basis):
    """`provenance`(LutProvenance) 와 `cap_basis`((kind, 채택 근거 pairs) tuple) 의 내용 지문(64자 hex)."""
    items = (
        ("manifest_sha256", provenance.manifest_sha256),
        ("generator_sha256", provenance.generator_sha256),
        ("slices", tuple(
            (s.kind, s.w_key, s.sha256, s.conditions, s.model_files_sha256) for s in provenance.slices)),
        ("cap_sha256", provenance.cap_sha256),
        ("cap_conditions", provenance.cap_conditions),
        ("cap_basis", cap_basis),
    )
    if provenance.midpoints_sha256 is not None:
        items = items + (("midpoints_sha256", provenance.midpoints_sha256),)
    if provenance.noise_sha256 is not None:
        items = items + (("noise_sha256", provenance.noise_sha256),)
    if provenance.mismatch_sha256 is not None:
        items = items + (("mismatch_sha256", provenance.mismatch_sha256),)
    return fp_of(items)
