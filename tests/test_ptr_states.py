#!/usr/bin/env python3
"""Проверка того, что PTR-проверка различает «записи нет» и «не смог узнать».

Запуск:  python3 tests/test_ptr_states.py

Регрессия, ради которой всё затевалось: транзиентный DNS-таймаут возвращался как
status="MISSING", то есть как авторитетное «у домена нет PTR», и поднимал HIGH-пейдж.
Авторитетным отрицанием является только NXDOMAIN/NoAnswer; всё остальное — ERROR.

Фреймворка нет намеренно: в репозитории нет тестовой обвязки, а одного runnable
self-check достаточно, чтобы поймать возврат дефекта.
"""

import importlib.machinery
import importlib.util
import pathlib
import re
import sys

import dns.exception
import dns.resolver

SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "externalscripts" / "mail.dns.audit"

_loader = importlib.machinery.SourceFileLoader("mail_dns_audit", str(SCRIPT))
_spec = importlib.util.spec_from_loader("mail_dns_audit", _loader)
mod = importlib.util.module_from_spec(_spec)
_loader.exec_module(mod)


# --- минимальные подделки ответов dnspython -------------------------------

class _Rec:
    def __init__(self, text):
        self._text = text

    def to_text(self):
        return self._text


class _RRset:
    ttl = 300


class _Response:
    flags = 0


class _Answer:
    def __init__(self, texts):
        self._recs = [_Rec(t) for t in texts]
        self.rrset = _RRset() if texts else None
        self.response = _Response()

    def __iter__(self):
        return iter(self._recs)


class _SilentDNSError(dns.exception.DNSException):
    """Сбой DNS, у которого str() пустой — проверяет фолбэк на имя класса."""

    def __str__(self):
        return ""


class FakeResolver:
    """Отдаёт заранее заданный ответ или исключение по типу записи."""

    def __init__(self, by_rdtype):
        self.by_rdtype = by_rdtype
        self.lifetime = 3.0
        self.timeout = 3.0

    def resolve(self, name, rdtype, **kwargs):
        value = self.by_rdtype.get(rdtype)
        if isinstance(value, Exception):
            raise value
        if value is None:
            raise dns.resolver.NXDOMAIN()
        return value


# RFC 5737 documentation address: the test must not pin a real installation
IP = "192.0.2.10"
FAILURES = []


def check(label, condition, detail=""):
    if condition:
        print("  ok   {}".format(label))
    else:
        print("  FAIL {} {}".format(label, detail))
        FAILURES.append(label)


def ptr(by_rdtype):
    return mod.check_ptr_fcrdns(FakeResolver(by_rdtype), IP, False)


