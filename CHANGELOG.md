# Changelog
All notable changes to this project will be documented in this file.

## [0.1.59] - 2026-07-28

### Fixed
- **Проверка совпадения версий требует два опроса подряд.** Она была одиночной выборкой и поднимала предупреждение на всех восьми хостах при каждом обновлении: макрос шаблона меняется в момент импорта, а элемент узнаёт новую версию скрипта только на следующем опросе, и между этими двумя моментами несовпадение истинно по-настоящему.

  **Оговорка, которую честнее записать, чем умолчать.** Требование повторности сужает окно, но не закрывает его: если к моменту импорта элемент успел дважды получить старую версию, условие выполнится и предупреждение всё равно появится. Полностью убрать это выборкой по числу опросов нельзя — сравниваются две величины, меняющиеся в разное время. Предупреждение самостоятельно гаснет на следующем опросе и во время обновления говорит правду, поэтому дальше я его не усложнял. Порядок раскатки уменьшает шум: сначала скрипт на все машины, потом импорт шаблона.

### Note
Тот же урок про повторность встретился за день трижды: у триггера молчащего нейм-сервера, у самотеста DNSBL (там `#2` уже стоял, но принудительный сбор, запущенный дважды подряд, делает два «последовательных» опроса с интервалом в секунды и обесценивает защиту) и здесь. Сейчас повторности требуют 10 триггеров из 60.

## [0.1.58] - 2026-07-28

### Fixed
- **Триггер «нейм-серверы не отвечают SOA» требует два опроса подряд.** Он был написан как `last(...)>0` — единственный в шаблоне среди чувствительных к транзиентам, где у всех остальных стоит `#2`. На первый же день работы он сработал на одиночном пропущенном SOA у `misterlogistic.com`, а прямая проверка тут же показала, что все четыре сервера отвечают. Один непрошедший запрос — обычный шум; два подряд — находка. Тот же урок, что породил `#2` у триггеров PTR и DNSBL.

### Note
При проверке правок резолвера выяснилось, что принудительный сбор (`check-now`), запущенный дважды подряд, делает два «последовательных» опроса с интервалом в секунды и тем обесценивает защиту `#2`: при штатном часовом опросе это были бы два разных часа. Три сработавших самотеста DNSBL оказались именно таким артефактом проверки, а не состоянием зон — обе зоны отвечают канареечным адресом 127.0.0.2 корректно.

## [0.1.57] - 2026-07-28

### Changed
- **Скрипт исполняется в отдельном окружении Python по пути `/opt/zabbix-mail-dns/venv`.** Шебанг указывает на него, системный интерпретатор больше не используется. Причина конкретная: на одном из пяти прокси системным остаётся Python 3.6.8, где нет `ipaddress.subnet_of()`, а на остальных — от 3.11 до 3.12, и версии dnspython расходились от 2.2.1 до 2.6.1. Теперь везде Python 3.11+ и dnspython 2.8.0, скрипт байт-в-байт одинаков, поведение воспроизводимо. Подпорка под 3.6 в коде оставлена: если окружение отсутствует, проверку запустят системным интерпретатором, и падать она при этом не должна.
- **Блок `--simulate` перестроен поверх `_default_result()`.** Рукописная копия разошлась со схемой на 54 ключа и вводила в заблуждение каждого, кто ею проверял шаблон. Теперь переопределяются только демонстрируемые поля, а разойтись со схемой она не может по построению.

### Docs
- Установка переписана под окружение Python; три раздела устранения неполадок — `externally-managed-environment` (PEP 668), отсутствие Python 3 и отсутствие dnspython — свёрнуты в один, потому что у всех трёх теперь один и тот же ответ.
- Из обоих README удалён дубль истории изменений: 36 строк, устаревших на четыре версии, повторявшихся на двух языках. Осталась ссылка на CHANGELOG.
- В список возможностей добавлено то, что появилось за 0.1.53–0.1.56 и там не значилось: дубликаты записей, null MX, отозванный ключ и тестовый режим DKIM, молчащие нейм-серверы, пооперационные признаки видимости, обнаружение по каждому адресу и селектору, видимость непокрытых чёрными списками адресов.
- Задокументированы макросы `{$MAIL_DNS_NODATA_SEC}`, `{$DNSBL_MAX_IP}` и `{$CIDR_ALLOWLIST}` — в том числе то, что PTR проверяется у каждого адреса независимо от лимита чёрных списков.
- `requirements.txt` описывает установку в окружение, а не в системный Python.

