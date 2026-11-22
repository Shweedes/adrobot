"""Реальный клиент и фейк совпадают с `KeitaroPort` по именам параметров."""

import inspect

import pytest

from app.keitaro.client import KeitaroClient
from app.services.ports import KeitaroPort
from tests.fakes import FakeKeitaro

PORT_METHODS = [
    name for name, member in vars(KeitaroPort).items() if inspect.iscoroutinefunction(member)
]


def _params(function) -> list[str]:
    return list(inspect.signature(function).parameters)


def test_port_lists_all_operations():
    assert len(PORT_METHODS) == 12


@pytest.mark.parametrize("implementation", [KeitaroClient, FakeKeitaro])
@pytest.mark.parametrize("name", PORT_METHODS)
def test_implementation_matches_port(implementation, name):
    assert hasattr(implementation, name)
    assert _params(getattr(implementation, name)) == _params(getattr(KeitaroPort, name))
