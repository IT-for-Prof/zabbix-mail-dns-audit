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
- ✅ Отслеживание DKIM ключей
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

**Способ A: виртуальное окружение (рекомендуется)**

```bash
apt update
apt install -y python3-full python3-venv

mkdir -p /opt/zabbix-dns-monitoring
cd /opt/zabbix-dns-monitoring

python3 -m venv .venv
. .venv/bin/activate

pip install -U pip
pip install dnspython
```

Дальнейший запуск скрипта:

```bash
. /opt/zabbix-dns-monitoring/.venv/bin/activate
python mail.dns.audit example.com
```

Или с полным путём:

```bash
/opt/zabbix-dns-monitoring/.venv/bin/python mail.dns.audit example.com
```

**Способ B: системный пакет (если доступен)**

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
apk add --no-cache python3 py3-pip
pip3 install dnspython
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

# Тест работоспособности
/usr/lib/zabbix/externalscripts/mail.dns.audit example.com 8.8.8.8 3
```

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
   - Interfaces: IP сервера Zabbix (localhost)
4. Перейдите на вкладку Templates
5. Добавьте `Template Mail DNS Audit Zabbix`
6. Create

## Конфигурация

Все параметры настраиваются через макросы шаблона в Zabbix:

### Основные сетевые параметры

| Макрос | Значение | Описание |
|--------|----------|---------|
| `{$DNS_RESOLVER}` | (пусто) | IP резолверов (запятая). Пусто = системные |
| `{$DNS_TIMEOUT_SEC}` | `3` | Таймаут DNS запроса (сек) |
| `{$DNS_SHUFFLE}` | `1` | Перемешивать резолверы (1/0) |
| `{$DNS_SLOW_MS}` | `3000` | Порог медленного DNS (ms) |

### SPF и проверки

| Макрос | Значение | Описание |
|--------|----------|---------|
| `{$SPF_MAX_LOOKUPS}` | `10` | Максимум lookups для SPF |
| `{$SPF_EXPECT_ALL}` | `-all\|~all` | Регулярное выражение для "all" |
| `{$CIDR_ALLOWLIST}` | (пусто) | Разрешённые CIDR для SPF |

### DNSBL параметры

| Макрос | Значение | Описание |
|--------|----------|---------|
| `{$DNSBL_ZONES}` | `zen.spamhaus.org,bl.spamcop.net` | Зоны для проверки |
| `{$DNSBL_CACHE_TTL_SEC}` | `1200` | TTL кэша DNSBL (сек) |
| `{$DNSBL_MAX_IP}` | `1` | Макс. IP для DNSBL |
| `{$MAX_MX_CHECK}` | `5` | Макс. MX для проверки |

### Другое

| Макрос | Значение | Описание |
|--------|----------|---------|
| `{$CHECK_IPV6}` | `0` | Проверять AAAA (1/0) |
| `{$DKIM_SELECTORS}` | `default` | Селекторы DKIM |
| `{$TEMPLATE_VERSION}` | `0.1.26` | Версия шаблона |
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
  "zen.spamhaus.org,bl.spamcop.net" "" "10" "-all|~all" "1200" "5" "1" "default" "1" \
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

Запуск скрипта Zabbix с venv:

```bash
/opt/dns-venv/bin/python /usr/lib/zabbix/externalscripts/mail.dns.audit example.com
```

Или добавьте в конфиг Zabbix (если запуск через внешний скрипт):

```bash
#!/bin/bash
. /opt/dns-venv/bin/activate
/usr/lib/zabbix/externalscripts/mail.dns.audit "$@"
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
Zabbix Server
    ↓
mail.dns.audit (Master Item)
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

- DNSBL результаты хранятся в `/tmp/mail_dns_audit_cache.json`
- TTL управляется макросом `{$DNSBL_CACHE_TTL_SEC}` (по умолчанию 1200 сек)
- Кэш ускоряет повторные проверки и снижает нагрузку

## История изменений

Полная история: [CHANGELOG.md](CHANGELOG.md)

Последние обновления:
- **v0.1.26** (2025-12-30): Решение проблемы таймаутов — {$DNS_RESOLVER} по умолчанию пуст для использования системного резолвера.
- **v0.1.18** (2025-12-26): Добавлен nodata-триггер для master item (обнаружение таймаутов/отсутствия данных).
- **v0.1.17** (2025-12-26): Добавлены проверки и триггеры на дубликаты DNS (MX, DMARC, DKIM, NS, SOA).
- **v0.1.16** (2025-12-24): Удалены UUID из шаблона для портативности.
- **v0.1.15** (2025-12-24): Добавлен shuffle контроль резолверов через макрос `{$DNS_SHUFFLE}`
- **v0.1.13** (2025-12-24): DNSBL fallback через альтернативные резолверы
- **v0.1.10** (2025-12-24): Ссылка на GitHub репозиторий в описании

## Лицензия

MIT License © itforprof.com by Konstantin Tyutyunnik

## Ссылки

- GitHub: https://github.com/IT-for-Prof/zabbix-mail-dns-audit
- Веб-сайт: https://itforprof.com
- Issues: https://github.com/IT-for-Prof/zabbix-mail-dns-audit/issues

