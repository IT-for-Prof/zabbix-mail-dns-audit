# Changelog
All notable changes to this project will be documented in this file.

## [0.1.52] - 2026-07-27

### Fixed
- "Record is missing" was still claimable from a run that never saw the record. With an unreachable resolver every lookup returns empty, so `mail.mx.count` reads 0 and `mail.dkim.present` reads 0 — two **HIGH** alerts per host asserting the domain had lost its MX and DKIM records. `meta.error` stays empty in that scenario, so the "DNS audit script error" dependency did not suppress them. Reproduced against a black-holed resolver: 16 failed lookups, both records reported absent. The script now counts failed lookups and both triggers require `mail.dns.lookup_failures=0` — absence is only asserted from a complete look. This is the PTR fix from 0.1.51 generalised to every check, without touching the 25 existing `query_records()` call sites.
- The "MX PTR FCrDNS failed" trigger fired on a single sample; it now requires two consecutive polls, matching the PTR-missing and DNSBL triggers.
- Removed a dead `noanswer` variable in the DNSBL branch (assigned in three places, read nowhere). The NODATA outcome it reached for already falls through to `CHECK FAILED`; that intent is now a comment instead of unused state.

### Added
- `meta.lookup_failures` and the `mail.dns.lookup_failures` item. `-1` means the running script predates the field — deliberately distinct from `0`, so the absence guards stay closed on an unmeasured run rather than opening.
- Trigger "DNS lookups failing — absence checks suppressed". Gating the absence triggers without announcing it would have made them go blind silently, which is the failure mode this whole release is about.

### Note for contributors
- The external check is named `mail.dns.audit` with no `.py` suffix, so a bare `ruff check .` walks the tree, lints only `tests/` and reports "All checks passed" having never opened the 1200-line script. Lint it explicitly — `ruff check externalscripts/mail.dns.audit` — or add `extend-include = ["externalscripts/mail.dns.audit"]` to a local ruff config. The dead variable fixed above was invisible to the bare command.

## [0.1.51] - 2026-07-27

### Fixed
- A transient DNS failure on the PTR lookup was reported as `status: "MISSING"` — i.e. as an authoritative "this domain has no PTR record" — and raised a HIGH page. `query_records()` collapsed four semantically distinct outcomes (`NXDOMAIN`, `NoAnswer`, `Timeout`, `NoNameservers`) into the same empty list, because its 3-tuple contract had no channel for *why* the result was empty; `check_ptr_fcrdns()` then read empty as MISSING, leaving its `ERROR` branch unreachable (output always showed `"missing":1,"errors":0`). Only NXDOMAIN/NoAnswer now mean MISSING; a failed lookup yields `ERROR` with the reason. Observed as 13 false HIGH alerts in 33 days on a domain whose PTR was present throughout, each one coinciding with a "DNS query slow" event — the signature of a query burning the full 3s `resolver.lifetime`.

- The forward A lookup inside `check_ptr_fcrdns()` had the same defect one line below the PTR one: a timeout there produced `NO_FCRDNS` — an assertion that the forward record disagrees with the PTR — feeding a trigger that carries no consecutive-poll filter at all. It now yields `ERROR` like the PTR leg.
- The error envelope skeleton introduced in 0.1.50 was incomplete: `ptr` and `dmarc` were missing, so on any fatal error every `$.ptr.*` and `$.dmarc.*` item with a default error handler went NOTSUPPORTED — including the new `mail.ptr.errors`, i.e. the visibility mechanism disappeared exactly when the script failed hardest. Both roots are now in the skeleton. The `lld_*` roots are deliberately still absent: a discovery rule fed `{"data": []}` asserts "nothing exists" and starts the 30d deletion clock on everything it discovered, whereas NOTSUPPORTED asserts nothing.