## [0.1.56] - 2026-07-28

Правки по итогам ревью пятью независимыми рецензентами. Семь находок подтверждены двумя и более рецензентами независимо; все семь внесены в 0.1.53–0.1.55, то есть это исправление собственных ошибок, а не унаследованных.

### Fixed
- **Защита проверок отсутствия ослепляла весь шаблон.** `_LOOKUP_FAILURES` — один счётчик на процесс, и в него попадали провалы `check_ns_sync`, которая опрашивает авторитативные серверы **напрямую**. Комментарий, написанный в 0.1.53 рядом с этим кодом, сам же и указывал, что такой трафик межсетевой экран может резать на каждом прогоне. Достаточно одного постоянно молчащего сервера — и все 15 проверок отсутствия подавлены навсегда, включая **HIGH** «нет MX-записей», а добавленное в 0.1.55 нарастание вырождается в никогда не гаснущий HIGH, который оператор заглушит. Воспроизведено рецензентом на живом домене: `check_ns_sync("eurotrade-group.ru")` даёт `unanswered=1` и `_LOOKUP_FAILURES=1` одновременно.

  Исправлено по существу, а не заплаткой. Во-первых, опрос авторитативных серверов больше не питает общий счётчик — свою видимость он выражает через `unanswered`. Во-вторых, введены **пооперационные признаки видимости**: восемь флагов `seen.{mx,spf,dkim,ds,dmarc,transport,bimi,autoconfig}`, и каждая проверка отсутствия смотрит только на свой раздел. Показано подстроенным сбоем: обрыв запросов DKIM даёт `seen.dkim=false` при семи остальных `true`, то есть подавляется одна проверка вместо пятнадцати.
- **`ipaddress.subnet_of()` требует Python 3.7, а на `mon.itforprof.com` стоит 3.6.8.** `AttributeError` не ловится веткой `except ValueError`, и весь прогон схлопывался бы в аварийный конверт. Код был мёртв, пока `{$CIDR_ALLOWLIST}` пуст, — но триггер, дающий оператору повод его заполнить, добавлен в этом же цикле работ. Заменено на явное сравнение границ сети; проверено прямо на боевой машине с Python 3.6.8, где `subnet_of` действительно отсутствует.
- **Триггер «серверы не отвечают SOA» не мог сработать по своему назначению.** Таймаут, поднимающий `unanswered>0`, одновременно поднимал `lookup_failures>0`, а триггер был закрыт защитой `lookup_failures=0`. Он срабатывал бы только на опечатке в делегировании, но никогда — на мёртвом сервере. Защита снята: `unanswered>0` есть положительное наблюдение, а не утверждение об отсутствии, и предусловия полноты не требует.
- **`lld_mx_ip` был привязан не к тому запросу**: к апексному MX, а наполняется адресами MX-хостов. Ответ MX при провале A-запросов давал пустой `data` и запускал часы удаления на всех per-IP элементах — ровно то, что запрещает докстрока собственной функции.
- **Слияние кэша шло в обратную сторону.** `merged.update(data)` накладывал весь снимок начала прогона, откатывая записи, сделанные другими хостами за это время. Теперь применяются только ключи, изменённые этим прогоном.
- **Запись кэша шла после снятия дедлайна и до вывода.** Повторное чтение и перезапись разделяемого файла в окне без защиты возвращали отказ «поллер убил процесс, вывода нет». Порядок изменён: сначала вывод и сброс буфера, затем кэш. Вывод — обязательство, кэш — оптимизация.
- **`*NONE*` вместо `*UNKNOWN*` для NS и DS.** Скрипт опускал ключ при неудачном запросе, а `error_handler_params: '[]'` в шаблоне превращал это в «делегирования нет» — неотличимо от подтверждённо пустого ответа.
- **Булев флаг DNSBL по каждому адресу врал дважды.** `error_handler: DISCARD_VALUE` **отбрасывал** значение, когда адреса нет в списке, поэтому исключённый из чёрного списка адрес оставался единицей навсегда и триггер не гас. Плюс адрес за пределами `{$DNSBL_MAX_IP}` был неотличим от чистого. Предобработка переписана: 1 в списке, 0 проверен и чист, 2 не проверялся. Все четыре случая, включая исключение из списка, проверены.
- **Битые механизмы `ip4:`/`ip6:` больше не подменяют собой нарушение allowlist.** В 0.1.55 они либо поднимали алерт «сети вне списка» на хостах без списка, либо отбрасывались вовсе, унося единственное обнаружение. Теперь у них свой счётчик и свой триггер.
- **`ptr.not_checked` удалён как мёртвый.** После отвязки PTR от лимита в 0.1.55 статус `NOT_CHECKED` перестал появляться, поле стало тождественно нулём, а три описания в шаблоне продолжали обещать поведение, которого код не производит. Непокрытие осталось только у чёрных списков и считается в `dnsbl.not_checked`.

