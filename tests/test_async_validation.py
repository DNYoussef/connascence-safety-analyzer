"""
Simple async test to validate pytest-asyncio is working correctly.
"""
import asyncio

import pytest


@pytest.mark.asyncio
async def test_async_basic():
    """Test basic async/await functionality."""
    await asyncio.sleep(0.01)
    assert True


@pytest.mark.asyncio
async def test_async_return_value():
    """Test async function with return value."""

    async def get_value():
        await asyncio.sleep(0.01)
        return 42

    result = await get_value()
    assert result == 42


@pytest.mark.asyncio
async def test_async_multiple_awaits():
    """Test multiple async operations."""

    async def add(a, b):
        await asyncio.sleep(0.01)
        return a + b

    result1 = await add(1, 2)
    result2 = await add(3, 4)

    assert result1 == 3
    assert result2 == 7


@pytest.mark.asyncio
async def test_async_exception_handling():
    """Test async exception handling."""

    async def raise_error():
        await asyncio.sleep(0.01)
        raise ValueError("Test error")

    with pytest.raises(ValueError, match="Test error"):
        await raise_error()
