# HTTP 1.1 — Полный конспект

> **Преподаватель:** Бекенд Разработчик  
> **Тема:** Request, Response, Methods, Headers, Status Codes

---

## Содержание

1. [Структура Request и Response](#1-структура-request-и-response)
2. [HTTP Методы](#2-http-методы)
3. [HTTP Заголовки](#3-http-заголовки)
4. [Коды статуса](#4-коды-статуса)
5. [Шпаргалка](#5-шпаргалка)

---

## 1. Структура Request и Response

HTTP — текстовый протокол. Каждое сообщение состоит из **трёх частей**:

```
Start Line      ← первая строка (разная для Request и Response)
Headers         ← метаданные, по одному на строку: "Имя: Значение"
                ← ПУСТАЯ СТРОКА (обязательный разделитель, CRLF \r\n)
Body            ← тело (необязательно)
```

### 1.1 Request (запрос клиента)

```http
POST /api/login HTTP/1.1
Host: example.com
Content-Type: application/json
Content-Length: 35

{"login": "bob", "password": "123"}
```

| Часть | Формат | Пример |
|---|---|---|
| Start Line | `METHOD URI HTTP/VERSION` | `POST /api/users HTTP/1.1` |
| Headers | `Имя: Значение` | `Host: example.com` |
| Blank Line | `\r\n` | *(пустая строка)* |
| Body | любой формат | `{"name":"Alice"}` |

### 1.2 Response (ответ сервера)

```http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 27

{"token": "eyJhbGci..."}
```

| Часть | Формат | Пример |
|---|---|---|
| Status Line | `HTTP/VERSION STATUS_CODE REASON` | `HTTP/1.1 201 Created` |
| Headers | `Имя: Значение` | `Content-Type: application/json` |
| Blank Line | `\r\n` | *(пустая строка)* |
| Body | любой формат | `{"id": 42}` |

> **Как посмотреть живьём:**  
> `curl -v https://httpbin.org/get` — строки `>` это запрос, `<` это ответ.  
> Или DevTools в браузере → Network → любой запрос → Headers / Response.

---

## 2. HTTP Методы

Метод определяет **действие** над ресурсом. У каждого метода три ключевых свойства:

- **Безопасный** — не изменяет данные на сервере
- **Идемпотентный** — повторный вызов с теми же данными даёт тот же результат
- **Тело запроса** — есть или нет

| Метод | Безопасный | Идемпотентный | Тело запроса | Тело ответа | Кешируется |
|---|:---:|:---:|:---:|:---:|:---:|
| GET | ✅ | ✅ | ❌ | ✅ | ✅ |
| POST | ❌ | ❌ | ✅ | ✅ | ❌ |
| PUT | ❌ | ✅ | ✅ | опционально | ❌ |
| PATCH | ❌ | зависит | ✅ | опционально | ❌ |
| DELETE | ❌ | ✅ | не рекомендуется | опционально | ❌ |
| HEAD | ✅ | ✅ | ❌ | ❌ | ✅ |
| OPTIONS | ✅ | ✅ | ❌ | опционально | ❌ |
| CONNECT | ❌ | ❌ | ❌ | ❌ | ❌ |
| TRACE | ✅ | ✅ | ❌ | ✅ (эхо) | ❌ |

---

### GET — получить ресурс

Запрашивает данные. Никогда не изменяет состояние. Параметры передаются в URL (query string).

```http
GET /api/users/42 HTTP/1.1
Host: example.com
Accept: application/json
Authorization: Bearer eyJ...
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"id": 42, "name": "Alice"}
```

**Применяется для:** получения профиля, списка товаров, поиска, чтения статьи.

---

### POST — создать ресурс / отправить данные

Создаёт новый ресурс или отправляет данные для обработки. **Не идемпотентен** — каждый вызов создаёт новую запись. Данные передаются в теле.

```http
POST /api/users HTTP/1.1
Host: example.com
Content-Type: application/json
Content-Length: 34

{"name": "Bob", "email": "b@ex.com"}
```

```http
HTTP/1.1 201 Created
Location: /api/users/43
Content-Type: application/json

{"id": 43, "name": "Bob"}
```

**Применяется для:** регистрации, входа, создания заказа, загрузки файла.

---

### PUT — полностью заменить ресурс

Заменяет ресурс **целиком**. Если ресурса нет — создаёт. Поля, не указанные в теле, **сбрасываются**. Идемпотентен.

```http
PUT /api/users/42 HTTP/1.1
Host: example.com
Content-Type: application/json

{"name": "Alice", "email": "a@ex.com", "age": 30, "role": "admin"}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"id": 42, "name": "Alice", "email": "a@ex.com", "age": 30}
```

**Применяется для:** полного обновления профиля, upsert (создать или заменить), замены документа целиком.

> ⚠️ **PUT vs PATCH:** PUT требует передачи всех полей. Забытое поле будет удалено или сброшено в null.

---

### PATCH — частично обновить ресурс

Изменяет **только указанные поля**. Остальные поля не трогает. Идемпотентность зависит от реализации.

```http
PATCH /api/users/42 HTTP/1.1
Host: example.com
Content-Type: application/json

{"email": "newemail@ex.com"}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"id": 42, "name": "Alice", "email": "newemail@ex.com"}
```

**Применяется для:** изменения одного поля, обновления статуса, пометки как прочитанного.

---

### DELETE — удалить ресурс

Удаляет ресурс. Идемпотентен: повторное удаление уже удалённого ресурса вернёт 404, но состояние не изменится. Тело запроса технически допустимо, но большинство серверов игнорирует.

```http
DELETE /api/users/42 HTTP/1.1
Host: example.com
Authorization: Bearer eyJ...
```

```http
HTTP/1.1 204 No Content
```

**Применяется для:** удаления записи, отмены подписки, удаления файла.

> ✅ **Правильный ответ на DELETE** — `204 No Content` (не `200` с пустым телом).

---

### HEAD — получить только заголовки

Работает как GET, но **без тела ответа**. Сервер отправляет только заголовки. Используется для проверки ресурса без загрузки контента.

```http
HEAD /files/report.pdf HTTP/1.1
Host: example.com
```

```http
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Length: 204800
Last-Modified: Mon, 01 Jan 2024 12:00:00 GMT
```

**Применяется для:** проверки изменения файла (кеш), узнать размер файла перед скачиванием, проверки доступности URL.

---

### OPTIONS — узнать возможности сервера

Возвращает список методов и заголовков, допустимых для ресурса. Ключевой метод для **CORS preflight** — браузер автоматически делает OPTIONS перед каждым кросс-доменным запросом.

```http
OPTIONS /api/users HTTP/1.1
Host: api.example.com
Origin: https://app.example.com
Access-Control-Request-Method: POST
```

```http
HTTP/1.1 204 No Content
Allow: GET, POST, PUT, DELETE
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
```

**Применяется для:** CORS preflight в браузере, документирования API, проверки допустимых операций.

---

### CONNECT — установить туннель

Устанавливает **TCP-туннель через прокси**. Клиент просит прокси соединиться с сервером и пропускать трафик насквозь. Именно так HTTPS работает через HTTP-прокси.

```http
CONNECT example.com:443 HTTP/1.1
Host: example.com:443
```

```http
HTTP/1.1 200 Connection Established
(далее — сырой TCP/TLS трафик)
```

**Применяется для:** HTTPS через корпоративный HTTP-прокси, VPN-подобных туннелей.

---

### TRACE — диагностика пути запроса

Эхо-метод: сервер возвращает **полученный запрос обратно клиенту**. Позволяет увидеть как промежуточные прокси изменяли запрос.

```http
TRACE /path HTTP/1.1
Host: example.com
Custom-Header: test-value
```

```http
HTTP/1.1 200 OK
Content-Type: message/http

TRACE /path HTTP/1.1
Host: example.com
Custom-Header: test-value
```

> ⚠️ На продакшене **всегда отключён** из соображений безопасности (XST-атаки).

---

## 3. HTTP Заголовки

Заголовки — метаданные запроса и ответа. Формат: `Имя: Значение`. Имена регистронезависимы. Разделяются от тела **обязательной пустой строкой**.

### 3.1 Заголовки запроса (Request Headers)

| Заголовок | Описание | Пример |
|---|---|---|
| `Host` | Домен и порт. **Единственный обязательный** в HTTP/1.1 | `Host: api.example.com:8080` |
| `Authorization` | Учётные данные для аутентификации | `Authorization: Bearer eyJ...` |
| `Content-Type` | MIME-тип тела запроса. Обязателен при наличии тела | `Content-Type: application/json` |
| `Content-Length` | Размер тела запроса в байтах | `Content-Length: 348` |
| `Accept` | Форматы которые клиент готов принять | `Accept: application/json, */*;q=0.8` |
| `Accept-Encoding` | Поддерживаемые алгоритмы сжатия | `Accept-Encoding: gzip, deflate, br` |
| `Accept-Language` | Предпочитаемые языки ответа | `Accept-Language: ru-RU, en;q=0.8` |
| `Cookie` | Куки, ранее установленные сервером | `Cookie: session=abc123; theme=dark` |
| `User-Agent` | Идентификатор клиента: браузер, версия, ОС | `User-Agent: Mozilla/5.0 Chrome/120` |
| `Referer` | URL страницы с которой сделан запрос | `Referer: https://example.com/products` |
| `Origin` | Источник запроса (схема + домен). Ключевой для CORS | `Origin: https://app.example.com` |
| `If-Modified-Since` | Условный GET: вернуть только если изменилось | `If-Modified-Since: Tue, 01 Jan 2024` |
| `If-None-Match` | Условный GET по ETag. Если совпадает — 304 | `If-None-Match: "33a64df5..."` |
| `Connection` | Управление соединением. По умолчанию keep-alive | `Connection: keep-alive` |
| `Transfer-Encoding` | Способ передачи тела | `Transfer-Encoding: chunked` |

### 3.2 Заголовки ответа (Response Headers)

| Заголовок | Описание | Пример |
|---|---|---|
| `Content-Type` | MIME-тип тела ответа | `Content-Type: application/json; charset=utf-8` |
| `Content-Length` | Точный размер тела ответа | `Content-Length: 1024` |
| `Content-Encoding` | Алгоритм сжатия тела ответа | `Content-Encoding: gzip` |
| `Set-Cookie` | Устанавливает куки в браузере. Один заголовок — одна кука | `Set-Cookie: session=xyz; HttpOnly; Secure; Max-Age=3600` |
| `Location` | URL для редиректа (3xx) или созданного ресурса (201) | `Location: /api/users/43` |
| `Cache-Control` | Директивы кеширования | `Cache-Control: max-age=3600, public` |
| `ETag` | Уникальный ID версии ресурса (для условных запросов) | `ETag: "33a64df5..."` |
| `Last-Modified` | Дата последнего изменения ресурса | `Last-Modified: Tue, 15 Jan 2024 12:00:00 GMT` |
| `WWW-Authenticate` | При 401 — схема аутентификации | `WWW-Authenticate: Bearer realm="api"` |
| `Access-Control-Allow-Origin` | CORS: разрешённые источники | `Access-Control-Allow-Origin: *` |
| `Access-Control-Allow-Methods` | CORS: разрешённые методы | `Access-Control-Allow-Methods: GET, POST` |
| `Retry-After` | При 429/503 — через сколько секунд повторить | `Retry-After: 120` |
| `X-Request-Id` | Кастомный ID запроса для трассировки | `X-Request-Id: 550e8400-e29b-41d4...` |
| `Strict-Transport-Security` | HSTS: требует HTTPS. Защита от downgrade-атак | `Strict-Transport-Security: max-age=31536000` |
| `X-Content-Type-Options` | Запрет MIME-сниффинга браузером | `X-Content-Type-Options: nosniff` |

---

## 4. Коды статуса

Трёхзначный код в строке ответа. Первая цифра — класс.

### 4.1 1xx — Информационные

| Код | Название | Описание |
|---|---|---|
| 100 | Continue | Сервер получил заголовки, клиент может отправлять тело. Используется с `Expect: 100-continue` |
| 101 | Switching Protocols | Сервер принимает смену протокола. Используется при апгрейде до WebSocket |
| 102 | Processing | Сервер обрабатывает запрос, ответ ещё не готов. Предотвращает таймаут |
| 103 | Early Hints | Предварительная отправка заголовков `Link` до финального ответа |

### 4.2 2xx — Успех

| Код | Название | Описание |
|---|---|---|
| 200 | OK | Универсальный успешный ответ. Для GET — данные в теле |
| 201 | Created | Ресурс создан. Всегда с заголовком `Location` |
| 202 | Accepted | Запрос принят, обработка ещё не завершена (асинхронные задачи) |
| 203 | Non-Authoritative Information | Данные получены от прокси, не от оригинального сервера |
| 204 | No Content | Успех, тело ответа пустое. Стандарт для DELETE и PATCH |
| 205 | Reset Content | Успех, клиент должен сбросить форму/представление |
| 206 | Partial Content | Частичный контент по `Range`-запросу. Основа докачки и видео-стриминга |
| 207 | Multi-Status | Несколько статусов для разных под-запросов (WebDAV) |
| 208 | Already Reported | Результаты уже включены в предыдущий Multi-Status |
| 226 | IM Used | GET с delta-кодированием. Тело — изменения относительно базовой версии |

### 4.3 3xx — Перенаправление

| Код | Название | Описание |
|---|---|---|
| 300 | Multiple Choices | Несколько вариантов ресурса, клиент должен выбрать |
| 301 | Moved Permanently | Ресурс перемещён навсегда. Поисковики обновляют URL |
| 302 | Found | Временный редирект. Метод меняется на GET |
| 303 | See Other | После POST перенаправить на GET. Паттерн Post/Redirect/Get |
| 304 | Not Modified | Ресурс не изменился. Браузер берёт из кеша. Тела нет |
| 305 | Use Proxy | Устаревший. Использовать прокси из `Location` |
| 307 | Temporary Redirect | Временный редирект **с сохранением метода**. POST остаётся POST |
| 308 | Permanent Redirect | Постоянный редирект **с сохранением метода**. Современная замена 301 |

> **302 vs 307:** оба временные, но 302 меняет метод на GET, а 307 сохраняет оригинальный метод.  
> **301 vs 308:** оба постоянные, но 301 меняет метод на GET, а 308 сохраняет.

### 4.4 4xx — Ошибки клиента

| Код | Название | Описание |
|---|---|---|
| 400 | Bad Request | Некорректный запрос: плохой JSON, отсутствующие поля, невалидные данные |
| 401 | Unauthorized | Не аутентифицирован. Токен отсутствует, истёк или невалиден. Всегда с `WWW-Authenticate` |
| 402 | Payment Required | Зарезервирован. Применяется в API при превышении лимита платного плана |
| 403 | Forbidden | Аутентифицирован, но нет прав. Повторная аутентификация не поможет |
| 404 | Not Found | Ресурс не найден. Также используется вместо 403 чтобы скрыть существование ресурса |
| 405 | Method Not Allowed | Метод не поддерживается для URL. Всегда с заголовком `Allow:` |
| 406 | Not Acceptable | Сервер не может вернуть данные в формате из `Accept` |
| 407 | Proxy Authentication Required | Требуется аутентификация на прокси, а не на целевом сервере |
| 408 | Request Timeout | Клиент не отправил запрос за отведённое время |
| 409 | Conflict | Конфликт с текущим состоянием: дубль email, race condition |
| 410 | Gone | Ресурс удалён навсегда. В отличие от 404, клиент знает что больше не нужно запрашивать |
| 411 | Length Required | Сервер требует заголовок `Content-Length` |
| 412 | Precondition Failed | Условие из `If-Match` / `If-Unmodified-Since` не выполнено |
| 413 | Content Too Large | Тело запроса превышает лимит. Типично при загрузке большого файла |
| 414 | URI Too Long | URL длиннее допустимого (обычно лимит 2048–8192 байт) |
| 415 | Unsupported Media Type | `Content-Type` запроса не поддерживается сервером |
| 416 | Range Not Satisfiable | Запрошенный `Range` выходит за пределы файла |
| 417 | Expectation Failed | Сервер не может выполнить условие из заголовка `Expect` |
| 418 | I'm a teapot | Первоапрельская шутка (RFC 2324, 1998). Чайник отказывается варить кофе |
| 421 | Misdirected Request | Запрос направлен на сервер который не может его обработать |
| 422 | Unprocessable Content | Синтаксис верный, но данные семантически некорректны (ошибки валидации) |
| 423 | Locked | Ресурс заблокирован другим клиентом (WebDAV) |
| 424 | Failed Dependency | Запрос не выполнен из-за ошибки зависимого запроса (WebDAV) |
| 425 | Too Early | Защита от replay-атак в TLS 1.3 Early Data |
| 426 | Upgrade Required | Клиент должен переключиться на другой протокол (указан в `Upgrade`) |
| 428 | Precondition Required | Сервер требует условный запрос (If-Match). Защита от «потерянных обновлений» |
| 429 | Too Many Requests | Превышен rate limit. Всегда с заголовком `Retry-After` |
| 431 | Request Header Fields Too Large | Заголовки запроса слишком большие (куки, токены) |
| 451 | Unavailable For Legal Reasons | Недоступно по юридическим причинам (цензура, авторские права) |

> **401 vs 403 — самая частая путаница:**  
> `401` = «Я не знаю кто ты» (нет/плохой токен)  
> `403` = «Знаю, но сюда нельзя» (нет прав)

### 4.5 5xx — Ошибки сервера

| Код | Название | Описание |
|---|---|---|
| 500 | Internal Server Error | Общая ошибка сервера. Необработанное исключение, падение кода |
| 501 | Not Implemented | Метод не реализован на сервере |
| 502 | Bad Gateway | Прокси получил некорректный ответ от бэкенда. Типично при падении сервиса за nginx |
| 503 | Service Unavailable | Сервер временно недоступен: перегружен или на обслуживании. С `Retry-After` |
| 504 | Gateway Timeout | Прокси не дождался ответа от бэкенда. Бэкенд завис или слишком медленный |
| 505 | HTTP Version Not Supported | Сервер не поддерживает версию протокола из запроса |
| 506 | Variant Also Negotiates | Ошибка конфигурации content negotiation |
| 507 | Insufficient Storage | Недостаточно места на сервере (WebDAV, загрузка файлов) |
| 508 | Loop Detected | Бесконечный цикл при обработке запроса (WebDAV) |
| 510 | Not Extended | Сервер требует расширений протокола HTTP |
| 511 | Network Authentication Required | Нужна аутентификация в сети (captive portal в Wi-Fi) |

---

## 5. Шпаргалка

### Выбор метода

```
Хочу получить данные?              → GET
Хочу создать новый ресурс?         → POST
Хочу заменить ресурс целиком?      → PUT
Хочу изменить одно-два поля?       → PATCH
Хочу удалить ресурс?               → DELETE
Хочу проверить ресурс без загрузки → HEAD
Хочу узнать что умеет сервер?      → OPTIONS
```

### Правильный код ответа

```
GET успешно?           → 200 OK
POST создал ресурс?    → 201 Created + Location
Операция без данных?   → 204 No Content
Временный редирект?    → 307 (метод сохраняется) или 302 (метод → GET)
Постоянный редирект?   → 308 (метод сохраняется) или 301 (метод → GET)
Плохие данные?         → 400 Bad Request
Нет токена/плохой?     → 401 Unauthorized
Нет прав?              → 403 Forbidden
Не нашёл?              → 404 Not Found
Ошибка валидации?      → 422 Unprocessable Content
Rate limit?            → 429 Too Many Requests
Упал сервер?           → 500 Internal Server Error
Упал бэкенд за nginx?  → 502 Bad Gateway
Сервис недоступен?     → 503 Service Unavailable
Бэкенд завис?          → 504 Gateway Timeout
```

### Ключевые концепции

| Термин | Суть |
|---|---|
| **Идемпотентность** | Повторный запрос с теми же данными не меняет результат. GET, PUT, DELETE, HEAD, OPTIONS — идемпотентны. POST — нет |
| **Безопасный метод** | Не изменяет данные на сервере. GET, HEAD, OPTIONS, TRACE |
| **CORS preflight** | Браузер автоматически делает OPTIONS перед кросс-доменным запросом |
| **Условный запрос** | GET с `If-None-Match` или `If-Modified-Since`. Если ресурс не изменился → 304 без тела |
| **Кеширование** | Управляется через `Cache-Control`, `ETag`, `Last-Modified` |
| **keep-alive** | В HTTP/1.1 соединение по умолчанию не закрывается после запроса |
| **chunked transfer** | Передача тела частями без заранее известного `Content-Length` |

---

*Конспект составлен по материалам: RFC 7230, RFC 7231, RFC 7232, RFC 7233, RFC 7234, RFC 7235, RFC 2324 (418)*
