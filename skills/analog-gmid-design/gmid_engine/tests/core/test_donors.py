"""XRUN-F1 card B interface card C2 -- `Donors` 추상 기반(B-T4).

oracle 종류: (식) C2 원문 'abc.ABC, 직접 생성 TypeError, 네 메서드 모두 추상', '추상 메서드 하나를 빠뜨린 Donors 하위 클래스는
생성 때 TypeError'. 기대값은 예외 종류뿐이다.
"""
import abc

import pytest

from gmid_engine.core import Donors

_METHODS = ("find", "register", "find_failure", "register_failure")


def _impl(name):
    def method(self, *args):
        return None
    method.__name__ = name
    return method


def _subclass(missing=None):
    body = {m: _impl(m) for m in _METHODS if m != missing}
    return type("FakeDonors_%s" % (missing or "full"), (Donors,), body)


def test_donors_is_abc():
    # oracle 대조: C2 'abc.ABC'
    assert issubclass(Donors, abc.ABC)
    assert set(_METHODS) <= set(Donors.__abstractmethods__)


def test_donors_direct_construction_type_error():
    # oracle 대조: C2 '직접 생성 TypeError'
    with pytest.raises(TypeError):
        Donors()


@pytest.mark.parametrize("missing", _METHODS)
def test_donors_subclass_missing_one_method_type_error(missing):
    # oracle 대조: C2 '추상 메서드 하나를 빠뜨린 Donors 하위 클래스는 생성 때 TypeError'(네 메서드 각각)
    cls = _subclass(missing)
    with pytest.raises(TypeError):
        cls()


def test_donors_subclass_with_all_four_methods_constructs():
    # 대조군: 네 메서드를 모두 구현하면 생성된다(위 TypeError 가 '빠뜨림' 때문임을 확인)
    obj = _subclass()()
    assert isinstance(obj, Donors)
