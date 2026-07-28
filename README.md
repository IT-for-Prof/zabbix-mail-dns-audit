# Zabbix Mail DNS Audit

![Zabbix 7.0+](https://img.shields.io/badge/Zabbix-7.0%2B-blue)
![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-green)

Мониторинг почтовой инфраструктуры доменов в Zabbix: MX, SPF, DMARC, DKIM, DNSBL, DNSSEC, PTR/FCrDNS для MX.

**Автор:** itforprof.com by Konstantin Tyutyunnik

## О проекте

Zabbix Mail DNS Audit — интегрированное решение для аудита DNS конфигурации почтовых доменов:

- **Python3 скрипт** для проверки DNS записей
- **Zabbix 7.0 шаблон** с готовыми элементами, триггерами и дашбордом
- **Автоматическое обнаружение** MX хостов и DNSBL зон через LLD
- **Кэширование** результатов для оптимизации нагрузки
- **Fallback механизм** при блокировке публичных резолверов

## Возможности

- ✅ Проверка MX записей и TTL
- ✅ Анализ SPF (RFC 7208), подсчёт lookups
- ✅ Мониторинг DMARC политик
- ✅ Отслеживание DKIM ключей и валидация размера RSA ключа (алерты при ключе < 2048 бит или ≤ 1024 бит)
- ✅ Обнаружение режима выравнивания DMARC (adkim/aspf: relaxed или strict)
- ✅ Обнаружение нарушения MX → CNAME (RFC 5321 §5 запрещает CNAME в качестве цели MX)
- ✅ Проверка DNSBL (со статусами: LISTED, NOT LISTED, POLICY/ERROR, CHECK FAILED)
- ✅ Валидация DNSSEC (DS записи, AD флаги)
- ✅ Проверка PTR/FCrDNS для MX (отсутствие PTR, несходимость, generic PTR)
- ✅ Транспортная безопасность: MTA-STS и TLS-RPT
- ✅ BIMI (наличие TXT default._bimi)
- ✅ Консистентность авторитативных NS (SOA serial)
- ✅ Расширенные триггеры DMARC (p=none, pct<100) и SPF (+all, ?all)
- ✅ Мониторинг скорости DNS (порог {$DNS_SLOW_MS})
- ✅ Поддержка IPv6 (опционально)
- ✅ Несколько DNS резолверов с перемешиванием
- ✅ Локальное кэширование результатов
- ✅ Проверка DNS автоконфигурации почтового клиента (autoconfig, autodiscover, SRV)
- ✅ Отображение изменений до/после: триггеры SPF, MX, DKIM и DMARC показывают «было → стало» в колонке Info списка проблем (Zabbix operational data)

- ✅ Дубликаты записей: MX, DMARC, DKIM-селекторы, NS, SOA (две DMARC-записи по RFC 7489 отключают политику целиком)
- ✅ Null MX (RFC 7505): домен, отключивший приём почты, называется прямо, а не выдаётся за отсутствие MX
- ✅ Отозванный ключ DKIM (пустой `p=`) и тестовый режим `t=y` (RFC 6376 §3.6.1) — запись на месте, а защиты нет
- ✅ Нейм-серверы, не отвечающие SOA: молчащий участник делегирования невидим для проверки согласованности серийников
- ✅ Пооперационные признаки видимости: проверка отсутствия утверждает «записи нет» только когда её собственные запросы ответили
- ✅ Обнаружение по каждому адресу, MX-хосту, DKIM-селектору и нейм-серверу: статус PTR, CNAME, размер ключа, серийник SOA
- ✅ Адреса, оставшиеся вне проверки по чёрным спискам, видны отдельно — «не проверено» не читается как «чисто»
- ✅ Смена NS- и DS-записей с показом «было → стало»

## Требования

- Zabbix 7.0+
- Python 3.11+ в отдельном окружении по пути `/opt/zabbix-mail-dns/venv` (см. шаг 1)
- dnspython 2.6+ (ставится в это окружение)
- Linux/Unix окружение
- Доступ в Интернет для DNS и DNSBL запросов

> **Почему venv, а не системный Python.** Скрипт исполняется на прокси, а они бывают
> разных поколений: на одной машине системным остаётся Python 3.6, где нет
> `ipaddress.subnet_of()`. Отдельное окружение по одинаковому пути даёт всем машинам
> один интерпретатор и одну версию dnspython, поэтому скрипт остаётся байт-в-байт
> одинаковым везде, а поведение — воспроизводимым.

## Быстрая установка

### Шаг 1: Окружение Python

Одинаково на сервере Zabbix и на каждом прокси, где исполняется проверка:

```bash
# Выбрать самый новый доступный интерпретатор
best=""; for v in 3.13 3.12 3.11; do [ -x /usr/bin/python$v ] && { best=$v; break; }; done

mkdir -p /opt/zabbix-mail-dns
/usr/bin/python$best -m venv /opt/zabbix-mail-dns/venv
/opt/zabbix-mail-dns/venv/bin/pip install --upgrade pip
/opt/zabbix-mail-dns/venv/bin/pip install "dnspython>=2.6"
chown -R zabbix:zabbix /opt/zabbix-mail-dns
```

Проверка:

```bash
/opt/zabbix-mail-dns/venv/bin/python3 -c "import sys, dns; print(sys.version, dns.__version__)"
```

Шебанг скрипта указывает на это окружение, поэтому системный Python не используется и
конфликтов с пакетами дистрибутива (PEP 668, `externally-managed-environment`) не
возникает.

### Шаг 2: Развёртывание скрипта

Выберите один из трёх вариантов:

#### Вариант A: Git (полное клонирование)

```bash
git clone https://github.com/IT-for-Prof/zabbix-mail-dns-audit.git
cd zabbix-mail-dns-audit
cp externalscripts/mail.dns.audit /usr/lib/zabbix/externalscripts/
chmod 755 /usr/lib/zabbix/externalscripts/mail.dns.audit
chown zabbix:zabbix /usr/lib/zabbix/externalscripts/mail.dns.audit
```

#### Вариант B: wget (прямая загрузка скрипта)

```bash
# Загрузка скрипта напрямую в Zabbix
wget -O /usr/lib/zabbix/externalscripts/mail.dns.audit \
  https://raw.githubusercontent.com/IT-for-Prof/zabbix-mail-dns-audit/main/externalscripts/mail.dns.audit

# Установка прав
chmod 755 /usr/lib/zabbix/externalscripts/mail.dns.audit
chown zabbix:zabbix /usr/lib/zabbix/externalscripts/mail.dns.audit
```

#### Вариант C: curl (альтернативная загрузка)

```bash
# Загрузка скрипта через curl
curl -L https://raw.githubusercontent.com/IT-for-Prof/zabbix-mail-dns-audit/main/externalscripts/mail.dns.audit \
  -o /usr/lib/zabbix/externalscripts/mail.dns.audit

# Установка прав
chmod 755 /usr/lib/zabbix/externalscripts/mail.dns.audit
chown zabbix:zabbix /usr/lib/zabbix/externalscripts/mail.dns.audit
```

#### Проверка установки скрипта

```bash
# Проверка наличия файла
ls -l /usr/lib/zabbix/externalscripts/mail.dns.audit

# Проверка зависимостей (версия скрипта, Python, dnspython)
/usr/lib/zabbix/externalscripts/mail.dns.audit --selfcheck

# Тест работоспособности
/usr/lib/zabbix/externalscripts/mail.dns.audit example.com 8.8.8.8 3
```

> **Zabbix Proxy:** Если хосты мониторятся через **Zabbix Proxy**, разверните скрипт и Python-зависимости на **прокси-сервере**, а не на Zabbix Server. Внешние скрипты выполняются на той машине (сервер или прокси), которая мониторит хост. Шаги установки одинаковы для каждого прокси. После установки на каждой машине запустите `--selfcheck`.

> **Таймаут выполнения:** скрипт ограничивает общее время работы дедлайном (по умолчанию 25 c, переменная окружения `MAIL_DNS_DEADLINE_SEC`), который должен держаться **ниже** таймаута внешних проверок Zabbix. Тогда зависший резолвер даёт понятную ошибку (`meta.error`) вместо «Timeout while executing a shell script».
>
> **Таймаут обязательно поднять вручную.** У внешних проверок Zabbix значение по умолчанию — **3 секунды** при допустимом диапазоне 1–30, а не 30 секунд. Типичный прогон занимает около 5 секунд, поэтому на умолчании поллер убьёт скрипт раньше, чем сработает дедлайн, и аварийный конверт вы не увидите никогда. Задайте таймаут внешних проверок в 30 секунд (*Administration → General → Timeouts*) и оставьте `MAIL_DNS_DEADLINE_SEC ≈ Timeout − 5`. Значение на прокси перекрывает глобальное, а значение элемента — оба; проверка исполняется на прокси, так что поднимать нужно именно там.

### Шаг 3: Загрузка шаблона и импорт

**Вариант A: Git (уже скачан)**

```bash
# Шаблон уже находится в клонированном репозитории
ls template_mail_dns_audit_zabbix.yaml
```

**Вариант B: wget (загрузка шаблона)**

```bash
# Загрузка шаблона для импорта
wget -O /tmp/template_mail_dns_audit_zabbix.yaml \
  https://raw.githubusercontent.com/IT-for-Prof/zabbix-mail-dns-audit/main/template_mail_dns_audit_zabbix.yaml
```

**Вариант C: curl (загрузка шаблона)**

```bash
# Загрузка шаблона через curl
curl -L https://raw.githubusercontent.com/IT-for-Prof/zabbix-mail-dns-audit/main/template_mail_dns_audit_zabbix.yaml \
  -o /tmp/template_mail_dns_audit_zabbix.yaml
```

**Импорт в Zabbix:**

1. Откройте веб-интерфейс Zabbix
2. Admin → Templates
3. Нажмите Import
4. Выберите файл `template_mail_dns_audit_zabbix.yaml`
5. Нажмите Import

### Шаг 4: Создание хоста для мониторинга

1. Data Collection → Hosts
2. Create Host
3. Заполните:
   - Host name: `example.com` (или имя домена)
   - Visible name: видимое имя
   - Groups: выберите группу
   - Interfaces: `127.0.0.1` (заглушка — внешние скрипты не используют интерфейс хоста)
4. Перейдите на вкладку Templates
5. Добавьте `Template Mail DNS Audit Zabbix`
6. Create

## Обновление

### Шаг 1: Обновить скрипт

```bash
wget -O /usr/lib/zabbix/externalscripts/mail.dns.audit \
  https://raw.githubusercontent.com/IT-for-Prof/zabbix-mail-dns-audit/main/externalscripts/mail.dns.audit
chmod 755 /usr/lib/zabbix/externalscripts/mail.dns.audit
chown zabbix:zabbix /usr/lib/zabbix/externalscripts/mail.dns.audit
```

> **Zabbix Proxy:** Обновите скрипт на **каждом прокси-сервере**, где он установлен.

### Шаг 2: Обновить шаблон

```bash
wget -O /tmp/template_mail_dns_audit_zabbix.yaml \
  https://raw.githubusercontent.com/IT-for-Prof/zabbix-mail-dns-audit/main/template_mail_dns_audit_zabbix.yaml
```

Импорт в Zabbix: Data collection → Templates → Import → выбрать файл → Import.

### Шаг 3: Проверить версию

После обновления триггер `Script version mismatch` должен исчезнуть. Если триггер остался — скрипт на сервере или прокси не обновлён.

```bash
# Проверить версию скрипта
/usr/lib/zabbix/externalscripts/mail.dns.audit --version
```

## Конфигурация

Все параметры настраиваются через макросы шаблона в Zabbix:

### Основные сетевые параметры

| Макрос | Значение | Описание |
|--------|----------|---------|
| `{$DNS_RESOLVER}` | (пусто) | IP резолверов (запятая). Пусто = системные |
| `{$DNS_TIMEOUT_SEC}` | `10` | Таймаут одного DNS-запроса (сек). Это цена зависшего запроса: при 3 с транзиентный сбой успевал выглядеть как «записи нет» |
| `{$DNS_SHUFFLE}` | `1` | Перемешивать резолверы (1/0) |
| `{$DNS_SLOW_MS}` | `12000` | Порог медленного DNS (мс). Должен превышать `{$DNS_TIMEOUT_SEC}`, иначе триггер вырождается в дубликат «один запрос отвалился» |

### SPF и проверки

| Макрос | Значение | Описание |
|--------|----------|---------|
| `{$SPF_MAX_LOOKUPS}` | `10` | Максимум lookups для SPF |
| `{$SPF_EXPECT_ALL}` | `-all\|~all` | Регулярное выражение для "all" |
| `{$CIDR_ALLOWLIST}` | (пусто) | Разрешённые CIDR для SPF |

### DNSBL параметры

| Макрос | Значение | Описание |
|--------|----------|---------|
| `{$DNSBL_ZONES}` | `zen.spamhaus.org,b.barracudacentral.org` | Зоны для проверки. Barracuda требует бесплатной регистрации опрашивающих IP |
| `{$DNSBL_TEST_IP}` | `127.0.0.2` | Канареечный адрес: живой список обязан его вернуть. Пусто — самотест выключен |
| `{$DNSBL_CACHE_TTL_SEC}` | `1200` | TTL кэша DNSBL (сек) |
| `{$DNSBL_MAX_IP}` | `5` | Макс. IP для DNSBL (`0` — без ограничения) |
| `{$MAX_MX_CHECK}` | `5` | Макс. MX для проверки |

### Управление проверками

Макросы для включения/отключения отдельных проверок на уровне хоста. Переопределяют значения шаблона.

| Макрос | По умолчанию | Описание |
|--------|-------------|---------|
| `{$CHECK_BIMI}` | `1` | `0` — отключить триггер об отсутствии BIMI |
| `{$CHECK_DMARC_RUA}` | `0` | `1` — включить триггер, если DMARC есть, но `rua=` не задан (opt-in — `rua=` опционален по RFC 7489) |
| `{$CHECK_DNSSEC}` | `1` | `0` — отключить триггеры DNSSEC AD flag и DS record |
| `{$CHECK_MTA_STS}` | `1` | `0` — отключить триггер об отсутствии MTA-STS |
| `{$CHECK_TLS_RPT}` | `1` | `0` — отключить триггер об отсутствии TLS-RPT |
| `{$MAIL_CLIENT_AUTOCONFIG_CHECK}` | `1` | `0` — отключить триггеры autoconfig/autodiscover |
| `{$SPF_CHECK_MX_COVERAGE}` | `1` | `0` — отключить триггер "MX не авторизован в SPF" |

### Другое

| Макрос | Значение | Описание |
|--------|----------|---------|
| `{$CHECK_IPV6}` | `0` | Проверять AAAA (1/0) |
| `{$DKIM_SELECTORS}` | `default` | Селекторы DKIM (через запятую, без `._domainkey`) |
| `{$TEMPLATE_VERSION}` | `0.1.61` | Версия шаблона. Должна совпадать с `VERSION` в скрипте — иначе поднимется предупреждение о несовпадении |
| `{$MAIL_DNS_NODATA_SEC}` | `3h` | Порог отсутствия данных для nodata-триггера master item. Должен превышать два интервала опроса: при опросе раз в час значение `1800` держалось истинным полчаса из каждого часа, и триггер мигал постоянно |

### Признаки видимости и покрытие

| Макрос | Назначение |
|---|---|
| `{$MAIL_DNS_NODATA_SEC}` | Окно тишины до алерта «скрипт не запускается». Должно превышать удвоенный интервал опроса: при часовом опросе получасовое окно истинно половину каждого часа. Zabbix не вычисляет период меньше 30 секунд. |
| `{$DNSBL_MAX_IP}` | Сколько адресов проверять по чёрным спискам. PTR и FCrDNS проверяются у **каждого** адреса независимо от этого лимита — у обратного DNS нет внешних квот. Оставшиеся за лимитом считаются в `mail.dnsbl.not_checked`. |
| `{$CIDR_ALLOWLIST}` | Сети, которым разрешено быть в SPF. Пустое значение отключает сравнение; битые механизмы `ip4:`/`ip6:` считаются отдельно и сообщаются всегда. |

## Использование

### Проверка скрипта вручную

```bash
# Базовая проверка
./externalscripts/mail.dns.audit example.com

# С указанием резолвера
./externalscripts/mail.dns.audit example.com 8.8.8.8 3 0

# С полными параметрами
./externalscripts/mail.dns.audit example.com \
  "8.8.8.8" \           # resolver
  "3" \                 # timeout_sec
  "0" \                 # check_ipv6
  "zen.spamhaus.org" \  # dnsbl_zones
  "" \                  # cidr_allowlist
  "10" \                # spf_max_lookups
  "-all|~all" \         # spf_expect_all
  "1200" \              # dnsbl_cache_ttl
  "5" \                 # max_mx
  "1" \                 # dnsbl_max_ip
  "default" \           # dkim_selectors
  "1"                   # shuffle_resolvers
```

### Результаты в Zabbix

- **Latest Data**: просмотр элементов (mail.mx.count, mail.spf.status, mail.dnsbl.* и т.д.)
- **Triggers**: настроенные триггеры на проблемы (отсутствие MX, DNSBL, медленный DNS, nodata для master item)
- **Duplicate checks**: флаги и триггеры на дубли MX, DMARC, DKIM селекторов, NS, SOA
- **Dashboard**: "Mail DNS Audit Overview" отображает общий статус

## Тестирование

### Набор тестов и линтер

```bash
# Все четыре файла тестов. Каждый — самостоятельный скрипт, выход 1 при расхождении
python3 tests/test_wave1_contracts.py
python3 tests/test_ptr_states.py
python3 tests/test_dnsbl_states.py
python3 tests/test_template_contracts.py

# Линтер (правила F и E9; .ruff.toml включает скрипт без расширения .py)
ruff check .
```

> **Каким интерпретатором.** `test_template_contracts.py` разбирает YAML шаблона и
> требует PyYAML, а рабочее окружение `/opt/zabbix-mail-dns/venv` его намеренно не
> несёт — там только dnspython, потому что самому скрипту больше ничего не нужно.
> Поэтому тесты запускают **системным** `python3`, а не интерпретатором окружения.
> Этот же файл через `node` компилирует все JavaScript-шаги предобработки из шаблона,
> так что для него нужен установленный `node`.

### Встроенные симуляции

```bash
# Симуляция плохого SPF
./externalscripts/mail.dns.audit example.com 8.8.8.8 3 0 \
  "zen.spamhaus.org" "" "10" "-all|~all" "1200" "5" "1" "default" "1" \
  --simulate bad_spf

# Симуляция DNSBL
./externalscripts/mail.dns.audit example.com 8.8.8.8 3 0 \
  "zen.spamhaus.org" "" "10" "-all|~all" "1200" "5" "1" "default" "1" \
  --simulate dnsbl
```

### DNSBL самотест

```bash
# Проверка статуса тестового IP в DNSBL
./externalscripts/mail.dns.audit example.com 8.8.8.8 3 0 \
  "zen.spamhaus.org,b.barracudacentral.org" "" "10" "-all|~all" "1200" "5" "1" "default" "1" \
  --dnsbl-test-ip 127.0.0.2
```

### Отладка

```bash
# Включить отладочный вывод
DEBUG_DNSBL=1 ./externalscripts/mail.dns.audit example.com
```

## Устранение неполадок

### Скрипт не запускается: нет интерпретатора или dnspython

Все три прежних случая — `externally-managed-environment` (PEP 668), отсутствие
Python 3 нужной версии и отсутствие dnspython — решаются одним и тем же: окружением
из шага 1. Проверить, что оно на месте:

```bash
ls -l /opt/zabbix-mail-dns/venv/bin/python3
/usr/lib/zabbix/externalscripts/mail.dns.audit --selfcheck
```

`--selfcheck` печатает версию скрипта, версию Python и версию dnspython. Если окружения
нет, Zabbix получит структурированную ошибку в `meta.error`, а не пустой ответ, и
сработает триггер «DNS audit script error».

### DNSBL: "POLICY/ERROR" статус

Публичные резолверы (8.8.8.8) блокируются DNSBL провайдерами. Решение:

1. Установите локальный резолвер (Unbound/Bind) на локальной машине
2. Установите макрос: `{$DNS_RESOLVER} = "127.0.0.1"`

### Zabbix Proxy: скрипт не работает

Внешние скрипты выполняются на **прокси**, который мониторит хост, а не на Zabbix Server. Если элемент показывает "not supported" на хосте под прокси:

1. Разверните скрипт на каждом прокси-сервере:
```bash
# Выполнить на машине прокси
wget -O /usr/lib/zabbix/externalscripts/mail.dns.audit \
  https://raw.githubusercontent.com/IT-for-Prof/zabbix-mail-dns-audit/main/externalscripts/mail.dns.audit
chmod 755 /usr/lib/zabbix/externalscripts/mail.dns.audit
chown zabbix:zabbix /usr/lib/zabbix/externalscripts/mail.dns.audit
```

2. Установите Python и dnspython на прокси (те же шаги, что и для сервера выше).

3. Убедитесь, что путь `ExternalScripts` в `zabbix_proxy.conf` совпадает с `/usr/lib/zabbix/externalscripts/`.

4. Проверьте от имени пользователя zabbix на машине прокси:
```bash
su - zabbix -c "/usr/lib/zabbix/externalscripts/mail.dns.audit example.com"
```

### Скрипт не выполняется из Zabbix

```bash
# Проверка прав
ls -l /usr/lib/zabbix/externalscripts/mail.dns.audit

# Права должны быть 755, владелец zabbix:zabbix
chmod 755 /usr/lib/zabbix/externalscripts/mail.dns.audit
chown zabbix:zabbix /usr/lib/zabbix/externalscripts/mail.dns.audit

# Тест от имени пользователя zabbix
su - zabbix -c "/usr/lib/zabbix/externalscripts/mail.dns.audit example.com"
```

## Архитектура

### Поток данных

```
Zabbix Server (или Proxy, если хост мониторится через прокси)
    ↓
mail.dns.audit (Master Item — External Check)
    ↓
Python скрипт (externalscripts/mail.dns.audit)
    ├→ Получить MX записи
    ├→ Получить SPF/DMARC/DKIM
    ├→ Анализировать SPF механизмы
    ├→ Проверить DNSBL зоны
    └→ Верифицировать DNSSEC
    ↓
JSON результат + кэш
    ↓
LLD Discovery (автоматическое обнаружение)
    ├→ mail.mx[{#MXHOST}]
    ├→ mail.dnsbl[{#DNSBL_IP}][{#DNSBL_ZONE}]
    └→ Зависимые элементы
    ↓
Triggers & Alerts
```

### Кэширование

- DNSBL результаты хранятся в `/tmp/mail_dns_audit_cache.json` на машине, выполняющей скрипт (Zabbix Server или Proxy)
- TTL управляется макросом `{$DNSBL_CACHE_TTL_SEC}` (по умолчанию 1200 сек)
- Кэш ускоряет повторные проверки и снижает нагрузку

## История изменений

Полная история с обоснованиями: [CHANGELOG.md](CHANGELOG.md)

## Ссылки

- GitHub: https://github.com/IT-for-Prof/zabbix-mail-dns-audit
- Веб-сайт: https://itforprof.com
- Issues: https://github.com/IT-for-Prof/zabbix-mail-dns-audit/issues

