import pytest

from pydantic import ValidationError

from src.currency.schemas import (
    CurrencyConversionResponse,
    CurrencyRate,
    CurrenciesResponse
)


@pytest.mark.asyncio
async def test_get_currencies(
        test_client,
        mock_send_request_for_currencies,
        override_api_client,
        override_current_user
):
    """
    Тестирует эндпоинт /currencies на успешное получение списка валют.
    """
    headers = {'Authorization': 'Bearer fake-token'}
    response = await test_client.get('/currencies', headers=headers)
    assert response.status_code == 200
    payload = response.json()
    try:
        resp = CurrenciesResponse.model_validate(payload)
    except ValidationError as e:
        pytest.fail(f'The server response does not match the schema: {e}')
    assert resp.success is True
    assert 'USD' in resp.currencies


@pytest.mark.asyncio
async def test_get_currency_rate(
        test_client,
        mock_send_request_for_rates,
        override_api_client,
        override_current_user
):
    """
    Тестирует эндпоинт /currencies/rates на получение курса валют.
    """
    headers = {'Authorization': 'Bearer fake-token'}
    params = [
        ('source', 'USD'),
        ('currencies', 'RUB'),
        ('currencies', 'EUR'),
    ]

    response = await test_client.get('/currencies/rates', headers=headers, params=params)
    assert response.status_code == 200
    payload = response.json()
    try:
        resp = CurrencyRate.model_validate(payload)
    except ValidationError as e:
        pytest.fail(f'The server response does not match the schema: {e}')
    assert resp.success is True
    assert resp.source == 'USD'


@pytest.mark.asyncio
async def test_get_converted_currency(
        test_client,
        mock_send_request_for_convert,
        override_api_client,
        override_current_user
):
    """
    Тестирует эндпоинт /currencies/convert на конвертацию валюты.
    """
    headers = {'Authorization': 'Bearer fake-token'}
    params = [
        ('amount', 2),
        ('from_currency', 'USD'),
        ('to_currency', 'EUR')
    ]
    response = await test_client.get('/currencies/convert', headers=headers, params=params)
    assert response.status_code == 200
    payload = response.json()
    try:
        resp = CurrencyConversionResponse.model_validate(payload)
    except ValidationError as e:
        pytest.fail(f'The server response does not match the schema: {e}')
    assert resp.success is True
    assert resp.query.from_ == 'USD'
    assert resp.query.to == 'EUR'
    assert resp.query.amount == 2
