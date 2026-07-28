#!/usr/bin/env python3
"""Проверки шаблона, которые Zabbix при импорте не делает.

Запуск:  python3 tests/test_template_contracts.py

Каждая проверка здесь появилась после конкретной находки ревью:

1. JavaScript в шагах предобработки компилируется. Zabbix не компилирует его при
   импорте, поэтому опечатка проходит молча, а элемент уходит в NOTSUPPORTED на
   каждом значении. Так и случилось: два тела были записаны в YAML-скаляре в
   одинарных кавычках с последовательностью backslash-n, а YAML в одинарных
   кавычках escape-последовательности не разбирает, и в JS попадал настоящий
   обратный слэш.
2. Числовые функции не применяются к текстовым элементам. min/max/avg и прочие
   принимают только Float и Integer; на элементе типа TEXT выражение недопустимо.
   Для строк нужен count(..., "eq", ...), причём оператор обязателен: по
   умолчанию для строк действует like.
3. Каждый триггер, кроме двух, объявляет зависимость от триггера ошибки скрипта,
   иначе во время аварии посыпятся утверждения об отсутствии записей.
4. UUID уникальны — иначе импорт перезапишет чужую сущность.

Без node проверка 1 пропускается, остальные работают.
"""

import json
import pathlib
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
TPL = ROOT / "template_mail_dns_audit_zabbix.yaml"

NUMERIC_ONLY = {
    "min", "max", "avg", "sum", "percentile", "forecast", "timeleft",
    "trendavg", "trendmin", "trendmax", "trendsum", "trendcount",
}
TEXTUAL = {"TEXT", "CHAR", "LOG"}

_failures = []


def check(label, condition, detail=""):
    if condition:
        print("  ok   {}".format(label))
    else:
        print("  FAIL {} {}".format(label, detail))
        _failures.append(label)


def walk(node, out):
    """Собрать элементы, триггеры, JS-шаги и uuid по всему дереву."""
    if isinstance(node, dict):
        ctx = node.get("key")
        for key, value in node.items():
            if key == "uuid":
                out["uuids"].append(value)
            elif key in ("items", "item_prototypes") and isinstance(value, list):
                for item in value:
                    out["items"][item["key"].split("[")[0]] = item.get("value_type", "FLOAT")
                    out["raw_items"].append(item)
            elif key in ("triggers", "trigger_prototypes") and isinstance(value, list):
                out["triggers"].extend(t for t in value if "expression" in t)
            elif key == "preprocessing" and isinstance(value, list):
                for step in value:
                    if step.get("type") == "JAVASCRIPT":
                        out["js"].append((ctx, step["parameters"][0]))
            walk(value, out)
    elif isinstance(node, list):
        for value in node:
            walk(value, out)


def main():
    tpl = yaml.safe_load(TPL.read_text(encoding="utf-8"))
    found = {"items": {}, "triggers": [], "js": [], "uuids": [], "raw_items": []}
    walk(tpl, found)

    print("JavaScript в предобработке компилируется")
    if subprocess.run(["which", "node"], capture_output=True).returncode:
        print("  skip node не установлен")
    else:
        broken = []
        for name, src in found["js"]:
            probe = 'new Function("value", {})'.format(json.dumps(src))
            if subprocess.run(["node", "-e", probe], capture_output=True).returncode:
                broken.append(name)
        check("все {} шагов компилируются".format(len(found["js"])), not broken, broken)
        literal = [n for n, s in found["js"] if "\\n" in s]
        check("нет литерального backslash-n вместо переноса строки", not literal, literal)

    print("числовые функции не применяются к текстовым элементам")
    import re
    misuse = []
    for trigger in found["triggers"]:
        expr = str(trigger.get("expression", "")) + str(trigger.get("recovery_expression", ""))
        for func, key in re.findall(r"\b(\w+)\(/[^/]+/([a-zA-Z0-9_.]+)", expr):
            if func in NUMERIC_ONLY and found["items"].get(key) in TEXTUAL:
                misuse.append((trigger["name"][:40], func, key))
    check("ни одной несовместимой пары", not misuse, misuse)

    print("зависимости от триггера ошибки скрипта")
    no_dep = [t["name"] for t in found["triggers"] if not t.get("dependencies")]
    check(
        "без зависимости ровно два: сам триггер ошибки и nodata",
        len(no_dep) == 2 and all("script error" in n or "not running" in n for n in no_dep),
        no_dep,
    )

    print("булевы поля JSON приводятся к числу")
    # Элемент типа UNSIGNED, чей JSONPath указывает на true/false в выводе скрипта,
    # обязан иметь шаг BOOL_TO_DECIMAL — иначе Zabbix отвергает значение целиком и
    # элемент уходит в NOTSUPPORTED. Ошибку видно только на живых данных, поэтому
    # эталон берётся из реального прогона скрипта.
    sample = ROOT / "tests" / "sample_output.json"
    if not sample.exists():
        print("  skip нет tests/sample_output.json — эталон вывода скрипта")
    else:
        data = json.loads(sample.read_text(encoding="utf-8"))

        def resolve(path):
            cur = data
            for part in path[2:].split("."):
                if part.endswith("()") or part == "length":
                    return None
                if not isinstance(cur, dict) or part not in cur:
                    return None
                cur = cur[part]
            return cur

        missing = []
        for item in found["raw_items"]:
            if item.get("value_type") != "UNSIGNED":
                continue
            steps = item.get("preprocessing") or []
            jp = [s for s in steps if s.get("type") == "JSONPATH"]
            if not jp:
                continue
            val = resolve(jp[0]["parameters"][0])
            if isinstance(val, bool) and not any(s.get("type") == "BOOL_TO_DECIMAL" for s in steps):
                missing.append(item["key"])
        check("у каждого UNSIGNED над булевым полем есть BOOL_TO_DECIMAL", not missing, missing)
        # Страж против вакуумного прохода: если эталон устареет, resolve() вернёт None
        # для всех путей, ни одно булево поле не найдётся, и проверка выше пройдёт с
        # нулевым покрытием, ничего не проверив. Тот же приём, что в test_ptr_states.py.
        examined = sum(
            1 for item in found["raw_items"]
            if item.get("value_type") == "UNSIGNED"
            and [s for s in (item.get("preprocessing") or []) if s.get("type") == "JSONPATH"]
            and isinstance(
                resolve([s for s in item["preprocessing"] if s.get("type") == "JSONPATH"][0]["parameters"][0]),
                bool,
            )
        )
        check("эталон свежий: проверено хотя бы 5 булевых полей", examined >= 5,
              "найдено {} — вероятно, tests/sample_output.json устарел; "
              "пересоздать: python3 externalscripts/mail.dns.audit <ваш-домен> 127.0.0.1 10 0 "
              "zen.spamhaus.org '' 10 '-all|~all' 1200 5 5 default 1 > tests/sample_output.json".format(examined))

    print("уникальность uuid")
    dupes = {u for u in found["uuids"] if found["uuids"].count(u) > 1}
    check("дублей нет", not dupes, sorted(dupes))

    print()
    if _failures:
        print("не сошлось: {}".format(", ".join(_failures)))
        return 1
    print("всё сошлось")
    return 0


if __name__ == "__main__":
    sys.exit(main())
