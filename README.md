# Асинхронный сервис процессинга платежей

Сервис принимает запрос на оплату, обрабатывает его через эмулятор платежного шлюза и отправляет результат клиенту на webhook.

Стек: FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), PostgreSQL, RabbitMQ (FastStream), Alembic, Docker.

## Запуск и остановка сервиса

### Запуск

Для запуска сервиса необходимо:

1. Создать .env на основе .env.example:

```bash
cp .env.example .env
```
2. Поднять (запустить) Docker-контейнеры:

```bash
docker compose up -d --build
```

В результате запустятся следующие сервисы:

| Сервис | Назначение |
|---|---|
| `postgres`| База данных |
| `rabbitmq` | Брокер сообщений |
| `migrations` | Применяет миграции и завершается |
| `api` | HTTP API (http://localhost:8000) |
| `relay` | Переносит события из таблицы `outbox` в RabbitMQ |
| `consumer` | Обрабатывает платежи и отправляет webhook |

Дополнительные ссылки:

- Swagger: http://localhost:8000/docs
- Панель RabbitMQ: http://localhost:15672 (логин `guest` и пароль `guest`)

### Остановка

Для остановки сервиса с сохранением томов данных следует выполнить:

```bash
docker compose down
```

Для остановки сервиса с удалением томов данных (тома PostgreSQL и RabbitMQ) следует выполнить:

```bash
docker compose down -v
```

После `down -v` тома базы данных и очередей создаются заново при следующем `docker compose up`.

## API

Все запросы требуют заголовок `X-API-Key` (значение - `API_KEY` считывается из `.env`).

### Создание платежа

```bash
curl -X POST http://localhost:8000/api/v1/payments \
  -H "X-API-Key: 1" \
  -H "Idempotency-Key: order-123" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": "100.50",
    "currency": "RUB",
    "description": "Order 123",
    "metadata": {"order_id": 123},
    "webhook_url": "https://httpbin.org/post"
  }'
```

Ответ `202 Accepted`:

```json
{
  "payment_id": "01a15992-9f91-71e8-9974-0c2370f2507c",
  "status": "pending",
  "created_at": "2026-10-20T13:59:03.761686Z"
}
```

- Повтор запроса с тем же `Idempotency-Key` и теми же данными вернет тот же платеж.
- Повтор запроса с тем же ключом, но с другими данными, получит в ответе `409 Conflict`.

### Получение платежа

```bash
curl http://localhost:8000/api/v1/payments/01a15992-9f91-71e8-9974-0c2370f2507c \
  -H "X-API-Key: 1"
```

Ответ `200 OK`:

```json
{
  "payment_id": "01a15992-9f91-71e8-9974-0c2370f2507c",
  "amount": "100.50",
  "currency": "RUB",
  "description": "Order 123",
  "metadata": {"order_id": 123},
  "status": "succeeded",
  "webhook_url": "https://httpbin.org/post",
  "idempotency_key": "order-123",
  "created_at": "2026-10-20T13:59:03.761686Z",
  "processed_at": "2026-10-20T13:59:10.072889Z"
}
```

### Отправление Webhook

После обработки сервис отправляет `POST` на `webhook_url`:

```json
{
  "payment_id": "01a15992-9f91-71e8-9974-0c2370f2507c",
  "status": "succeeded",
  "amount": "100.50",
  "currency": "RUB",
  "processed_at": "2026-10-20T13:59:10.072889+00:00"
}
```

Webhook может прийти повторно, поэтому обрабатывать его следует идемпотентно по `payment_id`.

## Основные компоненты

| Компонент | Описание |
|---|---|
| **API** | HTTP-сервис на FastAPI. Принимает запросы на создание платежа и выдает информацию о платеже. Сам платеж не обрабатывает: только сохраняет его и событие о нем в базу данных. Защита от дублей построена на `Idempotency-Key`: ключ уникален в базе, поэтому повторный или одновременный запрос с тем же ключом не создаст второй платеж |
| **Outbox** | Таблица `outbox` в PostgreSQL. Хранит события, которые еще нужно отправить в RabbitMQ. Событие записывается в одной транзакции с платежом, поэтому либо сохраняются оба, либо ни одно. Если брокер недоступен, событие дождется в таблице следующей попытки relay и не потеряется |
| **Relay** | Отдельный процесс. С заданной периодичностью читает неотправленные события из `outbox`, публикует их в RabbitMQ и помечает как отправленные. Несколько запущенных relay не отправят одно событие дважды: выбранные записи блокируются |
| **RabbitMQ** | Брокер сообщений. Exchange `payments` направляет события в очередь `payments.new`. Сообщения, которые не удалось обработать, RabbitMQ перекладывает через exchange `payments.dlx` в очередь `payments.new.dlq` (Dead Letter Queue) |
| **Consumer** | Отдельный процесс, который читает очередь `payments.new`. Для каждого сообщения проводит платеж через платежный шлюз, сохраняет результат и отправляет webhook. На время обработки платеж блокируется и проводится только из статуса `pending`, поэтому повторное сообщение не приведет к повторному списанию, а только к повторной отправке webhook. Webhook отправляется до 3 раз с паузами 1 и 2 секунды; если все попытки неудачны, сообщение уходит в DLQ |
| **Платежный шлюз** | Эмулятор внешнего платежного шлюза. Отвечает через 2–5 секунд: в 90 % случаев успехом и в 10 % отказом |
| **Webhook** | Уведомление клиенту о результате платежа: `POST`-запрос на `webhook_url`, указанный при создании платежа |
| **Migrations** | Миграции Alembic. Создают таблицы `payments` и `outbox` |

## Алгоритм работы сервиса

Сервис осуществляет работу по следующему алгоритму:

1. API принимает `POST /api/v1/payments` и в одной транзакции сохраняет платеж в таблицу `payments` и событие в таблицу `outbox`;
2. Relay раз в несколько секунд забирает неотправленные события из `outbox` и публикует их в exchange `payments` с ключом `payments.new`;
3. Сообщение попадает в очередь `payments.new`;
4. Consumer получает сообщение, эмулирует оплату (от 2 до 5 секунд с вероятностью 90 % успеха), сохраняет статус `succeeded` или `failed` и отправляет webhook;
5. Если webhook не доставлен за 3 попытки, сообщение уходит через exchange `payments.dlx` в очередь `payments.new.dlq`.

## Структура

Код лежит в папке `src/payment_service/`:

| Папка | Содержание |
|---|---|
| `domain` | Сущность `Payment`, статусы, правила |
| `application` | Сценарии (use cases) и интерфейсы |
| `infrastructure` | PostgreSQL, RabbitMQ, эмулятор шлюза, отправка webhook |
| `presentation` | HTTP-роутеры и обработчик сообщений |
| `bootstrap` | Сборка и точки входа: `api`, `relay`, `consumer` |

Зависимости направлены внутрь: `domain` ни от чего не зависит, `application` знает только `domain`, конкретные реализации (база, брокер) подключаются в `bootstrap`.

## Переменные окружения

| Переменная | Описание |
|---|---|
| `API_KEY` | Ключ для заголовка `X-API-Key` |
| `POSTGRES__NAME` | Имя базы в PostgreSQL |
| `POSTGRES__USERNAME` | Логин учетной записи PostgreSQL |
| `POSTGRES__PASSWORD` | Пароль от учетной записи PostgreSQL |
| `POSTGRES__HOST` | Хост PostgreSQL (в Docker подменяется на `postgres`) |
| `POSTGRES__PORT` | Порт PostgreSQL |
| `RABBITMQ__URL` | Адрес RabbitMQ (в Docker подменяется на `rabbitmq`) |
| `OUTBOX_RABBITMQ__ATTEMPTS_MAXIMUM` | Сколько раз relay пытается опубликовать событие |
| `OUTBOX_RABBITMQ__BATCH_LIMIT` | Сколько событий relay берет за раз |
| `OUTBOX_RABBITMQ__DISPATCH_INTERVAL_SECONDS` | Пауза между проходами relay |

## Локальная разработка

### Запуск сервиса без Docker-контейнера для основного приложения

Для запуска сервиса без Docker-контейнера для основного приложения необходимо:

1. Создать .env на основе .env.example:

```bash
cp .env.example .env
```

2. Поднять (запустить) Docker-контейнер базы данных:

```bash
docker compose up -d postgres
```

3. Поднять (запустить) Docker-контейнер брокера сообщений:

```bash
docker compose up -d rabbitmq
```

4. Установить зависимости сервиса:

```bash
uv sync
```

5. Применить (накатить) миграции базы данных:

```bash
uv run alembic upgrade head
```

6. Запустить основной сервис в отдельном терминале:

```bash
uv run uvicorn payment_service.bootstrap.api:app --reload
```

7. Запустить сервис relay в отдельном терминале:

```bash
uv run python -m payment_service.bootstrap.relay
```

8. Запустить сервис consumer в отдельном терминале:

```bash
uv run python -m payment_service.bootstrap.consumer
```

### Остановка сервиса без Docker-контейнера для основного приложения

Для остановки сервиса без Docker-контейнера для основного приложения необходимо:

1. Остановить основной сервис и сервисы relay и consumer, нажав комбинацию клавиш `Ctrl+C` в каждом терминале;

2. Остановить работу Docker-контейнера брокера сообщений:

- для остановки с сохранением данных:

```bash
docker compose stop rabbitmq
```

- для остановки с удалением данных:

```bash
docker compose down -v rabbitmq
```


3. Остановить работу Docker-контейнера базы данных:

- для остановки с сохранением данных:

```bash
docker compose stop postgres
```

- для остановки с удалением данных:

```bash
docker compose down -v postgres
```
