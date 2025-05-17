from typing import Dict

from pydantic import BaseModel


class CurrenciesResponse(BaseModel):
    success: bool
    currencies: dict[str, str]


class CurrencyRate(BaseModel):
    success: bool
    timestamp: int
    source: str
    quotes: Dict[str, float]

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "timestamp": 1747256405,
                "source": "USD",
                "quotes": {
                    "USDEUR": 0.89499,
                    "USDRUB": 80.374049
                }
            }
        }
    }


class QueryModel(BaseModel):
    from_: str = 'USD'
    to: str
    amount: float


class InfoModel(BaseModel):
    timestamp: int
    quote: float


class CurrencyConversionResponse(BaseModel):
    success: bool
    query: QueryModel
    info: InfoModel
    result: float

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "query": {
                    "from": "USD",
                    "to": "EUR",
                    "amount": 2
                },
                "info": {
                    "timestamp": 1747255923,
                    "quote": 0.89507
                },
                "result": 1.79014
            }
        }
    }
