#!/usr/bin/env python3
"""Вердикт DNSBL берётся из A-записи; таймаут TXT его не отменяет.

Запуск:  python3 tests/test_dnsbl_states.py

Регрессия, ради которой всё затевалось: A-запрос к zen.spamhaus.org возвращал
127.0.0.2 (однозначный LISTED), следом вспомогательный TXT упирался в lifetime,
и статус безусловно перезаписывался на "CHECK FAILED". За сутки так испортилось
25 записей из 29 — канареечный триггер "DNSBL zone cannot prove it is alive"
висел на живой зоне, а настоящее попадание в блоклист потерялось бы вместе с
алертом.

Фреймворка нет намеренно — как и в соседних тестах репозитория.
"""

import importlib.machinery
import importlib.util
import pathlib
import sys

import dns.exception
import dns.resolver

SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "externalscripts" / "mail.dns.audit"

_loader = importlib.machinery.SourceFileLoader("mail_dns_audit", str(SCRIPT))
_spec = importlib.util.spec_from_loader("mail_dns_audit", _loader)
mod = importlib.util.module_from_spec(_spec)
_loader.exec_module(mod)


class _Rec:
    def __init__(self, text):
        self._text = text

    def to_text(self):
        return self._text

    @property
    def strings(self):
        return [self._text.encode()]


class _RRset:
    ttl = 300


class _Answer:
    def __init__(self, texts):
        self._recs = [_Rec(t) for t in texts]
        self.rrset = _RRset() if texts else None
        self.response = None

    def __iter__(self):
        return iter(self._recs)


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


# RFC 5737 documentation address: тест не должен опираться на реальную установку
IP = "192.0.2.10"
ZONE = "zen.example.org"
FAILURES = []


def check(label, condition, detail=""):
    if condition:
        print("  ok   {}".format(label))
    else:
        print("  FAIL {} {}".format(label, detail))
        FAILURES.append(label)


def dnsbl(by_rdtype):
    entries, listed = mod.check_dnsbl(FakeResolver(by_rdtype), IP, [ZONE], {}, 300)
    return entries[0], listed


def main():
    timeout = dns.exception.Timeout("The resolution lifetime expired after 10.1 seconds")

    print("таймаут TXT поверх успешного A не отменяет вердикт")
    entry, listed = dnsbl({"A": _Answer(["127.0.0.2"]), "TXT": timeout})
    check("статус берётся из A, а не из ошибки TXT", entry["status"] == "LISTED", entry)
    check("адрес попал в список listed", len(listed) == 1, listed)
    check("текст ошибки сохранён", "error" in entry and "lifetime" in entry["error"], entry)
    check("ошибка видна в txt, раз настоящего TXT нет", entry["txt"] == [entry["error"]], entry)

    print("таймаут самого A по-прежнему = CHECK FAILED")
    entry, listed = dnsbl({"A": timeout, "TXT": timeout})
    check("нет A -- нет вердикта", entry["status"] == "CHECK FAILED", entry)
    check("в listed ничего не попало", listed == [], listed)

    print("policy-ответ определяется по A и без TXT")
    entry, _ = dnsbl({"A": _Answer(["127.255.255.254"]), "TXT": timeout})
    check("127.255.x -> POLICY/ERROR", entry["status"] == "POLICY/ERROR", entry)

    print("авторитетное отрицание не путается с ошибкой")
    entry, _ = dnsbl({"A": None, "TXT": None})
    check("NXDOMAIN -> NOT LISTED", entry["status"] == "NOT LISTED", entry)

    print("живой TXT не подменяется текстом ошибки")
    entry, _ = dnsbl({"A": _Answer(["127.0.0.2"]), "TXT": _Answer(["Listed by XBL"])})
    check("TXT остался настоящим", entry["txt"] == ["Listed by XBL"], entry)
    check("ошибки нет", "error" not in entry, entry)

    print()
    if FAILURES:
        print("не сошлось: {}".format(", ".join(FAILURES)))
        return 1
    print("всё сошлось")
    return 0


if __name__ == "__main__":
    sys.exit(main())
