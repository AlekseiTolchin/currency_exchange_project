from typing import Annotated, List, Optional

from fastapi import APIRouter, Query, Depends, status, HTTPException

from src.auth.models import User
from src.config import settings
from src.currency.utils import fetch_currencies, fetch_currency_rate, convert_currency
from src.currency.schemas import CurrencyRate, CurrencyConversionResponse, CurrenciesResponse
from src.auth.security import get_current_user


COMMON_RESPONSES = {
    400: {'description': 'Bad Request'},
    401: {'description': 'Unauthorized'},
    404: {'description': 'Not Found'},
    429: {'description': 'Too many requests'},
    500: {'description': 'Internal Server Error'},
}


currencies_router = APIRouter(prefix='/currencies', tags=['currencies'])


def get_api_client() -> dict:
    """Зависимость для конфигурации клиента API"""
    return {
        'headers': {
            'apikey': settings.CURRENCY_API_KEY
        }
    }


@currencies_router.get('/', response_model=CurrenciesResponse, responses=COMMON_RESPONSES)
async def get_currencies(
        current_user: Annotated[User, Depends(get_current_user)],
        api_client: dict = Depends(get_api_client),

)-> CurrenciesResponse:
    """Получить список доступных валют."""

    headers = api_client.get('headers', {})
    if not headers:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Client API headers not configured'
        )

    currencies = await fetch_currencies(headers)
    return CurrenciesResponse(**currencies)


@currencies_router.get('/rates', response_model=CurrencyRate, responses=COMMON_RESPONSES)
async def get_currency_rate(
    current_user: Annotated[User, Depends(get_current_user)],
    source: str = Query(default='USD', description='Базовая валюта'),
    currencies: Optional[List[str]] = Query(default=None, description='Валюты, например: EUR, GBP, JPY'),
    api_client: dict = Depends(get_api_client),
) -> CurrencyRate:
    """Получить курсы валют относительно базовой валюты."""

    headers = api_client.get('headers', {})
    if not headers:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Client API headers not configured'
        )

    currencies_str = ','.join(currencies) if currencies else None
    courses = await fetch_currency_rate(source, currencies_str, headers)
    return CurrencyRate(**courses)


@currencies_router.get(
    '/convert',
    response_model=CurrencyConversionResponse,
    responses=COMMON_RESPONSES
)
async def get_converted_currency(
    current_user: Annotated[User, Depends(get_current_user)],
    amount: float = Query(description='Количество'),
    from_currency: str = Query(description='Из'),
    to_currency: str = Query(description='В'),
    api_client: dict = Depends(get_api_client)
) -> CurrencyConversionResponse:
    """Конвертировать сумму из одной валюты в другую."""

    headers = api_client.get('headers', {})
    if not headers:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Client API headers not configured'
        )

    exchange_result = await convert_currency(amount, from_currency, to_currency, headers)
    return CurrencyConversionResponse(**exchange_result)
