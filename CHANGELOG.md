# Changelog
All notable changes to this project will be documented in this file.

## [0.1.30] - 2026-02-20

### Changed
- DMARC `p=none` trigger severity raised from INFO to WARNING.

### Added
- New HIGH trigger: DMARC policy downgraded to none (detects regression from `quarantine`/`reject` → `none` using `last(,#2)`).

## [0.1.29] - 2026-02-20

### Added
- `check_mail_client_config()` in `mail.dns.audit`: DNS presence checks for `autoconfig.<domain>` (A/CNAME), `autodiscover.<domain>` (A/CNAME), and `_autodiscover._tcp.<domain>` (SRV).
- Five new dependent Zabbix items: `mail.autoconfig.present`, `mail.autoconfig.type`, `mail.autodiscover.present`, `mail.autodiscover.type`, `mail.autodiscover_srv.present`.
- Three new triggers: autoconfig missing (INFO), autodiscover missing (INFO), no autoconfiguration at all (WARNING).
- New DNS script error trigger (`mail.dns.error` non-empty → HIGH) used as dependency to suppress autoconfiguration alerts during script failures.

## [0.1.28] - 2026-02-20

- Значительно улучшена информативность триггеров за счет добавления контекстной информации.
- Все триггеры теперь включают {HOST.HOST} для четкой идентификации целевого домена.
- Расширены описания триггеров с рекомендациями по исправлению проблем.
- Добавлены значения параметров в имена триггеров (счетчики, проценты, пороги) для быстрого анализа.
- LLD триггеры (DNSBL, PTR) теперь показывают полную информацию о проблеме: MX хост, IP, тип ошибки.
- Версия шаблона повышена до 0.1.28.

## [0.1.27] - 2026-01-13
- Значение макроса {$DNS_RESOLVER} в шаблоне установлено в пустое значение для использования системного резолвера по умолчанию.
- Предыдущий список публичных резолверов перенесен в описание макроса как справочный.
- Версия шаблона повышена до 0.1.26.
- Добавлены проверки и триггеры на дубликаты DNS записей (MX, DMARC, DKIM селекторы, NS, SOA) в скрипте и шаблоне.
- В master item JSON добавлен блок duplicates для вывода флагов и деталей дублей.
- Версии скрипта и шаблона повышены до 0.1.17.

## [0.1.18] - 2025-12-26
- Добавлен nodata-триггер для master item mail.dns.audit (обнаружение таймаутов/отсутствия данных).
- Макрос {$MAIL_DNS_NODATA_SEC}=1800 сек для порога отсутствия данных.
- Версии шаблона/доков повышены до 0.1.18.

## [0.1.19] - 2025-12-26
- Добавлены проверки PTR/FCrDNS для MX IP: статусы MISSING/NO_FCRDNS/GENERIC/OK, сводка в JSON.
- Новый dependent items: mail.ptr.missing.count, mail.ptr.nofcrdns.count, mail.ptr.generic.count; триггеры на отсутствие PTR (HIGH), FCrDNS fail (WARNING), generic PTR (INFO).
- Версия скрипта и шаблона повышена до 0.1.19.

## [0.1.20] - 2025-12-26
- Добавлены проверки MTA-STS и TLS-RPT, BIMI presence.
- Добавлен контроль консистентности авторитативных NS (SOA serial mismatch).
- Улучшены триггеры DMARC (p=none, pct<100) и SPF (+all HIGH, ?all INFO).
- Добавлен триггер на медленный DNS (mail.dns.query_time_ms > {$DNS_SLOW_MS}).
- Версии скрипта и шаблона повышены до 0.1.20.

## [0.1.21] - 2025-12-26
- Исправлено отсутствие полей plus_all/neutral_all в JSON при пустом SPF (исключает ошибки preprocessing JSONPath).
- Версии скрипта и шаблона повышены до 0.1.21.

## [0.1.22] - 2025-12-26
- Добавлены error_handler CUSTOM_VALUE в JSONPath для MTA-STS, TLS-RPT, BIMI presence, чтобы предотвращать ошибки preprocessing при отсутствии секции в старых данных master item.
- Версия шаблона повышена до 0.1.22 (скрипт остаётся 0.1.21).

## [0.1.23] - 2025-12-26
- Добавлены error_handler CUSTOM_VALUE для ns_consistency (consistent, mismatch) чтобы исключить ошибки preprocessing на старых данных master item.
- Версия шаблона повышена до 0.1.23 (скрипт остаётся 0.1.21).

## [0.1.24] - 2025-12-26
- Добавлены error_handler CUSTOM_VALUE для mail.spf.plus_all и mail.spf.neutral_all, чтобы исключить ошибки preprocessing при старых данных master item.
- Версия шаблона повышена до 0.1.24 (скрипт остаётся 0.1.21).

## [0.1.25] - 2025-12-26
- Уточнено описание макроса {$DKIM_SELECTORS}: селекторы без ._domainkey, через запятую без пробелов, с примерами.
- Версия шаблона повышена до 0.1.25 (скрипт остаётся 0.1.21).