### Added
- Тесты выросли с 49 до 73 проверок. Каждая находка ревью превращена в проверку: подстановка `subnet_of` против штатной реализации, разделение битых механизмов и нарушений allowlist, сохранность чужих записей в кэше, полнота признаков видимости. Формула покрытия PTR вынесена в `count_ptr_checked()`, чтобы тест **вызывал** рабочий код, а не переписывал его — на это указали три рецензента.
- Страж против вакуумного прохода в проверках шаблона: если эталонный вывод устареет, проверка приведения булевых полей нашла бы ноль полей и молча прошла. Теперь она требует не менее пяти и печатает команду пересоздания эталона.

### Note
Ни одна из семи находок не была бы поймана тестами: тесты проверяли то, что автор уже понял. Их нашли независимые рецензенты, читавшие код без авторских допущений, — и только после этого каждая стала проверкой.

## [0.1.55] - 2026-07-28

Исправление подхода, а не отдельных мест. В 0.1.54 знание RFC было применено для понижения серьёзности и сокращения охвата — для мониторинга работоспособности это неверно. RFC уточняет **формат и причину**, но не решает, о чём молчать.

### Fixed
- **Null MX снова HIGH.** В 0.1.54 запись `MX 0 .` понижала алерт до INFO со ссылкой на RFC 7505. Для домена, наблюдаемого как почтовый сервер, это отказ: каждый отправитель в интернете получает окончательный отказ в приёме почты. Знание RFC осталось, но работает на точность формулировки — вместо невнятного «No MX records found» событие называет причину прямо. Если домен действительно не должен принимать почту, его следует снять с шаблона, а не понижать серьёзность.
- **PTR и FCrDNS отвязаны от `{$DNSBL_MAX_IP}`.** Лимит вводился ради квот публичных чёрных списков, но глушил и обратный DNS, у которого никаких внешних квот нет: адреса сверх пятого не проверялись вовсе. Теперь PTR проверяется у **каждого** адреса, а лимит ограничивает только обращения к спискам. На домене с 15 адресами покрытие выросло с 5 до 15. Цена — около двух запросов на дополнительный адрес: холодный прогон 3.3 с, тёплый 0.9 с при дедлайне 25 с.

### Added
- **`mail.dnsbl.not_checked` и триггер к нему** (WARNING). Адреса, оставшиеся за пределами квоты, теперь видны: их PTR проверен, но утверждать «не в чёрных списках» про них нельзя. Молчание о непроверенном — не то же самое, что чистый результат, и оператор должен видеть разницу.
- **Нарастание при длительной слепоте** (HIGH). Защита проверок отсутствия от ложных срабатываний нужна — без неё в 0.1.51 пришли 13 ложных HIGH. Но четыре опроса подряд с потерянными запросами означают, что четыре часа никто не подтверждает наличие MX, DKIM, SPF, DMARC и DNSSEC, а тишина при этом читается как здоровье. Устойчивая невозможность проверить почтовый домен — сам по себе отказ мониторинга, и теперь он звучит.

## [0.1.54] - 2026-07-28

Правки по результатам замеров на боевой истории и проверки по RFC, которых не было.

### Fixed
- **Пятнадцать проверок отсутствия защищены `lookup_failures=0`.** Раньше защита стояла на пяти, а десять триггеров — MTA-STS, TLS-RPT, BIMI, DNSSEC DS и AD, autoconfig, autodiscover, покрытие MX в SPF — утверждали «записи нет» на прогоне, который эту запись не мог увидеть. Замер по истории: **5.1% прогонов теряют хотя бы один запрос**, до 17.6% на отдельных доменах (saab-cos.ru), при нуле на доменах, обслуживаемых другим регистратором. Сбои кучкуются во времени — две машины в пределах минуты, три за одиннадцать, — то есть отказ общий, и это ровно та форма, в которой в 0.1.51 пришли 13 ложных HIGH за 33 дня. Совпадений «прогон с потерями И проверка прочитана как ноль» пока ноль, но экспозиция была 5%, а не 0.
- **Null MX больше не выдаётся за отсутствие MX** (RFC 7505 §3). Домен с единственной записью `MX 0 .` заявляет, что почту не принимает; скрипт молча отбрасывал её, счётчик MX уходил в ноль и поднимался **HIGH** «No MX records found» на осознанное и корректное решение. Воспроизведено на `example.com`. Добавлен элемент `mail.mx.null`, триггер отсутствия MX получил защиту от него, а сам факт отдаётся как INFO.
- **`meta.resolver_used` перестал быть пустым.** Он отдавал *запрошенный* резолвер, а `{$DNS_RESOLVER}` пуст на всех восьми хостах — значит используется системный, и элемент, заведённый ради диагностики, не показывал ничего. Теперь отдаёт фактический список серверов резолвера.