def main():
    print("PTR: авторитетное отрицание -> MISSING")
    r = ptr({"PTR": dns.resolver.NXDOMAIN()})
    check("NXDOMAIN -> MISSING", r["status"] == "MISSING", r)

    r = ptr({"PTR": dns.resolver.NoAnswer()})
    check("NoAnswer -> MISSING", r["status"] == "MISSING", r)

    print("PTR: сбой измерения -> ERROR (регрессия, ради которой тест написан)")
    r = ptr({"PTR": dns.exception.Timeout()})
    check("Timeout -> ERROR, не MISSING", r["status"] == "ERROR", r)

    r = ptr({"PTR": dns.resolver.NoNameservers()})
    check("NoNameservers (SERVFAIL) -> ERROR", r["status"] == "ERROR", r)

    # Исключение с пустым сообщением: если причина окажется пустой строкой,
    # проверка на истинность снова выдала бы MISSING — то есть исходный баг.
    r = ptr({"PTR": _SilentDNSError()})
    check("сбой с пустым сообщением -> ERROR", r["status"] == "ERROR", r)
    check("причина не пустая", bool(r.get("error")), r)

    # Прямая A-проверка — второе плечо той же функции. Сбой на ней не должен
    # утверждать, что PTR не разрешается обратно (это триггер без фильтра #2).
    r = ptr({"PTR": _Answer(["mail.example.com."]), "A": dns.exception.Timeout()})
    check("таймаут на прямой A -> ERROR, не NO_FCRDNS", r["status"] == "ERROR", r)

    print("PTR: рабочие пути не задеты")
    r = ptr({"PTR": _Answer(["mail.example.com."]), "A": _Answer([IP])})
    check("совпадающая A -> OK", r["status"] == "OK", r)

    r = ptr({"PTR": _Answer(["mail.example.com."]), "A": _Answer(["203.0.113.1"])})
    check("несовпадающая A -> NO_FCRDNS", r["status"] == "NO_FCRDNS", r)

    r = ptr({"PTR": _Answer(["dynamic-1-2-3-4.example.net."]), "A": _Answer([IP])})
    check("generic-имя -> GENERIC", r["status"] == "GENERIC", r)

    print("детализация: какой именно IP, а не только сколько")
    ents = [{"ip": "1.1.1.1", "status": "MISSING"},
            {"ip": "2.2.2.2", "status": "OK"},
            {"ip": "3.3.3.3", "status": "MISSING"}]
    check("перечисляет только нужный статус",
          mod._ptr_details(ents, "MISSING") == "1.1.1.1, 3.3.3.3", mod._ptr_details(ents, "MISSING"))
    check("пусто -> *NONE*, а не пустая строка",
          mod._ptr_details(ents, "GENERIC") == "*NONE*", mod._ptr_details(ents, "GENERIC"))
    check("нет записей -> *NONE*", mod._ptr_details([], "MISSING") == "*NONE*")

    print("аварийный скелет покрывает корни JSONPath, которые читают зависимые items")
    tpl = SCRIPT.parent.parent / "template_mail_dns_audit_zabbix.yaml"
    roots = set(re.findall(r"\$\.([a-z_0-9]+)", tpl.read_text(encoding="utf-8")))
    # Проверка не должна проходить вхолостую: если бы шаблон не нашёлся или регексп
    # перестал совпадать, roots оказался бы пуст и «пропаж нет» было бы правдой ни о чём.
    check("шаблон прочитан и корни найдены", len(roots) >= 10, "найдено: {}".format(len(roots)))
    # lld_* исключены по шаблону имени, а не перечислением: новое правило обнаружения
    # не должно ронять тест и подталкивать к «исправлению», которое запустит
    # 30-дневное удаление обнаруженного. См. комментарий в _default_result().
    required = {r for r in roots if not r.startswith("lld_")}
    missing = sorted(required - set(mod._default_result().keys()))
    check("ни один читаемый корень не потерян", not missing, "отсутствуют: {}".format(missing))
    check("ptr.errors переживает аварийный ответ",
          "errors" in mod._default_result().get("ptr", {}), mod._default_result().get("ptr"))

    print("счётчик неудачных запросов: отличает «не нашли» от «не смогли посмотреть»")
    mod._LOOKUP_FAILURES = 0
    mod.query_records(FakeResolver({"MX": dns.resolver.NXDOMAIN()}), "n", "MX")
    check("авторитетное отрицание не считается сбоем", mod._LOOKUP_FAILURES == 0, mod._LOOKUP_FAILURES)
    mod.query_records(FakeResolver({"MX": dns.exception.Timeout()}), "n", "MX")
    mod.query_records(FakeResolver({"MX": dns.resolver.NoNameservers()}), "n", "MX")
    check("таймаут и SERVFAIL считаются", mod._LOOKUP_FAILURES == 2, mod._LOOKUP_FAILURES)
    check("счётчик есть в аварийном скелете",
          "lookup_failures" in mod._default_result()["meta"], mod._default_result()["meta"].keys())
    mod._LOOKUP_FAILURES = 0

    print("контракт query_records(): ровно три элемента — 25 вызовов не должны сломаться")
    out = mod.query_records(FakeResolver({"PTR": _Answer(["x."])}), "irrelevant", "PTR")
    check("возвращает 3-кортеж", isinstance(out, tuple) and len(out) == 3, out)
    records, _ttl, _ad = out
    check("первый элемент — список записей", records == ["x."], records)

    print()
    if FAILURES:
        print("ПРОВАЛЕНО: {}".format(", ".join(FAILURES)))
        return 1
    print("всё сошлось")
    return 0


if __name__ == "__main__":
    sys.exit(main())
