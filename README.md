# Zabbix Mail DNS Audit

![Zabbix 7.0+](https://img.shields.io/badge/Zabbix-7.0%2B-blue)
![Python 3.6+](https://img.shields.io/badge/Python-3.6%2B-green)

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

## Требования

- Zabbix 7.0+
- Python 3.6+
- dnspython 2.0+
- Linux/Unix окружение
- Доступ в Интернет для DNS и DNSBL запросов

## Быстрая установка

### Шаг 1: Установка зависимостей

#### Ubuntu/Debian 12+ и Python 3.11+ (PEP 668)

Начиная с Debian 12/Ubuntu 23.10, система защищает глобальный Python от модификации через pip. Используйте один из способов:

**Способ A: виртуальное окружение**

```bash
apt update
apt install -y python3-full python3-venv

mkdir -p /opt/zabbix-dns-monitoring
python3 -m venv /opt/zabbix-dns-monitoring/.venv
/opt/zabbix-dns-monitoring/.venv/bin/pip install -U pip dnspython
```

> **⚠️ Важно для Zabbix:** Шебанг скрипта — `#!/usr/bin/python3` (системный Python). Zabbix запускает внешний скрипт напрямую через шебанг — виртуальное окружение **не активируется**. После копирования скрипта в `externalscripts/` обновите шебанг:
>
> ```bash
> sed -i '1s|.*|#!/opt/zabbix-dns-monitoring/.venv/bin/python3|' /usr/lib/zabbix/externalscripts/mail.dns.audit
> ```
>
> Или используйте **Способ B** (`python3-dnspython` через apt) — проще и не требует изменения шебанга.

Ручное тестирование:

```bash
/opt/zabbix-dns-monitoring/.venv/bin/python3 /usr/lib/zabbix/externalscripts/mail.dns.audit example.com
```

**Способ B: системный пакет (рекомендуется для Zabbix)**

```bash
apt update
apt install -y python3-dnspython
```

Если пакет `python3-dnspython` не найден в репозитории, используйте Способ A.

**Способ C: для миграции существующего кода (не рекомендуется)**

Если абсолютно необходимо нарушить защиту (на свой риск):

```bash
pip3 install dnspython --break-system-packages
```

Это может нарушить системные зависимости при обновлении Python.

#### Ubuntu/Debian (старые версии до 22.04)

```bash
apt update
apt install -y python3 python3-pip
pip3 install dnspython
```

#### CentOS/RHEL

```bash
yum install -y python3 python3-pip
pip3 install dnspython
```

#### Alpine (контейнер)

```bash
apk add --no-cache python3 py3-dnspython
```

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

> **Таймаут выполнения:** скрипт ограничивает общее время работы дедлайном (по умолчанию 25 c, переменная окружения `MAIL_DNS_DEADLINE_SEC`), который держится **ниже** значения `Timeout` внешних проверок Zabbix (по умолчанию 30 c). Зависший резолвер даёт понятную ошибку (`meta.error`) вместо «Timeout while executing a shell script». Если вы меняете `Timeout` в `zabbix_server.conf`/`zabbix_proxy.conf`, задайте `MAIL_DNS_DEADLINE_SEC ≈ Timeout − 5`.

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
| `{$DNSBL_MAX_IP}` | `1` | Макс. IP для DNSBL |
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
| `{$TEMPLATE_VERSION}` | `0.1.52` | Версия шаблона |
| `{$MAIL_DNS_NODATA_SEC}` | `1800` | Порог отсутствия данных (сек) для nodata-триггера master item |

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

### Ошибка: `error: externally-managed-environment` при установке dnspython

Это ошибка PEP 668 в Debian 12+ и Ubuntu 23.10+, защищающая системный Python.

**Решение: используйте виртуальное окружение**

```bash
apt install -y python3-full python3-venv

# Создайте окружение
python3 -m venv /opt/dns-venv
. /opt/dns-venv/bin/activate

# Установите пакет
pip install dnspython
```

Обновите шебанг развёрнутого скрипта, чтобы он использовал Python из venv:

```bash
sed -i '1s|.*|#!/opt/dns-venv/bin/python3|' /usr/lib/zabbix/externalscripts/mail.dns.audit
```

Или проверьте вручную:

```bash
/opt/dns-venv/bin/python3 /usr/lib/zabbix/externalscripts/mail.dns.audit example.com
```

**Альтернатива: системный пакет (если доступен)**

```bash
apt install -y python3-dnspython
```

### Python 3 не найден

```bash
# На сервере Zabbix установить Python
apt install -y python3 python3-pip
pip3 install dnspython
```

### dnspython не установлена

```bash
pip3 install dnspython>=2.0

# Или в контейнере:
docker exec zabbix-server apk add --no-cache py3-dnspython
```

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

Полная история: [CHANGELOG.md](CHANGELOG.md)

Последние обновления:
- **v0.1.52** — Отсутствие записи больше нельзя утверждать с неполного обзора: скрипт считает неудачные DNS-запросы (`meta.lookup_failures`), а HIGH-триггеры «No MX records found» и «DKIM record missing» получили условие `lookup_failures=0`. Раньше недоступный резолвер давал два ложных HIGH-пейджа на хост — воспроизведено: 16 неудачных запросов, пустые MX и DKIM, при этом `meta.error` пуст, так что зависимость от «DNS audit script error» не спасала. Новый триггер сообщает, что проверки отсутствия сейчас подавлены — иначе они замолкали бы тихо. Фильтр `min(...,#2)` добавлен триггеру FCrDNS. Значение `-1` у `mail.dns.lookup_failures` означает «не измерено» и намеренно отличается от `0`
- **v0.1.51** — Транзиентный сбой DNS больше не выдаётся за отсутствие PTR: `query_records()` схлопывала `NXDOMAIN`, `NoAnswer`, `Timeout` и `NoNameservers` в один пустой список, и `check_ptr_fcrdns()` читала его как `MISSING` — 13 ложных HIGH за 33 дня при живой PTR-записи. Добавлена `query_records_ex()` с причиной неуспеха; авторитетным отрицанием считаются только `NXDOMAIN`/`NoAnswer`. То же исправлено на прямом A-запросе. Аварийный скелет дополнен корнями `ptr` и `dmarc` (`lld_*` намеренно не добавлены — пустой `data` запускает удаление обнаруженного). Новые элементы: счётчик ошибок PTR, список адресов без PTR, самотест живости DNSBL-зон. Первый тест в репозитории: `tests/test_ptr_states.py`
- **v0.1.50** — Конверты ошибок теперь содержат полную структуру результата (а не только `meta`): при ошибке запуска/дедлайне/исключении ~35 зависимых элементов больше не уходят в NOTSUPPORTED — скелет вынесен в единый `_default_result()`, ошибка резолвит все JSONPath (заполнен только `meta.error`), триггер «DNS audit script error» по-прежнему срабатывает; Ctrl-C (`KeyboardInterrupt`) пробрасывается; в README описана связь `MAIL_DNS_DEADLINE_SEC` ↔ Zabbix `Timeout`
- **v0.1.49** — Надёжность и информативность: отсутствие зависимости `dnspython` больше не выдаёт сырой traceback (молчаливый NOTSUPPORTED), а структурированный `meta.error` — триггер «DNS audit script error» срабатывает сразу с понятным сообщением; добавлен общий дедлайн выполнения (25с, env `MAIL_DNS_DEADLINE_SEC`) — зависший резолвер даёт чистую ошибку вместо «Timeout while executing a shell script»; верхнеуровневый перехват исключений в `main()`; флаг `--selfcheck` для проверки зависимостей после установки; `requirements.txt`; в шаблоне у `mail.dns.error` добавлен обработчик ошибок (не-JSON вывод тоже взводит триггер ошибки)
- **v0.1.48** — DNSSEC: установлен бит EDNS DO — флаг `ad_flag` ранее был всегда `False`, т.к. валидирующий резолвер не возвращал флаг AD без запроса DNSSEC (исправление #1, спасибо @Salzi); таймаут `{$DNS_TIMEOUT_SEC}` теперь применяется на всех путях резолвера (раньше игнорировался при пустом `{$DNS_RESOLVER}`); `ad_flag` теперь учитывает ответы apex `MX` и `DS`, а не только A/AAAA MX-хостов — подписанные домены с почтой во внешней неподписанной зоне (Microsoft 365 / Proofpoint, напр. `nasa.gov`) больше не показывают ложный `False`
- **v0.1.47** — Триггеры: имена проблем «DNSBL check failed» и «MX IP listed in DNSBL» (`*UNKNOWN*` → `{ITEM.LASTVALUE<N>}`), убрана задвоенная единица в «DNS query slow»; «было → стало» на триггерах изменения SPF/MX/DKIM/DMARC теперь работает через кросс-запусковый кэш скрипта; атомарная запись кэша
- **v0.1.46** — SPF: исправлен парсинг квалификаторов RFC 7208 §4.6.1 (`+mx`, `+a`, `-include:...` ранее игнорировались); исправлено ложное совпадение `all` с механизмом `a`; DNS-резолвер по умолчанию изменён на `127.0.0.1`
- **v0.1.45** — Кэш DNSBL: ошибки (CHECK FAILED, POLICY/ERROR) теперь кэшируются на 120 сек вместо полного TTL; смена DNS-резолвера больше не возвращает устаревшие результаты — резолвер включён в ключ кэша
- **v0.1.44** — DKIM: `rsa-unknown` вместо `rsa-0`; теги `dmarc_before`/`dmarc_after` на триггере понижения DMARC; блок `vendor:` с автором в метаданных шаблона Zabbix 7.0
- **v0.1.43** — Триггеры изменения DKIM и DMARC теперь показывают «было → стало» в колонке Info списка проблем
- **v0.1.42** — Триггеры изменения MX и SPF теперь показывают «было → стало» в колонке Info списка проблем
- **v0.1.41** — Имена триггеров: "DNS audit script error" показывает текст ошибки `{ITEM.LASTVALUE}`; "DMARC rua= malformed" показывает неверное значение; "DNS query slow" показывает фактическое время; исправлен баг `{ITEM.LASTVALUE3}` в описании триггера "MX IP listed in DNSBL"
- **v0.1.40** — Триггер "DNSBL check failed" теперь показывает IP, зону и причину прямо в имени проблемы через `{?last(...mail.dnsbl.listed.details)}`; описание обновлено с указанием общих причин (публичный резолвер заблокирован, рекомендуется локальный Unbound)
- **v0.1.39** — DKIM ключ: размер RSA (min_key_bits, weak_key_count), триггеры WARNING (<2048 бит) и HIGH (≤1024 бит); DMARC adkim/aspf — информационные элементы; MX→CNAME нарушение RFC 5321 §5 — триггер WARNING
- **v0.1.38** — DMARC rua=: opt-in триггер на отсутствие (INFO, {$CHECK_DMARC_RUA}=0 по умолчанию) + всегда активный триггер на некорректный формат (WARNING)
- **v0.1.37** — Удалён триггер DMARC rua= missing — rua= опционален по RFC 7489; отсутствие допустимо
- **v0.1.36** — Bugfix: имена DNSBL-триггеров теперь показывают точный текст ответа; добавлены 6 пропущенных skip-макросов; восстановлена зависимость от mail.dns.error в 15 триггерах; исправлено значение {$TEMPLATE_VERSION}
- **v0.1.35** — Макросы для отключения проверок DNSSEC/MTA-STS/TLS-RPT/BIMI на уровне хоста ({$CHECK_DNSSEC}, {$CHECK_MTA_STS}, {$CHECK_TLS_RPT}, {$CHECK_BIMI})
- **v0.1.34** — Bugfix: обработка null в DMARC rua=, определение mx_covered через a:hostname в SPF, синхронизация VERSION скрипта
- **v0.1.33** — 8 новых триггеров (отсутствие MX, нарушения RFC SPF, обнаружение изменений, DMARC rua, сбои DNSBL), зависимости от ошибок на всех триггерах, макрос {$MAIL_CLIENT_AUTOCONFIG_CHECK}
- **v0.1.32** (2026-02-20): Добавлен элемент `mail.script.version` и триггер WARNING на несовпадение версии скрипта с `{$TEMPLATE_VERSION}` — выявляет устаревший скрипт на прокси.
- **v0.1.31** (2026-02-20): Исправлен shebang скрипта (`#!/usr/bin/python3`); добавлен `.gitattributes` для LF-окончаний строк — устраняет сбой запуска скрипта из Zabbix из-за CRLF и отсутствия PATH.
- **v0.1.30** (2026-02-20): Повышена важность триггера DMARC p=none до WARNING; добавлен триггер HIGH на откат политики DMARC с quarantine/reject → none.
- **v0.1.29** (2026-02-20): Добавлены проверки DNS автоконфигурации почтового клиента (autoconfig, autodiscover, SRV) и соответствующие триггеры.
- **v0.1.28** (2026-02-20): Улучшена информативность триггеров — добавлены {HOST.HOST}, контекстные данные и описания с рекомендациями.
- **v0.1.27** (2026-01-13): Замена {HOST.NAME} на {HOST.HOST} в ключах элементов для надёжности.
- **v0.1.26** (2025-12-30): Решение проблемы таймаутов — {$DNS_RESOLVER} по умолчанию пуст для использования системного резолвера.
- **v0.1.18** (2025-12-26): Добавлен nodata-триггер для master item (обнаружение таймаутов/отсутствия данных).
- **v0.1.17** (2025-12-26): Добавлены проверки и триггеры на дубликаты DNS (MX, DMARC, DKIM, NS, SOA).
- **v0.1.16** (2025-12-24): Удалены UUID из шаблона для портативности.

## Ссылки

- GitHub: https://github.com/IT-for-Prof/zabbix-mail-dns-audit
- Веб-сайт: https://itforprof.com
- Issues: https://github.com/IT-for-Prof/zabbix-mail-dns-audit/issues