### Added
- `query_records_ex()` returns the failure reason alongside the records. `query_records()` is now a thin wrapper preserving the existing 3-tuple form, so all 25 existing call sites are untouched; the other checks (MX/SPF/DMARC/DKIM/NS/SOA) can adopt the tri-state later by switching to `_ex`.
- `tests/test_ptr_states.py` — first test in the repo. Asserts the exception→status mapping across all four DNS failure classes plus the OK/NO_FCRDNS/GENERIC paths, and pins the `query_records()` 3-tuple contract. No framework: `python3 tests/test_ptr_states.py`.
- Template: `mail.ptr.errors` item (`$.ptr.errors`), so a lookup failure stays visible instead of turning a loud false positive into a silent blind spot. The value was already computed by the script and never surfaced.
- `ptr.missing_details` / `ptr.nofcrdns_details` — the affected IPs, not just the count. With several MX records (3 of the 11 monitored domains have two) `count=1` does not say which address is broken. Zabbix expression macros cannot render text, so the trigger reads these via `{ITEM.LASTVALUE<n>}`, the same shape already used by the DNSBL details item. Empty renders as `*NONE*` rather than a blank, so a quiet trigger name is not mistaken for a broken template.

### Changed
- Template: the "MX PTR missing" trigger now requires two consecutive bad polls (`min(...,#2)>0`) and is AVERAGE rather than HIGH. Same noise filter already applied to the DNSBL trigger in 0.1.47, for the same reason; missing reverse DNS degrades deliverability but is not an outage. The estate's escalation-step filter cannot help here — it is time-based (5 min) while an hourly-polled item holds a false state for a full hour.

## [0.1.50] - 2026-06-12

### Fixed
- Error envelopes now emit the **full default result skeleton** (every key the dependent items read), not just `meta`. Previously a startup/deadline/fatal error left ~35 dependent items (those without a preprocessing error handler) flipping to NOTSUPPORTED on every poll. The default skeleton is now factored into a single `_default_result()` used by both the normal run and `_emit_error()`, so an error resolves all dependent JSONPaths (only `meta.error` is populated) while the "DNS audit script error" trigger still fires. (Follow-up to a code review of 0.1.49.)

### Changed
- Top-level guard re-raises `KeyboardInterrupt` (alongside `SystemExit`) so a manual Ctrl-C keeps conventional behaviour; only genuinely unexpected exceptions are converted to the JSON error envelope.
- Documented the relationship between `MAIL_DNS_DEADLINE_SEC` (default 25s) and the Zabbix external-check `Timeout` (default 30s) in the README.

## [0.1.49] - 2026-06-12

### Fixed
- A missing Python dependency (dnspython) no longer dumps a raw traceback that silently becomes a NOTSUPPORTED item with no useful alert. The `dns.*` imports are now guarded and emit a structured `{"meta":{"error":"missing Python dependency …"}}` envelope, so the **"DNS audit script error"** trigger fires immediately with a clear, actionable message. (Surfaced by a proxy where `python3-dnspython` was absent.)
- A stuck/unreachable resolver no longer lets the script run past the Zabbix external-check `Timeout` and get killed ("Timeout while executing a shell script"). A total-runtime **deadline** (default 25s, override via env `MAIL_DNS_DEADLINE_SEC`) now emits a clean `meta.error` instead. The SIGALRM handler emits the envelope and hard-exits, so it can't be swallowed by inner `except` blocks.
- Top-level guard around `main()`: any otherwise-uncaught exception (argument parsing, resolver construction) emits the JSON error envelope instead of a traceback. `_emit_error()` flushes stdout explicitly.

### Added
- `--selfcheck` flag — `mail.dns.audit --selfcheck` prints `selfcheck: OK version=… python=… dnspython=…` for post-deploy dependency verification.
- `requirements.txt` (`dnspython>=2.0`).
- Template: `mail.dns.error` JSONPath step now has a `CUSTOM_VALUE` error handler, so even a genuinely non-JSON script output (e.g. a traceback Zabbix captured) trips the "script error" trigger instead of going NOTSUPPORTED — and suppresses the misleading "version mismatch (running unknown)" warning via the existing trigger dependency.

## [0.1.48] - 2026-06-12

