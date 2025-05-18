# Обмен валют

Приложение с интегрированным сервисом обмена валют [apilayer.com](https://apilayer.com/marketplace/currency_data-api)

## Как запустить проект

Скачать удаленный репозиторий выполнив команду

```
git clone https://github.com/AlekseiTolchin/currency_exchange_project
```

Python3.11 должен быть уже установлен. Затем используйте `pip `
(или pip3, есть конфликт с Python2) для установки зависимостей:

```
pip install -r requirements.txt
```

Применить миграции:

```
alembic upgrade head
```

В корневой директории проекта создать файл `.env` со следующими настройками:

- `CURRENCY_API_KEY`= Зарегистрироваться на [apilayer.com](https://apilayer.com/marketplace/currency_data-api) и получить API-ключ
- `CURRENCY_API_URL`= https://api.apilayer.com/currency_data/
- `JWT_SECRET_KEY`= можно создать с помощью openssl, выполнив команду `openssl rand -hex 32`
- `JWT_ALGORITHM`= тип алгоритма, например `HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES`= срок действия `access` токена в минутах
- `REFRESH_TOKEN_EXPIRE_DAYS`= срок действия `refresh` токена в днях

Из корневой директории проекта выполнить команду:

```
uvicorn src.main:app --reload
```

Ссылка для тестирования:

http://127.0.0.1:8000/docs/ - `документация API`  
