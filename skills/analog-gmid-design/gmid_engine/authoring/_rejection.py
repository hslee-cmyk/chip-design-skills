"""authoring 공용 helper -- 로드 게이트 위반 묶음을 `SchemaRejectedError` 하나로 내는 한 가지 형식.

* `reject(gate, where, hits)`: detail = {"gate", "where", "hits"}. 선언 접근자들과 `json_read`·`topology_load` 가 같이 쓴다.
* `require_object(gate, doc)`: 최상위 값이 객체가 아니면 거부. 선언 접근자들이 같이 쓴다.
"""
from gmid_engine.core import SchemaRejectedError

from .topology_model import SchemaHit


def reject(gate, where, hits, **extra):
    """`hits`(SchemaHit 모음)를 담은 `SchemaRejectedError` 를 낸다. `extra` 는 detail 에 더할 불변 값."""
    detail = {"gate": gate, "where": where, "hits": tuple(hits)}
    detail.update(extra)
    raise SchemaRejectedError(detail=detail)


def require_object(gate, doc):
    """topology 최상위 값이 JSON 객체가 아니면 `top_not_object` 로 거부한다(선언 접근자를 단독으로 부를 때의 입구 검사)."""
    if not isinstance(doc, dict):
        reject(gate, "$", (SchemaHit("top_not_object", "$", "topology 최상위 값이 JSON 객체가 아니다: "
                                     + type(doc).__name__),))
