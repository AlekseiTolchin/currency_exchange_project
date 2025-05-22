from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from src.currency.utils import (
    send_request,
    fetch_currencies,
    fetch_currency_rate,
    convert_currency,
)


@pytest.mark.asyncio
async def test_send_request_success():
    """
    Тестирует функцию send_request на успешный запрос к внешнему API.
    """
    expected_response = {'foo': 'bar'}

    with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        url = 'https://api.example.com'
        headers = {'apikey': 'test'}
        response = await send_request(url, headers)

        assert response == expected_response
        mock_get.assert_called_once_with(url, headers=headers, params=None)


@pytest.mark.asyncio
async def test_fetch_currencies_success(mock_send_request_for_currencies):
    """
    Тестирует функцию fetch_currencies на успешное получение списка валют.
    """
    headers = {'api_key': 'test_key'}
    currencies_response = await fetch_currencies(headers)

    assert currencies_response['success'] is True
    assert 'currencies' in currencies_response
    assert isinstance(currencies_response['currencies'], dict)
    assert 'USD' in currencies_response['currencies']
    assert currencies_response['currencies']['USD'] == 'US Dollar'
    mock_send_request_for_currencies.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_currency_rate_success(mock_send_request_for_rates):
    """
    Тестирует функцию fetch_currency_rate на успешное получение курсов валют.
    """
    headers = {'api_key': 'test_key'}
    currency_rate_response = await fetch_currency_rate(
        source='USD',
        currencies='RUB,EUR',
        headers=headers
    )

    assert currency_rate_response['success'] is True
    assert currency_rate_response['source'] == 'USD'
    assert 'quotes' in currency_rate_response
    assert isinstance(currency_rate_response['quotes'], dict)
    assert 'USDRUB' in currency_rate_response['quotes']
    assert 'USDEUR' in currency_rate_response['quotes']
    assert currency_rate_response['quotes']['USDRUB'] == 80.374049
    assert currency_rate_response['quotes']['USDEUR'] == 0.89499
    mock_send_request_for_rates.assert_called_once()


@pytest.mark.asyncio
async def test_convert_currency_success(mock_send_request_for_convert):
    """
    Тестирует функцию convert_currency на успешную конвертацию валюты.
    """
    headers = {'api_key': 'test_key'}
    conversion_response = await convert_currency(
        amount=2,
        from_currency='USD',
        to_currency='EUR',
        headers=headers
    )

    assert conversion_response['success'] is True
    assert conversion_response['query']['amount'] == 2
    assert conversion_response['query']['from'] == 'USD'
    assert conversion_response['query']['to'] == 'EUR'
    assert isinstance(conversion_response['query'], dict)
    mock_send_request_for_convert.assert_called_once()
