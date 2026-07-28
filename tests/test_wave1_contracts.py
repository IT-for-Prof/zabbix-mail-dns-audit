#!/usr/bin/env python3
"""Контракты, добавленные первой волной восстановления покрытия (v0.1.53).

Запуск:  python3 tests/test_wave1_contracts.py

Проверяется то, что нельзя воспроизвести сетевым прогоном детерминированно:

1. build_lld() различает «посмотрели, ничего нет» ([]) и «не смогли узнать» (None).
   Пустой data запускает у Zabbix отсчёт удаления всего ранее обнаруженного, и
   транзиентный таймаут не должен получать право на такое утверждение. Это то же
   правило, по которому корни lld_* отсутствуют в аварийном конверте.
2. Аварийный конверт несёт реальное время работы и реальное число сбоев. Раньше
   оба поля были нулями, из-за чего прогон, упёршийся в дедлайн, выглядел как
   мгновенный и не поднимал ни триггер медленного DNS, ни триггер подавления
   проверок на отсутствие.
3. ptr.checked считает только фактически осмотренные адреса. NOT_CHECKED и
   SKIP_IPV6 существуют ради того, чтобы у per-IP элементов было значение, но в
   знаменатель покрытия они попадать не должны.
4. Блок prev содержит шесть ключей: NS и DS восстановлены в той же идиоме
   «было -> стало», что и SPF, MX, DKIM, DMARC.

Фреймворка нет намеренно — как и в test_ptr_states.py.
"""

import importlib.machinery
import importlib.util
import io
import json
import pathlib
import sys
import contextlib

SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "externalscripts" / "mail.dns.audit"

_loader = importlib.machinery.SourceFileLoader("mail_dns_audit", str(SCRIPT))
_spec = importlib.util.spec_from_loader("mail_dns_audit", _loader)
mod = importlib.util.module_from_spec(_spec)
_loader.exec_module(mod)

_failures = []


def check(label, condition, detail=""):
    if condition:
        print("  ok   {}".format(label))
    else:
        print("  FAIL {} {}".format(label, detail))
        _failures.append(label)


