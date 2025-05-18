from fastapi import FastAPI

from src.currency.router import currencies_router
from src.auth.router import auth_router


app = FastAPI()


@app.get('/')
def welcome() -> dict:
    return {
        'message': 'Currency exchange app'
    }


app.include_router(currencies_router)
app.include_router(auth_router)
