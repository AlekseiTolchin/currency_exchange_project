from typing import Any, Optional

import httpx
from fastapi import HTTPException, status

from src.config import settings


async def send_request(
        api_url: str,
        headers: dict,
        params: Optional[dict] = None
) -> dict[str, Any]:
    """Асинхронно отправляет GET-запрос к внешнему API валют."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f'External currency API error: {e.response.text}'
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f'Error communicating with external currency API: {e}'
        )


async def fetch_currencies(headers: dict) -> dict[str, Any]:
    """Получает список всех доступных валют из внешнего API."""

    api_url = f'{settings.CURRENCY_API_URL}list'
    currencies = await send_request(api_url, headers, None)
    if not currencies.get('success'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST
        )
    return currencies


async def fetch_currency_rate(
        source: str,
        currencies: Optional[str] = None,
        headers: dict = None
) -> dict[str, Any]:
    """Получает актуальные курсы обмена относительно базовой валюты."""

    if not source:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Source currency must be provided'
        )
    params = {
        'source': source,
        'currencies': currencies
    }
    api_url = f'{settings.CURRENCY_API_URL}live'
    currency_rates = await send_request(api_url, headers, params)
    if not currency_rates.get('success'):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY
        )

    return currency_rates


async def convert_currency(
        amount: float,
        from_currency: str,
        to_currency: str,
        headers: dict = None
) -> dict[str, Any]:
    """
    Конвертирует указанную сумму из одной валюты в другую.
    """
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Amount must be greater than 0'
        )

    if not from_currency or not to_currency:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Both source and target currencies must be specified'
        )
    params = {
        'to': to_currency,
        'from': from_currency,
        'amount': amount,
    }
    api_url = f'{settings.CURRENCY_API_URL}convert'
    converted_currency = await send_request(api_url, headers, params)
    if not converted_currency.get('success'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST
        )

    return converted_currency
