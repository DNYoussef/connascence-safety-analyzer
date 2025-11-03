"""Minimal asyncio plugin for the test suite."""

from __future__ import annotations

import asyncio
import inspect

import pytest


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool | None:
    test_callable = pyfuncitem.obj
    if not inspect.iscoroutinefunction(test_callable):
        return None

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        loop.run_until_complete(test_callable(**pyfuncitem.funcargs))
    finally:
        loop.close()
        asyncio.set_event_loop(None)
    return True


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "asyncio: execute async tests via bundled plugin")