### Fixed
- DNSSEC `ad_flag` was structurally always `False`: the resolver never set the EDNS DO bit, so a validating recursive resolver never returned the AD (Authenticated Data) flag, and `query_records()` always read it as `0`. `build_resolver()` now calls `resolver.use_edns(0, dns.flags.DO, 4096)`. (Fixes #1, thanks @Salzi.)
- The configured DNS timeout (`{$DNS_TIMEOUT_SEC}`) was ignored on the system-config resolver path (empty `{$DNS_RESOLVER}`): `lifetime`/`timeout` were set only inside the custom-nameservers branch, so the default path silently used dnspython defaults (5s/2s). They are now applied on every code path. (Fixes #1, thanks @Salzi.)
- `dnssec.ad_flag` aggregation no longer misses DNSSEC-signed domains whose mail is hosted in an unsigned provider zone (e.g. Microsoft 365 / Proofpoint). It was OR-ed only from the MX hosts' A/AAAA lookups — which belong to the provider's zone — so a signed apex with an unsigned MX host (e.g. `nasa.gov`) read `False`. It now also incorporates the apex `MX` answer and the parent-signed `DS` answer.

## [0.1.47] - 2026-06-06

### Fixed
- DNSBL "check failed" aggregate trigger: problem name showed `*UNKNOWN*` because it used an expression macro `{?last(…mail.dnsbl.listed.details)}` on a TEXT item (Zabbix expression macros evaluate numerically and cannot render text). Now uses `{ITEM.LASTVALUE2}` with the details item present in the expression, and requires two consecutive failed polls (`min(…,#2)>0`) to suppress single transient resolver blips.
- "MX IP listed in DNSBL" trigger: Reason in the description showed `*UNKNOWN*` (same expression-macro-on-text issue) — now `{ITEM.LASTVALUE3}`.
- "DNS query slow" trigger name showed a doubled unit (`4409 msms`) — the item already carries `units: ms`, so the literal `ms` after `{ITEM.LASTVALUE}` was removed.
- Before→after ("было → стало") display on the SPF/MX/DKIM "record changed" and DMARC "downgraded" triggers was fully broken: it used `{?last(text)}` (→ `*UNKNOWN*`) and `{ITEM.PREVVALUE}` (unsupported in event names/operational data — rendered as the literal macro and dropped the before/after tags). Zabbix has no native way to show a previous text value there, so the script now supplies the prior value via its cross-run cache.

### Added
- Script emits a `prev` block (`spf`, `mx`, `dkim`, `dmarc`) carrying the previously seen values, namespaced in the cache (`__snapshot__|<domain>`) so it never collides with DNSBL entries.
- Four new dependent items — `mail.spf.record.prev`, `mail.mx.records.prev`, `mail.dkim.records.prev`, `mail.dmarc.policy.prev` — feed the before→after opdata/tags via the supported, text-capable `{ITEM.LASTVALUE}`. Change-trigger expressions place these display items first so the positional macros resolve unambiguously (Zabbix numbers `{ITEM.LASTVALUE<N>}` by function reference, not distinct item).

### Changed
- `save_cache()` now writes atomically (temp file + `os.replace`) so concurrent per-host external-check processes cannot corrupt the shared cache file.

## [0.1.46] - 2026-04-23

### Fixed
- SPF parser: RFC 7208 §4.6.1 compliance — mechanism identification now strips qualifier prefixes (`+`, `-`, `~`, `?`) before matching. Previously `+mx`, `+a`, `-include:...` etc. were silently ignored because `token.startswith("mx")` fails for `+mx`.
- SPF parser: `a` mechanism no longer incorrectly matches `all` — `token.startswith("a")` matched `"all"` since `"all".startswith("a")` is true, causing `all` to be treated as an `a` mechanism (extra DNS query, inflated lookup count). Now uses exact match: `bare == "a" or bare.startswith("a:") or bare.startswith("a/")`.
- SPF parser: `all` mechanism detection changed from `endswith("all")` to exact match `bare == "all"` after qualifier stripping — avoids false matches on unrelated tokens.

### Changed
- Default DNS resolver changed from `1.1.1.1` (Cloudflare) to `127.0.0.1` (localhost) — assumes a local recursive resolver (Unbound) is available on Zabbix server/proxy hosts.

## [0.1.45] - 2026-03-03

### Fixed
- DNSBL cache: errors (CHECK FAILED, POLICY/ERROR) were cached for full TTL (20 min), now expire after 120 seconds for quick retry
- DNSBL cache: switching DNS resolver no longer serves stale results from a previous resolver — resolver is now part of the cache key

## [0.1.44] - 2026-02-25

### Fixed
- DKIM records summary: show `rsa-unknown` instead of `rsa-0` when key size cannot be parsed

### Added
- Event tags `dmarc_before`/`dmarc_after` on "DMARC policy downgraded" trigger for API/webhook consistency
- Template `vendor:` block (`name: itforprof.com`) — author/vendor displayed in native Zabbix 7.0 template metadata; version removed from description text

## [0.1.43] - 2026-02-25

### Added
- Item: `mail.dkim.records` — stores DKIM records formatted as "selector:type-bits" (comma-separated); used for before/after display
- Trigger operational data (`opdata`) on "DKIM record changed": shows `old DKIM → new DKIM` in Problems list Info column
- Trigger operational data (`opdata`) on "DMARC policy downgraded": shows `old policy → none` in Problems list Info column
- Event tags `dkim_before`/`dkim_after` on DKIM changed trigger for API/webhook consumers

## [0.1.42] - 2026-02-25

### Added
- Item: `mail.spf.record` — stores the raw SPF TXT string; used to show before/after in trigger operational data
- Item: `mail.mx.records` — stores MX records formatted as "priority host" (comma-separated); used for before/after display
- Trigger operational data (`opdata`) on "SPF record changed": shows `old SPF → new SPF` in Problems list Info column
- Trigger operational data (`opdata`) on "MX records changed": shows `old MX → new MX` in Problems list Info column
- Event tags `spf_before`/`spf_after` and `mx_before`/`mx_after` on respective triggers for API/webhook consumers

## [0.1.41] - 2026-02-22

### Changed
- Trigger: "DNS audit script error" name now includes `{ITEM.LASTVALUE}` — shows the actual error message directly in the problem name; all 32 dependency references updated accordingly
- Trigger: "DMARC rua= malformed" name now includes `{ITEM.LASTVALUE2}` — shows the actual malformed rua= value
- Trigger: "DNS query slow" name now shows actual query time: `({ITEM.LASTVALUE}ms > {$DNS_SLOW_MS}ms)`
- Trigger prototype: "MX IP listed in DNSBL" description fixed — was using `{ITEM.LASTVALUE3}` (non-existent, 3rd item) for the reason; replaced with `{?last(...mail.mx.ip.listed.txt[{#MXIP}])}`
- Script version bumped to 0.1.41 to stay in sync with template

## [0.1.40] - 2026-02-22

### Changed
- Trigger: "DNSBL check failed" name now includes inline details via `{?last(...mail.dnsbl.listed.details)}` — shows affected IPs, zones, and failure reason directly in the problem name instead of just a count
- Trigger: "DNSBL check failed" description updated with common causes and remediation steps (public resolver blocked, local Unbound recommended)

## [0.1.39] - 2026-02-22

### Added
- Item: `mail.dkim.min_key_bits` — minimum RSA key size (bits) across all monitored DKIM selectors; 0 if no DKIM found or key unparseable
- Item: `mail.dkim.weak_key_count` — count of DKIM selectors with RSA key below 2048 bits
- Trigger: DKIM key too small (WARNING) — fires when min_key_bits > 0 and < 2048 and DKIM present; suppressed when HIGH trigger is active; depends on mail.dns.error
- Trigger: DKIM key critically weak (HIGH) — fires when min_key_bits > 0 and ≤ 1024 and DKIM present; depends on mail.dns.error
- Item: `mail.dmarc.adkim` — DKIM alignment mode from DMARC record (r=relaxed/default, s=strict); informational, no trigger (relaxed is RFC 7489 default)
- Item: `mail.dmarc.aspf` — SPF alignment mode from DMARC record (r=relaxed/default, s=strict); informational, no trigger
- Item: `mail.mx.cname_violation.count` — count of MX targets that resolve to a CNAME (RFC 5321 §5 violation)
- Trigger: MX target is a CNAME (WARNING) — fires when mx.cname_violation.count > 0; depends on mail.dns.error

### Changed
- Script and template version bumped to 0.1.39

## [0.1.38] - 2026-02-22

### Added
- Trigger: DMARC rua= not configured (INFO, opt-in via `{$CHECK_DMARC_RUA}=1`, default off) — fires when DMARC present but rua= absent; rua= is optional per RFC 7489 so check is disabled by default
- Trigger: DMARC rua= malformed (WARNING, always on) — fires when rua= is present but does not start with `mailto:` scheme; catches configuration mistakes
- Macro: `{$CHECK_DMARC_RUA}` (default 0) — set to 1 to enable the rua= absent alert

## [0.1.37] - 2026-02-22

### Removed
- Trigger: DMARC rua= missing — removed per RFC 7489: rua= is optional; absence is valid and should not alert

## [0.1.36] - 2026-02-22

### Fixed
- DNSBL check failed and DNSBL policy/error trigger names now include `{ITEM.LASTVALUE2}` showing the exact DNSBL response text
- Added 6 missing template macros: `{$CHECK_BIMI}`, `{$CHECK_DNSSEC}`, `{$CHECK_MTA_STS}`, `{$CHECK_TLS_RPT}`, `{$MAIL_CLIENT_AUTOCONFIG_CHECK}`, `{$SPF_CHECK_MX_COVERAGE}` — without these the skip macros never worked (always evaluated as empty string)
- Restored error dependency (`mail.dns.error`) to 15 triggers lost during previous import with `deleteMissing: true`
- Fixed `{$TEMPLATE_VERSION}` macro value in Zabbix (was stuck at 0.1.32, causing false version mismatch alerts)

## [0.1.35] - 2026-02-22

### Added
- Macro {$CHECK_DNSSEC} (default 1) — set to 0 on hosts without DNSSEC to suppress AD flag and DS record alerts
- Macro {$CHECK_MTA_STS} (default 1) — set to 0 on hosts without MTA-STS to suppress MTA-STS missing alert
- Macro {$CHECK_TLS_RPT} (default 1) — set to 0 on hosts without TLS-RPT to suppress TLS-RPT missing alert
- Macro {$CHECK_BIMI} (default 1) — set to 0 on hosts without BIMI to suppress BIMI missing alert

## [0.1.34] - 2026-02-22

### Fixed
- DMARC rua= trigger now correctly fires when rua is JSON null (value "null") — previously length()=0 check missed null values
- SPF mx_covered now detects a:hostname mechanisms that directly name an MX host — prevents false-positive "MX not authorized in SPF" alert when a:mail.example.com is used instead of mx mechanism
- Script VERSION bumped to match template version (was left at 0.1.32 in 0.1.33 release)

## [0.1.33] - 2026-02-22

### Added
- Trigger: MX count = 0 (HIGH) — domain cannot receive mail
- Trigger: SPF lookup estimate exceeds RFC 7208 limit of 10 (AVERAGE)
- Trigger: Multiple SPF TXT records detected — RFC violation (AVERAGE)
- Trigger: SPF record changed — hash-based change detection (WARNING)
- Trigger: MX records changed — hash-based change detection (WARNING)
- Trigger: DKIM record changed — hash-based change detection (WARNING)
- Trigger: DMARC rua= missing — no aggregate reports configured (WARNING)
- Trigger: DNSBL check failure — query timeout or error (WARNING)
- Macro: {$MAIL_CLIENT_AUTOCONFIG_CHECK} — set to 0 to skip autoconfig/autodiscover alerts on servers without mail client autoconfiguration

### Fixed
- Added mail.dns.error dependency to all triggers that lacked it (DKIM, DMARC, MTA-STS, TLS-RPT, BIMI, DNSSEC, NS, PTR, SPF) — prevents false alert spam on script errors
- NS mismatch trigger now attached to mail.ns.serial_mismatch.count item — {ITEM.LASTVALUE} now shows actual mismatch count instead of 0
- DMARC policy triggers now require mail.dmarc.present=1 — prevents false positive when DMARC record absent
- mail.dmarc.rua item now has error_handler — prevents unsupported state when DMARC absent
- Script version mismatch trigger now suppressed when script errors
- Added HIGH nodata trigger (no data for 3h) to detect when script stops running

## [0.1.32] - 2026-02-20

### Added
- New dependent item `mail.script.version` (TEXT): extracts `$.meta.version` from the master item JSON, showing which script version produced the last result.
- New WARNING trigger: fires when `mail.script.version` does not match `{$TEMPLATE_VERSION}`, making outdated scripts on proxies immediately visible in problems.

## [0.1.31] - 2026-02-20

### Fixed
- Script shebang changed from `#!/usr/bin/env python3` to `#!/usr/bin/python3` — Zabbix runs external scripts with a minimal environment (no PATH), causing `env` to fail to locate the interpreter.
- Added `.gitattributes` to enforce LF line endings for `externalscripts/mail.dns.audit` and `*.py` — CRLF from Windows would corrupt the shebang with a trailing `\r`, making the interpreter path invalid on Linux.

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