def main():
    print("build_lld(): [] и None означают разное")
    seen = mod.build_lld([], [], ["zone.example"], dkim_data=[], ns_data=[])
    check("пустой список -> корень есть и пуст",
          seen.get("lld_dkim_selector") == {"data": []}
          and seen.get("lld_ns") == {"data": []},
          seen)

    blind = mod.build_lld([], [], ["zone.example"], dkim_data=None, ns_data=None)
    check("None -> корня нет вовсе",
          "lld_dkim_selector" not in blind and "lld_ns" not in blind,
          sorted(blind))
    check("прежние корни не задеты",
          {"lld_mx", "lld_mx_ip", "lld_dnsbl_zones"} <= set(blind),
          sorted(blind))

    filled = mod.build_lld(
        [{"host": "mx.example", "prio": 10}],
        [{"mx_host": "mx.example", "ip": "192.0.2.1", "proto": "A"}],
        [],
        dkim_data=[{"selector": "s1"}, {"selector": "s2"}],
        ns_data=[{"ns": "ns1.example"}, {"ns": None}],
    )
    check("селекторы попадают в макросы",
          [d["{#DKIM_SELECTOR}"] for d in filled["lld_dkim_selector"]["data"]] == ["s1", "s2"])
    check("NS без имени отбрасывается",
          [d["{#NSHOST}"] for d in filled["lld_ns"]["data"]] == ["ns1.example"])

    print("аварийный конверт несёт реальные значения")
    mod._START = mod.time.time() - 4.2          # как если бы прогон шёл 4.2 секунды
    mod._LOOKUP_FAILURES = 7
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        mod._emit_error("deadline", resolver_used="192.0.2.1")
    env = json.loads(buf.getvalue())
    check("query_time_ms — реальное время, не ноль",
          4000 <= env["meta"]["query_time_ms"] <= 6000, env["meta"]["query_time_ms"])
    check("lookup_failures — реальный счётчик, не ноль",
          env["meta"]["lookup_failures"] == 7, env["meta"]["lookup_failures"])
    check("схема конверта полная, корни lld_* отсутствуют",
          "duplicates" in env and not [k for k in env if k.startswith("lld_")],
          sorted(k for k in env if k.startswith("lld_")))

    print("все пять корней подчиняются одному правилу")
    everything = mod.build_lld([], [], ["z"], dkim_data=[], ns_data=[])
    check("список -> все пять корней есть",
          {"lld_mx", "lld_mx_ip", "lld_dnsbl_zones", "lld_dkim_selector", "lld_ns"} == set(everything),
          sorted(everything))
    nothing = mod.build_lld(None, None, ["z"], dkim_data=None, ns_data=None)
    check("None -> остаётся только корень из макроса, а не пустые data",
          set(nothing) == {"lld_dnsbl_zones"}, sorted(nothing))

    print("обнаружение не размножает дубли")
    dup = mod.build_lld(
        None, None, [],
        dkim_data=[{"selector": "s1"}, {"selector": "s1"}, {"selector": "s2"}],
        ns_data=[{"ns": "a.example"}, {"ns": "a.example"}, {"ns": None}],
    )
    check("повторный селектор даёт одну строку",
          [d["{#DKIM_SELECTOR}"] for d in dup["lld_dkim_selector"]["data"]] == ["s1", "s2"],
          dup["lld_dkim_selector"]["data"])
    check("повторный NS даёт одну строку",
          [d["{#NSHOST}"] for d in dup["lld_ns"]["data"]] == ["a.example"],
          dup["lld_ns"]["data"])

    print("отбор адресов: тот же код, что в рабочем прогоне")
    check("первые max_ip проверяются", mod.classify_address("192.0.2.1", 0, 5) == "CHECK")
    check("сверх лимита — NOT_CHECKED", mod.classify_address("192.0.2.1", 5, 5) == "NOT_CHECKED")
    check("max_ip == 0 означает без лимита",
          mod.classify_address("192.0.2.1", 99, 0) == "CHECK")
    check("IPv6 пропускается", mod.classify_address("2001:db8::1", 0, 5) == "SKIP_IPV6")
    check("IPv6 не тратит бюджет — после него слот ещё свободен",
          mod.classify_address("2001:db8::1", 4, 5) == "SKIP_IPV6"
          and mod.classify_address("192.0.2.1", 4, 5) == "CHECK")
    check("мусор вместо адреса — ERROR", mod.classify_address("не-адрес", 0, 5) == "ERROR")

    print("_ptr_details выбирает адреса по статусу")
    entries = [
        {"ip": "192.0.2.1", "status": "OK"},
        {"ip": "192.0.2.2", "status": "MISSING"},
        {"ip": "2001:db8::1", "status": "SKIP_IPV6"},
    ]
    check("_ptr_details выбирает адреса по статусу",
          mod._ptr_details(entries, "MISSING") == "192.0.2.2",
          mod._ptr_details(entries, "MISSING"))
    check("_ptr_details отдаёт *NONE* вместо пустой строки",
          mod._ptr_details(entries, "NO_FCRDNS") == "*NONE*")

    print("DKIM: отозванный ключ и тестовый режим (RFC 6376 §3.6.1)")
    res = mod.parse_dkim_records([
        "s1:v=DKIM1; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEF",
        "s2:v=DKIM1; k=rsa; p=",
        "s3:v=DKIM1; t=y; p=MIIBIjANBgkqhkiG9w0BAQEF",
        "s4:v=DKIM1; t=y:s; p=MIIBIjANBgkqhkiG9w0BAQEF",
        "s5:v=DKIM1; t=s; p=MIIBIjANBgkqhkiG9w0BAQEF",
        "s6:v=DKIM1; k=rsa",
    ])
    r = {x["selector"]: x for x in res["records"]}
    check("пустой p= — отозванный ключ", r["s2"]["revoked"] is True)
    check("отсутствие тега p — не отзыв, а сломанная запись", r["s6"]["revoked"] is False)
    check("t=y — тестовый режим", r["s3"]["testing"] is True)
    check("t=y:s — флаги через двоеточие разбираются", r["s4"]["testing"] is True)
    check("t=s — не тестовый режим", r["s5"]["testing"] is False)
    check("счётчики сходятся",
          res["revoked_count"] == 1 and res["testing_count"] == 2,
          (res["revoked_count"], res["testing_count"]))

    print("скелет несёт поля, которые читает шаблон")
    skel = mod._default_result()
    check("mx_null присутствует и False", skel["mx_null"] is False)
    check("ns_consistency.unanswered присутствует", "unanswered" in skel["ns_consistency"])
    check("dkim.revoked_count и testing_count присутствуют",
          {"revoked_count", "testing_count"} <= set(skel["dkim"]))

    print("покрытие PTR считает та же функция, что и рабочий прогон")
    entries = [
        {"ip": "192.0.2.1", "status": "OK"},
        {"ip": "192.0.2.2", "status": "MISSING"},
        {"ip": "2001:db8::1", "status": "SKIP_IPV6"},
        {"ip": "мусор", "status": "ERROR"},
    ]
    check("осмотрено 2 из 4 обнаруженных", mod.count_ptr_checked(entries) == 2,
          mod.count_ptr_checked(entries))
    check("пустой список -> ноль", mod.count_ptr_checked([]) == 0)

    print("_subnet_of работает без Python 3.7")
    import ipaddress as _ip
    net = _ip.ip_network
    for a, b, expected in (("10.0.0.0/24", "10.0.0.0/8", True),
                           ("10.0.0.0/8", "10.0.0.0/24", False),
                           ("192.0.2.0/24", "192.0.2.0/24", True),
                           ("203.0.113.0/24", "10.0.0.0/8", False),
                           ("2001:db8::/48", "2001:db8::/32", True)):
        check("{} в {} -> {}".format(a, b, expected),
              mod._subnet_of(net(a), net(b)) is expected)
    check("разные семейства адресов не роняют прогон",
          mod._subnet_of(net("10.0.0.0/8"), net("2001:db8::/32")) is False)

    print("битый ip4: не выдаётся за нарушение allowlist")
    spf = ["v=spf1 ip4:203.0.113.0/24 ip4:не-сеть -all"]
    без = mod.parse_spf("example.com", spf, None, [], False, 5.0, "-all|~all", [])
    check("без allowlist: битый механизм посчитан отдельно",
          без["cidr_malformed"] == ["ip4:не-сеть"] and без["cidr_out_of_allowlist"] == [],
          (без["cidr_malformed"], без["cidr_out_of_allowlist"]))
    с = mod.parse_spf("example.com", spf, None,
                      [_ip.ip_network("198.51.100.0/24")], False, 5.0, "-all|~all", [])
    check("с allowlist: чужая сеть попадает в нарушения, битая -- нет",
          с["cidr_out_of_allowlist"] == ["ip4:203.0.113.0/24"]
          and с["cidr_malformed"] == ["ip4:не-сеть"],
          (с["cidr_out_of_allowlist"], с["cidr_malformed"]))

    print("кэш сохраняет записи других процессов")
    import json as _json
    import os as _os
    import tempfile as _tf
    path = _tf.mktemp(suffix=".json")
    _json.dump({"A": {"v": 1}, "B": {"v": 1}}, open(path, "w"))
    loaded = mod.load_cache(path)
    # Снимок и разницу берём у самого скрипта, а не повторяем их здесь: своя копия
    # формулы проходит тест и тогда, когда рабочий код уже разошёлся с ней.
    start = mod.snapshot_cache(loaded)
    loaded["A"] = {"v": 2}                                      # правим свой ключ
    _json.dump({"A": {"v": 1}, "B": {"v": 99}}, open(path, "w"))  # чужой процесс успел
    mod.save_cache(path, mod.cache_changes(loaded, start))
    after = _json.load(open(path))
    check("свой ключ записан", after["A"] == {"v": 2}, after)
    check("чужой ключ не откачен", after["B"] == {"v": 99}, after)
    _os.unlink(path)

    print("снимок кэша глубокий")
    # Отличает глубокую копию от мелкой: при dict(cache) снимок разделил бы вложенный
    # словарь с оригиналом, правка на месте оказалась бы видна и в снимке, и
    # cache_changes решил бы, что менять нечего.
    orig = {"K": {"v": 1}}
    snap = mod.snapshot_cache(orig)
    orig["K"]["v"] = 2                                          # правка НА МЕСТЕ
    check("правка на месте попадает в изменения",
          mod.cache_changes(orig, snap) == {"K": {"v": 2}}, mod.cache_changes(orig, snap))
    check("нетронутый ключ в изменения не попадает",
          mod.cache_changes({"K": {"v": 1}}, {"K": {"v": 1}}) == {}, "не пусто")

    print("признаки видимости заведены по разделам")
    seen = mod._default_result()["seen"]
    check("восемь разделов",
          set(seen) == {"mx", "spf", "dkim", "ds", "dmarc", "transport", "bimi", "autoconfig"},
          sorted(seen))
    check("по умолчанию False -- прогон, ничего не увидевший, ничего и не утверждает",
          all(v is False for v in seen.values()), seen)

    print("разрыв покрытия чёрных списков считается по широкому знаменателю")
    # ERROR у check_ptr_fcrdns -- это и «адрес не разобрать», и «исправный IPv4, у
    # которого не ответил обратный DNS». Второй квоту потратил и лежит в checked_ips.
    # Сузишь знаменатель до count_ptr_checked -- вычитание занизит разрыв, и непроверенное
    # прочитается как чистое. Тест держит два счётчика раздельными намеренно.
    ptr = ([{"status": "OK"}] * 4 + [{"status": "ERROR"}]
           + [{"status": "OK"}] * 17 + [{"status": "ERROR"}] * 3)
    checked = ["1.2.3.{}".format(i) for i in range(5)]
    check("20 адресов без вердикта, ошибки PTR не вычитаются",
          mod.count_dnsbl_not_checked(ptr, checked) == 20,
          mod.count_dnsbl_not_checked(ptr, checked))
    check("знаменатель шире, чем у count_ptr_checked",
          mod.count_dnsbl_not_checked(ptr, checked) > max(0, mod.count_ptr_checked(ptr) - len(checked)),
          (mod.count_dnsbl_not_checked(ptr, checked), mod.count_ptr_checked(ptr)))
    check("IPv6 не попадает в разрыв покрытия",
          mod.count_dnsbl_not_checked([{"status": "SKIP_IPV6"}] * 9 + [{"status": "OK"}], ["1.2.3.4"]) == 0,
          mod.count_dnsbl_not_checked([{"status": "SKIP_IPV6"}] * 9 + [{"status": "OK"}], ["1.2.3.4"]))
    check("отрицательного разрыва не бывает",
          mod.count_dnsbl_not_checked([{"status": "OK"}], ["a", "b", "c"]) == 0,
          mod.count_dnsbl_not_checked([{"status": "OK"}], ["a", "b", "c"]))
    check("пустой ввод даёт ноль", mod.count_dnsbl_not_checked([], []) == 0,
          mod.count_dnsbl_not_checked([], []))
    check("запись без ключа status считается адресом",
          mod.count_dnsbl_not_checked([{}, {}], []) == 2,
          mod.count_dnsbl_not_checked([{}, {}], []))
    # Граница, которую счётчик НЕ закрывает, закреплена тестом, а не только текстом:
    # адрес, к которому обратились, но все зоны ответили CHECK FAILED, лежит в
    # checked_ips и даёт ноль. Вердикта про него нет, и считает это отдельный элемент
    # mail.dnsbl.check_failed.count. Если однажды решат, что not_checked обязан покрывать
    # и этот случай, тест упадёт и заставит поправить заодно описание элемента.
    check("адрес с провалившимся запросом в разрыв НЕ попадает (его считает check_failed)",
          mod.count_dnsbl_not_checked([{"status": "OK"}], ["1.2.3.4"]) == 0,
          mod.count_dnsbl_not_checked([{"status": "OK"}], ["1.2.3.4"]))

    print("prev охватывает шесть записей")
    prev = mod._default_result()["prev"]
    check("ключи spf, mx, dkim, dmarc, ns, ds",
          set(prev) == {"spf", "mx", "dkim", "dmarc", "ns", "ds"}, sorted(prev))
    check("значения по умолчанию — строки, не None",
          all(isinstance(v, str) for v in prev.values()), prev)

    print()
    if _failures:
        print("не сошлось: {}".format(", ".join(_failures)))
        return 1
    print("всё сошлось")
    return 0


if __name__ == "__main__":
    sys.exit(main())