### Added
- **Счётчик нейм-серверов, не ответивших SOA** (`mail.ns.unanswered`, WARNING). Слепое пятно найдено на живом хосте: у `eurotrade-group.ru` сервер `ns4.timeweb.org` не отвечает SOA, а агрегат показывает `consistent=1`, `mismatch=0`. Причина в том, что серийники собираются только из успешных ответов, поэтому молчащий участник делегирования не попадает в расхождение **никогда** — увидеть его можно было только в per-NS элементе. Теперь он считается отдельно.
- **Отозванный ключ DKIM** (`mail.dkim.revoked.count`, **HIGH**). По RFC 6376 §3.6.1 пустое значение `p=` означает отзыв ключа. Запись при этом остаётся опубликованной, поэтому триггер отсутствия DKIM молчит, а получатели отвергают каждую подпись. Отсутствие тега `p` — это сломанная запись, а не отзыв; два состояния теперь различаются.
- **Тестовый режим DKIM** (`mail.dkim.testing.count`, WARNING). По RFC 6376 §3.6.1 при `t=y` получатели обязаны обращаться с сообщениями как с неподписанными даже при неуспешной проверке подписи — то есть ключ может быть безупречен, а защиты нет. Разбирается список флагов через двоеточие (`t=y:s`), как требует ABNF.

### Note on measurement
Первая оценка частоты потерь дала 0.2% и была неверна в 26 раз: знаменатель брался из истории `query_time_ms` за 31 день, тогда как счётчик `lookup_failures` существует со вчерашнего дня. Отдельно `DISCARD_UNCHANGED` превращает историю в ступенчатую функцию — 17 значений за месяц это 17 изменений, а не 17 прогонов, и наивный подсчёт ошибся бы ещё в сорок раз. Знаменатель обязан совпадать с покрытием данных, а элементы с отбрасыванием неизменного нужно разворачивать.

## [0.1.53] - 2026-07-27

Первая из двух волн восстановления покрытия. Возвращает проверки, молча потерявшие потребителя, и достраивает целостность триггерной сети. Новых сетевых запросов не добавляет.

### Fixed
- **Проверки на дубликаты записей вернулись в шаблон.** Скрипт считал дубликаты MX, DMARC, DKIM-селекторов, NS и SOA с версии 0.1.18, но семь элементов `mail.dup.*` и три триггера исчезли из шаблона в 0.1.19 — в коммите, который по описанию и записи в CHANGELOG только добавлял PTR-проверки, а на деле удалил 1531 строку. Ни в CHANGELOG, ни в описании коммита об этом не было ни слова. Семь месяцев блок `duplicates` считался, тратил DNS-запросы, попадал в master item и никуда не приходил. Восстановление идёт по ключам, именам и смыслу; исходные UUID из 0.1.18 сохранить не удалось — Zabbix при импорте требует UUIDv4, а те были записаны вручную и этому формату не отвечают.
- **Аварийный конверт перестал занижать два поля.** На пути дедлайна `meta.query_time_ms` и `meta.lookup_failures` всегда были нулями: прогон, упёршийся в 25-секундный дедлайн, отдавал «0 мс» — то есть единственный случай, когда DNS был заведомо медленным, выглядел мгновенным. График времени ответа рисовал ноль вместо пика, триггер медленного DNS не срабатывал никогда, а триггер подавления проверок на отсутствие не видел упавших запросов. Воспроизведено на резолвере-чёрной дыре: прошло 3088 мс, отдано 0.
- **Аварийный конверт стал по-настоящему полным.** С 0.1.50 он обещал резолвить все зависимые JSONPath, но `spf_analysis` и `snapshots` в нём были пустыми словарями, и 20 элементов всё равно уходили в NOTSUPPORTED. Форма `spf_analysis` теперь вынесена в общую функцию с `parse_spf()`, поэтому разойтись они больше не могут. Проверено: из 87 путей шаблона конверт резолвит 82, оставшиеся пять — намеренно опущенные корни `lld_*`.
- **Четыре триггера получили недостающую зависимость от «DNS audit script error»**: «DNS query slow» и три прототипа DNSBL по каждому IP. Теперь 51 триггер из 53 молчит во время аварии скрипта; без зависимости остались ровно те два, которым она противопоказана, — сам триггер ошибки и nodata.

