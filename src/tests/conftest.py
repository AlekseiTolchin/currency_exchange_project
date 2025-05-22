from unittest.mock import patch, AsyncMock

import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from src.auth.models import User
from src.currency.router import get_api_client
from src.auth.security import get_current_user
from src.main import app


async def fake_current_user():
    """
    Возвращает фиктивного пользователя для использования в тестах, связанных с авторизацией.
    """
    return User(
        id=1,
        first_name='test_user',
        last_name='test_user',
        username='test_username',
        email='testuser@test.com',
        hashed_password="test_hash",
        is_active=True,
    )


async def fake_api_client():
    """
    Возвращает фиктивный API-клиент с тестовым API-ключом для подмены зависимостей.
    """
    return {'headers': {'apikey': 'test_api_key'}}


@pytest_asyncio.fixture()
async def override_api_client():
    """
    Фикстура для подмены зависимости get_api_client в приложении на тестовую реализацию.
    """
    app.dependency_overrides[get_api_client] = fake_api_client
    yield
    app.dependency_overrides.pop(get_api_client, None)


@pytest_asyncio.fixture()
async def override_current_user():
    """
    Фикстура для подмены зависимости get_current_user на фиктивного пользователя.
    """
    app.dependency_overrides[get_current_user] = fake_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest_asyncio.fixture(scope='function')
async def test_client():
    """
    Фикстура для асинхронного тестового клиента httpx, работающего с ASGI-приложением.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        yield client


@pytest_asyncio.fixture(scope='function')
async def mock_send_request_for_currencies():
    """
    Мокающая фикстура для функции send_request (список валют).
    Возвращает заранее заданный успешный ответ с несколькими валютами.
    """
    mock = AsyncMock()
    mock.return_value = {
        'success': True,
        'currencies': {
            'USD': 'US Dollar',
            'EUR': 'Euro',
            'JPY': 'Japanese Yen',
            'GBP': 'British Pound',
            'RUB': 'Russian Ruble'
        }
    }
    with patch('src.currency.utils.send_request', mock):
        yield mock


@pytest_asyncio.fixture(scope='function')
async def mock_send_request_for_rates():
    """
    Мокающая фикстура для функции send_request (получение курсов валют).
    Возвращает успешный ответ с курсами для EUR и RUB.
    """
    mock = AsyncMock()
    mock.return_value = {
        'success': True,
        'timestamp': 1747256405,
        'source': 'USD',
        'quotes': {
            'USDEUR': 0.89499,
            'USDRUB': 80.374049
        }
    }
    with patch('src.currency.utils.send_request', mock):
        yield mock


@pytest_asyncio.fixture(scope='function')
async def mock_send_request_for_convert():
    """
    Мокающая фикстура для функции send_request (конвертация валюты).
    Возвращает успешный ответ с результатом конвертации 2 USD в EUR.
    """
    mock = AsyncMock()
    mock.return_value = {
        'success': True,
        'query': {
            'from': 'USD',
            "to": 'EUR',
            'amount': 2
        },
        'info': {
            'timestamp': 1747255923,
            'quote': 0.89507
        },
        'result': 1.79014
    }
    with patch('src.currency.utils.send_request', mock):
        yield mock