## [0.1.27] - 2026-01-13
- Замена {HOST.NAME} на {HOST.HOST} в ключах item шаблона для повышения надежности и исключения зависимости от визуального имени хоста.
- {HOST.HOST} — техническое имя хоста, всегда заполнено и уникально, в отличие от {HOST.NAME}, которое может быть произвольным текстом.
- Версия шаблона повышена до 0.1.27.

## [0.1.26] - 2025-12-30
- Значение макроса {$DNS_RESOLVER} в шаблоне установлено в пустое значение для использования системного резолвера по умолчанию.
- Предыдущий список публичных резолверов перенесен в описание макроса как справочный.
- Версия шаблона повышена до 0.1.26.

## [0.1.16] - 2025-12-24
- Исправлена проблема импорта шаблона ("Template group already exists") путем сопоставления UUID группы `Templates/Applications`.
- Версии скрипта и шаблона повышены до 0.1.16.

## [0.1.15] - 2025-12-24
- Добавлен macro {$DNS_SHUFFLE} (по умолчанию 1) для управления перемешиванием списка резолверов в скрипте и шаблоне; ключи обновлены.
- Версии скрипта и шаблона повышены до 0.1.15; описание шаблона обновлено.
- Расширено описание {$DNS_RESOLVER}: пустое значение использует системный resolv.conf; рекомендован локальный рекурсор для DNSBL; упомянута связь с {$DNS_SHUFFLE}.

## [0.1.14] - 2025-12-24
- Добавлена ротация (shuffle) списка DNS-резолверов для распределения нагрузки между серверами.
- Обновлена версия скрипта.

## [0.1.13] - 2025-12-24
- DNSBL fallback: on POLICY/ERROR or CHECK FAILED, script retries other resolvers from {$DNS_RESOLVER} and accepts LISTED/NOT LISTED if any resolver responds normally.
- Warnings updated: advise using trusted/non-public resolvers; trigger description adjusted.
- Script version set to 0.1.13.

## [0.1.12] - 2025-12-24
- Fixed DNS slow trigger name to avoid double "ms" suffix (min 5m={ITEM.LASTVALUE1}).

## [0.1.11] - 2025-12-24
- Added trigger to detect non-JSON external script output (e.g., missing python3) with remediation steps.
- Template version bumped to 0.1.11.

## [0.1.10] - 2025-12-24
- Added repository link to template description (https://github.com/IT-for-Prof/zabbix-mail-dns-audit) and version 0.1.10 macro.

## [0.1.9] - 2025-12-24
- Master item mail.dns.audit now runs hourly (delay 1h) and stores history 1d to reduce load.
- Template version bumped to 0.1.9 (description and {$TEMPLATE_VERSION} macro).

## [0.1.8] - 2025-12-24
- Added explicit versioning: script VERSION meta field and template macro {$TEMPLATE_VERSION}=0.1.8.
- DNSBL test/self-reporting now includes script version in meta for downstream items.

## [0.1.7] - 2025-12-24
- DNSBL classification aligned with Spamhaus semantics: NXDOMAIN -> NOT LISTED; empty/NOANSWER/SERVFAIL/timeouts -> CHECK FAILED; 127.255.* policy codes -> POLICY/ERROR; listed codes unchanged.
- Added DNSBL policy/error and check-failed counters with dedicated triggers and improved DNSBL health calculation (now fails on policy/error/check failed).
- Added optional DNSBL self-test IP flag to external script for validating listed/not-listed handling.

## [0.1.6] - 2025-12-22
- Implemented Zabbix 7.0 Dashboard "Mail DNS Audit Overview" with Gauges and problem monitoring.
- Added numeric health metrics (DMARC score, SPF health, DNSBL health) for better visualization and indicator widgets.
- Established trigger dependencies to suppress noise during script execution failures.
- Ensured template dashboard compatibility with Zabbix 7.0 by using relative item references.

## [0.1.3] - 2025-12-22
- Improved DNSBL triggers informativeness: added TXT explanation/technical error to POLICY/ERROR and CHECK FAILED alerts via {ITEM.LASTVALUE2}.
- Script now includes technical error messages in the TXT field for CHECK FAILED status.

## [0.1.2] - 2025-12-22
- Added DNSBL A+TXT collection with normalized statuses (LISTED / POLICY/ERROR / CHECK FAILED / NOT LISTED) in mail.dns.audit.
- Extended template with per-IP DNSBL status and TXT items plus dedicated triggers for policy/error and check failure.

## [0.1.1] - 2025-12-22
- Fixed DNSBL trigger prototype to display the actual DNSBL zone name in alerts.

## [0.1.0] - 2025-12-21
- Added mail.dns.audit external Python check (DNS, SPF, DNSBL, DNSSEC).
- Added Zabbix 7 template Template Mail DNS Audit Zabbix7 with dependent items, LLD, triggers.
- Installed Python 3 + dnspython in zabbix-server container and deployed script.
- Created hosts for test domains with template applied.