### Added
- **Смена NS- и DS-записей отслеживается** в той же идиоме «было → стало», что SPF, MX, DKIM и DMARC: блок `prev` расширен с четырёх ключей до шести.
- **Состояние `NOT_CHECKED` для обнаруженных, но не проверенных адресов.** Обнаружение видит все IP, а проверяются только первые `{$DNSBL_MAX_IP}`; раньше остальные элементы оставались пустыми навсегда и были неотличимы от отсутствующей PTR-записи. Добавлены `ptr.not_checked` и `ptr.discovered`, а `ptr.checked` больше не считает неосмотренные адреса — «0 из 5» не должно включать те, на которые не смотрели.
- **Корни обнаружения `lld_dkim_selector` и `lld_ns`.** Прогон, потерявший хоть один запрос, их не публикует вовсе: пустой `data` запускает у Zabbix отсчёт удаления всего обнаруженного, и транзиентный таймаут не должен получать право на такое утверждение. То же правило, по которому `lld_*` отсутствуют в аварийном конверте.
- Элементы `mail.dup.ns.details` и триггеры на дубликаты DMARC (**HIGH**) и SOA (**WARNING**) — раньше у этих двух были только флаги без алертов. Две DMARC-записи по RFC 7489 заставляют получателя игнорировать политику целиком, включая `p=reject`.
- Макрос `{$MAIL_DNS_NODATA_SEC}` вернулся, но со значением `3h`, а не с историческими 1800 секундами: интервал опроса был часовым уже в 0.1.18, поэтому получасовое окно истинно половину каждого часа и триггер флапал бы постоянно. В описании зафиксирована нижняя граница Zabbix в 30 секунд и причина, по которой `nodata()` намеренно вызывается без параметра `strict` — проверка исполняется на прокси.
- **Триггеры на смену NS и DS.** Раньше у этих двух записей был только хеш, а хеш в имени триггера не покажешь; теперь скрипт отдаёт списки `ns` и `ds`, и событие называет прежнее и новое значение, как это давно делают SPF, MX, DKIM и DMARC. Триггер DS закрыт макросом `{$CHECK_DNSSEC}`.
- **Триггер на механизм `ptr` в SPF** (INFO, RFC 7208 §5.5) и **на сети вне `{$CIDR_ALLOWLIST}`** (WARNING). Оба элемента существовали и наполнялись, реагировать на них было некому — а `{$CIDR_ALLOWLIST}` без этого триггера вообще ни на что не влиял.
- **Триггер на неразрешимые механизмы `a:` в SPF.** Для `mx:` он был всегда, для `a:` — никогда, хотя симптом и последствия те же.
- **Прототипы PTR по каждому адресу** на существующей оси `mail.mx.ip.discovery`: статус и имя из обратной зоны, плюс триггеры отсутствия PTR и провала FCrDNS с именем адреса в событии. Это снимает надобность в обходном пути через `{ITEM.LASTVALUE<n>}` для новых алертов.
- **Прототип CNAME по каждому MX-хосту**: агрегатный счётчик нарушений RFC 5321 §5.1 был, имя виновного хоста — нет.
- **Два правила обнаружения**: DKIM-селекторы и авторитативные NS. У NS намеренно только элементы без триггеров — агрегатный триггер рассинхрона уже есть, а anycast-узлы легитимно отдают разные серийники.
- **Диагностические элементы**: использованный резолвер, обнаружено/проверено/не проверено адресов, детализация провалов FCrDNS.
- `tests/test_wave1_contracts.py` — детерминированные проверки того, что сетевым прогоном не воспроизвести: различие `[]` и `None` в корнях обнаружения, реальные значения в аварийном конверте, знаменатель покрытия PTR, шесть ключей в `prev`.

### Changed
- `{$DNSBL_MAX_IP}` поднят с 1 до 5. Замер на 35 почтовых доменах: при лимите 1 проверялось 27% обнаруженных адресов и 17% доменов целиком, при 5 — 82% и 86%. Стоимость линейна, примерно +5 DNS-запросов на адрес. При лимите 1 три четверти per-IP элементов не получали данных никогда.
- Кэш переехал в `/tmp/mail_dns_audit_cache.<uid>.json`. Каталог `/tmp` со sticky-битом: файл, оставленный прогоном от root, пользователь `zabbix` заменить уже не может, `os.replace` падает с EPERM, `save_cache` эту ошибку проглатывает — и кэш DNSBL становится инертным, а все значения `prev.*` замерзают навсегда без единого признака. Отдельные файлы по пользователям делают такое столкновение невозможным, а не просто маловероятным. Одноразовая цена — первый прогон после обновления с пустым `prev`.
- `save_cache()` перечитывает файл перед записью и накладывает свои ключи на свежий снимок. Атомарность записи сама по себе не спасала от потери обновлений: файл загружается в начале прогона, а записывается через секунды, и запись целиком затирала всё, что за это время добавили процессы других хостов.

### Fixed по результатам ревью

Ревью нашло в этой же волне четыре дефекта, каждый из которых пережил бы импорт молча.

- **Два JavaScript-тела не компилировались.** Прототипы `mail.dkim.key_bits[{#DKIM_SELECTOR}]` и `mail.ns.serial[{#NSHOST}]` были записаны в YAML-скаляре в одинарных кавычках с последовательностью `\n`, а такой скаляр escape-последовательности не разбирает — в JS попадал настоящий обратный слэш, и скрипт не компилировался. Zabbix не компилирует предобработку при импорте, поэтому импорт бы прошёл, а оба новых правила обнаружения не дали бы ни одного значения. Теперь есть `tests/test_template_contracts.py`, который прогоняет все 44 JS-шага через `node`.
- **`min()` на текстовом элементе.** Прототипы триггеров PTR использовали `min(...,#2)="MISSING"`, а `min()` принимает только Float и Integer. Заменено на `count(...,#2,"eq","MISSING")=2`; `"eq"` обязателен, потому что для строк оператор по умолчанию — `like`. Тест проверяет весь шаблон на числовые функции поверх текстовых элементов.
- **Правило «пустой `data` — это утверждение» применялось к двум корням из пяти.** `lld_mx`, `lld_mx_ip` и `lld_dnsbl_zones` публиковались всегда, поэтому SERVFAIL на запросе MX отдавал `{"data": []}` и запускал часы удаления на все MX-хосты, все адреса и все новые per-IP элементы — молча, потому что триггер отсутствия MX сам подавлен guard'ом `lookup_failures=0`. Теперь правило одно для всех: корень, зависящий от DNS, при неудачном запросе опускается. `lld_dnsbl_zones` — единственное исключение, и оно обосновано: его содержимое приходит из макроса, а не из DNS.
- **Публикация корней зависела от общего счётчика сбоев.** `check_ns_sync` опрашивает авторитативные серверы напрямую — трафик, который межсетевой экран может резать на каждом прогоне. Тогда счётчик никогда не равен нулю и оба новых корня не публикуются никогда. Каждый корень теперь привязан к тому запросу, который его и устанавливает.
- **DNSBL-статус объявлял «не в списке» для адресов, к которым запрос не отправлялся.** Прототип возвращал `NOT LISTED`, если записей по адресу нет, — а их нет и у адреса за пределами `{$DNSBL_MAX_IP}`, и у IPv6. Второй по приоритету MX мог висеть в чёрном списке и показывать зелёное. Теперь адрес, которого нет в `dnsbl.checked_ips`, получает `NOT_CHECKED`.
- **Триггер на сети вне allowlist срабатывал при пустом allowlist.** Ветка разбора нераспознанного `ip4:`/`ip6:` не соблюдала выключатель, который соблюдает ветка сравнения, — и алерт с текстом «сети вне списка» поднимался на хосте, где список не настроен, называя при этом не ту причину.
- **`ns` и `ds` отдавались пустым списком при неудачном запросе**, то есть нарушали ровно то правило, которое эта же волна вводит тремя строками выше. Теперь при неудаче ключ опускается, а элемент показывает `*UNKNOWN*` вместо `*NONE*`.
- **Обнаружение размножало дубли.** Селектор, опубликованный дважды, давал две строки с одним ключом элемента — и именно тогда, когда оператор пришёл разбираться с дублями.
- **IPv6-адреса тратили бюджет проверок**, хотя тут же пропускались: при `{$CHECK_IPV6}=1` половина слотов уходила впустую, а тройка «обнаружено / проверено / не проверено» переставала сходиться.

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

